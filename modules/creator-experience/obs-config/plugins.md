# OBS plugins — pinned

Pin these specific plugin versions to match [`creator-experience`](../setup/manual.md). When upgrading OBS,
verify each plugin's release notes for that OBS version first.

| Plugin                    | Version ([`creator-experience`](../setup/manual.md))     | Source |
| ------------------------- | --------------------- | ------ |
| obs-websocket             | 5.5.x (bundled in OBS 30+) | https://github.com/obsproject/obs-websocket |
| Advanced Scene Switcher   | 1.27.x                | https://github.com/WarmUpTill/SceneSwitcher |
| Move Transition           | 3.0.x                 | https://github.com/exeldro/obs-move-transition |
| Source Clone              | 0.2.x                 | https://github.com/exeldro/obs-source-clone |
| OBS Background Removal    | 1.1.x                 | https://github.com/locaal-ai/obs-backgroundremoval |
| StreamFX (optional)       | 0.12.x                | https://github.com/Vhonowslend/StreamFX-Public |
| obs-multi-rtmp (optional) | 0.4.x                 | https://github.com/sorayuki/obs-multi-rtmp |

After installing/upgrading any plugin: OBS Help → Log Files → Upload Current
Log File and check there are no `WARN` lines mentioning the plugin name.
