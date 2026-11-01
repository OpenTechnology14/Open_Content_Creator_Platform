"""Rank bounded interaction windows and preserve explicit operator selections."""

from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict

from .models import Clip, ClipPlan, ShortsJob


def overlaps(start: float, end: float, other_start: float, other_end: float) -> bool:
    """Use half-open intervals so adjacent clips can be selected."""
    return start < other_end and other_start < end


def select_clips(job: ShortsJob) -> ClipPlan:
    """Manual selections first; top distinct interaction windows next; explicit fallback last.

    A score counts eligible viewer participation with a per-viewer cap. It is not bot detection,
    sentiment analysis or a promise the moment is entertaining. All offsets refer to this file.
    """
    clips = []
    seen = set()
    events = []
    ignored = 0
    for event in job.interactions:
        if (
            event.session_id != job.session_id
            or event.event_id in seen
            or event.is_bot
            or not event.eligible
            or event.offset_seconds >= job.duration_seconds
        ):
            ignored += 1
            continue
        seen.add(event.event_id)
        events.append(event)
    events.sort(key=lambda event: event.offset_seconds)
    offsets = [event.offset_seconds for event in events]

    def append(
        start: float, end: float, label: str, origin: str, score: float = 0, viewers: int = 0
    ) -> None:
        clips.append(
            Clip(
                start_seconds=start,
                end_seconds=end,
                label=label,
                clip_id=f"clip-{len(clips) + 1:03d}",
                origin=origin,
                score=score,
                unique_viewers=viewers,
            )
        )

    for section in job.manual_sections:
        append(section.start_seconds, section.end_seconds, section.label, "manual")

    length = min(job.clip_seconds, job.duration_seconds)

    def blocked(start: float, end: float) -> bool:
        return any(
            overlaps(start, end, item.start_seconds, item.end_seconds)
            for item in [*clips, *job.excluded_sections]
        )

    if job.automatic and length >= 5:
        # Bucket candidate centers to five-second increments: bounded by recording duration,
        # not one candidate per message in a chat flood. Binary search narrows event windows.
        starts = {
            max(
                0, min((int(offset // 5) * 5) - job.pre_roll_seconds, job.duration_seconds - length)
            )
            for offset in offsets
        }
        candidates = []
        for start in starts:
            end = start + length
            if blocked(start, end):
                continue
            participants = defaultdict(int)
            for event in events[bisect_left(offsets, start) : bisect_left(offsets, end)]:
                participants[event.user_key] = min(
                    job.per_viewer_cap, participants[event.user_key] + 1
                )
            score = sum(participants.values()) + len(participants)
            candidates.append((score, len(participants), start, end))
        candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
        for score, viewers, start, end in candidates:
            if len(clips) >= job.max_clips:
                break
            if score and not blocked(start, end):
                append(start, end, "High interaction moment", "interaction", score, viewers)
        if not clips:
            # Sparse/empty chat still produces a clearly labelled candidate unless excluded.
            # Try the midpoint, beginning and boundaries after exclusions, without fake scores.
            fallback_starts = [(job.duration_seconds - length) / 2, 0]
            fallback_starts.extend(section.end_seconds for section in job.excluded_sections)
            for start in fallback_starts:
                end = start + length
                if end <= job.duration_seconds and not blocked(start, end):
                    append(start, end, "Fallback — review this moment", "fallback")
                    break
    return ClipPlan(
        recording_id=job.recording_id,
        session_id=job.session_id,
        game_id=job.game_id,
        show_id=job.show_id,
        duration_seconds=job.duration_seconds,
        ignored_events=ignored,
        clips=clips,
        edit=job.edit,
    )
