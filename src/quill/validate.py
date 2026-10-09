from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .sync import project_assets_dir, safe_path
from .latex import LatexGraph, dependency_graph, reference_errors
from .workspace import _load_yaml


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


def _check_runtime_state(repo_root: Path, result: ValidationResult, target_name: str | None = None) -> None:
    paper_root = repo_root / "paper"
    if not paper_root.exists():
        return
    state_file = paper_root / "state.yaml"
    if not state_file.exists():
        result.errors.append("paper/state.yaml is missing")
        return
    state_data = _load_yaml(state_file)
    active_target = state_data.get("active_target")
    if not active_target:
        result.errors.append("paper/state.yaml is missing active_target")
        return
    if not (paper_root / str(active_target)).exists():
        result.errors.append(f"paper/{active_target} is missing")
    if not (paper_root / "shared/context.md").exists():
        result.warnings.append("paper/shared/context.md is missing")

    targets = state_data.get("targets", {})
    if not isinstance(targets, dict) or active_target not in targets:
        result.errors.append("paper/state.yaml active_target must name a declared target")
        return
    if target_name and target_name not in targets:
        result.errors.append(f"unknown target: {target_name}")
        return
    for name in ([target_name] if target_name else targets):
        target_root = safe_path(paper_root, name)
        metadata_path = safe_path(target_root, "target.yaml")
        if not metadata_path.is_file():
            result.errors.append(f"paper/{name}/target.yaml is missing")
            continue
        metadata = _load_yaml(metadata_path)
        entrypoint = str(metadata.get("entrypoint", "main.tex"))
        entry = safe_path(target_root, entrypoint)
        if entry.is_file():
            graph = dependency_graph(target_root, entrypoint)
        else:
            graph = LatexGraph()
            result.warnings.append(f"paper/{name}/{entrypoint} not assembled; checking section sources only")
            for path in sorted((target_root / "sections").rglob("*.tex")):
                part = dependency_graph(target_root, path.relative_to(target_root).as_posix())
                graph.files.update(part.files)
                graph.texts.update(part.texts)
                graph.errors.extend(part.errors)
                graph.warnings.extend(part.warnings)
            if (target_root / "references.bib").is_file():
                graph.files.add(Path("references.bib"))
            if metadata.get("imported_from") or targets[name].get("stage") == "camera-ready":
                graph.errors.append(f"missing manuscript entry point: {entrypoint}")
        result.errors.extend(f"{name}: {message}" for message in graph.errors + reference_errors(target_root, graph))
        result.warnings.extend(f"{name}: {message}" for message in graph.warnings)
        if targets[name].get("stage") == "camera-ready":
            for relative, text in graph.texts.items():
                if "TODO" in text:
                    result.errors.append(f"paper/{name}/{relative} contains TODO while in camera-ready stage")


def validate_repo(repo_root: Path, *, target_name: str | None = None) -> ValidationResult:
    result = ValidationResult()
    if not (project_assets_dir(repo_root) / "config.yaml").is_file():
        result.errors.append("missing .quill/config.yaml; run quill init for managed workspace utilities")
    try:
        _check_templates(repo_root, result)
        _check_runtime_state(repo_root, result, target_name)
    except (ValueError, OSError, yaml.YAMLError, TypeError, AttributeError) as exc:
        result.errors.append(str(exc))
    return result
