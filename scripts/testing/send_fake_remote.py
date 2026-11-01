#!/usr/bin/env python3
"""Send one allowlisted request through the loopback relay test harness."""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid

import websockets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="ws://127.0.0.1:8765/ws")
    parser.add_argument("--token", default="local-test-token")
    parser.add_argument("--target-device", required=True)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--scene")
    actions.add_argument("--toggle-stream", action="store_true")
    actions.add_argument("--workflow")
    return parser.parse_args()


async def send(arguments: argparse.Namespace) -> None:
    if arguments.scene:
        target, action, payload = "obs", "switch_scene", {"scene": arguments.scene}
    elif arguments.toggle_stream:
        target, action, payload = "obs", "toggle_stream", {}
    else:
        target, action, payload = "comfyui", "queue_workflow", {"workflow_path": arguments.workflow}
    request_id = str(uuid.uuid4())
    async with websockets.connect(arguments.url) as socket:
        await socket.send(json.dumps({"Auth": {"jwt": arguments.token}}))
        response = json.loads(await socket.recv())
        if "AuthOk" not in response:
            raise RuntimeError(f"Relay authentication failed: {response}")
        await socket.send(json.dumps({"Command": {
            "id": request_id,
            "source_device_id": "loopback-controller",
            "target_device_id": arguments.target_device,
            "target": target,
            "action": action,
            "payload": payload,
        }}))
        print(f"Sent {request_id}; waiting for local approval", flush=True)
        while True:
            response = json.loads(await socket.recv())
            if "CommandResult" in response and response["CommandResult"].get("id") == request_id:
                print(json.dumps(response, sort_keys=True), flush=True)
                return


if __name__ == "__main__":
    asyncio.run(send(parse_args()))
