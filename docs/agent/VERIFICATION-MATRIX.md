# Verification matrix

> **Status:** Living · **Last reviewed:** 2026-10-04 · **Owner:** OpenTechnology14

**What you changed → what actually proves it works locally.**

**Enforcement: required.** Implementation is not finished until it has been verified locally.
"Tested" is not a verification — the PR body and the `PROPOSALS.md` row name **which row you ran
and what it returned**. A queue row does not move to `Done` without that.

This is read *while* you work, not at PR time. The point of a verification step is that it runs
before you claim something works.

**Prefer the cheapest row that answers the question.** An offline test beats a running service
beats a manual pass. Do not silently downgrade a row because the cheap proof is inconvenient — say
you could not run it and why, in the row.

---

## The commands

Blender still-job changes require worker containment/failure tests, native ownership/retry
contracts, both build checks and the opt-in real-Blender smoke against an owned fixture.
The launcher must not claim persisted PIDs or overwrite earlier attempt artifacts. A native
GUI run and physical Windows acceptance remain separate from headless/hosted results.

`python3 scripts/testing/generate_docs.py --check` verifies full agent-instruction parity
and the canonical queue/module/rule snapshot. Use `--write` after source edits and inspect
the diff; do not hand-edit generated data. Drift rejection and safe target containment have
offline tests; snapshot freshness is also a required CI step.

`make verify` derives local gates from CI, expands both desktop app checks and reports every
NOT RUN command. Inspect its plan with `make verify ARGS=--list`; it preserves `.env` and
never starts the live acceptance stack. `make proposal-report ARGS='--check --summary'`
checks canonical queue IDs/model assignments against the lane map. See
[the verifier instructions](../../scripts/testing/README.md). Neither command replaces live
device/account acceptance or the existing required `make test` run.

```bash
make test                      # the required offline suite — no services, no network, no GPU
python3 -m ruff check modules/ scripts/     # blocking since P-001 WP-1 (2026-09-02); clean
/bin/bash -n scripts/**/*.sh   # parse under macOS bash 3.2, not just your shell
```

```bash
make up && make ps && make healthcheck      # bring the stack up and smoke it
make migrate                                # apply migrations in filename order
docker compose config -q                    # compose files are valid
docker compose -f docker-compose.yml -f docker-compose.digitalocean.yml config -q
```

```bash
cd modules/marketing-crosswalk
python3 -m generator.cli validate   # anchors + status claims still hold in both repos
python3 -m generator.cli selftest   # every template renders, no private links
```

```bash
make test-obs                  # OBS WebSocket reachable (needs OBS running)
```

The **full feature test run** is `tests/ACCEPTANCE-CHECKLIST.md` — the last step of every module,
and the release gate for the platform. It is not a command; it is a list, because 28 of its lines
are things only a human can confirm.

---

## The matrix

| You changed | What proves it | **Not sufficient** |
|---|---|---|
| Any `.sh` under `scripts/` | `make test` (parses under bash 3.2, no bash-4 builtins, strict mode) **and** running it against a real target | It ran on your machine. `mapfile` worked in your shell and still broke `make migrate` on stock macOS |
| A migration | `make migrate` against a real Postgres, then inspect the schema. Confirm ordering if you added a directory | The file existing. `0002_memory.sql` was applied all along while three docs said it was not |
| `docker-compose.yml` | `docker compose config -q` on **both** the base and the DO overlay, then `make up && make healthcheck` | `make up` alone. The overlay is what breaks, and only in cloud |
| Python in a module | `make test` + `ruff check` + actually running the entry point against its real input | Import success. A script that imports is not a script that works |
| P-066 personality prompts, saved reactions and scripted Q&A | Focused `test_voice_studio.py` and `test_phrase_routing.py`; real `scripts/testing/voice_studio_smoke.py` with an installed model; Stream Rust tests and Svelte check/build; native prompt/render/revision UI; `make test` + Ruff; then manual Soundbox WAV/hotkey/Stop All/track recording and Windows repeat | A WAV, bundle or OBS acknowledgement is not an audible correct-track pass. Model grounding instructions are not factuality verification. Approval is a human review action, not a test result |
| Stream Autopilot's stream-module bindings (P-056) | `make test` + focused `tests/automation_control/test_stream_director.py` + fresh host-output CLI preview; then `--discover-obs` and local OBS/NodeCG/audio/n8n acceptance for enabled bindings | A preview or protocol acknowledgement does not prove an audible clip, visible overlay, or completed workflow |
| Stream Autopilot lifecycle (P-056) | Focused supervisor state/failure/recovery tests; actual `stream_autopilot status`, `rehearse` and read-only `preflight`; inspection tests must prove HTTP-only cleanup and no effect shutdown; Stream Extend Rust/Svelte builds; native bundled UI rehearsal; then repeat with a production driver and real local services | The no-effects driver proves lifecycle behavior, persistence and UI packaging. It does not prove a host process, OBS broadcast, game input release, voice/avatar output or unattended recovery |
| P-068 pre-render and timing (`stream_speech --prerender`) | `tests/audio_production/test_prerender.py` + `make test` + Ruff; a real run on this machine over at least twenty realistic paragraphs (the OS-voice baseline), and for any engine the same run with the cache cold, then warm | A scripted clock and fake engines prove the percentile, hit-versus-render accounting and pass-condition logic. They say nothing about a real engine's speed, and one run is one machine at one moment (no cross-session consistency) |
| P-068 clone-source recording checker (`tts/check_voice_sample.py`) | `tests/audio_production/test_voice_sample_check.py` + `make test` + Ruff; a real run on the owner's first recording (all nine checks read against what was heard) and on OS speech; the thresholds retuned against that recording | Synthetic and OS-speech tests prove the measurements and grading, and a real AAC round trip proves the lossy-source detector at low bitrates. None of it proves the thresholds suit a real microphone, and a pass does not mean the recording will clone well |
| P-068 blind audition rig (`tts/audition.py`) | `tests/audio_production/test_voice_audition.py` + `make test` + Ruff; a real `build` with installed OS voices through `--native`, checking the takes' measured levels match and that nothing printed or named identifies a voice; a `reveal` recorded once | Synthetic-tone tests prove the controls (shuffle, level match, hidden key, one recorded ranking), not that a listening test is valid. The result is only as good as the candidates fed in and the owner's ears, and a sample-rate difference can still reveal a voice |
| P-068 local-voice provider seam (`stream_speech` `provider: local`, render cache) | `tests/audio_production/test_local_voice_provider.py` (fake engine) + `make test` + Ruff; real `python -m stream_speech --validate` with and without a local voice configured; for any real engine, additionally `--validate` ready, a rendered line played through the worker with the avatar still mouth-syncing, and the P-068 §6 measurements | A fake engine proves the seam, the cache and the unchanged playback events. It proves nothing about any engine's installation, quality, latency, determinism or a cloned voice, and a passing offline suite does not mean a local voice can render |
| Stream Autopilot speech/avatar/chat runtime (P-056) | Focused speech, playback-timed avatar, Twitch envelope and production-driver tests; native `stream_speech --validate`; real audible reply plus active-playback cancellation timing; Twitch CLI validation; then test-channel chat → backend → voice/avatar recording | Native Mac speech proves synthesis/playback/cancellation only. Twitch envelope fixtures do not prove account authorization or real messages; avatar configuration does not prove a loaded model/hotkeys; Windows needs its own native run |
| P-003 selective module installer and desktop setup | `make test` + Ruff; actual CLI list/plan/install/doctor and capture scan; PowerShell bootstrap plan on Windows; both apps Rust tests and Svelte check/build; shared plugin Rust tests; native bundled UI selection/install/check/capture scan, restart persistence, guides and shared environments; repeat on Windows | Package consistency, application presence and device enumeration do not certify service operation, GPU compatibility, capture stability or full module readiness. A Mac UI pass is not a native Windows pass |
| P-003 desktop connection settings | Both app Rust tests + shared `local-settings` tests + Svelte checks/builds; inspect serialized public file for secret absence/private permissions; native save/restart and invalid-input pass; test real OBS/ComfyUI connection separately; repeat credential storage on Windows | A redacted frontend DTO does not prove the secret avoided disk/logs. Saving an endpoint does not prove the service is reachable |
| P-003 readiness contract and OpenTechnology sync | Shared setup-engine tests, including expiry and an exact bearer-authenticated loopback HTTP body; both app Rust suites and Svelte checks/builds; verify operational controls consume capabilities in native bundles; companion receiver/template tests; repeat native UI and credential storage on Windows, then one hosted sync | A rendered status is not a capability gate. A mocked receiver does not prove hosted credentials, routing or physical hardware |
| P-058 desktop remote control | Shared relay-client tests with a real loopback WebSocket; cloud relay handshake/message validation; both app Rust tests and Svelte check/build; two connected native app instances through `scripts/testing/fake_relay.py`; verify authenticated device discovery, same-product target filtering, pending approval, denial, approved local action and correlated result; inspect public settings for secret absence; repeat on Windows and the hosted relay before claiming those targets | A discovered device or green connection badge does not prove the intended workstation can complete an action. A queued request does not prove the approved OBS/ComfyUI action completed |
| P-062 Social Management | Focused `tests/social_management` and shared Tauri plugin tests; both app Svelte checks/builds; `make test` + Ruff; run both native Social tabs on the MacBook display; inspect the public ledger and OS credential entry separately; connect disposable YouTube/Twitch/X/Discord accounts and complete one private upload/live/post/message; repeat credential, UI and provider acceptance on Windows | A rendered dropdown or mocked provider response does not prove developer registration, channel eligibility, OAuth callback configuration, OS-vault persistence, or that a post/stream/message reached the selected account |
| P-065 recording handoff and profile workspaces | Shared recording-library and Social Manager Rust tests; fake OBS request-order/ownership contracts; focused social/desktop Python contracts; both full app Rust suites and Svelte check/build; `make test` + Ruff; then a native Stream Extend-managed OBS session producing a playable file in Creator Extend with source/target profile persistence, reveal/import/archive, restart, two-account route restoration, and pre-existing-recording safety; repeat on Windows | A fake OBS path or JSON inbox entry does not prove encoder output, picture/audio quality, OS file reveal, restart behavior, or that real provider accounts were routed. A recording in the inbox is not evidence that editing or publishing completed |
| P-056 native Windows/Mac setup and speech | `make test` + focused speech/setup contracts + `python scripts/setup/stream_autopilot.py doctor` and `smoke` with installed dependencies on each claimed OS; retain report and WAV/MP4 artifacts | A mocked Windows speech call or Mac smoke pass is not a native Windows pass. OBS, gameplay and desktop bundles need separate acceptance |
| P-056 show calendar / Shorts / editing / input handoff | `make test` + Ruff + real planner CLI and synthetic-video `stream_shorts produce`; inspect the branded frame, captions, timed punch-in, audio metadata and review UI; then live adapter input-release acceptance | Draft calendar flags do not start streams or editors; project briefs are operator-maintained snapshots, not saved product artifacts. Caption/punch-in cues are supplied rather than inferred. Fake adapter receipts do not prove device-level takeover. Synthetic interaction metadata does not prove live chat ingress |
| Creator Extend workflow inputs / outputs / bundled templates and P-063 preflight | Rust input/upload/queue/history/reference/byte-bound and bundled-resource contracts; fake ComfyUI endpoint/node/model/VRAM preflight and queue-guard contracts; Svelte check/build; actual desktop bundle; explicit local ComfyUI synthetic image and preview round trip; `make test` | A green node/model inventory does not prove enough VRAM, image decoding, job completion or output quality. An HTTP upload acknowledgement or empty history panel does not prove preview rendering. A Mac pass does not prove Windows compatibility |
| Nature Generation learned tiers (P-059) | Schema/workflow structural tests, model-registry verification and real local ComfyUI GPU runs per tier; visually inspect structure retention, mask seams, relighting and adapter originality at full resolution; `make test` + Ruff | A valid graph or completed prompt does not prove a usable image. Tier 0 evidence does not prove any learned tier. A synthetic or unclear-rights corpus does not authorize training |
| Cityscape Generation learned tiers (P-060) | Schema/workflow tests must enforce lineart on structural jobs; model-registry verification and real local ComfyUI GPU runs per tier; inspect verticals, window grids, signage removal and day/night separation at 100%; `make test` + Ruff | A nature workflow or generic inpaint pass does not prove city geometry. A rendered image does not prove privacy/rights review or adapter distributability |
| Blender production jobs (P-061) | Python/Rust/operator contracts plus a real two-scene Blender job; exercise failure, cancel, retry and restart recovery; verify immutable manifests and optional MinIO artifacts; repeat the native app path on macOS and Windows; `make test` | A spawned Blender process or optimistic addon message does not prove scene completion, cancellation, recovery or upload. Mocked Blender alone cannot close live acceptance |
| A ComfyUI workflow JSON | Load it in ComfyUI and run it once end to end, then update the on-disk table in that `workflows/README.md` | Committing the file. Six indexed workflows never existed and the index claimed otherwise for months |
| A module's `setup/manual.md` | **Walk it on a clean machine**, then correct it in the same session (`DM-MODULE-DRIFT`) | Reading it back. A setup doc is a spec until someone walks it |
| A module's `setup/automated.md` | Run every command in it. If it says nothing is automated, confirm that is still true | Assuming the module's dependencies are automated because yours are |
| A new module | `make test` (setup docs exist, labels declared, both matrices list it, `CLAUDE.md` §11 has a row) + a `PROPOSALS.md` row + a `deviations.md` entry | Creating the directory. Six index tables go stale at once — that is what `DM-MODULE` is for |
| `CLAUDE.md` §11 status | `marketing-crosswalk validate` — subjects cite the row **verbatim** and drift fails loudly | Editing the table. The claim gate reads it, and a silent edit either over-claims or blocks wrongly |
| A `README.md` or `product-spec.md` **heading** | `marketing-crosswalk validate` — anchors match exact heading text | Renaming it. This broke on 2026-08-30 and the tool caught it, not a human |
| `marketing-crosswalk` itself | `validate` **and** `selftest` **and** `ruff check` | `validate` alone. It checks the registry; `selftest` checks that every template still renders |
| Docs only | `make test` — links resolve, index complete, proposals queued, headers present | "Links look right." All of these were run by hand until they were forgotten once |
| Which docs a change should touch | `python3 scripts/testing/doc_advisory.py` lists the `DM-*` rules your diff fires (advisory, exit 0); `tests/docs/test_doc_advisory.py` proves the matching | Reading `DOC-UPDATE-MATRIX.md` by eye. It maps paths, not meaning: the five judgement rules still rest on you |
| `design-system/` (tokens, specs, registers, consumers) | `tests/design_system/` (token shape, source drift, contrast recomputation, decisions, consumers, registry row, registers) + `tests/docs` + `marketing-crosswalk validate` and `selftest` + `make test`; supply the sibling checkouts (`OPENTECHAPP_REPO_PATH`, `OTBLOG_REPO_PATH`, `MYFEED_REPO_PATH`, `JOB_HUNTER_REPO_PATH`) to re-read external observations at their pinned revisions | A token that "looks right". The tests prove each recorded value still exists in its source and each contrast ratio recomputes; they do not prove a design is good, that a consumer implements it, or that a person can use it — keyboard and screen-reader passes stay manual |
| Agent skills (`.claude/skills/*/SKILL.md`) and their pointer in `CLAUDE.md` §14 | `tests/docs/test_agent_skills.py` (frontmatter, real paths, pointer completeness, voice guardrail) + `python3 scripts/testing/generate_docs.py --check` + `make test`; then open the skill cold and follow its first steps against the repo | A skill that reads well. Skills summarise documents that move; the test proves paths and pointers exist, not that the advice is still right — re-read the cited document when it changes |
| An owner decision row, gate or open question | `tests/docs/test_decision_questions.py` (every open lane row, the P-074 and P-075 gates, the design-system hub decisions and every `Pending` queue row end with one plain-English `**Question:**`; sentence rules; the rule is written in the five documents that tell people to add decisions) + `make test` | A question that reads well. The test proves one short sentence is present and carries no identifier or code span, not that it asks what its explanation asks — read each new one against its row |
| A top-level `docs/*.md` document | `tests/docs/test_status_headers.py` (a status and a dated review in the first 15 lines, or an explicit exemption with its reason; a stale exemption fails) + `make test` | Copying a date from the last commit. The guard checks presence and a plausible date, not that a review happened: use the last commit that changed the document's own claims, never a banner, an import or a hygiene edit |
| The work-registration pointer (`CLAUDE.md` section 17) and the four skills that carry it | `tests/docs/test_work_registration_pointers.py` (the section links both library workflows at one pinned revision, each skill says "Register first" and cites section 17, and no file keeps its own list of Kinds) + `python3 scripts/testing/generate_docs.py --check` + `make test` | A pointer that reads well. The test proves the links and the pin agree with each other, not that the pinned revision still exists or that the library has not changed its Kinds: refresh the pin when the library changes |
| A lane row in `docs/todo/`, or a statement about the repository's own state in `design-system/` | `tests/docs/test_lane_rows_current.py` (an *Awaiting acceptance* row names a `Pending` proposal; an accept-or-retire decision names only proposals that wait; an "also <ID>" pointer leads to a row about the same proposal; the hub does not say the root `LICENSE` is missing) + `make test` | Trusting a row because it was right when written. The test catches those four classes, not every drift: the map's state labels and waiting items are not compared with the queue, and the audit ledgers' own statements are not checked |
| P-001 private release evidence collector | Focused `tests/docs/test_release_check.py`, full `make test` and Ruff; actual collection against a fresh clean checkout, inspect commit/tree/check statuses and verify `SHA256SUMS.txt`; confirm dirty/source-change/timeout failures and every NOT RUN release gate | A Python-only report or installer hash does not prove clean-host installation, build provenance, signing, secret/SBOM review, native/live acceptance, rollback or owner release approval |
| P-001 relay context/role/provider safety | Relay tests with real requirements and `-p scripts.testing.no_skips`; live `test_tenant_isolation.py` on owned Postgres; same/cross-tenant read/write, reuse/reset, superuser/owner rejection, migration/password bootstrap; provider 501-before-effects and preserved refresh; mutation checks, `make test` and Ruff | Source RLS does not protect a superuser/owner. Skipped API tests or fake provider success do not prove safety. Native trust-auth tests do not prove production password auth, Docker or existing-volume upgrade |
| P-072 private shell preview | Preview Node tests, locked Rust suite and admission/CSP/IPC Python checks; shared/legacy app suites; all three frontend checks/builds; actual private Tauri bundle; `make test` and Ruff; then U-01/U-02/U-07 native opening/restart/vault/keyboard/narrow-width/import/denied-origin acceptance | A debug bundle/configured CSP does not prove native usability/enforcement, clean-host compatibility, device acceptance, parity/migration or public release |
| Proposal agent model assignments | `tests/docs/test_proposal_models.py` + `make test` + `git diff --check`; inspect every queue row and detailed header for model, supported effort and rationale; confirm the execution client offers the selected model before work | A Markdown model assignment does not change a running task, certify model quality, identify a historical execution model, or approve Pending/Deferred work |
| P-063 app launch and assisted setup | For each native Windows artifact: clean machine with no developer tools/Python/FFmpeg/OBS/Docker/WSL/models/accounts; install → usable Module setup → bundled guide → saved selection → reopen; record artifact hash, OS, elapsed time, user actions and terminal/AI interventions. Then test optional-step skip/failure, selected install, retry/reboot recovery, second-app reuse, selected Docker start, migration/bucket/workflow initialization twice, OS credential storage/copy, the bounded capture probe's detected/signal/recorded states, and Creator's endpoint/node/model/VRAM preflight before a real output; run shared runner contracts and `make test`; repeat on macOS for parity | Windows Python CI or a source build is not clean-machine installer acceptance. App-open time is not time to a verified broadcast/content output. A green ComfyUI inventory does not prove VRAM sufficiency or output quality. A green Compose helper exit without inspecting tables, buckets, workflow count and secret boundaries is not data/workflow acceptance. A capture probe without a known HDMI source and physical OBS recording is not stream acceptance. An OBS/Docker failure must not block unrelated setup |
| P-063 audio setup assistance | Shared plugin tests for missing/found tools, platform isolation, environment roots and bundled reference availability; both app Rust suites and Svelte check/build; actual Mac app bundle and native panel click-through; `make test` | Filesystem presence cannot prove active audio devices, routes, levels, mix-minus or OBS hotkeys. References are not accepted native import presets. A Mac check does not certify Windows/Linux |
| **A module you consider finished** | Its section of `tests/ACCEPTANCE-CHECKLIST.md`, run end to end — the automated half by command, the manual half ticked off in that module's `setup/manual.md` § Verification | "Setup completed." Installed is not verified, and the manual half is exactly the part no command covers |
| A bug fix, anywhere | A test that **fails before the fix and passes after**. Prove it by reverting the fix and watching it fail | A test that passes. A test written after the fix that never saw the bug proves nothing |

---

## Recording what you ran

In the `PROPOSALS.md` row and the PR body, name the row and the result:

> Verified: `make test` (174 pass), `marketing-crosswalk validate` (34 anchors, 26 status claims),
> `ruff check` (clean). **Not run:** `make migrate` against live Postgres — no database
> available in this environment.

**"Not run" is an acceptable answer; silence is not.** A row you could not verify is a known gap;
a row you skipped quietly is a claim nobody can check.

## What cannot be verified locally today

Recorded so a reader can tell these were considered rather than overlooked:

| Path | Why not | Owner |
|---|---|---|
| A complete creator journey | Harness exists (`tests/acceptance/`, `P-016`, all 4 phases done) and **passed in CI 2026-09-01** (run 33452956159 (private development evidence; not distributed)) — but still needs a Docker daemon, Postgres, Redis, and MinIO to run *locally*, which not every authoring environment has. Run with `make test-acceptance` where they are available | `P-016` — all 4 phases done, including Phase 4's `storage-data` promotion (2026-09-01) |
| GPU inference, ComfyUI, VTube Studio, avatar/audio hardware | Needs the hardware and the desktop app installed — but **has now been done once**, locally, on real hardware: ComfyUI on Apple M1 Pro Metal/MPS, 5 of 6 previously-untested `image-editing` workflows GPU-run end to end (`P-043`, 2026-09-02). Not CI-repeatable (no GPU in CI), so still `**manual**` in `tests/ACCEPTANCE-CHECKLIST.md`, not automated | The module's own setup doc; `P-043`'s row in `docs/PROPOSALS.md` for what was actually run |
| OBS itself | Needs the desktop app installed and a scene collection exported by hand | The module's own setup doc |
| DigitalOcean deployment | Needs a droplet and a tailnet | `P-001` release evidence |
| Live Postgres/MinIO behaviour | The offline suite deliberately excludes services; mark such tests `@pytest.mark.live` | `P-016` |

The first row is why almost every module is still `scaffolded` despite this session's build-out:
the thing that produces promotion evidence **is** built now, but promoting a module's status is a
deliberate decision with its own evidence record (see `storage-data`'s in `CLAUDE.md` §11), not
something that happens automatically the moment a test suite exists for it.

### P-056 production owner, game and rig acceptance

Run the Automation Control and Character Avatar focused suites, the Minecraft Node contract
tests, Stream Rust/Svelte checks and the packaged-owner opt-in Rust test with
`HCP_AUTOPILOT_TEST_PYTHON` pointing at a prepared local Python environment. The native fake-OBS
contract must prove recording before stream, replay isolation, profile conflicts, final inbox
handoff and stop superseding a delayed start. Then build the actual app and inspect fail-closed
preflight, locked Run and emergency stop on the built-in MacBook display. `make test` is required.
These establish ownership/packaging contracts, not live broadcasting, audible/visible output,
physical Windows, real game takeover or performance. Run A1–A11 and the declared workstation
60-minute capture before phase completion; capture timestamps, OBS lag and hardware with results.
