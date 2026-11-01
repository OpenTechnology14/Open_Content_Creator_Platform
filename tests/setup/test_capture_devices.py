"""Capture diagnostics parse platform tools without claiming a live recording passed."""

import importlib.util
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "capture_devices", ROOT / "scripts/setup/capture_devices.py"
)
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def test_directshow_parser_keeps_video_and_audio_but_not_alternative_names():
    output = """
[dshow @ 0001] "USB Video" (video)
[dshow @ 0001]   Alternative name "@device_pnp_foo"
[dshow @ 0001] "Digital Audio Interface" (audio)
"""
    devices = capture.parse_dshow_devices(output)
    assert [(item["name"], item["kind"]) for item in devices] == [
        ("USB Video", "video"),
        ("Digital Audio Interface", "audio"),
    ]
    assert all(item["backend"] == "DirectShow" for item in devices)


def test_avfoundation_parser_tracks_video_and_audio_sections():
    output = """
[AVFoundation indev @ 0x1] AVFoundation video devices:
[AVFoundation indev @ 0x1] [0] FaceTime HD Camera
[AVFoundation indev @ 0x1] [1] Capture screen 0
[AVFoundation indev @ 0x1] AVFoundation audio devices:
[AVFoundation indev @ 0x1] [0] MacBook Pro Microphone
"""
    devices = capture.parse_avfoundation_devices(output)
    assert [(item["id"], item["name"]) for item in devices] == [
        ("avfoundation:video:0", "FaceTime HD Camera"),
        ("avfoundation:video:1", "Capture screen 0"),
        ("avfoundation:audio:0", "MacBook Pro Microphone"),
    ]


def test_report_requires_obs_and_a_video_device(monkeypatch):
    monkeypatch.setattr(capture, "ffmpeg_executable", lambda: "ffmpeg")
    monkeypatch.setattr(
        capture,
        "ffmpeg_devices",
        lambda executable, system: (
            [
                {
                    "id": "dshow:video:USB Video",
                    "name": "USB Video",
                    "kind": "video",
                    "backend": "DirectShow",
                }
            ],
            "Capture devices enumerated through FFmpeg.",
        ),
    )
    monkeypatch.setattr(
        capture,
        "obs_installation",
        lambda system: {"found": True, "path": "obs64.exe", "detail": "OBS found"},
    )
    monkeypatch.setattr(capture, "windows_pnp_devices", lambda: [])
    report = capture.build_report("Windows")
    assert report["status"] == "ready_for_obs_setup"
    assert report["scope"].startswith("Enumeration only")
    assert report["video_devices"][0]["name"] == "USB Video"


def test_ffmpeg_device_listing_accepts_expected_nonzero_exit(monkeypatch):
    monkeypatch.setattr(
        capture,
        "command_output",
        lambda command: subprocess.CompletedProcess(
            command, 1, "", '[dshow @ 1] "USB Capture HDMI" (video)'
        ),
    )
    devices, detail = capture.ffmpeg_devices("ffmpeg", "Windows")
    assert devices[0]["name"] == "USB Capture HDMI"
    assert "enumerated" in detail


def test_windows_bootstrap_owns_prerequisites_modules_and_capture_scan():
    script = (ROOT / "scripts/setup/windows.ps1").read_text(encoding="utf-8")
    for value in (
        "Python.Python.3.12",
        "OBSProject.OBSStudio",
        "Gyan.FFmpeg",
        "scripts/setup/modules.py",
        "scripts/setup/capture_devices.py",
        "-PlanOnly",
    ):
        assert value in script
    assert "Invoke-Expression" not in script


def test_windows_pnp_fallback_only_selects_healthy_camera_classes():
    items = [
        {"name": "USB Capture", "class": "Camera", "status": "OK", "instance_id": "one"},
        {"name": "Disabled Cam", "class": "Image", "status": "Error", "instance_id": "two"},
        {"name": "Speakers", "class": "Media", "status": "OK", "instance_id": "three"},
    ]
    assert capture.pnp_capture_devices(items) == [
        {
            "id": "windows-pnp:video:one",
            "name": "USB Capture",
            "kind": "video",
            "backend": "Windows Plug and Play",
        }
    ]


def test_macos_native_fallback_reads_camera_and_input(monkeypatch):
    value = """{
      "SPCameraDataType":[{"_name":"FaceTime HD Camera","spcamera_unique-id":"camera-1"}],
      "SPAudioDataType":[{"_items":[{"_name":"MacBook Pro Microphone","coreaudio_device_input":1}]}]
    }"""
    monkeypatch.setattr(capture.shutil, "which", lambda name: "/usr/sbin/system_profiler")
    monkeypatch.setattr(
        capture,
        "command_output",
        lambda command: subprocess.CompletedProcess(command, 0, value, ""),
    )
    assert [(item["kind"], item["name"]) for item in capture.macos_native_devices()] == [
        ("video", "FaceTime HD Camera"),
        ("audio", "MacBook Pro Microphone"),
    ]
