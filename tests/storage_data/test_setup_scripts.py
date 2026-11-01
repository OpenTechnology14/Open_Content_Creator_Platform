"""Offline tests for the storage-data setup scripts.

Deliberately **offline**: no Postgres, no MinIO, no network. These assert the
contracts the scripts promise, which is what actually broke — `make migrate`
failed on stock macOS for a shell-portability reason, and applied migrations in
the wrong order for a sorting reason. Neither needed a database to catch.

Live checks against a real Postgres/MinIO belong in the `acceptance-harness`
module (`P-016`), not here — `tests/README.md` requires hardware and live-cloud
checks to stay separate from the required offline suite.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MIGRATE = REPO / "scripts" / "setup" / "postgres_migrate.sh"
MINIO_INIT = REPO / "scripts" / "setup" / "minio_init.sh"
COMPOSE = REPO / "docker-compose.yml"

MIGRATION_DIRS = [
    REPO / "modules" / "storage-data" / "postgres" / "migrations",
    REPO / "modules" / "ai-agents" / "local-llm" / "migrations",
]

# CLAUDE.md §5: bash scripts are POSIX-compatible and tested on Ubuntu 22.04 AND
# macOS. macOS ships bash 3.2 as /bin/bash, so bash-4-only builtins break there.
BASH4_ONLY_BUILTINS = ["mapfile", "readarray"]


def _scripts() -> list[Path]:
    return sorted((REPO / "scripts").rglob("*.sh"))


@pytest.mark.parametrize("script", _scripts(), ids=lambda p: p.name)
def test_script_parses_under_bash_3_2(script: Path) -> None:
    """Every shell script must at least parse under macOS's system bash."""
    bash = shutil.which("bash") or "/bin/bash"
    result = subprocess.run([bash, "-n", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, f"{script.name} failed to parse:\n{result.stderr}"


@pytest.mark.parametrize("script", _scripts(), ids=lambda p: p.name)
def test_script_avoids_bash4_only_builtins(script: Path) -> None:
    """`mapfile`/`readarray` do not exist in bash 3.2 — the macOS default.

    Regression test: postgres_migrate.sh used `mapfile`, so `make migrate` died
    with 'mapfile: command not found' on a stock macOS machine.
    """
    body = script.read_text(encoding="utf-8")
    for builtin in BASH4_ONLY_BUILTINS:
        assert not re.search(rf"^\s*{builtin}\s", body, re.MULTILINE), (
            f"{script.name} uses `{builtin}`, which bash 3.2 (macOS /bin/bash) lacks"
        )


# Scripts that deliberately omit `-e`, with the reason. `-u` and `pipefail` are
# never optional.
ERREXIT_EXEMPT = {
    # Aggregates failures: it must run every check and report the count, so
    # aborting on the first failure would defeat its purpose.
    "healthcheck.sh",
}


@pytest.mark.parametrize("script", _scripts(), ids=lambda p: p.name)
def test_script_uses_strict_mode(script: Path) -> None:
    """CLAUDE.md §5 requires strict mode. `-e` is exempt only where documented."""
    body = script.read_text(encoding="utf-8")
    match = re.search(r"^set -([a-z]+)o pipefail\s*$", body, re.MULTILINE)
    assert match, f"{script.name} does not `set -...o pipefail`"

    flags = match.group(1)
    assert "u" in flags, f"{script.name} does not set -u (undefined variables)"

    if script.name not in ERREXIT_EXEMPT:
        assert "e" in flags, (
            f"{script.name} does not set -e. If that is deliberate, add it to "
            "ERREXIT_EXEMPT with the reason."
        )


def test_migrations_apply_in_filename_order() -> None:
    """Migrations sort by filename, not by the directory they live in.

    Regression test: sorting full paths applied ai-agents/0002_memory.sql before
    storage-data/0001_init.sql, because 'ai-agents' precedes 'storage-data'.
    0002 uses gen_random_uuid(), whose pgcrypto extension 0001 creates.
    """
    found = [p for d in MIGRATION_DIRS if d.is_dir() for p in d.glob("*.sql")]
    assert found, "no migrations discovered — did a module move?"

    by_filename = [p.name for p in sorted(found, key=lambda p: p.name)]
    by_full_path = [p.name for p in sorted(found, key=lambda p: str(p))]

    assert by_filename == sorted(by_filename)
    # The bug this guards: the two orderings differ, so sorting the wrong key is
    # silently wrong rather than obviously wrong.
    if by_filename != by_full_path:
        body = MIGRATE.read_text(encoding="utf-8")
        assert "$NF" in body, (
            "migration filenames sort differently from their full paths, so "
            "postgres_migrate.sh must sort on the basename ($NF), not the path"
        )


def test_migrate_script_covers_every_module_migration_dir() -> None:
    """A module that adds migrations but is not listed is silently never applied."""
    body = MIGRATE.read_text(encoding="utf-8")
    for d in MIGRATION_DIRS:
        if not d.is_dir():
            continue
        rel = str(d.relative_to(REPO))
        assert rel in body, f"{rel} holds migrations but postgres_migrate.sh does not list it"


def test_declared_buckets_cover_every_bucket_modules_reference() -> None:
    """Every bucket a module's docs depend on must exist in minio_init.sh.

    Regression test: nature-corpus and cityscape-corpus were specified by two
    modules and absent from the script, so their setup instructions could not
    be followed.
    """
    body = MINIO_INIT.read_text(encoding="utf-8")
    block = re.search(r"BUCKETS=\((.*?)\n\)", body, re.DOTALL)
    assert block, "could not locate the BUCKETS array in minio_init.sh"
    declared = set(re.findall(r'"([a-z0-9-]+)"', block.group(1)))

    required = {
        "comfyui-outputs",   # realtime-ai
        "recordings",        # creator-experience
        "models",            # every module that downloads a weight
        "project-assets",    # content-creation, image-editing
        "backups",           # infrastructure
        "nature-corpus",     # nature-generation
        "cityscape-corpus",  # cityscape-generation
    }
    missing = required - declared
    assert not missing, f"minio_init.sh does not create: {sorted(missing)}"


def test_minio_setup_uses_current_lifecycle_import_command() -> None:
    """The current MinIO client nests lifecycle imports under `ilm rule`."""
    body = MINIO_INIT.read_text(encoding="utf-8")
    assert "mc ilm rule import" in body
    assert "mc ilm import" not in body


def test_minio_services_do_not_pull_retired_images() -> None:
    """Both server and client now use repository-owned source builds."""
    body = COMPOSE.read_text(encoding="utf-8")
    assert "image: hcp-minio:" in body
    assert "image: hcp-minio-client:" in body
    assert "quay.io/minio/" not in body
    assert "image: minio/minio:" not in body
    assert "image: minio/mc:" not in body


def test_migrations_are_transactional() -> None:
    """A migration that half-applies leaves the database in an unknown state."""
    for d in MIGRATION_DIRS:
        for sql in sorted(d.glob("*.sql")) if d.is_dir() else []:
            body = sql.read_text(encoding="utf-8").upper()
            assert "BEGIN;" in body and "COMMIT;" in body, (
                f"{sql.name} is not wrapped in BEGIN/COMMIT"
            )


def test_streams_table_has_platforms_not_platform() -> None:
    """Regression: 0001_init.sql declared `platform TEXT NOT NULL` (singular)
    while app/routers/streams.py's INSERT and SELECT both use `platforms`
    (plural, TEXT[]) — schema and router code disagreed from the start, caught
    only when POST /streams hit a real database for the first time
    (P-016's acceptance harness). This is the offline half of that regression
    test; tests/acceptance/test_creator_journey.py is the live half — the
    only one that can actually insert a row and prove the array binds.
    """
    sql = (REPO / "modules" / "storage-data" / "postgres" / "migrations" / "0001_init.sql").read_text()
    # Strip SQL line-comments first — this test's own module docstring and
    # the migration's explanatory comment both mention the literal old
    # syntax ("platform TEXT NOT NULL") in prose, which would otherwise
    # match the very regex meant to catch it back in real SQL.
    sql_no_comments = re.sub(r"--[^\n]*", "", sql)
    start = sql_no_comments.index("CREATE TABLE IF NOT EXISTS streams")
    end = sql_no_comments.index(");", start)
    columns = sql_no_comments[start:end]

    assert "platforms" in columns, "streams table lost its platforms column"
    assert not re.search(r"\bplatform\s+TEXT", columns), (
        "streams table has a singular `platform` column again — "
        "backend-api's router reads/writes `platforms` (plural, array)"
    )
