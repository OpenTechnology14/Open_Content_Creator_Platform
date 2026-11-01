"""VTube Studio adapter using operator-configured hotkey IDs."""

from __future__ import annotations

from vtube.vts_client import VTSClient, VTSConfig

from .models import AvatarSettings


class VtsAvatarAdapter:
    def __init__(self, settings: AvatarSettings, allow_token_request: bool = True) -> None:
        self.settings = settings
        self.client = VTSClient(
            VTSConfig(url=settings.vts_url, allow_token_request=allow_token_request)
        )

    async def connect(self) -> None:
        await self.client.connect()

    async def _bound_model(self, avatar_id: str) -> None:
        binding = self.settings.avatars[avatar_id]
        if binding.vts_model_id:
            current = await self.client.get_current_model()
            if (
                not current.get("data", {}).get("modelLoaded")
                or current.get("data", {}).get("modelID") != binding.vts_model_id
            ):
                raise RuntimeError("configured avatar model is not loaded")

    async def cue(self, avatar_id: str, cue: str) -> None:
        if not self.settings.full_body_enabled:
            raise ValueError("body cues are disabled")
        await self._bound_model(avatar_id)
        hotkey = self.settings.avatars[avatar_id].cues[cue]
        inventory = await self.client._send("HotkeysInCurrentModelRequest")
        item = next(
            (
                item
                for item in inventory.get("data", {}).get("availableHotkeys", [])
                if item.get("hotkeyID") == hotkey
            ),
            None,
        )
        if not item or item.get("type") not in {"TriggerAnimation", "ToggleExpression"}:
            raise RuntimeError("body cue is not an owned animation/expression hotkey")
        result = await self.client.trigger_hotkey(hotkey)
        if result.get("messageType") == "APIError":
            raise RuntimeError("configured body cue was rejected")

    async def _trigger(self, avatar_id: str, key: str) -> None:
        await self._bound_model(avatar_id)
        binding = self.settings.avatars[avatar_id]
        response = await self.client.trigger_hotkey(getattr(binding, key))
        if response.get("messageType") == "APIError":
            raise RuntimeError("VTube Studio rejected configured hotkey")

    async def talk(self, avatar_id: str) -> None:
        await self._trigger(avatar_id, "talk_hotkey")

    async def idle(self, avatar_id: str) -> None:
        await self._trigger(avatar_id, "idle_hotkey")
        if self.settings.full_body_enabled:
            await self.cue(avatar_id, "neutral")

    async def close(self) -> None:
        await self.client.close()
