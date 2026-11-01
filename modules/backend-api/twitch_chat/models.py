"""Validated, session-scoped Twitch chat bindings."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")]
TwitchId = Annotated[str, Field(pattern=r"^[0-9]{1,32}$")]


class TwitchSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1]
    session_id: Identifier
    broadcaster_user_id: TwitchId
    user_id: TwitchId
    websocket_url: str = Field(pattern=r"^wss://eventsub\.wss\.twitch\.tv/ws(?:\?.*)?$")
    helix_url: str = Field(
        default="https://api.twitch.tv/helix", pattern=r"^https://api\.twitch\.tv/helix$"
    )
    reconnect_min_seconds: float = Field(default=1, ge=0.1, le=30)
    reconnect_max_seconds: float = Field(default=30, ge=1, le=300)


def load_settings(path: Path) -> TwitchSettings:
    return TwitchSettings.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
