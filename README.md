# Quill

Quill is a portable academic-writing skill for Codex and Claude Code. It drafts
and revises research prose while preserving claims, assumptions, evidence,
uncertainty, numbers, notation, and citations.

Formerly Pepper. The package, CLI, and skill are now named `quill`, and the
repository is [iamsikun/quill](https://github.com/iamsikun/quill).

Ask naturally: “Polish this methods paragraph,” “Draft an introduction from these
notes,” or “Revise this section in response to the reviewer.” You can also invoke
Quill explicitly as `$quill` in Codex or `/quill` in Claude Code.

## Install the skill

Install the optional Python utility from this checkout:

```bash
uv tool install /path/to/quill
quill skill install
```

The default installs a self-contained skill for both hosts at the user level,
making it available across projects. For development, use
`uv tool install -e /path/to/quill`.

```bash
quill skill install --host codex --scope user
quill skill install --host claude --scope user

# Commit a skill to a particular project for collaborators:
quill skill install --host all --scope project

# After upgrading the Python utility:
quill skill sync --host all --scope user
```

| Host | User destination | Project destination |
|---|---|---|
| Codex | `$CODEX_HOME/skills/quill`, defaulting to `~/.codex/skills/quill` | `.agents/skills/quill` |
| Claude Code | `~/.claude/skills/quill` | `.claude/skills/quill` |

Choose the scope you need; installing at both scopes may produce duplicate entries.
The installer never changes host settings or writes `AGENTS.md`/`CLAUDE.md`. It
records ownership in `.quill-install.json` inside the installed skill. Sync updates
unchanged owned files, removes unchanged obsolete files, and preserves unknown
files. A local conflict prevents updates to all selected hosts; resolve it manually
and retry. There is no force-overwrite flag.

You can also copy or install the canonical `skills/quill` folder with your host's
skill installer. The skill itself needs no Python, Quill CLI, or external service
for ordinary writing. References travel with it. Start a fresh host session if
Quill has not appeared. Automatic selection depends on the host and request;
explicit invocation is available when you want to select it directly.

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

## Optional managed manuscript utilities

Writing does not require a `paper/` directory. For a project that benefits from
managed targets and source context:

```bash
quill init
quill new-paper \
  --title "Example paper" \
  --topic "The research question and setting." \
  --contribution "A supported contribution" \
  --venue neurips \
  --paper-type Empirical
```

`quill init` adds missing configuration and template assets only. Existing files
are preserved. It does not install skills or create manuscript state. Use
`quill import-paper --help` to import an existing LaTeX project.

New workspaces use `.quill/`. Existing projects with `.pepper/config.yaml` keep
using their configuration and templates in place, including when running
`quill init`. If both directories have a configuration, `.quill/` takes precedence.

Retained utilities include `new-paper`, `import-paper`, `set-target`,
`create-journal-version`, `sync-context`, `log-decision`, `clear-session`,
`assemble`, `camera-ready`, `validate`, and `version`. Assembly regenerates a managed
`main.tex`; use it only when regeneration is intended. Compilation requires a
LaTeX installation. Template shells and venue metadata are starting points, not
verified current submission requirements. Obtain official style files separately.

Existing projects keep their `paper/state.yaml`, shared context, source map,
bibliography, session decisions, and target files. The skill reads relevant context
without requiring it for self-contained writing.

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
| `pepper install`, `pepper sync` | `quill skill install`, `quill skill sync`; use `quill init` for project assets |
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
QUILL_WHEEL="$PWD/dist/quill-0.2.0-py3-none-any.whl" uv run pytest -q
```

Tests cover installed content and references, ownership protection, migration, and
managed utilities. `evals/README.md` describes the 16 synthetic behavioral cases,
three-arm comparison, and fresh-session discovery checks. Behavioral results are
recorded separately from mechanical tests; neither a valid manifest nor a fluent
answer establishes improved human comprehension.
See [the evaluation results](evals/RESULTS.md) for the actual host checks and their
limitations.
