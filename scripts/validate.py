"""Validate skills/quill against the Agent Skills spec and repo conventions.

Usage: uv run python scripts/validate.py
"""

import json
import re
import sys
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "quill"
ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end]) or {}, text[end + 5 :]


def versions(fields: dict) -> dict[str, str | None]:
    """Every place a release version lives; they must all agree."""
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    init = re.search(r'__version__ = "([^"]+)"', (ROOT / "src" / "quill" / "__init__.py").read_text())
    return {
        "SKILL.md metadata.version": (fields.get("metadata") or {}).get("version"),
        ".claude-plugin/plugin.json": plugin.get("version"),
        "pyproject.toml": project.get("version"),
        "src/quill/__init__.py": init.group(1) if init else None,
    }


def validate() -> list[str]:
    errors: list[str] = []
    text = (SKILL_DIR / "SKILL.md").read_text()
    fields, body = parse_frontmatter(text)

    extra = set(fields) - ALLOWED_FIELDS
    if extra:
        errors.append(f"non-standard frontmatter fields: {sorted(extra)}")
    name = fields.get("name", "")
    if not (1 <= len(name) <= 64 and NAME_RE.match(name)):
        errors.append(f"invalid name: {name!r}")
    if name != SKILL_DIR.name:
        errors.append(f"name {name!r} does not match directory {SKILL_DIR.name!r}")
    desc = fields.get("description", "")
    if not (1 <= len(desc) <= 1024):
        errors.append(f"description length {len(desc)} not in 1..1024")
    if "compatibility" in fields and len(fields["compatibility"]) > 500:
        errors.append("compatibility longer than 500 chars")

    n_lines = text.count("\n") + 1
    if n_lines > 500:
        errors.append(f"SKILL.md has {n_lines} lines (> 500)")

    refs = set(re.findall(r"`(references/[^`]+\.md)`", body)) | set(re.findall(r"\]\((references/[^)]+\.md)\)", body))
    for ref in sorted(refs):
        if not (SKILL_DIR / ref).is_file():
            errors.append(f"broken reference: {ref}")

    found = versions(fields)
    if len(set(found.values())) != 1 or None in found.values():
        errors.append("version mismatch: " + ", ".join(f"{k}={v}" for k, v in found.items()))
    json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    json.loads((ROOT / "evals" / "cases.json").read_text())
    return errors


def main() -> int:
    errors = validate()
    text = (SKILL_DIR / "SKILL.md").read_text()
    fields, body = parse_frontmatter(text)
    print(f"SKILL.md: {text.count(chr(10)) + 1} lines, ~{len(body.split())} words in body, "
          f"description {len(fields.get('description', ''))} chars")
    for ref in sorted((SKILL_DIR / "references").glob("*.md")):
        print(f"  {ref.relative_to(SKILL_DIR)}: {ref.read_text().count(chr(10)) + 1} lines")
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
