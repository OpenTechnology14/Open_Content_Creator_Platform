"""
Source Health Exporter for Open Content Creator Platform.

Polls OBS sources, audio buses, virtual cameras, NodeCG, VTube Studio,
and TTS output — exposes Prometheus metrics on :9101/metrics and a
human-readable debug view on :9101/debug.
"""

import asyncio
import json
import logging
import os
import signal
import time
from contextlib import suppress
from dataclasses import dataclass, field
from enum import Enum
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Optional

import yaml

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("source-health")

# ---------------------------------------------------------------------------
# Metric registry (lightweight, no prometheus_client dependency required)
# ---------------------------------------------------------------------------

class MetricType(Enum):
    GAUGE = "gauge"


@dataclass
class Metric:
    name: str
    help: str
    type: MetricType = MetricType.GAUGE
    samples: dict = field(default_factory=dict)

    def set(self, value: float, labels: Optional[dict] = None):
        key = tuple(sorted((labels or {}).items()))
        self.samples[key] = value

    def remove(self, labels: Optional[dict] = None):
        key = tuple(sorted((labels or {}).items()))
        self.samples.pop(key, None)

    def clear(self):
        self.samples.clear()


class Registry:
    def __init__(self):
        self._metrics: dict[str, Metric] = {}

    def gauge(self, name: str, help_text: str) -> Metric:
        if name not in self._metrics:
            self._metrics[name] = Metric(name=name, help=help_text)
        return self._metrics[name]

    def render(self) -> str:
        lines = []
        for m in self._metrics.values():
            if not m.samples:
                continue
            lines.append(f"# HELP {m.name} {m.help}")
            lines.append(f"# TYPE {m.name} {m.type.value}")
            for labels, value in m.samples.items():
                if labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in labels)
                    lines.append(f"{m.name}{{{label_str}}} {value}")
                else:
                    lines.append(f"{m.name} {value}")
        return "\n".join(lines) + "\n"


registry = Registry()

# ---------------------------------------------------------------------------
# Metrics definitions
# ---------------------------------------------------------------------------

SOURCE_UP = registry.gauge(
    "hcp_source_up",
    "1 if the source connection is healthy, 0 if down",
)
SOURCE_LATENCY = registry.gauge(
    "hcp_source_latency_ms",
    "Round-trip latency to the source in milliseconds",
)
OBS_SOURCE_ACTIVE = registry.gauge(
    "hcp_obs_source_active",
    "1 if the OBS source is active and visible",
)
OBS_SOURCE_WIDTH = registry.gauge(
    "hcp_obs_source_width",
    "Width in pixels of the OBS source",
)
OBS_SOURCE_HEIGHT = registry.gauge(
    "hcp_obs_source_height",
    "Height in pixels of the OBS source",
)
OBS_DROPPED_FRAMES_PCT = registry.gauge(
    "hcp_obs_dropped_frames_pct",
    "OBS dropped frames as a percentage",
)
OBS_STREAM_ACTIVE = registry.gauge(
    "hcp_obs_stream_active",
    "1 if OBS is currently streaming",
)
OBS_RECORDING_ACTIVE = registry.gauge(
    "hcp_obs_recording_active",
    "1 if OBS is currently recording",
)
AUDIO_BUS_LEVEL_DB = registry.gauge(
    "hcp_audio_bus_level_db",
    "Current audio level in dB for a bus",
)
AUDIO_BUS_SILENT = registry.gauge(
    "hcp_audio_bus_silent",
    "1 if the audio bus has been below silence threshold",
)
VCAM_FPS = registry.gauge(
    "hcp_virtual_camera_fps",
    "Measured FPS of a virtual camera device",
)
VCAM_BLACK_FRAMES = registry.gauge(
    "hcp_virtual_camera_black_frames",
    "1 if the virtual camera is outputting black/frozen frames",
)
NODECG_BUNDLE_LOADED = registry.gauge(
    "hcp_nodecg_bundle_loaded",
    "1 if a NodeCG bundle is loaded and responding",
)
NODECG_REPLICANT_AGE_S = registry.gauge(
    "hcp_nodecg_replicant_age_seconds",
    "Seconds since a replicant was last updated",
)
TTS_LAST_OUTPUT_AGO_S = registry.gauge(
    "hcp_tts_last_output_seconds_ago",
    "Seconds since the last TTS audio was produced",
)
AGENT_LAST_REPLY_AGO_S = registry.gauge(
    "hcp_agent_last_reply_seconds_ago",
    "Seconds since the AI agent last replied",
)

# ---------------------------------------------------------------------------
# Debug state (shared across collectors for /debug endpoint)
# ---------------------------------------------------------------------------

debug_state: dict = {}


def update_debug(source: str, data: dict):
    debug_state[source] = {
        "last_check": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **data,
    }


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------

class OBSCollector:
    """Polls OBS via obs-websocket 5.x."""

    def __init__(self, host: str = "localhost", port: int = 4455, password: str = ""):
        self.url = f"ws://{host}:{port}"
        self.password = password
        self._ws = None

    async def collect(self):
        try:
            import obsws_python as obsws
        except ImportError:
            SOURCE_UP.set(0, {"source": "obs", "type": "websocket"})
            update_debug("obs", {"status": "error", "detail": "obsws_python not installed"})
            return

        t0 = time.monotonic()
        try:
            cl = obsws.ReqClient(
                host=self.url.split("://")[1].split(":")[0],
                port=int(self.url.split(":")[-1]),
                password=self.password,
                timeout=5,
            )
            latency = (time.monotonic() - t0) * 1000
            SOURCE_UP.set(1, {"source": "obs", "type": "websocket"})
            SOURCE_LATENCY.set(round(latency, 1), {"source": "obs"})

            # Stream / recording status
            stream_status = cl.get_stream_status()
            OBS_STREAM_ACTIVE.set(1 if stream_status.output_active else 0)

            record_status = cl.get_record_status()
            OBS_RECORDING_ACTIVE.set(1 if record_status.output_active else 0)

            # Dropped frames
            stats = cl.get_stats()
            if hasattr(stats, "output_skipped_frames") and hasattr(stats, "output_total_frames"):
                total = stats.output_total_frames
                if total > 0:
                    pct = (stats.output_skipped_frames / total) * 100
                    OBS_DROPPED_FRAMES_PCT.set(round(pct, 2))

            # Per-source status
            scene = cl.get_current_program_scene()
            scene_name = scene.scene_name if hasattr(scene, "scene_name") else scene.current_program_scene_name
            items = cl.get_scene_item_list(scene_name)
            sources_debug = []
            for item in items.scene_items:
                name = item.get("sourceName", item.get("source_name", "unknown"))
                enabled = item.get("sceneItemEnabled", True)
                OBS_SOURCE_ACTIVE.set(1 if enabled else 0, {"name": name, "scene": scene_name})
                source_info = {"name": name, "enabled": enabled}
                with suppress(Exception):
                    width = item.get("sourceWidth", 0)
                    height = item.get("sourceHeight", 0)
                    if width:
                        OBS_SOURCE_WIDTH.set(width, {"name": name})
                        OBS_SOURCE_HEIGHT.set(height, {"name": name})
                        source_info["resolution"] = f"{width}x{height}"
                sources_debug.append(source_info)

            cl.disconnect()
            update_debug("obs", {
                "status": "connected",
                "latency_ms": round(latency, 1),
                "streaming": stream_status.output_active,
                "recording": record_status.output_active,
                "scene": scene_name,
                "sources": sources_debug,
            })

        except Exception as e:
            SOURCE_UP.set(0, {"source": "obs", "type": "websocket"})
            SOURCE_LATENCY.set(-1, {"source": "obs"})
            update_debug("obs", {"status": "down", "error": str(e)})
            log.warning("OBS collector failed: %s", e)


class VoiceMeeterCollector:
    """Polls VoiceMeeter via the Remote API (Windows only)."""

    BUSES = {
        "MIC": {"strip": 0},
        "GAME": {"strip": 1},
        "MUSIC": {"strip": 2},
        "AI_VOICE": {"strip": 3},
        "CALL_IN": {"strip": 4},
    }
    SILENCE_THRESHOLD_DB = -60

    def __init__(self, bus_map: Optional[dict] = None):
        if bus_map:
            self.BUSES = bus_map

    async def collect(self):
        try:
            import voicemeeterlib
        except ImportError:
            SOURCE_UP.set(0, {"source": "voicemeeter", "type": "remote_api"})
            update_debug("voicemeeter", {"status": "error", "detail": "voicemeeterlib not installed (Windows only)"})
            return

        t0 = time.monotonic()
        try:
            with voicemeeterlib.api("potato") as vm:
                latency = (time.monotonic() - t0) * 1000
                SOURCE_UP.set(1, {"source": "voicemeeter", "type": "remote_api"})
                SOURCE_LATENCY.set(round(latency, 1), {"source": "voicemeeter"})

                bus_debug = {}
                for bus_name, cfg in self.BUSES.items():
                    strip_idx = cfg["strip"]
                    try:
                        levels = vm.strip[strip_idx].levels.prefader
                        level_db = max(levels) if levels else -120
                        AUDIO_BUS_LEVEL_DB.set(round(level_db, 1), {"bus": bus_name})
                        is_silent = 1 if level_db < self.SILENCE_THRESHOLD_DB else 0
                        AUDIO_BUS_SILENT.set(is_silent, {"bus": bus_name})
                        bus_debug[bus_name] = {
                            "level_db": round(level_db, 1),
                            "silent": bool(is_silent),
                            "mute": vm.strip[strip_idx].mute,
                        }
                    except Exception as be:
                        bus_debug[bus_name] = {"error": str(be)}

                update_debug("voicemeeter", {
                    "status": "connected",
                    "latency_ms": round(latency, 1),
                    "buses": bus_debug,
                })

        except Exception as e:
            SOURCE_UP.set(0, {"source": "voicemeeter", "type": "remote_api"})
            update_debug("voicemeeter", {"status": "down", "error": str(e)})
            log.warning("VoiceMeeter collector failed: %s", e)


class VirtualCameraCollector:
    """Checks virtual camera devices via OpenCV."""

    def __init__(self, devices: list[dict] | None = None):
        self.devices = devices or []

    async def collect(self):
        try:
            import cv2
            import numpy as np
        except ImportError:
            for dev in self.devices:
                name = dev.get("name", "unknown")
                SOURCE_UP.set(0, {"source": name, "type": "virtual_camera"})
            update_debug("virtual_cameras", {"status": "error", "detail": "opencv-python not installed"})
            return

        cams_debug = {}
        for dev in self.devices:
            name = dev.get("name", "unknown")
            device_id = dev.get("device_id", 0)

            t0 = time.monotonic()
            try:
                cap = cv2.VideoCapture(device_id)
                if not cap.isOpened():
                    SOURCE_UP.set(0, {"source": name, "type": "virtual_camera"})
                    VCAM_FPS.set(0, {"device": name})
                    cams_debug[name] = {"status": "not_found", "device_id": device_id}
                    continue

                fps = cap.get(cv2.CAP_PROP_FPS) or 0
                frames_ok = 0
                black_count = 0
                sample_count = 3

                for _ in range(sample_count):
                    ret, frame = cap.read()
                    if ret:
                        frames_ok += 1
                        if np.mean(frame) < 5:
                            black_count += 1

                cap.release()
                latency = (time.monotonic() - t0) * 1000

                if frames_ok == 0:
                    SOURCE_UP.set(0, {"source": name, "type": "virtual_camera"})
                    VCAM_FPS.set(0, {"device": name})
                    VCAM_BLACK_FRAMES.set(1, {"device": name})
                    cams_debug[name] = {"status": "no_frames"}
                else:
                    SOURCE_UP.set(1, {"source": name, "type": "virtual_camera"})
                    VCAM_FPS.set(round(fps, 1), {"device": name})
                    is_black = 1 if black_count == frames_ok else 0
                    VCAM_BLACK_FRAMES.set(is_black, {"device": name})
                    SOURCE_LATENCY.set(round(latency, 1), {"source": name})
                    cams_debug[name] = {
                        "status": "ok",
                        "fps": round(fps, 1),
                        "black_frames": bool(is_black),
                        "latency_ms": round(latency, 1),
                    }

            except Exception as e:
                SOURCE_UP.set(0, {"source": name, "type": "virtual_camera"})
                cams_debug[name] = {"status": "error", "error": str(e)}
                log.warning("Virtual camera %s failed: %s", name, e)

        update_debug("virtual_cameras", {"cameras": cams_debug})


class NodeCGCollector:
    """Checks NodeCG WebSocket and bundle health."""

    def __init__(self, host: str = "localhost", port: int = 9091):
        self.base_url = f"http://{host}:{port}"

    async def collect(self):
        try:
            import aiohttp
        except ImportError:
            SOURCE_UP.set(0, {"source": "nodecg", "type": "http"})
            update_debug("nodecg", {"status": "error", "detail": "aiohttp not installed"})
            return

        t0 = time.monotonic()
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/api/v1/bundles") as resp:
                    latency = (time.monotonic() - t0) * 1000
                    if resp.status == 200:
                        bundles = await resp.json()
                        SOURCE_UP.set(1, {"source": "nodecg", "type": "http"})
                        SOURCE_LATENCY.set(round(latency, 1), {"source": "nodecg"})

                        bundle_names = []
                        for b in bundles:
                            bname = b if isinstance(b, str) else b.get("name", "unknown")
                            NODECG_BUNDLE_LOADED.set(1, {"bundle": bname})
                            bundle_names.append(bname)

                        update_debug("nodecg", {
                            "status": "connected",
                            "latency_ms": round(latency, 1),
                            "bundles": bundle_names,
                        })
                    else:
                        SOURCE_UP.set(0, {"source": "nodecg", "type": "http"})
                        update_debug("nodecg", {"status": "http_error", "code": resp.status})

        except Exception as e:
            SOURCE_UP.set(0, {"source": "nodecg", "type": "http"})
            update_debug("nodecg", {"status": "down", "error": str(e)})
            log.warning("NodeCG collector failed: %s", e)


class VTubeStudioCollector:
    """Checks VTube Studio WebSocket API."""

    def __init__(self, host: str = "localhost", port: int = 8001):
        self.url = f"ws://{host}:{port}"

    async def collect(self):
        try:
            import websockets
        except ImportError:
            SOURCE_UP.set(0, {"source": "vtube_studio", "type": "websocket"})
            update_debug("vtube_studio", {"status": "error", "detail": "websockets not installed"})
            return

        t0 = time.monotonic()
        try:
            async with websockets.connect(self.url, close_timeout=3, open_timeout=5) as ws:
                request = {
                    "apiName": "VTubeStudioPublicAPI",
                    "apiVersion": "1.0",
                    "requestID": "health-check",
                    "messageType": "APIStateRequest",
                }
                await ws.send(json.dumps(request))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                latency = (time.monotonic() - t0) * 1000
                data = json.loads(raw)

                SOURCE_UP.set(1, {"source": "vtube_studio", "type": "websocket"})
                SOURCE_LATENCY.set(round(latency, 1), {"source": "vtube_studio"})

                api_data = data.get("data", {})
                update_debug("vtube_studio", {
                    "status": "connected",
                    "latency_ms": round(latency, 1),
                    "active": api_data.get("active", False),
                    "vts_version": api_data.get("vTubeStudioVersion", "unknown"),
                    "current_model": api_data.get("currentModelID", "none"),
                })

        except Exception as e:
            SOURCE_UP.set(0, {"source": "vtube_studio", "type": "websocket"})
            update_debug("vtube_studio", {"status": "down", "error": str(e)})
            log.warning("VTube Studio collector failed: %s", e)


class TTSAgentCollector:
    """Monitors TTS and AI agent activity via Redis pub/sub timestamps."""

    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self._last_tts_time: float = 0
        self._last_agent_reply_time: float = 0
        self._listener_started = False

    async def start_listener(self):
        """Background task that subscribes to Redis channels and records timestamps."""
        if self._listener_started:
            return
        self._listener_started = True

        try:
            import redis.asyncio as aioredis
        except ImportError:
            log.warning("redis[async] not installed — TTS/agent monitoring disabled")
            return

        async def _listen():
            try:
                r = aioredis.Redis(host=self.redis_host, port=self.redis_port)
                pubsub = r.pubsub()
                await pubsub.subscribe("tts.say", "agent.reply")
                async for msg in pubsub.listen():
                    if msg["type"] == "message":
                        channel = msg["channel"]
                        if isinstance(channel, bytes):
                            channel = channel.decode()
                        now = time.time()
                        if channel == "tts.say":
                            self._last_tts_time = now
                        elif channel == "agent.reply":
                            self._last_agent_reply_time = now
            except Exception as e:
                log.warning("Redis listener failed: %s", e)
                self._listener_started = False

        asyncio.get_event_loop().create_task(_listen())

    async def collect(self):
        try:
            import redis as sync_redis
        except ImportError:
            SOURCE_UP.set(0, {"source": "redis_tts", "type": "pubsub"})
            update_debug("tts_agent", {"status": "error", "detail": "redis not installed"})
            return

        t0 = time.monotonic()
        try:
            r = sync_redis.Redis(
                host=self.redis_host, port=self.redis_port,
                socket_connect_timeout=3, socket_timeout=3,
            )
            r.ping()
            latency = (time.monotonic() - t0) * 1000
            SOURCE_UP.set(1, {"source": "redis_tts", "type": "pubsub"})
            SOURCE_LATENCY.set(round(latency, 1), {"source": "redis_tts"})

            await self.start_listener()

            now = time.time()
            tts_ago = round(now - self._last_tts_time, 1) if self._last_tts_time else -1
            agent_ago = round(now - self._last_agent_reply_time, 1) if self._last_agent_reply_time else -1

            if self._last_tts_time:
                TTS_LAST_OUTPUT_AGO_S.set(tts_ago)
            if self._last_agent_reply_time:
                AGENT_LAST_REPLY_AGO_S.set(agent_ago)

            update_debug("tts_agent", {
                "status": "connected",
                "redis_latency_ms": round(latency, 1),
                "tts_last_output_seconds_ago": tts_ago if tts_ago >= 0 else "never",
                "agent_last_reply_seconds_ago": agent_ago if agent_ago >= 0 else "never",
            })

        except Exception as e:
            SOURCE_UP.set(0, {"source": "redis_tts", "type": "pubsub"})
            update_debug("tts_agent", {"status": "down", "error": str(e)})
            log.warning("TTS/Agent collector failed: %s", e)


class DeepFaceLiveCollector:
    """Monitors DeepFaceLive process and its virtual camera output."""

    def __init__(self, process_name: str = "DeepFaceLive"):
        self.process_name = process_name

    async def collect(self):
        try:
            import psutil
        except ImportError:
            SOURCE_UP.set(0, {"source": "deepfacelive", "type": "process"})
            update_debug("deepfacelive", {"status": "error", "detail": "psutil not installed"})
            return

        found = False
        pid = None
        cpu = None
        mem_mb = None

        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
            try:
                if self.process_name.lower() in proc.info["name"].lower():
                    found = True
                    pid = proc.info["pid"]
                    cpu = proc.info["cpu_percent"]
                    mem_mb = round(proc.info["memory_info"].rss / 1024 / 1024, 1)
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if found:
            SOURCE_UP.set(1, {"source": "deepfacelive", "type": "process"})
            update_debug("deepfacelive", {
                "status": "running",
                "pid": pid,
                "cpu_percent": cpu,
                "memory_mb": mem_mb,
            })
        else:
            SOURCE_UP.set(0, {"source": "deepfacelive", "type": "process"})
            update_debug("deepfacelive", {"status": "not_running"})


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(path: str = "config.yml") -> dict:
    if os.path.exists(path):
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


# ---------------------------------------------------------------------------
# HTTP server (metrics + debug endpoints)
# ---------------------------------------------------------------------------

class ExporterHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            body = registry.render().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/debug":
            body = json.dumps(debug_state, indent=2, default=str).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/health":
            sources_up = sum(
                1 for (labels, val) in SOURCE_UP.samples.items()
                if val == 1
            )
            sources_total = len(SOURCE_UP.samples)
            status = "healthy" if sources_up == sources_total else "degraded"
            if sources_total == 0:
                status = "no_sources"

            body = json.dumps({
                "status": status,
                "sources_up": sources_up,
                "sources_total": sources_total,
            }).encode()
            self.send_response(200 if status == "healthy" else 503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress default access logs


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def run_collectors(collectors: list, interval: float):
    while True:
        tasks = [c.collect() for c in collectors]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(interval)


def main():
    config = load_config(
        os.getenv("CONFIG_PATH", os.path.join(os.path.dirname(__file__), "config.yml"))
    )

    port = int(config.get("port", os.getenv("EXPORTER_PORT", 9101)))
    interval = float(config.get("interval_seconds", 15))

    obs_cfg = config.get("obs", {})
    vm_cfg = config.get("voicemeeter", {})
    vcam_cfg = config.get("virtual_cameras", [])
    nodecg_cfg = config.get("nodecg", {})
    vts_cfg = config.get("vtube_studio", {})
    tts_cfg = config.get("tts_agent", {})
    dfl_cfg = config.get("deepfacelive", {})

    collectors = []

    if obs_cfg.get("enabled", True):
        collectors.append(OBSCollector(
            host=obs_cfg.get("host", "localhost"),
            port=obs_cfg.get("port", 4455),
            password=obs_cfg.get("password", os.getenv("OBS_WEBSOCKET_PASSWORD", "")),
        ))

    if vm_cfg.get("enabled", True):
        collectors.append(VoiceMeeterCollector(bus_map=vm_cfg.get("buses")))

    if vcam_cfg:
        collectors.append(VirtualCameraCollector(devices=vcam_cfg))

    if nodecg_cfg.get("enabled", True):
        collectors.append(NodeCGCollector(
            host=nodecg_cfg.get("host", "localhost"),
            port=nodecg_cfg.get("port", 9091),
        ))

    if vts_cfg.get("enabled", True):
        collectors.append(VTubeStudioCollector(
            host=vts_cfg.get("host", "localhost"),
            port=vts_cfg.get("port", 8001),
        ))

    if tts_cfg.get("enabled", True):
        collectors.append(TTSAgentCollector(
            redis_host=tts_cfg.get("redis_host", os.getenv("REDIS_HOST", "localhost")),
            redis_port=int(tts_cfg.get("redis_port", os.getenv("REDIS_PORT", 6379))),
        ))

    if dfl_cfg.get("enabled", True):
        collectors.append(DeepFaceLiveCollector(
            process_name=dfl_cfg.get("process_name", "DeepFaceLive"),
        ))

    log.info("Starting source-health-exporter on :%d (interval=%ds, collectors=%d)",
             port, interval, len(collectors))

    server = HTTPServer(("0.0.0.0", port), ExporterHandler)
    Thread(target=server.serve_forever, daemon=True).start()

    loop = asyncio.new_event_loop()

    def shutdown(*_):
        log.info("Shutting down")
        server.shutdown()
        loop.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    loop.run_until_complete(run_collectors(collectors, interval))


if __name__ == "__main__":
    main()
