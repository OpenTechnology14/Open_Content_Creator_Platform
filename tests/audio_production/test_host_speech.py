"""Speech export rejects cross-session content and does not evaluate viewer text."""

import importlib.util
import json
import subprocess
import wave
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "host_speech", ROOT / "modules/audio-production/tts/render_reply.py"
)
speech = importlib.util.module_from_spec(spec)
spec.loader.exec_module(speech)


def test_reply_session_and_kind_checked(tmp_path):
    path = tmp_path / "reply.json"
    path.write_text(
        json.dumps({"schema_version": 1, "kind": "reply", "session_id": "one", "text": "Hello"})
    )
    assert speech.read_reply(path, "one") == "Hello"
    with pytest.raises(ValueError):
        speech.read_reply(path, "two")
    path.write_text(
        json.dumps({"schema_version": 1, "kind": "control", "session_id": "one", "text": "Hello"})
    )
    with pytest.raises(ValueError):
        speech.read_reply(path, "one")


def test_speech_text_is_stdin_and_rendered_audio_is_checked(monkeypatch, tmp_path):
    text = "--voice bad $(do-not-execute) `or-this`"

    def run(command, **kwargs):
        assert text not in command
        assert kwargs["input"] == text
        assert "shell" not in kwargs
        output = command[command.index("-o") + 1]
        with wave.open(output, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(22050)
            audio.writeframes(b"\x00\x01" * 22050)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(speech.sys, "platform", "darwin")
    monkeypatch.setattr(speech.shutil, "which", lambda _: "/usr/bin/say")
    monkeypatch.setattr(speech.subprocess, "run", run)
    output = tmp_path / "speech.wav"
    assert speech.render(text, output) == 1
    assert output.exists()
    with pytest.raises(ValueError):
        speech.render("overwrite", output)


def test_windows_speech_keeps_untrusted_values_in_json(monkeypatch, tmp_path):
    text = "Nova: café $(Stop-Process) `whoami` ; --voice"
    voice = "Voice ' $(do-not-run)"

    def run(command, **kwargs):
        assert text not in " ".join(command)
        assert voice not in " ".join(command)
        assert "shell" not in kwargs
        assert "ExecutionPolicy" not in " ".join(command)
        payload = json.loads(kwargs["input"])
        assert payload["text"] == text
        assert payload["voice"] == voice
        with wave.open(payload["output"], "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(22050)
            audio.writeframes(b"\x00\x01" * 22050)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(speech.sys, "platform", "win32")
    monkeypatch.setattr(speech.shutil, "which", lambda _: "powershell.exe")
    monkeypatch.setattr(speech.subprocess, "run", run)
    assert speech.render(text, tmp_path / "café with spaces" / "speech.wav", voice) == 1


def test_windows_synthesis_failure_does_not_leave_output(monkeypatch, tmp_path):
    def run(command, **kwargs):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(speech.sys, "platform", "win32")
    monkeypatch.setattr(speech.shutil, "which", lambda _: "powershell.exe")
    monkeypatch.setattr(speech.subprocess, "run", run)
    output = tmp_path / "speech.wav"
    with pytest.raises(subprocess.CalledProcessError):
        speech.render("Hello", output)
    assert not output.exists()
