"""Calendar invariants for a daily show without broadcaster/hardware identities."""

from datetime import date
from pathlib import Path
import sys

import pytest
import yaml
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))
from show_planner.planner import Program, calendar, load_program  # noqa: E402
from show_planner.youtube import compile_youtube_plan  # noqa: E402


def program():
    return load_program(ROOT / "configs/local/stream-programming.yaml")


def test_daily_calendar_two_flagships_per_week_and_all_profiles_reachable():
    data = program()
    episodes = calendar(data, date(2026, 9, 7), 28)
    assert len(episodes) == 28
    for start in range(0, 28, 7):
        assert sum(row["flagship"] for row in episodes[start : start + 7]) == 2
    assert len({row["subject_id"] for row in episodes}) == 21
    assert {row["profile"]["id"] for row in episodes if row["profile"]} == {
        "flight-simulator-agent",
        "beamng-agent",
        "roblox-agent",
        "opentech-marketing",
        "marketing-stream-extend",
        "marketing-content-extend",
        "marketing-ai-learning",
        "marketing-ai-control-layer",
        "marketing-chatbot-routing",
        "video-review",
    }
    assert all(
        row["game_id"] is None
        for row in episodes
        if row["profile"] and row["profile"]["kind"] != "game"
    )
    assert all(row["shorts_requested"] and row["status"] == "draft" for row in episodes)
    assert not any("xbox" in row["title"].lower() for row in episodes)


def test_expansion_keeps_primary_shows_and_overlapping_queries_consistent():
    data = program()
    one = calendar(data, date(2026, 9, 7), 28)
    two = calendar(data, date(2026, 9, 7), 28, 2)
    assert len(two) == 56
    assert [row for row in two if row["episode_id"].endswith("primary")] == one
    assert calendar(data, date(2026, 9, 10), 3) == one[3:6]


def test_persona_and_show_catalogs_cover_the_same_subjects():
    host = yaml.safe_load((ROOT / "configs/local/stream-autopilot.yaml").read_text())
    data = program()
    assert len(data.shows) == 50
    assert {show.scope_id for show in data.shows} == {
        value["game_id"] for value in host["personas"].values()
    }
    assert all(host["personas"][show.persona_id]["game_id"] == show.scope_id for show in data.shows)


def test_profiles_separate_game_marketing_and_video_review_policies():
    data = program()
    profiles = {profile.id: profile for profile in data.profiles}
    assert profiles["opentech-marketing"].display_name == "OpenTechApp Marketing"
    assert profiles["opentech-marketing"].kind == "marketing"
    assert profiles["opentech-marketing"].source.allowed_refs == [
        "task-management",
    ]
    assert profiles["opentech-marketing"].marketing_module_id == "task-management"
    assert profiles["opentech-marketing"].marketing_target == "task-management"
    assert {
        profile.marketing_module_id for profile in data.profiles if profile.kind == "marketing"
    } == {
        "task-management",
        "stream-extend",
        "content-extend",
        "ai-learning",
        "ai-control-layer",
        "chatbot-routing",
    }
    assert all(
        profile.source.allowed_refs == [profile.marketing_module_id]
        for profile in data.profiles
        if profile.kind == "marketing"
    )
    assert profiles["video-review"].display_name == "VideoReview"
    assert profiles["video-review"].kind == "video-review"
    assert profiles["video-review"].source.rights_confirmation_required
    assert {
        profile.subject_id for profile in data.profiles if profile.agent_control == "experimental"
    } == {"microsoft-flight-simulator-2024", "beamng-drive", "roblox"}
    assert all(
        profile.youtube is None
        or (
            profile.youtube.approval_required
            and not profile.youtube.upload_enabled
            and profile.youtube.visibility in ("private", "unlisted")
        )
        for profile in data.profiles
    )


def test_marketing_profiles_bind_directly_to_crosswalk_modules():
    data = program()
    registry = yaml.safe_load(
        (ROOT / "modules/marketing-crosswalk/crosswalk/modules.yml").read_text(encoding="utf-8")
    )
    modules = {row["module"]: row for row in registry["modules"]}
    profiles = {profile.id: profile for profile in data.profiles if profile.kind == "marketing"}

    assert set(profiles) == {
        "opentech-marketing",
        "marketing-stream-extend",
        "marketing-content-extend",
        "marketing-ai-learning",
        "marketing-ai-control-layer",
        "marketing-chatbot-routing",
    }
    for profile in profiles.values():
        module = modules[profile.marketing_module_id]
        assert module["target"] == profile.marketing_target
        assert profile.source.allowed_refs == [profile.marketing_module_id]
        assert set(profile.source.artifact_prefixes) == {profile.marketing_module_id}


def test_scoped_youtube_plans_require_allowlisted_sources_local_media_and_rights(tmp_path):
    data = program()
    media = tmp_path / "review.mp4"
    media.write_bytes(b"placeholder")
    crosswalk = tmp_path / "modules" / "marketing-crosswalk" / "out"
    crosswalk.mkdir(parents=True)
    artifact = crosswalk / "task-management--extend_platform--blog-brief.md"
    artifact.write_text("# Approved draft\n")
    marketing = compile_youtube_plan(
        data,
        profile_id="opentech-marketing",
        source_ref="task-management",
        media_path=media,
        title="OpenTechApp workflow",
        source_artifact_path=artifact,
        workspace_root=tmp_path,
    )
    assert marketing["status"] == "awaiting-approval"
    assert marketing["marketing_module"] == {
        "id": "task-management",
        "target": "task-management",
    }
    assert marketing["destination"]["visibility"] == "private"
    assert marketing["destination"]["channel_env"] == "HCP_OPENTECH_YOUTUBE_CHANNEL_ID"
    assert marketing["upload_enabled"] is False
    with pytest.raises(ValueError, match="allowlist"):
        compile_youtube_plan(
            data,
            profile_id="opentech-marketing",
            source_ref="arbitrary-url",
            media_path=media,
            title="Wrong source",
            source_artifact_path=artifact,
            workspace_root=tmp_path,
        )
    wrong_artifact = crosswalk / "stream-extend--automation-control--blog-brief.md"
    wrong_artifact.write_text("# Wrong product draft\n")
    with pytest.raises(ValueError, match="Crosswalk scope"):
        compile_youtube_plan(
            data,
            profile_id="opentech-marketing",
            source_ref="task-management",
            media_path=media,
            title="Wrong artifact",
            source_artifact_path=wrong_artifact,
            workspace_root=tmp_path,
        )
    with pytest.raises(ValueError, match="rights"):
        compile_youtube_plan(
            data,
            profile_id="video-review",
            source_ref="try-not-to-laugh",
            media_path=media,
            title="Review",
        )
    review = compile_youtube_plan(
        data,
        profile_id="video-review",
        source_ref="try-not-to-laugh",
        media_path=media,
        title="Review",
        rights_confirmed=True,
        approved=True,
    )
    assert review["status"] == "approved-draft"
    assert review["source"]["rights_confirmed"] is True
    assert review["upload_enabled"] is False


@pytest.mark.parametrize(
    "change", ["unknown", "wrong_scope", "wrong_format", "public", "soundboard_marketing"]
)
def test_invalid_profile_bindings_and_public_destinations_are_rejected(change):
    raw = program().model_dump()
    show = next(show for show in raw["shows"] if show["profile_id"] == "opentech-marketing")
    if change == "unknown":
        show["profile_id"] = "missing"
    elif change == "wrong_scope":
        show["subject_id"] = "other"
    elif change == "wrong_format":
        show["format"] = "gameplay"
    elif change == "soundboard_marketing":
        profile = next(p for p in raw["profiles"] if p["id"] == "opentech-marketing")
        profile["audio_policy"] = "gaming-reactive"
    else:
        profile = next(profile for profile in raw["profiles"] if profile["id"] == "video-review")
        profile["youtube"]["visibility"] = "public"
    with pytest.raises(ValidationError):
        Program.model_validate(raw)


def test_build_show_pairs_share_continuity_and_shorts_metadata():
    data = program()
    episodes = calendar(data, date(2026, 9, 7), 60)
    for project in data.projects:
        paired = [row for row in episodes if row["project_id"] == project.id]
        if project.stage == "deferred":
            assert not paired
            continue
        assert {row["format"] for row in paired} == {"tutorial", "workshop"}
        assert all(row["project_brief"] == project.model_dump() for row in paired)
        assert all(row["shorts_requested"] for row in paired)
    raw = data.model_dump()
    raw["projects"][0]["next_step"] = "Test the saved checkpoint's respawn position."
    revised = calendar(Program.model_validate(raw), date(2026, 9, 7), 60)
    matching = [row for row in revised if row["project_id"] == raw["projects"][0]["id"]]
    assert all(
        row["project_brief"]["next_step"] == raw["projects"][0]["next_step"] for row in matching
    )


@pytest.mark.parametrize("change", ["missing", "wrong_game", "deferred", "duplicate", "no_project"])
def test_invalid_project_bindings_cannot_reach_calendar(change):
    raw = program().model_dump()
    show = next(show for show in raw["shows"] if show["format"] == "tutorial")
    if change == "missing":
        show["project_id"] = "missing"
    elif change == "wrong_game":
        raw["projects"][0]["game_id"] = "other-game"
    elif change == "deferred":
        raw["projects"][0]["stage"] = "deferred"
    elif change == "duplicate":
        raw["projects"].append(raw["projects"][0])
    else:
        show["project_id"] = None
    with pytest.raises(ValidationError):
        Program.model_validate(raw)


def test_legacy_gameplay_catalog_without_projects_still_loads():
    raw = program().model_dump()
    raw.pop("projects")
    raw["shows"] = [show for show in raw["shows"] if show["format"] == "gameplay"]
    ids = {show["id"] for show in raw["shows"]}
    raw["rotation"] = [ref for ref in raw["rotation"] if ref in ids]
    for show in raw["shows"]:
        show.pop("format")
        show.pop("project_id")
    episodes = calendar(Program.model_validate(raw), date(2026, 9, 7), 28)
    assert all(row["format"] == "gameplay" and row["project_brief"] is None for row in episodes)


def test_conflicts_bad_references_and_dst_ambiguity_are_rejected():
    raw = program().model_dump()
    with pytest.raises(ValidationError):
        Program.model_validate({**raw, "rotation": ["missing"]})
    overlap = Program.model_validate({**raw, "secondary_start": "19:30"})
    with pytest.raises(ValueError, match="overlap"):
        calendar(overlap, date(2026, 9, 7), 1, 2)
    ambiguous = Program.model_validate({**raw, "primary_start": "01:30"})
    with pytest.raises(ValueError, match="unambiguous"):
        calendar(ambiguous, date(2026, 11, 1), 1)
    spring = Program.model_validate({**raw, "primary_start": "02:30"})
    with pytest.raises(ValueError, match="nonexistent"):
        calendar(spring, date(2027, 3, 14), 1)
