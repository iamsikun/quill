"""Conservative checks for literal LaTeX dependencies; this is not a TeX engine."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


def source_text(text: str) -> str:
    """Hide comments and verbatim examples from dependency/reference checks."""
    text = re.sub(r"\\begin\{(verbatim\*?|lstlisting|minted)\}.*?\\end\{\1\}", "", text, flags=re.S)
    text = re.sub(r"\\verb\*?([^\w\s]).*?\1", "", text)
    lines = []
    for line in text.splitlines():
        for index, character in enumerate(line):
            if character == "%":
                preceding = len(line[:index]) - len(line[:index].rstrip("\\"))
                if preceding % 2 == 0:
                    line = line[:index]
                    break
        lines.append(line)
    return "\n".join(lines)


@dataclass
class LatexGraph:
    files: set[Path] = field(default_factory=set)
    texts: dict[Path, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


_DEPENDENCY = re.compile(
    r"\\(?P<command>input|include|includegraphics|bibliography|addbibresource|"
    r"documentclass|usepackage|RequirePackage|LoadClass|bibliographystyle|"
    r"lstinputlisting|verbatiminput)(?![A-Za-z])\*?\s*(?:\[[^\]]*\]\s*)*"
    r"(?:\{(?P<argument>[^{}]*)\}|(?P<bare>[^\s{}%]+))"
)
_EXTENSIONS = {
    "input": (".tex",), "include": (".tex",),
    "includegraphics": (".pdf", ".png", ".jpg", ".jpeg", ".eps"),
    "bibliography": (".bib",), "addbibresource": (".bib",),
    "documentclass": (".cls",), "LoadClass": (".cls",),
    "usepackage": (".sty",), "RequirePackage": (".sty",),
    "bibliographystyle": (".bst",), "lstinputlisting": (), "verbatiminput": (),
}
_SYSTEM_RESOURCES = {"documentclass", "LoadClass", "usepackage", "RequirePackage", "bibliographystyle"}


def dependency_graph(root: Path, entrypoint: str = "main.tex") -> LatexGraph:
    """Follow literal inputs from the compilation root, retaining relative paths.

    System styles may be provided by TeX. Missing manuscript inputs, graphics and
    bibliographies are errors. Macro-generated paths are reported as unsupported.
    """
    root = root.resolve()
    result = LatexGraph()
    graphics_dirs: list[str] = []

    def resolve(name: str, extensions: tuple[str, ...], searches: list[str]) -> Path | None:
        if not name or any(char in name for char in "\\#{}"):
            result.warnings.append(f"cannot statically resolve dependency {name!r}")
            return None
        if Path(name).is_absolute():
            result.errors.append(f"absolute dependency is not portable: {name}")
            return None
        for directory in searches:
            candidate = root / directory / name
            options = [candidate, *(Path(str(candidate) + extension) for extension in extensions)]
            for path in options:
                if not path.resolve().is_relative_to(root):
                    result.errors.append(f"dependency escapes manuscript root: {name}")
                    return None
                if path.is_file():
                    return path.relative_to(root)
        return None

    def visit(relative: Path, *, parse: bool = True) -> None:
        if relative in result.files:
            return
        result.files.add(relative)
        if not parse:
            return
        text = source_text((root / relative).read_text(encoding="utf-8", errors="replace"))
        result.texts[relative] = text
        for match in re.finditer(r"\\graphicspath\s*\{((?:\s*\{[^{}]*\})+)\s*\}", text):
            graphics_dirs.extend(re.findall(r"\{([^{}]*)\}", match.group(1)))
        if re.search(r"\\(?:subimport|import|subfile|inputminted|includeonly)\b", text):
            result.warnings.append(f"{relative}: import/subfile/minted/includeonly needs a TeX build or manual dependency review")
        for match in _DEPENDENCY.finditer(text):
            command = match.group("command")
            if match.group("bare") and command != "input":
                continue
            argument = (match.group("argument") or match.group("bare") or "").strip()
            names = argument.split(",") if command in {"bibliography", "usepackage", "RequirePackage"} else [argument]
            for name in names:
                name = name.strip()
                before = len(result.errors) + len(result.warnings)
                searches = ["", *graphics_dirs] if command == "includegraphics" else [""]
                path = resolve(name, _EXTENSIONS[command], searches)
                if path is not None:
                    visit(path, parse=command in {"input", "include", "documentclass", "LoadClass", "usepackage", "RequirePackage"})
                elif before == len(result.errors) + len(result.warnings) and command not in _SYSTEM_RESOURCES:
                    result.errors.append(f"{relative}: missing {command} dependency {name!r}")

    entry = resolve(entrypoint, (), [""])
    if entry is None:
        result.errors.append(f"missing manuscript entry point: {entrypoint}")
    else:
        visit(entry)
    return result


def reference_errors(root: Path, graph: LatexGraph) -> list[str]:
    """Check literal reference and citation keys within one document's graph."""
    labels: dict[str, list[str]] = {}
    references: list[tuple[str, str]] = []
    citations: list[tuple[str, str]] = []
    bibkeys: set[str] = set()
    for relative in graph.files:
        if relative.suffix == ".bib":
            bibkeys.update(re.findall(r"@(?!(?:string|comment|preamble)\b)\w+\s*[{(]\s*([^,\s]+)\s*,",
                                      (root / relative).read_text(errors="replace"), flags=re.I))
    for relative, text in graph.texts.items():
        # Local classes/packages can define macros whose labels are parameters.
        if relative.suffix in {".sty", ".cls"}:
            continue
        for key in re.findall(r"\\label\s*\{([^{}]+)\}", text):
            labels.setdefault(key, []).append(str(relative))
        for keys in re.findall(r"\\(?:ref|eqref|pageref|autoref|cref|Cref|vref|nameref)\*?\s*\{([^{}]+)\}", text):
            references.extend((str(relative), key.strip()) for key in keys.split(","))
        for keys in re.findall(r"\\(?:[Cc]ite\w*|[Pp]arencite|[Tt]extcite|[Aa]utocite|footcite|nocite)\*?\s*(?:\[[^\]]*\]\s*)*\{([^{}]+)\}", text):
            citations.extend((str(relative), key.strip()) for key in keys.split(",") if key.strip() != "*")
        bibkeys.update(re.findall(r"\\bibitem\s*(?:\[[^\]]*\]\s*)?\{([^{}]+)\}", text))
    errors = [f"duplicate \\label{{{key}}} in: {', '.join(paths)}" for key, paths in sorted(labels.items()) if len(paths) > 1]
    for kind, used, defined in (("reference", references, labels), ("citation", citations, bibkeys)):
        for location, key in used:
            if not any(char in key for char in "\\#") and key not in defined:
                errors.append(f"{location}: undefined {kind} {key!r}")
    return errors
