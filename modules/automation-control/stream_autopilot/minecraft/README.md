# Private-world Minecraft adapter

P-056's first bounded game adapter uses Mineflayer 4.39.0 and requires Node.js 22+.
The pinned dependency lock overrides UUID to 11.1.1; the current package audit reports zero
advisories. `npm ci --ignore-scripts` installs code dependencies only, not a game or model.

This adapter is for an explicitly permitted **private/loopback Java test server** supporting
an offline dedicated bot identity. It does not configure a server, bypass online authentication,
log in to Microsoft, join public servers, impersonate a personal account, attack, dig, use
inventory, run chat commands or control the workstation keyboard/mouse. Fill in the named
world and permission statement in `configs/local/minecraft-gameplay.json` before enabling;
passing tests does not provide that permission. Defaults remain disabled/unbound.

Prepare/test locally:

```bash
npm ci --ignore-scripts --prefix modules/automation-control/stream_autopilot/minecraft
node --test modules/automation-control/stream_autopilot/minecraft/core.test.mjs
PYTHONPATH=modules/automation-control python3 -m stream_autopilot.gameplay --config configs/local/minecraft-gameplay.json --validate
```

The supervisor owns the protocol client in preview only when the selected policy enables
Minecraft gameplay and the permitted binding validates. A configured task holds forward,
back or jump for 50–1000 ms, releases control and compares before/after observations. No
observed movement is a failed task, not success. Release/close preempt a pending task and
advance the epoch; stale commands cannot regain input. EOF/signals clear controls and quit.
The Python transport sends no backend/OBS/avatar secret to the game SDK.

This is an outbound protocol client, not a game renderer. Actual Java-client rendering, OBS
capture, device/server input-release timing and manual takeover remain real acceptance.
Realtime game/render/audio work stays on the workstation; DigitalOcean is not part of this
adapter. Keep private-world acceptance and host/version/permission evidence in P-056.

API authority: [Mineflayer API](https://github.com/PrismarineJS/mineflayer/blob/master/docs/api.md)
and [official examples](https://github.com/PrismarineJS/mineflayer/blob/master/docs/README.md).
