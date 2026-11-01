"""Production lifecycle driver for the existing Stream Autopilot module workers."""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

import httpx
import yaml
from pydantic import BaseModel, ConfigDict, Field

from .models import CapabilityCheck, SessionPolicy

Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")]
ROOT = Path(__file__).resolve().parents[3]


class RuntimeSettings(BaseModel):
    """Operator-owned bindings; commands stay fixed in code and cannot execute viewer data."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    ollama_host: str | None = Field(default=None, max_length=2048)
    ollama_model: str | None = Field(default=None, min_length=1, max_length=200)
    schema_version: Literal[1]
    on_air_session: Identifier
    backend_url: str
    host_config: Path
    director_config: Path
    speech_config: Path
    avatar_config: Path
    twitch_config: Path
    gameplay_config: Path | None = None
    host_rehearsal: bool = False
    director_apply: bool = False
    avatar_enabled: bool = False
    twitch_enabled: bool = False
    control_broadcast: bool = False
    shutdown_timeout_seconds: float = Field(default=2, ge=0.1, le=10)

    def checked_backend_url(self) -> str:
        parsed = urlsplit(self.backend_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("backend_url must be a credential-free HTTP(S) URL")
        return self.backend_url.rstrip("/")


def load_runtime_settings(path: Path) -> RuntimeSettings:
    settings = RuntimeSettings.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    resolved: dict[str, Path | str] = {}
    for name in (
        "host_config",
        "director_config",
        "speech_config",
        "avatar_config",
        "twitch_config",
        "gameplay_config",
    ):
        value = getattr(settings, name)
        if value is None:
            continue
        if not value.is_absolute():
            value = (ROOT if value.parts and value.parts[0] == "configs" else path.parent) / value
        if not value.is_file():
            raise ValueError(f"{name} does not exist")
        resolved[name] = value
    if os.environ.get("AUTOPILOT_BACKEND_URL"):
        resolved["backend_url"] = os.environ["AUTOPILOT_BACKEND_URL"]
    settings = settings.model_copy(update=resolved)
    director = yaml.safe_load(settings.director_config.read_text())
    speech = yaml.safe_load(settings.speech_config.read_text())
    routed = director.get("phrase_manifest") is not None
    if routed != (speech.get("reply_source", "stream-host") == "stream-director"):
        raise ValueError("Phrase routing requires speech reply_source: stream-director")
    if routed and not settings.director_apply:
        raise ValueError("Phrase routing needs the applied director to deliver live speech")
    settings.checked_backend_url()
    return settings


class ProductionDriver:
    """Own worker process groups and translate lifecycle actions into bounded local effects."""

    def __init__(self, settings: RuntimeSettings) -> None:
        self.settings = settings
        self.processes: dict[str, asyncio.subprocess.Process] = {}
        self.broadcast_owned = False
        self.effects_owned = False
        self.host_bindings: dict = {}
        self.game = None
        self.avatar_effects_owned = False
        self.http = httpx.AsyncClient(timeout=httpx.Timeout(3, connect=2))
        from stream_director.phrases import load

        manifest = yaml.safe_load(settings.director_config.read_text()).get("phrase_manifest")
        path = Path(manifest) if manifest else None
        if path is not None and not path.is_absolute():
            path = settings.director_config.parent / path
        self.phrase_stop_hotkeys = sorted({p.stop_hotkey for p in load(path).values()})

    def _environment(self, module: str) -> dict[str, str]:
        env = os.environ.copy()
        module_path = str(ROOT / "modules" / module)
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            module_path if not existing else os.pathsep.join((module_path, existing))
        )
        env["AUTOPILOT_SESSION_ID"] = self.settings.on_air_session
        env["AUTOPILOT_BACKEND_URL"] = self.settings.checked_backend_url()
        if self.settings.ollama_host:
            env["OLLAMA_HOST"] = self.settings.ollama_host
        if self.settings.ollama_model:
            env["OLLAMA_MODEL"] = self.settings.ollama_model
        return env

    def _commands(self, *, validate: bool = False) -> dict[str, tuple[list[str], str]]:
        mode = "--validate" if validate else "--backend"
        host = [
            sys.executable,
            "-m",
            "stream_host",
            "--config",
            str(self.settings.host_config),
            mode,
        ]
        if self.settings.host_rehearsal and not validate:
            host.append("--rehearsal")
        director = [
            sys.executable,
            "-m",
            "stream_director",
            "--config",
            str(self.settings.director_config),
            mode,
        ]
        if self.settings.director_apply and not validate:
            director.append("--apply")
        commands = {
            "host": (host, "ai-agents"),
            "director": (director, "automation-control"),
            "speech": (
                [
                    sys.executable,
                    "-m",
                    "stream_speech",
                    "--config",
                    str(self.settings.speech_config),
                    mode,
                ],
                "audio-production",
            ),
        }
        if self.settings.avatar_enabled:
            commands["avatar"] = (
                [
                    sys.executable,
                    "-m",
                    "stream_avatar",
                    "--config",
                    str(self.settings.avatar_config),
                    mode,
                ],
                "character-avatar",
            )
        if self.settings.twitch_enabled:
            commands["twitch"] = (
                [
                    sys.executable,
                    "-m",
                    "twitch_chat",
                    "--config",
                    str(self.settings.twitch_config),
                    *(["--validate"] if validate else []),
                ],
                "backend-api",
            )
        return commands

    async def _validate_component(
        self, name: str, command: list[str], module: str
    ) -> CapabilityCheck:
        process = await asyncio.create_subprocess_exec(
            *command,
            env=self._environment(module),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), 10)
        except asyncio.CancelledError:
            process.kill()
            await process.wait()
            raise
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return CapabilityCheck(id=name, status="missing", detail="validation timed out")
        try:
            report = yaml.safe_load(stdout)
        except yaml.YAMLError:
            report = None
        if name == "host" and isinstance(report, dict):
            self.host_bindings = report.get("bindings", {}).get(self.settings.on_air_session, {})
        valid = process.returncode == 0 and isinstance(report, dict) and report.get("valid") is True
        return CapabilityCheck(
            id=name,
            status="ready" if valid else "missing",
            detail="configuration and local dependency validated" if valid else "validation failed",
        )

    async def preflight(self, session_id: str, policy: SessionPolicy) -> list[CapabilityCheck]:
        checks: list[CapabilityCheck] = []
        checks.append(
            CapabilityCheck(
                id="on-air-session",
                status="ready" if session_id == self.settings.on_air_session else "missing",
                detail=(
                    "selected session owns the shared local output"
                    if session_id == self.settings.on_air_session
                    else f"runtime is bound to {self.settings.on_air_session}"
                ),
            )
        )
        key = os.environ.get("HCP_API_KEY", "")
        key_ready = bool(key and key not in {"change-me", "change-me-to-a-long-random-string"})
        checks.append(
            CapabilityCheck(
                id="backend-auth",
                status="ready" if key_ready else "missing",
                detail="backend API key is configured" if key_ready else "set HCP_API_KEY",
            )
        )
        if key_ready:
            try:
                response = await self.http.get(self.settings.checked_backend_url() + "/ready")
                ready = response.status_code == 200 and response.json().get("status") == "ok"
            except (httpx.HTTPError, ValueError):
                ready = False
            checks.append(
                CapabilityCheck(
                    id="backend",
                    status="ready" if ready else "missing",
                    detail="backend datastore and event bus are ready"
                    if ready
                    else "backend is unavailable",
                )
            )
        if self.settings.avatar_enabled:
            token = Path.home() / ".hcp" / "vts_token"
            checks.append(
                CapabilityCheck(
                    id="avatar-authorization",
                    status="ready" if token.is_file() and token.stat().st_size > 0 else "missing",
                    detail="existing VTS plugin authorization required; accept it through the manual avatar setup",
                )
            )
        for name, (command, module) in self._commands(validate=True).items():
            checks.append(await self._validate_component(name, command, module))
        if not self.settings.host_rehearsal:
            model_ready = False
            try:
                url = (self.settings.ollama_host or os.environ.get("OLLAMA_HOST", "")).rstrip("/")
                parsed = urlsplit(url)
                if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                        or parsed.username or parsed.password or parsed.query or parsed.fragment):
                    raise ValueError("invalid local model endpoint")
                model = self.settings.ollama_model or os.environ.get("OLLAMA_MODEL", "")
                if model:
                    response = await self.http.get(url + "/api/tags")
                    response.raise_for_status()
                    models = response.json().get("models", [])
                    model_ready = any(
                        item.get("name") == model or item.get("model") == model
                        for item in models if isinstance(item, dict)
                    )
            except (httpx.HTTPError, ValueError, AttributeError):
                pass
            checks.append(CapabilityCheck(
                id="local-model", status="ready" if model_ready else "missing",
                detail="configured Ollama model is installed" if model_ready
                else "set OLLAMA_HOST/OLLAMA_MODEL and install that local model",
            ))
        if policy.gameplay_enabled:
            if policy.game_id != "minecraft" or self.settings.gameplay_config is None:
                checks.append(
                    CapabilityCheck(
                        id="gameplay-adapter",
                        status="missing",
                        detail="bind the supported Minecraft private-world adapter",
                    )
                )
            else:
                command = [
                    sys.executable,
                    "-m",
                    "stream_autopilot.gameplay",
                    "--config",
                    str(self.settings.gameplay_config),
                    "--validate",
                ]
                checks.append(
                    await self._validate_component(
                        "gameplay-adapter", command, "automation-control"
                    )
                )
        return checks

    async def _spawn(self, name: str, command: list[str], module: str) -> None:
        current = self.processes.get(name)
        if current is not None and current.returncode is None:
            return
        options = (
            {"start_new_session": True}
            if os.name != "nt"
            else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        )
        process = await asyncio.create_subprocess_exec(
            *command,
            env=self._environment(module),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            **options,
        )
        self.processes[name] = process
        self.effects_owned = True
        if name == "avatar":
            self.avatar_effects_owned = True
        try:
            await asyncio.sleep(0.1)
            if process.returncode is not None:
                raise RuntimeError(f"{name} worker exited during startup")
        except BaseException:
            await self._hard_terminate(name)
            raise

    async def _terminate(self, name: str) -> None:
        process = self.processes.pop(name, None)
        if process is None or process.returncode is not None:
            return
        timeout = (
            min(self.settings.shutdown_timeout_seconds, 0.15)
            if name == "speech"
            else self.settings.shutdown_timeout_seconds
        )
        if os.name == "nt":
            killer = await asyncio.create_subprocess_exec(
                "taskkill",
                "/PID",
                str(process.pid),
                "/T",
                "/F",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await killer.wait()
        else:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            await asyncio.wait_for(process.wait(), timeout)
        except asyncio.TimeoutError:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            await process.wait()

    async def _hard_terminate(self, name: str) -> None:
        """Immediately remove one process tree; used only by the operator pause path."""
        process = self.processes.pop(name, None)
        if process is None or process.returncode is not None:
            return
        if os.name == "nt":
            killer = await asyncio.create_subprocess_exec(
                "taskkill",
                "/PID",
                str(process.pid),
                "/T",
                "/F",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await killer.wait()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        await process.wait()

    async def _control(self, session_id: str, action: str, paused: bool) -> None:
        now = datetime.now(timezone.utc).isoformat()
        response = await self.http.post(
            self.settings.checked_backend_url() + "/events",
            headers={"X-API-Key": os.environ.get("HCP_API_KEY", "")},
            json={
                "source": "stream-autopilot",
                "kind": "input",
                "stream_id": session_id,
                "data": {
                    "schema_version": 1,
                    "kind": action,
                    "event_id": f"operator-{action}-{int(datetime.now().timestamp() * 1000)}",
                    "session_id": session_id,
                    "occurred_at": now,
                },
            },
        )
        response.raise_for_status()

    async def _notify_control(self, session_id: str, action: str, paused: bool) -> None:
        try:
            await asyncio.wait_for(self._control(session_id, action, paused), 0.1)
        except (asyncio.TimeoutError, httpx.HTTPError):
            # Local process ownership is the safety boundary; the event is best-effort telemetry.
            return

    async def preview(self, session_id: str, policy: SessionPolicy) -> None:
        if session_id != self.settings.on_air_session:
            raise ValueError("selected session does not own the shared local output")
        prior = set(self.processes)
        try:
            for name, (command, module) in self._commands().items():
                await self._spawn(name, command, module)
            if policy.gameplay_enabled:
                from .gameplay import MinecraftPeer

                if policy.game_id != "minecraft" or self.settings.gameplay_config is None:
                    raise ValueError("supported permitted game binding is missing")
                self.game = MinecraftPeer(self.settings.gameplay_config)
                await self.game.open()
                self.processes["gameplay"] = self.game.process
            await self._control(session_id, "resume", False)
        except BaseException:
            if self.game:
                await self.game.close()
                self.game = None
            for name in list(self.processes):
                if name not in prior:
                    await self._hard_terminate(name)
            raise

    async def run(self, session_id: str, policy: SessionPolicy) -> None:
        if not self.settings.control_broadcast and not policy.local_run_authorized:
            raise RuntimeError("runtime broadcast control is disabled")
        if any(
            name not in self.processes or self.processes[name].returncode is not None
            for name in self._commands()
        ):
            raise RuntimeError("preview workers are unavailable")
        if policy.gameplay_enabled:
            if self.game is None:
                raise RuntimeError("game adapter is not in a verified preview")
            await self.game.perform()
        if not self.settings.control_broadcast:
            return  # Explicitly authorized local operation has no broadcast side effect.
        if os.environ.get("AUTOPILOT_NATIVE_BROADCAST_OWNER") == "1":
            return  # The desktop uses its recording-first OBS owner and shared inbox.
        from stream_director.obs import ObsClient
        from stream_director.__main__ import obs_url

        client = ObsClient(obs_url(), os.environ.get("OBS_WEBSOCKET_PASSWORD", ""), 3)
        try:
            status = await client.request("GetStreamStatus", {})
            if status.get("outputActive"):
                raise RuntimeError("OBS is already streaming; refusing to claim it")
            await client.request("StartStream", {})
            self.broadcast_owned = True
        finally:
            await client.close()

    async def pause(self, session_id: str, policy: SessionPolicy) -> None:
        # Silence speech before any dependency or input-release wait.
        await self._hard_terminate("speech")
        release_error = None
        if self.game:
            try:
                await self.game.release()
            except (RuntimeError, OSError, asyncio.TimeoutError) as exc:
                release_error = exc
            finally:
                await self.game.close()
                self.game = None
        for name in ("gameplay", "director", "avatar", "twitch", "host"):
            await self._hard_terminate(name)
        if release_error:
            raise RuntimeError("game input release was not confirmed")
        await self.reset_avatar()
        await asyncio.shield(self._stop_phrases())
        await self._notify_control(session_id, "pause", True)

    async def reset_avatar(self) -> None:
        if not self.avatar_effects_owned:
            return
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "stream_avatar",
            "--config",
            str(self.settings.avatar_config),
            "--idle",
            env=self._environment("character-avatar"),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            await asyncio.wait_for(process.wait(), 2)
        except BaseException:
            if process.returncode is None:
                process.kill()
                await process.wait()
            raise
        if process.returncode != 0:
            raise RuntimeError("owned avatar idle reset is unconfirmed")
        self.avatar_effects_owned = False

    async def cue(self, session_id: str, cue: str, event_id: str) -> dict:
        if (
            cue
            not in {
                "wave",
                "nod",
                "shrug",
                "look_left",
                "look_right",
                "happy",
                "surprised",
                "neutral",
            }
            or not self.settings.avatar_enabled
        ):
            raise ValueError("avatar cue is unavailable")
        avatar = self.host_bindings.get("avatar_id")
        if (
            not avatar
            or "avatar" not in self.processes
            or self.processes["avatar"].returncode is not None
        ):
            raise ValueError("avatar is not in a live local preview")
        response = await self.http.post(
            self.settings.checked_backend_url() + "/events",
            headers={"X-API-Key": os.environ.get("HCP_API_KEY", "")},
            json={
                "source": "stream-avatar",
                "kind": "cue",
                "stream_id": session_id,
                "data": {
                    "schema_version": 1,
                    "kind": "cue",
                    "event_id": event_id,
                    "session_id": session_id,
                    "avatar_id": avatar,
                    "cue": cue,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            },
        )
        response.raise_for_status()
        return {"queued": True, "motion_verified": False}

    async def _stop_phrases(self) -> None:
        """OBS owns clip playback, so killing the director alone cannot silence it."""
        if not self.phrase_stop_hotkeys:
            return
        from stream_director.obs import ObsClient
        from stream_director.__main__ import obs_url

        client = ObsClient(obs_url(), os.environ.get("OBS_WEBSOCKET_PASSWORD", ""), 1)
        try:
            for hotkey in self.phrase_stop_hotkeys:
                await client.request("TriggerHotkeyByName", {"hotkeyName": hotkey})
        finally:
            await client.close()

    async def stop(self, session_id: str, policy: SessionPolicy) -> None:
        if not self.effects_owned and not self.processes and not self.broadcast_owned:
            return
        await self._hard_terminate("speech")
        release_error = None
        if self.game:
            try:
                await self.game.release()
            except (RuntimeError, OSError, asyncio.TimeoutError) as exc:
                release_error = exc
            finally:
                await self.game.close()
                self.game = None
        for name in list(self.processes):
            await self._hard_terminate(name)
        await self.reset_avatar()
        await asyncio.shield(self._stop_phrases())
        await self._notify_control(session_id, "pause", True)
        if self.broadcast_owned:
            from stream_director.obs import ObsClient
            from stream_director.__main__ import obs_url

            client = ObsClient(obs_url(), os.environ.get("OBS_WEBSOCKET_PASSWORD", ""), 3)
            try:
                await client.request("StopStream", {})
                self.broadcast_owned = False
            finally:
                await client.close()
        if release_error:
            raise RuntimeError("game input release was not confirmed")
        self.effects_owned = False

    async def close(self) -> None:
        """Close only this driver's effect ownership; inspection cannot stop other audio."""
        try:
            if self.game:
                await self.game.close()
                self.game = None
            for name in list(self.processes):
                await self._hard_terminate(name)
            await self.reset_avatar()
            if self.broadcast_owned:
                from stream_director.obs import ObsClient
                from stream_director.__main__ import obs_url

                client = ObsClient(obs_url(), os.environ.get("OBS_WEBSOCKET_PASSWORD", ""), 3)
                try:
                    await client.request("StopStream", {})
                    self.broadcast_owned = False
                finally:
                    await client.close()
            if self.effects_owned:
                await asyncio.shield(self._stop_phrases())
        finally:
            await self.http.aclose()
