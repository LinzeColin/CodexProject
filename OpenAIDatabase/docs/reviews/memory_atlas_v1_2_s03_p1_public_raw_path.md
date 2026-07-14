# Memory Atlas v1.2 S03 P1 Public Raw Path

Task ID: `MA-V12-S03P1`.

Acceptance ID: `ACC-MA-V12-S03P1`.

Status: `phase_s03_p1_public_raw_path_defined_pending_s03_p2`.

Validator: `validate:v1.2-s03-p1`.

## Scope

S03 P1 defines the public raw archive path, raw manifest/hash file contract,
append-only rule and hash drift fail rule.

Implemented files:

- `机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json`
- `data/public_raw/README.md`
- `人类可读/06_Raw明文公开与只读归档说明.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p1.cjs`

## Acceptance Mapping

| Requirement | Evidence |
|---|---|
| public raw archive path | `data/public_raw/README.md`; policy `public_raw_root` and `source_raw_roots` |
| raw manifest/hash file | policy `manifest_contract` |
| append-only rule | policy `append_only_rule` |
| hash drift fail rule | policy `hash_drift_fail_rule` |

## Boundaries

- No S03 P2 credential gate.
- No S03 P3 manifest generation.
- No connector implementation.
- No transcript ingestion in S03 P1.
- No GitHub main upload in this phase.

Next gate: pending S03 P2.
