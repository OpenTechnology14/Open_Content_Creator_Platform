"""Render local vertical MP4s with a deterministic FFmpeg layout and no upload side effects."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import textwrap
from pathlib import Path

from .models import Clip, ClipPlan


def inspect_media(source: Path) -> dict:
    """Read video metadata using the bundled imageio-ffmpeg executable."""
    import imageio_ffmpeg

    reader = imageio_ffmpeg.read_frames(str(source), pix_fmt="rgb24")
    try:
        return next(reader)
    finally:
        reader.close()


def _overlap(start: float, end: float, other_start: float, other_end: float) -> bool:
    return start < other_end and other_start < end


def _relative_range(clip: Clip, start: float, end: float) -> tuple[float, float]:
    return max(0, start - clip.start_seconds), min(clip.end_seconds, end) - clip.start_seconds


def _text_asset(directory: Path, name: str, value: str, width: int | None = None) -> str:
    text = "\n".join(textwrap.wrap(value, width=width) or [value]) if width else value
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path.name


def build_video_filter(plan: ClipPlan, clip: Clip, asset_dir: Path) -> str:
    """Build a bounded filter graph from validated edit data and local text assets."""
    style = plan.edit.style
    background = style.background_color.replace("#", "0x")
    accent = style.accent_color.replace("#", "0x")
    layout = (
        "scale=720:1280:force_original_aspect_ratio=decrease:force_divisible_by=2,"
        f"pad=720:1280:(ow-iw)/2:(oh-ih)/2:color={background},setsar=1"
    )
    if not plan.edit.enabled:
        return f"[0:v]{layout},fps=30[outv]"
    punch_ins = [
        cue
        for cue in plan.edit.punch_ins
        if _overlap(clip.start_seconds, clip.end_seconds, cue.start_seconds, cue.end_seconds)
    ]
    split_outputs = ["basein", *(f"pin{i}" for i in range(len(punch_ins)))]
    filters = []
    if punch_ins:
        filters.append(
            f"[0:v]split={len(split_outputs)}" + "".join(f"[{x}]" for x in split_outputs)
        )
    else:
        filters.append("[0:v]null[basein]")
    filters.append(f"[basein]{layout}[base]")
    current = "base"
    for index, cue in enumerate(punch_ins):
        start, end = _relative_range(clip, cue.start_seconds, cue.end_seconds)
        zoom = (
            f"crop=iw/{cue.scale}:ih/{cue.scale}:"
            f"(iw-ow)*{cue.focus_x}:(ih-oh)*{cue.focus_y},{layout}"
        )
        filters.append(f"[pin{index}]{zoom}[zoom{index}]")
        output = f"composite{index}"
        filters.append(
            f"[{current}][zoom{index}]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})'"
            f"[{output}]"
        )
        current = output

    title_file = _text_asset(asset_dir, "brand.txt", style.brand_title)
    watermark_file = _text_asset(asset_dir, "watermark.txt", style.watermark)
    draw_filters = [
        f"drawbox=x=0:y=0:w=iw:h=12:color={accent}:t=fill",
        f"drawtext=textfile={title_file}:fontcolor=white:fontsize=36:x=40:y=46:fix_bounds=1",
        (
            f"drawtext=textfile={watermark_file}:fontcolor=white@0.75:fontsize=24:"
            "x=w-text_w-36:y=h-text_h-30:fix_bounds=1"
        ),
    ]
    if style.captions_enabled:
        captions = [
            cue
            for cue in plan.edit.captions
            if _overlap(clip.start_seconds, clip.end_seconds, cue.start_seconds, cue.end_seconds)
        ]
        for index, cue in enumerate(captions):
            start, end = _relative_range(clip, cue.start_seconds, cue.end_seconds)
            caption_file = _text_asset(asset_dir, f"caption-{index:03d}.txt", cue.text, width=26)
            draw_filters.append(
                f"drawtext=textfile={caption_file}:fontcolor=white:fontsize=42:"
                "box=1:boxcolor=black@0.72:boxborderw=18:"
                f"x=(w-text_w)/2:y=h*0.76:fix_bounds=1:enable='between(t,{start:.3f},{end:.3f})'"
            )
    filters.append(f"[{current}]" + ",".join(draw_filters) + ",fps=30[outv]")
    return ";".join(filters)


def render_plan(plan: ClipPlan, source: Path, destination: Path) -> dict:
    """Render to a new directory; refuse overwrite and incomplete source recordings.

    Full-frame fit preserves the game's HUD. Optional validated edit cues add branding,
    supplied captions, punch-ins and audio leveling without network or GPU dependencies.
    """
    import imageio_ffmpeg

    source = source.resolve(strict=True)
    if not source.is_file() or source.suffix.lower() not in {".mp4", ".mkv", ".mov", ".webm"}:
        raise ValueError("provide a local MP4/MKV/MOV/WebM recording")
    if not plan.clips:
        raise ValueError("plan contains no clips")
    metadata = inspect_media(source)
    actual_duration = float(metadata.get("duration", 0))
    if actual_duration <= 0 or abs(actual_duration - plan.duration_seconds) > 0.25:
        raise ValueError("declared duration does not match media; regenerate the job/plan")
    destination.mkdir(parents=True, exist_ok=False)
    fingerprint = hashlib.sha256(plan.model_dump_json().encode()).hexdigest()
    results = []
    manifest = {
        "schema_version": 1,
        "recording_id": plan.recording_id,
        "session_id": plan.session_id,
        "show_id": plan.show_id,
        "game_id": plan.game_id,
        "source": str(source),
        "plan_sha256": fingerprint,
        "status": "rendering",
        "outputs": results,
        "published": False,
    }
    manifest_path = destination / "manifest.json"

    def save() -> None:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    save()
    try:
        for clip in plan.clips:
            target = destination / f"{clip.clip_id}.mp4"
            with tempfile.TemporaryDirectory(prefix="edit-", dir=destination) as temporary:
                asset_dir = Path(temporary)
                command = [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-nostdin",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-n",
                    "-ss",
                    str(clip.start_seconds),
                    "-i",
                    str(source),
                    "-t",
                    str(clip.end_seconds - clip.start_seconds),
                    "-map",
                    "[outv]",
                    "-map",
                    "0:a:0?",
                    "-filter_complex",
                    build_video_filter(plan, clip, asset_dir),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "23",
                    "-pix_fmt",
                    "yuv420p",
                ]
                if plan.edit.enabled and plan.edit.style.normalize_audio:
                    command.extend(
                        ["-af", f"loudnorm=I={plan.edit.style.target_lufs}:TP=-1.5:LRA=11"]
                    )
                command.extend(
                    ["-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(target)]
                )
                subprocess.run(
                    command, check=True, capture_output=True, timeout=300, cwd=asset_dir
                )
            rendered = inspect_media(target)
            if (
                tuple(rendered["size"]) != (720, 1280)
                or abs(rendered["duration"] - (clip.end_seconds - clip.start_seconds)) > 0.3
            ):
                raise ValueError("rendered video failed size/duration verification")
            results.append(
                {
                    **clip.model_dump(),
                    "path": str(target.resolve()),
                    "duration_seconds": rendered["duration"],
                    "status": "rendered",
                    "captions": (
                        sum(
                            _overlap(
                                clip.start_seconds,
                                clip.end_seconds,
                                cue.start_seconds,
                                cue.end_seconds,
                            )
                            for cue in plan.edit.captions
                        )
                        if plan.edit.enabled and plan.edit.style.captions_enabled
                        else 0
                    ),
                    "punch_ins": (
                        sum(
                            _overlap(
                                clip.start_seconds,
                                clip.end_seconds,
                                cue.start_seconds,
                                cue.end_seconds,
                            )
                            for cue in plan.edit.punch_ins
                        )
                        if plan.edit.enabled
                        else 0
                    ),
                    "audio_normalized": (
                        plan.edit.enabled and plan.edit.style.normalize_audio
                    ),
                }
            )
            save()
        manifest["status"] = "complete"
        save()
        return manifest
    except BaseException:
        manifest["status"] = "failed"
        save()
        raise
