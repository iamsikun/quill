# Optional managed workspaces

Pasted prose and ordinary manuscript files need no Quill setup. Do not run the
CLI or create project state merely because this skill was selected.

When the project already uses Quill or its predecessor Pepper, read `paper/state.yaml` for the active target,
`paper/shared/context.md` for the source map, and that target's `target.yaml` for
metadata. Read an existing session log, outline, or revision plan only as relevant.
Resolve paths relative to the project, not the installed skill. Missing state must
not prevent a self-contained edit. Preserve the user's current file organization.

For an explicit request to create a managed workspace, first check that the
optional `quill` CLI is available. `quill init` installs configuration and
template assets without installing skills or changing host instructions.
`quill new-paper --help` and `quill import-paper --help` describe required inputs.
Ask for essential missing metadata rather than inventing contributions or a venue.
Do not install software as an incidental step in a prose edit.

Useful deterministic helpers, when the task warrants them:

- `quill set-target TARGET` selects an existing target.
- `quill sync-context` updates managed context from section files.
- `quill log-decision TEXT` records a requested persistent editorial decision.
- `quill validate` checks managed project structure and references; it does not
  certify scientific correctness or readability.
- `quill assemble` regenerates a managed `main.tex`; use only when regeneration
  is intended, since it can replace an existing document shell.

Writing is performed by the current host using this skill. There are no CLI writing
briefs to execute and no required specialist agents. Assembly, compilation, and
submission packaging are separate operations, not automatic consequences of editing.

Existing `.pepper/` configuration and templates remain supported; new projects use
`.quill/`. Do not rename existing manuscript configuration as part of a prose edit.

If legacy Pepper adapters still inject conflicting defaults, explain that
`quill migrate --dry-run` previews their removal and `quill migrate` removes
unchanged, manifest-owned adapters. Do not migrate an unrelated project or discard
customized files. Continue a self-contained writing task when migration is unnecessary.
