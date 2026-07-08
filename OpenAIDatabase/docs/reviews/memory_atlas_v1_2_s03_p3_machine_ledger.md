# Memory Atlas v1.2 S03 P3 Machine Ledger

Task ID: `MA-V12-S03P3`.

Acceptance ID: `ACC-MA-V12-S03P3`.

Status: `phase_s03_p3_machine_ledger_completed_pending_s03_review`.

Validator: `validate:v1.2-s03-p3`.

## Result

S03 P3 adds the machine ledger layer for public raw archive integrity.

The new generator proves that raw manifest/hash can be generated and that each
non-empty manifest row maps source/file/hash/imported_at. The baseline manifest
is empty because the repository currently contains no real raw transcript under
`data/public_raw/`; README and placeholder files are intentionally excluded.

## Files

- `scripts/raw_archive_manifest.py`
- `机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json`
- `机器治理/证据与日志/raw_archive_manifests/raw_manifest.s03_p3_baseline.jsonl`
- `机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl`
- `人类可读/08_Raw机器账本说明.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p3.cjs`
- `tests/test_s03p3_raw_manifest.py`

## Acceptance Coverage

- raw manifest/hash can be generated.
- Manifest rows map `source_id`, `relative_path`, `sha256` and `imported_at`.
- Hash drift or deleted manifest entries fail validation.
- New raw files remain append-only additions.
- Human-readable pages explain the machine ledger without turning manifest rows
  into the primary human surface.

## Boundaries

- No connector implementation.
- No real transcript ingestion in this phase.
- No UI work.
- No public raw file mutation in this phase.
- No GitHub main upload in this phase.

Next gate: pending S03 Review.
