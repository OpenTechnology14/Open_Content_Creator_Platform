"""Content-addressed cache of rendered local speech (P-068 section 4.3, P-067 section 7.4).

A local engine takes tens of seconds per line, so a line that has not changed must never be
rendered twice. The key covers the text and the whole voice spec, including the *content* of the
reference recording, so re-recording the sample or changing any setting stops old renders being
reused. The logical voice id is deliberately not part of the key: two bindings with the same spec
produce the same audio, and renaming a binding should not re-render the library.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import wave
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import LocalVoice

CACHE_SCHEMA = 1


def cache_key(text: str, voice: LocalVoice, speaker_ref_sha256: str | None) -> str:
    material = {
        "schema": CACHE_SCHEMA,
        "text": text,
        "voice": voice.model_dump(mode="json"),
        "speaker_ref_sha256": speaker_ref_sha256,
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class RenderCache:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def _paths(self, key: str) -> tuple[Path, Path]:
        return self.directory / f"{key}.wav", self.directory / f"{key}.json"

    def fetch(self, key: str, output: Path) -> float | None:
        """Copy a cached render to `output` and return its duration, or None on any miss.

        A truncated or unreadable entry is a miss, never an error: the line is simply rendered
        again and the entry replaced.
        """
        wav, meta = self._paths(key)
        try:
            recorded = json.loads(meta.read_text(encoding="utf-8"))["bytes"]
            if wav.stat().st_size != recorded:
                return None
            with wave.open(str(wav), "rb") as audio:
                frames, rate = audio.getnframes(), audio.getframerate()
        except (OSError, ValueError, KeyError, EOFError, wave.Error):
            return None
        if frames == 0 or rate <= 0:
            return None
        shutil.copyfile(wav, output)
        return frames / rate

    def store(self, key: str, source: Path) -> None:
        """Publish `source` under `key`. The metadata is replaced last, so an entry whose metadata
        exists always has its complete audio, even if two workers store the same line at once."""
        self.directory.mkdir(parents=True, exist_ok=True)
        wav, meta = self._paths(key)
        token = uuid4().hex
        staged_wav = self.directory / f".{key}.{token}.wav.tmp"
        staged_meta = self.directory / f".{key}.{token}.json.tmp"
        try:
            shutil.copyfile(source, staged_wav)
            staged_meta.write_text(
                json.dumps(
                    {
                        "schema": CACHE_SCHEMA,
                        "bytes": staged_wav.stat().st_size,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                encoding="utf-8",
            )
            os.replace(staged_wav, wav)
            os.replace(staged_meta, meta)
        finally:
            staged_wav.unlink(missing_ok=True)
            staged_meta.unlink(missing_ok=True)
