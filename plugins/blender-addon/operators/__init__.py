"""
Creator Extend Blender operators.
"""

import bpy
import os
import subprocess
import json
import uuid
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


# -------------------------------------------------------------------------
# Template Gallery
# -------------------------------------------------------------------------

class CE_OT_OpenTemplateGallery(bpy.types.Operator):
    """Open the Creator Extend template gallery"""
    bl_idname = "creator_extend.open_templates"
    bl_label = "Open Template Gallery"
    bl_options = {'REGISTER'}

    def execute(self, context):
        # Templates are in the platform's content-creation/blender/projects/ dir
        prefs = context.preferences.addons[__package__.split('.')[0]].preferences
        template_dir = prefs.template_dir

        if not template_dir or not os.path.isdir(template_dir):
            self.report({'WARNING'},
                "Template directory not set. Go to Edit → Preferences → "
                "Add-ons → Creator Extend to configure.")
            return {'CANCELLED'}

        # List .blend files in the template directory
        templates = list(Path(template_dir).glob("**/*.blend"))
        if not templates:
            self.report({'INFO'}, f"No .blend templates found in {template_dir}")
            return {'CANCELLED'}

        # For now, report the count. A proper gallery UI comes later.
        self.report({'INFO'},
            f"Found {len(templates)} templates in {template_dir}")
        return {'FINISHED'}


# -------------------------------------------------------------------------
# MinIO Upload
# -------------------------------------------------------------------------

class CE_OT_UploadToMinio(bpy.types.Operator):
    """Upload the current render to MinIO/S3"""
    bl_idname = "creator_extend.upload_minio"
    bl_label = "Upload to MinIO"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if not HAS_BOTO3:
            self.report({'ERROR'},
                "boto3 not installed. Run: pip install boto3")
            return {'CANCELLED'}

        prefs = context.preferences.addons[__package__.split('.')[0]].preferences

        # Get the render output path
        output_path = bpy.context.scene.render.filepath
        if not output_path:
            self.report({'ERROR'}, "No render output path set")
            return {'CANCELLED'}

        # Resolve the actual rendered file
        render_file = bpy.path.abspath(output_path)
        if not os.path.isfile(render_file):
            self.report({'WARNING'},
                f"Render file not found: {render_file}. Render first.")
            return {'CANCELLED'}

        try:
            s3 = boto3.client(
                's3',
                endpoint_url=prefs.minio_endpoint,
                aws_access_key_id=prefs.minio_access_key,
                aws_secret_access_key=prefs.minio_secret_key,
            )

            bucket = prefs.minio_bucket or "renders"
            filename = os.path.basename(render_file)
            key = f"blender/{bpy.path.basename(bpy.data.filepath)}/{filename}"

            s3.upload_file(render_file, bucket, key)
            self.report({'INFO'}, f"Uploaded to {bucket}/{key}")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Upload failed: {str(e)}")
            return {'CANCELLED'}


# -------------------------------------------------------------------------
# ComfyUI Integration
# -------------------------------------------------------------------------

class CE_OT_SendToComfyUI(bpy.types.Operator):
    """Send the current render/frame to ComfyUI for AI processing"""
    bl_idname = "creator_extend.send_comfyui"
    bl_label = "Send to ComfyUI"
    bl_options = {'REGISTER'}

    workflow: bpy.props.StringProperty(
        name="Workflow",
        description="ComfyUI workflow to use (e.g., upscale, stylize)",
        default="upscale"
    )

    def execute(self, context):
        if not HAS_REQUESTS:
            self.report({'ERROR'},
                "requests not installed. Run: pip install requests")
            return {'CANCELLED'}

        prefs = context.preferences.addons[__package__.split('.')[0]].preferences
        comfyui_url = prefs.comfyui_url

        # Check ComfyUI availability
        try:
            resp = requests.get(f"{comfyui_url}/system_stats", timeout=3)
            if resp.status_code != 200:
                self.report({'ERROR'}, "ComfyUI is not responding")
                return {'CANCELLED'}
        except Exception:
            self.report({'ERROR'},
                f"Cannot reach ComfyUI at {comfyui_url}. Is it running?")
            return {'CANCELLED'}

        # Get current frame as image
        output_path = bpy.context.scene.render.filepath
        render_file = bpy.path.abspath(output_path)

        if not os.path.isfile(render_file):
            self.report({'WARNING'}, "No rendered frame found. Render first.")
            return {'CANCELLED'}

        # Upload image to ComfyUI input directory
        try:
            with open(render_file, 'rb') as f:
                files = {'image': (os.path.basename(render_file), f)}
                resp = requests.post(
                    f"{comfyui_url}/upload/image",
                    files=files,
                )

            if resp.status_code != 200:
                self.report({'ERROR'},
                    f"ComfyUI upload failed: {resp.text}")
                return {'CANCELLED'}

            upload_result = resp.json()
            filename = upload_result.get('name', '')

            self.report({'INFO'},
                f"Sent to ComfyUI as '{filename}' — "
                f"open ComfyUI to run the {self.workflow} workflow")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"ComfyUI send failed: {str(e)}")
            return {'CANCELLED'}


# -------------------------------------------------------------------------
# Open Creator Extend App
# -------------------------------------------------------------------------

class CE_OT_OpenCreatorExtend(bpy.types.Operator):
    """Open the Creator Extend desktop app"""
    bl_idname = "creator_extend.open_app"
    bl_label = "Open Creator Extend"
    bl_options = {'REGISTER'}

    def execute(self, context):
        import sys
        import webbrowser

        # Try URL scheme first, fall back to website
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", "creatorextend://"])
            elif sys.platform == "win32":
                subprocess.Popen(["start", "creatorextend://"], shell=True)
            else:
                subprocess.Popen(["xdg-open", "creatorextend://"])
        except Exception:
            webbrowser.open("https://creatorextend.com/download")

        return {'FINISHED'}


# -------------------------------------------------------------------------
# Batch Render
# -------------------------------------------------------------------------

class CE_OT_BatchRender(bpy.types.Operator):
    """Render selected saved-project scenes locally; uploads remain a separate action"""
    bl_idname = "creator_extend.batch_render"
    bl_label = "Render Selected Scenes Locally"
    bl_options = {'REGISTER'}

    output_directory: bpy.props.StringProperty(name="Output folder", subtype='DIR_PATH')

    def invoke(self, context, event):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Save the project before submitting a render job")
            return {'CANCELLED'}
        self.output_directory = str(Path(bpy.data.filepath).parent / "creator-extend-renders")
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        self.layout.label(text="Renders saved-project PNG stills. Save scene edits first.")
        self.layout.prop(self, "output_directory")
        for scene in bpy.data.scenes:
            self.layout.prop(scene, "creator_extend_batch_selected", text=scene.name)

    def execute(self, context):
        selected = [scene.name for scene in bpy.data.scenes if scene.creator_extend_batch_selected]
        if not 1 <= len(selected) <= 16:
            self.report({'ERROR'}, "Select 1–16 scenes")
            return {'CANCELLED'}
        script = Path(__file__).resolve().parents[1] / "render_worker.py"
        if not script.is_file():
            script = Path(__file__).resolve().parents[3] / "modules/content-creation/blender/scripts/batch_render.py"
        if not script.is_file():
            self.report({'ERROR'}, "Use the packaged Creator Extend addon; render worker is missing")
            return {'CANCELLED'}
        root = Path(bpy.path.abspath(self.output_directory)).resolve()
        root.mkdir(parents=True, exist_ok=True)
        ident = uuid.uuid4().hex
        self._metadata = root / f"blender-{ident}" / "job.json"
        self._log_path = root / f"blender-{ident}.log"
        log = os.fdopen(os.open(self._log_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_APPEND, 0o600), 'wb')
        command = [bpy.app.binary_path, '--factory-startup', '--disable-autoexec', '--background',
                   bpy.data.filepath, '--python', str(script), '--', '--output', str(root), '--job-id', ident]
        command.extend(f'--scene={name}' for name in selected)
        try:
            self._process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log)
        except OSError:
            log.close()
            self.report({'ERROR'}, "Blender job process did not start")
            return {'CANCELLED'}
        log.close()
        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Owned local render job started; no upload enabled")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            try:
                if self._log_path.stat().st_size > 1048576:
                    with self._log_path.open('wb'):
                        pass
            except OSError:
                if not getattr(self, '_log_warning', False):
                    self.report({'WARNING'}, "Job log is unavailable; still observing the owned process")
                    self._log_warning = True
        if event.type == 'ESC':
            self._process.kill()
            self._process.wait(timeout=10)
            context.window_manager.event_timer_remove(self._timer)
            if self._metadata.is_file():
                try:
                    value = json.loads(self._metadata.read_text())
                    if not isinstance(value, dict):
                        raise ValueError("Invalid job manifest")
                    value['status'] = 'cancelled'
                    temporary = self._metadata.with_suffix('.cancel-tmp')
                    temporary.write_text(json.dumps(value))
                    temporary.replace(self._metadata)
                except (OSError, ValueError):
                    self.report({'ERROR'}, "Worker stopped, but its cancellation manifest could not be saved")
            self.report({'WARNING'}, "Owned render job cancelled; earlier outputs retained")
            return {'CANCELLED'}
        if event.type == 'TIMER' and self._process.poll() is not None:
            context.window_manager.event_timer_remove(self._timer)
            try:
                value = json.loads(self._metadata.read_text())
                if not isinstance(value, dict):
                    raise ValueError("Invalid job manifest")
            except (OSError, ValueError):
                self.report({'ERROR'}, "Worker exited without a readable job manifest; inspect retained outputs")
                return {'CANCELLED'}
            if self._process.returncode == 0 and value.get('status') == 'complete':
                self.report({'INFO'}, "Local render job completed; inspect its manifest and PNGs")
                return {'FINISHED'}
            self.report({'ERROR'}, "Render job failed; successful outputs and logs are preserved")
            return {'CANCELLED'}
        return {'PASS_THROUGH'}
