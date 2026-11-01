"""Load cityscape-generation's `grading` package under a collision-safe
module name. See tests/nature_generation/_load.py for the full reasoning
— this is the same helper, pointed at the other module, so both can be
imported in the same pytest session without one silently shadowing the
other via `sys.modules["grading"]`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_GRADING_DIR = _REPO / "modules" / "cityscape-generation" / "grading"
_UNIQUE_NAME = "hcp_cityscape_grading"


def _load_package():
    if _UNIQUE_NAME in sys.modules:
        return sys.modules[_UNIQUE_NAME]
    spec = importlib.util.spec_from_file_location(
        _UNIQUE_NAME,
        _GRADING_DIR / "__init__.py",
        submodule_search_locations=[str(_GRADING_DIR)],
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules[_UNIQUE_NAME] = package
    spec.loader.exec_module(package)
    return package


def _load_submodule(name: str):
    _load_package()
    full_name = f"{_UNIQUE_NAME}.{name}"
    if full_name not in sys.modules:
        importlib.import_module(full_name)
    return sys.modules[full_name]


tone = _load_submodule("tone")
presets = _load_submodule("presets")
geometry = _load_submodule("geometry")
