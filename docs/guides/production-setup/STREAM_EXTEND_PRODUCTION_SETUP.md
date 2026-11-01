# Stream Extend — production setup

**Labels:** `Stream` · Companion guide: [Creator Extend production setup](CREATOR_EXTEND_PRODUCTION_SETUP.md)
**Games authority:** [`STREAM_AUTOPILOT_GAME_EVALUATION.md`](../../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md)
**Status:** written from the code and module docs on this branch. Every step is runnable today
*unless* it is marked **NOT SHIPPED** or **EXTERNAL ACCEPTANCE** — read those markers literally.

This guide takes one MacBook Pro from a clean checkout to a public gaming stream. It is written
for someone who has never used OBS. Every step ends with something you run or look at, and a
stated pass condition. If a verification fails, stop — do not continue to the next section.

> **Read this first.** The repository's own verdict on what is real is
> [`docs/AUDIT.md`](../../AUDIT.md), and per-module maturity is [`CLAUDE.md`](../../../CLAUDE.md) §11.
> Most modules are `scaffolded`. This guide never tells you a scaffolded thing works.

**Markers used throughout:**

| Marker | Meaning |
|---|---|
| **SHIPPED** | Code exists and offline tests cover it. You can run the step now. |
| **EXTERNAL ACCEPTANCE** | Code exists but only a live run with real hardware/accounts proves it. You are the acceptance. |
| **NOT SHIPPED** | Documented intent only. Do it by hand; no command in this repo does it. |

---

## Contents

1. [Prerequisites](#1-prerequisites)
2. [Hardware baseline](#2-hardware-baseline)
3. [Streaming platform setup](#3-streaming-platform-setup)
4. [Games](#4-games)
5. [Stream Extend build + install](#5-stream-extend-build--install)
6. [Profile setup and the mid-stream switch test](#6-profile-setup-and-the-mid-stream-switch-test)
7. [AI generation + gameplay test](#7-ai-generation--gameplay-test)
8. [Private test stream (dry run)](#8-private-test-stream-dry-run)
9. [Public go-live checklist](#9-public-go-live-checklist)
10. [Failure modes and recovery](#10-failure-modes-and-recovery)

---

## 1. Prerequisites

Do these in order. Later steps assume earlier ones passed.

### 1.0 Repository and toolchain

Stream Extend is a Tauri 2 app: a Rust backend and a SvelteKit frontend. You need both toolchains
plus Python 3.12, which is what every module installer in this repo targets.

```bash
git clone https://github.com/OpenTechnology14/Open_Content_Creator_Platform.git
cd Open_Content_Creator_Platform
```

```bash
xcode-select --install || true
```

That is Apple's command line tools. It is a no-op if they are already present.

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
```

```bash
brew install node@22 python@3.12
```

**Verify all four — every line must print a version, not an error:**

```bash
git --version && rustc --version && cargo --version && node --version && python3.12 --version
```

Pass condition: `rustc` ≥ 1.77, `node` ≥ 20, `python3.12` reports 3.12.x. Node 22 is what the
apps' `package.json` devDependencies (Vite 6, SvelteKit 2, Svelte 5) are built against.

### 1.1 OBS Studio — the one non-negotiable dependency

Stream Extend does not encode or capture anything itself. It drives OBS over
obs-websocket v5. Without OBS there is no stream. `modules/creator-experience/setup/manual.md`
pins **OBS Studio ≥ 30.x**; obs-websocket 5.x is built into OBS 28+, so there is no separate
plugin to install.

```bash
brew install --cask obs
```

Or download from <https://obsproject.com/>.

Now enable the WebSocket server, which is off by default:

1. Open OBS.
2. **Tools → WebSocket Server Settings**.
3. Tick **Enable WebSocket server**.
4. Leave **Server Port** at `4455` — that is the default in `AppConfig::default()` at
   [`apps/stream-extend/src-tauri/src/lib.rs`](../../../apps/stream-extend/src-tauri/src/lib.rs).
5. Click **Show Connect Info**, copy the **Server Password**, and paste it somewhere temporary.
   You will type it into Stream Extend once, in §5.6, after which it lives in the macOS Keychain
   and is never displayed again.
6. **Apply**, then **OK**.

**Verify — this is the single most important check in the guide:**

```bash
python3.12 -m venv .venv                                               # once
.venv/bin/python -m pip install -r scripts/setup/requirements-obs.txt   # once: the OBS WebSocket client
.venv/bin/python scripts/setup/test_obs_websocket.py
```

Or, equivalently, `make test-obs` with that venv activated (`source .venv/bin/activate`). The script reads
`OBS_WEBSOCKET_HOST`, `OBS_WEBSOCKET_PORT` and `OBS_WEBSOCKET_PASSWORD` from the environment, then from the
repo-root `.env` (gitignored; see `.env.example`) for anything unset — give it the password from step 5 in
one of those. Pass condition: it reports a connection and an OBS version.
If it cannot connect, nothing downstream in this guide will work; fix it here.

### 1.2 FFmpeg

OBS bundles its own FFmpeg for encoding, but the module tooling and any manual clip inspection
want a system one.

```bash
brew install ffmpeg
```

```bash
ffmpeg -version | head -1
```

### 1.3 ComfyUI — only if you want AI generation on stream

ComfyUI is the AI image/video backend. **Stream Extend does not queue ComfyUI workflows** — that
is Creator Extend's job (`comfyui_queue_configured` is a Creator Extend command). Stream Extend
only stores a ComfyUI URL in its Connections view. Install ComfyUI here only if you are doing §7.

Follow [`modules/realtime-ai/setup/manual.md`](../../../modules/realtime-ai/setup/manual.md) —
it is the authority. The macOS path:

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git modules/realtime-ai/comfyui/app
cd modules/realtime-ai/comfyui/app
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Apple Silicon, torch installs with MPS support from the default index — do **not** use the
`--index-url .../cu121` line from the module doc; that is the CUDA path for Linux/WSL.

ComfyUI Manager is called non-negotiable by the module doc, and it is right — it is how you
install community nodes without cloning each one:

```bash
cd custom_nodes && git clone https://github.com/Comfy-Org/ComfyUI-Manager.git && cd ..
```

```bash
python3.12 main.py --listen 127.0.0.1 --port 8188
```

**Verify:**

```bash
curl -fsS http://localhost:8188/system_stats | head -c 200
```

Pass condition: JSON, not a connection error.

**Models.** The authoritative shopping list is
[`modules/realtime-ai/comfyui/models.md`](../../../modules/realtime-ai/comfyui/models.md). For a
16 GB M1 Pro that is also running OBS and a game, take the realtime column only:

| Slot | Model | Why this one on 16 GB |
|---|---|---|
| checkpoint | SD 1.5 (~4 GB) | The realtime LCM stylization candidate. SDXL's ~7 GB competes with the game for unified memory. |
| LoRA | LCM-LoRA SD1.5 (~50 MB) | Pairs with SD 1.5 for few-step inference. Without it, realtime is not realtime. |
| VAE | SDXL VAE | Only if you later move to SDXL. Skip for now. |

Do not download SDXL base, Flux Fill, or SAM ViT-H onto this machine for streaming work. The
games evaluation is explicit that the 3060's 12 GB "does not guarantee … enough memory for a game
plus all AI models simultaneously"; 16 GB of *shared* Mac memory is a tighter budget than that.
Heavy models belong on the Creator Extend render pass — see the
[companion guide §5](CREATOR_EXTEND_PRODUCTION_SETUP.md#5-ai-driven-content-pipeline).

### 1.4 Dependencies this guide deliberately does not install

You will find these in the repo's module tables. For a first gaming stream they are cost without
benefit, and several are **NOT SHIPPED** as automation:

| Tool | Module | Why skip for stream one |
|---|---|---|
| Blender | [`content-creation`](../../../modules/content-creation/setup/manual.md) | Render-side. Belongs on the Creator Extend pass, not the encode host. |
| Krita | [`image-editing`](../../../modules/image-editing/setup/manual.md) | Same. Desktop app, `automated.md` says no automation exists. |
| NodeCG broadcast graphics | [`broadcast-graphics`](../../../modules/broadcast-graphics/setup/manual.md) | `make up-with-graphics` works, but overlays are a second-stream problem. Add after your first clean recording. |
| Ollama / local LLM co-host | [`ai-agents`](../../../modules/ai-agents/setup/manual.md) | `automated.md`: datastore yes, Ollama no. The AI host is the biggest single source of first-stream failure. |
| VoiceMeeter / BlackHole routing | [`audio-production`](../../../modules/audio-production/setup/manual.md) | OS-level routing is manual. OBS's own audio mixer is enough for capture-card + mic. |

Add them one at a time, each with its own recording test, after §9 passes once.

### 1.5 Optional: the containerised services

Six modules have a genuinely automated path. None of them are required to stream.

```bash
cp .env.example .env
docker compose up -d
```

```bash
docker compose ps
```

Pass condition: Postgres, Redis and MinIO report healthy. This gives you MinIO for asset storage
and is the prerequisite for the observability dashboards the app's Dashboard view links to. If
you skip it, the Grafana/Platform API/n8n/NodeCG links on the Stream Extend dashboard will not
resolve — that is expected, not a bug.

---

## 2. Hardware baseline

Everything here is sourced from
[`STREAM_AUTOPILOT_GAME_EVALUATION.md`](../../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md).
That document is the authority; this section is the buy/don't-buy summary.

### 2.1 What you own

| Item | Spec | Role in this guide |
|---|---|---|
| MacBook Pro | M1 Pro, 8 CPU / 14 GPU cores, 16 GB unified memory | OBS host, encoder, AI host, soundboard, speech |
| Xbox Series S | — | Game source for the console-routed titles |

Two facts about the Mac that change what you can do, both from the evaluation doc:

- **The 16 GB is shared** between applications and graphics. It is not 16 GB of VRAM. A game, OBS,
  and an SD 1.5 model are all drawing on the same pool.
- **The Mac cannot run CUDA.** Any effects path that assumes CUDA is a tower-or-later path.

The Mac's HDMI port is an **output**. You cannot plug the Xbox into it.

### 2.2 What to buy now — one line item

| Item | Price | Status |
|---|---|---|
| **Elgato Game Capture 4K S** | **$159.99** | **Buy this. Nothing else yet.** |

The evaluation doc records Elgato's listed price of $159.99 and confirms the card lists Mac, Xbox
and OBS compatibility, with system requirements including Apple M1 or better. Before checkout,
verify the current macOS version and USB connection requirements on Elgato's own page — the doc
flags that as a check you must do, not one it did for you.

Connect it: **Xbox HDMI out → capture card HDMI in; card → a USB 3 port on the Mac directly.**
Not through a hub. Use HDMI passthrough on the card to your play monitor. Start capture at
**1080p60 SDR** — do not start at 4K or HDR.

### 2.3 What to buy later — and the gate

| Item | Allocation | Gate before buying |
|---|---:|---|
| One used tower incl. RAM upgrade | up to $650 | Xbox pilot passes a complete local recording with synchronized voice, avatar, chat and Soundbox |
| Cables/adapters | $40 | — |
| Tax/shipping reserve | $100 | — |
| **Planned ceiling** | **$949.99** | Leaves $50.01 under $1,000 |

Tower search target: Ryzen 5 5600 or i5-12400-class CPU, **RTX 3060 12 GB** (check the VRAM —
other 3060 variants exist), 32 GB RAM, 1 TB NVMe, supported Windows 11, standard replaceable PSU.

Three cautions the evaluation doc is explicit about, worth repeating because they cost money:

- This is a **spending ceiling, not a verified bundle**. The doc found low refurbished prices that
  included out-of-stock listings; no purchasable $650 system is claimed.
- A 32 GB RTX 3060 build is **below Tarkov's published recommended tier** (RTX 4070 / i7-14700F /
  64 GB). Passing Tarkov is explicitly not a gate for anything.
- Prefer NVIDIA over an RX 6600/6650 XT if you want a future CUDA effects path, but benchmark your
  AI software against the card before treating it as an AI workstation.

**Nothing has been purchased.** No hardware or cloud resource is selected, benchmarked, deployed
or funded. Do not read any row above as a completed transaction.

### 2.4 Capture topology

Staged baseline, from the evaluation doc's capture-layout section:

```
Xbox Series S ──HDMI──> Elgato 4K S ──USB 3──> MacBook Pro (OBS)
                            │
                            └──HDMI passthrough──> play monitor
```

Hard limits you cannot configure around:

- **One USB card gives one live picture.** An HDMI switch selects one source; it does not give you
  two simultaneous captures.
- **A PC captures its own game with no card.** When the tower arrives it does not need a second
  Elgato; keep the one card on the Xbox.
- **Capture count, encoder count and uplink are three separate ceilings.** As arithmetic only,
  three 6 Mbps outputs need 18 Mbps before audio and overhead.

---

## 3. Streaming platform setup

> **This section is where your public gamer profile gets built.** Everything from §3.0 on is
> identity work, not plumbing. The order matters: handle before accounts, accounts before clients,
> clients before any public broadcast. Doing it in a different order is how people end up with four
> different names on four platforms and no way to fix it.

### 3.0 Reserve three handles — do this before installing anything

**Do this first. Before OBS is configured, before a single game client is downloaded.**

You are publishing across **three separate accounts**, not one. That decision is upstream of
everything else in this guide, and reversing it later is the expensive kind of mistake — a switch
six months in orphans every link, every VOD reference, and every search result pointing at the old
name.

#### The three accounts

| Account | Carries | Platforms | Channel art needs |
|---|---|---|---|
| **Games** | All game content — Minecraft, Dota 2, Roblox now; CS2, GTA V, VALORANT, Tarkov, Fortnite, Overwatch, League, WoW, Among Us, BeamNG as they come online | Twitch (primary) + YouTube Gaming | Avatar, banner, Twitch panels, watermark |
| **Reactions** | Try Not to Laugh, Nova Reviews the Edit | Twitch + YouTube | Avatar, banner, panels, watermark |
| **OpenTechnology** | Blog walkthroughs, OpenTech Build Brief, OpenTechApp Workflow Clinic, livestreamed working sessions — all app and blog-side content | YouTube only | Avatar, banner, watermark. No Twitch panels needed |

**Why three and not one:** the audiences do not overlap and the content bars are incompatible. A
subscriber who came for Roblox does not want a Workflow Clinic in their feed, and a prospective
client evaluating OpenTechnology should not land on a Try Not to Laugh VOD. Separate accounts also
let each one build a coherent recommendation profile with the algorithm instead of confusing it.

> **Voice differs per account too.** Each account gets its own AI-host voice binding — energetic
> for Games, Latin-accented for Reactions, deep and measured for OpenTechnology. That is specified
> in the AI walkthrough and mascot system proposal (`P-066` in
> [`docs/PROPOSALS.md`](../../PROPOSALS.md)), not here. This guide only needs you to know the
> account split exists, so you reserve the right number of handles.

#### Step 1 — pick three candidates per account

Nine names total. Constraints that will actually bite you, on every one:

| Constraint | Why |
|---|---|
| 3–20 characters | Twitch's limit is 25, Roblox's is 20. 20 is your real ceiling |
| Letters, numbers, underscore only | Roblox allows one underscore and no other punctuation. Narrowest rule — obey it everywhere |
| No leading/trailing underscore | Rejected by Roblox |
| Readable when spoken aloud | You will say it on stream, and viewers will type it from memory |
| No year, no "TV", no "Live", no "Official" | These date you or imply a second, realer account somewhere |

**Related, not identical.** A shared root with a clear suffix — `<root>`, `<root>Reacts`,
`<root>Tech` — gets you cross-account recognition without one account's content bleeding into
another's recommendations. Three unrelated names throw away the recognition; three near-identical
ones confuse viewers about which is which.

#### Step 2 — check every surface that account actually needs

Not every account needs every surface. Check before claiming anything:

| Surface | Games | Reactions | OpenTech | Where |
|---|:---:|:---:|:---:|---|
| **Twitch** | ✅ primary | ✅ | — | <https://twitch.tv/signup> |
| **YouTube** | ✅ Gaming | ✅ | ✅ only | <https://youtube.com> → Settings → Channel → Handle |
| **Roblox** | ✅ | — | — | <https://www.roblox.com/signup> — **narrowest rules, not renameable for free** |
| **Minecraft Java (MSA)** | ✅ | — | — | <https://www.minecraft.net/msaprofile/mygames/editprofile> — changeable, with a cooldown |
| **Steam (Dota 2)** | ✅ | — | — | <https://store.steampowered.com/join/> — no Dota-specific ID; your Steam profile name is what viewers see |
| **Riot ID (League, VALORANT)** | ✅ later | — | — | <https://account.riotgames.com/> — only when those games enter the rotation |

Game-client handles belong to the **Games** account only. Reactions and OpenTechnology need no
game identity at all, which makes their checks much faster.

Also check the domain and X handle for each. Cheap to hold, expensive to lose.

#### Step 3 — decide now if one is unavailable

This is the decision people defer and regret.

- **Games handle unavailable on Twitch or Roblox** → the candidate is dead. Next candidate. Those
  two are non-negotiable: Twitch is the primary destination, and Roblox names are not freely
  renameable on your youngest-audience surface.
- **Reactions handle unavailable on Twitch or YouTube** → dead. Those are its only two surfaces.
- **OpenTechnology handle unavailable on YouTube** → dead. It has one surface, so there is no
  compromise available.
- **Unavailable on one minor surface only** → use a **consistent, predictable** suffix everywhere it
  is needed, never a different one per platform. Write the mapping down.
- **Available everywhere** → **claim all three accounts now**, in this sitting, including surfaces
  you will not use for months. Free, and about an hour total.

#### Step 4 — record the mapping

One table, somewhere you will find it in a year: account → handle → per-surface variant. You will
need it every time you add a platform or a game.

#### Step 5 — cross-promotion links (later, but plan for it now)

Once all three exist, link them to each other so a viewer who finds one can find the others:

- **YouTube:** Studio → Customization → Basic info → Links. Add the other two channels.
- **Twitch:** Settings → Channel → Panels. Add a panel linking the other accounts.

**Do this after each account has content**, not now. A link to an empty channel is worse than no
link — it advertises abandonment. Revisit once each has published something.

**Verify:** every surface marked ✅ above resolves to an account you control, under that account's
handle or its recorded variant. Open each profile URL in a browser, logged out, and confirm. Only
then continue to §3.1.

### 3.1 The three tracks

Your three accounts map onto profiles in the Social Management catalog at
[`modules/social-management/catalog.yaml`](../../../modules/social-management/catalog.yaml):

| Account | Content | Destinations | Catalog profile |
|---|---|---|---|
| **Games** | Game streams | Twitch (primary) + YouTube multi-cast | `stream-main` — `twitch` and `youtube` both carry `live-stream`. Use `agent-labs` for autonomy runs |
| **Reactions** | TNTL, Nova Reviews the Edit | Twitch + YouTube | **No dedicated profile yet.** `video-review` is the closest — `kind: content`, YouTube and TikTok both at `default_visibility: private`. It is a staging identity, not a live one |
| **OpenTechnology** | Blog walkthroughs, Build Brief, Workflow Clinic, working sessions | YouTube only | `opentech-marketing` — `kind: hybrid`, YouTube carries `live-stream` |

**The gap you should know about:** the catalog was written before the three-account split and has
no live-capable Reactions profile. `video-review` exists but is shaped for private review, not
broadcast. Adding one means editing `catalog.yaml` and rebuilding — the catalog is *compiled into*
the Tauri plugin, so it is a code change with a queue row, not a runtime setting (§6.2).

Until that lands, run Reactions content through `stream-main` and change the OBS destination by
hand. Note that this means the recording handoff will tag it with the wrong source profile, so fix
the content profile manually in Creator Extend's inbox.

Note that `stream-main` also declares Kick, Rumble, Trovo, DLive and Restream destinations. All
five are `adapter: catalog-only` with `connection_status: planned` and carry the note "Account and
ingest adapter acceptance is not implemented yet." They appear in the picker; they do not connect.
Leaving room for more platforms later is exactly what those rows are.

### 3.2 Twitch — primary

1. Create or sign in to your Twitch account at <https://twitch.tv>.
2. Complete **two-factor authentication**. Twitch requires 2FA before it will issue a stream key.
3. Go to **Creator Dashboard → Settings → Stream**.
4. Copy the **Primary Stream Key**.
5. In OBS: **Settings → Stream**. Service: **Twitch**. Click **Connect Account** if you prefer
   OAuth, or **Use Stream Key** and paste.
6. **Settings → Output**, set **Output Mode: Advanced**, then apply the encoder settings from
   [`modules/creator-experience/setup/manual.md`](../../../modules/creator-experience/setup/manual.md):
   rate control **CBR**, bitrate **6000 kbps** for 1080p60, keyframe interval **2**, profile
   **high**. On the M1 Pro your encoder is **Apple VT H.264 Hardware** — the NVENC presets in that
   doc are for NVIDIA and will not appear.
7. **Settings → Video**: base and output canvas **1920×1080**, downscale filter **Lanczos**,
   **60 FPS**.

**Verify:** OBS **Settings → Stream** shows a connected account or a saved key, and
**Settings → Output** shows CBR at 6000 with keyframe interval 2. Do not stream yet.

### 3.3 YouTube — multi-cast

YouTube requires live-streaming enablement, and it is not instant:

1. At <https://youtube.com/verify>, verify your channel by phone.
2. Enable live streaming in **YouTube Studio → Create → Go Live**.
3. **Wait 24 hours.** First-time activation has a 24-hour hold. Do this the day before, not the
   morning of.
4. Once enabled: **YouTube Studio → Go Live → Stream** tab. Copy the **Stream key** and the
   **Stream URL**.

YouTube is your *second* destination, which OBS cannot do natively — OBS streams to one RTMP
endpoint. The decision doc is
[`modules/creator-experience/obs-config/multi-platform.md`](../../../modules/creator-experience/obs-config/multi-platform.md).

**Evaluation for your specific situation — Restream vs obs-multi-rtmp:**

| Option | Cost | Latency | Verdict for an M1 Pro on home uplink |
|---|---|---|---|
| `obs-multi-rtmp` plugin | Free | None added | **Start here.** Two 6 Mbps streams = 12 Mbps up, plus overhead. The doc's own recommendation is to start here if bandwidth allows. |
| Restream / Castr | $16–49/mo | +200–500 ms | Move here only when uplink is the bottleneck or you need 4+ platforms. |
| Self-hosted NGINX-RTMP on a DO droplet | Droplet cost | Low if nearby | The config file "will live at `modules/infrastructure/digitalocean/nginx-rtmp.conf` when implemented" — it is deferred and does not exist. Not an option today. |

Before choosing, measure your actual uplink:

```bash
networkQuality -v
```

Pass condition for two-platform multicast: sustained upload **≥ 20 Mbps**. The multi-platform doc
suggests ≥ 50 Mbps for three streams; two at 6 Mbps needs 12 Mbps of payload and you want real
headroom above that. If you are under 20, stream Twitch only for your first outing and add YouTube
after §9 passes.

Install the plugin from <https://github.com/sorayuki/obs-multi-rtmp>, restart OBS, then
**Docks → Multiple Output**, **Add new target**, paste the YouTube URL and key.

**Verify:** the Multiple Output dock lists a YouTube target alongside OBS's own Twitch output.

> **Restream is in the catalog but not connectable.** `catalog.yaml` lists `restream` as
> `adapter: catalog-only`, `connection_status: planned`, with the note "Multistream account and
> ingest adapter acceptance is not implemented yet." If you subscribe to Restream, you configure it
> in OBS and in Restream's own dashboard — Stream Extend cannot drive it. **NOT SHIPPED.**

### 3.4 Chat and moderation

Chat is read by the autopilot config at
[`configs/local/twitch-chat.yaml`](../../../configs/local/twitch-chat.yaml), not by the Tauri app.
For your first stream, moderate in Twitch's own interface:

1. **Creator Dashboard → Settings → Moderation**.
2. Turn on **AutoMod** at level 2 or higher.
3. Add at least one human moderator. Do not solo-moderate a first public stream while also playing.
4. Set **Chat delay** to 2 seconds — it is the cheapest anti-raid measure there is.
5. Open <https://dashboard.twitch.tv/popout/u/YOUR_NAME/stream-manager/chat> on a second display.

The AI host's own moderation path lives in
[`modules/ai-agents/setup/manual.md`](../../../modules/ai-agents/setup/manual.md) and is
**NOT SHIPPED** as automation — `automated.md` for that module says the datastore is automated and
Ollama is not.

**Verify:** send a message from your phone's Twitch app and watch it arrive in the popout.

### 3.5 The OpenTech YouTube-only track

For OpenTechnologyApp / OpenTechnologyBlog content streams, use the `opentech-marketing` profile,
which is `kind: hybrid` — so it appears in **both** apps' profile switchers. Its YouTube
destination carries `account-read`, `live-stream` and `post-video`.

Switch OBS's stream destination to YouTube only (disable the multi-rtmp Twitch target), and select
`OpenTechMarketing` in the Stream Extend profile switcher before going live. The recording handoff
then tags the resulting file with that profile, so Creator Extend routes it to the blog pipeline
rather than the gaming one — see
[companion guide §7](CREATOR_EXTEND_PRODUCTION_SETUP.md#7-cross-links-to-opentechnologyapp--opentechnologyblog).

### 3.6 Branding artifacts — prepare these during setup, not after

An empty channel with a default avatar converts nobody. Prepare these while you are already in each
platform's settings, rather than making a second pass later.

**Three accounts means three sets.** Budget for that — it is the main cost of the account split,
and it is worth paying.

**What each surface needs:**

| Artifact | Spec | Games | Reactions | OpenTech |
|---|---|:---:|:---:|:---:|
| Profile picture | **256×256** PNG, square. Must read at 32 px | Twitch, YouTube, Roblox, Steam | Twitch, YouTube | YouTube |
| Channel banner | Twitch **1200×480**; YouTube **2560×1440** with a **1546×423** safe area | Both | Both | YouTube |
| Panel graphics | **320×100** PNG each | Twitch — About, Schedule, Socials | Twitch | — |
| Video watermark | **150×150** PNG, transparent | YouTube | YouTube | YouTube |
| About copy | 2–3 sentences | Twitch, YouTube, Steam | Twitch, YouTube | YouTube |

A Minecraft skin is separate from all of this and belongs to the Games account only.

**The 32-pixel rule.** Your profile picture will be seen at 32 px in a sidebar far more often than
at full size. Shrink it to 32 px and look at it. If it is mud, it is the wrong image — a face or a
single bold glyph survives; a detailed scene does not. Same discipline as the thumbnail
200-pixel rule in the
[companion guide §5.3](CREATOR_EXTEND_PRODUCTION_SETUP.md#53-generate-a-thumbnail).

**About copy — one version per account, reused across that account's surfaces.** Name what the
account actually carries; that is what someone deciding whether to follow is scanning for.

**Games:**

```
[GamesHandle] — Minecraft, Roblox, and Dota 2, with an AI co-host along for the ride.
Building an AI streaming setup in public and showing the work.
Live [days] at [time] [timezone].
```

**Reactions:**

```
[ReactionsHandle] — Try Not to Laugh, and an AI co-host with opinions about editing.
Reactions and breakdowns. The work gets the commentary, not the person.
```

**OpenTechnology:**

```
[OpenTechHandle] — Walkthroughs and working sessions for OpenTechnologyApp and the blog.
Build briefs, workflow clinics, and the occasional unedited working session.
```

Reuse each account's text verbatim across that account's own surfaces — Twitch, YouTube, and Steam
for Games. Divergent bios *within* one account read as abandonment. Divergent bios *between*
accounts are correct; they are different products.

The Reactions line about targeting the work rather than the person is not decoration. It is the
show bible's own rule for `VideoReview` — commentary targets editing choices, not the people in the
video — and stating it publicly is what keeps the format defensible.

**Can the platform auto-generate any of this? No — and here is exactly what it does do.**

I checked rather than assumed. `apps/shared/social-manager` compiles **four fixed brand assets**
into both apps and serves them to the webview as data URLs — `hybrid-platform`, `stream-extend`,
`creator-extend` and `opentechapp`, each declared with a `logo_path` in
[`modules/social-management/catalog.yaml`](../../../modules/social-management/catalog.yaml). That is
a **serving** mechanism for the platform's own product logos, not a generator, and they are not your
channel's branding. No channel-art, banner, or panel generator exists in this repository.
**NOT SHIPPED.**

What does genuinely help is the Creator Extend ComfyUI path, used as an image generator:

1. Generate banner and avatar art with a committed workflow and SDXL — the same queue path as
   thumbnails, [companion guide §5.3](CREATOR_EXTEND_PRODUCTION_SETUP.md#53-generate-a-thumbnail).
2. Composite text and crop to each spec in Krita —
   [companion guide §5.4](CREATOR_EXTEND_PRODUCTION_SETUP.md#54-finish-the-thumbnail).
3. Upload by hand in each platform's settings.

That covers three of the five artifacts with tools you are installing anyway. Treat it as "generate
the raster, assemble by hand," not as automation.

**One visual constraint, accepted now:** a single color palette and a single typeface across every
artifact and all three games. Per-game *overlay* variants are fine. Per-game *branding* is how a
profile stops looking like one person.

**Verify:** open every surface of all three accounts in a browser while **logged out** — both
Twitch channels, all three YouTube channels, and your Steam profile. Each shows that account's
avatar, banner and About copy. Logged out is the point: that is what a new viewer sees.

---

## 4. Games

The authority for every claim in this section is
[`STREAM_AUTOPILOT_GAME_EVALUATION.md`](../../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md).
**All ten games remain pending until tested.** Installing a client is not acceptance evidence.
Nothing below has been benchmarked.

### 4.1 The Mac rotation — three games

Your Mac rotation is **Minecraft Java, Roblox, and Dota 2**. Deep setup for each is below. The
other Mac-viable titles from the evaluation doc are deferred — see §4.1.4.

Three games is the right number. It is enough for a recognizable schedule and few enough that you
can actually pass the acceptance recording on each one before going public.

**Audience shape drives your profile settings, so decide this before you configure anything:**

| Game | Audience | Content bar | Positioning consequence |
|---|---|---|---|
| **Minecraft Java** | Broad, all ages. The widest funnel of the three | **Family-friendly by default.** Assume minors are watching | Highest algorithmic upside, and it is the autonomy target — the "AI plays Minecraft" hook is the most legible thing you can show a new viewer. Keep chat rules strict and language clean |
| **Roblox** | **Skews young.** Meaningfully younger than Minecraft | **Highest moderation bar of the three.** Treat it as a kids' platform, because it is | Your content-appropriateness standard here sets the ceiling for your whole channel — a clip from a Roblox stream is the one most likely to be surfaced to a young viewer. No edgy humor, no exceptions |
| **Dota 2** | Small but hardcore. Lowest casual traffic | Adult audience; language bar relaxes | **Higher skill expectations.** This audience can tell whether you know the game. Position as learning-in-public or analysis if you are not strong — pretending is the fastest way to lose them. Retention here is earned by competence, not personality |

The practical conflict: Roblox's moderation bar and Dota 2's relaxed one are incompatible on a
single identity if you drift. Pick the **strictest common standard** — Roblox's — and hold it
across all three. One channel, one standard. Splitting into two personas fragments exactly the
profile you are trying to build (§3.0).

This maps directly onto audience mode in the profile switcher: see
[§6.2](#62-the-profiles-you-get) for which catalog profile to select per game.

#### 4.1.1 Minecraft Java — the first autonomy target

This is where you start, for a reason the evaluation doc makes explicitly: it is the first desktop
autonomy candidate, via a *permitted environment*.

1. Buy and download the launcher from <https://minecraft.net>.
2. Launch, sign in, and select a **Java Edition** profile. Bedrock is what the Xbox runs; the two
   are different editions and are not interchangeable.
3. **Pin your version, render distance, and modpack** before any test. The doc requires this —
   requirements were revised July 2026 and an unpinned test is not repeatable.
4. Suggested first pin: latest release, render distance **12 chunks**, **no shaders**, vanilla.
   There is no shader or RTX guarantee on this hardware.

OBS capture settings for Minecraft on macOS:

- Source type: **macOS Screen Capture**, then **Window Capture** mode, target the Minecraft window.
  Game Capture is a Windows-only OBS source; it does not exist on macOS.
- Grant OBS **Screen Recording** permission in **System Settings → Privacy & Security → Screen
  Recording**, then fully quit and reopen OBS. It will not work until you restart it.
- Set the source to **1920×1080**, and in Minecraft run windowed at 1920×1080 so the capture is
  1:1 with no rescale.

**Permitted-automation notes.** Read this before writing a single line of bot code:

- Game-playing automation is a **separate capability gate** from capture, voice and chat. The doc
  is explicit: "Capture/voice/chat support does not authorize or implement gameplay bots."
- What exists today is the autopilot *lifecycle rehearsal* — a supervisor that plans a session. It
  does not play. See §7.3.
- Minecraft is the candidate because a *permitted environment* (your own server, your own world,
  under Mojang's terms) is achievable. Dota 2's supported bot scripting is the documented
  alternative. Neither is implemented here.
- **NOT SHIPPED:** no game adapter in this repo plays a game or releases input back to a human.
  Physical input release and return to agent control "still require device/game-specific
  implementation and acceptance."

> **Autonomy risk — verify permission before anything runs unattended live.**
>
> The evaluation doc sets a rule for hardware claims: do not count compatibility-layer experiments
> as supported. **Apply the same discipline to automation.** A bot that "works when I tried it" is
> not a permitted automation any more than a game running under a translation layer is a supported
> platform. Both are experiments you have not earned the right to call working.
>
> Before anything automated runs on a live public stream:
>
> 1. **Confirm the environment permits it.** For Minecraft that means your own server, your own
>    world, under Mojang's terms — not a public server whose rules you have not read, and not a
>    third-party client. Write down which specific permission you are relying on.
> 2. **Run it unattended and offline first**, recording locally, for at least as long as you intend
>    to stream it. A bot that desyncs at minute 40 will desync at minute 40 in public.
> 3. **Keep a hand on the stop.** Verify you can stop the automation and take over mid-session
>    *before* you need to. The evaluation doc requires verifying "stop/mute and session switching
>    during speech and a Soundbox clip" — the same check applies to input handover.
> 4. **Never leave an autonomous session live and unwatched.** The failure you cannot recover from
>    is the one that happened while nobody was looking and went straight to VOD.
>
> If you cannot satisfy step 1 in one sentence naming the permission, the answer is no.

**Verify:** make a 60-second local OBS recording of Minecraft with your mic. Play it back. Picture
sharp at 1080p, audio in sync, no dropped-frame warning in OBS's status bar.

#### 4.1.2 Roblox

Official Mac client. The evaluation doc's qualification is the one that matters: experiences vary
substantially, so **validate the specific experiences you intend to stream**, not "Roblox."

**Install:**

```bash
open https://www.roblox.com/download
```

Install the downloaded `.dmg`, then launch Roblox once from Applications so it completes its
first-run update before you ever try to capture it.

**Client setup:**

1. Sign in with the handle you reserved in §3.0.
2. **Settings → Privacy.** You are streaming to a young audience — turn off anything that surfaces
   your friends list or your real details on screen.
3. **Settings → Graphics.** Set **Graphics Mode: Manual**, quality **7–8 of 10**. Roblox's
   auto-quality moves the slider mid-session, which changes your frame pacing while you are live.
   Pin it.
4. **Settings → Display → Full Screen: Off.** Run windowed at 1920×1080 so OBS captures 1:1.
5. Pick your rotation of **two or three specific experiences** and write down their names and
   creator. Each one is a separate performance profile.

**OBS capture:** same **macOS Screen Capture → Window Capture** path as Minecraft (§4.1.1),
targeting the Roblox window. Screen Recording permission and the OBS restart apply identically.

One Roblox-specific trap: Roblox re-creates its window when you join a different experience, so a
Window Capture source bound to the old window goes black on the join. Either re-select the window
in source properties after joining, or use **Display Capture** cropped to the Roblox window for a
session where you will hop between experiences. Test this before going live — it is the most likely
way a Roblox stream breaks.

**Automation notes.** No adapter exists. The evaluation doc says Roblox "VM compatibility is
unverified" and that the capture and input adapter must be validated separately. Treat Roblox as a
human-play game for now.

**Content bar — the operational rule.** This audience skews young. Before you stream an experience,
play it privately once and ask whether you would be comfortable with a clip from it in front of a
10-year-old, because that is the realistic outcome. If the answer is anything but yes, pick a
different experience.

**Verify:** join your first target experience, record 60 seconds in OBS with mic, then **join a
second experience without stopping the recording**. Play it back. Both segments have picture — no
black frames at the join. That transition is the actual test.

#### 4.1.3 Dota 2

A Mac client exists, but **Valve's requirements table still specifies Intel**, so M1 compatibility
is something you test, not something you assume. This is the least certain of your three.

**Install:**

```bash
brew install --cask steam
```

Then launch Steam, sign in, and install Dota 2 from the store page. Free to play.

**Client setup:**

1. Set your Steam profile name to the handle from §3.0. Your Steam account is your identity here —
   there is no separate Dota ID to reserve, but the displayed name is what viewers see.
2. **Settings → Video.** Windowed at 1920×1080. Turn **off** the advanced options first pass —
   no ambient occlusion, no high-quality water, no tree wind. Frame-time stability beats fidelity
   on a machine that is also encoding.
3. Set **Maximum frames per second** to **60**, matching your OBS canvas. An uncapped Dota will
   happily spend GPU you need for the encoder.
4. **Settings → Options → Advanced Options → Enable Console** if you intend to look at bot
   scripting later.

**OBS capture:** same Window Capture path. Dota is the heaviest of your three on this hardware —
watch OBS's **rendering lag** indicator specifically, not just encoding lag. Rendering lag means
the Mac could not composite the frame; it is the first thing that gives out here.

**Test it properly, because the menus lie.** The evaluation doc is explicit: test a **busy team
fight and a long session**, not only menus. Dota's menu runs beautifully on anything. A five-hero
teamfight with spell effects in minute 45 is the actual workload. Specifically:

1. Run a bot match, not a demo — demo mode does not reproduce the load.
2. Play **at least 40 minutes**, into the late game where effects stack.
3. Record the whole thing locally while playing.
4. Afterwards, record average FPS, **1% lows**, and OBS's rendering and encoding lag.

**Automation notes.** Dota 2 has **supported bot scripting** — the evaluation doc names it as the
documented alternative to a Minecraft permitted environment. That makes it the second autonomy
candidate, and it is genuinely supported by Valve rather than tolerated. But: nothing in this repo
implements it, and the autonomy risk rules in §4.1.1 apply unchanged. Supported-by-Valve is step 1
of four, not a green light.

**Positioning.** This audience notices skill. If you are not strong at Dota, say so on stream and
frame the segment as learning or analysis — that is a viable position with this crowd, and
pretending is not.

**Verify:** a 40-minute bot match recorded locally, played back, with average FPS, 1% lows and both
OBS lag figures written down. If rendering lag is non-zero during teamfights, drop Dota's settings
before you drop anything else.

#### 4.1.4 Deferred — future adds

The evaluation doc lists two more Mac-viable routes. Both are **out of the rotation for now**, and
the reason is the same in each case: three games you have accepted beats five you have not.

| Game | Mac status | Why deferred | Reopen when |
|---|---|---|---|
| **League of Legends** | Candidate — Riot's localized requirements explicitly list Apple M1 | Adding a fourth MOBA-adjacent title alongside Dota 2 splits the same audience twice. Pick one MOBA first | Dota 2 has passed its acceptance recording and you want a second, broader-audience MOBA. Note the doc makes no assumption of native ARM compilation — test the current client |
| **Fortnite** | **No supported native Mac build.** Cloud only, via GeForce NOW | Capturing a cloud-streamed window stacks cloud latency on top of encode latency, and the picture is worse than the Series S route | You want Fortnite at all — in which case use the **Xbox Series S** (§4.2), not the Mac. That is the better picture and the simpler path |

Two constraints to carry forward if you do reopen either:

- **No cloud-VM path for League.** Vanguard is VM-incompatible and Shadow's compatibility list names
  it explicitly.
- **Do not generalize approved cloud gaming to arbitrary VMs.** GeForce NOW being supported for
  Fortnite says nothing about renting a GPU VM for it.

All eight remaining titles stay routed through Xbox or the planned tower, unchanged — §4.2.

### 4.2 Xbox / Windows-tower routing

These eight have **no supported macOS client**. Do not attempt them on the Mac — and specifically,
the evaluation doc says not to count compatibility-layer experiments as supported.

| Game | Route today | Route when the tower lands |
|---|---|---|
| Counter-Strike 2 | — (no console version) | Windows. GTX 1660 Super / RTX 2060-class or better. A 144+ FPS competitive target needs its own CPU/frame-time assessment. |
| VALORANT | **Xbox Series S** | Windows. GTX 1650-class or better. Prefer Series S or a physical PC — Vanguard blocks VMs. |
| GTA V | **Xbox** (GTA V/Online) | RTX 3060 12 GB for Enhanced; Legacy is lighter. FiveM roleplay is a separate PC/server evaluation, not Xbox GTA Online. |
| Overwatch | **Xbox Series S** | GTX 1660 Super / RTX 2060-class. Measure frame times at your chosen preset. |
| Fortnite | **Xbox Series S** | GTX 1660 Super / RTX 3060 reduced; RTX 3070-class for the Epic preset. |
| Among Us | **Xbox** (officially supported) | Modern integrated graphics. Innersloth explicitly lists Mac as unsupported. No GPU purchase is justified by this game alone. |
| Escape from Tarkov | — | RTX 3060 12 GB as a *budget trial only*. Publisher recommends RTX 4070 / 64 GB. Test demanding maps. |
| MSFS 2024 / BeamNG | — | Tower. Both appear as `agent-labs` show profiles in the social catalog (`flight-simulator-agent`, `beamng-agent`); no adapter exists. |

**Xbox capture procedure — do this once, it applies to all console titles:**

1. Xbox HDMI out → Elgato 4K S HDMI in. Card USB → Mac USB 3 port, directly.
2. Card HDMI out (passthrough) → your play monitor.
3. On the Xbox: **Settings → General → TV & display options → Resolution 1080p, Refresh rate 60Hz**.
   Then **Video modes** and **turn off Allow HDR** and **Allow 4K**. Start at 1080p60 SDR as the
   evaluation doc directs. Raise it later, once a recording has passed.
4. Run the repo's capture scanner:

```bash
python3.12 scripts/setup/capture_devices.py
```

On macOS this reports AVFoundation devices. Pass condition: the Elgato appears as both a video and
an audio device. If it does not, the problem is the cable, the port, or the Xbox's HDCP setting —
not OBS.

5. In OBS: **Sources → + → Video Capture Device**. Select the Elgato. Set **1920×1080**, **60 fps**.
6. Add the card's audio: either select it as the device's audio input, or add a separate
   **Audio Input Capture** source pointing at the Elgato.

**Verify:** you see and hear live Xbox gameplay in the OBS preview, and the OBS audio mixer shows
the capture card's meter moving. Make a 60-second recording and play it back before going further.

---

## 5. Stream Extend build + install

### 5.1 What you are building

A Tauri 2 desktop app. Rust backend at
[`apps/stream-extend/src-tauri/src/`](../../../apps/stream-extend/src-tauri/src/), SvelteKit
frontend at [`apps/stream-extend/src/`](../../../apps/stream-extend/src/), and five shared
crates/components pulled in from [`apps/shared/`](../../../apps/shared/).

An `apps/stream-extend/README.md` does not exist — this section is written from the source
and from [`modules/infrastructure/setup/desktop-setup.md`](../../../modules/infrastructure/setup/desktop-setup.md),
which is the app launch and setup authority.

> **Prebuilt installers exist.** Private Windows x64 and Apple Silicon Mac installers are produced
> by the Desktop installers workflow (private development evidence; not distributed).
> If you can reach that workflow's artifacts, download the `.dmg` and skip to §5.5. Build from
> source when you cannot, or when you are changing code.

### 5.2 Install frontend dependencies

```bash
cd apps/stream-extend && npm ci
```

`npm ci` rather than `npm install` — there is a committed `package-lock.json` and you want the
exact tree it pins.

**Verify:**

```bash
npm run check
```

Pass condition: `svelte-check` reports **0 errors**. Warnings are acceptable. This runs
`svelte-kit sync` first, which generates the `.svelte-kit` types the build needs.

### 5.3 Build the frontend

```bash
npm run build
```

**Verify:**

```bash
ls build/index.html
```

Pass condition: the file exists. `adapter-static` emits the SPA that Tauri embeds.

### 5.4 Build and bundle the app

First, prove the Rust side compiles and its tests pass:

```bash
cargo test --locked --manifest-path src-tauri/Cargo.toml
```

Pass condition: all tests pass. This includes
[`apps/stream-extend/src-tauri/tests/obs_contract.rs`](../../../apps/stream-extend/src-tauri/tests/obs_contract.rs),
the fake-OBS WebSocket contract. That test is what proves the §6 handoff logic: recording starts
before streaming, stop returns the real path, and an already-active recording is neither claimed
nor stopped.

Then bundle:

```bash
npm run tauri build
```

This takes 10–25 minutes on a first run — it compiles the entire Rust dependency tree including
`obws`, `tokio`, and the relay client. Subsequent builds are minutes.

**Verify:**

```bash
ls -d src-tauri/target/release/bundle/macos/*.app src-tauri/target/release/bundle/dmg/*.dmg
```

Pass condition: both an `.app` and a `.dmg` exist.

### 5.5 Entitlements and first launch

The bundle is **ad-hoc signed**, not notarized. macOS Gatekeeper will refuse it on first open.

```bash
open src-tauri/target/release/bundle/macos/
```

Then, in Finder, **right-click the app → Open → Open**. Using right-click-Open is what registers
the exception; double-clicking will just be blocked again.

If Gatekeeper still refuses:

```bash
xattr -dr com.apple.quarantine src-tauri/target/release/bundle/macos/Stream\ Extend.app
```

Then grant the three permissions the app's work actually needs, in
**System Settings → Privacy & Security**:

| Permission | Why | Granted to |
|---|---|---|
| **Screen Recording** | Window/display capture for Mac-native games | **OBS**, not Stream Extend — OBS does the capturing |
| **Camera** | Webcam source | OBS |
| **Microphone** | Mic source | OBS |

Stream Extend itself needs no capture entitlement. It drives OBS over a local WebSocket and reads
and writes its own files under `~/Library/Application Support/HybridCreatorPlatform/`. Secrets go
to the macOS Keychain via the shared `local-settings` crate — the OBS password crosses the boundary
exactly once, on save, and after that the UI only ever sees an `obs_password_set` boolean.

**Verify:** the app window opens and the header shows **Stream Extend** with an
**OBS Disconnected** indicator. Disconnected is correct at this point — you have not entered
credentials yet.

### 5.6 First-run wizard

The app opens on six workspace tabs: **Module setup**, **Connections**, **Remote control**,
**Social**, **Automated streaming**, **Dashboard**.

**Step 1 — Connections.**

1. Click **Connections**.
2. **OBS host**: `localhost`. **OBS WebSocket port**: `4455`.
3. **New OBS password**: paste the password from §1.1.
4. Fill the rest only if you ran §1.5's Docker stack: ComfyUI `http://localhost:8188`,
   Grafana `http://localhost:3000`, Platform API `http://localhost:8000`.
5. Click **Save and test OBS** — not "Save settings". The test variant runs the connection
   diagnostic immediately.

Pass condition: a success message. If it fails, the diagnostic returns a specific state, and each
one has one cause:

| Diagnostic state | What it means | Fix |
|---|---|---|
| `websocket_unreachable` | Nothing answered on 4455 | OBS is closed, or **Tools → WebSocket Server Settings → Enable** is unticked |
| `authentication_failed` | OBS rejected the password | Re-copy from **Show Connect Info**; re-save |
| `incompatible` | OBS or obs-websocket version mismatch | Update OBS Studio to ≥ 30.x |
| `handshake_failed` | Answered, handshake failed | Check authentication and WebSocket settings |

**Step 2 — Module setup.**

1. Click **Module setup**.
2. Tick **Automation / Control**. This is required — the Automated streaming tab's bridge looks for
   an interpreter at `.venv-modules/automation-control/bin/python` and errors with "Install
   Automation / Control in Module setup before running Autopilot checks" if it is absent.
3. Tick **Social Management**. Its isolated Python environment is what the OAuth loopback service
   in §6 runs from, and it is shared by both apps.
4. Click the installer and wait for durable progress to complete.
5. Click **Scan capture hardware**. Select the Elgato as the video source and its audio input as the
   capture-card audio source. Save.
6. Click **Check readiness**.

Pass condition: both checks in
[`configs/setup/stream-extend.json`](../../../configs/setup/stream-extend.json) report **ready** —
`stream.obs.websocket` ("Authenticated to OBS WebSocket and read its version") and
`stream.obs.scenes` ("OBS returned a non-empty scene collection").

> **This gate is real and it is deliberate.** Until both pass, the `obs-control` capability stays
> locked and the Dashboard shows: "OBS controls are locked until the current WebSocket and scene
> checks pass." If `stream.obs.scenes` is blocked, the fix is in OBS — create or import at least one
> scene. Selecting a capture device in Module setup does **not** mark capture ready; the shared UI
> is explicit that it "does not open the device or mark capture ready without the separate OBS
> recording acceptance step."

**Step 3 — Dashboard.**

Click **Dashboard**. Your OBS scenes appear as buttons. Click one.

**Verify:** OBS switches to that scene and the button highlights as active. The scene-switch command
re-reads the scene list after switching, so the highlight is OBS's own observed state, not an
optimistic UI guess.

---

## 6. Profile setup and the mid-stream switch test

This section covers the P-065 work merged in `c409a34`. The proposal is
[`PROPOSAL_RECORDING_HANDOFF_AND_PROFILE_WORKSPACES.md`](../../proposals/PROPOSAL_RECORDING_HANDOFF_AND_PROFILE_WORKSPACES.md);
its queue state is `Code complete — external acceptance open`, authoritative in
[`docs/PROPOSALS.md`](../../PROPOSALS.md). Everything below marked **SHIPPED** has offline test
coverage. The live-OBS half is **EXTERNAL ACCEPTANCE** — you are the acceptance.

### 6.1 What a profile is

A profile is a **workspace**: a brand, a provider, a capability, and a connected account, remembered
as a set. The component is
[`apps/shared/ui/ProfileSwitcher.svelte`](../../../apps/shared/ui/ProfileSwitcher.svelte), and it
sits in the app header — visible from every view, not buried in settings.

Two properties that matter operationally:

- **Per-profile routing memory.** Social Management remembers the selected brand, provider,
  capability and connected account *separately for every profile*. Switching back restores that
  profile's last route rather than resetting you to the first account. This is the entire point of
  the feature.
- **Kind filtering.** `ProfileSwitcher.svelte` filters to `item.kind === kind || item.kind === 'hybrid'`.
  In Stream Extend (`kind="stream"`) you see stream and hybrid profiles. Content-only profiles do
  not appear.

### 6.2 The profiles you get

From [`modules/social-management/catalog.yaml`](../../../modules/social-management/catalog.yaml),
these appear in Stream Extend's switcher:

| Profile | Kind | Use it for | Live destinations |
|---|---|---|---|
| **Main Stream** (`stream-main`) | stream | Your default gaming stream | YouTube, Twitch (+ 5 planned) |
| **Agent Game Labs** (`agent-labs`) | stream | Autonomy experiments — carries `flight-simulator-agent`, `beamng-agent`, `roblox-agent` show profiles | YouTube, Twitch, Kick |
| **OpenTechMarketing** (`opentech-marketing`) | hybrid | OpenTechnologyApp/Blog content streams | YouTube |

Per game, per platform, per audience mode — using the audience shapes from
[§4.1](#41-the-mac-rotation--three-games):

| Session | Account | Profile | Platforms | Audience mode — what to actually change |
|---|---|---|---|---|
| **Minecraft**, human-played | Games | **Main Stream** | Twitch + YouTube | Family-friendly. Clean language, strict chat rules, broad-appeal overlay tone |
| **Minecraft**, autonomy run | Games | **Agent Game Labs** | Twitch + YouTube | Technical framing. Show the supervisor state; explain what the automation is doing. Different overlay, same language bar |
| **Roblox** | Games | **Main Stream** | Twitch + YouTube | **Strictest setting of all.** Followers-only chat on by default, AutoMod at its highest, no edgy humor. Assume minors |
| **Dota 2** | Games | **Main Stream** | Twitch + YouTube | Adult audience, relaxed language bar — but hold the §4.1 common standard. Analysis-forward overlay; assume viewers know the game |
| **TNTL / Nova Reviews the Edit** | Reactions | `video-review`, or `stream-main` with a manual destination — see §3.1 | Twitch + YouTube | Commentary targets the work, never the person. Rights confirmed before any clip airs |
| **Lesson / product content** | OpenTech | **OpenTechMarketing** | YouTube only | Professional. No gaming overlay at all. See §3.5 |

**The trap to avoid:** letting Dota 2's relaxed bar leak into a Roblox stream because both run under
**Main Stream**. The profile changes routing, not your behavior. Hold the strictest common standard
across every session on that profile — §4.1 explains why splitting into two personas costs more
than it saves.

Adding a profile means editing `catalog.yaml` and rebuilding — the catalog is *compiled into* the
Tauri plugin, per the social-manager README. There is no in-app profile creation. Treat that as a
code change with a queue row, not a runtime setting.

### 6.3 Connect accounts

1. **Social** tab.
2. Pick **Main Stream**.
3. For **Twitch**, capability **live-stream**, click authorize.

Consent opens in your **system browser**, not in the app webview — providers reject embedded
webviews, so this is deliberate. The loopback service binds `127.0.0.1:8765`. Tokens go to the macOS
Keychain; the webview receives only the authorization URL and redacted connection records.

Twitch's `live-stream` capability requests the `channel:read:stream_key` scope. Per the catalog's
own note, the stream key is returned only to the live handoff and is **never persisted**.

4. Repeat for **YouTube**, capability **live-stream**. YouTube needs `SOCIAL_YOUTUBE_CLIENT_ID` and
   `SOCIAL_YOUTUBE_CLIENT_SECRET`, and its catalog notes require that you enable **YouTube Data API
   v3** and **YouTube Live Streaming API** at <https://console.cloud.google.com/apis/credentials>,
   and that the channel be eligible for live streaming.

**Verify:** the header switcher shows `twitch · account routed` when Main Stream is active. The
literal string `no account selected` means the OAuth did not complete.

### 6.4 The mid-stream profile-switch test

This is the specific end-to-end test. Budget 15 minutes. Do it **before** any public stream.

**Setup**

1. OBS open, Elgato connected, Xbox on and showing gameplay.
2. Stream Extend open on **Dashboard**.
3. In OBS **Settings → Stream**, point at Twitch. Set the Twitch broadcast to unlisted or run it on
   a throwaway channel — this test does go live.
4. Header switcher set to **Main Stream**.

**Run**

| # | Action | Expected | Why it matters |
|---|---|---|---|
| 1 | Note OBS is not recording and not streaming | Both idle | `start_live_session` refuses if OBS is already streaming, and will not claim a recording OBS already owns |
| 2 | Click **🔴 Go Live + Record** | Button becomes **⬛ Stop + Send to Creator**; stats row appears | One click starts recording *then* streaming. If streaming fails, the recording it started is rolled back |
| 3 | Check OBS | **Both** the REC and LIVE indicators are on | The recording is Stream Extend's, not yours |
| 4 | Read the stats row | Shows kbps, `Skipped: n/m`, and **`Recording for Creator Extend`** | That third string is the ownership marker. If it says `External recording not owned`, OBS was already recording and Stream Extend correctly declined to claim it — stop, stop OBS's recording, and restart the test |
| 5 | **Wait 3 minutes.** Play. Talk. | Skipped frames stay near 0 | You need real footage, not a 5-second file |
| 6 | **Mid-stream:** switch the header profile to **Agent Game Labs** | Switcher updates; sub-label shows that profile's own routing | **The stream does not drop.** The switcher changes *workspace routing*, not the OBS output |
| 7 | Switch back to **Main Stream** | Its previous provider and account are **restored**, not reset | This is per-profile preference restoration — the headline behavior of P-065 |
| 8 | Play 1 more minute | — | Proves the switch did not destabilize the session |
| 9 | Click **⬛ Stop + Send to Creator** | Message: `Recording <name> is ready in Creator Extend.` | OBS finalized the file and `library.register()` accepted it |

**Pass condition:** step 9 produces that exact message shape, naming a real file.

**If step 9 instead says** "OBS finalized the recording, but Creator Extend inbox registration
failed: … Import the file manually in Creator Extend" — the video is safe. Registration failed, not
recording. The inbox only accepts canonical, non-empty local video files; the usual cause is an OBS
recording path on a volume the app cannot canonicalize. Import it by hand in Creator Extend and fix
the OBS recording path to a local SSD folder.

**Understand what step 6 does and does not do.** The profile switcher changes which brand, provider
and account subsequent actions route to. It does **not** reconfigure OBS scenes, swap encoder
settings, or change your RTMP destination mid-broadcast. If you want different scenes per game, make
them OBS scenes and switch them from the Dashboard's scene buttons. Expecting a profile switch to
re-point your stream is the single most likely misreading of this feature.

**Then hand off.** Open Creator Extend and confirm the recording is in the inbox before you call
this passed — that is
[companion guide §4](CREATOR_EXTEND_PRODUCTION_SETUP.md#4-recording-library-setup).

### 6.5 Boundaries you must not design around

From the proposal's own boundaries section:

- A stream you start **directly in OBS** is not claimed by Stream Extend. Only the in-app
  live-session control produces a handoff. Always use the app's button.
- The ownership marker is **in memory only** and deliberately does not survive a crash. After an app
  restart, Stream Extend will not claim or stop recording work it can no longer prove it owns.
- Registration **does not copy, move or upload** the video. It records a canonical path. If you move
  the file afterwards, the inbox marks it unavailable.
- Creator Extend's recording state (`ready`, `editing`, `archived`) is workflow metadata, not proof
  that editing or publishing happened.

---

## 7. AI generation + gameplay test

**Target: Minecraft Java on the Mac, one AI-gen mode, one captured end-to-end session.**

### 7.1 Set expectations before you start

On a 16 GB M1 Pro running Minecraft, OBS, and an encoder, you are not getting per-frame realtime
stylization at 60 fps. The honest target is **on-demand generation between gameplay beats** —
viewer-prompted images that appear as an overlay for a few seconds. Plan the show around that.

### 7.2 Configure ComfyUI for the realtime slot

With ComfyUI running from §1.3:

1. Place SD 1.5 in `ComfyUI/models/checkpoints/`.
2. Place LCM-LoRA SD1.5 in `ComfyUI/models/loras/`.
3. Restart ComfyUI.

```bash
curl -fsS http://localhost:8188/object_info/CheckpointLoaderSimple | head -c 400
```

Pass condition: your SD 1.5 filename appears in the returned node info. If it does not, ComfyUI did
not see the file — check the folder and restart.

**Prompts.** Keep them short and pre-written; do not compose on stream. Three that suit a Minecraft
build stream:

```
a cozy oak cabin in a pine forest, warm lantern light, painterly, soft focus
an isometric redstone contraption, technical diagram style, clean lines, blueprint
a vast cave system with glowing crystals, dramatic lighting, atmospheric
```

Keep a `negative` of `blurry, watermark, text, distorted` on each.

**Render latency — measure it, do not assume it.** Queue one prompt and time it:

```bash
time curl -fsS -X POST http://localhost:8188/prompt -H 'Content-Type: application/json' -d @your-workflow-api.json
```

That times the *enqueue*, not the render. For the real figure, watch the ComfyUI console for the
per-run seconds line. Pass condition for on-stream use: **under 15 seconds** at SD 1.5 + LCM, 512×512,
4–8 steps. Above 25 seconds, cut the resolution or the step count — an audience will not wait.

**Queueing from an app is Creator Extend's job.** Stream Extend has no `comfyui_queue` command; the
frontend queue path (`comfyui_queue_configured`, with a preflight against live node and model
inventory) is registered in Creator Extend only. During a stream, either queue from the ComfyUI web
UI on a second display, or run Creator Extend alongside.

### 7.3 Autopilot — what "Automated streaming" actually does

The **Automated streaming** tab is a **lifecycle rehearsal**, not a game bot. Read
[`apps/stream-extend/src-tauri/src/autopilot.rs`](../../../apps/stream-extend/src-tauri/src/autopilot.rs):
it bundles six fixed files, runs `python -m stream_autopilot` in the automation-control venv with a
20-second timeout, and exposes exactly two commands — `status` and `rehearse`.

Two things to know:

- It runs against
  [`configs/local/stream-supervisor.yaml`](../../../configs/local/stream-supervisor.yaml), **not**
  `stream-autopilot.yaml`. The autopilot YAML holds persona definitions — `nova-builder` is the
  Minecraft persona, with `game_id: minecraft`. The supervisor YAML is what the bridge passes as
  `--config`.
- **NOT SHIPPED: it does not play Minecraft.** Nothing in this repo plays a game.

**Run it:**

1. **Automated streaming** tab.
2. Click status.

Pass condition: a report renders. "Install Automation / Control in Module setup before running
Autopilot checks" means you skipped §5.6 step 2.

### 7.4 The end-to-end captured session

| # | Action | Verify |
|---|---|---|
| 1 | ComfyUI up, SD 1.5 + LCM-LoRA loaded | `/system_stats` returns JSON |
| 2 | Minecraft Java running windowed 1920×1080, version and render distance pinned | Your pinned settings written down |
| 3 | OBS: Window Capture on Minecraft, mic added, a Browser or Image source reserved for AI output | Both sources visible in preview |
| 4 | Stream Extend: profile **Agent Game Labs**, readiness green | Switcher shows the profile and a routed account |
| 5 | Click **🔴 Go Live + Record** | Stats row reads `Recording for Creator Extend` |
| 6 | Play **10 minutes**. Queue **3** prompts at natural pauses. Show each result on stream. | Each render lands under your measured latency budget |
| 7 | Watch OBS's status bar the whole time | Skipped frames **< 1%** of total. Above that, drop the ComfyUI resolution first, then the game's render distance |
| 8 | Click **⬛ Stop + Send to Creator** | `Recording <name> is ready in Creator Extend.` |
| 9 | Open Creator Extend → **Recordings** | The file is listed, with source profile `agent-labs`, status `ready`, and a plausible size |

**Pass condition: step 9.** The recording is in the inbox, correctly attributed, and marked
available. That single row is what proves the technical chain — capture, encode, AI generation,
session ownership, finalization, and cross-app handoff — worked together.

**Step 10 — the channel review gate. Do this before the recording goes anywhere near publishing.**

Watch the recording back and answer one question about every AI-generated output that appeared on
screen: **would I put this on my channel?**

Not "did the pipeline work." Not "was it fast enough." Those are steps 1–9. This is a taste
judgment about public output, and it is a separate gate because it fails for different reasons and
it is the one that damages a profile rather than a session.

Review every AI-gen moment for:

| Check | Fail looks like |
|---|---|
| **Coherence** | Melted geometry, six-fingered hands, pseudo-text. Funny once in chat, embarrassing in a VOD thumbnail |
| **Appropriateness** | Anything you would not show the Roblox audience. Your strictest standard governs (§4.1) |
| **Likeness** | A generated face resembling a real person. The realtime-ai module's ethics rule is a hard constraint, not a suggestion — use only your own likeness or one you have explicit consent for |
| **On-screen duration** | An image that sat on screen for 40 seconds because the render was slow. Dead air is a quality failure |
| **Framing** | Did you explain what the audience was looking at, or did an image just appear? |

**Pass condition: every AI-gen moment is one you would publish.** If any one fails, the recording is
a **practice run** — keep the performance data from step 9, and do not hand it to Creator Extend for
publishing. Fix the prompt, the model, or the timing, and record again.

This gate is cheap here and expensive later. An AI-gen glitch that reaches a public VOD becomes
part of your profile through the VOD itself, through clips, and through algorithmic surfacing — and
you do not control any of those three once it is out.

**Record the numbers.** The evaluation doc requires, for every game row: exact edition/build, OS,
CPU/GPU/RAM, resolution, preset, map/mode, capture path, average FPS, 1% lows, memory use, OBS
rendering/encoding lag, and audio sync. It also requires you to record failures. Without this, the
Minecraft row stays `pending` no matter how well the session felt.

---

## 8. Private test stream (dry run)

> **The private-first rule — this is a standing mandate, not a one-time step.**
>
> **Run one full private cycle per game, per profile, before that combination ever goes public.**
> Three games × the profiles you actually use. Not one drill total — one per combination.
>
> This is not QA busywork. It is profile protection. A public stream is not ephemeral: it becomes a
> VOD, clips get cut from it, and the algorithm surfaces whichever moment it likes best — which is
> frequently the moment you would least choose. A misconfigured alert, a half-finished overlay, a
> glitched AI-gen image, or an audio channel you forgot to unmute does not disappear when the
> stream ends. It becomes a durable part of your public identity, and you control none of the three
> surfaces that carry it.
>
> The drill costs 30 minutes. Undoing a bad first impression costs months, and sometimes cannot be
> done at all.
>
> **Re-run the drill whenever any of these change** — each has broken a stream for someone:
>
> - A new game enters the rotation
> - A new profile, or a profile's destinations change
> - A new overlay, alert, or scene collection
> - A new AI-gen mode, model, or workflow
> - New capture hardware, or a card moved to a different port
> - An OBS or Stream Extend version bump
>
> Keep a note of which combinations have passed and when. "I think we tested that" is how the
> untested one goes live.

Do this **once, in full**, per combination, before any public broadcast. It is 30 minutes.

### 8.1 Set up private destinations

**Twitch:**

1. **Creator Dashboard → Stream Manager → Edit Stream Info**.
2. Twitch has no true private mode. Use either a **throwaway channel**, or your main channel with
   **Settings → Stream → Store past broadcasts** on and a plan to delete the VOD.
3. Do **not** announce it anywhere.

**YouTube:**

1. **YouTube Studio → Go Live → Stream**.
2. Set visibility to **Private** — it stays private for the whole broadcast, and that is a genuine
   private broadcast, unlike Twitch.
3. Copy the key into your obs-multi-rtmp target.

### 8.2 The dry run checklist

Work top to bottom. Tick every line. A failed line stops the run.

**Pre-flight — hardware**

- [ ] Xbox Series S on, at 1080p60, HDR **off**, 4K **off**
- [ ] Elgato 4K S: Xbox → card HDMI in; card → Mac **USB 3 direct**, no hub
- [ ] Card HDMI passthrough → play monitor, showing picture
- [ ] `python3.12 scripts/setup/capture_devices.py` lists the Elgato as video **and** audio
- [ ] Mac on **wired Ethernet**, not Wi-Fi
- [ ] `networkQuality -v` shows sustained upload ≥ 20 Mbps
- [ ] Mac plugged into power, **Low Power Mode off**, lid open, sleep disabled
- [ ] Every unneeded app quit — 16 GB is shared memory and you are about to spend it

**Pre-flight — software**

- [ ] OBS open, WebSocket enabled on 4455
- [ ] OBS: canvas 1920×1080, 60 fps, Lanczos
- [ ] OBS: Advanced output, Apple VT H.264 Hardware, CBR 6000, keyframe 2
- [ ] OBS: recording path is a **local SSD folder** with ≥ 20 GB free
- [ ] OBS: capture card video source and audio source both present, meters moving
- [ ] OBS: mic source present, meter peaking around −12 dB when you speak normally
- [ ] obs-multi-rtmp dock has the YouTube target, if you are multi-casting
- [ ] Stream Extend open, **OBS Connected** in the header
- [ ] **Module setup → Check readiness**: `stream.obs.websocket` and `stream.obs.scenes` both ready
- [ ] Dashboard scene buttons visible and **not** locked
- [ ] Header profile set to **Main Stream**, sub-label shows a routed account
- [ ] Twitch chat popout open on a second display
- [ ] AutoMod on, 2-second chat delay, one human moderator standing by

**The run**

- [ ] Click **🔴 Go Live + Record** — in the app, never in OBS
- [ ] OBS shows **both** REC and LIVE
- [ ] Stats row reads **`Recording for Creator Extend`**
- [ ] Open the Twitch and YouTube players on your phone — both show picture within 30 seconds
- [ ] Say a test phrase. It arrives on both players. Check A/V sync on the phone, not the Mac
- [ ] Play **20 minutes** of real gameplay
- [ ] Switch OBS scenes twice from the **Dashboard** buttons — the stream does not drop
- [ ] Switch the header profile to **Agent Game Labs** and back — the stream does not drop
- [ ] Post a chat message from your phone; it arrives in the popout
- [ ] Watch skipped frames every ~5 minutes: **< 1%** of total, and **not climbing**
- [ ] Watch Activity Monitor memory pressure: stays out of the red

**Teardown**

- [ ] Click **⬛ Stop + Send to Creator**
- [ ] Both players go offline
- [ ] Message reads `Recording <name> is ready in Creator Extend.`
- [ ] Open Creator Extend → **Recordings** — the file is there, size plausible for 20 minutes,
      status `ready`, source profile `stream-main`
- [ ] Play the recording back in full-screen. Sharp, in sync, no audio dropouts
- [ ] Delete the Twitch VOD and the private YouTube broadcast if this was a throwaway
- [ ] Write down: average FPS, 1% lows, skipped-frame count, memory pressure, anything that felt
      wrong

**Pass condition: every line ticked, and the played-back recording is watchable end to end.** If
any line failed, fix it and run the whole checklist again. A partial re-run does not count — the
failures in this system are interaction failures.

---

## 9. Public go-live checklist

### 9.0 Gate: the private drill for *this* combination has passed

**Before anything in §9.1, confirm this exact game + profile combination has passed a full §8
private cycle.** Not a similar one. This one.

- [ ] This **game** has passed a full private drill
- [ ] This **profile** has passed a full private drill
- [ ] Nothing in the §8 re-run list has changed since — no new overlay, alert, AI-gen mode, model,
      capture hardware, or OBS / Stream Extend version bump
- [ ] The drill recording was played back end to end and was watchable
- [ ] Every AI-gen moment in it passed the §7.4 step 10 channel review gate
- [ ] Branding artifacts are live: avatar, banner, panels, About copy (§3.6), verified **logged out**

**If any line is unticked, do not go live.** Run the drill. This is the gate that keeps a broken
configuration from becoming a permanent VOD, and it is the one people skip because they are excited.

### 9.1 Pre-flight (T-minus 30 minutes)

Everything in §8.2's two pre-flight blocks, plus:

- [ ] Stream title and category set on **both** Twitch and YouTube
- [ ] Thumbnail set on YouTube
- [ ] Moderator confirmed **present**, not just invited
- [ ] Phone charged, on the network, both players bookmarked
- [ ] A **10-minute local recording** made and played back today — not yesterday
- [ ] Notifications silenced: **Focus → Do Not Disturb** on the Mac, phone on silent
- [ ] Desktop cleared of anything you would not screenshot
- [ ] Free disk ≥ 20 GB. An OBS recording that fills the disk stops the recording *and* can stall
      the encoder
- [ ] You know where the **stop** button is without looking

### 9.2 During

| Every | Check | Threshold | If breached |
|---|---|---|---|
| 5 min | Skipped frames | < 1% and not climbing | Drop bitrate to 4500, then lower the ComfyUI resolution |
| 5 min | Chat | No unmoderated pile-up | Hand to moderator; enable followers-only |
| 10 min | Phone player | Both platforms live, A/V in sync | See §10 |
| 10 min | Memory pressure | Out of the red | Quit ComfyUI. It is the most expendable process on the machine |
| 15 min | Free disk | > 5 GB | Stop the session cleanly and restart it |

Never touch OBS's own Start/Stop Streaming buttons during an app-managed session. Stopping in OBS
leaves Stream Extend's in-memory ownership marker set, and the handoff will not fire.

### 9.3 Post

- [ ] Click **⬛ Stop + Send to Creator** — in the app
- [ ] Confirm `Recording <name> is ready in Creator Extend.`
- [ ] Both platforms show offline
- [ ] Open Creator Extend → **Recordings**; confirm the file, and assign the content profile
- [ ] Play the first and last minute of the recording; confirm both are good
- [ ] Set Twitch VOD visibility; publish or schedule the YouTube VOD
- [ ] Copy the run's numbers into your acceptance log — FPS, 1% lows, skipped frames, memory,
      anything that broke
- [ ] Hand off to [Creator Extend §8](CREATOR_EXTEND_PRODUCTION_SETUP.md#8-test-end-to-end) to
      produce clips

---

## 10. Failure modes and recovery

There is no incident playbook in this repository to reference —
[`docs/architecture/disaster-recovery.md`](../../architecture/disaster-recovery.md) is the backup
and restore runbook for the data services, not a live-stream playbook. This section is the
stream-side one, derived from the actual error paths in the code.

### 10.1 Capture card drops

**Symptom:** OBS capture source goes black; audio meter flat.

| Priority | Action |
|---|---|
| 1 | **Switch scenes immediately** — Dashboard button, to a camera or "be right back" scene. Do this before diagnosing. Dead air is the real failure |
| 2 | In OBS, right-click the Video Capture Device → **Properties** → reselect the Elgato → **OK**. This re-opens the device and fixes most drops |
| 3 | If the device is gone from the list: unplug the USB, wait 5 seconds, replug **into the same port**, then redo step 2 |
| 4 | Check the Xbox is not in a mode change. HDCP on a streaming app will black the capture — that is by design, not a fault |
| 5 | Re-run `python3.12 scripts/setup/capture_devices.py` in another terminal to confirm the OS still sees the card |

**Do not stop the Stream Extend session to fix capture.** The stream can survive a black source;
restarting the session costs you the VOD continuity and the recording handoff.

**Prevention:** direct USB 3 port, 1080p60 SDR, HDR and 4K off on the Xbox.

### 10.2 OBS crashes

This is the worst case, because Stream Extend's session ownership is deliberately in-memory only.

**What happens:** the stream drops. The recording is finalized by OBS's own crash recovery, or it is
not. Stream Extend's ownership marker is lost.

| Priority | Action |
|---|---|
| 1 | Reopen OBS. It will offer to recover the unfinished recording — **accept** |
| 2 | Check the OBS recording folder for the file. It is usually there and usually playable |
| 3 | In Stream Extend, click **Connections → Save and test OBS** to re-establish the WebSocket |
| 4 | **Module setup → Check readiness** — both checks must go green again before the Dashboard unlocks |
| 5 | Start a **new** session with **🔴 Go Live + Record**. Do not expect the old one to resume |
| 6 | In Creator Extend → Recordings, use **Add existing recording** to import the recovered file by hand |

Step 6 is why manual import exists. The app cannot claim a recording it cannot prove it owns, so
after a crash you tell it explicitly.

**Prevention:** do not run ComfyUI at SDXL sizes alongside OBS and a game on 16 GB. Memory pressure
is the most common OBS crash cause on this hardware.

### 10.3 AI generation falls behind

**Symptom:** prompts queue up; renders arrive after the moment has passed; the game stutters.

| Priority | Action |
|---|---|
| 1 | **Stop queueing.** Let the backlog drain. Do not add "one more" |
| 2 | Drop the ComfyUI resolution — 512×512 to 384×384 is a large saving |
| 3 | Drop LCM steps to 4 |
| 4 | If the *game* is stuttering, not just the render: **quit ComfyUI entirely.** The stream survives without AI; it does not survive a stuttering game |
| 5 | Check Activity Monitor memory pressure. Red means the OS is swapping, and every process is now slow |

**Prevention:** measure the render latency in §7.2 and pick prompts that fit inside it. Never queue
during a combat or high-motion sequence.

### 10.4 AI-gen ships junk to a public VOD

**The most under-rated failure in this guide**, because it does not look like a failure while it is
happening. The stream stays up, the frames keep flowing, nothing errors. A malformed, off-tone or
inappropriate generated image simply appears on a live public broadcast — and then persists in the
VOD, in any clip someone cuts, and in whatever the algorithm decides to surface.

**Why this one is different:** every other failure in §10 costs you a session. This one costs you
profile. You cannot fully retract it, because the three surfaces that carry it are not yours.

**Mitigation, in order of effectiveness:**

| # | Control | Where |
|---|---|---|
| 1 | **Private-first drill** for every new AI-gen mode, model or workflow, before it is ever live | §8 |
| 2 | **Channel review gate** — "would I put this on my channel?" on every AI-gen moment, before publishing | §7.4 step 10 |
| 3 | **Pre-written, pre-tested prompts only.** Never compose a prompt live | §7.2 |
| 4 | **Strong negative prompt** on every workflow: `blurry, watermark, text, distorted` | §7.2 |
| 5 | **Preview before display.** Route AI output to a source you enable manually, not one that auto-shows on completion | OBS source setup |
| 6 | **Strictest-audience standard.** Roblox's bar governs all three games | §4.1 |
| 7 | **Never generate likenesses** of real people. Hard constraint from the realtime-ai module's ethics rule | §1.3 |

**If it happens anyway, during the stream:**

1. **Switch scenes immediately.** Get it off screen before you discuss it — same reflex as a capture
   drop (§10.1).
2. Disable the AI-gen source. Do not try to regenerate live.
3. Acknowledge it briefly and move on. Do not dwell; dwelling is what makes it the clip.
4. Note the timecode.

**After the stream:**

1. **Edit or delete the VOD.** Twitch: Video Producer → trim or delete. YouTube: Studio → Editor →
   cut the segment. Do this **before** you sleep — the window where nobody has clipped it yet is
   measured in hours.
2. Check whether anyone clipped it. Twitch: Creator Dashboard → Content → Clips. Delete what you own.
3. Do **not** hand the recording to Creator Extend for clip production until the segment is cut.
4. Fix the root cause — prompt, model, or the step-5 manual-enable control — before that AI-gen mode
   runs live again, and re-run the private drill for it.

### 10.5 Chat overrun

| Priority | Action |
|---|---|
| 1 | Hand chat to your moderator, out loud, on stream |
| 2 | Twitch: **Followers-only mode**, 10-minute minimum |
| 3 | Raise **chat delay** to 10 seconds |
| 4 | If it is a raid: **Creator Dashboard → Settings → Moderation → Suspicious User Controls**, restrict |
| 5 | Last resort: emote-only mode |

**Prevention:** a human moderator present before you go live. This is the one failure mode with no
technical fix.

### 10.6 Handoff to Creator Extend fails

**Symptom:** stop produces "OBS finalized the recording, but Creator Extend inbox registration
failed: … Import the file manually."

**Your video is safe.** The stream stopped cleanly and OBS finalized the file. Only the inbox
registration failed. The inbox accepts only canonical, non-empty local video files, so the causes
are few:

| Cause | Fix |
|---|---|
| Recording path on a network or external volume | Set the OBS recording path to a local SSD folder |
| File is zero bytes | The encoder failed. Check OBS's log for encoder errors |
| Path could not be canonicalized (symlink, unusual mount) | Use a plain path under your home directory |

Recovery either way: Creator Extend → **Recordings** → **Add existing recording**, pick the file.
The inbox deduplicates by canonical path, so a repeated path updates the existing record instead of
creating a second one — re-importing is safe.

The worse message is "The stream stopped, but OBS did not confirm recording finalization." Then:
stop recording in OBS by hand first, then import.

### 10.7 Stream drops on one platform only

| Which | Action |
|---|---|
| YouTube drops, Twitch fine | obs-multi-rtmp target. Right-click it → stop → start. It reconnects without touching your Twitch output |
| Twitch drops, YouTube fine | OBS's own output. Check OBS's status bar for a reconnect message — OBS auto-retries. If it does not recover in 60 seconds, stop the session cleanly and restart it |
| Both drop | Network. Check the cable, then `networkQuality -v`. Do not restart the session until the link is back |

### 10.8 "OBS controls are locked"

Not a failure — the readiness gate doing its job. `obs-control` requires both
`stream.obs.websocket` and `stream.obs.scenes`. Open **Module setup → Check readiness** and read
which one is blocked:

- `stream.obs.websocket` blocked → OBS is closed, or the WebSocket is off, or the password changed
- `stream.obs.scenes` blocked → OBS has **zero scenes**. Create one

### 10.9 "Stream Extend already owns a live session"

You clicked Go Live twice, or a previous session did not stop cleanly. Click
**⬛ Stop + Send to Creator** to clear the ownership marker, then start again. If the button is not
showing the stop state, restart the app — the marker is in-memory and a restart clears it, which is
precisely why it was designed not to persist.

---

## Where this guide's material comes from

| Section | Sources |
|---|---|
| Prerequisites | [`creator-experience`](../../../modules/creator-experience/setup/manual.md), [`realtime-ai`](../../../modules/realtime-ai/setup/manual.md), [`models.md`](../../../modules/realtime-ai/comfyui/models.md), [`storage-data`](../../../modules/storage-data/setup/manual.md) |
| Hardware | [`STREAM_AUTOPILOT_GAME_EVALUATION.md`](../../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md) |
| Platforms | [`multi-platform.md`](../../../modules/creator-experience/obs-config/multi-platform.md), [`catalog.yaml`](../../../modules/social-management/catalog.yaml), [`social-management`](../../../modules/social-management/setup/manual.md) |
| Games | [`STREAM_AUTOPILOT_GAME_EVALUATION.md`](../../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md), [`PROPOSAL_STREAM_AUTOPILOT.md`](../../proposals/PROPOSAL_STREAM_AUTOPILOT.md), [`STREAM_AUTOPILOT_SHOW_BIBLE.md`](../../proposals/STREAM_AUTOPILOT_SHOW_BIBLE.md) |
| Build | [`apps/stream-extend/src-tauri/src/lib.rs`](../../../apps/stream-extend/src-tauri/src/lib.rs), [`obs.rs`](../../../apps/stream-extend/src-tauri/src/obs.rs), [`desktop-setup.md`](../../../modules/infrastructure/setup/desktop-setup.md), [`configs/setup/stream-extend.json`](../../../configs/setup/stream-extend.json) |
| Profiles | [`ProfileSwitcher.svelte`](../../../apps/shared/ui/ProfileSwitcher.svelte), [`apps/shared/ui/README.md`](../../../apps/shared/ui/README.md), [`apps/shared/social-manager/README.md`](../../../apps/shared/social-manager/README.md), [`PROPOSAL_RECORDING_HANDOFF_AND_PROFILE_WORKSPACES.md`](../../proposals/PROPOSAL_RECORDING_HANDOFF_AND_PROFILE_WORKSPACES.md) |
| Autopilot | [`autopilot.rs`](../../../apps/stream-extend/src-tauri/src/autopilot.rs), [`configs/local/stream-autopilot.yaml`](../../../configs/local/stream-autopilot.yaml), [`configs/local/stream-supervisor.yaml`](../../../configs/local/stream-supervisor.yaml), [`automation-control`](../../../modules/automation-control/setup/manual.md) |
| Handoff | [`apps/shared/recording-library/README.md`](../../../apps/shared/recording-library/README.md), [`RecordingLibrary.svelte`](../../../apps/shared/ui/RecordingLibrary.svelte) |
