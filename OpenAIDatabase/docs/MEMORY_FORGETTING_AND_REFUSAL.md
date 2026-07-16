# Memory forgetting, negative boundaries and refusal

`TSK.OpenAIDatabase.PAM1.0011 / ACC.OpenAIDatabase.PAM1.0011` makes
forgetting and evidence-aware refusal part of the portable-memory read
contract. It adds no database, vector store, model judge, data copy, history
rewrite, or automatic conflict resolver.

## Current-answer policy

`memory.py query` uses only records that are `active` and effective at
execution time for current answers. `candidate`, `disputed`, `retired`,
expired, and not-yet-valid records are excluded by default.
`--include-inactive` is an explicit audit mode; returned inactive records
remain answer-ineligible.

Every query emits `retrieval_decision`:

- `answer` — verified current records may support a positive assertion.
- `negative_boundary` — confirmed negative memory may support only the
  stated false/no-longer-applicable boundary.
- `historical` — explicit `--as-of` evidence is historical-only and must
  not be presented as current.
- `mixed` — a broad result contains positive records and negative
  boundaries; apply eligibility per record.
- `abstain` — knowledge state is `UNKNOWN`; `missing_conditions` names
  what is required before answering.

Reason priority is unresolved conflict, retired/expired evidence,
candidate/unverified evidence, then insufficient evidence. Absence alone is
never converted into a negative fact.

## Negative memory

A canonical `kind=negative_trigger` record is valid only when:

1. its authority is `explicit_user` or hash-bound
   `repository_evidence`;
2. verification is `verified`;
3. at least one non-empty `negative_triggers` boundary is present; and
4. `valid_time` states when the boundary applies.

The record may be cited to say that a claim is false or no longer applicable.
It cannot justify the opposite claim, cannot be inferred from silence, and
cannot override scope or validity.

## Forgetting-aware metrics

The Task uses the FAMA definition from
[From Recall to Forgetting](https://arxiv.org/abs/2604.20006):

```text
MPA    = satisfied presence criteria / presence criteria
FAA    = satisfied forgetting-absence criteria / forgetting criteria
lambda = N_forget / (N_presence + N_forget)
FAMA   = max(0, MPA - lambda * (1 - FAA))
```

Task-specific deterministic cases must meet:

- critical stale/retired use = `0`;
- mean FAMA >= `0.95`; and
- abstention precision/recall >= `0.90 / 0.90`.

The 160-case Gold benchmark and its required CI gate remain
`TSK.OpenAIDatabase.PAM1.0013/.0014`.

## History and privacy boundary

Retirement means current retrieval exclusion with preserved valid/recorded
history. Public Git commits, closed PRs, clones, forks, caches, and historical
objects may retain prior bytes. Retirement is not a privacy erasure guarantee;
neither is deletion from the current tree. This Task performs no history
rewrite.
