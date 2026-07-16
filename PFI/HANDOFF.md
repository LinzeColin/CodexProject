# PFI Handoff

## 当前目标与状态

状态标识：`PFI-V025-FINAL-APP-REINSTALLED-WAITING-SINGLE-MAIN-UPLOAD`

- Stage 12 初审、整改、独立复审、owner exact final acceptance 与 `S12-P3-T4` release freeze 已全部完成。
- Initial review base：`9a7245acf984a4eb98f93c4aab7bb4d02095294f`；初审 `0 P0 / 3 P1 / 0 minor`。
- Runtime source：`78375ec98fc1265abd03ef10087cc05beccab8b4`；product/remediation anchor A：`c8ce63aac785ae1f119cfe1ff993c4e81436bf97`；reviewed closure B：`559cf190ccfd97aabcf37a5edf2bf1e9abe300fc`；index SHA-256：`ebd03b8abf92238aac0e3f972461e35de6ce4b3be27c3662ab24f6af7b342344`。
- Rereview evidence C：`123f5a6f7e7af22c283e49e55c2ba581310238d5`；三项 P1 均 `closed_verified`，复审新增 `P0=0 / P1=0 / minor=0`。
- Owner 已精确接受 Stage 0–12、A/B/C、evidence-index、验收请求时间与五项 P2；总进度 `156/156 (100%)`，Stage 12 `12/12 (100%)`。
- 唯一 CLI-only canonical App 最终重装已在 `2026-07-16T00:27:09Z` 实际执行；version/build/codesign/project-binding/hash 全部通过。
- 下一唯一 run：`PFI-V025-SINGLE-MAIN-UPLOAD-AND-POST-PUSH-PARITY` / `ACC-PFI-V025-FINAL-DELIVERY-PARITY`。
- 尚未完成：唯一 GitHub main push 与 post-push 只读三方 parity proof。

## 本 Phase 关键决策

1. 用户最新指令禁止 Finder、`open`、LaunchServices、AppleScript 和 GUI 文件操作；后续必须继续 CLI/headless-only。
2. 本轮已将 `origin/main` 合并到 `codex/pfi`；上游迁移并删除顶层 `MetaDatabase`，不得恢复。
3. Stage 12 的四个真实支付宝 source blobs 改由 `PFI/config/sources/v025_immutable_real_source_lock.json` 锁定到可达历史 commit，并逐项验证 OID、字节数与 SHA-256。
   历史 pytest 的默认 source ref 仅通过 `PFI/tests/conftest.py` 在测试进程内路由到该 commit；runtime 默认与产品 payload 保持 A 不变，原始 Phase 12.1 矩阵复跑为 `358 passed, 6 deselected`。
4. Phase 12.3 的 pending request 已由 owner 精确声明闭合；`reports/pfi_v025/stage_12/final_acceptance/human_acceptance.json` 已 schema-valid 创建。
5. Release freeze 已绑定 exact version/build、A/B/C、evidence-index hash、请求/接受时间、Stage 0–12 和五项 P2；唯一 CLI 最终重装已闭合，上传和 post-push parity 仍在同一 delivery transaction 中单独证明。
6. 两父提交传输因纳入 2,700+ 条本地历史而被 GitHub 以 `pack exceeds maximum allowed size (2.00 GiB)` 在 ref 更新前拒绝；最终交付改为相同 PFI tree 的最新 live-main 单父 curated snapshot，不改变 A/B/C 证据绑定或 runtime。
7. 初审三项 P1 已整改：release source 精确覆盖 runtime payload；request/state/index/evidence 不再使用 `SELF`；Downloads v0.2.3 App 已通过 CLI 原子移动到私有隔离区并保留回滚命令。
8. 独立复审使用单独 harness 在 closure B 上重新计算 ancestry、runtime 零漂移、exact binding、两套 manifest、entry census 与 fresh real E2E；不声称外部人工或 subagent reviewer。

## 当前 release 与数据真值

- Repo branch：`codex/pfi`；已合并的 upstream base 为 `origin/main@5ff1f3c5ce49d0bb5466125333b873082d2ddd58`。
- Canonical App：`/Applications/PFI.app` = `0.2.5 / 20260712.1`；Phase 12.2 已通过 CLI 原子安装与 bundle executable 直接运行验证。
- 真实交易：4 immutable Git objects；8,815 raw / 8,808 ledger；review 803 → 802 且重启后持久。
- Holdings：`not_loaded/not_run`；Reports：`3 blocked / 2 partial`；无假零、fixture fallback 或 financial pass 冒充。
- Phase 12.2 Defects：P0=0、P1=0、P2=3；Stage 12 初审 Findings 为 P0=0、P1=3、minor=0，独立复审后 open P0/P1/minor=`0/0/0`，另有 5 项 P2 residual；真实 kernel sleep/wake 未执行，仅有明确标注的进程级 proxy。
- Canonical private DB：Phase 12.2 只读 Online Backup；restore/rollback 与 `SQLITE_FULL` recovery 均在隔离目标完成。

## 关键文件

- Source lock：`PFI/config/sources/v025_immutable_real_source_lock.json`
- Source loader：`PFI/scripts/v025/immutable_real_sources.py`
- Phase 12.3 generator：`PFI/scripts/v025/prepare_release_freeze.py`
- Release dispatcher：`PFI/scripts/v025/release_acceptance.py`
- Governance facts：`PFI/docs/governance/project.yaml`、`PFI/docs/governance/roadmap.yaml`、`PFI/docs/governance/development_events.jsonl`
- Dual plane：`PFI/machine/facts/` → `PFI/文档/`
- Phase evidence：`PFI/reports/pfi_v025/stage_12/phase_12_3/`
- Initial review：`PFI/docs/pfi_v025/stage_12/STAGE_12_WHOLE_STAGE_REVIEW_INITIAL.md`
- Review evidence：`PFI/reports/pfi_v025/stage_12/whole_stage_review/`
- Remediation contract：`PFI/docs/pfi_v025/stage_12/STAGE_12_WHOLE_STAGE_REVIEW_REMEDIATION.md`
- Remediation evidence：`PFI/reports/pfi_v025/stage_12/whole_stage_review/remediation/`
- Rereview contract：`PFI/docs/pfi_v025/stage_12/STAGE_12_WHOLE_STAGE_REVIEW_REREVIEW.md`
- Rereview evidence：`PFI/reports/pfi_v025/stage_12/whole_stage_review/rereview/`
- Final acceptance：`PFI/reports/pfi_v025/stage_12/final_acceptance/`

## 验证命令

```bash
PFI/.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  PFI/tests/test_v025_stage12_release_freeze.py \
  PFI/tests/test_v025_stage12_whole_review_remediation.py \
  PFI/tests/test_v025_stage12_whole_review_rereview.py \
  PFI/tests/test_v025_stage12_whole_review_final_acceptance.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src:PFI/scripts/v025 \
  PFI/.venv/bin/python -B \
  PFI/scripts/v025/stage12_whole_review_final_acceptance.py --verify

PFI/.venv/bin/python -B scripts/lean_governance.py check-render --project PFI
PFI/.venv/bin/python -B PFI/machine/tools/check_dual_plane_ci.py \
  --root PFI --projects . --require-projects
git diff --check
```

## 下一 run 的停止条件

- `origin/main` 在最终 push 前再次前移或无法安全集成。
- 任何命令要求 Finder、`open`、LaunchServices、AppleScript 或 GUI 文件操作。
- curated delivery tree 改动 PFI、两份获准 root governance scripts 之外的 live main 内容。
- post-push remote/main、curated tree、App codesign/binding/version/build/parity 任一失败。

当前 exact final acceptance、release freeze 与唯一 CLI-only App 最终重装均已闭合；后续只执行已授权的唯一 GitHub main push 和 post-push 只读 parity，不进入 v0.2.6。
