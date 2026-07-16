# Governed Memory Mutation Transactions

Duplicate/conflict classification, supersession boundaries and current/as-of
semantics are defined by `docs/MEMORY_LIFECYCLE_QUERIES.md`. An admitted plan
with any lifecycle blocker may be inspected, but cannot be applied or settled.

`TSK.OpenAIDatabase.PAM1.0009` provides the local, deterministic mutation waist.
It accepts only `add`, `update`, `retire`, or `dispute` envelopes governed by
`config/memory-mutation.schema.json` and `config/memory-mutation-policy.json`.

## Admission boundary

- Every envelope must bind actor, source, source time, authorization, scope,
  valid time, exact 40-character base SHA, and a stable idempotency key.
- The key is `memory-mutation:` plus SHA-256 of canonical compact JSON for the
  full envelope with `idempotency_key` omitted; changing any target or content
  therefore requires a different key.
- `explicit_user` may become active without another manual review only when the
  envelope records `explicit_user_zero_human` authorization.
- Hash-bound `repository_evidence` may govern project/task facts. `raw_import`
  remains evidence-only and `model_inference` is never persisted.
- Missing or mismatched authorization, stale base, main-branch apply, unknown
  source, path escape, credential-shaped content, or an occupied writer lock
  fails closed before canonical bytes change.

## ChatGPT / host flow

Use one concise, explicit command; the Agent must resolve the memory ID before
update/retire/dispute and must not infer missing scope or authorization:

- `记住：<fact>；scope=<global|project|task|conversation>`
- `更新记忆 <memory-id>：<new fact>`
- `停用记忆 <memory-id>：<reason>`
- `争议记忆 <memory-id>：<reason>`

The trusted host converts the command to one envelope and runs the complete
transaction. There is no daily Issue/manual-review queue. A tool-less model
must return a plan or a fail-closed reason and must not claim a GitHub write.
Inference and raw evidence remain evidence-only.

## Codex candidate-branch flow

1. Start from the exact `main` SHA in the envelope and create the deterministic
   branch printed by the plan under `automation-c/memory-*`.
2. Re-run the plan, then apply only with its exact base and idempotency key:

   ```bash
   python3 scripts/memory.py mutate --envelope <relative.json> \
     --apply --base-sha <exact-base> --idempotency-key <exact-key>
   ```

3. Refresh both generated Agent views, commit the exact candidate, and build the
   redacted transaction marker with:

   ```bash
   python3 scripts/memory_automation_c.py \
     --plan <mutation-plan.json> --head-sha <exact-head-sha>
   ```

4. Open exactly one same-repository non-draft PR. Read-only required CI tests the
   exact head/base pair; trusted default-branch Settlement alone squash-merges
   or closes, then deletes the exact head branch. Never direct-push `main` and
   never create an Issue queue.
5. Replaying the same accepted outcome produces zero canonical writes, no
   second PR, and no second settlement write. Reusing an idempotency-derived
   record ID for different content fails closed.

The deterministic offline acceptance command is:

```bash
python3 scripts/evaluate_memory_automation_c_e2e.py --check
```

It runs exactly seven synthetic scenarios in disposable local Git repositories:
add, update, retire, dispute, duplicate no-op, invalid input, and rejected model
inference. It executes the production mutation CLI, generated-view builder,
five-profile reader, exact transaction marker, pure Settlement policy, local
squash/close/delete, and terminal `0/0/0` audit. It performs zero live network
requests and zero target-repository writes.

`kind=negative_trigger` add/update payloads also follow
`MEMORY_FORGETTING_AND_REFUSAL.md`: only explicit-user or hash-bound
repository evidence may confirm a non-empty, validity-bounded negative
boundary. Silence never becomes a negative fact.

## Current delivery boundary

`TSK.OpenAIDatabase.PAM1.0017` validates the transaction glue and seven-scenario
E2E through the Task Pack's permitted sandbox/test-repository path. The tracked
report is `data/derived/evaluation/memory_gold/reports/automation_c_e2e_v1.json`.
`TSK.OpenAIDatabase.PAM1.0019` still owns production publication and independent
five-profile live acceptance. Until that later gate passes, sandbox commits and
modeled PR state are not claimed as live GitHub mutation evidence.
