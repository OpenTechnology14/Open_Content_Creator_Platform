"""
Creator Extend — Krita Plugin

Bridges Krita's Python plugin system with the Creator Extend platform.
Adds menu items and docker panels for:

1. AI Diffusion quick-access (generative fill, inpaint, outpaint, upscale)
2. Batch upscale via ComfyUI (calls modules/image-editing/krita/scripts/batch_upscale.py)
3. Style transfer via IPAdapter (calls modules/image-editing/krita/scripts/apply_style.py)
4. Export to MinIO/S3 (calls modules/image-editing/krita/scripts/export_to_minio.py)
5. SAM auto-segmentation for selection masks
6. Video frame editing workflow

Requires: Krita 5.2+, Python 3.10+
Optional: krita-ai-diffusion plugin for generative features

License: MIT
"""
