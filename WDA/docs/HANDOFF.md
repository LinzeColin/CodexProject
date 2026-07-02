# WDA Handoff

## Current Goal

Execute WDA Stage 2 Sprint 2B local candidate bundle and schema-only read-only probe.

## Current Status

- Local worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/WDA`
- Project directory: `WDA/`
- Branch: `codex/wda`
- Product scope: WDA Control Plane for WeChat data analysis feasibility; current scope is copied candidate DB bundle handling and schema-only SQLite probing, not raw message reading
- Implementation status: Sprint 2B-A/2B-B artifacts generated; no runtime code yet
- Latest Sprint 1C outputs: `WDA/docs/stage2_sprint1c/`
- Latest Sprint 2 outputs: `WDA/docs/stage2_sprint2_safe_readability/`
- Latest Sprint 2B-A outputs: `WDA/docs/stage2_sprint2b_candidate_bundle/`
- Latest Sprint 2B-B outputs: `WDA/docs/stage2_sprint2b_schema_probe/`
- Local Sprint 2B copied bundle: `/Users/linzezhang/Downloads/WDA_MetaData/raw_ferry/sprint2b_candidate_db_bundle_20260703`
- Raw Gate: `Conditional Investigation`; message readability not proven; Raw Gate is not Go

## Key Decisions

- Keep WDA as one long-lived project worktree.
- Do not create a full CodexProject copy for each chat.
- Do not expand unrelated project directories into this worktree.
- Treat current WDA files as governance/bootstrap only, not product implementation.
- Treat old computer as the highest-value data source candidate.
- Treat new computer as WDA Control Plane / WDA_HOME / database / RAG / Web host.
- Do not copy the full old WeChat cache; Sprint 2 should use a copied candidate DB bundle if approved.
- Treat `/Volumes/My Passport/WDA_MetaData/raw_ferry/old_mac_wechat_full_export_20260702_apfs.sparseimage` as the authoritative old-computer export.
- Do not use the abandoned direct ExFAT partial copy as authoritative.
- Keep `key_info`, login paths, and MMKV/key-value stores as skip/no-open.
- Sprint 2B-A bundle must exclude `key_info`, login paths, MMKV, KVDB/key-value stores, sensitive skip paths, and raw `msg/file`, `msg/attach`, `msg/video` cache paths.
- Sprint 2B-B must run from the local copied bundle only; no external drive or APFS source is required after bundle validation.
- Sprint 2B-B read-only SQLite probe found 0 plain SQLite schema-open successes across 91 main candidates; all 91 remained `not_plain_sqlite_or_encrypted_unknown` under the approved safe path.

## Files To Read First

- `AGENTS.md`
- `WDA/AGENTS.md`
- `WDA/README.md`
- `WDA/docs/HANDOFF.md`
- `WDA/功能清单.md`
- `WDA/开发记录.md`
- `WDA/模型参数文件.md`
- `WDA/docs/governance/project.yaml`
- `WDA/docs/governance/roadmap.yaml`
- `WDA/docs/stage2_sprint1c/multi_device_topline_comparison.md`
- `WDA/docs/stage2_sprint1c/multi_device_raw_gate_summary.md`
- `WDA/docs/stage2_sprint1c/next_sprint2_safe_readability_plan.md`
- `WDA/docs/stage2_sprint2_safe_readability/README.md`
- `WDA/docs/stage2_sprint2_safe_readability/safe_readability_decision.md`
- `WDA/docs/stage2_sprint2_safe_readability/sprint2_validation_report.md`
- `WDA/docs/stage2_sprint2b_candidate_bundle/README.md`
- `WDA/docs/stage2_sprint2b_candidate_bundle/bundle_validation_report.md`
- `WDA/docs/stage2_sprint2b_schema_probe/README.md`
- `WDA/docs/stage2_sprint2b_schema_probe/sprint2b_safe_readability_decision.md`

## Validation

Lightweight project check:

```bash
/usr/bin/python3 -B scripts/lean_governance.py check-render --project WDA
```

Do not expand unrelated projects to satisfy full monorepo validation unless the user explicitly asks for a root-governance run.

Latest verified command:

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/lean_governance.py check-render --project WDA
```

Result: passed with `drift_count=0` and `reference_issue_count=0` after Sprint 2B output generation.

Latest Sprint 2B local validation:

- Required Sprint 2B-A/B outputs present: true
- Candidate bundle manifest/checksum/local file count: 169/169/169
- Deny-marker violations in selected bundle: 0
- Probe main candidates: 91
- Plain SQLite schema-open successes: 0
- Read-only open failures: 91
- Message/contact row access violations: 0
- External/APFS mounts visible before Sprint 2B-B validation: 0

## Next Step

Run Sprint 2B-C only if explicitly approved. Recommended next step is a decision point, not raw import: review Sprint 2B schema-only failure results, decide whether WDA should use an approved readable export/user-provided artifact path, and keep the gate narrow. Do not attempt SQLCipher keys, protected-store bypass, `key_info`/MMKV/login-store opening, message/contact row selection, or message parsing.
