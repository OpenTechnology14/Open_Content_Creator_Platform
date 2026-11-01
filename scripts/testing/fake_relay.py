#!/usr/bin/env python3
"""Loopback-only relay used for desktop remote-control acceptance tests."""

from __future__ import annotations

import argparse
import asyncio
import json
from http import HTTPStatus

import websockets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--token", default="local-test-token")
    return parser.parse_args()


async def run(port: int, token: str) -> None:
    clients: set[websockets.WebSocketServerProtocol] = set()

    async def health(path: str, _headers):
        if path.endswith("/api/v1/health"):
            return HTTPStatus.OK, [("Content-Type", "application/json")], b'{"status":"ok","service":"fake-relay"}'
        return None

    async def relay(socket: websockets.WebSocketServerProtocol) -> None:
        raw = await asyncio.wait_for(socket.recv(), timeout=5)
        message = json.loads(raw)
        supplied = message.get("Auth", {}).get("jwt")
        if supplied != token:
            await socket.send(json.dumps({"AuthError": {"reason": "Invalid local test token"}}))
            return
        await socket.send(json.dumps({"AuthOk": {"subscription": {
            "tier": "connect", "active": True, "tenant_id": "local-test", "expires_at": None,
        }}}))
        clients.add(socket)
        try:
            try:
                async for raw in socket:
                    message = json.loads(raw)
                    if message == "Ping" or "Ping" in message:
                        await socket.send(json.dumps("Pong"))
                        continue
                    peers = [client for client in clients if client is not socket]
                    await asyncio.gather(*(peer.send(raw) for peer in peers))
            except websockets.ConnectionClosed:
                pass
        finally:
            clients.discard(socket)

    async with websockets.serve(relay, "127.0.0.1", port, process_request=health):
        print(f"Fake relay ready at http://127.0.0.1:{port}", flush=True)
        await asyncio.Future()


if __name__ == "__main__":
    arguments = parse_args()
    asyncio.run(run(arguments.port, arguments.token))
