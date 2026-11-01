# background-removal

OBS Background Removal preset .json files. See [`realtime-ai`](../setup/manual.md).

## Background workflow recipes

Four approaches, cheapest first. Recipes live in [`recipes/`](recipes/).

| # | Recipe | Cost | Notes |
|---|---|---|---|
| 1 | **Static image** | Lowest | Single PNG. Fastest and cleanest — start here |
| 2 | **Blurred room** | Low | Segmentation + gaussian blur on a duplicate webcam source |
| 3 | **Animated loop** | Low | Short MP4 background; cheap on GPU |
| 4 | **AI-generated environment** | Highest | ComfyUI batch-generates a still or short loop **ahead of time** — see [`recipes/ai-environment.md`](recipes/ai-environment.md) |

Recipe 4's cost is paid offline, not per frame — that is the whole point of generating ahead of
time. `repaint_region.py` handles masked touch-ups on the generated background afterward.

`config.json` in this folder holds the model and threshold settings the plugin path uses.

