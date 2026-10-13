from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from importlib import metadata
from importlib.resources import files
from pathlib import Path, PurePosixPath

MANIFEST_PATH = Path(".pepper/install-manifest.json")  # Legacy Pepper ownership, used by migration
MARKER_START = "<!-- pepper:start -->"
MARKER_END = "<!-- pepper:end -->"


@dataclass
class SyncResult:
    written_files: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    planned_changes: list[str] = field(default_factory=list)
    diffs: list[str] = field(default_factory=list)


def package_version() -> str:
    try:
        return metadata.version("quill")
    except metadata.PackageNotFoundError:
        from . import __version__
        return __version__


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if any((candidate / marker).exists() for marker in
               (".quill/config.yaml", ".pepper/config.yaml", "paper/state.yaml", ".git", "pyproject.toml")):
            return candidate
    return current


def project_assets_dir(repo_root: Path) -> Path:
    """Use legacy configuration in place until a project explicitly adopts .quill."""
    for directory in (".quill", ".pepper"):
        if (repo_root / directory / "config.yaml").is_file():
            return repo_root / directory
    return repo_root / ".quill"


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path) -> str:
    return hash_bytes(path.read_bytes())


def safe_path(root: Path, relative: str) -> Path:
    """Resolve a manifest path without traversing links or escaping its owner."""
    part = PurePosixPath(relative)
    if not relative or relative == "." or part.is_absolute() or ".." in part.parts or "\\" in relative or part.as_posix() != relative:
        raise ValueError(f"unsafe managed path: {relative!r}")
    if root.is_symlink():
        raise ValueError(f"refusing symlinked destination: {root}")
    if root.exists() and not root.is_dir():
        raise ValueError(f"parent is not a directory: {root}")
    current = root
    for index, name in enumerate(part.parts):
        current = current / name
        if current.is_symlink():
            raise ValueError(f"refusing symlinked destination: {current}")
        if current.exists() and not current.is_dir() and index < len(part.parts) - 1:
            raise ValueError(f"parent is not a directory: {current}")
    return current


def resource_bytes(node, prefix: str = "") -> dict[str, bytes]:
    assets: dict[str, bytes] = {}
    for child in sorted(node.iterdir(), key=lambda item: item.name):
        relative = f"{prefix}/{child.name}" if prefix else child.name
        if child.name in {".DS_Store", "__pycache__"}:
            continue
        if child.is_dir():
            assets.update(resource_bytes(child, relative))
        else:
            assets[relative] = child.read_bytes()
    return assets


def init_project(repo_root: Path) -> SyncResult:
    """Copy missing backend assets; existing configuration is always user-owned."""
    assets = resource_bytes(files("quill").joinpath("assets"))
    directory = project_assets_dir(repo_root).name
    assets = {relative.replace(".quill/", f"{directory}/", 1): payload
              for relative, payload in assets.items()}
    result = SyncResult()
    writes: list[tuple[Path, bytes]] = []
    for relative, payload in assets.items():
        try:
            destination = safe_path(repo_root, relative)
            if destination.exists():
                if not destination.is_file():
                    result.conflicts.append(relative)
                continue
            writes.append((destination, payload))
        except ValueError as exc:
            result.conflicts.append(str(exc))
    if result.conflicts:
        return result
    for destination, payload in writes:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        result.written_files.append(destination.relative_to(repo_root).as_posix())
    return result
