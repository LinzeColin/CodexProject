---
name: kmfa-dingtalk-attendance-skill
description: Use when operating, reviewing, migrating, automating, or modifying KMFA S19 DingTalk attendance automation, DWS attendance, OneDrive/private runtime attendance archives, repo-scoped attendance skill files, stage-2 shadow payroll consensus, PostgreSQL attendance schema, payroll-baseline preparation, or Codex automation prompts in LinzeColin/CodexProject.
---

# KMFA DingTalk Attendance Skill

## Use First

This skill is the portable, public-safe operating entry for KMFA S19 DingTalk attendance automation.
Use it only with a clone of `LinzeColin/CodexProject` and start from `main`.

Canonical GitHub path:

```text
KMFA/kmfa-dingtalk-attendance-skill/
```

Before acting, read:

1. `references/runbook.md`
2. `references/configuration.md`
3. `references/operating_contract.md` for v0.3 / stage-2 work
4. `references/source_of_truth_contract.md`
5. `KMFA/HANDOFF.md`
6. `KMFA/metadata/dingtalk_attendance/README.md`
7. The exact source or test files you will touch

## Hard Boundaries

- Do not create branches, PRs, issues, or worktrees unless the user explicitly changes this rule.
- Do not commit `.env.local`, webhook URLs, signing keys, app secrets, token values, DWS resolved IDs, SQLite, raw JSON/JSONL/GZ, employee attendance plaintext, report bodies, or OneDrive raw archives.
- Do not run DWS live commands or send DingTalk messages without explicit user authorization in the current thread.
- Live DWS gate env: `KMFA_S19_ALLOW_DWS_COMMANDS`.
- Use `python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only` before any live consideration.
- If changing behavior, use tests first and keep the change narrowly scoped.
- Any skill or automation prompt change must be committed and pushed to GitHub `main` in the same run unless validation fails.
- Local Codex automation state is not Git by itself. The canonical automation prompts must be mirrored under `automation/` in this folder before the local automation is updated.

## Current Attendance Rules

- Automation name: `每日早晚钉钉考勤检查`.
- Timezone: `Asia/Shanghai`.
- Morning run: 08:35. Evening run: 18:15.
- DWS backend is live-only; no sample employees or fixture attendance records are allowed as production data.
- Known no-record people: `张霖泽`, `林全意`; only their own missing records are exempted.
- Rest reminder rule: `REST_REQUIRED_THRESHOLD_DAYS = 23`.
- Rest reminder excluded names: `丁春法`, `李永占`; they are excluded only from `需要休息` and private ledger `rest_required_snapshots`, while all other statuses are still counted normally.
- Effective attendance day: the same natural day has both morning and evening punches.
- Monthly notification rollups reset by natural month.
- For each status section, show everyone when count is 10 or less; otherwise show total count plus Top 10.
- SQLite ledger is a rebuildable private index, not payroll basis and not a wage calculation source.
- Private ledger path: `KMFA/metadata/dingtalk_attendance/private_runtime/attendance_ledger.sqlite`; never commit it.

## Source And Data Boundaries

- Public/repo metadata root: `KMFA/metadata/`.
- DingTalk attendance metadata root: `KMFA/metadata/dingtalk_attendance/`.
- Private runtime root: `KMFA/metadata/dingtalk_attendance/private_runtime/`.
- Long-term private attendance archive root: `/Users/linzezhang/OneDrive/dingtalk_attendance/YYYYMM/`.
- Public GitHub may contain configs, schemas, validators, manifests, redacted status, docs, and deterministic synthetic fixtures.
- Public GitHub must not contain real employee attendance plaintext, raw DingTalk JSON/JSONL/GZ, SQLite databases, webhook URLs, access tokens, app secrets, resolved openDingTalkId/group ids, or report bodies.

When the user says "raw/original data is in `KMFA/metadata`", treat tracked `KMFA/metadata` as the public source-of-truth metadata/config layer. Real private DingTalk raw payloads remain private unless the user explicitly authorizes a different public-safe export.

## Automation Rules

Existing local Codex automation ids:

- Morning: `automation-3`, daily 08:35 Beijing time.
- Evening: `automation-4`, daily 18:15 Beijing time.

Both automation prompts must invoke this skill by name:

```text
$kmfa-dingtalk-attendance-skill
```

If the current agent cannot auto-resolve repo-scoped skills, it must read this file directly and continue with the same rules.

## Stage-2 / Payroll-Baseline Direction

The v0.3 task pack extends the current S19 system toward database and shadow payroll readiness:

1. Keep daily S19 attendance automation stable.
2. Add PostgreSQL-compatible schema and deterministic import contracts.
3. Preserve result/detail/location/trajectory evidence when available.
4. Generate canonical monthly snapshots.
5. On the 1st through 5th Beijing evening runs after a natural month ends, collect five independent canonical results for the previous month.
6. Accept stage-2 only when all five canonical hashes match exactly, quality can reach the Q5 target, and there are no unresolved P0/P1 issues.
7. Generate payroll baseline candidates only after accepted stage-2 consensus.

Current offline bridge:

- `scripts/prepare_raw_replay_day_fact_bundle.py` converts private OneDrive raw archive replay into private day facts and raw-detail linkage.
- `scripts/prepare_stage2_source_from_raw_replay.py` converts that private day-fact bundle into a Stage-2 source snapshot.
- `scripts/resolve_stage2_source.py` can use `KMFA_STAGE2_SOURCE_MODE=raw_replay_day_fact` and `KMFA_STAGE2_RAW_REPLAY_DAY_FACT_DIR` during eligible evening runs.
- This bridge does not prove PostgreSQL mutation: `database_transaction_committed` and `database_transaction_verified` remain false until an approved non-production PostgreSQL execution proof and post-load state verification proof exist.
- To break the acceptance/DB-proof loop, `scripts/prepare_preconsensus_postgres_landing_bundle.py` can build a pre-consensus PostgreSQL landing bundle from a Stage-2 source before payroll acceptance.
- After the fail-closed PostgreSQL execution guard and `scripts/verify_postgres_landing_state.py` both produce non-production proofs, `scripts/apply_stage2_database_proof.py` can write a DB-verified Stage-2 source whose database gates are true. Only then may `scripts/write_stage2_run_artifacts.py` produce a run manifest that can pass day-5 consensus DB gates.

SQLite remains a private transition ledger/cache, not the final payroll database.

## Portable Package

- Config templates: `templates/`
- Operating runbook and v0.3 contracts: `references/`
- Config map: `references/configuration.md`
- PostgreSQL schema: `database/postgres_schema.sql`
- Automation prompt mirrors: `automation/`
- Stage-2 scripts and fixtures: `scripts/`, `tests/`
- Skill conversion SWOT and downstream impact: `references/decision-impact.md`
- Local package validator: `tools/validate_skill_package.py`

Run the package validator from repo root:

```bash
python3 KMFA/kmfa-dingtalk-attendance-skill/tools/validate_skill_package.py
```
