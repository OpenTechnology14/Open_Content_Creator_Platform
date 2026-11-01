"""Small async OBS WebSocket v5 transport; serialized requests, no action retries."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import uuid


def authentication(password: str, salt: str, challenge: str) -> str:
    """OBS v5's documented challenge-response calculation."""
    secret = base64.b64encode(hashlib.sha256((password + salt).encode()).digest()).decode()
    return base64.b64encode(hashlib.sha256((secret + challenge).encode()).digest()).decode()


class ObsClient:
    def __init__(self, url: str, password: str, timeout: float) -> None:
        self.url, self.password, self.timeout = url, password, timeout
        self.socket = None
        self.lock = asyncio.Lock()

    async def _connect(self) -> None:
        from websockets.legacy.client import connect

        self.socket = await connect(
            self.url, open_timeout=self.timeout, close_timeout=1, max_size=1024 * 1024, max_queue=8
        )
        hello = json.loads(await self.socket.recv())
        if hello.get("op") != 0:
            raise ValueError("OBS did not send Hello")
        identify = {"rpcVersion": 1, "eventSubscriptions": 0}
        auth = hello["d"].get("authentication")
        if auth:
            identify["authentication"] = authentication(
                self.password, auth["salt"], auth["challenge"]
            )
        await self.socket.send(json.dumps({"op": 1, "d": identify}))
        response = json.loads(await self.socket.recv())
        if response.get("op") != 2:
            raise ValueError("OBS authentication/identification failed")

    async def _request(self, name: str, data: dict) -> dict:
        if self.socket is None:
            await self._connect()
        request_id = str(uuid.uuid4())
        await self.socket.send(
            json.dumps(
                {"op": 6, "d": {"requestType": name, "requestId": request_id, "requestData": data}}
            )
        )
        while True:
            message = json.loads(await self.socket.recv())
            if message.get("op") != 7 or message["d"].get("requestId") != request_id:
                continue
            result = message["d"]
            if not result["requestStatus"]["result"]:
                raise RuntimeError("OBS rejected request")
            return result.get("responseData", {})

    async def request(self, name: str, data: dict) -> dict:
        """Bound a request including handshake. Reset on uncertainty; never replay an action."""
        async with self.lock:
            try:
                return await asyncio.wait_for(self._request(name, data), timeout=self.timeout)
            except BaseException:
                await self.close()
                raise

    async def close(self) -> None:
        if self.socket is not None:
            socket, self.socket = self.socket, None
            await socket.close()
