# WDA Handoff

## Current Goal

Execute WDA Stage 2 Sprint 2E message-level data route decision after real artifact discovery failure.

## Current Status

- Local worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/WDA`
- Project directory: `WDA/`
- Branch: `codex/wda`
- Product scope: WDA Control Plane for WeChat data analysis feasibility; current scope is message-level data route decision, not raw message reading
- Implementation status: Sprint 2B-A/2B-B/2B-C, Sprint 2C contract, Sprint 2D discovery, and Sprint 2E route decision artifacts generated; no runtime code yet
- Latest Sprint 1C outputs: `WDA/docs/stage2_sprint1c/`
- Latest Sprint 2 outputs: `WDA/docs/stage2_sprint2_safe_readability/`
- Latest Sprint 2B-A outputs: `WDA/docs/stage2_sprint2b_candidate_bundle/`
- Latest Sprint 2B-B outputs: `WDA/docs/stage2_sprint2b_schema_probe/`
- Latest Sprint 2B-C outputs: `WDA/docs/stage2_sprint2b_route_decision/`
- Latest Sprint 2C outputs: `WDA/docs/stage2_sprint2c_readable_artifact_contract/`
- Latest Sprint 2D outputs: `WDA/docs/stage2_sprint2d_real_artifact_discovery/`
- Latest Sprint 2E outputs: `WDA/docs/stage2_sprint2e_message_data_route_decision/`
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
- Sprint 2B-C route decision recommends an owner-authorized readable artifact intake contract as the next route; it does not execute that route.
- WDA RAG/Web/Matrix data-dependent implementation remains blocked until a safe, authorized message-level import path exists.
- Sprint 2C defines the readable artifact contract only; it does not create `messages.jsonl`, validate a real artifact, or implement RAG/Web/Matrix.
- Sprint 2D searched real data sources metadata-only and found no validated message-level readable artifact; APFS was mounted read-only for discovery and detached after search.
- WDA still lacks message-level readable input; future conversion requires a separate approved sprint and a selected readable candidate.
- Sprint 2E chooses the next direction as official/user-readable artifact route selection and acquisition contract; it does not execute acquisition or import.
- Third-party adapter work is research-only backup; high-risk raw adapter work remains rejected under the current boundary.

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
- `WDA/docs/stage2_sprint2b_route_decision/README.md`
- `WDA/docs/stage2_sprint2b_route_decision/raw_gate_decision.md`
- `WDA/docs/stage2_sprint2b_route_decision/recommended_next_route.md`
- `WDA/docs/stage2_sprint2c_readable_artifact_contract/README.md`
- `WDA/docs/stage2_sprint2c_readable_artifact_contract/readable_artifact_contract.md`
- `WDA/docs/stage2_sprint2c_readable_artifact_contract/import_manifest_schema.md`
- `WDA/docs/stage2_sprint2c_readable_artifact_contract/next_sprint2d_validation_plan.md`
- `WDA/docs/stage2_sprint2d_real_artifact_discovery/README.md`
- `WDA/docs/stage2_sprint2d_real_artifact_discovery/sprint2d_decision.md`
- `WDA/docs/stage2_sprint2d_real_artifact_discovery/readable_artifact_candidates.csv`
- `WDA/docs/stage2_sprint2d_real_artifact_discovery/privacy_and_safety_validation.md`
- `WDA/docs/stage2_sprint2e_message_data_route_decision/README.md`
- `WDA/docs/stage2_sprint2e_message_data_route_decision/route_options_matrix.md`
- `WDA/docs/stage2_sprint2e_message_data_route_decision/recommended_next_step.md`

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

Latest Sprint 2B-C decision:

- Required route-decision outputs present: true
- Hard drive required: false
- `messages.jsonl` present under WDA repo stage docs: false
- Recommended next route: owner-authorized readable artifact intake contract
- Raw Gate: `Conditional Investigation`

Latest Sprint 2C contract:

- Required contract outputs present: true
- Hard drive required: false
- `messages.jsonl` produced: false
- Contract files defined: `import_manifest.json`, `messages.jsonl`, `conversations.jsonl`, `contacts.jsonl`, `media_index.csv`
- Next executable step: validate a small owner-authorized sample artifact only if the user provides or approves one
- Raw Gate: `Conditional Investigation`

Latest Sprint 2D discovery:

- Required discovery outputs present: true
- Discovery mode: real-data, metadata-only
- APFS source scanned: true, mounted read-only
- APFS detached after search: true
- Candidate rows reported: 12, all local generated report/metadata-like rows
- APFS message/chat-like readable artifact candidates: 0
- Protected DB/key/MMKV/login opened: 0
- Message content parsed: 0
- `messages.jsonl` produced: false
- Raw Gate: `Conditional Investigation`

Latest Sprint 2E route decision:

- Required decision outputs present: true
- Hard drive required: false
- `messages.jsonl` exists: false
- Recommended next sprint: Sprint 2F official/user-readable artifact route selection and acquisition contract
- Third-party adapter route: research-only backup, not execution
- High-risk raw adapter route: rejected under current boundary
- RAG/Web/Matrix: blocked
- Raw Gate: `Conditional Investigation`

## Next Step

Run Sprint 2F only if explicitly approved. Sprint 2F should select the official/user-readable artifact acquisition route and define owner authorization/local storage/validation stop conditions. Do not implement acquisition, import, third-party tools, protected DB probes, raw upload, or RAG/Web/Matrix until a later approved sprint.
