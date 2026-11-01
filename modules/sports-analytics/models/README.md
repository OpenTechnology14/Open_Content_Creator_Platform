# Sports analytics models

Model weights are **not** committed. Download them on first run:

```bash
# YOLOv8 (auto-downloads on first `YOLO('yolov8n.pt')` call from ultralytics)
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
python -c "from ultralytics import YOLO; YOLO('yolov8n-pose.pt')"
```

| Model            | Size  | Notes                                       |
| ---------------- | ----- | ------------------------------------------- |
| yolov8n.pt       | ~6 MB | Fastest. Use for realtime tracing.          |
| yolov8s.pt       | ~22 MB | Better accuracy. Try if `n` misses.        |
| yolov8n-pose.pt  | ~7 MB | Realtime pose. Use for swing analysis.     |
| Custom fine-tune | varies | See `../golf-tracer/README.md` for training notes. |

If you ship a fine-tuned weight, store it in MinIO under `models/` via
[`asset-pipeline`](../../asset-pipeline/README.md) rather than committing it to git, and record its
checksum, size, and license in [`model-registry`](../../model-registry/README.md)'s `registry.yml`
— this table has no checksum column, so it isn't provenance on its own.

## Choosing a ball-detection model

**A pretrained COCO YOLO will not reliably detect a golf ball.** COCO's "sports ball" class
overlaps soccer and basketball, and a small white ball against grass is a genuinely hard case.
Budget for one of these instead:

| Effort | Path | Trade-off |
|---|---|---|
| Lowest | A community-trained golf-ball YOLO (Hugging Face, Roboflow Universe) | Variable quality |
| Medium | Fine-tune on a public golf-ball dataset (~1–5k labelled frames on Roboflow) | 1–2 hours on an RTX 30-class card |
| Highest | Train from scratch on your own footage | Best accuracy for your camera and lighting; multi-day |

Record which path you took here, along with the model file, its mAP score, and its known failure
modes. A model that works in bright sun and fails at dusk is fine — an undocumented one is not.

**Never commit `.pt` files.** Store weights in MinIO under `models/` (or DO Spaces in cloud) via
[`asset-pipeline`](../../asset-pipeline/README.md). See [`storage-data`](../../storage-data/setup/manual.md)
for MinIO itself, and [`model-registry`](../../model-registry/README.md) for recording a real
checksum and license per weight.

