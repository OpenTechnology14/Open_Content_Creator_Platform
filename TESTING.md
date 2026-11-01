# Open Content Creator Platform — Test Scenarios

> **Status:** Living · **Last reviewed:** 2026-08-31 · **Owner:** OpenTechnology14

<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is a set of test scenarios, not a priority queue and not an authorization. A scenario that fails is a finding to route, not a task to start here.
> Unresolved implementation becomes a row in [`PROPOSALS.md`](docs/PROPOSALS.md); what then waits on a person goes in the
> [decision and run lanes](docs/todo/README.md); a document that does not exist yet is tracked in
> [`FUTURE_DOCS.md`](docs/FUTURE_DOCS.md).

Detailed test scenarios **by module**. Run the relevant section after completing that module's
[`setup/manual.md`](modules/README.md).

**Enforcement: reference.** These are scenarios to work through, not a gate.

## Relationship to the other two test documents

Four files, four jobs — read this before adding anything, so a fifth list does not appear:

| File | Shape | Answers |
|---|---|---|
| [`tests/ACCEPTANCE-CHECKLIST.md`](tests/ACCEPTANCE-CHECKLIST.md) | Atomic lines, by module | **What must be true** for a module, and the platform, to be done. The release gate |
| **This file** | Scenarios, by module | **How to test** one capability |
| [`docs/agent/VERIFICATION-MATRIX.md`](docs/agent/VERIFICATION-MATRIX.md) | By change type | **What proves the change** you just made, and what is *not* sufficient |
| [`tests/USE-CASES.md`](tests/USE-CASES.md) | Narrative across modules | **Does the whole thing work together** for a real job? |

The first three are all per-module. The fourth was added because none of them asks whether the
modules *compose* — which is the question an owner actually has.

If a scenario here proves a checklist line, say so in the checklist's marker. If a scenario proves
nothing on the checklist, ask whether the checklist is missing a line or the scenario is not worth
running.

**Two products:** `Stream` and `Content` — see `CLAUDE.md` §4 for which modules carry which label.

**Priority:** P0 = blocks that module, P1 = should fix before moving on, P2 = fix later

> **Nothing here is automated yet.** `make test` covers script portability and docs integrity
> only; every scenario below is a manual pass. Automating one and deleting it from here is
> progress — see `DM-ACCEPTANCE`.

---

## Quick Smoke Tests

```bash
# Docker services alive
make healthcheck

# OBS WebSocket reachable
make test-obs

# Container status
make ps

# All Python lints clean
make lint
```

---

## 1. OBS Foundation — `creator-experience` (`Content` `Stream`)

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 1.1 | OBS installed | Open OBS Studio | Version ≥ 30.x shown in title bar | P0 |
| 1.2 | WebSocket enabled | Tools → WebSocket Server Settings | Server enabled on port 4455, auth on | P0 |
| 1.3 | WebSocket password in .env | `grep OBS_WEBSOCKET_PASSWORD .env` | Non-empty value, not "change-me" | P0 |
| 1.4 | WebSocket test script | `make test-obs` | Exits 0, prints OBS version + current scene | P0 |
| 1.5 | Video settings | Settings → Video | Canvas 1920×1080, Output 1920×1080, FPS 60 | P1 |
| 1.6 | Encoder config | Settings → Output (Advanced) | NVENC/AMF/VT selected, CBR 6000 kbps, keyframe 2 | P1 |
| 1.7 | Recording format | Settings → Output → Recording | MKV format, auto-remux enabled | P1 |
| 1.8 | Audio sample rate | Settings → Audio | 48 kHz, Stereo | P0 |
| 1.9 | 8 scenes exist | Scene list in OBS | Starting Soon, Main Camera, Gameplay, Intermission, BRB, Ending, Vertical Output, Recording Sandbox | P0 |
| 1.10 | Mic filter chain | Right-click mic → Filters | Noise Suppression → Gate → Compressor → Limiter (in order) | P1 |
| 1.11 | Test stream | Stream 5 min to platform | 0 dropped frames in OBS stats | P0 |
| 1.12 | Test recording | Record 5 min locally | File plays cleanly, audio in sync | P0 |
| 1.13 | Scene collection exported | Check file | `modules/creator-experience/scenes/default.json` exists | P1 |
| 1.14 | Plugins installed | OBS plugin list | Advanced Scene Switcher, Move Transition, Source Clone present | P1 |

---

## 2. Face Filters + Background — `realtime-ai`, `character-avatar` (`Stream`)

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 2.1 | Face tool installed | Launch DeepFaceLive / Deep-Live-Cam / LivePortrait | App opens, webcam detected | P0 |
| 2.2 | Virtual camera output | Check face tool settings | Outputting to virtual camera device | P0 |
| 2.3 | OBS captures virtual cam | Add Video Capture → select virtual cam | Face-swapped feed visible in OBS preview | P0 |
| 2.4 | Background removal | Right-click source → Filters → Background Removal | Background replaced/removed, subject isolated | P1 |
| 2.5 | Latency acceptable | Talk on camera, watch preview | Lip sync delay < 150 ms (no noticeable lag) | P0 |
| 2.6 | GPU VRAM usage | Task Manager / nvidia-smi | ≤ 80% VRAM during face effect + OBS | P1 |
| 2.7 | Edge quality | Wave hand past face edges | No major artifacts on hair/glasses edges | P2 |

---

## 3. Golf Tracer + Sports CV — `sports-analytics` (`Content`)

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 3.1 | Dependencies installed | `pip install -r modules/sports-analytics/requirements.txt` | No errors | P0 |
| 3.2 | YOLO model loaded | Run `tracer.py` with test video | Model loads, prints detection count | P0 |
| 3.3 | Ball detection | Run on golf swing video | Ball detected in ≥ 70% of visible frames | P0 |
| 3.4 | Trajectory overlay | Check output frame/video | Smooth curve drawn along ball flight path | P0 |
| 3.5 | Kalman smoothing | Occlude ball briefly in video | Trajectory continues through occlusion | P1 |
| 3.6 | Calibration file | `cat modules/sports-analytics/golf-tracer/calibration.json` | pixel_to_meter ratio present | P1 |
| 3.7 | Virtual camera output | Run tracer → virtual camera → OBS source | Overlay visible in OBS preview | P1 |
| 3.8 | Pose estimation | Run `mediapipe_swing.py` on swing clip | Skeleton overlay drawn on body | P2 |

---

## 4. ComfyUI Content Creation — `realtime-ai`, `content-creation`, `storage-data` (`Content`)

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 4.1 | ComfyUI starts | `cd modules/realtime-ai/comfyui/app && python main.py` | Web UI at http://127.0.0.1:8188 | P0 |
| 4.2 | ComfyUI Manager | Open ComfyUI → Manager tab | Manager UI available, can install nodes | P0 |
| 4.3 | SDXL model loaded | Load checkpoint in workflow | No OOM, model loads within 30s | P0 |
| 4.4 | Thumbnail workflow | Load `thumbnail-1280x720.json` → Queue Prompt | Image generated at 1280×720 | P0 |
| 4.5 | MinIO running | `docker compose up -d minio` → `curl localhost:9000/minio/health/live` | 200 OK | P0 |
| 4.6 | MinIO console | Open http://localhost:9001 | Login works with .env credentials | P1 |
| 4.7 | Buckets created | `mc ls hcp/` | models, outputs, thumbnails buckets exist | P1 |
| 4.8 | Output to MinIO | Generate image → upload script | File appears in MinIO outputs bucket | P1 |
| 4.9 | Blender installed | Open Blender | Version ≥ 4.x | P1 |
| 4.10 | Blender title card | Render `projects/title-card.blend` | 1920×1080 PNG exported | P2 |

---

## 4B. AI Image + Video Editing — `image-editing` (`Content`)

### Desktop (Krita)

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 4B.1 | Krita installed | Open Krita | Version ≥ 5.2 | P0 |
| 4B.2 | AI Diffusion plugin | Settings → Python Plugin Manager | "AI Image Diffusion" enabled | P0 |
| 4B.3 | ComfyUI connection | AI Diffusion settings → Server URL `localhost:8188` | Green "Connected" status | P0 |
| 4B.4 | Inpainting model loaded | Load SDXL Inpainting in ComfyUI | Model loads, no OOM | P0 |
| 4B.5 | Generative fill | Select area → type prompt → Generate | Region filled on new layer | P0 |
| 4B.6 | Object removal | Paint mask over object → Generate (empty prompt) | Object removed, background reconstructed | P0 |
| 4B.7 | Outpaint | Extend canvas → select empty area → Generate | New area filled coherently with existing image | P1 |
| 4B.8 | Auto-select (SAM) | Click on object in AI Diffusion selection mode | Object auto-segmented, mask created | P1 |
| 4B.9 | Upscale | Open low-res image → AI Diffusion → Upscale 4x | Detail-preserving 4x super-resolution | P1 |
| 4B.10 | Background replace | Select subject → inpaint background with prompt | Subject preserved, background replaced | P2 |
| 4B.11 | Output to MinIO | Save edited image → run export script | File appears in MinIO outputs bucket | P1 |

### Mobile API (Creator Extend)

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 4B.12 | Inpaint endpoint | `POST /api/v1/edit/inpaint` with image + mask + prompt | Returns job_id, status "queued" | P0 |
| 4B.13 | Job status | `GET /api/v1/edit/status/{job_id}` | Returns progress + result_url when done | P0 |
| 4B.14 | Remove endpoint | `POST /api/v1/edit/remove` with image + mask | Object removed in result image | P1 |
| 4B.15 | Auto-select | `POST /api/v1/edit/auto-select` with image + point | Returns SAM-generated mask | P1 |
| 4B.16 | Video frame edit | `POST /api/v1/edit/video/frame` with video + frame + mask | Single frame edited in output video | P2 |
| 4B.17 | Video range edit | `POST /api/v1/edit/video/range` with frame range + mask | Edit propagated across frame range | P2 |
| 4B.18 | WebSocket progress | Connect to `/ws/v1/edit/progress` during job | Receives progress updates + optional preview | P2 |

---

## 5. ComfyUI + OBS Realtime — `realtime-ai` (`Content` `Stream`)

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 5.1 | Webcam frame loader | Install ComfyUI-LiveCam node or custom bridge | Webcam frames appear as ComfyUI input | P0 |
| 5.2 | LCM stylization | Load `realtime-lcm-stylize-v1.json` → run | Stylized output at ≥ 8 fps (RTX 30-series) | P0 |
| 5.3 | Virtual camera out | Output → pyvirtualcam / v4l2loopback | Virtual camera device shows ComfyUI output | P0 |
| 5.4 | OBS source | Add virtual cam as OBS source | Stylized feed visible in scene preview | P0 |
| 5.5 | End-to-end latency | Talk on camera, observe preview | < 200 ms total delay | P0 |
| 5.6 | Segmentation mode | Load `realtime-segmentation-v1.json` | Runs at 30+ fps, clean subject mask | P1 |
| 5.7 | Temporal stability | Hold still for 10s | No flickering or frame-to-frame jitter | P2 |

---

## 6. Audio Production + Routing — `audio-production` (`Stream`)

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 6.1 | VoiceMeeter installed | Open VoiceMeeter Potato (Win) / BlackHole+Loopback (Mac) | App launches, sees hardware devices | P0 |
| 6.2 | Mic on HW1 | VoiceMeeter Hardware Input 1 | Mic input active, meter moves when speaking | P0 |
| 6.3 | Desktop on VIN1 | Play system audio | VIN1 meter moves | P0 |
| 6.4 | Mic → A1 + B1 | Route mic to A1 (headphones) and B1 (OBS) | Hear yourself in headphones, OBS captures mic | P0 |
| 6.5 | Desktop → A1 + B1 not B2 | Check routing matrix | Desktop audio reaches headphones + stream, NOT Discord | P0 |
| 6.6 | Call echo test | Join Discord call, have partner speak | Partner does NOT hear themselves echoed back | P0 |
| 6.7 | Mic processing | Apply HPF → Gate → Compressor → Limiter | Mic peaks at -12 dB on normal speech | P1 |
| 6.8 | Sample rate match | Check all devices + VoiceMeeter + OBS | All set to 48000 Hz | P0 |
| 6.9 | AI-VOICE bus | Set AI app output → VoiceMeeter AUX Input | AI audio reaches stream + headphones, NOT mic-in for AI | P1 |
| 6.10 | Multi-track recording | OBS Settings → Audio → track assignments | Track 1: mix, Track 2: mic only, Track 3: desktop | P1 |

---

## 7. Broadcast Graphics + NodeCG — `broadcast-graphics`, `backend-api` (`Stream`)

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 7.1 | Redis running | `docker compose up -d redis` → `docker exec hcp-redis redis-cli ping` | PONG | P0 |
| 7.2 | FastAPI running | `docker compose up -d fastapi` → `curl localhost:8000/health` | 200 OK | P0 |
| 7.3 | FastAPI OpenAPI | Open http://localhost:8000/docs | Swagger UI loads with routes | P1 |
| 7.4 | NodeCG running | `docker compose up -d nodecg` → open http://localhost:9091 | Dashboard loads | P0 |
| 7.5 | Starter bundle loaded | NodeCG dashboard → check bundles | hcp-starter bundle with scoreboard, lower-third, sponsor rotator | P0 |
| 7.6 | Replicant update | Change score in dashboard panel | Graphic updates instantly | P0 |
| 7.7 | OBS Browser Source | Add Browser Source → `http://localhost:9091/bundles/hcp-starter/graphics/scoreboard.html` | Overlay renders in OBS | P0 |
| 7.8 | Live overlay update | Change value in NodeCG dashboard while OBS is previewing | OBS preview updates within 1 second | P0 |
| 7.9 | Redis pub/sub | Publish event to Redis channel → NodeCG receives | Overlay reacts to event | P1 |
| 7.10 | FastAPI → overlay | POST to /overlays API → check graphic | Overlay reflects new data | P1 |
| 7.11 | WebSocket fanout | Connect 2 Browser Sources → update data | Both update simultaneously | P2 |

---

## 8. AI Agents + Avatars — `ai-agents`, `character-avatar` (`Stream`)

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 8.1 | Postgres running | `docker compose up -d postgres` → `pg_isready -h localhost -U hcp` | Server is accepting connections | P0 |
| 8.2 | Migrations applied | `make migrate` | No errors, tables created | P0 |
| 8.3 | pgvector enabled | `psql -U hcp -d hcp -c "SELECT extversion FROM pg_extension WHERE extname='vector'"` | Returns version | P0 |
| 8.4 | Memory table exists | Query `agent_memories` table | Table with embedding vector(768) column | P1 |
| 8.5 | Ollama installed | `curl http://localhost:11434/api/tags` | Returns model list JSON | P0 |
| 8.6 | Model pulled | `ollama list` | llama3.1:8b or qwen2.5:7b present | P0 |
| 8.7 | LLM responds | `curl localhost:11434/api/generate -d '{"model":"...","prompt":"hi"}'` | Generates response text | P0 |
| 8.8 | Avatar tool runs | Launch VTube Studio / VSeeFace / PNGTuber Plus | App opens, avatar visible | P0 |
| 8.9 | TTS produces audio | Run XTTS / Piper on test text | Audio file generated, plays back | P1 |
| 8.10 | TTS → AI-VOICE bus | TTS output device → VoiceMeeter AUX Input | Audio on AI-VOICE bus in VoiceMeeter | P1 |
| 8.11 | Chat → agent → TTS → avatar | Send test chat message → Redis → agent service | Agent responds with voice + avatar lip movement | P1 |
| 8.12 | Memory persistence | Agent answers → restart service → ask about previous topic | Agent recalls earlier context via pgvector | P2 |

---

## 9. Infrastructure + Ops — `observability`, `infrastructure`, `automation-control` (`Stream`)

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 9.1 | Prometheus running | `docker compose up -d prometheus` → open http://localhost:9090 | Prometheus UI loads | P0 |
| 9.2 | Grafana running | `docker compose up -d grafana` → open http://localhost:3000 | Grafana login page | P0 |
| 9.3 | Loki running | `docker compose up -d loki promtail` → check Grafana Explore | Log queries return results | P0 |
| 9.4 | Source health exporter | `docker compose up -d source-health-exporter` → `curl localhost:9101/metrics` | Prometheus metrics returned | P0 |
| 9.5 | Exporter debug | `curl localhost:9101/debug` | JSON dump of all collector states | P1 |
| 9.6 | Grafana dashboards | Grafana → Dashboards | platform-overview, streaming-health, source-health present | P0 |
| 9.7 | Source health dashboard | Open source-health dashboard | Connection tiles, camera FPS, audio levels, latency chart | P1 |
| 9.8 | Alert rules loaded | Prometheus → Alerts | source-health rules visible (OBSConnectionDown, MicSilent, etc.) | P1 |
| 9.9 | Alert fires | Stop OBS → wait 2 min | OBSConnectionDown alert fires in Prometheus | P1 |
| 9.10 | healthcheck.sh | `make healthcheck` | All checks pass (FastAPI, Prometheus, Grafana) | P0 |
| 9.11 | Docker network | `docker network inspect hybrid-creator-platform_hcp-net` | All services on same bridge | P1 |
| 9.12 | n8n running | `docker compose --profile automation up -d` → open http://localhost:5678 | n8n UI loads | P1 |
| 9.13 | CI lint | `make lint` | No ruff errors on modules/ and scripts/ | P2 |
| 9.14 | Tailscale connected | `tailscale status` | Workstation + droplet both online (if applicable) | P2 |

---

## 10. Docker Compose — `infrastructure`, `storage-data`

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 10.1 | Full stack up | `make up` | All services start, `make ps` shows healthy | P0 |
| 10.2 | Service health | `make healthcheck` | FastAPI, Prometheus, Grafana all 200 | P0 |
| 10.3 | Postgres health | `docker exec hcp-postgres pg_isready` | "accepting connections" | P0 |
| 10.4 | Redis health | `docker exec hcp-redis redis-cli ping` | PONG | P0 |
| 10.5 | MinIO health | `curl -f http://localhost:9000/minio/health/live` | 200 | P0 |
| 10.6 | Service isolation | `docker exec hcp-fastapi curl -s http://postgres:5432` | Internal network resolves | P1 |
| 10.7 | Ports not exposed | `curl http://localhost:5432` from host | Connection refused (only 127.0.0.1 bound) | P1 |
| 10.8 | Volume persistence | `make down` then `make up` | Data persists in named volumes | P1 |
| 10.9 | Clean shutdown | `make down` | All containers stop, no orphans | P1 |
| 10.10 | DO overlay | `docker compose -f docker-compose.yml -f docker-compose.digitalocean.yml config` | Valid merged config, no errors | P2 |

---

## 11. Cross-Cutting

| # | Scenario | Steps | Expected | Priority |
|---|----------|-------|----------|----------|
| 11.1 | .env.example complete | Compare .env to .env.example | Every env var in docker-compose.yml has a .env.example entry | P1 |
| 11.2 | No secrets in git | `git log --all -p -- .env` | No results (never committed) | P0 |
| 11.3 | Module independence | Stop any one module's container | Other modules continue working | P1 |
| 11.4 | Setup timeline UI | Open `docs/setup-timeline.html` in browser | Page loads, checkboxes work, progress bar updates | P1 |
| 11.5 | Guide numbering consistent | `grep -r "Guide [0-9]" docs/ modules/` | All references use 1-9 numbering (no Guide 10 or Guide 6 infra) | P1 |

---

## 12. Generation — `nature-generation`, `cityscape-generation` (`Content`)

**No scenarios yet.** Both modules are design-only (no code, `P-011`), so there is nothing to run.
Their acceptance lines are marked **blocked** in
[`tests/ACCEPTANCE-CHECKLIST.md`](tests/ACCEPTANCE-CHECKLIST.md) for the same reason.

When Tier 0 grading ships, its scenarios belong here — and they are the easiest to write in the
whole document, because Tier 0 is deterministic: the same input and preset must produce a
byte-identical file every time. That is an assertion, not a judgement call.

## 13. Content generation — `marketing-crosswalk` (`Content`)

The only module whose scenarios are **already automated** — `make test` and
`python3 -m generator.cli selftest` cover them. Nothing manual to run.

That is what every other section here should eventually look like.
