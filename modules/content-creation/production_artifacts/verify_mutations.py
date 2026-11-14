"""Explicit sequential behavioral mutation audit; never imported by the offline suite.

Run only in the task's isolated worktree. Every edit is restored in finally and hashed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
UNIT = "tests/content_creation/test_production_artifacts.py::"
JOBS = "tests/content_creation/test_production_artifacts_jobs.py::"
# Each mutation changes executable admission/state behavior, never a compiler token.
CASES = [
    (
        "strict-fields",
        "models.py",
        'extra="forbid"',
        'extra="ignore"',
        UNIT + "test_strict_wire_rejects_unknown_fields_nonobjects_future_and_nan",
    ),
    (
        "json-size",
        "safety.py",
        "MAX_JSON = 1024 * 1024",
        "MAX_JSON = 2 * 1024 * 1024",
        UNIT + "test_decoder_enforces_size_duplicates_object_and_finite_values",
    ),
    (
        "json-object",
        "safety.py",
        "if not isinstance(value, dict):",
        "if False:",
        UNIT + "test_decoder_enforces_size_duplicates_object_and_finite_values",
    ),
    (
        "json-duplicates",
        "safety.py",
        "if key in result:",
        "if False:",
        UNIT + "test_decoder_enforces_size_duplicates_object_and_finite_values",
    ),
    (
        "json-finite",
        "safety.py",
        'parse_constant=lambda _: (_ for _ in ()).throw(Fault("invalid_request")),',
        "parse_constant=lambda _: 0,",
        UNIT + "test_decoder_enforces_size_duplicates_object_and_finite_values",
    ),
    (
        "path-containment",
        "safety.py",
        'raise Fault("unsafe_path")',
        "pass",
        UNIT + "test_relative_escape_to_existing_file_and_exclusive_write_are_rejected",
    ),
    (
        "nofollow",
        "safety.py",
        "os.O_NOFOLLOW",
        "0",
        UNIT + "test_root_and_ancestor_symlinks_are_rejected",
    ),
    (
        "regular-files",
        "safety.py",
        "if not stat.S_ISREG(os.fstat(result).st_mode):",
        "if False:",
        UNIT + "test_atomic_symlink_and_fifo_state_cannot_be_opened",
    ),
    (
        "symlink-target",
        "safety.py",
        "if stat.S_ISLNK(existing.st_mode):",
        "if False:",
        UNIT + "test_atomic_symlink_and_fifo_state_cannot_be_opened",
    ),
    (
        "exclusive-output",
        "safety.py",
        "if exclusive:",
        "if False:",
        UNIT + "test_relative_escape_to_existing_file_and_exclusive_write_are_rejected",
    ),
    (
        "flush-before-rename",
        "safety.py",
        "os.fsync(output.fileno())",
        "pass",
        UNIT + "test_atomic_fsync_failure_preserves_previous_bytes",
    ),
    (
        "operation-key",
        "store.py",
        "if operation.payload_sha256 != digest(payload):",
        "if False:",
        UNIT + "test_create_is_durable_idempotent_and_changed_operation_has_no_side_effects",
    ),
    (
        "revision-cas",
        "store.py",
        "if prod.revision != expected_revision:",
        "if False:",
        UNIT + "test_revision_conflict_has_no_side_effects",
    ),
    (
        "future-state",
        "store.py",
        "ge=1, le=1)",
        "ge=1, le=2)",
        UNIT + "test_corrupt_or_future_state_is_preserved_and_not_reinitialized",
    ),
    (
        "source-profiles",
        "sources.py",
        'raise Fault("profile_conflict")',
        "pass",
        JOBS + "test_bad_source_admission_leaves_no_snapshot",
    ),
    (
        "launcher-hash",
        "sources.py",
        "if request.source_sha256 != handle.expected_sha256:",
        "if False:",
        JOBS + "test_input_expected_hash_is_pinned_by_launcher",
    ),
    (
        "source-path-identity",
        "sources.py",
        'raise Fault("source_changed")',
        "pass",
        JOBS + "test_replacement_at_each_source_boundary_is_rejected[before-open]",
    ),
    (
        "disk-margin",
        "sources.py",
        "if free < estimate + margin:",
        "if False:",
        JOBS + "test_missing_dependency_and_disk_estimate_block_before_snapshot",
    ),
    (
        "source-cas",
        "sources.py",
        "if prod.revision != request.expected_revision:",
        "if False:",
        JOBS + "test_bad_source_admission_leaves_no_snapshot",
    ),
    (
        "manual-plan",
        "exports.py",
        'raise Fault("plan_conflict")',
        "pass",
        JOBS + "test_plan_pins_source_show_and_exact_manual_plain_range",
    ),
    (
        "export-cas",
        "exports.py",
        "if prod.revision != request.expected_revision:",
        "if False:",
        JOBS + "test_export_stale_revision_and_wrong_source_plan_rejected_without_attempt",
    ),
    (
        "export-source-pin",
        "exports.py",
        'raise Fault("source_unavailable")',
        "pass",
        JOBS + "test_export_stale_revision_and_wrong_source_plan_rejected_without_attempt",
    ),
    (
        "export-plan-pin",
        "exports.py",
        'raise Fault("plan_conflict")',
        "pass",
        JOBS + "test_valid_plan_id_with_altered_hash_is_not_admitted",
    ),
    (
        "terminal-monotonic",
        "exports.py",
        "if previous.phase in TERMINAL:",
        "if False:",
        JOBS + "test_terminal_attempt_cannot_reopen",
    ),
    (
        "restart-interrupted",
        "store.py",
        "if attempt.phase not in TERMINAL:",
        "if False:",
        JOBS + "test_restart_interrupts_active_attempt_never_kills_or_replays",
    ),
    (
        "owned-cancel",
        "media.py",
        "self.cancelled.set()",
        "pass",
        JOBS + "test_real_process_cancel_and_deadline_reap_only_live_owned_group",
    ),
    (
        "owned-deadline",
        "media.py",
        "moment > deadline",
        "False",
        JOBS + "test_owned_process_deadline_is_enforced",
    ),
    (
        "dependency",
        "media.py",
        'raise Fault("dependency_unavailable")',
        "pass",
        JOBS + "test_missing_executable_is_rejected_before_launch",
    ),
    (
        "full-decode",
        "media.py",
        "if full:",
        "if False:",
        UNIT + "test_media_probe_bounds_precede_full_decode_and_full_decode_is_required",
    ),
    (
        "fd-byte-hash",
        "media.py",
        "hash_fd(fd) != expected",
        "False",
        JOBS + "test_fd_hash_validation_and_postdecode_replacement_are_checked",
    ),
    (
        "output-preset",
        "exports.py",
        'raise Fault("invalid_media")',
        "pass",
        JOBS + "test_output_preset_dimensions_are_verified_before_admission",
    ),
    (
        "metadata-inspection",
        "exports.py",
        'raise Fault("source_changed")',
        "pass",
        JOBS + "test_inspection_checks_media_and_metadata_without_changing_history",
    ),
    (
        "event-ring",
        "exports.py",
        "del self.events[:-64]",
        "pass",
        JOBS + "test_progress_event_ring_and_sequence_are_bounded",
    ),
    (
        "faststart-offsets",
        "mp4.py",
        "value = struct.unpack_from(fmt, result, offset)[0] + delta",
        "value = struct.unpack_from(fmt, result, offset)[0]",
        UNIT + "test_faststart_relocates_chunk_offsets_without_reopening_path",
    ),
    (
        "stored-plan-hash",
        "store.py",
        "if digest(plan_body) != plan.sha256:",
        "if False:",
        JOBS + "test_changed_stored_plan_is_not_used_with_old_approved_hash",
    ),
    (
        "postprocess-cancel",
        "mp4.py",
        "if cancelled is not None and cancelled():",
        "if False:",
        UNIT + "test_faststart_cancellation_preserves_source_and_never_finishes",
    ),
    (
        "bounded-lock",
        "store.py",
        "if time.monotonic() >= deadline:",
        "if False:",
        JOBS + "test_store_interprocess_lock_has_bounded_busy_result",
    ),
    (
        "orphan-records",
        "store.py",
        'raise Fault("corrupt_state")',
        "pass",
        JOBS + "test_orphan_records_in_corrupt_ledger_are_preserved_and_rejected",
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    originals = {PACKAGE / name: (PACKAGE / name).read_bytes() for _, name, *_ in CASES}
    hashes = {
        str(path.relative_to(REPO)): hashlib.sha256(data).hexdigest()
        for path, data in originals.items()
    }
    results = []
    try:
        for name, filename, needle, replacement, test in CASES:
            path = PACKAGE / filename
            original = originals[path]
            if needle not in original.decode():
                raise RuntimeError("mutation anchor missing: " + name)
            if needle.startswith("raise Fault("):
                mutant = original.decode().replace(needle + "\n", replacement + "\n")
            else:
                mutant = original.decode().replace(needle, replacement)
            compile(mutant, str(path), "exec")
            path.write_text(mutant)
            try:
                run = subprocess.run(
                    [sys.executable, "-B", "-m", "pytest", test, "-q", "-p", "no:cacheprovider"],
                    cwd=REPO,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                    capture_output=True,
                    timeout=30,
                )
                log = run.stdout + run.stderr
                (args.output / (name + ".log")).write_bytes(log)
                invalid = any(
                    word in log
                    for word in [
                        b"SyntaxError",
                        b"ERROR collecting",
                        b"ImportError",
                        b"ModuleNotFoundError",
                        b"NameError",
                        b"UnboundLocalError",
                    ]
                )
                caught = run.returncode == 1 and b"FAILED " in log and not invalid
                results.append(
                    dict(
                        name=name,
                        test=test,
                        exit_code=run.returncode,
                        result="caught" if caught else "invalid-or-survived",
                    )
                )
                if not caught:
                    raise RuntimeError("behavioral mutation survived or invalid: " + name)
            finally:
                path.write_bytes(original)
    finally:
        for path, data in originals.items():
            path.write_bytes(data)
        restored = {
            str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in originals
        }
        report = dict(
            results=results,
            before_sha256=hashes,
            after_sha256=restored,
            restored=hashes == restored,
        )
        (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    if hashes != restored:
        raise SystemExit("source restoration mismatch")
    os.write(1, f"{len(results)} executable mutations caught; hashes restored\n".encode())


if __name__ == "__main__":
    main()
