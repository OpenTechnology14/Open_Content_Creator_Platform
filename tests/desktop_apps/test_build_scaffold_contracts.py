"""Offline structural checks for the two desktop apps' build scaffolding
(P-052, WP-3, HCP-004).

No Node/npm/Rust/cargo required — these are regression tests for the exact
gaps a real `npm install && npm run tauri build` surfaced on real hardware
this session: missing SvelteKit config files, an icon set referenced but
never generated, `tauri.conf.json`'s `frontendDist` pointing at raw source
instead of the adapter's real build output, and `@tauri-apps/cli` assumed
resolvable without ever being declared.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
APPS = ["stream-extend", "creator-extend"]


def _app_dir(app: str) -> Path:
    return REPO / "apps" / app


def _package_json(app: str) -> dict:
    return json.loads((_app_dir(app) / "package.json").read_text(encoding="utf-8"))


def _tauri_conf(app: str) -> dict:
    return json.loads(
        (_app_dir(app) / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
    )


# ── required SvelteKit scaffold files ────────────────────────────────────

@pytest.mark.parametrize("app", APPS)
def test_required_sveltekit_files_exist(app: str) -> None:
    app_dir = _app_dir(app)
    for rel in ("svelte.config.js", "vite.config.ts", "tsconfig.json", "src/app.html"):
        assert (app_dir / rel).is_file(), f"{app}/{rel} is missing — SvelteKit cannot build without it"


# ── @tauri-apps/cli ───────────────────────────────────────────────────────

@pytest.mark.parametrize("app", APPS)
def test_tauri_cli_is_a_devdependency(app: str) -> None:
    """package.json's own `"tauri": "tauri"` script assumes this resolves
    via `node_modules/.bin` — it must be declared, or `npm run tauri ...`
    fails on a clean `npm install` alone."""
    pkg = _package_json(app)
    assert "@tauri-apps/cli" in pkg.get("devDependencies", {})


# ── frontendDist <-> adapter-static output directory ─────────────────────

def _adapter_output_dir(app: str) -> str:
    body = (_app_dir(app) / "svelte.config.js").read_text(encoding="utf-8")
    match = re.search(r"pages:\s*['\"]([^'\"]+)['\"]", body)
    assert match, f"{app}/svelte.config.js: could not find adapter's `pages:` output directory"
    return match.group(1)


@pytest.mark.parametrize("app", APPS)
def test_frontend_dist_matches_adapter_static_output(app: str) -> None:
    """Direct regression test for the real bug: `frontendDist` was `"../src"`
    (raw Svelte source) while adapter-static built to `build/` — a real
    `tauri build` bundles whatever's at `frontendDist`, so a mismatch here
    means shipping either nothing or stale/wrong content."""
    frontend_dist = _tauri_conf(app)["build"]["frontendDist"]
    adapter_dir = _adapter_output_dir(app)
    assert frontend_dist.rstrip("/").endswith(adapter_dir), (
        f"{app}: tauri.conf.json frontendDist={frontend_dist!r} does not point at "
        f"svelte.config.js's adapter output dir {adapter_dir!r}"
    )


# ── icons ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("app", APPS)
def test_every_referenced_icon_exists(app: str) -> None:
    """Regression test for the real bug: tauri.conf.json referenced 5 icon
    files plus a tray icon, none of which existed on disk — `tauri build`
    fails immediately on a missing bundle icon."""
    conf = _tauri_conf(app)
    src_tauri = _app_dir(app) / "src-tauri"

    icon_paths = list(conf["bundle"]["icon"])
    tray_icon = conf.get("app", {}).get("trayIcon", {}).get("iconPath")
    if tray_icon:
        icon_paths.append(tray_icon)

    assert icon_paths, f"{app}: no icons declared to check"
    for rel in icon_paths:
        assert (src_tauri / rel).is_file(), f"{app}: referenced icon {rel!r} does not exist on disk"


# ── lockfiles / gitignore ─────────────────────────────────────────────────

def _tracked_files() -> set[str]:
    import subprocess

    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return set(out.splitlines())


@pytest.mark.parametrize("app", APPS)
def test_lockfiles_are_committed(app: str) -> None:
    """HCP-004's acceptance text is 'Reproducible package install' — an
    uncommitted lockfile means every install can silently drift."""
    tracked = _tracked_files()
    assert f"apps/{app}/package-lock.json" in tracked
    assert f"apps/{app}/src-tauri/Cargo.lock" in tracked


def test_gitignore_excludes_build_artifacts() -> None:
    body = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert ".svelte-kit/" in body
    assert "target/" in body


# ── version consistency ───────────────────────────────────────────────────

@pytest.mark.parametrize("app", APPS)
def test_version_numbers_agree(app: str) -> None:
    pkg_version = _package_json(app)["version"]

    cargo_toml = (_app_dir(app) / "src-tauri" / "Cargo.toml").read_text(encoding="utf-8")
    cargo_match = re.search(r'^version\s*=\s*"([^"]+)"', cargo_toml, re.MULTILINE)
    assert cargo_match, f"{app}/src-tauri/Cargo.toml: no top-level version found"

    conf_version = _tauri_conf(app)["version"]

    assert pkg_version == cargo_match.group(1) == conf_version, (
        f"{app}: version mismatch — package.json={pkg_version!r}, "
        f"Cargo.toml={cargo_match.group(1)!r}, tauri.conf.json={conf_version!r}"
    )


# ── plugin config shape ───────────────────────────────────────────────────

@pytest.mark.parametrize("app", APPS)
def test_plugin_config_values_are_not_maps(app: str) -> None:
    """Regression test for a real runtime bug: tauri.conf.json's
    `plugins.notification`/`plugins.dialog` were `{"all": true}` (a map),
    but their real config schema expects unit (null) — the app compiled
    fine but panicked at startup with
    `PluginInitialization("notification", "... invalid type: map, expected unit")`.
    Only checks the plugins known to have no real config schema in this
    Tauri version; `shell`'s `{"open": true}` is a real, valid config."""
    plugins = _tauri_conf(app).get("plugins", {})
    for name in ("notification", "dialog"):
        if name in plugins:
            assert plugins[name] is None, (
                f"{app}: plugins.{name} is {plugins[name]!r}, not null — this exact "
                f"shape crashed the app at startup on real hardware, see this test's docstring"
            )
