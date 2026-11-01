"""
Creator Extend — Blender sidebar panels.
"""

import bpy


class CE_PT_MainPanel(bpy.types.Panel):
    """Creator Extend main panel"""
    bl_label = "Creator Extend"
    bl_idname = "CE_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Creator Extend"

    def draw(self, context):
        layout = self.layout
        layout.operator("creator_extend.open_app", icon='URL')


class CE_PT_TemplatesPanel(bpy.types.Panel):
    """Template gallery panel"""
    bl_label = "Templates"
    bl_idname = "CE_PT_templates"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Creator Extend"
    bl_parent_id = "CE_PT_main"

    def draw(self, context):
        layout = self.layout
        layout.operator("creator_extend.open_templates", icon='FILE_FOLDER')
        layout.label(text="Starter .blend files for")
        layout.label(text="intros, overlays, motion graphics")


class CE_PT_ExportPanel(bpy.types.Panel):
    """Export / upload panel"""
    bl_label = "Export"
    bl_idname = "CE_PT_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Creator Extend"
    bl_parent_id = "CE_PT_main"

    def draw(self, context):
        layout = self.layout
        layout.operator("creator_extend.upload_minio", icon='EXPORT')
        layout.operator("creator_extend.batch_render", icon='RENDER_ANIMATION')


class CE_PT_ComfyUIPanel(bpy.types.Panel):
    """ComfyUI integration panel"""
    bl_label = "ComfyUI"
    bl_idname = "CE_PT_comfyui"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Creator Extend"
    bl_parent_id = "CE_PT_main"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        op = row.operator("creator_extend.send_comfyui", text="Upscale", icon='IMAGE')
        op.workflow = "upscale"

        row = layout.row()
        op = row.operator("creator_extend.send_comfyui", text="Style Transfer", icon='BRUSH_DATA')
        op.workflow = "stylize"

        row = layout.row()
        op = row.operator("creator_extend.send_comfyui", text="Inpaint", icon='TPAINT_HLT')
        op.workflow = "inpaint"
