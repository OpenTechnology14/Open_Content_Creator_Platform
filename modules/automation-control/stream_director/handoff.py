"""Fenced gameplay ownership contract. Does not stop OBS or change the show's identity."""

from __future__ import annotations

import asyncio
from typing import Literal, Optional, Protocol

from pydantic import BaseModel, ConfigDict, Field


class Receipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    epoch: int = Field(ge=1)
    action: Literal["released", "started"]


class GameControlAdapter(Protocol):
    async def stop_and_release(self, epoch: int) -> Receipt:
        """Cancel queued actions, stop the agent and release ALL held inputs, then acknowledge."""
        ...

    async def synchronize_and_start(self, epoch: int) -> Receipt:
        """Observe fresh state, discard old plans and arm this epoch without issuing inputs yet."""
        ...


class GameplayHandoff:
    """Operator controls for a single game session; actual adapters must check permits per input.

    No concrete game adapter ships here. An acknowledgement is supplied by an adapter, not
    physical proof from this class. Real input release and timeout behavior need hardware tests.
    """

    def __init__(
        self, session_id: str, adapter: Optional[GameControlAdapter], timeout_seconds: float = 3
    ) -> None:
        if not session_id or not 0 < timeout_seconds <= 30:
            raise ValueError("provide a session id and a 0–30 second handoff timeout")
        self.session_id = session_id
        self.adapter = adapter
        self.timeout_seconds = timeout_seconds
        self.epoch = 0
        self.owner = "unverified"
        self.reason = "needs_input_release_check"
        self._lock = asyncio.Lock()
        self._pending: set[asyncio.Task] = set()

    def permits_agent_input(self, epoch: int) -> bool:
        """Adapters must check this immediately before each input, including delayed actions."""
        return self.owner == "agent" and epoch == self.epoch

    def status(self) -> dict:
        """Return control ownership only; show/persona/capture/broadcast state stays outside."""
        return {
            "session_id": self.session_id,
            "epoch": self.epoch,
            "input_owner": self.owner,
            "reason": self.reason,
        }

    def _finished(self, task: asyncio.Task) -> None:
        self._pending.discard(task)
        if not task.cancelled():
            task.exception()  # Retrieve late failures without resurrecting ownership.

    async def _ack(self, operation, epoch: int, action: str) -> None:
        task = asyncio.create_task(operation(epoch))
        self._pending.add(task)
        task.add_done_callback(self._finished)
        done, _ = await asyncio.wait({task}, timeout=self.timeout_seconds)
        if not done:
            task.cancel()
            raise TimeoutError("game adapter acknowledgement timed out")
        receipt = Receipt.model_validate(task.result())
        if receipt.epoch != epoch or receipt.action != action:
            raise ValueError("stale or mismatched game adapter acknowledgement")

    async def switch(self, target: Literal["manual", "agent", "paused"]) -> dict:
        """Take control, let agent play, or pause gameplay; no OBS/voice/session reset occurs."""
        if target not in {"manual", "agent", "paused"}:
            raise ValueError("unknown gameplay owner")
        # A takeover must not queue behind an outstanding request to start an agent.
        self.epoch += 1
        requested_epoch = self.epoch
        self.owner = "switching"
        self.reason = "waiting_for_release"
        async with self._lock:
            if requested_epoch != self.epoch:
                return self.status()
            if self.adapter is None:
                self.owner, self.reason = "blocked", "game_adapter_unavailable"
                return self.status()
            if self._pending:
                self.owner, self.reason = "blocked", "prior_adapter_operation_still_running"
                return self.status()
            try:
                await self._ack(self.adapter.stop_and_release, requested_epoch, "released")
                if requested_epoch != self.epoch:
                    return self.status()
                if target == "agent":
                    self.reason = "waiting_for_fresh_state"
                    await self._ack(self.adapter.synchronize_and_start, requested_epoch, "started")
                if requested_epoch == self.epoch:
                    self.owner, self.reason = target, "acknowledged"
            except asyncio.CancelledError:
                if requested_epoch == self.epoch:
                    self.owner, self.reason = "blocked", "handoff_cancelled"
                for task in self._pending:
                    task.cancel()
                raise
            except Exception:
                if requested_epoch == self.epoch:
                    self.owner, self.reason = "blocked", "adapter_release_or_start_failed"
            return self.status()
