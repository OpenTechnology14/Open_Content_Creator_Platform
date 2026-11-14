"""Portable import/DTO tests and explicit unsupported-runtime admission.

The absent-fcntl regression runs real product imports in a fresh interpreter. Its finder
blocks only fcntl; it never substitutes product modules or changes the host's os.name.
"""

import os
import signal
from pathlib import Path
import subprocess
import sys
import textwrap


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PARENT = ROOT / "modules/content-creation"
sys.path.insert(0, str(PACKAGE_PARENT))

SCRIPT = r"""
import importlib
import importlib.abc
import json
import os
from pathlib import Path
import sys

if sys.argv[1].startswith('absent-fcntl'):
    class AbsentFcntl(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname == 'fcntl':
                raise ModuleNotFoundError("controlled missing fcntl", name='fcntl')
    assert 'fcntl' not in sys.modules
    sys.meta_path.insert(0, AbsentFcntl())

# These are the actual package files: collection/protocol/schema must import on Windows.
for name in ['models', 'safety', 'store', 'exports', 'sources', 'media', 'worker', 'schema', 'fixture_run', 'mp4']:
    importlib.import_module('production_artifacts.' + name)
from production_artifacts.models import RequestV1, schema_bundle
from production_artifacts.safety import Fault, SafeRoot
from production_artifacts.store import ProductionStore
from production_artifacts.exports import ExportRunner
from production_artifacts.media import ProcessOwner
from production_artifacts.worker import launch_registry
from production_artifacts.sources import InputHandle, reserve, register_finalized_source
from production_artifacts.fixture_run import run as fixture_run
from production_artifacts.safety import identity, hash_fd
from production_artifacts.mp4 import faststart

request = RequestV1.model_validate(dict(schema_version=1,request_id='portable',
    command='production.list',payload={}))
assert request.request_id == 'portable' and schema_bundle()['RequestV1']
unsupported = sys.argv[1].startswith('absent-fcntl') or os.name != 'posix'
if unsupported:
    # Install after all real imports. Any attempted production file/process access fails
    # the test at its actual boundary instead of being mocked into a successful result.
    def no_side_effects(event, args):
        if event in {'open', 'os.mkdir', 'subprocess.Popen'}:
            raise AssertionError('unsupported admission reached ' + event)
    sys.addaudithook(no_side_effects)
    class RootTripwire:
        def __getattribute__(self, name):
            raise AssertionError('unsupported admission accessed root: ' + name)
    operations = {
        'root': lambda: SafeRoot(Path(sys.argv[2]) / 'uncreated'),
        'store': lambda: ProductionStore(RootTripwire(), 'root-one'),
        'export': lambda: ExportRunner(RootTripwire()),
        'registry': lambda: launch_registry(-1),
        'process': lambda: ProcessOwner(sys.executable).run([sys.executable,'-B','-c','raise SystemExit(99)']),
        'dependency': lambda: ProcessOwner(sys.executable).binary(),
        'inspect': lambda: ProcessOwner(sys.executable).inspect(-1),
        'input': lambda: InputHandle.admit(RootTripwire(), 'source.mp4', '0'*64,
            source_profile_id='source',content_profile_id='content',origin='fixture'),
        'source': lambda: register_finalized_source(RootTripwire(),{},{}),
        'reserve': lambda: reserve(RootTripwire(),1),
        'identity': lambda: identity(-1),
        'hash': lambda: hash_fd(-1),
        'faststart': lambda: faststart(-1,-1),
        'fixture': lambda: fixture_run(Path('source.mp4'),'0'*64,Path(sys.argv[2])/'uncreated'),
    }
    for name, operation in operations.items():
        try:
            operation()
        except Fault as error:
            assert error.code == 'platform_unavailable', (name, error.code)
        else:
            raise AssertionError('unsupported operation was admitted: ' + name)
if sys.argv[1] in {'absent-fcntl-cli','native-cli'}:
    from production_artifacts.worker import main
    sys.argv = ['production_artifacts','--registry-fd','-1']
    main()
    raise AssertionError('unsupported CLI returned successfully')
print(json.dumps(dict(imports='ok',schema='ok',unsupported=unsupported)))
"""


def run_probe(tmp_path, mode):
    result = subprocess.run(
        [sys.executable, "-B", "-c", textwrap.dedent(SCRIPT), mode, str(tmp_path)],
        env={**os.environ, "PYTHONPATH": str(PACKAGE_PARENT), "PYTHONDONTWRITEBYTECODE": "1"},
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"imports": "ok"' in result.stdout
    assert not list(tmp_path.iterdir())
    return result.stdout


def test_real_imports_and_fail_closed_admission_without_fcntl(tmp_path):
    assert '"unsupported": true' in run_probe(tmp_path, "absent-fcntl")


def test_native_host_imports_and_windows_unsupported_admission(tmp_path):
    # Runs on actual Windows CI, without its imports or platform being simulated.
    output = run_probe(tmp_path, "native")
    assert ('"unsupported": true' in output) == (os.name != "posix")


def test_portable_worker_help_imports_without_starting_filesystem_runtime(tmp_path):
    result = subprocess.run(
        [sys.executable, "-B", "-m", "production_artifacts", "--help"],
        env={**os.environ, "PYTHONPATH": str(PACKAGE_PARENT), "PYTHONDONTWRITEBYTECODE": "1"},
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "--registry-fd" in result.stdout
    assert not list(tmp_path.iterdir())


def test_unsupported_cli_reports_platform_code_before_reading_registry(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            textwrap.dedent(SCRIPT),
            "native-cli" if os.name == "nt" else "absent-fcntl-cli",
            str(tmp_path),
        ],
        env={**os.environ, "PYTHONPATH": str(PACKAGE_PARENT), "PYTHONDONTWRITEBYTECODE": "1"},
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert result.stderr.strip() == "production worker initialization failed: platform_unavailable"
    assert not list(tmp_path.iterdir())


def test_portable_nested_positive_and_negative_wire_fixtures():
    import json
    from pydantic import ValidationError
    from production_artifacts.models import WIRE_MODELS, schema_bundle

    directory = PACKAGE_PARENT / "production_artifacts/wire"
    positive = json.loads((directory / "roundtrip.json").read_text())
    assert set(positive) == set(WIRE_MODELS)
    for name, value in positive.items():
        assert (
            WIRE_MODELS[name]
            .model_validate_json(json.dumps(value))
            .model_dump(mode="json", exclude_none=True)
            == value
        )
    for case in json.loads((directory / "negative.json").read_text()):
        try:
            WIRE_MODELS[case["model"]].model_validate_json(json.dumps(case["value"]))
        except ValidationError:
            pass
        else:
            raise AssertionError("invalid wire admitted: " + case["name"])
    schema = schema_bundle()
    assert schema["PlanPayload"]["properties"]["job"]["$ref"].endswith("/ExportJobV1")
    assert schema["PlanRecord"]["properties"]["clip_plan"]["$ref"].endswith("/ExportClipPlanV1")


def test_owned_hang_diagnostic_exits_before_outer_deadline_when_trace_stalls(tmp_path):
    # Real controlled local child; no Windows identity or product imports are replaced.
    code = """
import sys,time,faulthandler
from scripts.testing.production_artifacts_diagnostics import SessionDiagnostic
# Optional trace capture can stall; fatal self-exit must remain independent.
def stalled_trace(**kwargs):time.sleep(1)
faulthandler.dump_traceback=stalled_trace
diagnostic=SessionDiagnostic(sys.stderr,0.05)
diagnostic.start()
diagnostic.mark('collection','owned-test')
time.sleep(0.3)
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", textwrap.dedent(code)],
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert (
        result.returncode & 255 == 1 if os.name == "nt" else result.returncode == -signal.SIGALRM
    ), result.stdout + result.stderr
    assert "ORCH04_SESSION_TIMEOUT" not in result.stderr


def test_session_diagnostic_normal_completion_disarms_without_clobbering_pytest(tmp_path):
    code = """
import sys,time
from scripts.testing.production_artifacts_diagnostics import SessionDiagnostic
diagnostic=SessionDiagnostic(sys.stderr,0.1)
diagnostic.start()
diagnostic.close()
time.sleep(0.2)
print('normal-completion')
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", textwrap.dedent(code)],
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0 and "normal-completion" in result.stdout
    assert "disarm-request" in result.stderr and "TIMEOUT" not in result.stderr


def test_session_diagnostic_markers_are_bounded_and_exclude_parameters():
    import io
    from scripts.testing.production_artifacts_diagnostics import SessionDiagnostic, MAX_MARKERS

    stream = io.StringIO()
    diagnostic = SessionDiagnostic(stream)
    for _ in range(MAX_MARKERS + 2):
        diagnostic.mark("test-call", "owned[test-parameter]")
    assert diagnostic.markers == 2048
    assert diagnostic.records.qsize() <= 8
    records = b"".join(diagnostic.records.queue)
    has_parameters = b"test-parameter" in records
    assert not has_parameters


def test_session_plugin_is_inactive_outside_real_hosted_windows():
    from scripts.testing import production_artifacts_diagnostics as diagnostic

    if os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true":
        assert diagnostic._diagnostic is None
