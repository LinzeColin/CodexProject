# PFI v0.2.5 Stage 12 整阶段独立复审

## Run Contract

- Run：`STAGE12-WHOLE-REVIEW-REREVIEW`
- Acceptance：`ACC-PFI-V025-STAGE12-WHOLE-REVIEW`
- 模式：T3 `IMPLEMENT`，先只读复算，再写入非 runtime 复审证据与最小治理状态。
- Runtime source：`78375ec98fc1265abd03ef10087cc05beccab8b4`
- 产品/整改锚点 A：`c8ce63aac785ae1f119cfe1ff993c4e81436bf97`
- 整改闭合 B：`559cf190ccfd97aabcf37a5edf2bf1e9abe300fc`
- 目标：独立重算三项 P1 整改和完整 Stage 12 requirement matrix；不直接信任整改报告结论。
- 非目标：新 finding 整改、`S12-P3-T4`、最终 human acceptance、push、最终 App 重装、production acceptance、v0.2.6。
- 停止条件：新增 P0/P1、runtime/hash/entry/DB 漂移，或任何检查要求 Finder、`open`、LaunchServices、AppleScript、GUI 文件操作。

## 独立性边界

本复审是独立的 deterministic local rereview：使用单独 harness，重新计算 commit ancestry、runtime diff、release 四方身份、Phase 12.3 exact binding、artifact manifests、CLI 入口 census 与 fresh real headless E2E。它不声称外部人工 reviewer 或 subagent reviewer；owner 最终验收仍是独立 Gate。

## 预期判定

- 三项初审 P1：`closed_verified`。
- 复审新增 findings：`0 P0 / 0 P1 / 0 minor`。
- 五项 P2 residual 继续保留：kernel sleep/wake 仅代理、Holdings not_loaded、CLI-only 方法约束、axe-core 替代证据、六项历史状态测试债务。
- 复审通过后状态：`rereview_pass_waiting_explicit_final_acceptance`；总进度仍为 `155/156 (99.36%)`，Stage 12 仍为 `11/12 (91.67%)`。
- `human_acceptance.json` 必须继续不存在；只有 owner 对 exact version/build/product candidate/evidence-index hash/已知缺陷作明确验收后，才可进入后续 `S12-P3-T4` delivery transaction。

## 回滚

若复审闭合资产有误，只回滚该非 runtime 证据/治理提交；不得改写 A/B、不得恢复迁出目录、不得触碰 canonical private DB 或 canonical App。
