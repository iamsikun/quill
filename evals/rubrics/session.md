# Rubric for the long-session revision

You are grading one anonymous multi-turn revision of a synthetic manuscript. You see
the original manuscript, each user request, the assistant's reply to it, and the
manuscript after each turn. You do not know which instructions or tools produced it.

Grade scientific fidelity and scope first, then the writing.

1. `failures`: for each embedded failure listed, give `fixed`, `partial`, `not fixed`,
   `worse`, or `out of scope` (its turn never authorized editing that passage). A
   failure in the review-only turn (T5) is graded on the review: `found` or `missed`.
   A Conclusion failure is then also graded `fixed`/`partial`/`not fixed` from T6.
   Give a short note when the answer is not `fixed` or `found`.
2. `fidelity_errors`: every changed span whose claim, condition, number, notation,
   citation, or evaluation status no longer matches the original or the code notes,
   including invented mechanisms (for example, an unmeasured variance increase) and
   claims that a supplement or destination contains material it was never shown to
   contain. Quote the span. An empty list is a valid answer.
3. `new_defects`: problems the revision introduced that were not in the original:
   new generic sentences, new defensive contrasts, new caveat repetition, broken
   continuity, unexplained terms, or edits that removed a necessary explanation or
   limitation. Quote each.
4. `overcorrection`: changes to effective prose or preservation controls that made
   them worse (for example, deleting a necessary negation, the clipping disclosure,
   the replicate requirement, or snapshot provenance; editing venue checklist text).
5. `continuity`: 1 to 5. Does each revised section open from what precedes it and give
   each analysis a clear role?
6. `contribution_clarity`: 1 to 5. Can a reader of the final abstract and introduction
   state the main result and the evidence for it?
7. `reply_discipline`: for each turn, 2 if the reply gives only what was requested (a
   short note of edits is fine; for T5, the findings), 1 if usable with unrequested
   commentary, 0 if it misses the request.
8. `author_effort`: 1 to 5, how little revision the author would still need (5 = none).
9. `summary`: two or three sentences on the decisive strengths and failures.

Return only JSON with the keys above. `failures` maps failure IDs to
`{"status": ..., "note": ...}`; `reply_discipline` maps turn IDs to integers.
