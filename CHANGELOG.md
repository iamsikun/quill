# Changelog

Quill uses semantic versioning:
- **Major** releases change editing or drafting behavior noticeably, or remove CLI commands.
- **Minor** releases add guidance, references, or utilities.
- **Patch** releases make wording fixes.

## Unreleased

- Add optional portable writing memory with project and explicitly linked author
  scopes, three operating modes, and a workflow driven by normal editorial feedback.
- Add deterministic `quill style` helpers for exact capture, comparison, evidence
  recording, bounded context, inspection, restoration, forgetting, and export.
- Protect explicit author corrections, edited profiles, concurrent updates, and
  personal data across skill updates; preserve unknown attribution and scientific scope.
- Add isolated personalization evaluations and regression coverage. No hooks,
  background services, new runtime dependencies, or release changes are required.
- Learn from file revisions: `harvest` aligns changed paragraphs, keeps their context,
  and flags changed numbers, citations, references, and mathematics. An author can
  declare that edits between Quill's writes are theirs (`configure --revision-author`);
  Quill asks once per project.
- Keep memory fast and recoverable: profile history moves to an append-only
  `history.jsonl`, `restore` accepts any past revision and restores preferences only,
  stale locks from crashed writers are recovered, and sources are project-relative.
- Make `forget` precise: short shared text no longer removes unrelated records, and
  forgetting a preference keeps evidence other preferences use.
- Count distinct passages in one manuscript file as independent evidence.
- Add `promote` and a warning when a profile grows past 40 active preferences.
- Move the bundled personal style profile out of the skill into an evaluation fixture.

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
