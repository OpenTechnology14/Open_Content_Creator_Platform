# Stream Autopilot: game hardware evaluation

**Parent:** [P-056 proposal](PROPOSAL_STREAM_AUTOPILOT.md) · **Labels:** Stream
**Evaluated:** 2026-09-08 · **Status:** researched candidates; no game benchmarks completed

## Owner constraints and recommendation

Owner has an Xbox Series S, no capture card, and an initial hardware budget **under USD 1,000**.
Local hardware inspection found an M1 Pro MacBook Pro, 8 CPU cores, 14 GPU cores and 16 GB
unified memory. The Mac's memory is shared by applications and graphics, not dedicated VRAM.
The owner wants all ten previously identified games retained, plus Roblox and Among Us.
The additions are programming candidates, not a revised top-ten ranking.

Owner clarified the scaling strategy: start with **one inexpensive desktop**, add a second
when viewers and realized commission/revenue support it, then evaluate on-demand cloud GPU
capacity. The target is three independent AI-assisted broadcasts: two desktop game sessions
with interchangeable human/agent gameplay where supported. Console capture is one possible
backstage source, not a separate show identity. AI-host and production automation apply to all three. Initial spending does not have to buy both towers.

Reuse the Xbox for supported console games and the Mac for its OBS capture, DJ Soundbox,
lightweight host and speech. Select the first desktop for one validated, affordable autonomous
game workload; retain all ten games in the evaluation rather than forcing the first machine
to meet Tarkov's recommended tier. Add a second independent desktop stream only after the
first passes its full acceptance recording. Revenue is a hoped-for funding source, not a
forecast or assumed repayment. No hardware or cloud resources have been purchased.

## Staged stream capacity

| Stage | Hardware and intended role | Gate before expanding |
|---|---|---|
| Xbox pilot | Series S gameplay → capture card → Mac OBS/AI host; human plays | One complete local recording with synchronized voice, avatar, chat and Soundbox |
| First desktop | Desktop runs its game and captures/encodes it locally in OBS; intended second independent broadcast | A permitted game adapter actually plays and stops; game + host + encoder tested together; separate chat/audio/graphics/output ownership |
| Second desktop | Another independent game/OBS/host setup; intended third broadcast alongside Xbox and desktop 1 | First desktop is stable, measured uplink capacity is sufficient, and available funds cover the second machine and ongoing costs |
| Cloud later | Short, budget-limited trial for a compatible additional workload | Verify game/VM compatibility and real costs; record the existing roadmap decision before any full cloud broadcast deployment |

Each desktop can capture its own game without an additional HDMI capture card. Keep one card
for the Xbox. Local independent OBS setups are the proposed scaling unit, not a distributed
worker system or three heavyweight rendering pipelines on the 16 GB Mac. Reuse module code,
persona formats and sound assets, with independent runtime state and audio ownership per stream.
The current director only handles one on-air session per OBS/backend graphics owner; making
three isolated installations operate together remains implementation and acceptance work.

Separate concurrent broadcasts need configured platform destinations; do not assume one channel
accepts three independent feeds. Measure total upload demand including audio/overhead. As sizing
arithmetic only, three 6 Mbps video outputs consume 18 Mbps before those extras. Capture counts,
encoder counts and available bandwidth are separate capacity limits.

The cohort below preserves the [TwitchMetrics trailing-30-day watch-hours snapshot](https://www.twitchmetrics.net/games/viewership)
used in the parent proposal, excluding non-game categories. Counter-Strike means the current
CS2 client; Overwatch means the current live game, previously named Overwatch 2. Game variants
are explicit because Minecraft Java/Bedrock and GTA Legacy/Enhanced/FiveM are not interchangeable.

## Platform and GPU matrix

GPU entries are **evaluation targets chosen for 1080p, approximately 60 FPS, adjusted settings,
no ray tracing and no heavy shaders**. They are not official minimums or benchmark promises.
AI effects are budgeted separately. All game launch, capture and sustained-play results remain
pending; installing a client is not acceptance evidence.

| Game | M1 Pro MacBook assessment | Xbox Series S | Windows GPU to evaluate | Important qualification |
|---|---|---|---|---|
| League of Legends | Candidate: Riot's current localized requirements explicitly list Apple M1 | No console version of PC League | GTX 1650-class or better; proposed RTX 3060 tower has headroom | CPU and stable frame times matter; test current Mac client. [Riot requirements](https://support-leagueoflegends.riotgames.com/hc/hu/articles/201752654-Minim%C3%A1lis-%C3%A9s-aj%C3%A1nlott-rendszerk%C3%B6vetelm%C3%A9nyek-League-of-Legends) |
| Dota 2 | Mac client exists; M1 compatibility test required because Valve's table still specifies Intel | No | GTX 1650-class or better | Test a busy team fight and long session, not only menus. [Valve requirements](https://store.steampowered.com/app/570/Dota_2/) |
| Counter-Strike 2 | No supported macOS client; do not count compatibility-layer experiments as supported | No | GTX 1660 Super / RTX 2060-class or better | A 144+ FPS competitive target needs a separate CPU/frame-time assessment. [Valve platforms/specs](https://store.steampowered.com/app/730/CounterStrike_2/) |
| Grand Theft Auto V | No supported Mac client | Yes, console GTA V/Online | RTX 3060 12 GB for Enhanced; lighter Legacy separately | Rockstar lists RTX 3060 8 GB / RX 6600 XT recommended for Enhanced. FiveM roleplay is a separate PC/server evaluation, not Xbox GTA Online. [Rockstar specs](https://support.rockstargames.com/articles/lMQXeP2Z1mN3g9oZiBZFR/grand-theft-auto-v-pc-system-requirements) |
| VALORANT | No supported Mac client | Yes | GTX 1650-class or better | Prefer Series S or physical Windows PC. [Xbox release](https://www.xbox.com/de-DE/games/valorant) |
| Escape from Tarkov | No supported Mac client | No | RTX 3060 12 GB as a budget trial; RTX 4070-class for the published recommended tier | Publisher lists GTX 1660/Ryzen 5 3600/16 GB minimum versus RTX 4070/i7-14700F/64 GB recommended. A 32 GB budget PC is below that recommended tier; test demanding maps. [Publisher Steam listing](https://store.steampowered.com/app/3932890/Escape_from_Tarkov/) |
| Minecraft | Java candidate; Xbox Bedrock is a different edition | Yes, Bedrock | Vanilla: integrated graphics/GTX 1650-class; heavier shaders: separate RTX 3060+ trial | Current requirements were revised July 2026. Pin version, render distance and modpack for tests. No shader/RTX guarantee. [Mojang requirements update](https://www.minecraft.net/en-us/article/minecraft-java-edition-system-requirements), [editions](https://www.minecraft.net/en-us/store/minecraft-java-bedrock-edition-pc) |
| World of Warcraft | Current retail Midnight: **do not count M1 Pro as meeting the published M2 minimum**; Classic separate | No | RTX 3060 budget trial; RTX 4060-class or better for a stronger target | Correction to earlier conversation: the old M1 requirements were for an older expansion. Current Midnight product requirements list M2 minimum and RTX 40-series in the Windows recommended graphics tier. Retail raids/cities require separate CPU testing. [Current expansion requirements](https://eu.shop.battle.net/en-gb/product/world-of-warcraft-midnight) |
| Fortnite | No supported current native Mac build; supported cloud streaming is a separate route | Yes | GTX 1660 Super / RTX 3060 for reduced settings; RTX 3070-class for Epic preset evaluation | Epic's requirements distinguish recommended and Epic quality. Use Series S first. [Epic PC requirements](https://www.epicgames.com/help/c-202300000001636/c-202300000001690/a202300000012731?lang=en-US), [Mac cloud route](https://www.fortnite.com/mobile/geforce-now?lang=en-US) |
| Overwatch | No supported native Mac client | Yes | GTX 1660 Super / RTX 2060-class or better | Use Series S first; measure PC frame times at the chosen preset. [Blizzard supported platforms](https://news.blizzard.com/en-us/article/23814216/overwatch-2-launches-october-4-as-a-free-to-play-live-experience) |

Sources describe platform availability, requirements and restrictions; chosen GPU targets above
are engineering estimates. Current localized Riot/Midnight product search extracts were readable
even where the full pages redirected or failed to render. No assumption of native ARM compilation
is made for League or Dota. For WoW, verify the exact expansion again before buying or installing;
an M1 Pro's relative performance does not override a vendor's chip-generation requirement.

## Additional requested games

| Game | MacBook assessment | GPU trial target | Automation / platform notes |
|---|---|---|---|
| Roblox | Official Mac client; test selected experiences on M1 Pro | Integrated graphics for simple experiences; GTX 1650-class for a broader trial | Experiences vary substantially; validate capture and input adapter separately. [Roblox requirements](https://en.help.roblox.com/hc/en-us/articles/203312800-Computer-Hardware-Operating-System-Requirements) |
| Among Us | Innersloth explicitly lists Mac as unsupported | Modern integrated graphics trial; no dedicated GPU purchase justified by this game alone | Xbox is officially supported. A cloud VM and agent adapter remain unverified. [Innersloth platforms](https://innersloth.zendesk.com/hc/en-us/articles/9687230649108-Where-can-I-play-Among-Us) |

GPU trial targets are estimates, not measured recommendations or publisher requirements. Roblox
VM compatibility is unverified. The host/show catalog covers both games without claiming an
autonomous gameplay adapter exists. Keep all hardware labels backstage; taking control should
preserve the same live session, host, graphics and sound design. Physical input release and return
to agent control still require device/game-specific implementation and acceptance.

## Cloud evaluation, kept separate from GPU sizing

| Game | Ordinary rented GPU VM assessment |
|---|---|
| League of Legends | Exclude from the default Windows VM plan: Vanguard/VM incompatibility |
| Dota 2 | Candidate only; validate provider OS, drivers, encoder, latency and actual lobby |
| Counter-Strike 2 | Candidate only; validate the selected matchmaking/anti-cheat service separately |
| GTA V | Unverified; test exact Enhanced/Legacy/Online/FiveM combination and anti-cheat |
| VALORANT | Exclude from the default VM plan: Vanguard/VM incompatibility |
| Escape from Tarkov | Unverified; obtain provider/game compatibility evidence before renting |
| Minecraft Java | Candidate; server/bot logic alone can use CPU hosting, but rendered gameplay needs a graphics client |
| World of Warcraft | Unverified per provider and applicable game terms; an approved catalog service is distinct from a self-managed VM |
| Fortnite | Shadow lists it incompatible; Epic explicitly supports GeForce NOW. Do not generalize approved cloud gaming to arbitrary VMs |
| Overwatch | Candidate only; validate actual current client/provider combination |

[Shadow's August 2026 compatibility list](https://support.shadow.tech/hc/en-us/articles/32731823908625-Games-Incompatible-with-Shadow-PC)
explicitly names League, VALORANT and Fortnite. Absence from a blocked list is not proof a game
works. Cloud gaming subscriptions also do not grant an unrestricted desktop for our agent tools.

For scale only, [Paperspace's current price list](https://docs.digitalocean.com/products/paperspace/pricing/)
quotes RTX4000 at $0.56/hour and A4000 at $0.76/hour. At 120 powered-on hours/month, compute is
$67.20 or $91.20 per machine; at 720 hours it is $403.20 or $547.20. Add storage and applicable
plans/licenses/taxes. These workstation GPU names are not equivalent to desktop GeForce model
numbers. No VM is selected, benchmarked, deployed or funded. Keep the existing local-first
roadmap boundary; a complete cloud broadcast deployment still needs the decision recorded in
the parent proposal.

## Under-$1,000 initial buying envelope

These are **spending caps**, not a verified available PC bundle or guaranteed checkout total.

| Item | Allocation |
|---|---:|
| One used tower, including any necessary RAM upgrade | Up to $650 |
| Elgato 4K S capture card, observed US price before tax | $159.99 |
| Necessary cables/adapter allowance | $40 |
| Tax/shipping reserve | $100 |
| Planned total ceiling | $949.99 |
| Remaining headroom below $1,000 | $50.01 |

[Elgato lists the 4K S at $159.99](https://www.elgato.com/us/en/p/game-capture-4k-s) with Mac,
Xbox and OBS compatibility. [Its system requirements](https://www.elgato.com/eu/fi/explorer/products/capture/elgato-game-capture-4k-s-system-requirements/)
include Apple M1 or better. Verify macOS and USB connection requirements; start capture at
1080p60 SDR. Reuse the existing monitor, keyboard and mouse where possible. Game purchases,
subscriptions, additional monitors/storage and paid AI services are outside this hardware cap.

Broader-game tower search target: Ryzen 5 5600 or Intel i5-12400-class CPU; **RTX 3060 12 GB** (check VRAM,
since other 3060 variants exist); 32 GB RAM; 1 TB NVMe SSD; supported Windows 11 installation;
standard replaceable PSU with appropriate GPU power connectors and room for later upgrades.
This is a used-market target and spending ceiling, not the minimum price/specification for the
first desktop. A cheaper upgradeable tower is acceptable if it passes the selected first game's
combined gameplay, AI-host and OBS test. Select that workload before selecting the cheaper GPU.
If no verified machine fits the delivered cap, start with Xbox
capture and defer the tower. Low advertised prices found for refurbished RTX 3060 desktops
included out-of-stock listings, so no purchasable $650 system is claimed here.

An RX 6600/6650 XT tower can be a gaming alternative if materially cheaper, but benchmark
compatibility with the selected AI software before choosing it as an AI workstation. Prefer
NVIDIA for a future CUDA-dependent effects path; the Mac cannot run CUDA. The 3060's 12 GB
does not guarantee photorealistic full-body generation, nor enough memory for a game plus
all AI models simultaneously. Keep AI gaming/effects benchmarks separate.

Purchase the second tower later as the owner requested. Each tower must independently meet its
selected game/host/encoder needs; two machines do not combine GPU memory for one game's workload.
At an illustrative $650 per tower, two towers plus the Xbox card total $1,459.99 before cables
and tax over both stages. A second card is not required when desktops capture locally. Choose
the second machine from observed game demand and performance, rather than automatically cloning
the first specification. Revenue review should use received income after ongoing expenses;
no automatic purchasing or assumed monetization is configured.

## Capture layout and module integration

Staged baseline: Xbox HDMI → one capture card → Mac USB/OBS, with HDMI passthrough to the playing
monitor. Each desktop runs a separate local game/OBS capture and output. The Mac's HDMI port is
output. For a single broadcast that switches between machines, the same card can instead be
reconnected to the chosen source; an HDMI switch selects one source, not simultaneous capture.

For two live sources later, keep Xbox on the card and either add a second input for the tower
or test an OBS-to-OBS feed over the wired LAN. [OBS documents SRT](https://obsproject.com/kb/category/4),
but this transport is not configured or benchmarked here; it adds encoding/network/decoding
latency and load. A PC can also capture its own game in OBS with no capture card. One USB card
alone cannot provide two independent live pictures or ten channels.

Mac OBS remains the proposed owner of the Xbox stream's DJ Soundbox, captions, scenes and final
audio mix; desktop streams need their own instances and bindings. Each stream director must
retain its one-on-air-session rule within its own graphics/OBS owner. Multiple broadcasts need
separate graphics/audio/session ownership and additional implementation, not just more capture
hardware. Physical machine identity and game IDs will be bound through configuration/backend
contracts after actual machines exist. This document adds evaluation entries, not ten enabled
personas, game adapters or successful live integrations.

## Acceptance work still required

For **every row** above, record exact game edition/build, OS, CPU/GPU/RAM, resolution, preset,
map/mode, capture path, average FPS, 1% lows, memory use, OBS rendering/encoding lag and audio
sync. Start with gameplay alone, repeat with capture, then add voice/avatar/Soundbox one at a
time. Use a demanding scene and at least 30 minutes; complete the parent proposal's 60-minute
integrated recording gate before claiming the streaming setup works. Record failures too.

First tests: Series S Minecraft/Overwatch capture, then a permitted Minecraft environment as the
first desktop autonomy candidate (Dota supported bot scripting remains an alternative). Verify
stop/mute and session switching during speech and a Soundbox clip. Test desktop 1 alongside the
Xbox broadcast before adding desktop 2. Mac League/Java, Windows CS2, retail WoW and Tarkov stay
on the evaluation list; passing Tarkov is not a gate for adding a second lighter-game desktop.
All ten remain pending until tested.

Game-playing automation is a separate capability gate. Capture/voice/chat support does not
authorize or implement gameplay bots. Continue evaluating Minecraft permitted environments
and Dota's supported bot scripting separately from human-play co-host modes.

## Documentation verification

2026-09-08: `make test` exited 0 after adding this evaluation to the P-056 queue row.
The first run caught that missing queue link; it was corrected before the passing full rerun.
`python3 -m pytest tests/docs/test_docs_integrity.py -o addopts='' -q` returned
19,706 passed in 24.53 seconds. An explicit check of both new/untracked proposal documents
resolved 14 relative links, counted exactly ten game rows and verified the $949.99 allocation.
`git diff --check` exited 0. No live game or hardware acceptance is claimed.

After the owner's staged-purchase clarification, `make test` was rerun and exited 0
(`/tmp/hcp-staged-streams-test.log`). Both proposal documents still have 14 resolving relative
links, all ten game rows remain present, and `git diff --check` is clean. This verifies the
documentation change, not three concurrent broadcasts or autonomous gameplay.
