# Rubric for single-turn cases

You are grading anonymous answers to one synthetic academic-writing task. You do not
know which instructions produced any answer. Grade each answer independently against
the task, the source, and the grading fields. Do not reward length or confidence.

For each answer, return:

- `fidelity`: `pass` or `fail`. Fail if the answer changes, invents, or drops any item
  in `must_preserve`, does anything in `must_not`, or makes another consequential
  change to a claim, number, condition, unit, citation, or attribution. A faithful
  answer that is stylistically weak still passes.
- `scope`: `pass` or `fail`. Fail if it ignores the requested output form or editing
  depth, edits text it was told to keep, or rewrites when asked only to audit.
- `checks`: for each item in `rhetorical_checks`, `met`, `partial`, or `not met`.
- `discipline`: 2 if the reply contains only what was requested; 1 if usable after
  removing some unrequested commentary; 0 if it misses the request.
- `effort`: 1 to 5, how little revision the author would still need to make to the
  answer (5 = none). Fidelity failures cap this at 2.
- `reason`: one or two sentences naming the decisive strengths or failures.

Return only JSON: `{"answers": [{"label": ..., "fidelity": ..., "scope": ..., "checks":
[...], "discipline": ..., "effort": ..., "reason": ...}, ...]}` with one entry per
answer, in the order given.
