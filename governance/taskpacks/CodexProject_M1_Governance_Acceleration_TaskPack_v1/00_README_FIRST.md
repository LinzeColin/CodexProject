# CodexProject M1 治理执行链减负 Task Pack v1

## 一句话结论

本包不重建文件架构，不新增 `CURRENT.md`、`SHIP.md` 或另一套控制入口；它要求 Codex 在真实实施前完成 **两轮、每轮恰好 3 个全新独立只读 Agent 审查**，随后只以 shadow parity 方式优化现有 `scripts/lean_governance.py`，证明零质量回退后才允许有限激活。

## 当前观察基线

- 观察时间：2026-06-25 (Australia/Sydney review time)
- 分支：`main`
- SHA：`2d2e6eb9401dceb127f9f1f2041bcce57564d5c6`
- 提交：`Add Other8 S4PCT02 whkm structure`
- 注意：GitHub 在本包生成时已推进到 `S4PCT02`，不是较早的 `S4PBT02`。执行 `S1PAT01` 时必须重新读取远端/本地 HEAD；禁止把本 SHA 当成永久当前真相。

## 首次使用

1. 将本包解压到仓库外，不能直接覆盖仓库。
2. 把 `02_CODEX_MASTER_PROMPT.md` 原文交给 Codex。
3. 第一轮只执行 `S1PAT01`；不要一次运行全部 Roadmap。
4. S1/S2 只读；六份审查报告写入 `.git/codex-review/m1/<run_id>/` 或系统临时目录，不提交 Git。
5. 只有 `S2PCT02=PROCEED_SHADOW` 才可进入 S3。

## 不可变质量底线

- 保留现有机器事实平面和三个中文人类入口。
- `开发记录`继续完整包含 Stage -> Phase -> Task、工时/占比、Stop Condition、Stop Gate、证据和结果。
- 保留 T0-T3；不降低 T2/T3、release、nightly、manual full gate。
- PR Required Check 名称和 job 身份不变。
- READ_ONLY/PLAN/CI 零 tracked 写入。
- EEI 与 arxiv-daily-push 不允许写入；其活跃开发不能被本整改接管。
- 旧链在 shadow parity 完成前始终是唯一权威结果。

## 包内容

- `02_CODEX_MASTER_PROMPT.md`：Codex 总执行合同。
- `04_TWO_ROUND_SIX_AGENT_PROTOCOL.md`：两轮六 Agent 隔离与交叉验证规则。
- `05_CONSOLIDATED_FINDINGS.md`：本次静态预审问题种子；不是对真实运行测试的替代。
- `roadmap/`：完整 Roadmap（Markdown/YAML/CSV/PDF）。
- `prompts/`：第一轮和第二轮 6 个独立审查 Prompt，以及汇总 Prompt。
- `08_ACCEPTANCE_QUALITY_ROI.md`：质量、速度、输出、零写入和回滚指标。
- `08_CONTINUITY_AND_ROLLBACK.md`：任何新 Agent 的接续与回滚协议。
- `tools/validate_pack.py`：验证 Task Pack、Roadmap、Prompt 数量与校验和。

## 真实性说明

当前 ChatGPT 会话没有可调用的 Codex 子代理调度工具，因此没有伪称已在你的仓库真实 spawn 6 个 Codex Agent。本包包含两轮六轨隔离静态预审结果，并把真实 `2 × 3` Codex spawn 设为实施前硬门禁。真实运行、压力、并发、取消和 CI parity 必须由具有仓库工作区的 Codex 按 Roadmap 执行。
