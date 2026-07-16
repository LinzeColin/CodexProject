# PFI v0.2.5 Stage 12 Phase 12.3 Release-freeze Candidate

## Run contract

- Run unit：`S12-P3-T1..T3`；`S12-P3-T4` 仅登记为最终关口，不在本 run 执行。
- Acceptance：`ACC-PFI-V025-S12-P123-RELEASE-FREEZE-CANDIDATE`。
- Risk tier：`T3_RELEASE_EVIDENCE_PRIVACY_HUMAN_ACCEPTANCE`。
- 唯一目标：统一当前状态，生成 one-way final evidence index + detached hash，并生成精确绑定的 pending final acceptance request。
- 停止边界：独立 Stage 12 whole-stage review、整改、复审、最终明确验收、GitHub push、最终 canonical App 重装与 v0.2.6 均属于后续 run。

## 上游集成与 source migration

本 Phase 开始时，本地 `codex/pfi` 已将 `origin/main@5ff1f3c5ce49d0bb5466125333b873082d2ddd58` 合并为 `665ee5aa89e55fe36a8fbc4e35df8069a6dd6647`。上游引入 PFI dual-plane，并删除旧顶层 `MetaDatabase` tree；root governance 同时仍要求 PFI 根目录保留三份完整中文 human entries。

处理结果：

- 接受上游 migration，不恢复、复制或重新创建顶层 `MetaDatabase`。
- 保留 `PFI/功能清单.md`、`PFI/开发记录.md`、`PFI/模型参数文件.md`，继续由 Lean canonical facts 完整渲染。
- machine facts 成为七份 `PFI/文档/*.md` 的唯一编辑事实源；七份人类文档只由 renderer 生成。
- 四个已复核真实支付宝 source blobs 统一由 `v025_immutable_real_source_lock.json` 绑定 `78375ec98fc1265abd03ef10087cc05beccab8b4`，逐项校验 OID、bytes 和 SHA-256。该 commit 是当前 merge commit 的可达父提交。
- Stage 12 release test、真实浏览器 E2E 与 target-Mac UAT 共用同一个 loader，不再假设来源存在于当前 `HEAD` tree。

## 状态统一

统一后的当前真值：

- `VERSION=v0.2.5`；App=`0.2.5 / 20260712.1`。
- Stage 0–11 已完成；Stage 12 Phase 12.1/12.2 为 candidate pass。
- `S12-P3-T1..T3` candidate complete，`S12-P3-T4` 等待 whole-stage review 后明确最终验收。
- 总任务 `155/156 (99.36%)`；Stage 12 `11/12 (91.67%)`。
- 下一唯一 run：`STAGE12-WHOLE-REVIEW`。
- `production_accepted=false`、`final_human_acceptance=false`、`push_performed=false`、`release_freeze_performed=false`。

README 与 HANDOFF 只保留当前摘要和操作入口；完整 Stage→Phase→Task、acceptance、stop conditions、evidence、rollback 与历史 result 继续保留在 canonical roadmap、development events、三份 mandatory human entries 及版本化 `docs/reports`。

## Evidence index 与验收请求

`final_evidence_index.json` 只 hash 已存在且不可变的关键输入：Stage 0–11 phase/whole-stage evidence、whole-stage acceptance/index，以及 Stage 12.1/12.2 的 release、real E2E、UAT、resilience、defect 和 privacy artifacts。它故意排除自身、detached hash、Phase 12.3 evidence 与验收请求，避免 circular hash。

`human_acceptance_request.json` 绑定：

- product/version/build/App version；
- `SELF` candidate commit 语义；
- exact evidence-index SHA-256；
- accepted scope；
- 三项已知 P2；
- 必须先完成 Stage 12 独立整阶段审查、整改和复审；
- 若 review 改变 candidate，必须重新生成 request；
- 用户必须在 review 后明确接受 exact release。

TaskPack 的 `human_acceptance.schema.json` 要求真实 `accepted_at` 与至少 20 字 acceptance statement，因此 pending 状态不能伪装成该 schema。真正的 `reports/pfi_v025/stage_12/final_acceptance/human_acceptance.json` 在本 Phase 明确保持不存在。

## 验证与边界

Phase harness 执行 focused Stage 1/12 Python release tests、Node cache-policy tests、dual-plane CI、Lean renderer、完整 Git archive + current overlay governance、TaskPack evidence schema、privacy、artifact hash 与 `git diff --check`。

保持的已知限制：

- P2：真实 kernel sleep/wake 未执行；owned-process suspend/resume 只是明确标注的 proxy。
- P2：`SRC-HOLDINGS` 仍 `not_loaded/not_run`；不得声明 holding financial pass。
- P2：一个 noncanonical entry mismatch 仅完成 CLI census，未在 no-Finder 边界下修改。

本 Phase 不读取或修改 canonical private database，不安装 App，不调用 Finder/`open`/LaunchServices/AppleScript/GUI，不访问外部网络，不 push，不创建最终验收，不进入下一版本。

## Rollback

优先 revert Phase 12.3 candidate；若上游集成本身需撤销，再单独 revert merge commit。不得恢复已迁移 `MetaDatabase` tree。Phase 12.2 的 App rollback archive 保留，canonical database 与 remote main 未在本 Phase 修改。
