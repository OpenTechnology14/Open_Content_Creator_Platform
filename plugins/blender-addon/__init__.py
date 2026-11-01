"""
Creator Extend — Blender Addon

Free (MIT licensed) Blender addon that serves as the funnel into the
Creator Extend paid app. Features:

1. Template gallery — starter .blend files for motion graphics, intros, etc.
2. MinIO upload — export renders directly to MinIO/S3 asset storage
3. ComfyUI workflow triggers — send frames/renders to ComfyUI for AI processing
4. One-click open Creator Extend app

This addon does NOT require Creator Extend to function.
It makes Blender workflows faster; the app adds remote control + dashboards.
"""

bl_info = {
    "name": "Creator Extend",
    "author": "Open Content Creator Platform",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Creator Extend",
    "description": "Template gallery, MinIO upload, ComfyUI integration",
    "warning": "",
    "doc_url": "https://creatorextend.com/guides/comfyui",
    "category": "Render",
    "license": "MIT",
}

import bpy
from . import operators
from . import panels
from . import preferences


# -------------------------------------------------------------------------
# Registration
# -------------------------------------------------------------------------

classes = [
    preferences.CreatorExtendPreferences,
    operators.CE_OT_OpenTemplateGallery,
    operators.CE_OT_UploadToMinio,
    operators.CE_OT_SendToComfyUI,
    operators.CE_OT_OpenCreatorExtend,
    operators.CE_OT_BatchRender,
    panels.CE_PT_MainPanel,
    panels.CE_PT_TemplatesPanel,
    panels.CE_PT_ExportPanel,
    panels.CE_PT_ComfyUIPanel,
]


def register():
    bpy.types.Scene.creator_extend_batch_selected = bpy.props.BoolProperty(name="Render this scene", default=False)
    for cls in classes:
        bpy.utils.register_class(cls)
    print("[Creator Extend] Addon registered")


def unregister():
    if hasattr(bpy.types.Scene, "creator_extend_batch_selected"):
        del bpy.types.Scene.creator_extend_batch_selected
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("[Creator Extend] Addon unregistered")


if __name__ == "__main__":
    register()
