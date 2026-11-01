# Stream — decisions, runs and testing

> **Status:** Living · **Last reviewed:** 2026-10-04 · **Owner:** OpenTechnology14

**Enforcement: reference.** Row format, IDs, states and the intake rule are in the
[lane index](README.md). Every row names its canonical proposal; **the proposal wins** when the two
disagree. Nothing here authorizes work — [`../PROPOSALS.md`](../PROPOSALS.md) does.

**Scope.** Owner decisions, **live runs and testing** for streaming: accounts and handles, capture
hardware, the games, autonomy permission, live acceptance, performance gates, native Windows
acceptance and the kill switch. Turning a finished recording into content is the
[content lane](CONTENT_CREATE_TODO.md). The procedures these rows point at are the two production
setup guides — [Stream Extend](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md) and
[Creator Extend](../guides/production-setup/CREATOR_EXTEND_PRODUCTION_SETUP.md) — and the games
authority is [`../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md`](../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md).

**Nothing has been purchased, and no proposal records a live stream, upload or external post made
through this platform** (P-062 and P-065 say so explicitly). Every number elsewhere in the docs —
frames per second, latency, upload — is an estimate or a target until a row here records a
measurement.

## Next three

1. **ST-R01 — enable the OBS WebSocket server and run `make test-obs`.** Five minutes, and it
   unblocks every other OBS-dependent row. P-001 describes it as an owner action rather than more engineering.
2. **ST-D01 — reserve the three handles.** The three-account model is decided; the names are not.
   Every platform, OAuth and branding step is downstream of it, and a rename later orphans every
   link and VOD reference.
3. **ST-D02 — buy the capture card.** One $159.99 line item gates every Xbox-routed title. Nothing
   else needs buying yet.

## Awaiting acceptance

**None.** `P-066` was the only stream-lane proposal waiting on the owner. It was accepted on
2026-09-30 and is `In progress`; its row (`ST-A01`) is in the [Resolved](#resolved) log, and what is
left of it is `ST-D18`, `ST-R13` and the Windows rows below.

P-056 is `In progress` and needs no acceptance; its open items are ST-D06 and ST-D09–ST-D14 below.

## Decisions

### Accounts and platforms

| ID | Decision | Source | Blocks | Default if unanswered | State |
|---|---|---|---|---|---|
| ST-D01 | **Reserve three handles** — Games, Reactions, OpenTechnology: three candidates each, checked on every surface that account uses, then all claimed in one sitting. Constraints: 3–20 characters; letters, digits and one underscore (Roblox's rules are the narrowest); a shared root with a clear suffix **Question:** What three handles will you claim for Games, Reactions and OpenTechnology, sharing one root with a clear suffix? | [Stream guide §3.0](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#30-reserve-three-handles--do-this-before-installing-anything); P-067 §1.6 | ST-R02; every OAuth connection; CT-R08 | None. The three-account **model** was decided 2026-09-22; the **names** were not | open |
| ST-D03 | Add a **live-capable Reactions profile** to `catalog.yaml`? It has none — `video-review` is a private staging identity **Question:** Add a live-capable Reactions profile to the catalog? | P-067 §14 Q6; [guide §3.1](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#31-the-three-tracks); [`catalog.yaml`](../../modules/social-management/catalog.yaml) | Going live as Reactions under the right profile; CT-R07's publish path (not its render) | Add it — a compiled-catalog change with its own queue row. Until then run Reactions through `stream-main` and fix the content profile by hand in the inbox | open |
| ST-D04 | Multi-cast with `obs-multi-rtmp` (free, no added latency) or Restream (paid, +200–500 ms)? Decide **after** `networkQuality -v` shows sustained upload of at least 20 Mbps **Question:** Once upload is measured at 20 Mbps or more, multi-cast with the free plugin rather than paid Restream? | [guide §3.3](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#33-youtube--multi-cast); [`multi-platform.md`](../../modules/creator-experience/obs-config/multi-platform.md) | Any two-platform go-live | `obs-multi-rtmp` | open |
| ST-D05 | Final **account ownership, profile naming and default publication visibility** **Question:** Confirm account ownership, profile names and the default post visibility, given the catalog already defaults two destinations to private? | P-062 §12 | P-062 → `Done` | None stated. The catalog already defaults two destinations to private | open |
| ST-D13 | Streaming platform and language **Question:** Confirm Twitch as the first streaming platform, and say which language the streams use? | P-056 §12 | Chat adapter and persona requirements | Twitch first, per the current assumption; P-056 does not state a language. Largely settled by the guide | open — confirm |

### Hardware

| ID | Decision | Source | Blocks | Default if unanswered | State |
|---|---|---|---|---|---|
| ST-D02 | Buy the **Elgato Game Capture 4K S** ($159.99). First check Elgato's page for the current macOS version and USB requirements — the evaluation lists M1 or better but flags those as yours to verify **Question:** Buy the Elgato Game Capture 4K S for $159.99, after checking its current macOS and USB requirements? | [Games evaluation § under-$1,000 envelope](../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md); [guide §2.2](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#22-what-to-buy-now--one-line-item) | Every Xbox-routed title; ST-R04 | Buy it, and nothing else | open |
| ST-D08 | **Tower purchase gate.** Only after the Xbox pilot passes one complete local recording with synchronized voice, avatar, chat and Soundbox. Planned ceiling $949.99; **nothing purchased**; the evaluation found no purchasable $650 machine and claims none **Question:** Agree not to buy the tower until the Xbox pilot passes one complete local recording? | Games evaluation § staged capacity | Any desktop-hosted game; ST-D07 | Defer | open — gated by ST-R04 |
| ST-D07 | **Which physical Windows host performs native acceptance?** P-003, P-057, P-058, P-062, P-063, P-065 and P-066 all list native Windows acceptance as open, and **no proposal names a machine**. The planned tower would be the obvious candidate but is gated on ST-D08 **Question:** Which physical Windows machine will run native acceptance? | The seven proposals above — *new, found while organizing; P-066 added 2026-10-04* | ST-R17; ST-T11; CT-R12 | None | open |
| ST-D11 | **Reference workstation** — OS, GPU, VRAM — and the intended session count. "Benchmark the target machine; do not infer hardware from historical docs" **Question:** What operating system, GPU, VRAM and session count define the reference workstation? | P-056 §12 | **Every performance gate** (ST-T07) | None | open |

### Games and autonomy

| ID | Decision | Source | Blocks | Default if unanswered | State |
|---|---|---|---|---|---|
| ST-D06 | **Minecraft autonomy: write the one-sentence permission** — which rule you are relying on (your own server and world, under Mojang's terms). If you cannot say it in one sentence naming the permission, the answer is no **Question:** Can you name, in one sentence, the rule that lets an agent play Minecraft unattended on your own server? | [guide §4.1.1](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#411-minecraft-java--the-first-autonomy-target); P-056 §12 | Any unattended autonomy run (ST-R12) | No | open |
| ST-D09 | Co-host first, or gameplay first? **Question:** Finish one co-host path first, then add a single permitted gameplay adapter? | P-056 §12 | Gameplay implementation | The recorded lean: manual Xbox play plus autonomous desktop streams — finish one host path, then one permitted gameplay adapter. Confirm | open — confirm |
| ST-D10 | Real performer or synthetic host; realistic or stylized **Question:** Use the original VRM avatar as a synthetic host baseline, rather than a real performer? | P-056 §12 | Avatar integration | The original VRM is the proposed baseline | open — confirm |
| ST-D12 | One broadcast switching between games, or separate broadcasts? **Question:** Run three independent streams rather than one broadcast that switches between games? | P-056 §12 | The multi-session phase | The recorded lean: three independent streams, with runtime ownership isolated per stream | open — confirm |
| ST-D14 | New top-level module, or a nested coordinator? **Question:** Keep Stream Autopilot as a nested coordinator rather than a new top-level module? | P-056 §12 | Creating any top-level module | Nested coordinator | open |
| ST-D15 | **Roblox: shortlist two or three specific experiences** — name and creator. Experiences vary substantially, and a clip from the wrong one reaches a young audience **Question:** Which two or three Roblox experiences, by name and creator, are appropriate to record? | [guide §4.1.2](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#412-roblox) | ST-R03's Roblox pass | None | open |
| ST-D16 | Rename `rook-tactician`, `lux-commentator` and `ember-storyteller` to `nova-*` — their prompts all say to keep Nova's identity **Question:** Rename rook-tactician, lux-commentator and ember-storyteller to nova-prefixed names? | P-067 §14 Q8; §7.6 | Nothing — pure clarity | Rename with the registry | open |
| ST-D17 | Flight Simulator: register a 14th game profile, or drop it? Marked experimental; the adapter is not built **Question:** Register Flight Simulator as a fourteenth game profile, even though its adapter is not built? | P-067 §14 Q7 | Registry completeness | Register it — one config file | open |
| ST-D18 | **Align each gaming personality's production prompt and sound.** Audition the generated phrases in Stream Extend → Automated streaming → Personalities → Prompt & Voice Preview, edit the prompt, then approve an exact revision or reject it. The implementation does not approve creative output on the owner's behalf **Question:** Will you audition each gaming personality's generated phrases and approve or reject its prompt revision? | P-066 §Prompt, audition, alignment and improvement; §9 (last row) | ST-R13; any on-air use of a generated clip | Nothing is approved; the feature stays opt-in and off air | open |

## Runs

Live runs, ordered by what unblocks the most. **Proof** uses the
[lane index](README.md#row-format) vocabulary. Record the numbers each run produces — the games
evaluation requires edition and build, OS, hardware, resolution, preset, capture path, average FPS,
1% lows, memory use, OBS rendering and encoding lag and audio sync, *and failures too*. Until
recorded, a game's row stays `pending` however well the session felt. There is no evidence log yet
(`FD-12`); record them in the owning proposal, per the
[documentation workflow](../DOCUMENTATION_WORKFLOW.md).

| ID | Run | Proof | Needs | Source | State |
|---|---|---|---|---|---|
| ST-R01 | **Enable OBS WebSocket** (Tools → WebSocket Server Settings), then `make test-obs` | **live** | OBS installed | P-055; P-001 WP-5; [guide §1.1](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#11-obs-studio--the-one-non-negotiable-dependency) | **still open** — 2026-10-12 P-001 reran the pinned client: connection refused on configured local port 4455. Native UI access later became available; flag-only config confirms server disabled, port 4455, authentication required. Enabling the control listener and real OBS acceptance remain owner/testing actions. |
| ST-R02 | **Connect real accounts** through Social: Twitch `live-stream`, YouTube `live-stream` and `post-video`; the switcher must read `account routed` | **live** | ST-D01; the YouTube Data and Live Streaming APIs enabled; a Twitch developer app | [guide §3.2–3.4, §6.3](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#63-connect-accounts); P-062 | blocked by ST-D01 |
| ST-R03 | **A local recording of each Mac game.** Minecraft with settings pinned; Roblox with a **two-experience join** and no black frames at the join; Dota 2 as a **40-minute bot match** recording average FPS, 1% lows and OBS rendering and encoding lag | **live** | ST-R01; ST-D15 for Roblox | [guide §4.1.1–4.1.3](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#411-minecraft-java--the-first-autonomy-target); games evaluation § acceptance | **ready** for Minecraft; Roblox waits on ST-D15 |
| ST-R04 | **Xbox pilot.** Connect the Elgato (1080p60 SDR; HDR and 4K off); run `scripts/setup/capture_devices.py`; record 60 seconds with synchronized audio; then the Series S Minecraft and Overwatch capture | **live** | ST-D02 | [guide §4.2](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#42-xbox--windows-tower-routing); games evaluation § first tests | blocked by ST-D02 |
| ST-R05 | **Mid-stream profile-switch test** with real profiles — the nine-step table — ending in `Recording … is ready in Creator Extend` and a correctly attributed inbox row | **live** | ST-R02, ST-R03 | [guide §6.4](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#64-the-mid-stream-profile-switch-test); P-065 | blocked by ST-R02 |
| ST-R06 | **Handoff reveal acceptance**: Finder *Show in folder* on the Mac (Windows later) and the registration-failure recovery path — a recording on a non-local volume, then manual import | **manual** | ST-R05 | P-065; [guide §10.6](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#106-handoff-to-creator-extend-fails) | blocked by ST-R05 for full scope; owned synthetic manual-import/Finder reveal passed on Mac 2026-10-11 (P-065); automatic handoff/non-local-volume path remains open |
| ST-R07 | **Private dry run per game and profile** — the §8 checklist, about 20 minutes each. Re-run whenever a game, profile, overlay, AI-gen mode, capture hardware or app version changes. Track results in the [drill ledger](#private-drill-ledger) below | **live** | ST-R05 | [guide §8](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#8-private-test-stream-dry-run) | blocked by ST-R05 |
| ST-R08 | **First public go-live** | **live** | ST-R07 for that exact game and profile; ST-D04 if multi-casting | [guide §9](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#9-public-go-live-checklist) | blocked by ST-R07 |
| ST-R09 | **Air AI Learning lesson 1**: rehearse off-air with the task pre-run once; stream through Stream Extend; capture; then CT-R09 | **live** | ST-R08; CT-D11; CT-D12 | P-064 §10 Phase 2; [learning README](../learning/README.md) | blocked by ST-R08 |
| ST-R10 | **The 60-minute integrated recording gate**: voice, avatar, chat and Soundbox together, no cross-session speech, no sustained OBS rendering or encoding lag above 1%. Capture input and output timestamps and the hardware configuration with the result | **live** | Real Twitch, backend, VTube Studio, OBS and game bindings; ST-D11 | P-056 §3 | blocked by ST-D11 |
| ST-R11 | **Real chat on an operator test channel** — the correct persona speaks, with caption and lip timing | **live** | ST-R02; ST-R10's bindings | P-056 §9 scenario A6 | blocked |
| ST-R12 | **Minecraft permitted-environment autonomy run.** Bounded private-world adapter built; no real game run | **live** | ST-D06; private test server, observer/capture and dedicated bot identity | P-056 §12; guide §4.1.1 | blocked by ST-D06 |
| ST-R13 | **Astra on one real OBS install**: import the approved WAVs into Soundbox, enter the exact play and Stop All hotkeys, then confirm one audible path, the correct track, monitor isolation and a local recording | **manual** | An approved revision (ST-D18); a connected, off-air OBS (ST-R01) | P-066 §Prompt, audition, alignment (steps 5–7); §9 | blocked by ST-D18 |
| ST-R14 | **Remote control on two real devices**, including a live OBS or ComfyUI approval and the hosted relay. Loopback acceptance on the Mac is already recorded; the hosted relay, a successful live approval, Windows and the live OpenTechnology companion are not | **live** | A second device or the hosted relay | P-058 | open |
| ST-R15 | **Provider actions with real accounts**: YouTube upload acceptance, approved live-destination actions, and OS credential storage with real tokens and webhooks. No external post, upload or stream has ever been created by this platform | **live** | ST-R02; ST-D05 | P-056; P-062 | blocked by ST-R02 |
| ST-R16 | **Export a real OBS scene collection and profile** to replace the placeholder in `creator-experience` — no script can produce one. The committed scene collection parses, and its eight scene names and order match the scenes README | **manual** | OBS configured the way you stream | P-027; [`test_scenes.py`](../../tests/creator_experience/test_scenes.py) | open — owner work |
| ST-R17 | **A clean physical Windows host**: the missing-prerequisite path, winget and the desktop credential manager, Docker and WSL initialisation, OBS picture and audio, live ComfyUI preflight and output, and Astra's native Windows speech and Personalities UI | **live** | ST-D07 | P-063; P-003; P-058; P-062; P-065; P-066 | blocked by ST-D07 |
| ST-R18 | **Combined-app remote acceptance:** legacy/new relay compatibility, denial, expiry and one approved OBS/ComfyUI action on two real devices | **live** | ST-R14 baseline; P-072 Phase 2 build; PL-D11 pairing policy | [P-072 §9 U-08](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#9-test-and-pressure-matrix) | blocked — combined app not built |

### Private drill ledger

[Guide §9.0](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#90-gate-the-private-drill-for-this-combination-has-passed)
requires a passed private drill for **each game and profile combination** before it goes public, and
asks you to keep a note of which have passed and when. This is that note. A row is added the first
time a combination is planned; a date is written only with evidence behind it.

| Game | Profile | Account | Private drill passed | Evidence |
|---|---|---|---|---|
| Minecraft Java, human-played | Main Stream (`stream-main`) | Games | not run | — |
| Minecraft Java, autonomy | Agent Game Labs (`agent-labs`) | Games | not run — gated by ST-D06 | — |
| Roblox | Main Stream | Games | not run — needs ST-D15 | — |
| Dota 2 | Main Stream | Games | not run | — |
| Lesson or product content | OpenTechMarketing (`opentech-marketing`) | OpenTechnology | not run | — |
| Try Not to Laugh / Nova Reviews the Edit | `video-review`, or `stream-main` with a manual destination until ST-D03 | Reactions | not run | — |

## Testing

OpenTechnologyApp's testing is two things this repo's is not: **built into agent work** — one
command that runs every gate CI runs, named in the agent instructions — and **on-demand audits** —
named, tiered commands with a capped log. Here the procedures are rich but advisory, and the
proposal for closing that is [`P-071`](../proposals/PROPOSAL_DOCUMENT_GAPS.md) §7. This table is the
inventory of what exists and what does not. A row's **Gap** is what stops it being repeatable.

| ID | Test | Proves | How to run today | Gap | Source |
|---|---|---|---|---|---|
| ST-T01 | Offline suite | Structure and contracts across every module. **Not** capability — `CLAUDE.md` §11 forbids promoting a module on it | `make test` — **auto** | None | [`VERIFICATION-MATRIX.md`](../agent/VERIFICATION-MATRIX.md) |
| ST-T02 | Rust contracts, including the fake-OBS WebSocket contract | Recording starts before streaming, stop returns the real path, an already-active recording is never claimed | `cargo test --locked --manifest-path apps/stream-extend/src-tauri/Cargo.toml`, and the Creator Extend equivalent — **auto** | None | [`obs_contract.rs`](../../apps/stream-extend/src-tauri/tests/obs_contract.rs); [`comfyui_contract.rs`](../../apps/creator-extend/src-tauri/tests/comfyui_contract.rs) |
| ST-T03 | Live OBS and creator-journey acceptance | A real OBS answers; the creator journey runs against real services | `make test-obs`; `make test-acceptance` — **live** | Never run on this machine (P-055). `make test-acceptance` currently fails in CI — see ST-T13 | [`test_creator_journey.py`](../../tests/acceptance/test_creator_journey.py) |
| ST-T04 | The end-to-end chain: record → inbox → clips → private publish → verify | The recording handoff and the content pipeline together | [Creator guide §8](../guides/production-setup/CREATOR_EXTEND_PRODUCTION_SETUP.md#8-test-end-to-end) — **live** | Procedure written, never executed. It is CT-R01 | P-065 |
| ST-T05 | Voice A/B and the mid-clip switch | The three account voices are recognisably one Nova | P-067 §7.5 and P-068 §6.1 — **manual** | **Rig built, runbook not.** `tts/audition.py` (P-068 slice 2) does the blind-order part; the procedure still lives in two proposals and is merged into one runbook nowhere (`FD-15`), and the mid-clip switch has no tool. It is CT-R02 | P-067; P-068 |
| ST-T06 | Profile switching with real profiles | Per-profile routing is restored on switching back | [guide §6.4](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#64-the-mid-stream-profile-switch-test) — **live** | Offline contracts pass; never run with real accounts. It is ST-R05 | P-065 |
| ST-T07 | **Performance gates** | p95 accepted-chat-to-first-audio ≤ 4 s; captions and mouth state within 150 ms of playback; local mute and pause acknowledged within 250 ms; a 60-minute recording with no cross-session speech and no sustained OBS rendering or encoding lag above 1% | None — **blocked** | **These are targets to measure, not claims.** No harness captures them and no baseline exists. Needs ST-D11 | P-056 §3 |
| ST-T08 | **Pressure matrix A1–A11** — message flood, profile switch mid-reply, prompt injection, audio unplugged, mute while synthesis hangs, real chat, two games, adapter loses connection, crash during creation, GPU saturation, unsupported game | The host degrades by name and recovers | Mixed, by P-056 §9's own levels — A3 and A11 offline; A1 and A9 integration; A2 offline plus live audio; A4 fault injection; A5–A7 live; A8 adapter plus live; A10 real hardware | **No document maps any A-row to a test file or a recorded result.** A table of A-row → test → result is missing | P-056 §9 |
| ST-T09 | **Kill switch**: stop, mute and session switching during speech and during a Soundbox clip | An operator can always stop the host | **manual**, live | Required by the games evaluation; never run | Games evaluation § acceptance |
| ST-T10 | **Failure drills**: capture-card unplug, OBS killed and recovered, ComfyUI saturated, chat flood | The recovery steps in the guide are real | [guide §10](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#10-failure-modes-and-recovery) — **manual**, live | Written, **never rehearsed** | P-056 §9 |
| ST-T11 | **Native Windows acceptance** | The desktop apps and setup work on a clean Windows host | **live** | Needs ST-D07. CI builds and opens both apps on Windows; that is not physical acceptance | P-003; P-057; P-058; P-062; P-063; P-065; P-066 |
| ST-T12 | **Remote control, two devices** | An approved remote request reaches OBS or ComfyUI | **live** | The hosted relay, a successful live approval and Windows are unverified. It is ST-R14 | P-058 |
| ST-T13 | **CI health on `main`** | The gates pass where nobody's laptop is involved | GitHub Actions — **auto** | **The billing block has cleared, and the first real run is red.** On 2026-10-03 both desktop-app builds **passed** (10–18 minutes each) but `lint-and-test` failed at `make test-acceptance`: `docker compose up -d` could not pull `quay.io/minio/minio:latest` (`unauthorized`) — see PL-D08. Every run on 2026-09-26 failed after about two seconds — the same signature as the billing annotation seen on 2026-09-22 — so the five PRs merged that day (#43, #45, #46, #47, #49) **never had a meaningful CI run** | CI run 37085017528 (private development evidence; not distributed) |
| ST-T14 | **Combined installer, vault migration and rollback on macOS/Windows** | Clean-host setup, beginner guided tasks/recovery, labelled folder navigation, single-pack selection without unrelated tool warnings, conflict/cancel/restart recovery and shared data surviving legacy uninstall | P-072 U-01/U-02/U-03/U-06/U-07/U-13 — **manual**, native; §5 beginner navigation refinement | Private Mac preview artifact now built; opening/pack/layout/inbox checks are ready after unlock. Full migration/rollback need later build, both OS hosts and PL-D10–PL-D12 | [P-072 §9](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#9-test-and-pressure-matrix) |
| ST-T15 | **Live-stream/render contention** | Measured stream stability and usable Stop controls during resource pressure or worker failure | P-072 U-05 — **live** | Needs PL-D10 budgets, OBS plus real ComfyUI/Blender workload and combined app | [P-072 §9](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#9-test-and-pressure-matrix) |
| ST-T16 | **Combined workspace switching and owned recording** | Switching to Create preserves the pinned live destination and owned recording; live status/mute/stop remain visible across collapsed folders and all pages; pre-existing recordings remain external and final handoff plays correctly | P-072 U-04 — **live**; §5 beginner/live-safety contract | ST-R05/ST-R06 baseline and later parity/session build; private preview has no broadcast/session controller; feeds CT-R15/CT-R16 | [P-072 §9](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#9-test-and-pressure-matrix) |
| ST-T17 | **Generated asset to broadcast overlay** | One real cross-workspace journey ends in the intended visible OBS graphic | P-072 U-09 journey 2 — **live** | Real generator/overlay/OBS setup; baseline before convergence, then repeat in combined app | [P-072 §9](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#9-test-and-pressure-matrix) |

## Resolved

Newest first.

| Date | ID / source | Resolution | Recorded in |
|---|---|---|---|
| 2026-09-30 | ST-A01 — P-066 acceptance | **P-066 accepted: the owner authorized the full build**, including the Stream Extend interface and operator-controlled script pause/Q&A that the proposal had deferred. The six open items the old row listed (its §13) are gone from the proposal; what remains open is ST-D18, ST-R13 and native Windows (ST-D07, ST-R17, ST-T11). Moved here 2026-10-04, when the build reached `main` | [P-066 §1](../proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md#1-executive-summary); [queue row](../PROPOSALS.md) |
| 2026-09-22 | Stream guide §4.1 | **Mac rotation: Minecraft Java, Roblox and Dota 2.** League of Legends and Fortnite (cloud) are deferred with a stated reopening condition; the Xbox and tower routing is unchanged | [Stream guide §4.1](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#41-the-mac-rotation--three-games) — owner message |
| 2026-09-22 | Stream guide §3.0 | **Three accounts**: Games (Twitch and YouTube Gaming), Reactions (Twitch and YouTube), OpenTechnology (YouTube only), each with its own handle, branding and About copy | Stream guide §3.0; P-067 §1.6 — owner correction |
| 2026-09-22 | Stream guide §3 | Gaming streams: Twitch plus YouTube multi-cast, leaving room for more platforms. OpenTechnology content: YouTube only | Stream guide §3.1 — owner message |

## Pointers to the other lane

Shared decisions that also set the live host's voice are owned by the content lane: **CT-D02,
CT-D03**. Items this lane waits on: ST-R09 waits on CT-D11 and CT-D12. Items waiting on this lane:
CT-R08 → ST-D01 · CT-R09 → ST-R09 · CT-R07 → ST-D03 · CT-R12 → ST-D07.
