# Installing Quill

The [README](../README.md#install) gives the recommended one-line installer and the
Claude Code plugin. This page covers what the installer does, updates, other
installation methods, project copies for collaborators, and diagnostics.

## What the installer does

```bash
curl -fsSL https://raw.githubusercontent.com/iamsikun/quill/stable/install.sh | bash
```

The installer:
- clones Quill to `~/.local/share/quill`;
- links the skill into every agent it detects (`~/.claude/skills`, the shared
  `~/.agents/skills` read by Codex, Gemini CLI and Cursor, Copilot, OpenCode);
- installs the `quill` manuscript CLI with [uv](https://docs.astral.sh/uv/), as an
  editable install from that clone, so it follows the same updates;
- schedules a daily background update (launchd on macOS, cron on Linux).

Releases come from the `stable` branch, so work in progress never reaches your
agents. If you'd rather read the script before running it, clone the repo and run
`./install.sh`.

Use either the installer or the Claude Code plugin, not both.

## Updates

Installer updates only fast-forward to new releases, are skipped quietly when
offline, and never advance a working tree you have edited. Existing skill symlinks
pointing elsewhere are preserved.

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

With the Claude Code plugin, turn on auto-update: `/plugin` → **Marketplaces** →
**quill** → **Enable auto-update**. Third-party marketplaces have it off by default.

## Other installation methods

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

## Project copies

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
A conflict still exits nonzero; no selected host is changed. To resolve a conflict in
a customized copy, save your changes separately, restore the affected file to its
previously installed contents, inspect the preview, and retry. Do not edit the
ownership checksums. Keep personal preferences outside the skill folders; sync and
uninstall do not manage them.

## Diagnostics

Inspect the installation without changing it:

```bash
quill doctor
quill doctor --json
```

Diagnostics show CLI and skill versions, installation methods, resolved skill
paths, duplicate scopes, modified managed files, installer update state and
pending refreshes, and available optional tools. Exit status is 1 when an issue
needs attention. Missing LaTeX tools alone do not prevent ordinary writing.

## Moving from an earlier copy install

If you earlier ran `quill skill install` at user scope, remove those copies with
`quill skill uninstall --scope user` before running the installer; the installer
skips any existing copy rather than overwrite it. Earlier versions put the Codex copy
in `$CODEX_HOME/skills` (default `~/.codex/skills`), which current Codex no longer
reads. Uninstall removes that copy too, and `quill skill install` refuses to add a
second Codex copy until it is gone.

To move from Pepper, Quill's former name, see [Migrating from Pepper](migration.md).
