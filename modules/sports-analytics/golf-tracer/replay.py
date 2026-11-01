"""Replay buffer.

Holds the last N seconds of frames in RAM so a 'shot_detected' event can
trigger an instant replay (slow-mo, looped, with trajectory overlay).

Designed as a sidecar to tracer.py — wire them together in your own
orchestration once you've validated the tracer.
"""
from __future__ import annotations

import collections
import threading
import time
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Frame:
    ts: float
    image: np.ndarray


class ReplayBuffer:
    def __init__(self, seconds: float = 10.0, fps: float = 60.0) -> None:
        self.max_frames = int(seconds * fps)
        self.buffer: collections.deque[Frame] = collections.deque(maxlen=self.max_frames)
        self.lock = threading.Lock()

    def push(self, frame: np.ndarray) -> None:
        with self.lock:
            self.buffer.append(Frame(ts=time.time(), image=frame.copy()))

    def snapshot(self) -> list[Frame]:
        with self.lock:
            return list(self.buffer)

    def write_clip(self, out_path: str, slow_factor: float = 1.0, fps: float = 60.0) -> None:
        frames = self.snapshot()
        if not frames:
            return
        h, w = frames[0].image.shape[:2]
        out_fps = max(1.0, fps / slow_factor)
        writer = cv2.VideoWriter(
            out_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            out_fps,
            (w, h),
        )
        for f in frames:
            writer.write(f.image)
        writer.release()
