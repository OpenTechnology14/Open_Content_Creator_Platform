"""Pool safety regressions run without Postgres or optional relay dependencies."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_database(monkeypatch):
    package = "hcp_database_safety"
    config = types.ModuleType(f"{package}.config")
    config.settings = types.SimpleNamespace(database_url="postgresql://test")
    monkeypatch.setitem(sys.modules, package, types.ModuleType(package))
    monkeypatch.setitem(sys.modules, f"{package}.config", config)
    monkeypatch.setitem(sys.modules, "asyncpg", types.SimpleNamespace(Pool=object))
    spec = importlib.util.spec_from_file_location(
        f"{package}.database", ROOT / "cloud/relay-api/app/database.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Connection:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    async def execute(self, query, *args):
        self.calls.append((query, args))
        if self.fail:
            raise RuntimeError("synthetic database failure")


class Pool:
    def __init__(self, conn):
        self.conn = conn
        self.acquired = 0
        self.released = []

    async def acquire(self):
        self.acquired += 1
        return self.conn

    async def release(self, conn):
        self.released.append(conn)


def test_tenant_context_uses_a_real_parameterizable_query(monkeypatch):
    module = load_database(monkeypatch)
    conn = Connection()
    module.pool = Pool(conn)
    tenant = str(uuid.uuid4())
    assert asyncio.run(module.get_conn(tenant)) is conn
    assert conn.calls == [("SELECT set_config('app.tenant_id', $1, false)", (tenant,))]


def test_invalid_tenant_does_not_acquire_a_connection(monkeypatch):
    module = load_database(monkeypatch)
    module.pool = Pool(Connection())
    with pytest.raises(ValueError):
        asyncio.run(module.get_conn("not-a-uuid"))
    assert module.pool.acquired == 0


def test_setup_failure_releases_the_borrowed_connection(monkeypatch):
    module = load_database(monkeypatch)
    conn = Connection(fail=True)
    module.pool = Pool(conn)
    with pytest.raises(RuntimeError):
        asyncio.run(module.get_conn(str(uuid.uuid4())))
    assert module.pool.released == [conn]


def test_reset_failure_still_returns_connection_to_pool(monkeypatch):
    module = load_database(monkeypatch)
    conn = Connection(fail=True)
    module.pool = Pool(conn)
    with pytest.raises(RuntimeError):
        asyncio.run(module.release_conn(conn))
    assert module.pool.released == [conn]


def test_unscoped_acquisition_clears_previous_tenant(monkeypatch):
    module = load_database(monkeypatch)
    conn = Connection()
    module.pool = Pool(conn)
    asyncio.run(module.get_conn())
    assert conn.calls == [("SELECT set_config('app.tenant_id', $1, false)", ("",))]
