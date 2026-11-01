"""Still-job boundaries, failure retention and restoration without Blender dependencies."""

import importlib.util
import json
from pathlib import Path
import struct
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("batch_render", ROOT / "modules/content-creation/blender/scripts/batch_render.py")
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)
IDENT = "a" * 32


class Scenes(dict):
    def __iter__(self):
        return iter(self.values())


def backend(tmp_path, names, fail=()):
    project = tmp_path / "test.blend"
    project.write_bytes(b"BLENDER-v450" + b"project fixture")
    scenes = Scenes({name: SimpleNamespace(name=name, render=SimpleNamespace(filepath="original-path", image_settings=SimpleNamespace(file_format="JPEG"), resolution_x=64, resolution_y=64, resolution_percentage=100)) for name in names})
    original = SimpleNamespace(name="original window scene")
    window = SimpleNamespace(scene=original)

    def render(write_still, scene):
        if scene in fail:
            raise RuntimeError("controlled render failure")
        target = Path(scenes[scene].render.filepath)
        target.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 64, 64))

    return SimpleNamespace(data=SimpleNamespace(filepath=str(project), scenes=scenes), context=SimpleNamespace(window=window), ops=SimpleNamespace(render=SimpleNamespace(render=render)))


def test_plan_is_read_only_and_uses_selected_inventory(tmp_path):
    api = backend(tmp_path, ["one", "two"])
    plan = batch.make_plan(api, tmp_path, ["two"], IDENT)
    assert plan["available_scenes"] == ["one", "two"]
    assert plan["selected_scenes"] == ["two"]
    assert not Path(plan["output"]).exists()
    assert plan["upload_enabled"] is False


@pytest.mark.parametrize("names", [["missing"], ["one", "one"], ["one"] * 17])
def test_invalid_selections_fail_before_writes(tmp_path, names):
    api = backend(tmp_path, ["one"])
    with pytest.raises(ValueError):
        batch.make_plan(api, tmp_path, names, IDENT)
    assert not (tmp_path / ("blender-" + IDENT)).exists()


def test_scene_labels_cannot_escape_output_paths_and_settings_are_restored(tmp_path):
    names = ["../../outside", "two"]
    api = backend(tmp_path, names)
    original = api.context.window.scene
    plan = batch.make_plan(api, tmp_path, names, IDENT)
    result = batch.render_job(api, plan)
    assert result["status"] == "complete"
    assert [item["artifact"]["file"] for item in result["scenes"]] == ["00.png", "01.png"]
    assert api.context.window.scene is original
    for scene in api.data.scenes:
        assert scene.render.filepath == "original-path"
        assert scene.render.image_settings.file_format == "JPEG"


def test_partial_failure_preserves_success_and_manifest(tmp_path):
    api = backend(tmp_path, ["bad", "good"], fail=["bad"])
    plan = batch.make_plan(api, tmp_path, ["bad", "good"], IDENT)
    result = batch.render_job(api, plan)
    assert result["status"] == "failed"
    assert [item["status"] for item in result["scenes"]] == ["failed", "complete"]
    assert (Path(plan["output"]) / "01.png").exists()
    assert json.loads((Path(plan["output"]) / "job.json").read_text())["status"] == "failed"


def test_existing_attempt_and_empty_render_are_rejected(tmp_path):
    api = backend(tmp_path, ["one"])
    plan = batch.make_plan(api, tmp_path, [], IDENT)
    with pytest.raises(ValueError, match="Select"):
        batch.render_job(api, plan)
    assert not Path(plan["output"]).exists()
    Path(plan["output"]).mkdir()
    with pytest.raises(ValueError, match="already exists"):
        batch.make_plan(api, tmp_path, ["one"], IDENT)


def test_metadata_for_other_job_is_preserved(tmp_path):
    api = backend(tmp_path, ["one"])
    plan = batch.make_plan(api, tmp_path, ["one"], IDENT)
    metadata = tmp_path / "other.json"
    metadata.write_text('{"job_id":"other"}')
    with pytest.raises(ValueError, match="another job"):
        batch.render_job(api, plan, metadata)
    assert metadata.read_text() == '{"job_id":"other"}'
    assert not Path(plan["output"]).exists()


def test_invalid_png_is_not_marked_complete(tmp_path):
    api = backend(tmp_path, ["one"])
    api.ops.render.render = lambda **kwargs: Path(api.data.scenes["one"].render.filepath).write_bytes(b"\x89PNG\r\n\x1a\n")
    result = batch.render_job(api, batch.make_plan(api, tmp_path, ["one"], IDENT))
    assert result["status"] == "failed"
    assert result["scenes"][0]["artifact"] is None


def test_resolution_is_bounded_before_render(tmp_path):
    api = backend(tmp_path, ["one"])
    api.data.scenes["one"].render.resolution_x = 5000
    with pytest.raises(ValueError, match="4096"):
        batch.make_plan(api, tmp_path, ["one"], IDENT)
