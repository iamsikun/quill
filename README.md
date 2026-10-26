<p align="center">
  <img src="assets/social-preview.jpg" alt="Quill: academic writing for AI agents" width="100%">
</p>

# Quill

Quill helps AI agents such as Claude Code and Codex draft and revise research papers.
It improves how a paper reads without changing what the research says: claims,
assumptions, evidence, uncertainty, numbers, notation, and citations stay intact.

Quill also learns how you write. It notices what you correct in its drafts and what
you say you prefer, keeps those lessons in a profile you can read and edit, and
applies them in later sessions, in every project, and in every agent you use, so
you correct the same things less often.

Quill is a portable [agent skill](https://agentskills.io): a folder of writing
guidance that Claude Code, Codex, Cursor, Gemini CLI, Copilot, and OpenCode load
when you ask for help with a paper. An optional `quill` CLI adds checks for its
review and tools for LaTeX manuscripts.

## An example

Suppose a draft reports a laboratory study in which 180 participants were randomly
assigned to one of two layouts, and reduced distraction is a proposed explanation
that the study did not measure:

> **Draft:** Our results may suggest that layout A could potentially reduce errors,
> which is likely due to reduced distraction.

A fluent rewrite often removes the hedges and, with them, the distinction the
evidence requires:

> **Fluent but wrong:** Layout A reduces errors by reducing distraction.

Quill states the observed result directly and keeps the untested mechanism
qualified:

> **Quill:** Participants assigned to layout A made fewer errors on average than
> those assigned to layout B (2.1 versus 3.4). Reduced distraction may explain this
> difference.

This example is constructed from the skill's own
[editing illustrations](skills/quill/references/examples.md); it is not a quotation
from a real paper.

## What Quill does

- **Keeps the science intact.** Quill maintains distinctions such as association
  versus causation, estimate versus estimand, and simulation versus empirical
  evidence. It does not invent results, citations, or limitations. Fluent prose
  that changes a claim counts as a failed revision.
- **Drafts from your research.** Give it notes, results, and sources, and it writes
  a section or a full manuscript. It writes the parts the material supports and
  points out the gaps instead of filling them with guesses.
- **Edits at the depth you ask for.** A copyedit fixes mechanics and leaves effective
  sentences alone. A line edit improves the flow of sentences and paragraphs. A
  structural revision reshapes an argument, and a review returns feedback without
  changing your files.
- **Revises in response to reviewers.** It resolves the problems a reviewer
  identified while preserving the contributions the evidence supports, and it keeps
  rebuttal commentary out of the manuscript.
- **States supported findings directly.** Quill makes the strongest case the
  evidence supports: it removes stacked hedges and repeated caveats while keeping
  the conditions that change a finding's meaning.
- **Writes for the reader of the finished paper.** It keeps the main contribution
  prominent, gives each section its own job, and connects each passage to the
  argument. It has specific guidance for mathematical exposition, results, literature
  synthesis, tables, and captions.
- **Removes AI-like writing.** Ask it to “remove the AI-like writing” for an audit or
  a rewrite. It removes the habits that make careful prose read like an assistant's
  work report: defensive contrasts, workflow narration, repair notes in captions, code
  identifiers, and generic wrap-ups. It leaves effective prose alone.
- **Learns how you write.** Without a profile, it imposes no personal voice. See
  [Your writing profile](#your-writing-profile).
- **Reviews its work before delivering it.** Beyond a short polish, Quill checks the
  finished text against a [checklist](skills/quill/references/checklist.md) and your
  profile in two passes: one for meaning and the reader's path through the argument,
  one for expression. For a section or more, a fresh reviewer runs the passes when
  the host supports subagents.
- **Works with your files as they are.** It edits pasted text, Markdown, and LaTeX
  in your existing structure, and needs no setup for a paragraph edit.

Quill synthesizes literature you supply, but it does not search for literature, run
research, choose venues, or format submissions. It writes from the research you
supply. It does not verify that research.

## Install

**Any agent (recommended):**

```bash
curl -fsSL https://raw.githubusercontent.com/iamsikun/quill/stable/install.sh | bash
```

The installer links the skill into every agent it detects, installs the optional
CLI with [uv](https://docs.astral.sh/uv/) when uv is available, and keeps both up to
date with a daily background update from the `stable` branch. Restart your agent
afterwards.

**Claude Code plugin (alternative).** Use either the installer or the plugin, not both:

```bash
claude plugin marketplace add iamsikun/quill#stable
claude plugin install quill@quill
```

Then turn on auto-update: `/plugin` → **Marketplaces** → **quill** → **Enable
auto-update**.

[Installing Quill](docs/install.md) covers what the installer does, update controls,
other installation methods, project copies for collaborators, and diagnostics.

## Quick start

Open your paper's project in your agent and ask in plain language:

- “Polish this methods paragraph.”
- “Draft an introduction from `notes.md` and the results in `tables/`.”
- “Revise Section 4 in response to Reviewer 2.”
- “Review the discussion section. Don't edit it.”
- “Remove the AI-like writing from the abstract.”

Whether an agent chooses Quill on its own depends on the host and the request. To be
sure, invoke it as `/quill` in Claude Code or `$quill` in Codex. To start building your writing
profile, say “Learn my writing style,” then keep writing as usual.

## Your writing profile

Quill learns from two things you already do: the feedback you give it, and the edits
you make to text it wrote. It never stops the writing to ask about memory, and it
tells you in one line when it adds or changes a lesson.

Suppose Quill drafts a methods passage and you revise it:

> **Quill:** We introduce the estimator next. It uses repeated measurements to
> separate signal from noise.
>
> **You:** Repeated measurements let us separate signal from noise. We use this
> structure to construct the estimator.

Quill does not save your sentence. It saves the decision behind it: *explain the
enabling idea before naming the method.* The next time it introduces a method, in
this paper or another, it starts from the idea.

A preference you state is learned at once; a pattern in your edits is learned once it
appears in two separate passages. Corrections of results, numbers, citations, or
notation never become style lessons, and decisions that hold for one paper stay with
that project.

The profile is plain Markdown in `~/.config/quill/`, shared by every agent and
project. Edit it freely; your edits win. Ask Quill why a lesson exists, change its
scope, forget it, restore an earlier version, or pause learning. Memory adapts the
instructions Quill follows. It does not retrain a model.

[Your writing profile](docs/personalization.md) covers the profile's files, use across
agents and machines, coauthored projects, and agent permissions.

## Optional CLI

The skill needs no CLI to write or edit. The `quill` CLI adds deterministic support:

| Command | What it does |
|---|---|
| `quill check FILE` | Flags style candidates for the review and, with `--baseline`, changed numbers, citations, and mathematics |
| `quill review record` / `status` | Records which files passed the review and which changed since |
| `quill hook post-edit` / `stop` | Opt-in Claude Code hooks that make the review hard to skip |
| `quill style changes` / `baseline` | Shows Quill your edits to text it wrote |
| `quill new-paper`, `import-paper` | Sets up or imports a LaTeX manuscript without rewriting its sources |
| `quill validate`, `camera-ready` | Checks a LaTeX manuscript statically and builds a submission package |
| `quill doctor` | Inspects the installation |

See [The `quill` CLI](docs/cli.md) for options and behavior.

## Evaluation

Quill is tested on synthetic writing cases and a six-request revision session on a
manuscript with embedded problems. In the latest runs, a plain prompt without Quill
failed the fidelity check on 5 of 23 cases; among other errors, it invented a Monte
Carlo standard error and a policy effect. Quill with its references failed none of
30. These are preliminary grades from a blind model grader, not human readability
results. See [the evaluation results](evals/RESULTS.md) for the full comparisons and
their limitations.

## Development

The source skill lives in `skills/quill`; the wheel embeds the same folder.
Backend assets remain under `src/quill/assets`. Do not maintain host-specific
copies of the writing instructions.

```bash
uv sync
uv run pytest -q
uv build
QUILL_WHEEL="$(ls "$PWD"/dist/quill-*-py3-none-any.whl | tail -n 1)" uv run pytest -q
```

`uv run python scripts/validate.py` checks the skill against the Agent Skills spec and
confirms that the version agrees across `SKILL.md`, `.claude-plugin/plugin.json`,
`pyproject.toml`, and `src/quill/__init__.py`. Release steps are in
[AGENTS.md](AGENTS.md#releasing).

Tests cover installed content and references, ownership protection, migration, and
managed utilities. [`evals/README.md`](evals/README.md) describes the 44 synthetic
behavioral cases, the three-arm comparison, the multi-turn session evaluation with
file tools, fresh-session discovery checks, and the separate personalization cases.
Behavioral results are recorded separately from mechanical tests; neither a valid
manifest nor a fluent answer establishes improved human comprehension.

Quill was formerly named Pepper. See [Migrating from Pepper](docs/migration.md) and
[CHANGELOG.md](CHANGELOG.md) for what changed in each release.

## License

MIT. See [LICENSE](LICENSE).
