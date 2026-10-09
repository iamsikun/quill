# Quill development

Quill is a portable academic-writing skill with optional Python manuscript utilities.

- Edit the canonical skill at `skills/quill/SKILL.md` and its conditional references.
- Keep host-independent writing instructions in that folder. Do not regenerate agent
  roles, slash-command wrappers, or project-wide writing instructions.
- The CLI owns deterministic operations. Skill installation and optional project
  initialization are separate. Preserve user modifications during synchronization
  and remove legacy files only when ownership and checksums establish they are unchanged.
- Run `uv run pytest -q` after code changes and `uv build` after packaging changes.
- Behavioral evaluation cases and the comparison protocol live in `evals/`.
  Structural tests do not establish prose quality or automatic invocation rates.
