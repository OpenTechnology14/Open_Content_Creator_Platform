# Setup technique notes

> **Status:** Living · **Last reviewed:** 2026-10-05 · **Owner:** OpenTechnology14

Friction you hit while actually standing a module up — the gap between what a setup doc says and
what the tool in front of you does. General notes live here; module-specific corrections belong in
that module's own `setup/manual.md` as a dated note (`DM-MODULE-DRIFT` in
[`agent/DOC-UPDATE-MATRIX.md`](agent/DOC-UPDATE-MATRIX.md)).

**Enforcement: reference.** Read before a Medium-or-worse module in
[`agent/MODULE-MATRIX.md`](agent/MODULE-MATRIX.md).

**Nothing here is a capability claim.** 17 of 21 modules are `scaffolded` (`CLAUDE.md` §11; 4 are
`implemented`: `storage-data`, `marketing-crosswalk`, `asset-pipeline`, `model-registry`); these
are notes about *setup*, not evidence that anything works.

---

## Port collisions

Two are already known and both bite silently — the service starts, and the wrong thing answers.

| Port | Wanted by | Resolution |
|---|---|---|
| **9090** | Prometheus **and** NodeCG's default | NodeCG is moved to **9091** in Compose. A manual `nodecg setup` outside Compose defaults back to 9090 and will fight Prometheus |
| **3000** | Grafana, and most Node dev servers | Grafana holds it in this repo; start a Node tool elsewhere |

Every root-Compose port binds `127.0.0.1`, not `0.0.0.0`. If you find a service reachable from
another machine, that is a defect, not a convenience.

## Order of operations

- **Open Stream Extend or Creator Extend first.** Follow the
  [desktop launch guide](../modules/infrastructure/setup/desktop-setup.md), then select capabilities.
  OBS and Docker/WSL blockers belong to their features; neither should prevent the setup view
  or Dashboard from opening. This supersedes the former `make up`-first instruction.
- **Start only the selected dependencies.** Use `make up` when a chosen workflow needs the
  container stack. Download large weights after choosing the workflow and checking compatibility,
  disk space and terms; they are not part of reaching the first app window.
- **Cityscape grading before curation.** Correct lens distortion and perspective *before*
  promoting images to `curated/`, or the adapter learns your lens.
- **Tone work last in a Tier 0 chain.** Distortion → perspective → rotation → crop → tone.
  Grading first means regrading pixels you then discard.

## Things that look broken but are not

| Symptom | Actually |
|---|---|
| `docker compose up` starts nothing new | You want a profile: `make up-with-graphics` or `make up-with-automation` |
| Grafana shows no data | Provisioned datasources loaded, but nothing is *emitting* yet. Most exporters need their module running |
| A ComfyUI workflow will not load | All 8 indexed `image-editing` workflows are on disk (`P-028`), and 5 are GPU-run verified working (`P-043`, 2026-09-02). If it's `auto-select-sam-v1.json`, that's a confirmed upstream `transformers` incompatibility in its node pack, not a config problem — see that `workflows/README.md`'s Status section |
| Krita has no AI Diffusion panel | Extracted to the resource root instead of `pykrita/`, or not enabled in the Python Plugin Manager — two separate steps |
| Agent has no memory across restarts | `make migrate` was never run. It **does** apply `0002_memory.sql` and the extensions — corrected 2026-08-31, this was documented backwards |
| `make test-obs` fails | WebSocket server off in OBS, wrong port, or the `.env` password does not match — check all three before assuming a code problem. If it says `install OBS dependencies first`, the client library is missing from that Python: install `scripts/setup/requirements-obs.txt` into a venv (Homebrew Python refuses a bare `pip install`) |
| `make healthcheck` or `make test` fails immediately on Windows | The targets assume `bash` and `python3` are on `PATH`. Install a POSIX Bash shell and ensure `python3` resolves to the installed Python interpreter; a Windows Store `python3` alias is not sufficient. |
| A Tauri desktop app fails with `os error 4551` while compiling Rust helpers | Windows Application Control blocked the generated build executable. Use an organization-approved policy or build location; do not bypass the control in a project script. |
| OBS launches to a responsive window titled `Error`, including `--safe-mode` | OBS never opens WebSocket port 4455 in this state. Read and resolve the visible OBS error first, then enable secured WebSocket and run `scripts/setup/test_obs_websocket.py`; do not disable WebSocket authentication to work around it. |

## Steps that currently need user participation

Named so they are budgeted rather than discovered. Repeatable installs and configuration should
move into versioned in-app recipes where supported, as planned in
[P-063](PROPOSALS.md#p-063--open-apps-first-and-extend-in-app-setup). Current manual instructions
are not a claim that automation is impossible. This list is the cost proxy behind
[`agent/MODULE-MATRIX.md`](agent/MODULE-MATRIX.md).

- **OBS:** encoder, video, audio, and filter-chain settings across four panels; scene-collection
  import; enabling the WebSocket server and setting its password.
- **Krita:** plugin file-copy into `pykrita/`, restart, then enable in the Plugin Manager.
- **VoiceMeeter / Loopback / PipeWire:** the routing matrix itself. The committed config files are
  importable, but importing is a GUI action, and mix-minus is wrong until it is right.
- **VTube Studio:** face-tracking calibration against your own webcam.
- **Grafana:** changing `admin/admin`. The container does not force it, and it is the credential
  most often left as-is.
- **n8n:** per-workflow credentials. The import script brings the graph, not the secrets.

## Colour-space traps

Both generation modules depend on this and both name it, because it is the most common way tone
work goes wrong:

- **Saturation in gamma-encoded sRGB shifts hue** — the "oversaturated photo goes orange" failure.
  Work in LAB or linear light.
- **Vibrance is usually what someone means by "more saturated."** Global saturation pushes an
  already-saturated sky to neon while barely moving muted foliage.
- **8-bit clipped highlights are gone.** No tier of any module invents them back correctly.

## Model weights

- **Never committed** (`CLAUDE.md` §10: nothing over 5 MB). They live in MinIO `models/`.
- **The tooling to record a manifest, checksum, and licence now exists** — `model-registry`
  (`P-018`, 2026-09-01) — but `registry.yml` itself still ships empty. If you download a weight and
  don't run it through `model_registry.cli`, nothing records which one you got; the gap is
  populating real entries, not the tool to hold them.
- **License-gated downloads cannot be scripted** even in principle — some require accepting terms
  on a web page.

## Adding a note

Add one when something has actually cost you time and is **not** specific to one module. If it is
module-specific, it belongs in that module's `setup/manual.md` as a dated correction instead —
that is the `DM-MODULE-DRIFT` split, and putting a module quirk here makes both docs worse.
