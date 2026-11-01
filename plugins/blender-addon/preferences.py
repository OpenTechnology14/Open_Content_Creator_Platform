"""
Creator Extend — Blender addon preferences.
"""

import bpy


class CreatorExtendPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    # Template directory
    template_dir: bpy.props.StringProperty(
        name="Template Directory",
        description="Path to .blend template files (e.g., modules/content-creation/blender/projects)",
        subtype='DIR_PATH',
        default="",
    )

    # ComfyUI
    comfyui_url: bpy.props.StringProperty(
        name="ComfyUI URL",
        description="ComfyUI API endpoint",
        default="http://localhost:8188",
    )

    # MinIO / S3
    minio_endpoint: bpy.props.StringProperty(
        name="MinIO Endpoint",
        description="MinIO or S3-compatible endpoint URL",
        default="http://localhost:9000",
    )

    minio_access_key: bpy.props.StringProperty(
        name="Access Key",
        description="MinIO/S3 access key",
        default="",
    )

    minio_secret_key: bpy.props.StringProperty(
        name="Secret Key",
        description="MinIO/S3 secret key",
        subtype='PASSWORD',
        default="",
    )

    minio_bucket: bpy.props.StringProperty(
        name="Bucket",
        description="Target bucket for uploads",
        default="renders",
    )

    def draw(self, context):
        layout = self.layout

        # Templates
        box = layout.box()
        box.label(text="Templates", icon='FILE_FOLDER')
        box.prop(self, "template_dir")

        # ComfyUI
        box = layout.box()
        box.label(text="ComfyUI", icon='IMAGE')
        box.prop(self, "comfyui_url")

        # MinIO
        box = layout.box()
        box.label(text="MinIO / S3 Storage", icon='EXPORT')
        box.prop(self, "minio_endpoint")
        box.prop(self, "minio_access_key")
        box.prop(self, "minio_secret_key")
        box.prop(self, "minio_bucket")

        # Info
        layout.separator()
        layout.label(
            text="Get Creator Extend for a full dashboard: creatorextend.com",
            icon='URL',
        )
