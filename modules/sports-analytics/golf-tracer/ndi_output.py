#!/usr/bin/env python3
"""NDI output sender for the golf tracer overlay.

Sends rendered frames (with trajectory overlay) as an NDI source that OBS
can consume via the OBS NDI plugin. Lower latency than virtual camera.

Usage:
    python ndi_output.py --source "Golf Tracer"
    python ndi_output.py --source "Golf Tracer" --width 1920 --height 1080

Requirements:
    pip install ndi-python opencv-python numpy
    NDI SDK installed: https://ndi.video/tools/
    OBS NDI plugin: https://github.com/obs-ndi/obs-ndi

Note: ndi-python is a wrapper around the NDI SDK. If it's unavailable on
your platform, use pyvirtualcam as a fallback (see tracer.py).
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

import cv2
import numpy as np

log = logging.getLogger("ndi_output")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")


def create_ndi_sender(source_name: str):
    """Initialize an NDI sender. Returns (ndi_send, ndi_video_frame) or exits."""
    try:
        import NDIlib as ndi  # type: ignore[import-untyped]
    except ImportError:
        log.error(
            "ndi-python not installed. Install with: pip install ndi-python\n"
            "Also requires the NDI SDK: https://ndi.video/tools/"
        )
        sys.exit(1)

    if not ndi.initialize():
        log.error("NDI failed to initialize. Is the NDI SDK installed?")
        sys.exit(1)

    send_settings = ndi.SendCreate()
    send_settings.ndi_name = source_name
    ndi_send = ndi.send_create(send_settings)

    if ndi_send is None:
        log.error("Failed to create NDI sender")
        sys.exit(1)

    log.info("NDI sender created: '%s'", source_name)
    return ndi, ndi_send


def send_frame(ndi, ndi_send, frame: np.ndarray) -> None:
    """Send a single BGR frame over NDI."""
    # NDI expects BGRA
    if frame.shape[2] == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)

    h, w = frame.shape[:2]
    video_frame = ndi.VideoFrameV2()
    video_frame.data = frame
    video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_BGRA
    video_frame.xres = w
    video_frame.yres = h
    video_frame.line_stride_in_bytes = w * 4

    ndi.send_send_video_v2(ndi_send, video_frame)


def demo_loop(source_name: str, width: int, height: int, fps: int) -> None:
    """Demo: send a test pattern to verify NDI works before integrating with tracer."""
    ndi, ndi_send = create_ndi_sender(source_name)

    frame_interval = 1.0 / fps
    frame_count = 0

    log.info("Sending test pattern at %dx%d @ %d fps. Open OBS → Add NDI Source → '%s'",
             width, height, fps, source_name)
    log.info("Press Ctrl+C to stop.")

    try:
        while True:
            start = time.time()

            # Generate test frame with moving bar
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            x = (frame_count * 5) % width
            cv2.rectangle(frame, (x, 0), (x + 50, height), (0, 255, 0), -1)
            cv2.putText(frame, f"NDI: {source_name}", (50, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            cv2.putText(frame, f"Frame {frame_count}", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)

            send_frame(ndi, ndi_send, frame)
            frame_count += 1

            elapsed = time.time() - start
            sleep = frame_interval - elapsed
            if sleep > 0:
                time.sleep(sleep)

    except KeyboardInterrupt:
        log.info("Stopping NDI sender.")
    finally:
        ndi.send_destroy(ndi_send)
        ndi.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NDI output for golf tracer")
    parser.add_argument("--source", default="Golf Tracer", help="NDI source name")
    parser.add_argument("--width", type=int, default=1920, help="Frame width")
    parser.add_argument("--height", type=int, default=1080, help="Frame height")
    parser.add_argument("--fps", type=int, default=30, help="Target FPS")
    args = parser.parse_args()
    demo_loop(args.source, args.width, args.height, args.fps)
