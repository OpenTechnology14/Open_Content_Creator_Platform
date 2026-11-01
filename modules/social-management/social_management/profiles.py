"""Private local creator profiles layered over the committed starter catalog."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import Catalog, SocialProfile


class ProfileStore:
    def __init__(self, path: Path, base: Catalog) -> None:
        self.path = path
        self.base = base

    def read(self) -> list[SocialProfile]:
        if not self.path.exists():
            return []
        values = json.loads(self.path.read_text(encoding="utf-8"))
        return [SocialProfile.model_validate(item) for item in values]

    def catalog(self) -> Catalog:
        return self._merged(self.read())

    def _merged(self, custom: list[SocialProfile]) -> Catalog:
        base_ids = {item.id for item in self.base.profiles}
        if base_ids & {item.id for item in custom}:
            raise ValueError("a custom profile cannot replace a committed starter profile")
        return Catalog.model_validate(
            {
                **self.base.model_dump(mode="json"),
                "profiles": [
                    *[item.model_dump(mode="json") for item in self.base.profiles],
                    *[item.model_dump(mode="json") for item in custom],
                ],
            }
        )

    def put(self, profile: SocialProfile) -> None:
        if profile.id in {item.id for item in self.base.profiles}:
            raise ValueError("a custom profile cannot replace a committed starter profile")
        values = {item.id: item for item in self.read()}
        values[profile.id] = profile
        self._merged(list(values.values()))
        self._write(values.values())

    def delete(self, profile_id: str) -> None:
        values = {item.id: item for item in self.read()}
        if profile_id not in values:
            raise ValueError("unknown custom profile")
        del values[profile_id]
        self._write(values.values())

    def _write(self, profiles) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            self.path.parent.chmod(0o700)
        except OSError:
            pass
        payload = json.dumps([item.model_dump(mode="json") for item in profiles], indent=2)
        handle, temp_name = tempfile.mkstemp(dir=self.path.parent, prefix=".profiles-")
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write(payload)
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
