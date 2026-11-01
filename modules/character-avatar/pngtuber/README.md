# pngtuber

PNGTuber scene assets and config. See [`realtime-ai`](../../realtime-ai/setup/manual.md).

## Audio-level switching

The two-PNG approach — static PNG plus a "talking" PNG — is switched by audio level using OBS
**Advanced Audio Properties** together with the **Move** plugin. `example/scene.json` in this
folder is a working reference.

Set the trigger threshold **above your room noise floor**, or the mouth flaps continuously. If
the room is noisy enough that this is hard, gate the mic first — see
[audio-production](../../audio-production/setup/manual.md).

For more expression than two states can carry, move to VTube Studio / Live2D / VRM — see
[`../setup/manual.md`](../setup/manual.md).

