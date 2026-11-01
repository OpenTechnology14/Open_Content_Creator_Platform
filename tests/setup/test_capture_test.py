"""Capture acceptance probes remain deterministic and bounded without hardware."""

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("capture_test", ROOT / "scripts/setup/capture_test.py")
capture_test = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture_test)


def test_builds_fixed_directshow_command_without_shell_or_arbitrary_path():
    command = capture_test.build_command(
        "ffmpeg", "Windows", "dshow:video:USB Capture", "dshow:audio:Card Audio", "capture.mkv"
    )
    assert command[:7] == ["ffmpeg", "-hide_banner", "-loglevel", "info", "-f", "dshow", "-video_size"]
    assert command[command.index("-i") + 1] == 'video="USB Capture":audio="Card Audio"'
    assert "shell" not in command


def test_builds_avfoundation_command_with_none_audio():
    command = capture_test.build_command("ffmpeg", "Darwin", "avfoundation:video:2", None, "capture.mkv")
    assert command[command.index("-i") + 1] == "2:none"


def test_probe_reports_signal_and_recording_separately(tmp_path):
    output = tmp_path / "capture.mkv"

    def runner(command, **kwargs):
        output.write_bytes(b"recorded")
        return subprocess.CompletedProcess(
            command,
            0,
            "",
            "Stream #0:0: Video: rawvideo\nStream #0:1: Audio: pcm\nframe= 90 time=00:00:03.00",
        )

    # The real probe owns its temp output, so this runner only needs to create the
    # output path supplied by the command.
    def runner_with_command_output(command, **kwargs):
        Path(command[-1]).write_bytes(b"recorded")
        return runner(command, **kwargs)

    report = capture_test.probe(
        "dshow:video:USB Capture",
        "dshow:audio:Card Audio",
        system="Windows",
        executable="ffmpeg",
        runner=runner_with_command_output,
    )
    assert report["status"] == "accepted"
    assert report["stages"] == {"detected": True, "signal": True, "recorded": True, "accepted": True}
    assert report["audio_stream"] is True
    assert report["frames_observed"] == 90


def test_probe_without_ffmpeg_does_not_claim_readiness():
    report = capture_test.probe("dshow:video:USB Capture", system="Windows", executable=None)
    assert report["status"] == "action_required"
    assert report["stages"]["detected"] is True
    assert report["stages"]["signal"] is False
    assert report["stages"]["recorded"] is False


def test_rejects_unscanned_or_unsupported_ids():
    try:
        capture_test.build_command("ffmpeg", "Windows", "../escape", None, "capture.mkv")
    except ValueError as error:
        assert "latest local scan" in str(error)
    else:
        raise AssertionError("unscanned capture ID was accepted")
