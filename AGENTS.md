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
- `skills/quill/` is the installable unit: `install.sh` symlinks that folder into users'
  agents, so keep it self-contained. Its `SKILL.md` frontmatter may only use the six
  standard fields (`name`, `description`, `license`, `compatibility`, `metadata`,
  `allowed-tools`); `name` must stay `quill`, and `description` must stay at or under
  1024 characters. Keep `SKILL.md` under ~500 lines.
- The version lives in four places that must agree: `metadata.version` in `SKILL.md`,
  `.claude-plugin/plugin.json`, `pyproject.toml`, and `src/quill/__init__.py`.
- Validate after editing the skill or manifests: `uv run python scripts/validate.py`,
  `uvx --from skills-ref agentskills validate skills/quill`, and
  `claude plugin validate .`.

## Releasing

Development happens on `main`. Users install from the `stable` branch, and their
installs update automatically: `install.sh` runs a daily fast-forward, and Claude Code
checks the plugin version. Only move `stable` deliberately:

1. Run `uv run pytest -q`, the validators above, and at least one behavioral case from
   `evals/cases.json`.
2. Bump the version in all four places. Use semantic versioning as defined in
   `CHANGELOG.md`. Claude Code only updates a plugin when this version changes.
3. Add an entry to `CHANGELOG.md`.
4. Commit, tag, and publish:
   ```bash
   git tag vX.Y.Z
   git push origin main vX.Y.Z
   git push origin main:stable      # this is the release; it fast-forwards stable
   ```
5. Create the GitHub release so the repository page shows it. Pushing a tag does not:
   ```bash
   gh release create vX.Y.Z --title "Quill X.Y.Z" --notes-file NOTES.md --latest
   ```
   Base the notes on the changelog entry, and report the validation that was run
   along with its limits.

Never force-push `stable`. Installs update with `--ff-only`, so rewriting the branch's
history would leave them stuck on the old version.
