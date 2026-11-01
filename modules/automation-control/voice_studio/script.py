"""Operator-approved script segments, safe-boundary pause and one reviewed question."""

from __future__ import annotations

import asyncio
import uuid
import yaml

from .process import call
from .studio import Request


class ScriptPlayer:
    def __init__(self, studio) -> None:
        self.studio = studio
        self.state = studio.data.get("script", {"state": "empty"})
        if self.state.get("state") in {"playing", "pausing", "answering", "drafting_answer"}:
            self.state["state"] = "paused"
        self.task: asyncio.Task | None = None
        self.pause_requested = False
        self.save()

    def save(self) -> None:
        self.studio.data["script"] = self.state
        self.studio.save()

    async def stop(self) -> None:
        if self.task and not self.task.done():
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
        if self.state.get("state") != "empty":
            self.state["state"] = "paused"
            self.save()

    async def speak(self, text: str) -> None:
        folder = self.studio.library / "script-audio"
        folder.mkdir(exist_ok=True)
        path = folder / f"{uuid.uuid4().hex}.wav"
        try:
            await call(
                self.studio.root,
                "audio-production",
                "stream_speech.render",
                ["render"],
                {"text": text, "voice": self.state["voice"], "output": str(path)},
                60,
            )
            await call(
                self.studio.root,
                "audio-production",
                "stream_speech.render",
                ["play"],
                {"path": str(path)},
                120,
            )
        finally:
            path.unlink(missing_ok=True)

    async def play(self, answer: str | None = None) -> None:
        try:
            if answer is not None:
                await self.speak(answer)
                self.state["state"] = "paused"
                return
            while self.state["cursor"] < len(self.state["segments"]):
                await self.speak(self.state["segments"][self.state["cursor"]])
                self.state["cursor"] += 1
                self.save()
                if self.pause_requested:
                    self.state["state"] = "paused_for_question"
                    self.state["question"] = ""
                    self.state["answer"] = ""
                    return
            self.state["state"] = "finished"
        except asyncio.CancelledError:
            self.state["state"] = "paused"
            raise
        except Exception as exc:
            self.state.update(state="failed", error=str(exc)[:250])
        finally:
            self.save()

    async def draft_answer(self) -> None:
        try:
            result = await self.studio.author(
                {
                    "action": "answer",
                    "sources": self.state["sources"],
                    "question": self.state["question"],
                    "url": self.studio.settings.ollama_url,
                    "model": self.state["model"],
                    "timeout": self.studio.settings.model_timeout_seconds,
                }
            )
            self.state.update(state="answer_review", answer=result["answer"])
        except asyncio.CancelledError:
            self.state["state"] = "paused"
            raise
        except Exception as exc:
            self.state.update(
                state="answer_review", answer="That's outside today's brief.", error=str(exc)[:250]
            )
        finally:
            self.save()

    async def handle(self, request: Request) -> dict:
        action = request.action
        if action == "script_load":
            persona = self.studio.personas.get(request.persona_id)
            if not persona or persona["audio_policy"] == "gaming-reactive":
                raise ValueError("Select a scripted personality")
            if (
                not request.acceptance_confirmed
                or not request.sources.strip()
                or not request.segments
            ):
                raise ValueError("Review script and episode sources before loading")
            if any(not s.strip() or len(s) > 500 or "\0" in s for s in request.segments):
                raise ValueError("Each script segment must contain 1–500 characters")
            await self.stop()
            self.state = {
                "state": "ready",
                "persona_id": request.persona_id,
                "segments": request.segments,
                "sources": request.sources,
                "cursor": 0,
                "question": "",
                "answer": "",
                "error": "",
                "voice": request.voice
                or yaml.safe_load(
                    (self.studio.root / self.studio.settings.speech_config).read_text()
                )["voices"][persona["voice_id"]],
                "model": request.model,
                "id": uuid.uuid4().hex,
            }
        elif action == "script_pause":
            if self.state["state"] != "playing":
                raise ValueError("Script is not playing")
            self.pause_requested = True
            self.state["state"] = "pausing"
        elif action == "script_stop":
            await self.stop()
        elif action in {"script_play", "script_resume"}:
            if self.state["state"] not in {
                "ready",
                "paused",
                "paused_for_question",
                "answer_review",
                "failed",
            }:
                raise ValueError("Script is not ready to resume")
            if not request.monitor_confirmed:
                raise ValueError("Confirm the selected AI-VOICE output routing")
            self.pause_requested = False
            self.state.update(state="playing", question="", answer="", error="")
            self.task = asyncio.create_task(self.play())
        elif action == "script_question":
            if (
                self.state["state"] not in {"paused", "paused_for_question"}
                or self.state["question"]
            ):
                raise ValueError("Pause the script and admit only one question per pause")
            if not request.question.strip():
                raise ValueError("Enter a question")
            self.state.update(
                state="drafting_answer", question=request.question, answer="", error=""
            )
            self.task = asyncio.create_task(self.draft_answer())
        elif action == "script_answer":
            if self.state["state"] != "answer_review" or not request.answer.strip():
                raise ValueError("Review a drafted answer first")
            if (
                not request.acceptance_confirmed
                or not request.monitor_confirmed
                or "\0" in request.answer
            ):
                raise ValueError("Approve the answer and confirm AI-VOICE routing")
            self.state.update(state="answering", answer=request.answer)
            self.task = asyncio.create_task(self.play(request.answer))
        else:
            raise ValueError("Unknown script action")
        self.save()
        return self.studio.snapshot()
