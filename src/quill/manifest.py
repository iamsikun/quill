from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(slots=True)
class InstallManifest:
    package_version: str
    installed_at: str
    adapters: list[str]
    managed_files: list[str]
    managed_files_by_scope: dict[str, list[str]]
    hashes: dict[str, str]

    @classmethod
    def create(
        cls,
        package_version: str,
        *,
        adapters: list[str],
        managed_files_by_scope: dict[str, list[str]],
        hashes: dict[str, str],
    ) -> "InstallManifest":
        return cls(
            package_version=package_version,
            installed_at=datetime.now(UTC).isoformat(),
            adapters=sorted(adapters),
            managed_files=sorted(hashes),
            managed_files_by_scope={key: sorted(value) for key, value in managed_files_by_scope.items()},
            hashes=hashes,
        )

    @classmethod
    def load(cls, path: Path) -> "InstallManifest | None":
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            package_version=data["package_version"],
            installed_at=data["installed_at"],
            adapters=sorted(data.get("adapters", ["claude"])),
            managed_files=list(data["managed_files"]),
            managed_files_by_scope={
                key: list(value)
                for key, value in data.get("managed_files_by_scope", {"_core": list(data["managed_files"])}).items()
            },
            hashes=dict(data["hashes"]),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "package_version": self.package_version,
            "installed_at": self.installed_at,
            "adapters": self.adapters,
            "managed_files": self.managed_files,
            "managed_files_by_scope": self.managed_files_by_scope,
            "hashes": self.hashes,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
