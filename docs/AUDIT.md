# Open Content Creator Platform Audit

> **Status:** Living · **Last reviewed:** 2026-10-05 · **Owner:** OpenTechnology14

<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is a dated audit record, not a priority queue and not an authorization. Re-verify a finding before acting on it.
> Unresolved implementation becomes a row in [`PROPOSALS.md`](PROPOSALS.md); what then waits on a person goes in the
> [decision and run lanes](todo/README.md); a document that does not exist yet is tracked in
> [`FUTURE_DOCS.md`](FUTURE_DOCS.md).

**Audit date:** 2026-07-12
**Scope:** repository content, setup paths, desktop apps, APIs, cloud relay, scenario tests, documentation, and open-source readiness.


**P-063 audio setup assistance, 2026-10-04:** both apps include a parameter-free native
routing-tool presence check, bundled platform references and off-air acceptance guidance.
Standard-location evidence does not certify an active device, routing, levels or OBS hotkeys.
The reference follow-up corrected an output-only device assigned as Discord input and
conflicting full-mix/isolated recording track instructions; both regression tests failed before
the corrections and pass after. The custom VoiceMeeter XML and macOS JSON are reference templates,
not accepted native import presets. Native panel click-through is blocked by the locked Mac;
physical audio and Windows/Linux acceptance remain open. Audio Production remains scaffolded.
See [P-063 evidence](PROPOSALS.md#p-063--open-apps-first-and-extend-in-app-setup).

## Executive verdict

The repository is **not ready for a public production release**. It is suitable as an architecture/scaffolding preview if the README labels unfinished capabilities honestly. A public alpha becomes reasonable after the P0 release gates below are closed.

The strongest asset is the modular, local-first architecture and its written roadmap. The largest risk was the mismatch between product claims and executable evidence — ~~`TESTING.md` describes 126 scenarios, but `tests/` has no automated suite; CI contains a placeholder test step~~ **closed 2026-09-02**: `tests/` now runs 1000+ cases across every module (`make test`, unconditional in CI — see the Automated scenario suite row below), and CI's pytest step has no placeholder or skip condition. ~~Both desktop apps lack a complete build scaffold~~ **closed 2026-09-02** (`P-052`, `P-001` WP-3): both now build and bundle for real. ~~The OBS/ComfyUI command logic inside those scaffolds was stubbed~~ **closed by P-054/P-055**; P-063 now also supplies prerequisite detection, fixed OBS and Docker Desktop installation/launch actions, Docker/WSL classification, selected local service startup, fixed storage/workflow initialization, WebSocket diagnostics and bounded recording evidence. Real Docker initialization and hardware picture/audio acceptance remain open. Several critical service paths remain owner-only decisions (`D-01`, `P-001`). ~~ruff is still advisory (`|| true`)~~ **closed 2026-09-02** (`P-001` WP-1): the 4 known unused-import errors were real and fixable, not permanent — fixed, and `ruff check` is now blocking in CI and `make lint`.

## Verified evidence

**P-066 local personality audio, 2026-10-02:** The full authoring/review and manual scripted-Q&A
implementation is built in existing modules and Stream Extend. It includes resolved persona
prompts, installed Ollama phrase generation, native PCM previews, immutable revision feedback and
approval checks, local selection/rollback, one clip-or-live-voice route per reaction, and a separate
operator-approved script/pause/answer/resume cursor. The real Mac smoke generated four WAVs with
`qwen2.5-coder:7b` in 20.329 seconds; those files were neither approved nor played. Focused contracts
and desktop builds pass; native Mac inspection reached the studio catalog and prompt controls.
The [P-066 evidence record](proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md#implementation-verification--2026-10-02)
records the final resumed checks. Manual OBS file/hotkey/Stop All/correct-track recording, audible
isolation and native Windows acceptance remain open. The app cannot automatically import Soundbox
files; its script player is operator-controlled, not scheduled/chat-driven. No production approval,
broadcast, external publication or module-status promotion is implied.

**P-065 recording handoff and profile workspaces, 2026-09-20:** Stream Extend now owns a
bounded live session: it starts recording before streaming, rolls back a recording it started if
stream startup fails, stops streaming before recording, and registers OBS's finalized local path
for Creator Extend. It does not stop or claim a recording that was already active. A shared locked,
atomic local library deduplicates canonical paths without copying or uploading media; Creator Extend
can list, import, assign, reveal, mark and archive those recordings. Both apps persist independent
active Stream/Content profiles and remember each profile's brand, provider, capability and selected
connected account. Native macOS inspection showed the always-visible switchers, Main Content ↔
Video Review and Main Stream ↔ Agent Game Labs transitions, detailed routing selectors and the empty
Creator recording inbox. Three recording-library tests, four Social Manager tests, twenty Stream
Rust tests, thirty-seven Creator Rust contracts (one explicit live test ignored), nineteen focused
Python/desktop contracts, both Svelte checks/builds and the full offline suite pass. Real OBS
picture/audio/finalized-file acceptance, OS reveal on both platforms, native Windows UI and real
provider credentials/actions remain open; no external broadcast, upload or post was created.

**P-062 Social Management, 2026-09-10:** a new shared module defines five starter Stream/Content
identities plus validated private profile CRUD, four preloaded brand assets including OpenTechApp,
and fifteen providers with explicit available, registration-required, or planned states. Its
loopback picker, scoped OAuth/PKCE sessions, account verification, OS credential vault boundary,
redacted connection ledger, and approval-gated YouTube/Twitch/X/Discord adapters pass fifteen
focused offline tests. A shared native Social tab now compiles the catalog and logos into both
Tauri apps, starts the fixed loopback service from the isolated module environment, launches browser
consent, and shows redacted connections; two shared Rust tests pass. Both native Mac apps rendered
the correct default identity/logo; Stream Extend also rendered OpenTechMarketing/OpenTechApp,
enabled Discord, and visibly disabled planned Kick. No provider account was
connected and no post, upload, or live destination was created, so the module remains scaffolded.


**P-056 production-path extension, 2026-09-09:** Audio Production now has a bounded continuous
native speech/playback worker with generation-safe cancellation and exact playback events;
Character / Avatar drives VTube Studio Talk/Idle hotkeys from those events. Backend API has an
optional Twitch EventSub chat ingress with fixed subscription/reconnect handling. Automation /
Control has a production driver that owns the fixed host/director/speech/avatar/chat process set,
kills speech first on pause and keeps applied effects, Twitch, avatar and broadcast launch disabled
in committed config. Twenty-four focused tests pass. A real MacBook utterance was canceled during
audible playback in 0.0029 seconds with no false finish or retained WAV. No backend/OBS/VTube/
Ollama services or Twitch credentials were available, and native Windows playback/process-tree
acceptance is still gated. Twenty-four focused tests, the complete offline suite, full Python lint, diff checks and the Stream Extend Rust bundle contract pass. P-056 and affected modules remain In progress/scaffolded.

**P-057 Creator workflow inputs, 2026-09-08:** Creator Extend now has Configure controls for
images/masks, prompts and seeds, with backend validation and non-overwriting ComfyUI uploads.
Live desktop inspection found empty workflow lists outside the repository; curated JSON is now
bundled into the app and a regression test fails with the old loader. Mac UI verification
confirmed ten listed workflows, editor display, rejected negative seed and native file upload.
A real local ComfyUI CPU acceptance run uploaded a synthetic image, queued LoadImage → SaveImage,
observed completion and read back a 32×32 PNG. The completion slice then ran the installed SDXL
inpaint model through the rebuilt native UI on Apple Metal, completed in 40.37 seconds and showed
its 32×32 PNG preview in Output history. Native Windows acceptance remains open.
The completion slice now discovers output references from ComfyUI history, validates and streams
up to 8 MiB per preview, supports image/video previews, and retains twenty completed jobs for the
current app session. The same retrieval path passed against the real local ComfyUI; the rebuilt
native Mac app displayed the unlocked workflow catalog and Output history panel.
See [workflow input setup](../modules/content-creation/setup/workflow-inputs.md).

**P-003 desktop module setup, 2026-09-08:** both apps now have a shared module picker,
three profiles, saved per-app selections, shared isolated Python installs, progress/history,
bundled manual guides and fresh dependency/application checks. Native Mac UI acceptance
installed Audio Production dependencies, retained manual Soundboard steps, confirmed saved
choices after restart, reused the environment from the other app and expanded required modules.
The existing dashboards remain accessible. Checks explicitly distinguish package/app presence
from live service and full capability readiness. Nineteen setup tests and four shared-plugin
Rust tests pass; both app Rust suites pass (Creator 26, Stream 12). Full offline suite exits 0.
Persistent OBS/ComfyUI/MinIO connection settings and OS credential-manager storage were added
next and native Mac save/restart/redaction/clear flows passed. Native Windows acceptance, full
capability gating and OpenTechnology readiness synchronization were still open at that point. P-058 provides
approval-gated desktop relay control. See [desktop setup](../modules/infrastructure/setup/desktop-setup.md)
and the P-003 proposal's recorded verification.

The next P-003 slice adds a Windows PowerShell bootstrap and bundled capture-device diagnostics.
The bootstrap owns Python installation, optional OBS/FFmpeg winget installation, explicit module
presets, readiness checks and a capture report. Both apps can scan and save a discovered local
video/audio device. Native MacBook acceptance found OBS, the built-in camera and microphone and
restored saved choices after restart. PR #41 then passed the PowerShell plan and capture CLI on a
native Windows GitHub runner. A physical capture card, real OBS recording, fresh-host winget
installation and Windows desktop UI/hardware pass remain unverified.

The next P-003 slice adds `scripts/setup/windows.ps1` for Python/bootstrap automation, optional
winget OBS/FFmpeg installation, explicit module presets and a retained capture report. Both apps'
setup panel now bundles the same DirectShow/AVFoundation scanner and persists only devices from
the latest scan. Device enumeration is not a recording pass; native Windows and physical capture
card acceptance remain open.

**P-003 shared readiness completion, 2026-09-09:** both apps now use one versioned, config-owned
native readiness contract. Authenticated service probes calculate capabilities, stale evidence
expires, and the real Stream/Creator controls consume those capability states. Optional outbound
OpenTechnology synchronization sends sanitized idempotent events to the existing authenticated
setup-event receiver while the API key stays in the OS credential manager. Seven shared-engine
tests include exact loopback HTTP and expiry coverage; app Rust/Svelte suites and the full offline
suite pass. Native Mac UI acceptance rendered the contract and blocked OBS controls from real
disconnected evidence. Physical Windows/hardware and live hosted companion acceptance remain.

**P-056 Windows test readiness, 2026-09-08:** a native Python installer/doctor/rehearsal now
works on the Mac and includes a Windows System.Speech adapter, explicit timezone dependency
and Windows/macOS CI workflow. All 72 focused tests pass; the actual Mac rehearsal produced
speech, 28 draft episodes and three verified vertical clips. Native Windows execution and the
CI workflow have not run; whole-platform Windows support is not certified by this change.
See the [Windows test guide](../modules/ai-agents/stream_host/WINDOWS_TEST.md).

**P-056 creator-show extension, 2026-09-08:** catalog now contains 35 options across twelve games,
including three tutorial/workshop pairs with shared operator-maintained project briefs. GTA VI
is deferred and validation prevents scheduling it. Real CLI produces 28/56 draft episodes with
creator metadata; 31 focused tests pass, full `make test` exits 0 and Ruff 0.6.4 passes. No editor
resume, project saving, commercial listing or live host context injection has been implemented.

**P-056 profile expansion, 2026-09-10:** the version 2 program contains 45 options across
fourteen games and two non-game subjects. Five policy profiles cover experimental Microsoft Flight
Simulator 2024, BeamNG.drive and private Roblox controller labs plus `OpenTechMarketing` and
`VideoReview`. Planner validation binds each show to its expected profile/persona/subject. The
YouTube plan compiler accepts only configured sources and existing local media, requires rights
confirmation for reviews, limits visibility to private/unlisted and always reports upload disabled.
All 37 focused host/planner tests pass and a real 28-day CLI export reaches all sixteen subjects
and five profiles. A real OpenTechMarketing plan remains private, awaiting approval and has upload
disabled. The full offline suite reaches 100% with exit 0; Ruff and diff checks pass. No
game-control or YouTube upload adapter was implemented or accepted live; affected modules remain
scaffolded.

**P-056 programming extension, 2026-09-08:** Nova now has twelve inherited game variations and a
29-concept catalog. Draft planner CLI produces 28/56 episodes; all twelve games are represented.
The gameplay handoff contract is tested for input release acknowledgement and stale operations,
but no real input adapter/operator controls are installed. Content Creation's local Shorts CLI
selected and rendered three synthetic-recording clips; browser review/export retained an exact
manual section and a second real render produced the reviewed clips. All outputs are 720×1280;
no upload occurred. Combined focused tests: 60 passed; full `make test`: exit 0; Ruff 0.6.4 clean.
See [P-056](proposals/PROPOSAL_STREAM_AUTOPILOT.md) for commands, artifacts and live limitations.
Recording-completion/chat ingress, durable daily launch and live takeover remain unimplemented;
all affected module statuses remain scaffolded.

**P-056 lifecycle extension, 2026-09-08:** Automation / Control now has a durable session
supervisor for preflight, preview, running, pause, resume, emergency stop and stop. Required
capability failures, explicit live-start authorization, concurrent-session limits and bounded
idempotency history fail closed. A restart converts an active saved session to preview and marks
it for operator review instead of resuming. Eight focused tests pass, the real no-effects CLI
rehearsal ends stopped without starting a broadcast, and the bundled Stream Extend view completed
that rehearsal on the MacBook display. This is lifecycle/UI evidence only: the production driver
that owns actual host/director/audio/avatar/OBS/game processes remains unimplemented.

**P-056 advanced Shorts editing, 2026-09-08:** Content Creation now renders supplied timestamped
captions, validated brand colors/text, event-linked punch-ins and loudness-normalized audio through
the existing local FFmpeg pipeline. The 11-stage MacBook smoke run produced three 720×1280 clips
with three captions and two punch-ins; an additional 8-second render was visually inspected and a
silent-source render passed. Twenty-one focused tests, full `make test`, Ruff and `git diff --check`
pass. Caption/punch-in cues are supplied rather than inferred; transcription, subject tracking,
real-stream phone review and publishing remain open.

**P-056, 2026-09-08:** the new AI Agents `stream_host` worker and Audio Production speech exporter
have 21 focused passing tests, a real local CLI rehearsal, and a real 1.829-second synthesized
WAV. This establishes session/persona/queue/cancellation behavior and file synthesis only.
Live platform chat, Ollama inference, backend integration, continuous speech, body/avatar/OBS
rendering, gameplay and cloud VM execution remain open. No module status is promoted. See
[P-056](proposals/PROPOSAL_STREAM_AUTOPILOT.md) for exact paths, checks and remaining scope.

**P-056 director extension, 2026-09-08:** Automation / Control now has an event-driven integration
worker for existing soundboard slots/hotkeys, OBS scenes and voice mute, NodeCG lower thirds and
optional n8n triggers. File preview consumes real host CLI output. Protocol/behavior tests cover
the bindings; live OBS discovery at port 4455 returned connection refused. Audible soundboard
playback, visual NodeCG output, live mute/scenes and actual n8n workflow execution remain unverified.

| Check | Result | Evidence |
|---|---|---|
| Python parse check | Pass | 50 Python files parsed without syntax errors |
| Automated scenario suite | ~~Fail~~ **Fixed 2026-09-02** | ~~`tests/` contains no tests~~ — `make test` runs 1000+ cases across every module plus a 9-step acceptance-harness scenario suite (`tests/acceptance/`, `P-016`); CI runs it unconditionally on every push |
| CI enforcement | ~~Partial~~ **Full, 2026-09-02** | Pytest is unconditional and required (`P-016`); ruff is now blocking too (`P-001` WP-1) — no more `\|\| true`, and the 4 known errors it was hiding are fixed |
| Desktop app completeness | ~~Fail~~ **Build and command paths fixed, 2026-09-02 through 2026-09-13 (`P-052`, `P-054`, `P-055`, `P-063`)** | ~~Missing Svelte/Vite/TypeScript build configuration and stubbed OBS/ComfyUI actions~~ — both apps build and bundle, the command paths have contract coverage, and setup includes Python/FFmpeg/OBS/Docker Desktop prerequisite actions, selected local services, migrations, buckets, selected workflow import, and Creator-side ComfyUI node/model/VRAM preflight before queueing. Native Windows prerequisite failure/recovery, real Docker initialization, real OBS hardware recording, live Creator preflight and clean-host Creator output remain acceptance gaps. |
| Setup design | Proposed | `docs/proposals/PROPOSAL_SETUP_READINESS.md` specifies the contract, UI, checks, and injection points |
| Secret hygiene (working tree) | Partial pass | No high-confidence secret found outside ignored `.env`; history could not be audited because this checkout has no `.git` metadata |
| Environment contract | ~~Fail~~ **Fixed 2026-09-01** | ~~Six Compose-referenced values are absent from `.env.example`~~ — verified 2026-09-01 (P-035): every `${VAR}` `docker-compose.yml` references now has a matching entry in `.env.example`, confirmed by diffing the two files directly, not re-asserted from this row |
| Cloud-safe defaults | ~~Fail~~ **Fixed 2026-09-02 (`P-050`)** | ~~Weak fallback secrets, broad CORS, and public database/cache port mappings remain~~ — the relay now fails closed on a weak `RELAY_JWT_SECRET`/default DB URL in production, Postgres/Redis ports are `127.0.0.1`-only, CORS lists real Tauri origins instead of `*` |
| License/governance | ~~Fail~~ **Partially fixed, 2026-09-02 (`P-046`)** | `CONTRIBUTING.md`/`SECURITY.md`/`CODE_OF_CONDUCT.md` all exist with real content. Root `LICENSE` is still missing — blocked on `D-01`, an owner decision |
| Container/Rust validation | Blocked | Docker and Cargo were unavailable in the audit environment |

## P0 release gates

1. Select and add a root license. If the intended license is BSL with a future Apache conversion, describe the project as source-available until the conversion; do not call it OSI open source.
2. Replace placeholder CI with enforced lint, unit, API, scenario, and build jobs.
3. Add executable setup and service-readiness scenarios for fresh install, missing dependency, invalid credential, offline local mode, retry, and recovery.
4. Complete or clearly feature-flag unfinished Stream Extend and Creator Extend paths.
5. Remove production fallback secrets, restrict cloud port exposure, and replace credentialed wildcard CORS.
6. ~~Synchronize `.env.example` with every Compose variable.~~ **Done 2026-09-01** (P-035) — see the
   Environment contract row above.
7. Prove a clean clone can build and run the supported alpha path.

## P1 gates

- Add versioned setup/status endpoints and connect both desktop apps to the same contract.
- Add an OpenTech companion template and an opt-in ingestion bridge; no local media path or secret may be sent.
- Publish support, compatibility, privacy/data-flow, backup, and vulnerability-reporting documentation.
- Add dependency and secret scanning to CI.
- Validate macOS and Ubuntu setup paths; document Windows status explicitly.

## Scope limitations

This was a repository audit, not a live GPU/OBS/ComfyUI acceptance test. Docker, Cargo, hardware capture, and DigitalOcean deployment were not available. Those items remain unverified rather than assumed broken or working.
