# IDS v0.1 STAGE-001 Phase 1 Scope Boundary

## Identity

- Stage: `STAGE-001`
- Phase: `Phase 1`
- Task ID: `IDS-V0_1-STAGE001-P1`
- Acceptance ID: `ACC-STAGE-001`
- Stage title: `IDS 产品命名合同`
- Source stage file: `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-001_IDS产品命名合同.md`
- Source stage file SHA-256: `db3f6828b413d9f537a006058603ac8d1f306470ca8a51395c5815c20d36ebf4`
- Recorded at UTC: `2026-07-02T04:29:53Z`

## Goal

Confirm the repository governance boundary, inputs, outputs, affected paths,
and legacy-name policy for STAGE-001 before any naming implementation starts.

## In Scope For Phase 1

1. Confirm that STAGE-001 uses `IDS / Industrial Data System` as the new
   customer-visible product name.
2. Define the allowed and forbidden modification boundaries for later
   STAGE-001 phases.
3. List affected README, governance, roadmap, script, test, and documentation
   path groups that later phases must inspect or update.
4. Record the rule that old product names may remain only in migration notes,
   historical evidence, compatibility explanations, archive references, or
   rollback context.
5. Record the 10-stage upload rule for the current batch: `STAGE-001` through
   `STAGE-010` must finish, review, and repair before pushing a batch PR to
   GitHub `main`.

## Out Of Scope For Phase 1

- No runtime code changes.
- No backend, frontend, app bundle, sample, schema, migration, database, report,
  or generated output changes.
- No full old-name replacement yet; that belongs to Phase 2 and Phase 3.
- No full repository scan across unrelated projects.
- No dependency install, no `.venv`, no `node_modules`, no data/report/output
  generation, and no `IDS_DATA_ROOT` creation.
- No GitHub push or PR before the current 10-stage batch is complete and
  reviewed.

## Allowed Modification Boundary

Later STAGE-001 phases may modify only files that are needed to enforce the IDS
product naming contract. Candidate path groups are:

- `KM_IDSystem/README.md`
- `KM_IDSystem/AGENTS.md`
- `KM_IDSystem/docs/HANDOFF.md`
- `KM_IDSystem/docs/governance/`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/`
- `KM_IDSystem/功能清单.md`
- `KM_IDSystem/开发记录.md`
- `KM_IDSystem/模型参数文件.md`
- `KM_IDSystem/backend/` only if a customer-visible report, API title, or
  generated document name still exposes an old product name.
- `KM_IDSystem/frontend/` only if a customer-visible UI label still exposes an
  old product name.
- `KM_IDSystem/app_bundle/` only if a launcher, bundle name, or visible app
  metadata still exposes an old product name.
- `KM_IDSystem/scripts/` only if scripts print, install, validate, or generate
  visible product names.
- Existing focused tests or new narrow tests under `KM_IDSystem/**/tests/` when
  they validate the naming contract.

## Forbidden Modification Boundary

STAGE-001 must not:

- Touch unrelated projects or expand sparse checkout to make a global validator
  pass.
- Move, delete, overwrite, or clean original raw data.
- Commit secrets, API keys, database passwords, cloud credentials, local
  runtime data, generated reports, or dependency folders.
- Rewrite historical evidence just to hide legacy names.
- Claim a full legacy-name cleanup until Phase 3 has produced scan evidence.
- Implement any `STAGE-002+` requirement.

## Legacy Name Policy

New customer-visible UI, reports, formal documents, product names, generated
titles, and newly created governance summaries must use `IDS / Industrial Data
System`.

Old names may remain only when the context is one of:

- migration note;
- historical evidence;
- compatibility explanation;
- archive path;
- rollback instruction;
- source provenance for older artifacts.

Phase 1 does not certify that all old names have already been removed. It only
sets the rule that Phase 2 must implement and Phase 3 must verify.

## Inputs

- `AGENTS.md`
- `KM_IDSystem/AGENTS.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE001_ENTRY_CONTRACT.md`
- P0 taskpack stage file for `STAGE-001`

## Outputs

- This Phase 1 boundary document.
- `BATCH001_010_UPLOAD_LOCK.yaml` for the current 10-stage local batch.
- Roadmap/event updates and rendered Chinese entry files.

## Validation Plan

- `check-render --project KM_IDSystem`
- Parse this document and `BATCH001_010_UPLOAD_LOCK.yaml` for required Stage,
  phase, acceptance, batch, and no-upload markers.
- Confirm changed paths remain under `KM_IDSystem/`.
- Do not treat sparse-worktree full governance validation failure as a reason
  to expand unrelated projects.

## Decision

STAGE-001 Phase 1 is a boundary-confirmation phase only. The next run may enter
STAGE-001 Phase 2 to perform the minimum naming implementation slice, but it
must still avoid unrelated projects and must not upload to GitHub until the
`STAGE-001..STAGE-010` batch is complete, reviewed, and repaired.

## Validation Results

- `check-render --project KM_IDSystem`: passed with `drift_count=0`.
- Stage001 Phase1 marker check: passed.
- `events.jsonl` JSONL parse: passed.
- Changed scope check: passed; changed paths remain under `KM_IDSystem/`.
- `git diff --check`: passed.
- `validate --project KM_IDSystem --semantic`: blocked by existing sparse
  worktree omissions for root governance schemas/workflows/hooks and unrelated
  registered project directories. No unrelated project expansion was performed.
