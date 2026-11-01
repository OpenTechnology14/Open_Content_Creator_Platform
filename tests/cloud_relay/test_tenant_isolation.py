"""Real Postgres positive/negative controls for relay role, RLS and pooled context."""
from __future__ import annotations

import asyncio
import uuid

import pytest

asyncpg = pytest.importorskip("asyncpg")
from app import database  # noqa: E402

pytestmark = pytest.mark.live


async def isolation_run(server):
    admin = await asyncpg.connect(server["admin_url"])
    previous = database.settings.database_url
    tenants = [uuid.uuid4(), uuid.uuid4()]
    try:
        for tenant in tenants:
            await admin.execute("INSERT INTO tenants(id,email) VALUES($1,$2)",
                                tenant, f"{tenant}@example.invalid")
        database.settings.database_url = server["runtime_url"]
        await database.init_db()
        # Guard proves all tenant tables enforce RLS. One connection then proves reuse.
        await database.pool.close()
        database.pool = await asyncpg.create_pool(server["runtime_url"], min_size=1, max_size=1)
        async with database.TenantConnection(str(tenants[0])) as conn:
            pid = conn.get_server_pid()
            await conn.execute("INSERT INTO sync_data(tenant_id,key,value) VALUES($1,$2,$3)",
                               tenants[0], "settings/theme", '{"color":"dark"}')
            assert await conn.fetchval("SELECT count(*) FROM sync_data") == 1
        async with database.TenantConnection(str(tenants[1])) as conn:
            assert conn.get_server_pid() == pid
            assert await conn.fetchval("SELECT count(*) FROM sync_data") == 0
            assert await conn.execute("UPDATE sync_data SET value='{}' WHERE tenant_id=$1",
                                      tenants[0]) == "UPDATE 0"
            assert await conn.execute("DELETE FROM sync_data WHERE tenant_id=$1",
                                      tenants[0]) == "DELETE 0"
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.execute("INSERT INTO sync_data(tenant_id,key) VALUES($1,$2)",
                                   tenants[0], "forbidden")
        conn = await database.get_conn()
        try:
            assert conn.get_server_pid() == pid
            assert await conn.fetchval("SELECT current_setting('app.tenant_id',true)") == ""
            assert await conn.fetchval("SELECT count(*) FROM sync_data") == 0
        finally:
            await database.release_conn(conn)
        async with database.TenantConnection(str(tenants[0])) as conn:
            assert await conn.fetchval("SELECT count(*) FROM sync_data") == 1
        inserts = [
            ("devices", "INSERT INTO devices(id,tenant_id,name) VALUES($1,$2,$3)",
             [str(uuid.uuid4()), tenants[0], "Synthetic"]),
            ("metrics", "INSERT INTO metrics(tenant_id,name,value,timestamp) VALUES($1,$2,$3,NOW())",
             [tenants[0], "synthetic-metric", 1.0]),
            ("api_keys", "INSERT INTO api_keys(tenant_id,key_hash,name) VALUES($1,$2,$3)",
             [tenants[0], "synthetic-hash", "Synthetic"]),
            ("team_members", "INSERT INTO team_members(tenant_id,user_email) VALUES($1,$2)",
             [tenants[0], "synthetic@example.invalid"]),
            ("notification_log", "INSERT INTO notification_log(tenant_id,title,body) VALUES($1,$2,$3)",
             [tenants[0], "Synthetic", "No notification sent"]),
        ]
        for table, statement, values in inserts:
            async with database.TenantConnection(str(tenants[0])) as conn:
                await conn.execute(statement, *values)
                assert await conn.fetchval(f"SELECT count(*) FROM {table}") == 1
            async with database.TenantConnection(str(tenants[1])) as conn:
                assert await conn.fetchval(f"SELECT count(*) FROM {table}") == 0
                assert await conn.execute(f"UPDATE {table} SET tenant_id=tenant_id WHERE tenant_id=$1",
                                          tenants[0]) == "UPDATE 0"
                assert await conn.execute(f"DELETE FROM {table} WHERE tenant_id=$1", tenants[0]) == "DELETE 0"
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await conn.execute(statement, *values)
    finally:
        if database.pool:
            await database.pool.close()
            database.pool = None
        database.settings.database_url = previous
        for tenant in tenants:
            await admin.execute("DELETE FROM tenants WHERE id=$1", tenant)
        await admin.close()


def test_rls_blocks_cross_tenant_read_and_write_with_pooled_reuse(relay_postgres):
    asyncio.run(isolation_run(relay_postgres))


@pytest.mark.parametrize("unsafe", ["superuser", "table-owner"])
def test_startup_rejects_roles_that_bypass_tenant_row_security(relay_postgres, unsafe):
    async def run():
        admin = await asyncpg.connect(relay_postgres["admin_url"])
        previous = database.settings.database_url
        try:
            if unsafe == "table-owner":
                await admin.execute("ALTER TABLE sync_data OWNER TO relay_app")
            database.settings.database_url = (relay_postgres["admin_url"] if unsafe == "superuser"
                                              else relay_postgres["runtime_url"])
            with pytest.raises(RuntimeError, match="row security|non-superuser"):
                await database.init_db()
            assert database.pool is None
        finally:
            if unsafe == "table-owner":
                await admin.execute("ALTER TABLE sync_data OWNER TO hcp_test_admin")
            database.settings.database_url = previous
            await admin.close()
    asyncio.run(run())
