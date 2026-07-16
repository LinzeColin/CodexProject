# PFI v0.2.5 Stage 12 独立整阶段初审

## Run contract

- Review base：`9a7245acf984a4eb98f93c4aab7bb4d02095294f`。
- Acceptance：`ACC-PFI-V025-STAGE12-WHOLE-REVIEW-INITIAL`。
- 本 run 只执行独立初审；不整改、不复审、不创建最终 `human_acceptance.json`、不 freeze、不 push、不重装。
- 用户最新指令禁止 Finder、`open`、LaunchServices、AppleScript 与 GUI 文件操作；本审查使用 CLI、headless Chromium 与隔离临时目录。

## 初审方法

审查器不直接相信 Phase 的 `candidate_pass`，而是独立完成：

1. 在各自 immutable phase commit 上重算 119 个 declared artifact hash，并用 TaskPack schema 校验三份 Phase evidence。
2. 在 candidate commit 上重算 89 个 final-index 输入与 detached hash。
3. 重新读取四个 immutable real source objects，并运行一次当前 HEAD 的真实 headless import/review/report E2E；临时 DB、trace 和截图在提取脱敏摘要后删除。
4. CLI 重算 frontend/backend hash、codesign、canonical App identity 与 entry census，不启动 Finder。
5. 运行 Stage 12 focused tests、Stage 4–11 selected regression、Node cache tests、release/cache、dual-plane、renderer 和完整 archive+overlay governance。

审查执行真值是一套本地 deterministic runner 下的三种独立 lens，不声称外部人类或 subagent reviewer。

## 初审结论

状态：`remediation_required`；`0 critical / 3 important / 0 minor`。

1. `S12-WR-I01-RELEASE-COMMIT-DRIFT`：frontend/backend 和 canonical App hash 当前一致，但 release manifest 的 `git_commit` 仍停留在 Stage 9，早于后续 runtime-bound source changes，不能作为最终 source-commit 真值。
2. `S12-WR-I02-EXACT-ACCEPTANCE-BINDING`：Phase 12.3 pending request 仍写 `SELF`，state snapshot 记录的是提交前 HEAD/ahead；最终验收前必须绑定明确 source/candidate commit 语义并重建索引。
3. `S12-WR-I03-NONCANONICAL-OLD-APP`：CLI census 仍发现一个 Downloads v0.2.3 App；须在后续整改 run 中以 CLI-only 方式隔离或移除并复核。

## 保留但不伪装的 P2

- 真实 kernel sleep/wake 未执行，只有 owned-process suspend/resume proxy。
- `SRC-HOLDINGS` 仍 `not_loaded/not_run`；不得注入假持仓或声明 financial pass。
- Finder 方法被用户最新指令覆盖；只保留 canonical bundle executable 与 headless browser 证据。
- axe-core 不可用且未伪报，通过的是 deterministic WCAG 2.2 AA、CDP AX、keyboard 与 visual regression substitute。
- 6 个 historical-state-coupled tests 继续作为已登记 P2 test debt，由 current-state gates 替代。

## 下一唯一 run

`STAGE12-WHOLE-REVIEW-REMEDIATION`：只修复三项 important findings。整改完成后必须另起 run 做独立复审；只有复审零 P0/P1 且用户对 exact release 明确验收，才可执行 S12-P3-T4 与最终 delivery transaction。

## Rollback

Revert 本初审 commit 即可；review base、canonical private database、canonical App 和 remote main 均未在本 run 修改。
