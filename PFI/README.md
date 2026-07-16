# PFI

`PFI` 是本地优先的 Personal Financial Intelligence 项目。当前唯一产品版本为 `v0.2.5`，canonical 产品根为本目录；`QBVS`、`Alpha`、`Ralpha`、`Serenity` 均不是 PFI 子模块。

## 当前已验收冻结版本

状态标识：`PFI-V025-DELIVERED-REMOTE-RECOVERY-READY-LOCAL-RETIREMENT`

- Roadmap：Stage 0–12 已完成；`S12-P3-T4` 已由 owner 精确最终验收并执行 release freeze。
- 验收 Gate：A/B/C、evidence-index、请求时间、Stage 0–12 与五项非阻断 P2 已精确绑定；初审 `3` 项 P1 均 `closed_verified`，复审新增 `0 P0 / 0 P1 / 0 minor`。
- 任务进度：`156/156 (100%)`；Stage 12 为 `12/12 (100%)`。
- 唯一 CLI-only canonical App 最终重装已实际执行并通过；final delivery commit `d488b1f47d5ef8dd5f95fc7d6f9a5382d1486a8a` 已进入 GitHub `main`，当前远端仍保持已验收 product tree `a6aae2ae9e89f601b9a1833a45947ed625aa100c`。
- 原始 Roadmap 与 TaskPack 已归档到 `docs/source_packages/pfi_v025/`；本机 PFI worktree、App、入口、Downloads 原包与可重建 runtime 已获授权退休，缺失属于迁移后的预期状态。
- `final_human_acceptance=true`、`release_freeze_performed=true`、`final_reinstall_performed=true`、`production_accepted=true`、`push_performed=true`；v0.2.5 下一产品任务为 `NONE`。

## 当前 release identity

- Version：`v0.2.5`
- Build：`pfi-v025-s1p1-20260712.1`
- App：`0.2.5 / 20260712.1`
- Runtime source commit：`78375ec98fc1265abd03ef10087cc05beccab8b4`
- Remediation candidate：`c8ce63aac785ae1f119cfe1ff993c4e81436bf97`
- Reviewed remediation closure：`559cf190ccfd97aabcf37a5edf2bf1e9abe300fc`
- Rereview evidence：`123f5a6f7e7af22c283e49e55c2ba581310238d5`
- Evidence index：`sha256:ebd03b8abf92238aac0e3f972461e35de6ce4b3be27c3662ab24f6af7b342344`
- Canonical App：最终 CLI 原子重装于 `2026-07-16T00:27:09Z` 实际执行并通过 version/build/codesign/project-binding/hash；本地迁移后该 App 可不存在，按本页 source package 与 GitHub `main` 重建。
- 当前用户边界：禁止 Finder、`open`、LaunchServices、AppleScript 与 GUI 文件操作；上述操作计数保持 0。

## 生产真值边界

- 四个已复核支付宝来源由 [`config/sources/v025_immutable_real_source_lock.json`](config/sources/v025_immutable_real_source_lock.json) 固定 OID/bytes/SHA-256，并已在迁移后的 `LinzeColin/MetaDatabase@main` commit `8fad21d7e578c8ec56a1997d3a0e2f4a34a2fd6f` 逐项复验；不得恢复旧顶层 `MetaDatabase`。
- 真实交易规模为 8,815 raw / 8,808 ledger；Phase 12.2 的一次人工工作流复核使待复核计数从 803 变为 802，并在重启后持久。
- `SRC-HOLDINGS` 仍为 `not_loaded/not_run`；五份报告保持 `3 blocked / 2 partial`。缺失来源不得显示为零或财务通过。
- Canonical private SQLite 在目标 Mac 演练中只读；restore/rollback 只作用于隔离副本。初审 `3` 项 P1 已独立复审关闭，`5` 项 P2 residual 继续明确披露。

## Stage 12 初审、整改与复审证据

- 初审报告：`docs/pfi_v025/stage_12/STAGE_12_WHOLE_STAGE_REVIEW_INITIAL.md`
- Findings：`reports/pfi_v025/stage_12/whole_stage_review/initial_review_findings.json`
- Requirement matrix：`reports/pfi_v025/stage_12/whole_stage_review/requirement_matrix.json`
- Phase/index binding：`reports/pfi_v025/stage_12/whole_stage_review/phase_commit_binding.json`、`final_index_audit.json`
- Release/App truth：`reports/pfi_v025/stage_12/whole_stage_review/release_identity_audit.json`、`entry_audit.json`
- Fresh real E2E：`reports/pfi_v025/stage_12/whole_stage_review/fresh_real_e2e.json`
- Review evidence：`reports/pfi_v025/stage_12/whole_stage_review/evidence.json`
- 整改说明：`docs/pfi_v025/stage_12/STAGE_12_WHOLE_STAGE_REVIEW_REMEDIATION.md`
- 整改结论：`reports/pfi_v025/stage_12/whole_stage_review/remediation/closed_findings.json`
- Exact binding：`reports/pfi_v025/stage_12/whole_stage_review/remediation/exact_binding.json`
- Release identity：`reports/pfi_v025/stage_12/whole_stage_review/remediation/release_identity.json`
- CLI 入口隔离：`reports/pfi_v025/stage_12/whole_stage_review/remediation/entry_quarantine.json`
- 整改 evidence：`reports/pfi_v025/stage_12/whole_stage_review/remediation/evidence.json`
- 独立复审说明：`docs/pfi_v025/stage_12/STAGE_12_WHOLE_STAGE_REVIEW_REREVIEW.md`
- 复审 findings：`reports/pfi_v025/stage_12/whole_stage_review/rereview/findings.json`
- 复审 requirement matrix：`reports/pfi_v025/stage_12/whole_stage_review/rereview/requirement_matrix.json`
- 复审 evidence：`reports/pfi_v025/stage_12/whole_stage_review/rereview/evidence.json`
- 最终验收：`reports/pfi_v025/stage_12/final_acceptance/human_acceptance.json`
- Release freeze：`reports/pfi_v025/stage_12/final_acceptance/release_freeze.json`
- Final acceptance evidence：`reports/pfi_v025/stage_12/final_acceptance/evidence.json`
- Final CLI reinstall：`reports/pfi_v025/stage_12/final_delivery/cli_app_reinstall.json`

真正的 `human_acceptance.json` 已在整阶段审查、整改、独立复审及 owner 精确声明全部满足后创建并通过 TaskPack schema；App 最终重装、GitHub main 上传与 post-push parity 均已闭合。本地退休后的恢复入口见 `docs/source_packages/pfi_v025/SOURCE_PROVENANCE.md`。

## 运行与验证

```bash
# 当前 release identity（只读）
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src \
  PFI/.venv/bin/python -B PFI/scripts/v025/release_cache_contract.py \
  --project-root PFI --isolated-candidate --policy-json

# Stage 12 final acceptance 与历史复审验证（只读，不 push、不重装）
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src:PFI/scripts/v025 \
  PFI/.venv/bin/python -B \
  PFI/scripts/v025/stage12_whole_review_final_acceptance.py --verify

PFI/.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  PFI/tests/test_v025_stage12_release_freeze.py \
  PFI/tests/test_v025_stage12_whole_review_remediation.py \
  PFI/tests/test_v025_stage12_whole_review_rereview.py \
  PFI/tests/test_v025_stage12_whole_review_final_acceptance.py

# Canonical governance 与双平面检查
PFI/.venv/bin/python -B scripts/lean_governance.py check-render --project PFI
PFI/.venv/bin/python -B PFI/machine/tools/check_dual_plane_ci.py \
  --root PFI --projects . --require-projects
```

历史执行记录保存在 `docs/pfi_v025/` 与 `reports/pfi_v025/`；当前状态只以 `docs/governance/project.yaml`、`docs/governance/roadmap.yaml`、`docs/governance/development_events.jsonl`、`VERSION` 和本摘要为准。
