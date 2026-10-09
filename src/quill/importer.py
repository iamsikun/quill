from __future__ import annotations

from pathlib import Path

from .latex import dependency_graph, source_text
from .workspace import initialize_workspace


def _resolve_main_tex(source: Path) -> Path:
    if source.is_file():
        if source.suffix != ".tex":
            raise ValueError("select a .tex entry point")
        return source
    candidates = [path for path in sorted(source.rglob("*.tex"))
                  if not any(part.startswith(".") for part in path.relative_to(source).parts)
                  and "\\documentclass" in source_text(path.read_text(errors="replace"))]
    if len(candidates) != 1:
        raise ValueError(f"found {len(candidates)} document entry points under {source}; pass the exact .tex file")
    return candidates[0]


def import_paper(
    repo_root: Path, *, source: Path, title: str, topic: str = "",
    contributions: list[str] | None = None, venue_key: str = "generic",
    paper_type: str = "", import_mode: str = "review", target_name: str | None = None,
    source_root: Path | None = None,
) -> str:
    """Copy a document and its literal local dependencies without rewriting bytes."""
    source = source.resolve()
    main_tex = _resolve_main_tex(source)
    root = (source_root or (source if source.is_dir() else source.parent)).resolve()
    if not main_tex.is_relative_to(root):
        raise ValueError("entry point must be inside --source-root")
    entrypoint = main_tex.relative_to(root).as_posix()
    graph = dependency_graph(root, entrypoint)
    if graph.errors or graph.warnings:
        raise ValueError("import needs a complete literal dependency graph; no files changed:\n" +
                         "\n".join(graph.errors + graph.warnings))
    payloads = {path.as_posix(): (root / path).read_bytes() for path in sorted(graph.files)}
    return initialize_workspace(
        repo_root, title=title, topic=topic, contributions=contributions or [],
        venue_key=venue_key, paper_type=paper_type,
        stage="outlining" if import_mode == "revise" else "drafting",
        imported_from=str(main_tex), import_mode=import_mode, target_name=target_name,
        manuscript_files=payloads, entrypoint=entrypoint,
    )
