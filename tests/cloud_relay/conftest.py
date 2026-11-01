"""Owned, loopback-only Postgres for relay RLS tests; never tears down creator data."""
from __future__ import annotations

import asyncio
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "cloud/relay-api"))


def _native_available() -> bool:
    return all(shutil.which(tool) for tool in ("initdb", "pg_ctl", "psql"))


def _docker_available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=10).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if _native_available() or _docker_available():
        return
    for item in items:
        if "tests/cloud_relay/" in str(item.fspath) and "live" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="owned Postgres requires native tools or Docker"))


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=180, check=True)


async def _ready(url: str) -> bool:
    import asyncpg
    try:
        conn = await asyncpg.connect(url, timeout=2)
        await conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def relay_postgres(tmp_path_factory):
    """Start only an owned temporary cluster/container; no default Compose teardown."""
    directory = tmp_path_factory.mktemp("hcp-relay-acceptance")
    migrations = [REPO / "cloud/migrations" / name
                  for name in ("001_init.sql", "002_runtime_role.sql")]
    if _native_available():
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        data = directory / "data"
        # macOS Unix socket paths have a short limit; pytest's nested path exceeds it.
        socket_directory = Path(tempfile.mkdtemp(prefix="hcp-relay-socket-", dir="/tmp"))
        _run(["initdb", "-D", str(data), "-U", "hcp_test_admin", "--auth=trust", "--no-locale"])
        started = False
        try:
            _run(["pg_ctl", "-D", str(data), "-l", str(directory / "server.log"),
                  "-o", f"-h 127.0.0.1 -p {port} -k {socket_directory}", "-w", "start"])
            started = True
            connection = ["psql", "-h", "127.0.0.1", "-p", str(port), "-U", "hcp_test_admin",
                          "-d", "postgres", "-v", "ON_ERROR_STOP=1"]
            for migration in migrations:
                _run(connection + ["-f", str(migration)])
            yield {"admin_url": f"postgresql://hcp_test_admin@127.0.0.1:{port}/postgres",
                   "runtime_url": f"postgresql://relay_app@127.0.0.1:{port}/postgres",
                   "backend": "native"}
        finally:
            if started:
                _run(["pg_ctl", "-D", str(data), "-m", "fast", "-w", "stop"])
            shutil.rmtree(socket_directory)
    else:
        name = f"hcp-relay-acceptance-{uuid.uuid4().hex[:12]}"
        args = ["docker", "run", "--detach", "--rm", "--name", name,
                "-e", "POSTGRES_USER=hcp_test_admin", "-e", "POSTGRES_DB=relay",
                "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "-p", "127.0.0.1::5432"]
        for migration in migrations:
            args += ["-v", f"{migration}:/docker-entrypoint-initdb.d/{migration.name}:ro"]
        # Trust authentication is confined to this disposable loopback-only test instance.
        try:
            _run(args + ["postgres:16-alpine"])
            binding = _run(["docker", "port", name, "5432/tcp"]).stdout.strip()
            if not binding.startswith("127.0.0.1:"):
                pytest.fail("owned Postgres binding is not loopback-only", pytrace=False)
            port = int(binding.split(":")[1])
            urls = {"admin_url": f"postgresql://hcp_test_admin@127.0.0.1:{port}/relay",
                    "runtime_url": f"postgresql://relay_app@127.0.0.1:{port}/relay",
                    "backend": "docker"}
            deadline = time.monotonic() + 60
            while not asyncio.run(_ready(urls["runtime_url"])):
                if time.monotonic() >= deadline:
                    pytest.fail("owned Postgres runtime role did not become ready", pytrace=False)
                time.sleep(1)
            yield urls
        finally:
            subprocess.run(["docker", "rm", "--force", name], capture_output=True, timeout=30)
