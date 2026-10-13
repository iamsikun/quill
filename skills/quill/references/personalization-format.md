# Portable memory format, version 1

Read this only to maintain memory without the `quill style` CLI; the CLI performs
these steps itself. The format is independent of the CLI and host. `state.json` is
authoritative. `profile.md` is a readable view; `text/<sha256>.txt` contains exact
original UTF-8 bytes; `history.jsonl` holds earlier profile versions. `.gitignore`
contains `*`. Personal stores never belong inside the installed
skill. A project may contain just this memory without any manuscript workspace.

## State and transactions

```json
{
  "schema_version": 1,
  "revision": 0,
  "data": {
    "mode": "off",
    "author_store": null,
    "revision_author": null,
    "revision_author_asked": false,
    "evidence": {},
    "preferences": {},
    "snapshots": {}
  },
  "forgotten_ids": [],
  "forgotten_hashes": []
}
```

`mode` is `off`, `apply`, or `learn`. `author_store` is an explicitly selected
absolute path to a different, unlinked store; links are not followed recursively.
`revision_author` is the author ID the author declared for edits found between
agent writes, or null; `revision_author_asked` records that the question was
answered, so it is not asked again.
Automatic collection requires `learn`. `record --author-request` accepts an explicit
request to edit memory using attributed human style/exposition feedback while
preserving an `off` or `apply` mode. It does not authorize collecting manuscript diffs.
Inspecting, configuring, restoring, and forgetting
remain available in other modes. The empty state and current profile need no CLI.

A writer exclusively creates `.lock`, verifies the expected current revision,
and validates the complete proposed state before saving. Write immutable content
files first. When `preferences`, `mode`, or `author_store` change, append one JSON
line `{revision, time, mode, author_store, preferences}` holding the prior values
to `history.jsonl`. Increment `revision` and atomically replace `state.json` using
a same-directory temporary file. Release only a lock you created. The lock records
`pid`, `host`, `time`, and a random `token`. A lock is stale when its process no
longer exists on the same host, or when it is malformed and older than ten minutes;
remove a stale lock once and retry. Memory unavailability must not block writing.
Retain immutable content referenced by current or historical records. A failed
write may leave an unreferenced content file; it must never publish partial metadata.

Regenerate the readable profile only if it still equals the previous generated
view, or its inspected hash has been explicitly acknowledged during reconciliation.
If it differs, preserve its bytes. Restoring revision V uses the earliest history
line with `revision >= V` (or the current preferences when none exists). It
replaces only `preferences`; evidence, snapshots, mode, and author links stay
current. Links to forgotten evidence are dropped and unsupported rules become
`needs-review`. A purge rewrites `history.jsonl` and current data, then removes
unreferenced original text.

Forgetting a record removes it and every record sharing one of its exact passages
(`before`, `after`, `feedback`, or snapshot content). A passage of at least 40
characters is also removed where it is embedded in other passages or snapshots.
`request` and `context` text is removed only when no remaining record uses it.
Forgetting a preference also removes evidence that no other current preference
uses. A remaining rule whose text quotes forgotten material is replaced by a
needs-review placeholder.
Tombstones contain only IDs and hashes and prevent restoration/reingestion of exact
forgotten records. A purge can be retried after an interrupted content-file cleanup.

## Input to `record`

The host supplies editorial interpretation through `evidence` and `preferences`
lists. Either may be omitted. For example:

```json
{
  "evidence": [{
    "id": "intro-feedback-1",
    "kind": "feedback",
    "origin": "human",
    "author": "selected-author",
    "purpose": "exposition",
    "scope": {"section": ["introduction"]},
    "feedback": "In introductions, explain the problem before naming the method.",
    "lineage": "paper-a:introduction:opening"
  }],
  "preferences": [{
    "id": "problem-before-method",
    "text": "In introductions, explain the problem before naming the method; skip this when the problem is already clear nearby.",
    "scope": {"section": ["introduction"]},
    "status": "explicit",
    "support": ["intro-feedback-1"],
    "counter": []
  }]
}
```

IDs use 1–80 letters, digits, underscores, or hyphens, starting with a letter/digit.
Evidence IDs may be omitted; the CLI derives one from the record fingerprint.
Preference IDs are required. Reuse the preference ID when correcting a lesson.
Evidence records are immutable; supply a new record for a correction in attribution.
Record returns duplicate-ID aliases rather than counting an existing example again.

Evidence fields:

- `kind`: `feedback`, `revision`, `selection`, or `observation`.
- `origin`: `human`, `agent`, `mixed`, or `unknown`; human evidence requires `author`.
  For selections, human origin describes the decision, not authorship of the prose.
- `purpose`: `style`, `exposition`, `scientific`, `evidence`, `venue`, `collaborator`,
  or `unknown`.
- `before`, `after`: exact passages; required for revisions, selections, observations.
- `feedback`: required for feedback evidence. `request` and `context` optionally
  preserve the original task and relevant source/paragraph context.
- `source`: manuscript/passage locator; `baseline`: snapshot ID when available.
- `lineage`: stable independent passage/decision identity. Repeated records of the
  same passage share it. Default is `<source>#<first 16 hex digits of the before
  text's hash>` (falling back to feedback, then after text), or the content hash
  when there is no source. Distinct passages in one file therefore count separately.
- `scope`: optional applicability constraints, as below.

Scope keys are `section`, `audience`, `decision`, `genre`, and `project`. Each value
is a nonempty list of strings. All supplied constraints must match the current
task; an empty object is general. Tags use exact matching, so reuse established
tags rather than introducing synonymous spellings for the same scope.

Preferences have `id`, `text` (including qualifications/exceptions), `scope`,
`status`, `support`, and `counter`. Evidence links must resolve within the same
store. Status is `tentative`, `observed`, `explicit`, `retired`, or `needs-review`.
Only explicit and observed preferences enter routine writing context. Explicit
status needs human style/exposition feedback. Observed status needs at least two
eligible examples with distinct lineages and underlying decision content. Those
checks establish provenance prerequisites, not the truth of an inferred lesson.
Changing an explicit preference requires new explicit author feedback in support.
Active preferences use supporting evidence from one attributed author. Coauthor
observations can coexist in a store but must not be combined into an inferred
shared voice; choose the intended author's preference explicitly.

## Stored records and original bytes

For each evidence text field, save UTF-8 bytes at `text/<sha256>.txt` and replace
that field with a `blobs` mapping from field name to its hash. Preserve line endings.
No TeX execution, normalization, or citation rewriting occurs during comparison.

Stored evidence additionally has `id`, `time` (UTC ISO 8601), `content_hash`, and
`fingerprint`. Compute `content_hash` over the before/after/feedback blob mapping.
Compute `fingerprint` over the normalized evidence metadata and blobs, before
adding `id`, `time`, or `fingerprint`. Canonical JSON uses sorted keys, two-space
indentation, unescaped Unicode, and a trailing newline, encoded as UTF-8.
Normalization supplies `scope: {}`, `origin: "unknown"`, `author: null`,
`purpose: "unknown"`, `source: ""`, and `baseline: null` when omitted. The default
lineage is the nonempty source or, otherwise, the content hash. Include those
normalized fields, `blobs`, `lineage`, and `content_hash` when calculating the
fingerprint. Original request/context fields are stored in `blobs` but excluded
from `content_hash`, so changing context alone is not independent revision evidence.

Snapshot records contain `id`, `source`, `blob`, `origin: "agent"`, `parent` (previous
snapshot for that source or null), `sequence` (the resulting store revision), and
`time`. Select the latest baseline by sequence, not dictionary order. Repeating an
unchanged baseline is a no-op. `source` is the file path relative to the project root
when the file is inside the project.

Harvest splits both versions into paragraphs at blank lines, keeping a LaTeX
environment together, and aligns them. Edited paragraphs are paired one-to-one; a
split or merged paragraph stays with its source. Each change becomes a candidate
`{record, touches, moved}`. `record` is ready for `record` input: exact `before` and
`after` text, neighbouring paragraphs as `context`, the baseline ID, and a lineage
from the block's text. With a declared `revision_author` it is a human `revision`
by that author; otherwise an `observation` of unknown origin. `purpose` is always
`unknown` until the host classifies it. `touches` lists changed `math`,
`citation`, `reference`, or `number` tokens. `moved` marks a paragraph that
reappears elsewhere. Harvest never infers editorial intent.

CLI helpers perform these mechanical steps and validate supported status transitions.
Without them, follow the same schema and preserve IDs, references, and user edits.
If available tools cannot safely maintain the store, use a supplied/portable Markdown
profile and disclose that updates have not been persisted in the structured store.
