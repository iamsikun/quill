# Changelog

Quill uses semantic versioning:
- **Major** releases change editing or drafting behavior noticeably, or remove CLI commands.
- **Minor** releases add guidance, references, or utilities.
- **Patch** releases make wording fixes.

## Unreleased

## 0.6.0 — 2026-10-13

- Clarify local ChatGPT Work profile access and attachment snapshots. Exercise
  real profile tools and the changes/baseline loop in isolated Codex and Claude
  projects; establish baselines on first writes and explicitly log new lessons.
- Add optional personal writing memory. Quill learns from the author's feedback and
  from their edits to text it wrote, keeps lessons in a plain, editable
  `~/.config/quill/profile.md` with an `examples.md` log, and applies them in later
  sessions without interrupting the writing. Every agent with Quill installed shares
  the profile; a project may add its own lessons in `.quill/style/profile.md`.
- Add `quill style baseline` and `quill style changes`, which record Quill's last
  version of a file and report the author's paragraph-level edits, flagging changed
  numbers, citations, references, and mathematics.
- Move the bundled personal style profile out of the skill into an evaluation fixture.
- Add personalization evaluation cases and a runner comparing no memory, a static
  profile, and learned memory.

## 0.5.0 — 2026-10-10

- Add earned-confidence guidance: preserve supported conceptual ambition, state
  findings directly within their scope, and correct overclaims locally.
- Align drafting and revision guidance to retain material qualifications while
  reducing repetitive caveats and unsolicited advisory notes.
- Add five behavioral cases and separate scientific fidelity from rhetorical
  effectiveness. Record comparative and repeated-sample evaluations, including
  remaining delivery and fidelity failures; these are preliminary model judgments.

## 0.4.2 — 2026-10-09

- Add the project banner to the README. Writing instructions and CLI behavior are
  unchanged.

## 0.4.1 — 2026-10-09

- Describe Quill consistently across the plugin manifest, marketplace listing, and
  package metadata, and add search keywords and project links. Writing instructions
  and CLI behavior are unchanged.

## 0.4.0 — 2026-10-09

- Preserve manuscript entry points and nested LaTeX dependencies on import and in
  submission archives; never replace a manuscript with a template example.
- Refuse repeated target creation before writing, preserve shared context and
  bibliographies, and retain imported source bytes during assembly.
- Validate literal inputs, graphics, bibliography files, reference/citation keys,
  and duplicate labels separately for each target. Compilation remains a separate check.
- Preserve external skill symlinks and clones with personal work or unproven
  ownership. Retry failed CLI metadata refreshes on subsequent updates and expose
  pending refreshes and failures. Respect external CLI installations.
- Add `quill doctor` with text/JSON diagnostics and `--dry-run`/`--diff` previews for
  skill installation, synchronization, and removal. Document project-owned preferences.
- Add a generic manuscript target requiring only a title, with optional metadata
  and explicit names for additional targets.
- Add regression tests for these workflows, including compilation of an extracted
  submission archive. Writing instructions are unchanged.

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
