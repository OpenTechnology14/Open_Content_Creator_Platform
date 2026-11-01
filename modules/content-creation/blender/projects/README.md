# Blender Projects

Reference `.blend` files and tutorials for the content creation pipeline.

## Starter Projects (in order of complexity)

| # | Project | Output | Difficulty |
|---|---------|--------|-----------|
| 1 | 2D Title Card | PNG (1920×1080) | Beginner |
| 2 | Animated Lower-Third | MP4 with alpha (10s) | Beginner |
| 3 | 3D Logo Intro | MP4 (5-10s) | Intermediate |
| 4 | Composited Webcam Shot | MP4 with webcam as video texture | Intermediate |

## File naming

```
01-title-card.blend
02-lower-third.blend
03-logo-intro.blend
04-webcam-composite.blend
```

## Notes

- `.blend` files are binary — commit only the reference/template versions
- Large renders and output files go to MinIO, not git
- For AI-powered editing of Blender renders, see [`image-editing`](../../../image-editing/setup/manual.md) (Krita + ComfyUI)
