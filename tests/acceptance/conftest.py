"""Fixtures for the acceptance harness (P-016).

Brings up the default Compose profile, polls readiness, and tears down after.
Everything in `tests/acceptance/` is marked `live` and excluded from the
default `pytest` run by `pyproject.toml`'s `addopts = "-m 'not live'"` — this
suite needs Docker, Postgres, Redis, and MinIO. Run it explicitly with
`make test-acceptance` or `pytest -m live`.

Design constraints, from PROPOSAL_ACCEPTANCE_HARNESS.md §4:

- No Docker on the machine -> SKIP, never FAIL. A contributor without Docker
  must still see a green default suite.
- A service that never becomes ready -> FAIL, naming which service and its
  last response. Never a bare traceback.
- Teardown must be idempotent and must run even if setup only got partway.
"""

from __future__ import annotations

import shutil
import subprocess
import time
import uuid
from typing import Callable
from pathlib import Path
from typing import Iterator

import pytest

# importorskip, not a bare import: a missing httpx must skip this directory,
# never crash collection for the whole repo. tests/docs/ already asserts every
# module has a Verification section; this is the same "the offline suite must
# stay green no matter what" rule applied to this suite's own dependency.
httpx = pytest.importorskip(
    "httpx", reason="httpx not installed — needed only for tests/acceptance/", exc_type=ImportError
)

REPO = Path(__file__).resolve().parents[2]
API_BASE = "http://127.0.0.1:8000"
ACCEPTANCE_PROJECT = f"hcp-acceptance-{uuid.uuid4().hex[:12]}"

# How long to wait for the stack to become ready before failing. Cold image
# pulls on a fresh machine are the slow path; a warm cache is seconds.
READINESS_BUDGET_S = 180
POLL_INTERVAL_S = 2


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
            check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    return True


def _compose(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", "--project-name", ACCEPTANCE_PROJECT,
         "-f", str(REPO / "docker-compose.yml"), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=1200,
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-skip `live`-marked tests when Docker is unavailable.

    This is the one test class in the repo that needs a real decision at
    collection time rather than inside the test body — every `live` test
    would otherwise report a confusing connection-refused traceback instead
    of one clear reason.
    """
    if _docker_available():
        return
    skip_live = pytest.mark.skip(reason="docker unavailable — acceptance suite needs a daemon")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


def _wait_for_readiness() -> None:
    """Poll /ready until every dependency reports ok, or fail naming the
    service and its last response."""
    deadline = time.monotonic() + READINESS_BUDGET_S
    last_body: dict | str = "(no response yet)"

    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"{API_BASE}/ready", timeout=5)
            last_body = resp.json()
            if resp.status_code == 200 and last_body.get("status") == "ok":
                return
        except httpx.TransportError as exc:
            # Broad on purpose: this loop's whole job is absorbing every
            # transient network condition during startup, not enumerating
            # them. A narrower tuple here (ConnectError/ReadTimeout/
            # ConnectTimeout only) missed httpx.ReadError — a real
            # "Connection reset by peer" during container startup crashed
            # this fixture with a raw traceback on the harness's actual
            # first CI run, instead of being retried like S7 requires.
            # httpx.TransportError is the parent of every network-level
            # exception httpx raises (connect/read/write, timeouts, proxy,
            # protocol) without also swallowing request-construction bugs,
            # which are not httpx.RequestError's problem to hide.
            last_body = f"connection failed: {exc!r}"
        time.sleep(POLL_INTERVAL_S)

    failing = (
        {k: v for k, v in last_body.items() if v != "ok"}
        if isinstance(last_body, dict)
        else last_body
    )
    pytest.fail(
        f"stack did not become ready within {READINESS_BUDGET_S}s. "
        f"Last /ready response: {failing}",
        pytrace=False,
    )


@pytest.fixture(scope="session")
def docker_stack() -> Iterator[None]:
    """Bring up the default Compose profile for the whole acceptance session.

    Teardown always runs `docker compose down`, even if `up` only partially
    succeeded — a previous crashed run must not poison the next one (S10).
    """
    # This unique project owns its own volumes. Never run teardown against
    # the creator's default Compose project or delete their recordings/database.
    _compose("down", "--volumes", "--remove-orphans")

    up = _compose("up", "-d")
    try:
        if up.returncode != 0:
            pytest.fail(
                f"`docker compose up -d` failed:\nstdout: {up.stdout}\nstderr: {up.stderr}",
                pytrace=False,
            )
        _wait_for_readiness()
        yield
    finally:
        # Runs on normal completion, on a failed assertion, and on most
        # interrupts pytest can catch (S9) — but SIGKILL or a crash of the
        # pytest process itself will still leave containers running. Compose
        # state is why `down` also opens every session (S10), not just closes
        # this one.
        _compose("down", "--volumes", "--remove-orphans")


@pytest.fixture(scope="session")
def compose_runner(docker_stack: None) -> Callable[..., subprocess.CompletedProcess]:
    """Run a helper only against this session's disposable acceptance project."""
    return _compose


@pytest.fixture(scope="session")
def api_client(docker_stack: None) -> Iterator[httpx.Client]:
    """An httpx client bound to the FastAPI service, stack already ready."""
    with httpx.Client(base_url=API_BASE, timeout=10) as client:
        yield client
