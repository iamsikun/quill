from __future__ import annotations

import re
import shutil
import subprocess
import textwrap
import tempfile
import zipfile
from pathlib import Path

from .sync import project_assets_dir, safe_path
from .latex import dependency_graph, reference_errors
from .workspace import _load_state, _load_yaml, _save_state, _today, active_target


def _title_from_context(context_path: Path) -> str:
    if not context_path.exists():
        return "Untitled Paper"
    text = context_path.read_text(encoding="utf-8")
    match = re.search(r"## Title\s+(.+)", text)
    return match.group(1).strip() if match else "Untitled Paper"


def _outline_filename_map(outline_path: Path) -> dict[str, str]:
    if not outline_path.exists():
        return {}
    mapping: dict[str, str] = {}
    text = outline_path.read_text(encoding="utf-8")
    for match in re.finditer(r"###\s+.+?([A-Za-z /-]+)\s+\(filename:\s*([^)]+\.tex)\)", text):
        heading = match.group(1).strip().lower()
        filename = match.group(2).strip()
        mapping[heading] = filename
    return mapping


def _ordered_section_inputs(target_root: Path, audience: str) -> list[str]:
    sections_root = target_root / "sections"
    outline_map = _outline_filename_map(target_root / "outline.md")
    ordered: list[str] = []
    custom_candidates = {
        "abstract": outline_map.get("abstract"),
        "introduction": outline_map.get("introduction"),
        "related work": outline_map.get("related work") or outline_map.get("literature review"),
        "background": outline_map.get("background") or outline_map.get("model setup"),
        "methodology": outline_map.get("methodology") or outline_map.get("method"),
        "theory": outline_map.get("theory"),
        "experiments": outline_map.get("experiments") or outline_map.get("empirics"),
        "conclusion": outline_map.get("conclusion"),
        "appendix proofs": outline_map.get("appendix proofs"),
        "appendix experiments": outline_map.get("appendix experiments"),
    }
    default_names = [
        custom_candidates["abstract"] or "abstract.tex",
        custom_candidates["introduction"] or "introduction.tex",
        custom_candidates["related work"] or "related_work.tex",
        custom_candidates["background"] or "background.tex",
        custom_candidates["methodology"] or "methodology.tex",
        custom_candidates["theory"] or "theory.tex",
        custom_candidates["experiments"] or ("experiments.tex" if audience == "ml" else "empirics.tex"),
        custom_candidates["conclusion"] or "conclusion.tex",
        custom_candidates["appendix proofs"] or "appendix_proofs.tex",
        custom_candidates["appendix experiments"] or "appendix_experiments.tex",
    ]
    for name in default_names:
        if (sections_root / name).exists():
            ordered.append(name)
    remaining = sorted(
        path.name for path in sections_root.glob("*.tex") if path.name not in ordered and path.name not in {"abstract.tex"}
    )
    ordered.extend(remaining)
    return ordered


def assemble_paper(repo_root: Path, *, compile_pdf: bool = False, target_name: str | None = None,
                   update_stage: bool = True) -> Path:
    target = target_name or active_target(repo_root)
    target_root = safe_path(repo_root, f"paper/{target}")
    target_data = _load_yaml(target_root / "target.yaml")
    if not target_data:
        raise ValueError(f"missing target metadata: {target_root / 'target.yaml'}")
    if target_data.get("imported_from"):
        entrypoint = str(target_data.get("entrypoint", "main.tex"))
        main_path = safe_path(target_root, entrypoint)
        if not main_path.is_file():
            raise FileNotFoundError(main_path)
        if compile_pdf:
            _run_latex_sequence(target_root, entrypoint)
        return main_path
    title = target_data.get("title") or _title_from_context(repo_root / "paper/shared/context.md")
    audience = str(target_data.get("audience", "ml"))
    ordered_sections = _ordered_section_inputs(target_root, audience)
    section_inputs: list[str] = []
    appendix_inputs: list[str] = []
    for filename in ordered_sections:
        line = f"\\input{{sections/{Path(filename).stem}}}"
        if filename.startswith("appendix_"):
            appendix_inputs.append(line)
        elif filename != "abstract.tex":
            section_inputs.append(line)

    abstract_block = "\\input{sections/abstract}\n" if (target_root / "sections/abstract.tex").exists() else "% Abstract pending\n"
    bibliography_style = target_data.get("bibstyle") or "plainnat"
    template_name = target_data.get("template", "custom")
    template_dir = project_assets_dir(repo_root) / "templates" / template_name
    bibliography = target_root / "references.bib"
    bibliography_block = (f"\\bibliographystyle{{{bibliography_style}}}\n\\bibliography{{references}}"
                          if bibliography.is_file() and bibliography.read_text().strip() else "")
    main_tex = textwrap.dedent(
        f"""\
        % Generated by Quill's deterministic assembler.
        % Target template: {template_name}
        % Copy venue style files into `{template_dir.relative_to(repo_root)}/` before final compilation.
        \\documentclass{{article}}
        \\usepackage[utf8]{{inputenc}}
        \\usepackage[T1]{{fontenc}}
        \\usepackage{{amsmath,amssymb,amsthm}}
        \\usepackage{{graphicx}}
        \\usepackage{{booktabs}}
        \\usepackage{{threeparttable}}
        \\usepackage{{natbib}}
        \\usepackage{{hyperref}}
        \\title{{{title}}}
        \\author{{Anonymous Author(s)}}
        \\date{{}}
        \\begin{{document}}
        \\maketitle
        \\begin{{abstract}}
        {abstract_block.rstrip()}
        \\end{{abstract}}
        {chr(10).join(section_inputs)}
        {bibliography_block}
        """
    )
    if appendix_inputs:
        main_tex += "\n\\appendix\n" + "\n".join(appendix_inputs) + "\n"
    main_tex += "\\end{document}\n"
    main_path = safe_path(target_root, "main.tex")
    main_path.write_text(main_tex, encoding="utf-8")

    if compile_pdf:
        _run_latex_sequence(target_root)
    if update_stage:
        state = _load_state(repo_root)
        state.setdefault("targets", {}).setdefault(target, {})["stage"] = "drafting"
        _save_state(repo_root, state)
    return main_path


def _run_latex_sequence(target_root: Path, entrypoint: str = "main.tex") -> None:
    def run(command: list[str]) -> None:
        try:
            subprocess.run(command, cwd=target_root, check=True, capture_output=True, text=True, timeout=120)
        except subprocess.CalledProcessError as exc:
            raise ValueError(f"LaTeX build failed ({command[0]}):\n{(exc.stdout + exc.stderr)[-4000:]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ValueError("LaTeX build timed out after 120 seconds") from exc

    if shutil.which("latexmk"):
        run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", entrypoint])
        return
    command = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", entrypoint]
    run(command)
    auxiliary = target_root / (Path(entrypoint).stem + ".aux")
    if auxiliary.is_file():
        text = auxiliary.read_text(errors="replace")
        if "\\bibdata" in text and "\\citation" in text:
            run(["bibtex", Path(entrypoint).stem])
    run(command)
    run(command)


def camera_ready(repo_root: Path, *, compile_pdf: bool = False, target_name: str | None = None) -> Path:
    target = target_name or active_target(repo_root)
    target_root = safe_path(repo_root, f"paper/{target}")
    target_data = _load_yaml(target_root / "target.yaml")
    entrypoint = str(target_data.get("entrypoint", "main.tex"))
    if not safe_path(target_root, entrypoint).exists():
        assemble_paper(repo_root, compile_pdf=False, target_name=target, update_stage=False)
    graph = dependency_graph(target_root, entrypoint)
    problems = graph.errors + graph.warnings + reference_errors(target_root, graph)
    for relative in graph.files:
        if relative.as_posix() in {"VERIFICATION.md", "SUBMISSION_NOTES.md", "submission.zip"} or relative.parts[0] == "camera-ready":
            problems.append(f"manuscript dependency conflicts with generated output: {relative}")
    if problems:
        raise ValueError("submission package not created:\n" + "\n".join(problems))
    camera_root = safe_path(target_root, "camera-ready")
    zip_path = safe_path(target_root, "submission.zip")
    with tempfile.TemporaryDirectory(prefix=".quill-package-", dir=target_root) as temporary:
        staging = Path(temporary) / "contents"
        staging.mkdir()
        template_name = str(target_data.get("template", ""))
        if template_name:
            template = safe_path(project_assets_dir(repo_root), f"templates/{template_name}")
            for path in sorted(template.rglob("*")):
                if path.is_file() and path.suffix in {".sty", ".cls", ".bst", ".clo", ".def"}:
                    destination = staging / path.relative_to(template)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, destination)
        for relative in sorted(graph.files):
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target_root / relative, destination)
        # Styles may have their own local inputs. Check the assembled package too.
        packaged = dependency_graph(staging, entrypoint)
        if packaged.errors or packaged.warnings:
            raise ValueError("incomplete submission package:\n" + "\n".join(packaged.errors + packaged.warnings))
        if compile_pdf:
            _run_latex_sequence(staging, entrypoint)
        (staging / "VERIFICATION.md").write_text(
            f"# Camera-Ready Verification\n\n- Target: `{target}`\n- Generated: `{_today()}`\n"
            f"- Main manuscript: `{entrypoint}`\n- Static dependency checks: passed\n"
            f"- Compilation: {'passed' if compile_pdf else 'not requested'}\n", encoding="utf-8")
        (staging / "SUBMISSION_NOTES.md").write_text(
            "# Submission Notes\n\nConfirm current venue requirements, author information, "
            "anonymization mode, and official style files before submission.\n", encoding="utf-8")
        temporary_zip = Path(temporary) / "submission.zip"
        with zipfile.ZipFile(temporary_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(staging.rglob("*")):
                if path.is_file() and path.suffix not in {".aux", ".log", ".blg", ".fls", ".fdb_latexmk", ".out"}:
                    archive.write(path, path.relative_to(staging))
        if camera_root.exists():
            shutil.rmtree(camera_root)
        staging.rename(camera_root)
        temporary_zip.replace(zip_path)

    state = _load_state(repo_root)
    state.setdefault("targets", {}).setdefault(target, {})["stage"] = "camera-ready"
    _save_state(repo_root, state)
    return zip_path
