"""Preview or apply configured stream integrations. No stream start, purchases or game inputs."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx
from loguru import logger
from pydantic import ValidationError

from .config import HostOutput, load_settings
from .director import Director
from .obs import ObsClient

ROOT = Path(__file__).resolve().parents[3]
TOPICS = {"events.stream-host.reply", "events.stream-host.control"}


async def output(data: dict) -> None:
    sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
    sys.stdout.flush()


class Integrations:
    def __init__(
        self, obs: ObsClient, http: httpx.AsyncClient, base: str, key: str, apply: bool, emit=output
    ) -> None:
        self.obs, self.http, self.base, self.key = obs, http, base, key
        self.apply, self.emit = apply, emit
        self.overlay_written = False
        self.failures = 0

    async def execute(self, kind: str, data: dict) -> str:
        if kind == "soundboard.available":
            if not self.apply:
                return "unavailable"
            available = await self.obs.request("GetHotkeyList", {})
            return "available" if data["hotkeyName"] in available.get("hotkeys", []) else "unbound"
        if not self.apply:
            await self.emit({"kind": "preview", "action": kind, "data": data})
            return "preview"
        if kind == "graphics.lower_third":
            response = await self.http.put(
                self.base + "/overlays/lowerThird",
                headers={"X-API-Key": self.key},
                json={"name": "lowerThird", "payload": data},
            )
            response.raise_for_status()
            self.overlay_written = True
        elif kind in {"soundboard.play", "soundboard.stop"}:
            available = await self.obs.request("GetHotkeyList", {})
            if data["hotkeyName"] not in available.get("hotkeys", []):
                raise ValueError("configured soundboard hotkey is not registered in OBS")
            await self.obs.request("TriggerHotkeyByName", data)
        elif kind == "audio.mute":
            await self.obs.request("SetInputMute", data)
        elif kind == "obs.scene":
            await self.obs.request("SetCurrentProgramScene", data)
        elif kind == "automation.trigger":
            response = await self.http.post(
                self.base + "/automation/trigger", headers={"X-API-Key": self.key}, json=data
            )
            response.raise_for_status()
            return "queued"
        elif kind == "speech.reply":
            response = await self.http.post(
                self.base + "/events", headers={"X-API-Key": self.key},
                json={"source": "stream-director", "kind": "reply", "data": data},
            )
            response.raise_for_status()
        else:
            raise ValueError("unsupported director action")
        return "acknowledged"

    async def report(self, event: dict) -> None:
        if event.get("status") == "failed":
            self.failures += 1
        await self.emit(event)
        if self.apply:
            try:
                response = await self.http.post(
                    self.base + "/events",
                    headers={"X-API-Key": self.key},
                    json={"source": "stream-director", "kind": "action_result", "data": event},
                )
                response.raise_for_status()
            except httpx.HTTPError:
                # A telemetry failure must not disable the next local mute/stop action.
                logger.warning("director audit delivery failed; result remains on stdout")


def backend_url() -> str:
    value = os.environ.get("AUTOPILOT_BACKEND_URL", "").rstrip("/")
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("set AUTOPILOT_BACKEND_URL to a credential-free HTTP(S) URL")
    return value


def obs_url() -> str:
    host = os.environ.get("OBS_WEBSOCKET_HOST", "")
    port = int(os.environ.get("OBS_WEBSOCKET_PORT", "4455"))
    if not host or any(c in host for c in "/?#@") or not 1 <= port <= 65535:
        raise ValueError("set valid OBS_WEBSOCKET_HOST and OBS_WEBSOCKET_PORT")
    return f"ws://{host}:{port}"


async def run(args: argparse.Namespace) -> None:
    settings = load_settings(args.config, ROOT / "modules/soundboard/sounds/manifest.yaml")
    if args.validate:
        await output(
            {
                "valid": True,
                "on_air_session": settings.on_air_session,
                "bound_sounds": list(settings.sound_hotkeys),
            }
        )
        return
    base = backend_url() if args.backend or args.apply else ""
    key = os.environ.get("HCP_API_KEY", "")
    if base and (not key or key in {"change-me", "change-me-to-a-long-random-string"}):
        raise ValueError("set HCP_API_KEY to the configured backend key")
    obs = ObsClient(
        obs_url() if args.apply or args.discover_obs else "",
        os.environ.get("OBS_WEBSOCKET_PASSWORD", ""),
        settings.request_timeout_seconds,
    )
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as http:
        integrations = Integrations(obs, http, base, key, args.apply)
        director = Director(settings, integrations.execute, integrations.report)
        try:
            if args.discover_obs:
                for request in ("GetHotkeyList", "GetSceneList", "GetInputList"):
                    await output({"request": request, "data": await obs.request(request, {})})
            elif args.input:
                with args.input.open(encoding="utf-8") as stream:
                    while True:
                        line = stream.readline(16385)
                        if not line:
                            break
                        if len(line) > 16384:
                            raise ValueError("host output exceeds 16 KiB")
                        record = json.loads(line)
                        if record.get("kind") in {"reply", "control"}:
                            await director.handle(HostOutput.model_validate(record))
            else:
                from websockets.legacy.client import connect

                parsed = urlsplit(base)
                url = urlunsplit(
                    (
                        "wss" if parsed.scheme == "https" else "ws",
                        parsed.netloc,
                        parsed.path + "/ws",
                        "topics=" + ",".join(sorted(TOPICS)),
                        "",
                    )
                )
                async with connect(
                    url,
                    extra_headers={"X-API-Key": key},
                    max_size=16384,
                    max_queue=8,
                    open_timeout=5,
                    close_timeout=1,
                ) as socket:
                    async for message in socket:
                        try:
                            envelope = json.loads(message)
                            if envelope.get("channel") not in TOPICS:
                                continue
                            event = HostOutput.model_validate(envelope["data"]["data"])
                            if envelope["channel"] != "events.stream-host." + event.kind:
                                continue
                        except (ValidationError, ValueError, KeyError, TypeError, AttributeError):
                            logger.warning("director ignored malformed host envelope")
                            continue
                        await director.handle(event)
        finally:
            await director.close()
            if args.apply and integrations.overlay_written:
                await director._action("graphics.lower_third", {"visible": False})
            await obs.close()
        if args.input and integrations.failures:
            raise RuntimeError("one or more module actions failed")


def main() -> int:
    from websockets.exceptions import WebSocketException

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/local/stream-director.yaml")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate", action="store_true")
    mode.add_argument("--discover-obs", action="store_true", help="read OBS hotkeys/scenes/inputs")
    mode.add_argument("--input", type=Path, help="fresh host JSONL output")
    mode.add_argument("--backend", action="store_true", help="consume live backend host events")
    parser.add_argument(
        "--apply", action="store_true", help="perform configured actions; default is preview"
    )
    args = parser.parse_args()
    if args.apply and (args.validate or args.discover_obs):
        parser.error("--apply is only valid with --input or --backend")
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, RuntimeError, httpx.HTTPError, WebSocketException) as exc:
        logger.error(
            "director stopped: {}; check bindings and service configuration", type(exc).__name__
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
