"""
Creator Extend — Krita Plugin Script

This is the main Krita plugin script, loaded by Krita's Python plugin system.
Place this file (or symlink it) in Krita's pykrita/ directory:
  - macOS: ~/Library/Application Support/krita/pykrita/
  - Linux: ~/.local/share/krita/pykrita/
  - Windows: %APPDATA%/krita/pykrita/

Alongside it, create creator_extend_krita.desktop:
  [Desktop Entry]
  Type=Service
  ServiceTypes=Krita/PythonPlugin
  X-KDE-Library=creator_extend_krita
  X-Python-2-Compatible=false
  Name=Creator Extend
  Comment=AI editing, batch processing, and MinIO export
"""

from krita import (
    Krita, Extension, DockWidgetFactory, DockWidgetFactoryBase,
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox,
    QFileDialog, QMessageBox, QGroupBox, QHBoxLayout,
)
from PyQt5.QtCore import Qt
import subprocess
import sys
import os


# Path to the platform's Krita scripts
# Adjust this if the platform is installed elsewhere
PLATFORM_SCRIPTS = os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "modules", "image-editing", "krita", "scripts"
)


class CreatorExtendExtension(Extension):
    """Main extension — registers menu actions."""

    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        """Add Creator Extend menu items to Krita."""
        # Batch Upscale
        action = window.createAction(
            "ce_batch_upscale",
            "Creator Extend: Batch Upscale",
            "tools/scripts"
        )
        action.triggered.connect(self._batch_upscale)

        # Style Transfer
        action = window.createAction(
            "ce_style_transfer",
            "Creator Extend: Style Transfer",
            "tools/scripts"
        )
        action.triggered.connect(self._style_transfer)

        # Export to MinIO
        action = window.createAction(
            "ce_export_minio",
            "Creator Extend: Export to MinIO",
            "tools/scripts"
        )
        action.triggered.connect(self._export_minio)

        # Open Creator Extend App
        action = window.createAction(
            "ce_open_app",
            "Creator Extend: Open App",
            "tools/scripts"
        )
        action.triggered.connect(self._open_app)

    def _run_script(self, script_name, args=None):
        """Run a platform Krita script as a subprocess."""
        script_path = os.path.join(PLATFORM_SCRIPTS, f"{script_name}.py")
        if not os.path.isfile(script_path):
            QMessageBox.warning(
                None, "Creator Extend",
                f"Script not found: {script_path}\n\n"
                f"Make sure the hybrid-creator-platform is installed."
            )
            return

        cmd = [sys.executable, script_path] + (args or [])
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                QMessageBox.information(
                    None, "Creator Extend",
                    f"Script completed:\n{result.stdout[:500]}"
                )
            else:
                QMessageBox.warning(
                    None, "Creator Extend",
                    f"Script error:\n{result.stderr[:500]}"
                )
        except subprocess.TimeoutExpired:
            QMessageBox.warning(
                None, "Creator Extend", "Script timed out after 5 minutes."
            )
        except Exception as e:
            QMessageBox.critical(
                None, "Creator Extend", f"Failed to run script: {e}"
            )

    def _batch_upscale(self):
        folder = QFileDialog.getExistingDirectory(
            None, "Select folder of images to upscale"
        )
        if folder:
            self._run_script("batch_upscale", [
                "--input", folder,
                "--output", os.path.join(folder, "upscaled"),
                "--scale", "2",
            ])

    def _style_transfer(self):
        doc = Krita.instance().activeDocument()
        if not doc:
            QMessageBox.warning(
                None, "Creator Extend", "No document open."
            )
            return

        style_image, _ = QFileDialog.getOpenFileName(
            None, "Select style reference image",
            "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if style_image:
            # Save current document to temp, run style transfer, reload
            tmp_path = os.path.join(
                os.path.dirname(doc.fileName()) or "/tmp",
                "_ce_style_input.png"
            )
            doc.exportImage(tmp_path, doc.exportParameters("PNG"))
            self._run_script("apply_style", [
                "--input", tmp_path,
                "--style", style_image,
                "--output", tmp_path.replace("_input", "_output"),
            ])

    def _export_minio(self):
        doc = Krita.instance().activeDocument()
        if not doc:
            QMessageBox.warning(
                None, "Creator Extend", "No document open."
            )
            return

        self._run_script("export_to_minio", [
            "--input", doc.fileName() or "untitled",
        ])

    def _open_app(self):
        import webbrowser
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", "creatorextend://"])
            elif sys.platform == "win32":
                subprocess.Popen(["start", "creatorextend://"], shell=True)
            else:
                subprocess.Popen(["xdg-open", "creatorextend://"])
        except Exception:
            webbrowser.open("https://creatorextend.com/download")


class CreatorExtendDocker(QWidget):
    """Dockable panel with quick-access buttons."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Creator Extend")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # Header
        header = QLabel("Creator Extend")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        # AI Editing group
        ai_group = QGroupBox("AI Editing")
        ai_layout = QVBoxLayout()

        btn_upscale = QPushButton("Batch Upscale")
        btn_upscale.setToolTip("Upscale images via ComfyUI")
        ai_layout.addWidget(btn_upscale)

        # Style preset selector
        style_row = QHBoxLayout()
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "anime", "watercolor", "oil-painting",
            "pixel-art", "cinematic", "custom..."
        ])
        style_row.addWidget(QLabel("Style:"))
        style_row.addWidget(self.style_combo)
        ai_layout.addLayout(style_row)

        btn_style = QPushButton("Apply Style Transfer")
        btn_style.setToolTip("IPAdapter style transfer via ComfyUI")
        ai_layout.addWidget(btn_style)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        # Export group
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()

        btn_minio = QPushButton("Export to MinIO")
        btn_minio.setToolTip("Upload composite + layers to MinIO/S3")
        export_layout.addWidget(btn_minio)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        # Open app button
        btn_app = QPushButton("Open Creator Extend")
        btn_app.setToolTip("Open the full Creator Extend dashboard")
        btn_app.setStyleSheet(
            "background-color: #7c4dff; color: white; "
            "padding: 8px; border-radius: 4px;"
        )
        layout.addWidget(btn_app)

        self.setLayout(layout)


# Register with Krita
Krita.instance().addExtension(CreatorExtendExtension(Krita.instance()))
