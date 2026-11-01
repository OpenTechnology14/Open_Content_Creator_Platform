"""Read-only accepted local Soundboard manifest contract. No cross-module code imports."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Asset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reaction: str
    text: str = Field(min_length=1, max_length=280)
    file: Path
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    duration_seconds: float = Field(gt=0, le=30)
    peak: float = Field(gt=0, lt=1)
    hotkey: str = Field(min_length=1, max_length=200)


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision_id: str
    game_id: str
    voice_id: str
    stop_hotkey: str = Field(min_length=1, max_length=200)
    assets: list[Asset] = Field(min_length=1, max_length=8)


def load(path: Path | None) -> dict[str, Profile]:
    """Pin production revisions for the worker lifetime; restart at the session boundary."""
    if path is None:
        return {}
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("Phrase manifest exceeds 1 MiB")
    data = json.loads(path.read_text())
    if data.get("schema_version") != 1 or len(data.get("profiles", {})) > 32:
        raise ValueError("Invalid phrase manifest")
    return {key: Profile.model_validate(value) for key, value in data["profiles"].items()}


def intact(asset: Asset) -> bool:
    """Missing or changed assets may fall back before dispatch, never after a timeout."""
    try:
        return (
            asset.file.is_absolute()
            and asset.file.stat().st_size <= 5 * 1024 * 1024
            and hashlib.sha256(asset.file.read_bytes()).hexdigest() == asset.sha256
        )
    except OSError:
        return False
