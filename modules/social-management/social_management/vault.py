"""Token vault and redacted connection-state persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Protocol

from .models import ConnectionRecord

SERVICE = "HybridCreatorPlatform.social"


class TokenVault(Protocol):
    def set(self, connection_id: str, token: dict) -> None: ...
    def get(self, connection_id: str) -> dict: ...
    def delete(self, connection_id: str) -> None: ...


class KeyringVault:
    def set(self, connection_id: str, token: dict) -> None:
        import keyring

        keyring.set_password(SERVICE, connection_id, json.dumps(token))

    def get(self, connection_id: str) -> dict:
        import keyring

        value = keyring.get_password(SERVICE, connection_id)
        if value is None:
            raise ValueError("connection token is missing from the OS credential manager")
        return json.loads(value)

    def delete(self, connection_id: str) -> None:
        import keyring

        try:
            keyring.delete_password(SERVICE, connection_id)
        except keyring.errors.PasswordDeleteError:
            pass


class MemoryVault:
    def __init__(self) -> None:
        self.values: dict[str, dict] = {}

    def set(self, connection_id: str, token: dict) -> None:
        self.values[connection_id] = dict(token)

    def get(self, connection_id: str) -> dict:
        if connection_id not in self.values:
            raise ValueError("connection token is missing")
        return dict(self.values[connection_id])

    def delete(self, connection_id: str) -> None:
        self.values.pop(connection_id, None)


class ConnectionStore:
    """Atomic public metadata store. OAuth tokens never enter this file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> list[ConnectionRecord]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [ConnectionRecord.model_validate(item) for item in data]

    def put(self, record: ConnectionRecord) -> None:
        records = {item.id: item for item in self.read()}
        records[record.id] = record
        self._write(records.values())

    def delete(self, connection_id: str) -> None:
        records = {item.id: item for item in self.read()}
        if connection_id not in records:
            raise ValueError("unknown connection")
        del records[connection_id]
        self._write(records.values())

    def _write(self, records) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            self.path.parent.chmod(0o700)
        except OSError:
            pass
        payload = json.dumps([item.model_dump(mode="json") for item in records], indent=2)
        handle, temp_name = tempfile.mkstemp(dir=self.path.parent, prefix=".connections-")
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write(payload)
            os.chmod(temp_name, 0o600)
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
