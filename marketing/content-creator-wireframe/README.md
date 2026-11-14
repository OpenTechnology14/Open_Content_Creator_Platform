# Content Creator wireframe overview — how-to

> **Status:** First pass, corrected 2026-11-12 to screenshot placeholders · **Last reviewed:** 2026-11-12 · **Owner:** OpenTechnology14
> **Verified against:** `main` at `5cc86f3`, read from the code. The apps were not launched and no screenshot has been captured yet.

## What this is

A feature-organised map of the Content Creator Platform's desktop apps. For each feature it gives the **click paths** a person takes
(A → B → C) and a **screenshot placeholder** for each screen that matters, every step tied to the real component, function or command that implements it.
A feature here is something a person does ("run a ComfyUI workflow"), not a directory.

It exists so a product or marketing conversation about "what does it look like when you do X" has something concrete and current to point at,
and so whoever updates it next can check each claim against a real file and line instead of trusting prose.

It is **reference material, not a claim source.** What may be said publicly about a feature follows its status in
[`MARKETING.md`](../../MARKETING.md) and [`docs/AUDIT.md`](../../docs/AUDIT.md); each feature folder ends with what it does not do. It is not a registered
marketing module (nothing in the crosswalk generates from it), and "built" never means "accepted": no feature here has run on a real account
or live stream.

## Layout

```
marketing/content-creator-wireframe/
├── README.md              this file
├── overview.md            the whole app at once, composed from the feature folders
├── features/
│   └── <feature>/
│       ├── click-paths.md   the click sequences, each step linked to the code, with a placeholder where a screenshot goes
│       └── visual.md        screenshot index: one row per placeholder
└── screenshots/<feature>/step-NN.png   real captures of the running app (none yet)
```

## Features in this first pass

Seven features, chosen because they are what a person does first or most, and because each maps onto working code today.

| Feature | App and tab | Needs |
|---|---|---|
| [Setup and readiness](features/setup-and-readiness/click-paths.md) · [screenshots](features/setup-and-readiness/visual.md) | both apps, Module setup and Connections | nothing installed beforehand; this is where tools get installed |
| [ComfyUI workflows](features/comfyui-workflows/click-paths.md) · [screenshots](features/comfyui-workflows/visual.md) | Creator Extend, Dashboard | a running ComfyUI with the models |
| [Blender stills and creative tools](features/blender-stills/click-paths.md) · [screenshots](features/blender-stills/visual.md) | Creator Extend, Dashboard | Blender installed; Krita optional |
| [OBS control and the recording handoff](features/stream-control-and-recording/click-paths.md) · [screenshots](features/stream-control-and-recording/visual.md) | Stream Extend, Dashboard; Creator Extend, Recordings | OBS with its WebSocket server on |
| [Automated streaming](features/automated-streaming/click-paths.md) · [screenshots](features/automated-streaming/visual.md) | Stream Extend, Automated streaming | a local Ollama model; OBS; credentials only for real chat |
| [Personalities: prompt and voice preview](features/personalities-and-voice/click-paths.md) · [screenshots](features/personalities-and-voice/visual.md) | Stream Extend, Automated streaming | a local Ollama model; an installed operating-system voice; OBS for the audition |
| [Posture Screen](features/posture-screen/click-paths.md) · [screenshots](features/posture-screen/visual.md) | Creator Extend, Dashboard | the sports-analytics Python environment |

[`overview.md`](overview.md) puts them side by side. **Not covered this pass** (listed there, not dropped): the Remote control and Social tabs, the profile
switcher, audio routing, the combined preview's own settings, and the parts that live outside the apps.

## À la carte

Every `features/<feature>/` folder stands alone: read it, link to it, or lift it into a deck without the rest. Only `overview.md` assumes you
have seen more than one feature, and it is a view built from the folders, not a separate narrative. If a feature changes, update its own two files first, then
check whether the one line about it in `overview.md` needs a refresh.

## How the references stay true

Two kinds of citation, both checked by [`tests/docs/test_wireframe_refs.py`](../../tests/docs/test_wireframe_refs.py) on every run:

- **A link with a line anchor**, `[Check readiness](../../apps/shared/ui/ModuleSetup.svelte#L533)`. The link text is the label a person sees (or the function or command
  name) and must occur **on the anchored lines**; a label wrapped onto a second line needs both anchored (`#L10-L11`). The path is relative, so it works on GitHub and in a checkout.
- **A screenshot placeholder**, `[screenshot: marketing/content-creator-wireframe/screenshots/<feature>/step-NN.png]`, with a `*Caption:*` line directly above it. The path names the
  feature's own folder; numbers run 01, 02, … with no gaps; every placeholder has a row with the same caption in that feature's `visual.md` index. The set holds no mermaid, no ASCII
  art and no image except real captures under `screenshots/`.

Every other relative link must resolve, and each feature must be linked from this README and from `overview.md`.

**When the code moves.** Line numbers drift whenever someone edits a cited file, so the test fails on a drifted anchor. Repair it with one command:

```
python tests/docs/test_wireframe_refs.py --fix
```

It moves each anchor to the nearest line that still contains its label, and leaves alone (and reports) any label that is gone or renamed. That case needs a person:
update the document to the new label, do not loosen the test. Review the diff the fixer makes, because the nearest match is not always the intended one when the same words appear twice.

## Screenshots

- Screenshots are **real captures of the running app**, never drawn or reconstructed. A picture of a screen that was not captured from the app does not belong in this set.
- **None has been captured yet.** Each placeholder names the file it will become, and its row in the feature's `visual.md` says what must be open or running first.
- Capture is a **separate follow-up**: by hand with the apps running locally, or automated with Playwright. It is tracked on its own, not here.
- Files are `screenshots/<feature>/step-NN.png` (PNG or JPG), numbered to match the placeholders.
- Capture with **test data only**: no real account names, handles, keys or personal photos.
- Once a screenshot exists, replace its placeholder line with an image embed, `![Caption](relative/path/to/step-NN.png)`, and keep the Caption line. The guard then requires the embed to point at a real file under `screenshots/`, and fails if a captured file still sits behind a placeholder.

## How to read a click path

Steps are what a person does and sees, in order. "Inferred" at the top of each file is deliberate: the apps were not run, so each step is read from
the code and the labels it renders. The first person to follow a path in a running app should change anything that differs and date the change.

## Extending this set

1. Pick a feature (something a person does). Read the component that renders it, and the function behind each button.
2. Write `click-paths.md`: a `## Path N — …` section per thing a person does, numbered steps, a line-anchored link on every label, and a caption plus placeholder after each step that shows something new.
3. Write `visual.md` as the screenshot index: one row per placeholder.
4. Add the feature to the table above and to the index in `overview.md`; if it is new ground, add a line to the "not covered" list when you leave something out.
5. Run `python -m pytest tests/docs/test_wireframe_refs.py`. A wrong line reference is worse than none.
