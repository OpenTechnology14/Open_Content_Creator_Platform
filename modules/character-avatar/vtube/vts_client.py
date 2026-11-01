"""Minimal VTube Studio API client.

VTS exposes a JSON WebSocket on ws://127.0.0.1:8001 (default). This client
authenticates with a plugin token and exposes a handful of useful methods:
trigger hotkeys, set parameter values, list models.

Docs: https://github.com/DenchiSoft/VTubeStudio
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass

import websockets
from loguru import logger


@dataclass
class VTSConfig:
    url: str = "ws://127.0.0.1:8001"
    plugin_name: str = "HCP-Bridge"
    plugin_developer: str = "Open Content Creator Platform"
    allow_token_request: bool = True
    token_path: str = os.path.expanduser("~/.hcp/vts_token")


class VTSClient:
    def __init__(self, config: VTSConfig | None = None) -> None:
        self.config = config or VTSConfig()
        self.ws: websockets.WebSocketClientProtocol | None = None
        self.token: str | None = None

    async def connect(self) -> None:
        self.ws = await websockets.connect(
            self.config.url, max_size=65536, open_timeout=3, close_timeout=1
        )
        if os.path.exists(self.config.token_path):
            with open(self.config.token_path) as f:
                self.token = f.read().strip()
        else:
            if not self.config.allow_token_request:
                raise RuntimeError("existing VTS authorization required")
            self.token = await self._request_token()
            os.makedirs(os.path.dirname(self.config.token_path), exist_ok=True)
            fd = os.open(self.config.token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(self.token)
        await self._authenticate()

    async def close(self) -> None:
        if self.ws is not None:
            await self.ws.close()

    async def _send(self, message_type: str, data: dict | None = None) -> dict:
        assert self.ws is not None
        payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": str(uuid.uuid4()),
            "messageType": message_type,
            "data": data or {},
        }
        await self.ws.send(json.dumps(payload))
        response = json.loads(await asyncio.wait_for(self.ws.recv(), 3))
        if response.get("requestID") != payload["requestID"]:
            raise RuntimeError("VTS reply does not match the requested operation")
        return response

    async def _request_token(self) -> str:
        logger.info("requesting VTS auth token — accept the popup in VTube Studio")
        r = await self._send(
            "AuthenticationTokenRequest",
            {
                "pluginName": self.config.plugin_name,
                "pluginDeveloper": self.config.plugin_developer,
            },
        )
        return r["data"]["authenticationToken"]

    async def _authenticate(self) -> None:
        r = await self._send(
            "AuthenticationRequest",
            {
                "pluginName": self.config.plugin_name,
                "pluginDeveloper": self.config.plugin_developer,
                "authenticationToken": self.token,
            },
        )
        if not r["data"]["authenticated"]:
            raise RuntimeError(f"VTS auth failed: {r['data'].get('reason')}")
        logger.info("VTS authenticated")

    async def trigger_hotkey(self, hotkey_id: str) -> dict:
        return await self._send("HotkeyTriggerRequest", {"hotkeyID": hotkey_id})

    async def set_parameter(self, name: str, value: float, weight: float = 1.0) -> dict:
        return await self._send(
            "InjectParameterDataRequest",
            {"parameterValues": [{"id": name, "value": value, "weight": weight}]},
        )

    async def get_current_model(self) -> dict:
        return await self._send("CurrentModelRequest")


async def _demo() -> None:
    """Run with: python vts_client.py"""
    client = VTSClient()
    await client.connect()
    model = await client.get_current_model()
    print(json.dumps(model, indent=2))
    await client.close()


if __name__ == "__main__":
    asyncio.run(_demo())
