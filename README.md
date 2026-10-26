<p align="center">
  <img src="assets/social-preview.jpg" alt="Quill: academic writing for AI agents" width="100%">
</p>

# Quill

Quill helps AI agents such as Claude Code and Codex draft and revise research papers.
It improves how a paper reads without changing what the research says: claims,
assumptions, evidence, uncertainty, numbers, notation, and citations stay intact.

Ask in plain language: “Polish this methods paragraph,” “Draft an introduction from
these notes,” or “Revise this section in response to the reviewer.” You can also
invoke Quill explicitly as `$quill` in Codex or `/quill` in Claude Code.

## What Quill does

- **Edits at the depth you ask for.** A copyedit fixes mechanics and leaves effective
  sentences alone; a line edit improves the flow of sentences and paragraphs; a
  structural revision reshapes an argument; a draft is written from the notes and
  results you supply; a review returns feedback without changing your files.
- **Keeps the science intact.** Quill maintains distinctions such as association
  versus causation, estimate versus estimand, and simulation versus empirical
  evidence. It does not invent results, citations, or limitations. Fluent prose
  that changes a claim counts as a failed revision.
- **States supported findings directly.** Quill makes the strongest case the
  evidence supports: it removes stacked hedges and repeated caveats while keeping
  the conditions that change a finding's meaning.
- **Writes for the reader of the finished paper.** It keeps the main contribution
  prominent, connects each section to the argument before it, and removes the
  habits that make careful prose read like an assistant's work report: defensive
  contrasts, workflow narration, repair notes in captions, code identifiers, and
  generic wrap-ups. Ask it to “remove the AI-like writing” for an audit or a rewrite.
- **Reviews its work before delivering it.** Beyond a short polish, Quill checks the
  finished text against a [checklist](skills/quill/references/checklist.md) in two
  passes: one for meaning and the reader's path through the argument, one for
  expression. For a section or more, a fresh reviewer runs the passes when the
  host supports subagents.
- **Works with your files as they are.** It edits pasted text, Markdown, and LaTeX
  in your existing structure, and needs no setup for a paragraph edit.
- **Learns your writing style, if you ask.** Quill can learn from your feedback and
  from your edits to its text; otherwise it imposes no personal voice. See
  [Personal writing memory](#personal-writing-memory).
- **Manages LaTeX manuscripts, if you want.** An optional CLI sets up, imports,
  validates, and packages manuscripts. See [Manuscript utilities](#manuscript-utilities).

Quill synthesizes literature you supply, but it does not search for literature, run
research, choose venues, or format submissions. It writes from the research you
supply; it does not verify that research.

## Install

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

Restart your agent after installing. Releases come from the `stable` branch, so work
in progress never reaches your agents. If you'd rather read the script before running
it, clone the repo and run `./install.sh`.

**Claude Code plugin (alternative).** Use either the installer or the plugin, not both:

```bash
claude plugin marketplace add iamsikun/quill#stable
claude plugin install quill@quill
```

Then turn on auto-update: `/plugin` → **Marketplaces** → **quill** → **Enable
auto-update**. Third-party marketplaces have it off by default. Claude Code then picks up
each new release on its own.

Other installation methods, project copies for collaborators, update controls, and
diagnostics are described in [Installation details](#installation-details).

## Personal writing memory

Say “Learn my writing style,” then keep writing as usual. Quill learns from two
things you already do: the feedback you give it, and the edits you make to text it
wrote. It applies what it learned in later sessions, never stops to ask about
memory, and tells you in one line when it adds a lesson.

Your profile belongs to you, not to one project. It lives in `~/.config/quill/`
(or `$XDG_CONFIG_HOME/quill/`) as two plain Markdown files:

- `profile.md`: the lessons, grouped by where they apply. Edit it freely; your edits win.
- `examples.md`: the edits and feedback each lesson came from.

Every agent with Quill installed (Claude Code, Codex, Cursor, Gemini CLI, Copilot,
OpenCode) reads and updates this same profile, in any project. To use it on several
machines, sync that folder as you would other dotfiles. Local ChatGPT Work tasks
can also use this profile when file access is permitted. Cloud tasks need an
online, connected computer with local access enabled to use your local profile;
otherwise, attach or paste `profile.md`. An attachment supplies a snapshot and
does not save new lessons back to your local file. See OpenAI's
[local file access documentation](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-local-security).

A preference you state is learned at once. A pattern in your edits is learned once
it appears in two separate passages. Corrections of results, numbers, citations, or
notation never become style lessons. Ask Quill to explain, change, or forget a
lesson, or to pause learning.

A project's `.quill/style/` folder, which Git ignores, holds only what belongs to that
project: Quill's last version of each file it wrote, so it can see your edits, and
an optional `profile.md` for lessons that apply only to that paper. If coauthors also
edit a project's files, say so; Quill records `edits: others` there and learns in
that project only from your feedback in conversation.

Two optional commands help Quill see your edits:

```bash
quill style changes                     # paragraphs you changed since Quill last wrote each file
quill style baseline sections/intro.tex # record Quill's new version after it writes
```

`changes` flags edits that touch numbers, citations, references, or mathematics,
since those are usually corrections rather than style. Without the CLI, Quill still
learns from feedback in conversation.

Because the profile is outside your project, an agent may ask permission the first
time it reads or writes it. To allow it once and for all, add the folder to Claude
Code's `permissions.additionalDirectories` setting, or to Codex's
`[sandbox_workspace_write] writable_roots` in `~/.codex/config.toml` (as an absolute
path). Memory adapts the instructions Quill follows; it does not retrain a model.
See the [personalization workflow](skills/quill/references/personalization.md) and
the [evaluation protocol](evals/README.md#personalization).

## Review utilities

Two optional commands support the review. Neither is needed to write or edit prose.

```bash
quill check sections/intro.tex                     # candidates for the review to judge
quill check sections/intro.tex --baseline --lines 12-30  # also changed numbers, citations, math, out-of-span edits
quill review record sections/intro.tex             # this version passed the review
quill review status                                # which files changed since their last review
```

`quill check` reports style candidates, such as defensive contrasts, stock
scaffolding, commit hashes and workspace narration, code identifiers, and leftover
markers, with the checklist rule each relates to. With `--against FILE` or
`--baseline`, it also reports fidelity guards: changed numbers, citations,
references, and mathematics, and edits outside the `--lines` you authorized. Lint
patterns in your profile's `checks` header are reported too. Every hit is a
candidate for judgment; the counts are not a quality score. Review records live in
the project's `.quill/reviews/`, which Git ignores; any later edit makes a record
stale, and `quill review status` exits nonzero until the file is reviewed again.

In Claude Code you can make the review hard to skip with two opt-in hooks. Add them
to a project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [{"matcher": "Edit|Write",
                     "hooks": [{"type": "command", "command": "quill hook post-edit"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "quill hook stop"}]}]
  }
}
```

After each edit of a manuscript file, `post-edit` gives the agent the `quill check`
candidates and a reminder to review. `stop` asks the agent once to finish the
review before it ends its turn while an edited file has no current review record.
Neither hook edits your files or fails the session.

## Manuscript utilities

Writing needs no setup and no `paper/` directory. For a LaTeX project that benefits
from managed manuscript versions (targets), shared source context, validation, and
submission packages, use the optional CLI:

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

## Installation details

**Updates.** Installer updates only fast-forward to new releases, are skipped quietly
when offline, and never advance a working tree you have edited. Existing skill
symlinks pointing elsewhere are preserved.

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
installer refreshes the CLI. Failed refreshes are reported and retried by the next
update, even if Git is already current. Reinstalling with `--no-auto-update` disables
an existing job. Uninstall preserves clones with local changes, ignored files,
unpublished commits, or no recorded installer ownership (including older installations).

**Other installation methods:**
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
fresh agent session if Quill has not appeared. Whether an agent selects Quill
automatically depends on the host and the request; invoke it explicitly when you want
to be sure.

**Project copies.** The copy commands never change host settings or write
`AGENTS.md`/`CLAUDE.md`. They record ownership in `.quill-install.json` inside the
copied skill. Sync updates unchanged owned files, removes unchanged obsolete files, and
preserves unknown files. Uninstall removes only unchanged owned files. A local conflict
blocks the operation on all selected hosts; resolve it manually and retry. There is no
force-overwrite flag. Preview a copy update before applying it:

```bash
quill skill sync --scope project --dry-run
quill skill sync --scope project --diff
quill skill sync --scope project
```

`--diff` implies a read-only preview and includes conflicting content for manual
resolution. Both flags also work with `skill install` and `skill uninstall`.
A conflict still exits nonzero; no selected host is changed. To resolve a conflict in
a customized copy, save your changes separately, restore the affected file to its
previously installed contents, inspect the preview, and retry. Do not edit the
ownership checksums. Keep personal preferences outside the skill folders; sync and
uninstall do not manage them.

**Diagnostics.** Inspect the installation without changing it:

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

## Migrating from Pepper

Quill was formerly named Pepper. The package, CLI, and skill are now named `quill`,
and the repository is [iamsikun/quill](https://github.com/iamsikun/quill).

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
QUILL_WHEEL="$PWD/dist/quill-0.7.0-py3-none-any.whl" uv run pytest -q
```

`uv run python scripts/validate.py` checks the skill against the Agent Skills spec and
confirms that the version agrees across `SKILL.md`, `.claude-plugin/plugin.json`,
`pyproject.toml`, and `src/quill/__init__.py`. Release steps are in
[AGENTS.md](AGENTS.md#releasing).

Tests cover installed content and references, ownership protection, migration, and
managed utilities. `evals/README.md` describes the 44 synthetic behavioral cases,
the three-arm comparison, the multi-turn session evaluation with file tools,
fresh-session discovery checks, and the separate personalization cases. Behavioral results are recorded separately from mechanical
tests; neither a valid manifest nor a fluent answer establishes improved human
comprehension. See [the evaluation results](evals/RESULTS.md) for the actual host
checks and their limitations.

## License

MIT. See [LICENSE](LICENSE).
