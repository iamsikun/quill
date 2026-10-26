# Changelog

Quill uses semantic versioning:
- **Major** releases change editing or drafting behavior noticeably, or remove CLI commands.
- **Minor** releases add guidance, references, or utilities.
- **Patch** releases make wording fixes.

## Unreleased

- Restore two guardrails dropped when local edits were reconciled: neither brevity
  nor completeness is an editing objective on its own, and a corrected claim is not
  a lesson to always sound more confident.
- Reorganize the README around what Quill does, installation, and a quick start,
  with a worked example and a summary of the evaluation. Installation details, the
  CLI reference, the writing-profile details, and the Pepper migration guide move
  to `docs/`.

## 0.7.0 — 2026-10-26

- Review drafts against the writing guidance before delivery (#6). A new
  checklist gives every checkable rule an ID, a scope, a yes/no question, a
  default action, an exception, and an example, with routing by task and section.
  Beyond a short polish, the work ends with a two-pass review: meaning and the
  reader's path (with a reverse outline), then expression against every routed
  rule. Repairs are limited to flagged spans and rechecked. For a section or more,
  an independent reviewer runs the passes when the host supports subagents. The
  stopping rule now requires passing the review.
- Add guidance for natural scholarly prose and requests to remove AI-like writing
  (#5): workflow narration, repair notes in captions, code identifiers, tutorial
  filler, overloaded names, generic wrap-ups, and editor instructions, with what
  must be preserved and when to delete, relocate, or leave text unchanged.
- Keep the contribution hierarchy visible and choose detail by section (#3);
  explain apparent contradictions where they appear, give headings, displays, and
  notes distinct jobs, structure tables, record snapshot provenance, and check the
  delivered rendering (#4).
- Personal writing memory classifies corrections as author preferences, project
  decisions, scientific corrections, or shared writing-quality repairs; logs
  compliance failures and raises a lesson's enforcement level; lets profile
  `checks` patterns feed `quill check`; and keeps earlier profile versions in
  `history/` (#2, #4, #6).
- Add `quill check`, which reports style candidates and fidelity guards, and
  `quill review record|status`, which records reviewed file versions and reports
  stale reviews. Add opt-in Claude Code hooks (`quill hook post-edit` and `stop`),
  because the evaluation showed the review references were often not read without them.
- Add 23 behavioral cases for #3-#5, a multi-turn session evaluation with file
  tools, traces, preservation controls, and six arms, and a blind grader with
  frozen rubrics. Results are in `evals/RESULTS.md`. These are preliminary model
  judgments on synthetic material.
- Bring in editing guidance developed in a local installation from manuscript
  feedback. Substantial writing starts from the main messages and the evidence
  that earns them, introduces methods through the problems they address, chooses
  connectives by their logical relationship, and judges detail by what it helps
  readers understand. Wording duplicated between the core and the editing
  reference is consolidated.
- Add guidance on conclusions, supporting detail, appendix organization,
  assumptions, notation, and robustness, with four new editing examples.
- Distinguish reference passages from edit targets, verify the rendered artifact
  the user actually sees, and record writing retrospectives without turning local
  corrections into rules.

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
