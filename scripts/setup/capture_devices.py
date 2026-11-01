"""Inspect local capture hardware for OBS setup on Windows or macOS."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def command_output(command: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    """Run a fixed local diagnostic command without a shell."""
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def ffmpeg_executable() -> str | None:
    """Prefer a system FFmpeg, then the isolated imageio-ffmpeg binary when installed."""
    candidates = [shutil.which("ffmpeg")]
    if platform.system() == "Darwin":
        candidates.extend(["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"])
    elif platform.system() == "Windows":
        candidates.extend(
            [
                str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Links/ffmpeg.exe"),
                str(Path(os.environ.get("ProgramFiles", "")) / "WinGet/Links/ffmpeg.exe"),
            ]
        )
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    try:
        import imageio_ffmpeg

        candidate = imageio_ffmpeg.get_ffmpeg_exe()
        if Path(candidate).is_file():
            return candidate
    except (ImportError, OSError, RuntimeError):
        pass
    root = Path(__file__).resolve().parents[2]
    data_root = Path(os.environ.get("HCP_MODULE_DATA_ROOT", str(root)))
    environments = [
        data_root / ".venv-modules/content-creation",
        root / ".venv-stream-autopilot",
    ]
    for environment in environments:
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not python.is_file():
            continue
        try:
            result = command_output(
                [str(python), "-I", "-c", "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"],
                timeout=10,
            )
            candidate = result.stdout.strip()
            if result.returncode == 0 and Path(candidate).is_file():
                return candidate
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def parse_dshow_devices(output: str) -> list[dict[str, str]]:
    """Parse FFmpeg's DirectShow device list without treating alternative names as devices."""
    devices: list[dict[str, str]] = []
    pattern = re.compile(r'^\[[^]]+\]\s+"(.+)" \((video|audio)\)\s*$')
    for line in output.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        name, kind = match.groups()
        devices.append(
            {
                "id": f"dshow:{kind}:{name}",
                "name": name,
                "kind": kind,
                "backend": "DirectShow",
            }
        )
    return devices


def parse_avfoundation_devices(output: str) -> list[dict[str, str]]:
    """Parse FFmpeg's AVFoundation video and audio sections."""
    devices: list[dict[str, str]] = []
    kind: str | None = None
    section = re.compile(r"AVFoundation (video|audio) devices:")
    item = re.compile(r"\[(\d+)\]\s+(.+)$")
    for line in output.splitlines():
        section_match = section.search(line)
        if section_match:
            kind = section_match.group(1)
            continue
        if kind is None:
            continue
        # FFmpeg prefixes the useful '[0] Name' with one or more logging brackets.
        matches = list(item.finditer(line))
        if not matches:
            continue
        index, name = matches[-1].groups()
        if "AVFoundation" in name and "devices:" in name:
            continue
        devices.append(
            {
                "id": f"avfoundation:{kind}:{index}",
                "name": name.strip(),
                "kind": kind,
                "backend": "AVFoundation",
            }
        )
    return devices


def ffmpeg_devices(executable: str | None, system: str) -> tuple[list[dict[str, str]], str]:
    """Enumerate media devices through the platform backend used by FFmpeg/OBS."""
    if not executable:
        return [], "FFmpeg was not found; install it to enumerate OBS-compatible capture names."
    if system == "Windows":
        command = [executable, "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"]
        parser = parse_dshow_devices
    elif system == "Darwin":
        command = [executable, "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""]
        parser = parse_avfoundation_devices
    else:
        return [], f"Capture enumeration is not implemented for {system}."
    try:
        result = command_output(command)
        # Device-list invocations normally return nonzero because no media is captured.
        devices = parser(f"{result.stdout}\n{result.stderr}")
        return devices, "Capture devices enumerated through FFmpeg." if devices else "FFmpeg returned no capture devices."
    except (OSError, subprocess.SubprocessError):
        return [], "FFmpeg could not enumerate capture devices."


def windows_pnp_devices() -> list[dict[str, str]]:
    """Return present Windows camera/image/media devices as secondary driver evidence."""
    executable = shutil.which("powershell.exe") or shutil.which("powershell")
    if not executable:
        return []
    script = (
        "$ErrorActionPreference='Stop';"
        "$items=@(Get-PnpDevice -PresentOnly | Where-Object "
        "{$_.Class -in @('Camera','Image','Media')});"
        "$items | Select-Object FriendlyName,Class,Status,InstanceId | ConvertTo-Json -Compress"
    )
    try:
        result = command_output([executable, "-NoProfile", "-NonInteractive", "-Command", script])
        if result.returncode != 0 or not result.stdout.strip():
            return []
        value = json.loads(result.stdout)
        rows = value if isinstance(value, list) else [value]
        return [
            {
                "name": str(row.get("FriendlyName") or "Unknown device"),
                "class": str(row.get("Class") or "Unknown"),
                "status": str(row.get("Status") or "Unknown"),
                "instance_id": str(row.get("InstanceId") or ""),
            }
            for row in rows
            if isinstance(row, dict)
        ]
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def macos_native_devices() -> list[dict[str, str]]:
    """Use system_profiler as a no-install fallback for Mac camera and input discovery."""
    executable = shutil.which("system_profiler")
    if not executable:
        standard = Path("/usr/sbin/system_profiler")
        if not standard.is_file():
            return []
        executable = str(standard)
    try:
        result = command_output([executable, "SPCameraDataType", "SPAudioDataType", "-json"])
        if result.returncode != 0:
            return []
        value = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return []
    devices: list[dict[str, str]] = []
    for item in value.get("SPCameraDataType", []):
        if not isinstance(item, dict) or not item.get("_name"):
            continue
        identity = str(item.get("spcamera_unique-id") or item["_name"])
        devices.append(
            {
                "id": f"system-profiler:video:{identity}",
                "name": str(item["_name"]),
                "kind": "video",
                "backend": "macOS camera",
            }
        )

    def audio_items(item: Any) -> None:
        if isinstance(item, list):
            for child in item:
                audio_items(child)
        elif isinstance(item, dict):
            if item.get("_name") and item.get("coreaudio_device_input"):
                name = str(item["_name"])
                devices.append(
                    {
                        "id": f"system-profiler:audio:{name}",
                        "name": name,
                        "kind": "audio",
                        "backend": "CoreAudio",
                    }
                )
            for child in item.values():
                audio_items(child)

    audio_items(value.get("SPAudioDataType", []))
    return devices


def pnp_capture_devices(items: list[dict[str, str]]) -> list[dict[str, str]]:
    """Convert Windows PnP camera/image devices into first-run video choices."""
    return [
        {
            "id": f"windows-pnp:video:{item['instance_id']}",
            "name": item["name"],
            "kind": "video",
            "backend": "Windows Plug and Play",
        }
        for item in items
        if item["class"] in {"Camera", "Image"} and item["status"].lower() == "ok"
    ]


def obs_installation(system: str) -> dict[str, Any]:
    """Find OBS in PATH or its standard install location."""
    candidates: list[Path] = []
    on_path = shutil.which("obs64") or shutil.which("obs")
    if on_path:
        candidates.append(Path(on_path))
    if system == "Windows":
        for root in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            if root:
                candidates.append(Path(root) / "obs-studio/bin/64bit/obs64.exe")
    elif system == "Darwin":
        candidates.append(Path("/Applications/OBS.app/Contents/MacOS/OBS"))
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    return {
        "found": path is not None,
        "path": str(path) if path else None,
        "detail": "OBS Studio found; add the selected capture device as a Video Capture Device source."
        if path
        else "OBS Studio was not found in PATH or its standard install location.",
    }


def build_report(system: str | None = None) -> dict[str, Any]:
    """Build a fresh, local-only device report without opening a capture stream."""
    system = system or platform.system()
    ffmpeg = ffmpeg_executable()
    devices, enumeration_detail = ffmpeg_devices(ffmpeg, system)
    ffmpeg_devices_found = bool(devices)
    pnp = windows_pnp_devices() if system == "Windows" else []
    native = macos_native_devices() if system == "Darwin" else []
    if not devices:
        devices = pnp_capture_devices(pnp) if system == "Windows" else native
    video = [item for item in devices if item["kind"] == "video"]
    audio = [item for item in devices if item["kind"] == "audio"]
    obs = obs_installation(system)
    recommendations: list[str] = []
    if not obs["found"]:
        recommendations.append("Install OBS Studio before configuring a capture source.")
    if not ffmpeg:
        recommendations.append("Install FFmpeg so setup can enumerate capture-device names.")
    if not video:
        recommendations.append(
            "Connect the capture card directly to USB 3, connect the console HDMI output to its HDMI input, then scan again."
        )
    else:
        recommendations.append(
            "Select the intended video and audio devices, save them, then add the same names to an OBS Video Capture Device source."
        )
    recommendations.append(
        "Run a local OBS recording and confirm picture, game audio, microphone sync and 1080p60 stability before streaming."
    )
    return {
        "schema_version": 1,
        "checked_at": int(time.time()),
        "platform": system,
        "status": "ready_for_obs_setup" if obs["found"] and video else "action_required",
        "obs": obs,
        "ffmpeg": {
            "found": ffmpeg is not None,
            "path": ffmpeg,
            "detail": enumeration_detail,
        },
        "devices": devices,
        "video_devices": video,
        "audio_devices": audio,
        "windows_pnp_devices": pnp,
        "native_fallback_used": bool(devices) and not ffmpeg_devices_found,
        "recommendations": recommendations,
        "scope": "Enumeration only; a saved device still requires a real OBS recording test.",
    }


def render_text(report: dict[str, Any]) -> str:
    """Render a concise terminal report while retaining JSON for the desktop app."""
    lines = [
        f"Capture setup: {report['status']}",
        f"Platform: {report['platform']}",
        f"OBS: {report['obs']['detail']}",
        f"FFmpeg: {report['ffmpeg']['detail']}",
    ]
    for kind in ("video", "audio"):
        items = report[f"{kind}_devices"]
        lines.append(f"{kind.title()} devices ({len(items)}):")
        lines.extend(f"  - {item['name']} [{item['backend']}]" for item in items)
    lines.append("Next steps:")
    lines.extend(f"  - {item}" for item in report["recommendations"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="write the report as JSON")
    parser.add_argument("--output", type=Path, help="also save the JSON report to this path")
    args = parser.parse_args()
    report = build_report()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        temporary.replace(args.output)
    sys.stdout.write((json.dumps(report) if args.json else render_text(report)) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
