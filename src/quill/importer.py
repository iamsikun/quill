from __future__ import annotations

import re
import shutil
from pathlib import Path

from .workspace import (
    GRAPHIC_EXTENSIONS,
    _load_config,
    _slugify,
    _target_metadata,
    initialize_workspace,
    scan_source_map,
)


def _resolve_main_tex(source: Path) -> Path:
    if source.is_file():
        return source
    candidates = sorted(source.rglob("*.tex"))
    for candidate in candidates:
        text = candidate.read_text(encoding="utf-8", errors="ignore")
        if "\\documentclass" in text and "\\begin{document}" in text:
            return candidate
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f"no .tex files found under {source}")


def _discover_inputs(tex_text: str) -> list[str]:
    matches = re.findall(r"\\(?:input|include)\{([^}]+)\}", tex_text)
    return [match.strip() for match in matches]


def _resolve_include(base_dir: Path, value: str, extensions: tuple[str, ...]) -> Path | None:
    candidate = (base_dir / value).resolve()
    if candidate.exists():
        return candidate
    for extension in extensions:
        with_extension = candidate.with_suffix(extension)
        if with_extension.exists():
            return with_extension
    return None


def _extract_abstract(tex_text: str) -> str | None:
    match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex_text, re.DOTALL)
    if not match:
        return None
    return match.group(1).strip() + "\n"


def _split_monolithic_sections(tex_text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"\\section\{([^}]+)\}", tex_text))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(tex_text)
        title = match.group(1).strip()
        body = tex_text[start:end].strip()
        sections.append((title, body + "\n"))
    return sections


def _section_filename(title: str, audience: str) -> str:
    lowered = title.lower()
    mapping = {
        "abstract": "abstract.tex",
        "introduction": "introduction.tex",
        "related work": "related_work.tex",
        "literature review": "related_work.tex",
        "background": "background.tex",
        "preliminaries": "background.tex",
        "method": "methodology.tex",
        "methodology": "methodology.tex",
        "model": "methodology.tex",
        "theory": "theory.tex",
        "experiment": "experiments.tex",
        "results": "experiments.tex" if audience == "ml" else "empirics.tex",
        "empirics": "empirics.tex",
        "conclusion": "conclusion.tex",
        "discussion": "conclusion.tex",
        "appendix": "appendix_proofs.tex",
        "proof": "appendix_proofs.tex",
    }
    for needle, filename in mapping.items():
        if needle in lowered:
            return filename
    return f"{_slugify(title)}.tex"


def import_paper(
    repo_root: Path,
    *,
    source: Path,
    title: str,
    topic: str,
    contributions: list[str],
    venue_key: str,
    paper_type: str,
    import_mode: str = "review",
) -> str:
    main_tex = _resolve_main_tex(source.resolve())
    config = _load_config(repo_root)
    target = _target_metadata(config, venue_key)
    stage = "outlining" if import_mode == "revise" else "drafting"
    target_name = initialize_workspace(
        repo_root,
        title=title,
        topic=topic,
        contributions=contributions,
        venue_key=venue_key,
        paper_type=paper_type,
        source_map=scan_source_map(repo_root),
        stage=stage,
        imported_from=str(main_tex),
        import_mode=import_mode,
        target_name=target["name"],
    )
    target_root = repo_root / "paper" / target_name
    sections_root = target_root / "sections"
    source_root = main_tex.parent
    tex_text = main_tex.read_text(encoding="utf-8", errors="ignore")

    abstract_text = _extract_abstract(tex_text)
    if abstract_text:
        (sections_root / "abstract.tex").write_text(abstract_text, encoding="utf-8")

    include_paths = [_resolve_include(source_root, item, (".tex",)) for item in _discover_inputs(tex_text)]
    include_tex = [path for path in include_paths if path is not None]
    if include_tex:
        for tex_file in include_tex:
            destination = sections_root / tex_file.name
            shutil.copy2(tex_file, destination)
    else:
        seen: set[str] = set()
        for title_text, body in _split_monolithic_sections(tex_text):
            filename = _section_filename(title_text, str(target["audience"]))
            if filename in seen:
                stem = Path(filename).stem
                counter = 1
                while f"{stem}_{counter}.tex" in seen:
                    counter += 1
                filename = f"{stem}_{counter}.tex"
            seen.add(filename)
            (sections_root / filename).write_text(body, encoding="utf-8")

    bib_contents: list[str] = []
    for bib_file in sorted(source_root.rglob("*.bib")):
        bib_contents.append(bib_file.read_text(encoding="utf-8", errors="ignore").strip())
    merged_bib = "\n\n".join(part for part in bib_contents if part) + ("\n" if bib_contents else "")
    (repo_root / "paper/shared/references-master.bib").write_text(merged_bib, encoding="utf-8")
    (target_root / "references.bib").write_text(merged_bib, encoding="utf-8")

    figure_root = target_root / "figures"
    figure_root.mkdir(parents=True, exist_ok=True)
    figure_matches = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex_text)
    for raw_value in figure_matches:
        resolved = _resolve_include(source_root, raw_value, GRAPHIC_EXTENSIONS)
        if resolved is not None:
            shutil.copy2(resolved, figure_root / resolved.name)

    shutil.copy2(main_tex, target_root / "main.tex")
    return target_name
