"""The OBS WebSocket check reports what it found, exits non-zero when it cannot, and reads .env safely.

`obsws-python` is not a test dependency, so a fake stands in for it. The real client was run
against a mock OBS v5 server separately; these tests pin the script's own behaviour (output, exit
codes, `.env` precedence) without a network or a running OBS.
"""

import importlib.util
import logging
import os
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/setup/test_obs_websocket.py"
OBS_VARS = ("OBS_WEBSOCKET_HOST", "OBS_WEBSOCKET_PORT", "OBS_WEBSOCKET_PASSWORD")
SCENES = [{"sceneName": "Starting Soon"}, {"sceneName": "Gameplay"}]


def fake_obsws(connect_error=None, query_error=None):
    """A stand-in for `obsws_python`, plus the kwargs every ReqClient was built with.

    `library.clients` holds the clients that connected, so a test can see whether each was closed.
    """
    built = []
    clients = []

    class ReqClient:
        def __init__(self, **kwargs):
            built.append(kwargs)
            if connect_error is not None:
                raise connect_error
            self.disconnected = False
            clients.append(self)

        def disconnect(self):
            self.disconnected = True

        def get_version(self):
            if query_error is not None:
                raise query_error
            return types.SimpleNamespace(obs_version="31.0.0", obs_web_socket_version="5.5.4")

        def get_current_program_scene(self):
            return types.SimpleNamespace(current_program_scene_name="Gameplay")

        def get_scene_list(self):
            return types.SimpleNamespace(scenes=SCENES)

    library = types.ModuleType("obsws_python")
    library.ReqClient = ReqClient
    library.clients = clients
    return library, built


@pytest.fixture(autouse=True)
def hermetic(monkeypatch):
    """No OBS_WEBSOCKET_* leaks in from the real environment or out of the script's .env loader."""
    monkeypatch.setattr(os, "environ", {k: v for k, v in os.environ.items() if k not in OBS_VARS})
    logger = logging.getLogger("obsws_python")
    level = logger.level
    yield
    logger.setLevel(level)


def load_script(monkeypatch, tmp_path, library):
    """Import the script with `library` as obsws_python (None blocks the import).

    Its .env path is moved into tmp_path so a test can never read the repo's real .env.
    """
    monkeypatch.setitem(sys.modules, "obsws_python", library)
    spec = importlib.util.spec_from_file_location("obs_websocket_check", SCRIPT)
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    monkeypatch.setattr(script, "ENV_FILE", tmp_path / ".env")
    return script


def test_reports_version_scene_and_scene_list(monkeypatch, tmp_path, capsys):
    library, built = fake_obsws()
    script = load_script(monkeypatch, tmp_path, library)

    assert script.main() == 0

    assert capsys.readouterr().out.splitlines() == [
        "connecting to ws://127.0.0.1:4455 ...",
        "  OBS version    : 31.0.0",
        "  WS version     : 5.5.4",
        "  current scene  : Gameplay",
        "  total scenes   : 2",
        "    - Starting Soon",
        "    - Gameplay",
    ]
    assert built == [{"host": "127.0.0.1", "port": 4455, "password": "", "timeout": 5}]


def test_settings_come_from_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("OBS_WEBSOCKET_HOST", "obs.lan")
    monkeypatch.setenv("OBS_WEBSOCKET_PORT", "4466")
    monkeypatch.setenv("OBS_WEBSOCKET_PASSWORD", "hunter2")
    library, built = fake_obsws()
    script = load_script(monkeypatch, tmp_path, library)

    assert script.main() == 0

    assert built == [{"host": "obs.lan", "port": 4466, "password": "hunter2", "timeout": 5}]


def test_env_file_fills_gaps_but_never_overrides_the_environment(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text(
        "# OBS\n\nOBS_WEBSOCKET_HOST=from-file\nOBS_WEBSOCKET_PORT=5555\n"
        "OBS_WEBSOCKET_PASSWORD = from-file\nnot a setting\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OBS_WEBSOCKET_HOST", "from-env")
    library, built = fake_obsws()
    script = load_script(monkeypatch, tmp_path, library)

    assert script.main() == 0

    assert built == [{"host": "from-env", "port": 5555, "password": "from-file", "timeout": 5}]


def test_env_file_values_may_be_quoted_and_the_file_may_start_with_a_bom(monkeypatch, tmp_path):
    # Windows editors save "UTF-8 with BOM"; compose and python-dotenv both accept quoted values.
    (tmp_path / ".env").write_bytes(
        b"\xef\xbb\xbfOBS_WEBSOCKET_HOST=\"quoted.host\"\nOBS_WEBSOCKET_PASSWORD='two words'\n"
    )
    library, built = fake_obsws()
    script = load_script(monkeypatch, tmp_path, library)

    assert script.main() == 0

    assert built[0]["host"] == "quoted.host"
    assert built[0]["password"] == "two words"


def test_unbalanced_quotes_are_left_alone(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("OBS_WEBSOCKET_PASSWORD=\"abc\n", encoding="utf-8")
    script = load_script(monkeypatch, tmp_path, fake_obsws()[0])

    script.load_env_file(tmp_path / ".env")

    assert os.environ["OBS_WEBSOCKET_PASSWORD"] == '"abc'


def test_connect_failure_exits_one_with_a_single_line_on_stderr(monkeypatch, tmp_path, capsys):
    library, _ = fake_obsws(connect_error=ConnectionRefusedError("[Errno 61] Connection refused"))
    script = load_script(monkeypatch, tmp_path, library)

    assert script.main() == 1

    captured = capsys.readouterr()
    assert captured.err == "FAILED to connect: [Errno 61] Connection refused\n"
    assert "OBS version" not in captured.out


def test_closes_the_connection_after_a_successful_check(monkeypatch, tmp_path):
    library, _ = fake_obsws()
    script = load_script(monkeypatch, tmp_path, library)

    assert script.main() == 0

    assert [client.disconnected for client in library.clients] == [True]


def test_closes_the_connection_when_a_query_fails(monkeypatch, tmp_path):
    library, _ = fake_obsws(query_error=RuntimeError("boom"))
    script = load_script(monkeypatch, tmp_path, library)

    assert script.main() == 1

    assert [client.disconnected for client in library.clients] == [True]


def test_query_failure_exits_one(monkeypatch, tmp_path, capsys):
    library, _ = fake_obsws(query_error=RuntimeError("Request GetVersion returned code 600."))
    script = load_script(monkeypatch, tmp_path, library)

    assert script.main() == 1

    assert capsys.readouterr().err == "FAILED to query OBS: Request GetVersion returned code 600.\n"


def test_missing_library_exits_two_and_names_the_requirements_file(monkeypatch, tmp_path, capsys):
    with pytest.raises(SystemExit) as raised:
        load_script(monkeypatch, tmp_path, None)

    assert raised.value.code == 2
    err = capsys.readouterr().err
    assert "scripts/setup/requirements-obs.txt" in err
    assert sys.executable in err


def test_the_librarys_own_error_logging_is_silenced(monkeypatch, tmp_path):
    # obsws-python logs a full traceback to stderr on a refused connection unless told not to.
    load_script(monkeypatch, tmp_path, fake_obsws()[0])

    assert not logging.getLogger("obsws_python.baseclient").isEnabledFor(logging.ERROR)
