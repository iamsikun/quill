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
never touch a copy you have edited. Restart your agent after installing.

```bash
~/.local/share/quill/install.sh status      # version, links, CLI, last update
~/.local/share/quill/install.sh update      # update now
~/.local/share/quill/install.sh uninstall   # remove everything
```

Add `--no-auto-update` to the install command (`... | bash -s -- --no-auto-update`) to
manage updates yourself, or `--no-cli` to skip the CLI. The skill itself needs no
Python, CLI, or external service for ordinary writing. Without uv, the installer skips
the CLI and says so. If you already installed a `quill` CLI some other way, the installer
leaves it alone. When an update changes the package's metadata or dependencies, the
installer refreshes the CLI.

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
QUILL_WHEEL="$PWD/dist/quill-0.3.0-py3-none-any.whl" uv run pytest -q
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
