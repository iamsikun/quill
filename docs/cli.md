# The `quill` CLI

The CLI is optional. The skill writes and edits prose without it. The CLI adds
deterministic checks that support Quill's review and, for LaTeX projects, managed
manuscripts. The [installer](install.md) sets it up with uv.

## Review utilities

```bash
quill check sections/intro.tex                     # candidates for the review to judge
quill check sections/intro.tex --baseline --lines 12-30  # also changed numbers, citations, math, out-of-span edits
quill review record sections/intro.tex             # this version passed the review
quill review status                                # which files changed since their last review
```

`quill check` reports style candidates, such as defensive contrasts, stock
scaffolding, commit hashes and workspace narration, code identifiers, and leftover
markers, with the [checklist](../skills/quill/references/checklist.md) rule each
relates to. With `--against FILE` or `--baseline`, it also reports fidelity guards:
changed numbers, citations, references, and mathematics, and edits outside the
`--lines` you authorized. Lint patterns in your profile's `checks` header are
reported too. Every hit is a candidate for judgment; the counts are not a quality
score. Review records live in the project's `.quill/reviews/`, which Git ignores;
any later edit makes a record stale, and `quill review status` exits nonzero until
the file is reviewed again.

### Claude Code hooks

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

## Writing-profile utilities

`quill style changes` and `quill style baseline` help Quill see your edits to text
it wrote. See [Your writing profile](personalization.md#seeing-your-edits).

## Manuscript utilities

Writing needs no setup and no `paper/` directory. For a LaTeX project that benefits
from managed manuscript versions (targets), shared source context, validation, and
submission packages:

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

### Importing an existing manuscript

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

### Workspaces and other commands

New workspaces use `.quill/`. Projects created under Quill's former name keep their
`.pepper/` configuration; see [Migrating from Pepper](migration.md).

Other utilities are `create-journal-version`, `sync-context`, `log-decision`,
`clear-session`, `assemble`, and `version`. Assembly regenerates a managed
`main.tex`; use it only when regeneration is intended. Imported targets retain
their original entry point during assembly. Compilation requires a LaTeX
installation. Template shells and venue metadata are starting points, not verified
current submission requirements. Obtain official style files separately.

Existing projects keep their `paper/state.yaml`, shared context, source map,
bibliography, session decisions, and target files. The skill reads relevant context
without requiring it for self-contained writing.

### Validation and submission packages

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
