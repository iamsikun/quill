# Changelog

Quill uses semantic versioning:
- **Major** releases change editing or drafting behavior noticeably, or remove CLI commands.
- **Minor** releases add guidance, references, or utilities.
- **Patch** releases make wording fixes.

## 0.3.0 — 2026-10-09

- `install.sh` now installs the `quill` CLI by default as an editable uv tool from the
  clone, refreshes it when an update changes `pyproject.toml`, and removes it on
  uninstall. Use `--no-cli` to skip it. A CLI installed some other way is left alone.

## 0.2.0 — 2026-10-09

First release as Quill (formerly Pepper). Breaking restructure.
- One portable `quill` skill in `skills/quill/` replaces the generated specialist agents,
  slash-command wrappers, and project-wide writing instructions.
- Conditional references for editing, drafting, technical writing, examples, an optional
  author style, and managed workspaces.
- The Python package and CLI are renamed `quill`. `quill migrate` removes unchanged,
  manifest-owned Pepper adapters; `quill init` adds project assets under `.quill/`.
- Behavioral evaluation cases and a three-arm comparison protocol in `evals/`.
- Distribution:
  - `install.sh` with automatic daily updates from the `stable` branch, linking the skill
    into every detected agent
  - Claude Code plugin manifests
  - `quill skill uninstall` for copies made by `quill skill install`
  - user-level Codex copies now go to `~/.agents/skills`, where Codex reads skills,
    instead of `$CODEX_HOME/skills`; uninstall also removes copies at the old location
  - MIT license
