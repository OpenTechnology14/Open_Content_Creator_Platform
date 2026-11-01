"""Offline source-to-profile contracts; no sibling checkout or live services required."""

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "modules/marketing-crosswalk"
sys.path.insert(0, str(MODULE))
sys.path.insert(0, str(ROOT / "modules/automation-control"))

from generator.crosswalk import load  # noqa: E402
from generator.render import draft_filename, render  # noqa: E402
from generator.status import verify_evidence  # noqa: E402
from show_planner.planner import load_program  # noqa: E402
from show_planner.youtube import compile_youtube_plan  # noqa: E402


def test_every_marketing_profile_has_renderable_script_sources():
    cw = load(MODULE, ROOT)
    program = load_program(ROOT / "configs/local/stream-programming.yaml")
    assert cw.assets["stream-script"]["claim_level"] == "roadmap"
    for profile in program.profiles:
        if profile.kind != "marketing":
            continue
        module = profile.marketing_module_id
        assert cw.subjects[module], f"{profile.id} has no script sources"
        for subject in cw.subjects[module]:
            body = render(cw, module, subject, "stream-script")
            assert f"of `{module}`" in body
            assert subject["status_evidence"]["file"] in body
            evidence_target = subject["status_evidence"].get("target", profile.marketing_target)
            assert f"Evidence checkout: `{evidence_target}`" in body
            assert "AI-VOICE only; Soundboard disabled" in body
            assert "Pause-to-answer is scoped, not implemented" in body
            assert "_TODO" in body  # Deliberately not presented as an approved spoken script.


@pytest.mark.parametrize("module,count", [("ai-control-layer", 10), ("chatbot-routing", 7)])
def test_merged_blog_guides_have_individual_evidence_without_release_claims(tmp_path, module, count):
    cw = load(MODULE, ROOT)
    subjects = cw.subjects[module]
    assert len(subjects) == count
    assert "pending_pr" not in cw.module(module)
    assert "promotion" not in cw.module_meta[module]
    for subject in subjects:
        assert subject["status"] == "scaffolded"
        assert subject["coverage"]["source_guide"] is True
        assert subject["coverage"]["stream_episode"] is False
        assert subject["coverage"]["publication_verified"] is False
        evidence = subject["status_evidence"]
        assert evidence["file"] == f"content/blog/{subject['id']}.mdx"
        assert evidence["contains"].startswith("title:")
        assert not verify_evidence(subject, tmp_path).verified
        path = tmp_path / evidence["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(evidence["contains"], encoding="utf-8")
        assert verify_evidence(subject, tmp_path).verified
        path.write_text("title: Changed source", encoding="utf-8")
        assert not verify_evidence(subject, tmp_path).verified


def test_generated_scripts_handoff_only_to_the_bound_profile(tmp_path):
    cw = load(MODULE, ROOT)
    program = load_program(ROOT / "configs/local/stream-programming.yaml")
    profiles = [profile for profile in program.profiles if profile.kind == "marketing"]
    # Only the local-file handoff contract is tested; this is not a playable recording.
    media = tmp_path / "fixture.mp4"
    media.write_bytes(b"contract fixture, not a real recording")
    for profile in profiles:
        module = profile.marketing_module_id
        subject = cw.subjects[module][0]
        artifact = tmp_path / profile.source.artifact_root / draft_filename(
            module, subject, "stream-script"
        )
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(render(cw, module, subject, "stream-script"), encoding="utf-8")
        kwargs = dict(
            media_path=media, title=subject["name"], source_artifact_path=artifact,
            workspace_root=tmp_path,
        )
        plan = compile_youtube_plan(program, profile_id=profile.id, source_ref=module, **kwargs)
        assert plan["persona_id"] == profile.persona_id
        assert plan["audio_policy"] == profile.audio_policy
        assert plan["marketing_module"] == {"id": module, "target": cw.target_for(module)}
        assert plan["approval"] == {"required": True, "approved": False}
        assert plan["upload_enabled"] is False
        assert plan["destination"]["visibility"] == "private"
        for other in profiles:
            if other.id == profile.id:
                continue
            with pytest.raises(ValueError, match="Crosswalk scope"):
                compile_youtube_plan(
                    program, profile_id=other.id, source_ref=other.marketing_module_id, **kwargs
                )
