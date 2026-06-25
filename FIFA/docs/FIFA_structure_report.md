# FIFA S5PBT01 Structure Report

Task: `S5PBT01`
Acceptance: `ACC-S5PBT01`
Date: 2026-06-25

## Scope

This report binds the FIFA project structure after the Wave 2 manifest. The
active pipeline, legacy implementation, generated artifacts, and local ops
material are explicitly separated without changing product runtime behavior.
Machine-readable contract:
`governance/stage_gates/s5pb/fifa_structure_contract.yaml`.

## Structure Boundary

| Layer | Path | Role | Default run path |
|---|---|---|---|
| Active pipeline | `FIFA/tab-research-pipeline/` | parser, validation, export smoke, app scripts, tests | yes |
| Legacy | `FIFA/legacy/fifa-analysis-system/` | read-only historical implementation and tests | no |
| Artifacts | `FIFA/artifacts/` | generated latest reports and backups | no |
| Ops docs | `FIFA/ops/` | local launch agent, cleanup, and slim/audit notes | no |

## S5PBT01 Decisions

- `tab-research-pipeline/` remains the only default active pipeline path.
- `legacy/fifa-analysis-system/` remains in place for traceability and rollback
  context, but it is not imported or executed by the default FIFA smoke path.
- `artifacts/latest/` and `artifacts/backups/` remain generated-output layers.
  Their S5PAT02 archive candidates stay checksum-bound and are not moved in
  S5PBT01.
- `tab-research-pipeline/assets/app_icon/` remains active UI asset material and
  is not archived by this task.
- `ops/` is local operational documentation and launch metadata only; it is not
  application source.

## Legacy Reference Audit

- Active script/code reference to `legacy/fifa-analysis-system`: none observed.
- Documentation reference to `legacy/fifa-analysis-system`: retained in
  `FIFA/tab-research-pipeline/HANDOFF.md` as historical inventory.
- Default command path: `cd FIFA/tab-research-pipeline` followed by focused
  parser/validation/export smoke tests.

## Smoke Evidence

Log: `governance/stage_gates/s5pb/fifa_smoke_tests.log`

Focused smoke command:

```text
set PYTHONPATH=C:\Users\linze\Documents\Codex\2026-06-23\xian\work\test_stubs;.&& C:\Users\linze\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B -m unittest tests.test_pipeline.PipelineTests.test_parse_market_pairs tests.test_pipeline.PipelineTests.test_parse_market_pairs_rejects_invalid_decimal_odds_tokens tests.test_pipeline.PipelineTests.test_matches_gate_blocks_invalid_raw_decimal_odds tests.test_pipeline.PipelineTests.test_write_outputs tests.test_pipeline.PipelineTests.test_write_outputs_fails_closed_without_success_deliverables_when_gate_blocks tests.test_pipeline.PipelineTests.test_write_outputs_legacy_blocked_export_requires_explicit_flag -q
```

Result: `PASS`, 6 tests OK.

## Rollback

Rollback is a git revert of the S5PBT01 task commit. Since S5PBT01 does not move
legacy, artifact, ops, or active pipeline files, rollback removes the structure
contract, structure report, smoke log, README/AGENTS boundary notes, tests, and
run manifest only.

## Stop Conditions Preserved

- FIFA legacy participates in default run: no.
- Active pipeline path changed: no.
- Generated artifacts used as source truth: no.
- Ops docs used as runtime source: no.
- Betting automation enabled: no.
- Private values emitted: no.
