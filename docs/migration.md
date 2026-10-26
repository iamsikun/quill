# Migrating from Pepper

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

Projects with `.pepper/config.yaml` keep using their configuration and templates in
place, including when running `quill init`. If both `.pepper/` and `.quill/` have a
configuration, `.quill/` takes precedence.
