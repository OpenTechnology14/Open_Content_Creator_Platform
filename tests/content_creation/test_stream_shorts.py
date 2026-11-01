"""Selection and local output contracts: no GPU/network or real game recordings required."""

import json
from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/content-creation"))
from stream_shorts.models import ClipPlan, ShortsJob  # noqa: E402
from stream_shorts.render import build_video_filter  # noqa: E402
from stream_shorts.selector import select_clips  # noqa: E402
from stream_shorts.review import write_review  # noqa: E402


def job(**changes):
    return ShortsJob.model_validate(
        {
            "schema_version": 1,
            "recording_id": "recording-one",
            "session_id": "episode-one",
            "game_id": "minecraft",
            "show_id": "minecraft-town",
            "duration_seconds": 120,
            "clip_seconds": 20,
            "max_clips": 2,
            **changes,
        }
    )


def interaction(number, offset, user="viewer", **changes):
    return {
        "event_id": f"event-{number}",
        "session_id": "episode-one",
        "offset_seconds": offset,
        "user_key": user,
        **changes,
    }


def test_unique_participants_beat_one_spamming_viewer():
    events = [interaction(i, 10, "spammer") for i in range(100)]
    events += [interaction(100 + i, 70, f"viewer-{i}") for i in range(6)]
    plan = select_clips(job(interactions=events, max_clips=1))
    clip = plan.clips[0]
    assert clip.start_seconds <= 70 < clip.end_seconds
    assert clip.unique_viewers == 6


def test_foreign_duplicate_bot_ineligible_and_out_of_range_events_are_ignored():
    event = interaction(1, 50)
    plan = select_clips(
        job(
            interactions=[
                event,
                event,
                interaction(2, 50, session_id="other"),
                interaction(3, 50, is_bot=True),
                interaction(4, 50, eligible=False),
                interaction(5, 121),
            ]
        )
    )
    assert plan.ignored_events == 5
    assert plan.clips[0].score == 2


def test_manual_ranges_are_exact_and_automatic_clips_do_not_overlap_them():
    plan = select_clips(
        job(
            manual_sections=[{"start_seconds": 3.25, "end_seconds": 14.75, "label": "My moment"}],
            interactions=[interaction(1, 10), interaction(2, 80)],
        )
    )
    assert plan.clips[0].start_seconds == 3.25
    assert plan.clips[0].end_seconds == 14.75
    assert plan.clips[0].origin == "manual"
    assert len(plan.clips) == 2
    assert plan.clips[1].start_seconds > 14.75


def test_manual_selections_are_preserved_even_above_automatic_quota():
    plan = select_clips(
        job(
            max_clips=1,
            manual_sections=[
                {"start_seconds": 0, "end_seconds": 10},
                {"start_seconds": 20, "end_seconds": 30},
            ],
        )
    )
    assert len(plan.clips) == 2
    assert all(clip.origin == "manual" for clip in plan.clips)


def test_empty_interactions_use_an_honestly_labelled_fallback():
    plan = select_clips(job())
    assert len(plan.clips) == 1
    assert plan.clips[0].origin == "fallback"
    assert plan.clips[0].score == 0
    assert select_clips(job(automatic=False)).clips == []


def test_excluded_ranges_block_auto_selection_and_conflicting_manual_input():
    exclusions = [
        {"start_seconds": 0, "end_seconds": 60},
        {"start_seconds": 60, "end_seconds": 120},
    ]
    assert not select_clips(job(excluded_sections=exclusions)).clips
    with pytest.raises(ValidationError):
        job(
            excluded_sections=exclusions, manual_sections=[{"start_seconds": 10, "end_seconds": 20}]
        )


@pytest.mark.parametrize(
    "section",
    [
        {"start_seconds": -1, "end_seconds": 10},
        {"start_seconds": 10, "end_seconds": 10},
        {"start_seconds": 0, "end_seconds": 61},
        {"start_seconds": 110, "end_seconds": 130},
        {"start_seconds": float("nan"), "end_seconds": 20},
    ],
)
def test_invalid_operator_sections_rejected(section):
    with pytest.raises(ValidationError):
        job(manual_sections=[section])


def test_review_data_is_escaped_and_file_overwrite_is_rejected(tmp_path):
    plan = select_clips(
        job(
            manual_sections=[
                {"start_seconds": 0, "end_seconds": 10, "label": "</script><img src=x>"}
            ]
        )
    )
    target = tmp_path / "review.html"
    write_review(plan, target)
    text = target.read_text()
    assert "</script><img" not in text
    assert "\\u003c/script>" in text
    with pytest.raises(FileExistsError):
        write_review(plan, target)


def test_edited_plan_cannot_escape_output_directory_or_recording_bounds():
    plan = select_clips(job()).model_dump()
    plan["clips"][0]["clip_id"] = "../outside"
    with pytest.raises(ValidationError):
        ClipPlan.model_validate(plan)
    plan["clips"][0].update(clip_id="valid", start_seconds=110, end_seconds=130)
    with pytest.raises(ValidationError):
        ClipPlan.model_validate(plan)


def test_cli_fixture_is_a_valid_realistic_job():
    path = ROOT / "configs/local/stream-shorts-demo.json"
    plan = select_clips(ShortsJob.model_validate(json.loads(path.read_text())))
    assert len(plan.clips) == 3
    assert plan.clips[0].origin == "manual"
    assert len(plan.edit.captions) == 3
    assert len(plan.edit.punch_ins) == 2


def test_edit_cues_are_bounded_by_recording_and_have_safe_values():
    with pytest.raises(ValidationError):
        job(edit={"captions": [{"start_seconds": 1, "end_seconds": 22, "text": "too long"}]})
    with pytest.raises(ValidationError):
        job(edit={"punch_ins": [{"start_seconds": 118, "end_seconds": 121}]})
    with pytest.raises(ValidationError):
        job(edit={"style": {"accent_color": "red;movie=secret"}})


def test_edit_filter_uses_only_overlapping_cues_and_local_text_assets(tmp_path):
    plan = select_clips(
        job(
            manual_sections=[{"start_seconds": 20, "end_seconds": 30, "label": "Edit me"}],
            automatic=False,
            edit={
                "enabled": True,
                "style": {"brand_title": "Nova's Lab", "watermark": "@nova"},
                "captions": [
                    {"start_seconds": 21, "end_seconds": 23, "text": "Hello: chat; [safe]"},
                    {"start_seconds": 70, "end_seconds": 72, "text": "Outside clip"},
                ],
                "punch_ins": [
                    {"start_seconds": 22, "end_seconds": 24, "scale": 1.2, "focus_x": 0.4},
                ],
            },
        )
    )
    graph = build_video_filter(plan, plan.clips[0], tmp_path)
    assert "between(t,1.000,3.000)" in graph
    assert "between(t,2.000,4.000)" in graph
    assert "Outside clip" not in graph
    assert (tmp_path / "brand.txt").read_text() == "Nova's Lab"
    assert (tmp_path / "caption-000.txt").read_text() == "Hello: chat; [safe]"


def test_legacy_plan_keeps_plain_full_frame_layout(tmp_path):
    plan = select_clips(job())
    graph = build_video_filter(plan, plan.clips[0], tmp_path)
    assert "drawtext" not in graph
    assert "overlay" not in graph
    assert list(tmp_path.iterdir()) == []
