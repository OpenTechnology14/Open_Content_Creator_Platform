# OBS scene collections

Commit exported `.json` scene collections here so we can roll back when a
scene change breaks something on-air.

## Export

OBS → Scene Collection → Export → save as
`hcp-<purpose>-YYYYMMDD.json` (e.g. `hcp-golf-20260518.json`).

## Import

OBS → Scene Collection → Import → pick the JSON.

## Commit convention

```
scenes(creator-experience): hcp-golf-20260518 — add replay scene + lower third
```

Do **not** commit `.bak` files, audio recordings, or anything that isn't
the bare scene-collection JSON.

> ⚠️ **`default.json` is a placeholder, not an export.** Its own `_comment` says so, and all eight
> scenes carry `sources: []`. Importing it gives you empty scenes with the right names — useful as
> a skeleton, not as a configured OBS. `../obs-config/profile.ini` is listed below as a deliverable
> and does not exist yet. Tracked as `P-027` in [`../../../docs/PROPOSALS.md`](../../../docs/PROPOSALS.md).

## Foundational scene structure

Create these in order, empty first — sources come later. `default.json` in this folder is the
exported collection of exactly this set.

| # | Scene | Purpose |
|---|---|---|
| 1 | Starting Soon | Pre-stream waiting room |
| 2 | Main Camera | Primary on-camera scene |
| 3 | Gameplay / Activity | Primary content scene |
| 4 | Intermission | Break / sponsor |
| 5 | BRB | "Be right back" |
| 6 | Ending | Outro |
| 7 | Vertical Output | 1080×1920 for shorts/reels, nested via Source Clone |
| 8 | Recording Sandbox | Automation and AI experiments, never live |

**Scene Collections** (File → Scene Collections) let multiple personas or shows coexist on one
workstation — use them rather than one sprawling collection.

The Recording Sandbox scene is not optional decoration: every other module that drives OBS
programmatically (automation-control, ai-agents, broadcast-graphics) should be pointed at it
first, so a broken automation cannot take your live scene down.

## What to commit

- `scenes/default.json` — exported scene collection
- `../obs-config/profile.ini` — exported OBS profile
- `../obs-config/plugins.md` — plugin list with pinned versions

`OBS_WEBSOCKET_PASSWORD` goes in `.env`, which is gitignored. Never commit it.

