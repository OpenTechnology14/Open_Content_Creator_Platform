"""Load nature-generation's `grading` package under a collision-safe
module name.

Both nature-generation and cityscape-generation have a submodule literally
named `grading` (matching their own README.md's documented directory
name in both — not a name either module is free to change). A bare
`sys.path.insert(...); from grading import tone` works fine in isolation,
but if both modules' tests run in the same pytest process, the second
import silently reuses the FIRST module's already-cached `sys.modules
["grading"]` entry instead of loading its own — cityscape's tests would
then be exercising nature's code, an incorrect result nothing would
visibly flag as wrong. Verified this actually happens (not just
theoretically) before writing this loader: `import grading` after both
sys.path entries were inserted returned the *same object* for both.

`importlib` with an explicit, globally-unique module name sidesteps the
collision regardless of import order or which other test files ran first
in the same session.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_GRADING_DIR = _REPO / "modules" / "nature-generation" / "grading"
_UNIQUE_NAME = "hcp_nature_grading"


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
