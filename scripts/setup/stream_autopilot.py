"""Install, diagnose and rehearse Stream Autopilot on Windows or macOS with Python 3.11+."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import uuid
import venv
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
DEPENDENCIES = ("pydantic", "httpx", "PyYAML", "loguru", "websockets", "imageio-ffmpeg", "tzdata")


def environment() -> dict[str, str]:
    """Supply platform-correct module paths and consistent subprocess text encoding."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(
        str(ROOT / "modules" / name)
        for name in ("ai-agents", "automation-control", "content-creation")
    )
    return env


def install() -> None:
    """Create an isolated environment; use its interpreter without shell activation."""
    destination = ROOT / ".venv-stream-autopilot"
    executable = destination / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not destination.exists():
        venv.EnvBuilder(with_pip=True).create(destination)
    if not executable.is_file():
        raise RuntimeError("Existing .venv-stream-autopilot has no compatible interpreter")
    subprocess.run(
        [str(executable), "-c", "import sys; assert sys.version_info >= (3,11)"], check=True
    )
    subprocess.run(
        [
            str(executable),
            "-m",
            "pip",
            "install",
            "-r",
            str(ROOT / "configs/local/stream-test-requirements.txt"),
        ],
        check=True,
    )
    sys.stdout.write(
        f"Ready: {executable}\nNext: run this script's doctor and smoke commands with that interpreter.\n"
    )


def doctor() -> dict:
    """Check core prerequisites; OBS and Ollama are optional for the scripted test."""
    checks = {
        "python_3_11": sys.version_info >= (3, 11),
        "supported_os": sys.platform in {"win32", "darwin"},
    }
    versions = {}
    for name in DEPENDENCIES:
        try:
            versions[name] = importlib.metadata.version(name)
            checks[name] = True
        except importlib.metadata.PackageNotFoundError:
            checks[name] = False
    checks["native_speech_executable"] = bool(
        shutil.which("powershell.exe" if sys.platform == "win32" else "say")
    )
    try:
        ZoneInfo("America/New_York")
        checks["show_timezone"] = True
    except (KeyError, ValueError):
        checks["show_timezone"] = False
    try:
        import imageio_ffmpeg

        result = subprocess.run(
            [imageio_ffmpeg.get_ffmpeg_exe(), "-version"],
            capture_output=True,
            timeout=15,
            check=True,
        )
        checks["ffmpeg_executable"] = result.returncode == 0
    except (ImportError, OSError, RuntimeError, subprocess.SubprocessError):
        checks["ffmpeg_executable"] = False
    return {
        "ready": all(checks.values()),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "checks": checks,
        "versions": versions,
        "optional_on_path": {
            "obs": bool(shutil.which("obs64") or shutil.which("obs")),
            "ollama": bool(shutil.which("ollama")),
        },
        "note": "Native voice synthesis is verified by smoke. Optional apps may be installed outside PATH.",
    }


def smoke(destination: Path) -> dict:
    """Run actual local CLIs, synthesize speech and render three synthetic video highlights."""
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "running",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "steps": [],
        "llm_mode": "scripted",
        "obs_tested": False,
        "gameplay_tested": False,
        "live_chat_tested": False,
        "published": False,
        "native_speech": "System.Speech" if sys.platform == "win32" else "say",
    }
    report_path = destination / "report.json"

    def save() -> None:
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def step(name: str, command: list[str]) -> Path:
        entry = {"name": name, "status": "running"}
        report["steps"].append(entry)
        save()
        started = time.monotonic()
        output = destination / f"{name}.json"
        sys.stdout.write(f"Running {name}...\n")
        sys.stdout.flush()
        try:
            with (
                output.open("w", encoding="utf-8") as stdout,
                (destination / f"{name}.log").open("w", encoding="utf-8") as stderr,
            ):
                subprocess.run(
                    command,
                    cwd=ROOT,
                    env=environment(),
                    stdout=stdout,
                    stderr=stderr,
                    check=True,
                    timeout=600,
                )
            entry["status"] = "passed"
            return output
        except BaseException:
            entry["status"] = "failed"
            raise
        finally:
            entry["seconds"] = round(time.monotonic() - started, 2)
            save()

    def cli(module: str, *args: object) -> list[str]:
        return [sys.executable, "-m", module, *(str(arg) for arg in args)]

    save()
    try:
        report["doctor"] = doctor()
        save()
        if not report["doctor"]["ready"]:
            raise RuntimeError("Core prerequisites missing; inspect report.json doctor checks")
        step("host-validation", cli("stream_host", "--validate"))
        step("director-validation", cli("stream_director", "--validate"))
        supervisor = step("supervisor-rehearsal", cli("stream_autopilot", "rehearse"))
        supervisor_report = json.loads(supervisor.read_text(encoding="utf-8"))
        if supervisor_report["broadcast_started"] or supervisor_report["status"]["lifecycle"] != "stopped":
            raise ValueError("Lifecycle rehearsal must stop without starting a broadcast")
        events = step(
            "host-rehearsal",
            cli(
                "stream_host",
                "--rehearsal",
                "--input",
                ROOT / "configs/local/stream-autopilot-demo.jsonl",
            ),
        )
        step("director-preview", cli("stream_director", "--input", events))
        replies = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
        reply = next(
            value
            for value in replies
            if value.get("kind") == "reply" and value["session_id"] == "minecraft-main"
        )
        reply_path = destination / "reply.json"
        reply_path.write_text(json.dumps(reply), encoding="utf-8")
        step(
            "speech",
            [
                sys.executable,
                str(ROOT / "modules/audio-production/tts/render_reply.py"),
                "--reply",
                str(reply_path),
                "--session",
                "minecraft-main",
                "--output",
                str(destination / "reply.wav"),
            ],
        )
        calendar_path = step("calendar", cli("show_planner", "--start", "2026-09-08", "--days", 28))
        if len(json.loads(calendar_path.read_text(encoding="utf-8"))["episodes"]) != 28:
            raise ValueError("Calendar must contain 28 episodes")
        import imageio_ffmpeg

        source = destination / "source.mp4"
        step(
            "synthetic-source",
            [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-n",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=640x360:rate=15",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=44100",
                "-t",
                "90",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-crf",
                "30",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                str(source),
            ],
        )
        job = ROOT / "configs/local/stream-shorts-demo.json"
        plan = step("clip-plan", cli("stream_shorts", "select", "--job", job))
        step(
            "clip-review",
            cli("stream_shorts", "review", "--plan", plan, "--output", destination / "review.html"),
        )
        manifest = step(
            "shorts",
            cli(
                "stream_shorts",
                "produce",
                "--job",
                job,
                "--source",
                source,
                "--output",
                destination / "shorts",
            ),
        )
        rendered = json.loads(manifest.read_text(encoding="utf-8"))
        if rendered["status"] != "complete" or len(rendered["outputs"]) != 3:
            raise ValueError("Expected three verified vertical clips")
        if sum(item["captions"] for item in rendered["outputs"]) != 3:
            raise ValueError("Expected three applied caption cues")
        if sum(item["punch_ins"] for item in rendered["outputs"]) != 2:
            raise ValueError("Expected two applied punch-in cues")
        if not all(item["audio_normalized"] for item in rendered["outputs"]):
            raise ValueError("Expected normalized audio in every clip")
        report["status"] = "passed"
    except BaseException as exc:
        report["status"] = "failed"
        report["error_type"] = type(exc).__name__
        raise
    finally:
        save()
        sys.stdout.write(f"Test report: {report_path}\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("install", help="install Python dependencies into a local virtual environment")
    sub.add_parser("doctor", help="check local test prerequisites")
    test = sub.add_parser(
        "smoke", help="run a local rehearsal with real speech and synthetic Shorts"
    )
    test.add_argument("--output", type=Path, help="new output folder (must not exist)")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        sys.stderr.write("Use Python 3.11 or newer; Python 3.12 is the documented test target.\n")
        return 1
    try:
        if args.command == "install":
            install()
        elif args.command == "doctor":
            result = doctor()
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
            return 0 if result["ready"] else 1
        else:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            smoke(
                args.output
                or ROOT / "output/stream-autopilot" / f"local-test-{stamp}-{uuid.uuid4().hex[:6]}"
            )
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.stderr.write(
            f"{args.command} failed: {type(exc).__name__}. Check prerequisites and the test report/logs.\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
