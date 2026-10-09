from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .sync import project_assets_dir


@dataclass(slots=True)
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _check_templates(repo_root: Path, result: ValidationResult) -> None:
    templates_root = project_assets_dir(repo_root) / "templates"
    if not templates_root.exists():
        result.errors.append(f"{templates_root.relative_to(repo_root)} is missing")
        return
    for venue_dir in sorted(path for path in templates_root.iterdir() if path.is_dir()):
        if not (venue_dir / "template-manifest.yaml").exists():
            result.errors.append(f"{venue_dir.relative_to(repo_root).as_posix()} is missing template-manifest.yaml")
        if not (venue_dir / "main.tex").exists():
            result.warnings.append(f"{venue_dir.relative_to(repo_root).as_posix()} is missing main.tex")


def _check_runtime_state(repo_root: Path, result: ValidationResult) -> None:
    paper_root = repo_root / "paper"
    if not paper_root.exists():
        return
    state_file = paper_root / "state.yaml"
    if not state_file.exists():
        result.errors.append("paper/state.yaml is missing")
        return
    state_data = yaml.safe_load(state_file.read_text(encoding="utf-8")) or {}
    active_target = state_data.get("active_target")
    if not active_target:
        result.errors.append("paper/state.yaml is missing active_target")
        return
    if not (paper_root / str(active_target)).exists():
        result.errors.append(f"paper/{active_target} is missing")
    if not (paper_root / "shared/context.md").exists():
        result.warnings.append("paper/shared/context.md is missing")

    camera_ready = any(
        target_data.get("stage") == "camera-ready"
        for target_data in (state_data.get("targets") or {}).values()
        if isinstance(target_data, dict)
    )
    tex_files = list(paper_root.glob("*/main.tex")) + list(paper_root.glob("*/sections/*.tex"))
    label_locations: dict[str, list[str]] = {}
    for tex_file in tex_files:
        text = tex_file.read_text(encoding="utf-8", errors="ignore")
        rel = tex_file.relative_to(repo_root).as_posix()
        if r"\ref{??}" in text or r"\cite{??}" in text:
            result.errors.append(f"{rel} has unresolved placeholder references")
        if camera_ready and "TODO" in text:
            result.errors.append(f"{rel} contains TODO while in camera-ready stage")
        for match in re.finditer(r"\\label\{([^}]+)\}", text):
            label_locations.setdefault(match.group(1), []).append(rel)
    for label, files in label_locations.items():
        if len(files) > 1:
            result.warnings.append(f"duplicate \\label{{{label}}} in: {', '.join(files)}")


def validate_repo(repo_root: Path) -> ValidationResult:
    result = ValidationResult()
    if not (project_assets_dir(repo_root) / "config.yaml").is_file():
        result.errors.append("missing .quill/config.yaml; run quill init for managed workspace utilities")
    _check_templates(repo_root, result)
    _check_runtime_state(repo_root, result)
    return result
