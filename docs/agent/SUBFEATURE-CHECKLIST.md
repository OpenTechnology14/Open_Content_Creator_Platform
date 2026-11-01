# Module subfeature checklist

**P-061 still-job update, 2026-10-09:** explicit local scene selection, durable results,
owned native cancellation/retry/restart reporting and real Blender PNG rendering are built.
See the [recorded verification](../proposals/PROPOSAL_BLENDER_PRODUCTION_JOBS.md#implementation-verification--2026-10-09).
Animation, optional batch upload, physical Windows and native/addon UI acceptance remain open;
no module status changes.

> **Status:** Living · **Last reviewed:** 2026-09-10 · **Owner:** OpenTechnology14

This is the per-module view of what is built and what evidence still has to be collected. It
connects three sources that answer different questions:

- [`../../tests/ACCEPTANCE-CHECKLIST.md`](../../tests/ACCEPTANCE-CHECKLIST.md) is the release gate
  and remains the canonical definition of done.
- Each module's `setup/automated.md` is the repeatable setup and test path; `setup/manual.md` is the
  live service, desktop, audio, visual, account, and hardware path.
- [`../PROPOSALS.md`](../PROPOSALS.md) is the only work queue. An open item here must already have a
  proposal before implementation begins.

**Enforcement: required evidence index.** Documentation tests require every module to appear here
and to keep both setup workflows. Capability and evidence claims are governed by the linked
acceptance checklist and proposal records.

## How to read the checklist

| Column | Values |
|---|---|
| Implementation | **Built** = code/config exists; **Partial** = useful slice exists; **Open** = named capability is not built |
| Automated evidence | **Pass** = covered by the offline suite; **Contract** = structure/config is checked but no live dependency ran; **None** = no automatic proof |
| Human/live evidence | **Passed** = dated real-system evidence exists; **Pending** = run the linked manual workflow; **Blocked** = a prerequisite or implementation is missing |

A **Built / Pending** row is normal: it means the repository work exists but still needs a person,
service, account, device, GPU, or operating-system pass. Module-level status remains in `AGENTS.md`
and `CLAUDE.md`; these rows do not promote a module by themselves.

## Module test workflow index

| Module | Automated workflow | Manual/live workflow | Acceptance section |
|---|---|---|---|
| `creator-experience` | [automated](../../modules/creator-experience/setup/automated.md) | [manual](../../modules/creator-experience/setup/manual.md) | [Capture](../../tests/ACCEPTANCE-CHECKLIST.md#capture--creator-experience) |
| `soundboard` | [automated](../../modules/soundboard/setup/automated.md) | [manual](../../modules/soundboard/setup/manual.md) | [Sound bar](../../tests/ACCEPTANCE-CHECKLIST.md#sound-bar--soundboard) |
| `realtime-ai` | [automated](../../modules/realtime-ai/setup/automated.md) | [manual](../../modules/realtime-ai/setup/manual.md) | [Realtime AI](../../tests/ACCEPTANCE-CHECKLIST.md#realtime-ai--realtime-ai) |
| `automation-control` | [automated](../../modules/automation-control/setup/automated.md) | [manual](../../modules/automation-control/setup/manual.md) | [Automation](../../tests/ACCEPTANCE-CHECKLIST.md#automation--automation-control) |
| `storage-data` | [automated](../../modules/storage-data/setup/automated.md) | [manual](../../modules/storage-data/setup/manual.md) | [Foundations](../../tests/ACCEPTANCE-CHECKLIST.md#foundations--storage-data) |
| `sports-analytics` | [automated](../../modules/sports-analytics/setup/automated.md) | [manual](../../modules/sports-analytics/setup/manual.md) | [Sports CV](../../tests/ACCEPTANCE-CHECKLIST.md#sports-cv--sports-analytics) |
| `content-creation` | [automated](../../modules/content-creation/setup/automated.md) | [manual](../../modules/content-creation/setup/manual.md) | [Content pipeline](../../tests/ACCEPTANCE-CHECKLIST.md#content-pipeline--content-creation) |
| `image-editing` | [automated](../../modules/image-editing/setup/automated.md) | [manual](../../modules/image-editing/setup/manual.md) | [Image editing](../../tests/ACCEPTANCE-CHECKLIST.md#image-editing--image-editing) |
| `nature-generation` | [automated](../../modules/nature-generation/setup/automated.md) | [manual](../../modules/nature-generation/setup/manual.md) | [Generation](../../tests/ACCEPTANCE-CHECKLIST.md#generation--nature-generation-cityscape-generation) |
| `cityscape-generation` | [automated](../../modules/cityscape-generation/setup/automated.md) | [manual](../../modules/cityscape-generation/setup/manual.md) | [Generation](../../tests/ACCEPTANCE-CHECKLIST.md#generation--nature-generation-cityscape-generation) |
| `marketing-crosswalk` | [automated](../../modules/marketing-crosswalk/setup/automated.md) | [manual](../../modules/marketing-crosswalk/setup/manual.md) | [Content generation](../../tests/ACCEPTANCE-CHECKLIST.md#content-generation--marketing-crosswalk) |
| `social-management` | [automated](../../modules/social-management/setup/automated.md) | [manual](../../modules/social-management/setup/manual.md) | [Social management](../../tests/ACCEPTANCE-CHECKLIST.md#social-management--social-management) |
| `backend-api` | [automated](../../modules/backend-api/setup/automated.md) | [manual](../../modules/backend-api/setup/manual.md) | [API](../../tests/ACCEPTANCE-CHECKLIST.md#api--backend-api) |
| `broadcast-graphics` | [automated](../../modules/broadcast-graphics/setup/automated.md) | [manual](../../modules/broadcast-graphics/setup/manual.md) | [Graphics](../../tests/ACCEPTANCE-CHECKLIST.md#graphics--broadcast-graphics) |
| `observability` | [automated](../../modules/observability/setup/automated.md) | [manual](../../modules/observability/setup/manual.md) | [Monitoring](../../tests/ACCEPTANCE-CHECKLIST.md#monitoring--observability) |
| `infrastructure` | [automated](../../modules/infrastructure/setup/automated.md) | [manual](../../modules/infrastructure/setup/manual.md) | [Infrastructure](../../tests/ACCEPTANCE-CHECKLIST.md#infrastructure--infrastructure) |
| `audio-production` | [automated](../../modules/audio-production/setup/automated.md) | [manual](../../modules/audio-production/setup/manual.md) | [Audio](../../tests/ACCEPTANCE-CHECKLIST.md#audio--audio-production) |
| `character-avatar` | [automated](../../modules/character-avatar/setup/automated.md) | [manual](../../modules/character-avatar/setup/manual.md) | [Avatars](../../tests/ACCEPTANCE-CHECKLIST.md#avatars--character-avatar) |
| `ai-agents` | [automated](../../modules/ai-agents/setup/automated.md) | [manual](../../modules/ai-agents/setup/manual.md) | [Agents](../../tests/ACCEPTANCE-CHECKLIST.md#agents--ai-agents) |
| `asset-pipeline` | [automated](../../modules/asset-pipeline/setup/automated.md) | [manual](../../modules/asset-pipeline/setup/manual.md) | [Storage contract](../../tests/ACCEPTANCE-CHECKLIST.md#storage-contract--asset-pipeline) |
| `model-registry` | [automated](../../modules/model-registry/setup/automated.md) | [manual](../../modules/model-registry/setup/manual.md) | [Model provenance](../../tests/ACCEPTANCE-CHECKLIST.md#model-provenance--model-registry) |

## Shared foundations and production

| Module | Subfeature | Implementation | Automated evidence | Human/live evidence |
|---|---|---|---|---|
| `storage-data` | Postgres, Redis, MinIO Compose topology | Built | Contract | Pending service startup |
| `storage-data` | Ordered SQL migrations and agent memory table | Built | Pass | Pending live application |
| `storage-data` | Seven required object buckets | Built | Pass declaration | Pending live creation |
| `asset-pipeline` | Shared MinIO/S3 client and error contract | Built | Pass | Pending fresh MinIO pass |
| `asset-pipeline` | Realtime, worker, and image-editing consumers migrated | Built | Pass | Pending live upload/download |
| `model-registry` | Schema, checksum, license, and distributability validation | Built | Pass | Pending real weight entry |
| `model-registry` | MinIO registry synchronization | Built | Pass with mocked client | Pending live storage pass |
| `model-registry` | Populated registry of installed weights | Open | None | Blocked on owner-selected weights |
| `infrastructure` | Local and DigitalOcean Compose/deploy contracts | Built | Contract | Pending live deployment |
| `infrastructure` | Backup and restore path | Built | Contract | Pending proven restore |
| `infrastructure` | Tailscale private network posture | Partial | None | Pending two-node inspection |
| `observability` | Prometheus, Grafana, Loki, source-health topology | Built | Contract | Pending live dashboards/logs |
| `observability` | Human-visible alert destination | Open | None | Blocked on destination/configuration |

## Stream production

| Module | Subfeature | Implementation | Automated evidence | Human/live evidence |
|---|---|---|---|---|
| `creator-experience` | Windows prerequisite bootstrap and cross-platform device discovery | Built | Pass | Mac passed 2026-09-08; physical Windows/capture card pending |
| `creator-experience` | Device selection persistence | Built | Pass | Mac passed 2026-09-08; Windows pending |
| `creator-experience` | OBS scene collection | Partial | Contract | Blocked on populated scenes |
| `creator-experience` | Recording, bitrate, remux, and mic-chain acceptance | Partial | None | Pending OBS recording |
| `soundboard` | Licensed clip manifest and placeholder enforcement | Built | Pass | Pending bundled clip audition |
| `soundboard` | Director slot/hotkey/cooldown/off-air rules | Built | Pass | Pending OBS dock and track pass |
| `soundboard` | P-066 reviewed phrase manifest and exclusive clip-or-speech routing | Built | Focused pass | Pending actual WAV/hotkey/stop/track recording |
| `automation-control` | P-066 prompt editor, render/review library, rollback and manual script/Q&A cursor | Built | Focused pass | Mac local generation/render and native catalog inspected; full OBS/Windows acceptance pending |
| `realtime-ai` | Indexed ComfyUI workflows | Built | Pass | Pending local workflow selection |
| `realtime-ai` | LCM webcam stylization and virtual-camera route | Partial | Contract | Pending GPU/OBS latency pass |
| `realtime-ai` | ComfyUI output upload to object storage | Built | Contract | Pending live MinIO pass |
| `backend-api` | Health, authenticated mutation routes, and WebSocket auth | Built | Pass | Pending running-service health pass |
| `backend-api` | Redis-to-WebSocket fanout | Partial | None | Blocked on live harness |
| `broadcast-graphics` | NodeCG bundles, environment, channels, and files | Built | Pass | Pending running NodeCG pass |
| `broadcast-graphics` | Replicant dashboard updates and transparent OBS sources | Partial | Contract | Pending visual OBS pass |
| `audio-production` | Session-scoped native speech export | Built | Pass | Mac/Windows CI passed; live routing pending |
| `audio-production` | Local-voice provider seam and render cache (P-068 slice 1) | Built | Pass: 39 fake-engine contract tests; real `--validate` | No engine adapter, model, voice or measurement exists; voice studio and Autopilot production use native voices only |
| `audio-production` | Blind voice-audition rig (P-068 slice 2) | Built | Pass: 30 tests; real run on installed OS voices | No listening has been done; no non-OS candidate or Windows run; the mid-clip switch is not covered |
| `audio-production` | Clone-source recording checker (P-068 slice 3) | Built | Pass: 68 tests; real AAC round trips and OS speech | No microphone recording has been checked; thresholds are starting values; MP3 and mains hum are not validated |
| `audio-production` | Pre-render and render timing (P-068 slice 4) | Built | Pass: 30 tests with fake engines and a scripted clock; real baseline for the OS voice | No local engine has been timed, so the 60 s pass condition has never run on a real engine |
| `audio-production` | Canonical audio-bus routing configs | Built | Pass | Reference formats; pending native preset compatibility and live level check |
| `audio-production` | In-app routing-tool detection and bundled references (P-063) | Built | Pass: 23 shared plugin tests; both app checks/builds | Mac tool probe passed; native panel blocked by locked Mac; Windows/Linux pending |
| `audio-production` | Mix-minus, AI voice bus, and peak-level acceptance | Partial | None | Pending live audio pass |
| `ai-agents` | Nova identity, game variations, phrase cooldowns, and bounded sessions | Built | Pass | Pending live chat ingress |
| `ai-agents` | Input/output moderation gate | Built | Pass | Pending live blocked-message pass |
| `ai-agents` | Ollama response, memory, and avatar publication | Partial | Contract | Pending local model end-to-end pass |
| `character-avatar` | VTube Studio talk/idle event sequencing | Built | Pass | Pending live hotkey pass |
| `character-avatar` | Transparent render and voice-driven mouth movement | Partial | None | Pending avatar/OBS visual pass |
| `automation-control` | Stream director preview, event scoping, module dispatch, and pause rules | Built | Pass | Pending live OBS behavior |
| `automation-control` | Show profiles, calendar, platform policy, and approval drafts | Built | Pass | Pending account-scoped YouTube workflow |
| `automation-control` | Session lifecycle and stale-safe human/agent handoff contracts | Built | Pass | Mac rehearsal passed 2026-09-08 |
| `automation-control` | Concrete game-input adapters and authenticated Take control | Open | None | Blocked on adapters/operator controls |

## Creator production

| Module | Subfeature | Implementation | Automated evidence | Human/live evidence |
|---|---|---|---|---|
| `sports-analytics` | Golf tracer and pose command contracts | Partial | Pass | Pending recorded-footage visual pass |
| `sports-analytics` | NDI output | Partial | Contract | Pending OBS frame-rate pass |
| `sports-analytics` | Calibration applied to trajectory | Open | None | Blocked on implementation |
| `content-creation` | Interaction/manual-range Shorts selection and edit plans | Built | Pass | Synthetic Mac render passed 2026-09-08 |
| `content-creation` | Caption, branding, punch-in, audio normalization, and FFmpeg render | Built | Pass | Real stream/phone review pending |
| `content-creation` | Managed Stream Extend recording → Creator Extend inbox, profile routing, import/reveal/archive | Built | Pass | Real OBS file and native Windows reveal pending |
| `content-creation` | Creator workflow input/output preview contracts | Built | Pass | ComfyUI Mac pass; Windows pending |
| `content-creation` | Blender/Resolve pipeline and batch render | Partial | Contract | Batch render blocked; desktop passes pending |
| `image-editing` | Workflow structure and Krita script contracts | Built | Pass | Pending live Krita connection |
| `image-editing` | Inpaint, remove, outpaint, upscale, and background replacement | Built | Contract | Five workflows passed on Mac GPU 2026-09-02 |
| `image-editing` | SAM auto-select and video-range editing | Open | None | Blocked on node/model design |
| `nature-generation` | Deterministic Tier 0 tone pipeline | Built | Pass | Pending real-photo review |
| `nature-generation` | Learned generation and adapters | Open | None | Blocked on P-059 authorization/models |
| `cityscape-generation` | Deterministic Tier 0 perspective/geometry/tone pipeline | Built | Pass | Pending real-photo review |
| `cityscape-generation` | Skyline generation and learned adapters | Open | None | Blocked on P-060 authorization/models |
| `marketing-crosswalk` | Template rendering, status, private-link, and claim gates | Built | Pass | Pending cross-repository `validate` run |
| `marketing-crosswalk` | Registered module/profile marketing generation | Built | Pass | Pending publication workflow acceptance |

## Social identity and publication

| Module | Subfeature | Implementation | Automated evidence | Human/live evidence |
|---|---|---|---|---|
| `social-management` | Profile, brand/logo, destination, and capability dropdown contract | Built | Pass | Standalone picker and both native Tauri tabs passed on MacBook 2026-09-10 |
| `social-management` | Always-visible active workspaces and remembered per-profile account routes | Built | Pass | Native restart/two-real-account acceptance pending |
| `social-management` | Native reconnect and confirmation-gated account disconnect | Built | Pass | Real OS-vault deletion on macOS/Windows pending |
| `social-management` | Validated private custom profile create/update/remove | Built | Pass | Pending desktop editor integration |
| `social-management` | OAuth state/PKCE, provider verification, and OS-vault boundary | Built | Pass with fake providers | Pending real YouTube/Twitch/X/Discord accounts on macOS/Windows |
| `social-management` | Approved YouTube upload/live, Twitch live, X post, and Discord announcement adapters | Built | Pass request contracts | Pending real private post/upload/stream/message round trip |
| `social-management` | TikTok, Meta, LinkedIn, Bluesky, Mastodon, Kick, Rumble, Trovo, DLive, and Restream adapters | Open | Catalog contract | Blocked on registration/review and adapter work |

## Cross-module platform slices

These features span module boundaries, so their priority and completion remain in the named
proposal even though their pieces appear in the module rows above.

| Proposal | Subfeature | Implementation | Automated evidence | Human/live evidence |
|---|---|---|---|---|
| `P-003` | À la carte setup, dependency plans, readiness, capture diagnostics, and saved endpoints | Built | Pass | Mac passed; fresh Windows, capture card, hosted sync pending |
| `P-056` | Daily shows, personas, lifecycle, handoff contracts, speech, and Shorts | Partial | Pass | Mac/Windows CI passed; live OBS/chat/game adapters pending |
| `P-057` | Creator upload, prepared workflow, queue, completion discovery, and preview | Built | Pass | Mac ComfyUI passed; Windows UI pending |
| `P-058` | Authenticated relay transport, targeted commands, and local approval controls | Built | Pass | Mac loopback passed; hosted relay, Windows, and live service approvals pending |
| `P-065` | Managed OBS recording handoff plus persistent Stream/Content profile workspaces | Built | Pass | Real OBS picture/audio, app restart, and Windows UI pending |

## Update rule

When a capability changes, apply `DM-ACCEPTANCE`: update the acceptance line, the owning module's
manual verification steps, and this roll-up in the same change. When a pending manual/live pass is
completed, record the date and environment here and in the proposal evidence. Add implementation
work only through [`../PROPOSALS.md`](../PROPOSALS.md).

P-056 native production build: persistent owner, correlated preflight/control/status, hard
speech cancellation, recording-first owned OBS output, recording inbox handoff, bounded
private-world Minecraft movement/release and eight configured VTube rig cues are built.
Actual platform/OBS/game/rig and physical Windows acceptance remain open; expanded multi-host
work and other renderers/adapters depend on phase evidence. No module promotion.
