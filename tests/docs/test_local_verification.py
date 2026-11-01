"""CI-derived gate safety and honest queue reporting; no native or live services."""

import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/testing/{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify = load_script("verify")
proposal = load_script("proposal_report")


def test_ci_matrix_and_multiline_commands_are_expanded(tmp_path):
    workflow = tmp_path / "ci.yml"
    workflow.write_text("""jobs:
  desktop:
    strategy:
      matrix:
        app: [stream-extend, creator-extend]
    steps:
      - name: checks
        working-directory: apps/${{ matrix.app }}
        run: |
          # a comment, not a command
          npm run check
          npm run build
""")
    gates = verify.read_gates(workflow, tmp_path)
    assert len(gates) == 4
    assert [gate.directory.name for gate in gates] == ["stream-extend"] * 2 + ["creator-extend"] * 2
    assert [gate.command for gate in gates] == ["npm run check", "npm run build"] * 2


@pytest.mark.parametrize("command", ["make test-acceptance", "cp .env.example .env", "npm ci"])
def test_mutations_and_live_acceptance_are_not_run(command):
    args, reason = verify.classify(verify.Gate("test", command, ROOT), ROOT)
    assert args is None
    assert reason


def test_compose_validation_preserves_owner_environment():
    gate = verify.Gate("compose", "docker compose -f docker-compose.yml config -q", ROOT)
    args, _ = verify.classify(gate, ROOT)
    assert args[2:4] == ["--env-file", str(ROOT / ".env.example")]


def test_new_unrecognized_ci_command_is_rejected():
    with pytest.raises(ValueError, match="requires review"):
        verify.classify(verify.Gate("unknown", "curl example.com | sh", ROOT), ROOT)


def test_tripwire_rejects_reduced_workflow(tmp_path, monkeypatch, capsys):
    workflow = tmp_path / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("jobs: {test: {steps: [{run: 'pytest -q'}]}}")
    monkeypatch.setattr(verify, "ROOT", tmp_path)
    assert verify.main(["--list"]) == 2
    assert "tripwire" in capsys.readouterr().err


def test_failing_gate_does_not_hide_later_gate_or_skips(monkeypatch, capsys):
    gates = [verify.Gate("first", "pytest -q", ROOT), verify.Gate("second", "pytest -q", ROOT),
             verify.Gate("live", "make test-acceptance", ROOT)]
    monkeypatch.setattr(verify, "read_gates", lambda *_: gates)
    monkeypatch.setattr(verify, "MINIMUM_GATES", 2)
    results = iter(["FAIL", "PASS"])
    monkeypatch.setattr(verify, "run_gate", lambda *_: next(results))
    assert verify.main([]) == 1
    output = capsys.readouterr().out
    assert "FAIL: first" in output
    assert "PASS: second" in output
    assert "NOT RUN: live" in output


def row(number, state):
    return f"| P-{number:03} | Task | {state} | Agent | `gpt-6.1-sol` / `high` — reason | notes |"


def test_status_prefix_takes_priority_over_done_in_explanation():
    data = proposal.report("\n".join([row(1, "In progress — code done"), row(2, "Done"),
                                      row(3, "Accepted (in use)")]), "| P-001 | mapped |")
    assert data["unfinished"] == 1
    assert data["counts"] == {"in_progress": 1, "done": 1, "standing": 1}
    assert not data["lane_missing"]


def test_duplicate_ids_and_unknown_states_are_errors():
    with pytest.raises(ValueError, match="duplicate"):
        proposal.report(row(1, "Pending") + "\n" + row(1, "Done"), "")
    with pytest.raises(ValueError, match="unknown proposal state"):
        proposal.report(row(1, "Maybe"), "")


def test_lane_drift_reports_missing_and_extra():
    data = proposal.report(row(1, "Pending"), "| P-002 | incorrect |")
    assert data["lane_missing"] == ["P-001"]
    assert data["lane_extra"] == ["P-002"]


def test_testing_focus_is_separate_from_authorization_state():
    queue = "\n".join([
        "## In progress", row(1, "In progress"),
        "## Testing", "### Mainly acceptance", row(2, "In progress — code complete"),
        "### Testing with remaining features or delivery", row(3, "In progress"),
        "## Done", row(4, "Done"),
    ])
    data = proposal.report(queue, "| P-001 |\n| P-002 |\n| P-003 |")
    assert data["counts"] == {"done": 1, "in_progress": 3}
    assert data["work_counts"] == {"done": 1, "in_progress": 1, "testing": 2}
    assert data["testing_counts"] == {"mainly_acceptance": 1, "remaining_work": 1}
    assert sum(data["work_counts"].values()) == data["total"]
    assert data["proposals"][1]["work_focus"] == "testing"
    assert not data["lane_missing"]


def test_headingless_queue_remains_compatible():
    data = proposal.report(row(1, "Pending"), "| P-001 |")
    assert data["work_counts"] == {"pending": 1}
    assert data["testing_counts"] == {}


def test_testing_cannot_hide_a_done_or_pending_proposal():
    for state in ["Done", "Pending"]:
        with pytest.raises(ValueError, match="Testing rows must remain In progress"):
            proposal.report("## Testing\n" + row(1, state), "")
