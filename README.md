<p align="center">
  <img src="assets/social-preview.jpg" alt="Quill: academic writing for AI agents" width="100%">
</p>

# Quill

Quill is a portable academic-writing skill for Codex and Claude Code. It drafts
and revises research prose while preserving claims, assumptions, evidence,
uncertainty, numbers, notation, and citations.

Formerly Pepper. The package, CLI, and skill are now named `quill`, and the
repository is [iamsikun/quill](https://github.com/iamsikun/quill).

Ask naturally: “Polish this methods paragraph,” “Draft an introduction from these
notes,” or “Revise this section in response to the reviewer.” You can also invoke
Quill explicitly as `$quill` in Codex or `/quill` in Claude Code.

## Install

Install once and Quill keeps itself current. Releases come from the `stable` branch,
so work in progress never reaches your agents.

**Any agent (recommended):**

```bash
curl -fsSL https://raw.githubusercontent.com/iamsikun/quill/stable/install.sh | bash
```

This one command:
- clones Quill to `~/.local/share/quill`;
- links the skill into every agent it detects (`~/.claude/skills`, the shared
  `~/.agents/skills` read by Codex, Gemini CLI and Cursor, Copilot, OpenCode);
- installs the `quill` manuscript CLI with [uv](https://docs.astral.sh/uv/), as an
  editable install from that clone, so it follows the same updates;
- schedules a daily background update (launchd on macOS, cron on Linux).

Updates only ever fast-forward to new releases, are skipped quietly when offline, and
never advance a working tree you have edited. Existing skill symlinks pointing
elsewhere are preserved. Restart your agent after installing.

```bash
~/.local/share/quill/install.sh status      # version, links, CLI, last update
~/.local/share/quill/install.sh update      # update now
~/.local/share/quill/install.sh uninstall   # remove owned installation; preserve personal work
```

Add `--no-auto-update` to the install command (`... | bash -s -- --no-auto-update`) to
manage updates yourself, or `--no-cli` to skip the CLI. The skill itself needs no
Python, CLI, or external service for ordinary writing. Without uv, the installer skips
the CLI and says so. If you already installed a `quill` CLI some other way, the installer
leaves it alone. When an update changes the package's metadata or dependencies, the
installer refreshes the CLI.
Failed refreshes are reported and retried by the next update, even if Git is
already current. Reinstalling with `--no-auto-update` disables an existing job.
Uninstall preserves clones with local changes, ignored files, unpublished commits,
or no recorded installer ownership (including older installations).

If you'd rather read the script before running it, clone the repo and run
`./install.sh`.

**Claude Code: plugin marketplace.** This is the alternative to the installer for
Claude Code users; use one or the other, not both.

```bash
claude plugin marketplace add iamsikun/quill#stable
claude plugin install quill@quill
```

Then turn on auto-update: `/plugin` → **Marketplaces** → **quill** → **Enable
auto-update**. Third-party marketplaces have it off by default. Claude Code then picks up
each new release on its own.

**Other options:**
- **`skills` CLI:** `npx skills add iamsikun/quill -g` installs into the agents it
  detects. Update with the CLI's update command, which `npx skills --help` lists.
- **Manual:** symlink `skills/quill` from a clone into your agent's skills folder, then
  `git pull` to update.
- **Project copy for collaborators:** `quill skill install --scope project` copies the
  skill into `.agents/skills/quill` and `.claude/skills/quill` so you can commit it with
  a project. Copies do not update themselves; run `quill skill sync --scope project`
  after updating, and `quill skill uninstall --scope project` to remove them.

| Agent | User-level path | Project-level path |
|---|---|---|
| Claude Code | `~/.claude/skills/quill` | `.claude/skills/quill` |
| Codex | `~/.agents/skills/quill` | `.agents/skills/quill` |
| Gemini CLI | `~/.gemini/skills/quill` or `~/.agents/skills/quill` | `.gemini/skills/quill` or `.agents/skills/quill` |
| Cursor | `~/.cursor/skills/quill` or `~/.agents/skills/quill` | `.cursor/skills/quill` or `.agents/skills/quill` |

Install at only one scope; installing at both may produce duplicate entries. Start a
fresh agent session if Quill has not appeared. Automatic selection depends on the host
and request; explicit invocation is available when you want to select it directly.

The copy commands never change host settings or write `AGENTS.md`/`CLAUDE.md`. They
record ownership in `.quill-install.json` inside the copied skill. Sync updates
unchanged owned files, removes unchanged obsolete files, and preserves unknown files.
Uninstall removes only unchanged owned files. A local conflict blocks the operation on
all selected hosts; resolve it manually and retry. There is no force-overwrite flag.

Preview a copy update before applying it:

```bash
quill skill sync --scope project --dry-run
quill skill sync --scope project --diff
quill skill sync --scope project
```

`--diff` implies a read-only preview and includes conflicting content for manual
resolution. Both flags also work with `skill install` and `skill uninstall`.
A conflict still exits nonzero; no selected host is changed.

Keep personal preferences in a project-owned file such as `.quill/preferences.md`
(or your existing project documentation), outside the canonical and installed
skill folders. Attach that file or explicitly ask your agent to read it when using
Quill; the CLI does not automatically inject it. For example: “Use Quill and read
`.quill/preferences.md` before editing this section.” Sync and uninstall do not
manage this file. To resolve a customized skill-copy conflict, save your changes
separately, restore the affected file to its previously installed contents, inspect
the preview, and retry. Do not edit the ownership checksums.

Inspect the installation without changing it:

```bash
quill doctor
quill doctor --json
```

Diagnostics show CLI and skill versions, installation methods, resolved skill
paths, duplicate scopes, modified managed files, installer update state and
pending refreshes, and available optional tools. Exit status is 1 when an issue
needs attention. Missing LaTeX tools alone do not prevent ordinary writing.

**Moving from an earlier copy install.** If you earlier ran `quill skill install` at
user scope, remove those copies with `quill skill uninstall --scope user` before running
the installer; the installer skips any existing copy rather than overwrite it. Earlier
versions put the Codex copy in `$CODEX_HOME/skills` (default `~/.codex/skills`), which
current Codex no longer reads. Uninstall removes that copy too, and `quill skill install`
refuses to add a second Codex copy until it is gone.

See [CHANGELOG.md](CHANGELOG.md) for what changed in each release.

## Writing behavior

Quill distinguishes restrained copyediting, line editing, structural revision,
drafting, and review-only requests. It works with pasted text, Markdown, LaTeX, and
existing manuscript organization. It does not create a workspace for a paragraph
edit or impose a personal voice by default.

The compact core links to conditional references for editing, drafting, technical
exposition, examples, an optional author style, and managed workspaces. Scientific
fidelity is a constraint; sentence length, voice, repetition, and structure require
judgment. Fluent prose is not a successful revision if it changes the claim.

Literature synthesis from supplied sources is supported. Autonomous literature
search, research execution, venue selection, and submission formatting are outside
the skill's scope. It does not verify research by merely restating its sources.

## Personal writing memory

Personalization is optional and works through ordinary agent tools. Ask “Learn my
writing preferences for this project,” then continue drafting and revising normally.
Quill remembers appropriately scoped editorial feedback, applies relevant lessons
in later sessions, and can explain, correct, retire, or forget them on request.
There are no hooks, background watchers, or agent-specific memory dependencies.

Memory is **off** until enabled. **Apply** uses existing preferences without collecting
new examples; **learn** applies preferences and records useful feedback and baselines.
A current-task instruction can suspend learning without changing the saved mode.
Edits to files between Quill's writes are not attributed to you unless you say so:
the first time it finds such edits, Quill asks once whether they are yours and saves
the answer. Missing storage or an uncertain edit never requires stopping the writing.

Project memory lives in `.quill/style/`, excluded from Git by a store-local ignore
file. Explicitly selected author memory lives in
`~/.config/quill/authors/<author-id>/` (or under `XDG_CONFIG_HOME`), or a custom
location. Projects link author stores instead of copying them; `promote` copies a
chosen project preference into the linked author store. The store contains JSON
records, exact original text, a `history.jsonl` of profile versions, and a readable
`profile.md`. Install, sync, and uninstall do not manage this data. Existing explicit
project preferences remain supported. Quill no longer bundles a personal style
profile; supply your own profile or sample, or let memory learn one.

The skill can use ordinary file tools without the CLI. Optional deterministic helpers
make comparison, deduplication, revision checks, and recovery easier for agents:

```bash
quill style init --mode learn
quill style context --section introduction --audience economics
quill style harvest sections/intro.tex
quill style configure --revision-author sikun --expected-revision 3
quill style show
```

`harvest` aligns the changed paragraphs against Quill's last snapshot and flags
edits to numbers, citations, references, or mathematics. The agent uses `record` to
save an interpreted JSON update and `snapshot` after writing a passage. Mutations
require the current `--expected-revision` from `show` or `context`. `configure`
changes mode, author links, or the declared revision author; `history`, `restore`,
`forget`, `promote`, and `export` provide inspection, recovery, removal, reuse
across projects, and portable Markdown. A crashed writer's lock is recovered
automatically.
Commands return JSON by default except `export`, which writes Markdown to stdout.
Use `quill style COMMAND --help` for arguments. The CLI never calls a model or
decides what a human revision means.

Manually edited profiles are preserved until the agent reconciles the changes.
Forgetting purges associated text from managed history and snapshots and reconsiders
dependent rules; it cannot delete exported copies, backups, or source manuscripts.
Without persistent writable storage, Quill can use supplied preferences and return
a portable Markdown memory document when requested. It does not claim that another
session or agent has access to unsaved memory.

See the self-contained [personalization workflow](skills/quill/references/personalization.md)
and [record format](skills/quill/references/personalization-format.md). The separate
[behavioral evaluation protocol](evals/README.md#personalization) distinguishes
storage integrity, learning behavior, and author-assessed writing quality.

## Optional managed manuscript utilities

Writing does not require a `paper/` directory. For a project that benefits from
managed targets and source context:

```bash
quill init
quill new-paper --title "Example paper"
```

`quill init` adds missing configuration and template assets only. Existing files
are preserved. It does not install skills or create manuscript state. The default
`generic` venue creates `paper/manuscript` with a standard article and `plainnat`
bibliography style. Topic, contributions, paper type, and venue are optional; add
`--topic`, repeated `--contribution`, `--paper-type`, or `--venue neurips` as needed.
The generic venue also works with existing configuration files.

Creation refuses an existing target before writing files. Use `--target NAME` to
create another target, or `quill set-target NAME` to select one. Shared context and
the master bibliography are preserved when adding targets. Edit existing metadata
in `paper/<target>/target.yaml`; rerunning creation is not a metadata update.

Import an existing LaTeX manuscript without splitting or rewriting its sources:

```bash
quill import-paper /path/to/main.tex --title "Existing paper"
quill import-paper /path/to/project --title "Another version" --target revision
```

Import preserves the entry-point filename, relative paths, source bytes, nested
inputs, local styles, graphics, and bibliographies reachable through supported
literal commands. A directory with several document entry points requires selecting
the exact `.tex` file. Use `--source-root` when the compilation root differs from
the entry point's parent. Paths escaping that root, unresolved dependencies, and
dynamic paths requiring TeX expansion are rejected before creating a workspace.
Import does not merge bibliographies or copy unrelated project files. The
`--import-mode` flag records review/revision intent; it never rewrites the sources.

New workspaces use `.quill/`. Existing projects with `.pepper/config.yaml` keep
using their configuration and templates in place, including when running
`quill init`. If both directories have a configuration, `.quill/` takes precedence.

Retained utilities include `new-paper`, `import-paper`, `set-target`,
`create-journal-version`, `sync-context`, `log-decision`, `clear-session`,
`assemble`, `camera-ready`, `validate`, and `version`. Assembly regenerates a managed
`main.tex`; use it only when regeneration is intended. Imported targets retain
their original entry point during assembly. Compilation requires a
LaTeX installation. Template shells and venue metadata are starting points, not
verified current submission requirements. Obtain official style files separately.

Existing projects keep their `paper/state.yaml`, shared context, source map,
bibliography, session decisions, and target files. The skill reads relevant context
without requiring it for self-contained writing.

`quill validate` checks each target's reachable document separately for missing
inputs, graphics, bibliographies, undefined references/citations, and duplicate
labels. Use `--target NAME` to limit the check. Comments and verbatim examples are
excluded. These are static checks of common literal LaTeX commands, not execution
of TeX macros or verification of venue requirements. Warnings identify unsupported
constructs; use compilation to verify the actual document.

`quill camera-ready` builds a fresh package containing the manuscript and its
dependencies. It copies auxiliary template styles, never the template's example
manuscript, and rejects unresolved or unsupported dependencies. A failed check or
build leaves the previous package and target stage intact. `--compile` uses
`latexmk` when available, with a `pdflatex`/BibTeX fallback. The generated
`VERIFICATION.md` distinguishes static checks from successful compilation.

## Migrating from Pepper

Version 0.2 is a breaking restructure. Install the new utility and skill, then run
these commands **inside each legacy project you intend to migrate**:

```bash
quill migrate --dry-run
quill migrate
```

Migration removes only known legacy adapter files whose ownership and unchanged
content are confirmed by `.pepper/install-manifest.json`. It removes Pepper-marked
blocks from `AGENTS.md` and `CLAUDE.md`, preserving bytes outside those blocks.
Ambiguous markers are reported and left unchanged.

Customized or unowned adapters remain and are reported for manual resolution.
Unchanged safe removals still proceed when other files conflict; the command exits
nonzero so unresolved conflicts are visible. Settings are deleted only when the
entire file is unchanged and manifest-owned. Manuscripts, project configuration,
templates, custom agents, and unrelated settings remain intact. Without a legacy
manifest, migration cannot establish ownership of adapter files. Review reported
files yourself rather than deleting a whole `.claude` directory.

| Removed interface | Replacement |
|---|---|
| `pepper install`, `pepper sync` | `install.sh` (user level) or `quill skill install`/`sync --scope project`; use `quill init` for project assets |
| `draft-paper`, `draft-section`, `edit-section`, `review-paper`, `revise-paper`, `polish`, `workflow-brief` | Ask the host to use Quill and perform the writing directly |
| `literature-search` | Use your host's research tools; supply relevant sources to Quill |
| Generated specialist agents and slash-command wrappers | One portable `quill` skill |
| `dev-sync-root` | Edit the canonical skill directly; there are no generated adapter mirrors |

Existing installations of the earlier `pepper` Python package or skill are not
renamed automatically. Install Quill, then remove the old package or skill through
the tool that installed it after preserving any customizations. Historical
evaluation records retain the Pepper name and original prompts.

## Development and evaluation

The source skill lives in `skills/quill`; the wheel embeds the same folder.
Backend assets remain under `src/quill/assets`. Do not maintain host-specific
copies of the writing instructions.

```bash
uv sync
uv run pytest -q
uv build
QUILL_WHEEL="$PWD/dist/quill-0.5.0-py3-none-any.whl" uv run pytest -q
```

`uv run python scripts/validate.py` checks the skill against the Agent Skills spec and
confirms that the version agrees across `SKILL.md`, `.claude-plugin/plugin.json`,
`pyproject.toml`, and `src/quill/__init__.py`. Release steps are in
[AGENTS.md](AGENTS.md#releasing).

Tests cover installed content and references, ownership protection, migration, and
managed utilities. `evals/README.md` describes the 16 synthetic behavioral cases,
three-arm comparison, and fresh-session discovery checks. Behavioral results are
recorded separately from mechanical tests; neither a valid manifest nor a fluent
answer establishes improved human comprehension.
See [the evaluation results](evals/RESULTS.md) for the actual host checks and their
limitations.

## License

MIT. See [LICENSE](LICENSE).
