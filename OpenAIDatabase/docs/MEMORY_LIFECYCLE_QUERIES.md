# Memory lifecycle and bitemporal queries

`TSK.OpenAIDatabase.PAM1.0010 / ACC.OpenAIDatabase.PAM1.0010` defines the
deterministic lifecycle boundary for canonical memory records. It adds no
database, service, embedding authority, editable copy, or automatic conflict
resolution.

## Identity and normalization

Lifecycle identity is exactly `memory_key + scope.type + scope.key`.
Normalization applies Unicode NFKC, `casefold`, and Unicode whitespace
collapse while preserving punctuation. The classifier checks, in order:

1. `exact_duplicate` — same identity, kind and exact statement during an
   overlapping valid interval.
2. `normalized_duplicate` — same identity/kind and normalized statement during
   an overlapping valid interval.
3. `overlapping_validity_conflict` — linked lifecycle records with different
   facts and overlapping valid intervals.
4. `same_key_conflict` — unlinked different facts for the same identity and
   overlapping valid intervals.

Embeddings may assist retrieval later, but never uniquely classify or resolve
a duplicate or conflict.

## Time semantics

Valid intervals are half-open: `[valid_time.from, valid_time.to)`. Therefore a
superseded record ending at `T` and its successor starting at `T` never overlap.

- `memory.py query` returns only active records effective at execution time.
- `memory.py query --as-of T` reads truth effective at valid time `T`.
- `memory.py query --as-of T --recorded-as-of R` reads valid-time truth `T` as
  known at recorded time `R`.
- `--recorded-as-of` without `--as-of` fails closed.

Mutation-created lifecycle changes append immutable metadata under
`recorded_time.transitions`. For pre-contract supersession history without a
transition log, audit reconstruction uses the successor's `recorded_at`; if no
bounded reconstruction exists, the query abstains with
`recorded_time_history_incomplete`.

## Update and settlement

An update retires the old active record, closes its valid interval, records a
transition, creates one new active fact, and links both records through
`supersession`. Normalized no-fact updates fail closed. Reversal is another
explicit update, so current and historical truth remain separately queryable.

Any exact/normalized duplicate, overlapping validity conflict, unrepresented
same-key conflict, or unresolved conflict blocks automatic mutation settlement.
The system does not guess a winner; it emits only IDs, counts and hashes and
waits for governed evidence or explicit user authority. Full remote
branch/PR/CI/settlement glue remains `TSK.OpenAIDatabase.PAM1.0017`.
Current-answer eligibility, forgetting, confirmed negative boundaries and
evidence-aware refusal are defined by
`docs/MEMORY_FORGETTING_AND_REFUSAL.md`.
