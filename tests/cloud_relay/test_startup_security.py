"""Offline checks for the cloud relay's startup security posture (P-049, WP-2).

`startup_security.py` has zero framework imports by design, so this suite
needs neither the relay's dependencies installed nor a running service —
matching HCP-007's real gap: nothing enforced "startup refuses weak
production secrets" or a real CORS origin list before this.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
APP_DIR = REPO / "cloud" / "relay-api" / "app"

sys.path.insert(0, str(APP_DIR))

from startup_security import (  # noqa: E402
    allowed_origins,
    assert_safe_for_production,
    is_weak_secret,
)


# ── is_weak_secret ──────────────────────────────────────────────────────

def test_is_weak_secret_catches_compose_file_default():
    assert is_weak_secret("change-me-in-production")


def test_is_weak_secret_catches_env_example_placeholder():
    """A different literal string than the compose file's default — both
    placeholder conventions must be caught, or a user who only edits one
    file (or neither) still starts up with a real secret's shape but a
    guessable value."""
    assert is_weak_secret("change-me-use-at-least-32-random-characters")


def test_is_weak_secret_catches_empty_string():
    assert is_weak_secret("")


def test_is_weak_secret_is_case_insensitive():
    assert is_weak_secret("CHANGE-ME-IN-PRODUCTION")
    assert is_weak_secret("Change-Me-Whatever-You-Want")


def test_is_weak_secret_allows_a_real_looking_secret():
    assert not is_weak_secret("k3f9-8vQ2mZ7xR4nL1pW6tY0sB5jH8dC3aE9gU2iN7oV4qF")


# ── assert_safe_for_production ──────────────────────────────────────────

REAL_SECRET = "a-real-random-secret-value"
REAL_DB_URL = "postgresql+asyncpg://relay:relay@postgres:5432/relay"
DEFAULT_DB_URL = "postgresql+asyncpg://relay:relay@localhost:5432/relay"


def test_assert_safe_for_production_raises_on_weak_secret_in_production():
    with pytest.raises(RuntimeError, match="RELAY_JWT_SECRET"):
        assert_safe_for_production("production", "change-me-in-production", REAL_DB_URL)


def test_assert_safe_for_production_raises_on_empty_secret_in_production():
    with pytest.raises(RuntimeError):
        assert_safe_for_production("production", "", REAL_DB_URL)


def test_assert_safe_for_production_raises_on_default_database_url_in_production():
    """Matches PROPOSAL_RELEASE_GAP_CLOSURE.md §7.2's own example spec:
    "Production database URL must be explicit." Settings.database_url's own
    field default points at localhost — a deployment that forgot to set
    RELAY_DATABASE_URL would otherwise start up talking to nothing."""
    with pytest.raises(RuntimeError, match="RELAY_DATABASE_URL"):
        assert_safe_for_production("production", REAL_SECRET, DEFAULT_DB_URL)


def test_assert_safe_for_production_allows_weak_secret_outside_production():
    """A bare `python -m uvicorn` in local dev — Settings.environment
    defaults to "development" — must not be forced to configure a secret
    or database just to start."""
    assert assert_safe_for_production("development", "change-me-in-production", DEFAULT_DB_URL) is None


def test_assert_safe_for_production_allows_compose_service_hostname():
    """The compose file's own RELAY_DATABASE_URL uses the Docker service
    name `postgres`, not `localhost` — must not false-positive on that."""
    assert assert_safe_for_production("production", REAL_SECRET, REAL_DB_URL) is None


# ── allowed_origins ──────────────────────────────────────────────────────

def test_allowed_origins_never_contains_a_wildcard():
    """Regression for the actual bug: `allow_origins=["*"]` combined with
    `allow_credentials=True` — meaningless per the CORS spec and no boundary
    at all for non-browser clients."""
    assert "*" not in allowed_origins("production")
    assert "*" not in allowed_origins("development")


def test_allowed_origins_production_is_tauri_only():
    origins = allowed_origins("production")
    assert "tauri://localhost" in origins
    assert "https://tauri.localhost" in origins
    assert "http://localhost:5173" not in origins
    assert "http://localhost:5174" not in origins


def test_allowed_origins_non_production_also_includes_dev_servers():
    origins = allowed_origins("development")
    assert "tauri://localhost" in origins
    assert "http://localhost:5173" in origins
    assert "http://localhost:5174" in origins


def test_dev_origins_match_each_apps_own_tauri_conf_dev_url():
    """The dev origins aren't made up — pull devUrl straight from each app's
    committed tauri.conf.json so this can't silently drift from reality."""
    import json

    stream_conf = json.loads(
        (REPO / "apps" / "stream-extend" / "src-tauri" / "tauri.conf.json").read_text()
    )
    creator_conf = json.loads(
        (REPO / "apps" / "creator-extend" / "src-tauri" / "tauri.conf.json").read_text()
    )
    dev_origins = allowed_origins("development")
    assert stream_conf["build"]["devUrl"] in dev_origins
    assert creator_conf["build"]["devUrl"] in dev_origins


# ── compose file port bindings ───────────────────────────────────────────

def test_relay_compose_database_url_is_not_the_default_localhost_one():
    """Ties assert_safe_for_production's database check to the real compose
    file, not just a hardcoded string in this test."""
    compose = yaml.safe_load(
        (REPO / "cloud" / "docker-compose.relay.yml").read_text()
    )
    db_url = compose["services"]["relay-api"]["environment"]["RELAY_DATABASE_URL"]
    assert "localhost" not in db_url


def test_relay_compose_internal_services_bind_localhost_only():
    """Postgres and Redis are internal-only dependencies — the regression
    test for HCP-007's "publishes Postgres and Redis ports" finding.
    relay-api's own port is deliberately excluded: it's the actual public
    API surface, not an internal dependency."""
    compose = yaml.safe_load(
        (REPO / "cloud" / "docker-compose.relay.yml").read_text()
    )
    for service_name in ("postgres", "redis"):
        ports = compose["services"][service_name].get("ports", [])
        assert ports, f"{service_name} has no port mapping to check"
        for mapping in ports:
            assert mapping.startswith("127.0.0.1:"), (
                f"{service_name}'s port mapping {mapping!r} is not bound to "
                "127.0.0.1 — it would be reachable from outside the host"
            )
