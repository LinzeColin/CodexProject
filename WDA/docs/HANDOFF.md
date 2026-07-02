# WDA Handoff

## Current Goal

Execute WDA Stage 2 Sprint 2 safe readability classification from the old-computer APFS full export.

## Current Status

- Local worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/WDA`
- Project directory: `WDA/`
- Branch: `codex/wda`
- Product scope: WDA Control Plane for WeChat data analysis feasibility; current scope is APFS export container/header classification only, not raw message reading
- Implementation status: Sprint 2 safe readability artifacts generated; no runtime code yet
- Latest Sprint 1C outputs: `WDA/docs/stage2_sprint1c/`
- Latest Sprint 2 outputs: `WDA/docs/stage2_sprint2_safe_readability/`
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

Result: passed with `drift_count=0` and `reference_issue_count=0` after Sprint 2 output generation.

## Next Step

Run Sprint 2B only if explicitly approved: a schema-only, read-only probe on a copied non-sensitive candidate DB bundle. Keep the gate narrow: no source-directory scan, no decryption, no key extraction, no `key_info`/MMKV/login-store opening, no message/contact row selection, and no message parsing.
