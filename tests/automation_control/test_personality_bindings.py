"""One contract across the five files that together define a streaming personality.

A marketing personality is spread over stream-programming (show profile), stream-autopilot
(persona voice/identity), the Marketing Crosswalk registry (module and target), the social
catalog (account routing) and stream-director (Soundboard mapping). Each file validates itself;
this test is what keeps them agreeing with each other, so adding a module or personality fails
here until every side is wired.
"""

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))
sys.path.insert(0, str(ROOT / "modules/ai-agents"))
from show_planner.planner import load_program  # noqa: E402
from stream_host.models import load_config  # noqa: E402

CROSSWALK = ROOT / "modules/marketing-crosswalk/crosswalk"


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_every_crosswalk_module_has_exactly_one_scripted_personality():
    program = load_program(ROOT / "configs/local/stream-programming.yaml")
    registry = load_yaml(CROSSWALK / "modules.yml")
    targets = load_yaml(CROSSWALK / "targets.yml")["targets"]
    modules = {row["module"]: row for row in registry["modules"]}
    marketing = [profile for profile in program.profiles if profile.kind == "marketing"]

    bound = [profile.marketing_module_id for profile in marketing]
    # A discovery-only module (no subjects yet, a promotion plan on file) has no persona until it is
    # promoted; every module that can generate needs exactly one. A private module must never have one.
    needs_profile = {
        name for name, row in modules.items()
        if load_yaml(CROSSWALK / row["subjects"]).get("subjects")
        or "promotion" not in load_yaml(CROSSWALK / row["subjects"])
    }
    assert len(bound) == len(set(bound)), "a module must not have two marketing profiles"
    assert needs_profile <= set(bound) <= set(modules), "each generating module needs one marketing profile"
    private = {name for name, row in modules.items() if row.get("visibility") == "private"}
    assert not private & set(bound), "a private module must never have a stream profile"
    for profile in marketing:
        assert profile.marketing_target == modules[profile.marketing_module_id]["target"]
        assert profile.marketing_target in targets
        assert profile.audio_policy in {"opentech-scripted", "technical-scripted"}


def test_profile_and_persona_agree_on_scope_and_audio_policy():
    program = load_program(ROOT / "configs/local/stream-programming.yaml")
    host = load_config(ROOT / "configs/local/stream-autopilot.yaml")
    for profile in program.profiles:
        persona = host.personas[profile.persona_id]
        assert persona.game_id == profile.subject_id, profile.id
        assert persona.audio_policy == profile.audio_policy, profile.id


def test_scripted_personalities_have_no_soundboard_routes():
    host = load_config(ROOT / "configs/local/stream-autopilot.yaml")
    director = load_yaml(ROOT / "configs/local/stream-director.yaml")
    scripted = {
        persona.game_id
        for persona in host.personas.values()
        if persona.audio_policy != "gaming-reactive"
    }
    assert scripted, "scripted personalities should exist"
    assert not scripted & set(director.get("reaction_sounds") or {})


def test_every_show_profile_routes_to_one_social_account():
    program = load_program(ROOT / "configs/local/stream-programming.yaml")
    catalog = load_yaml(ROOT / "modules/social-management/catalog.yaml")
    owners = {}
    for account in catalog["profiles"]:
        for show_profile in account.get("show_profile_ids", []):
            assert show_profile not in owners, f"{show_profile} routed to two accounts"
            owners[show_profile] = account["id"]
    assert set(owners) == {profile.id for profile in program.profiles}
