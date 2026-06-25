# Codex Master Prompt - M1 治理执行链减负与零质量回退

你位于 `LinzeColin/CodexProject` 根目录。

本任务是根治理执行链优化，不是业务功能开发。观察基线为 `2d2e6eb9401dceb127f9f1f2041bcce57564d5c6`，但你必须以 `S1PAT01` 重新确认的实际 HEAD 为准。

## 总目标

在不改变现有双平面、三个中文人类入口、完整 Roadmap 与 T0-T3 质量门禁的前提下，降低普通开发任务的重复验证、重复读取和重复写入成本，提升每单位 Token 的可验收交付吞吐率，并保证开发、验收、发布、回滚与后续 Agent 接续的连续性和稳定性。

## 强制不变量

1. 保持现有双平面：Lean v2 机器事实 + `功能清单` / `开发记录` / `模型参数文件` 中文完整视图。
2. `开发记录`的完整 Roadmap 合同不得削弱。
3. 不新增 `CURRENT.md`、`SHIP.md`、`projectctl.py` 或任何新的当前真相源。
4. 不删除旧 validator；在 parity 证明完成前，legacy chain 是唯一权威 pass/fail。
5. 保持 `Project Governance` workflow/job 的 Required Check 身份、`contents: read` 权限、full/nightly/release gate。
6. READ_ONLY、PLAN、CI 必须零 tracked 写入。
7. 禁止写入 `EEI/**`、`arxiv-daily-push/**` 和其他项目业务目录。
8. 一次只执行一个 Roadmap Task ID 和一个 Acceptance 集合。
9. 未知或 Git/base/diff 失败必须 fail-closed，不能解释成“无变更”。
10. 禁止以缩短输出为由省略错误、Acceptance、Evidence、回滚或发布阻塞信息。

## 启动

只执行 `S1PAT01`：

```bash
git branch --show-current
git rev-parse HEAD
git status --short
git log -1 --format='%H%n%s%n%cI'
```

然后读取：

- `AGENTS.md`
- `docs/governance/STANDARD.md`
- `governance/projects.yaml`
- 本包 `01_BASELINE_AND_SCOPE.md`
- 本包 `roadmap/ROADMAP.md`

输出不超过一屏：实际基线、允许/禁止范围、当前 Task、测试、风险、回滚、Stop Conditions。完成后停止。

## S1/S2：真实两轮六 Agent 审查硬门禁

### Round 1

主 Agent 必须显式 spawn **恰好 3 个独立只读子 Agent**，分别使用：

- `prompts/round1/agent_1_security_code.md`
- `prompts/round1/agent_2_runtime_stress.md`
- `prompts/round1/agent_3_information_ux_architecture.md`

约束：

- 三个子 Agent 不得读取彼此输出；
- 不得递归 spawn；
- 不得修改仓库；
- 输出写到 `.git/codex-review/m1/<run_id>/round1/` 或系统临时目录；
- 每份审查报告符合 `schemas/review_report.schema.json`，其中每项 finding 符合 `schemas/finding.schema.json`；
- 主 Agent 等待三份报告后，使用 `prompts/consolidate_round1.md` 汇总。

### Round 2

使用三个**全新会话/全新子 Agent**，分别使用：

- `prompts/round2/agent_4_security_adversarial.md`
- `prompts/round2/agent_5_runtime_fault_injection.md`
- `prompts/round2/agent_6_information_adversarial.md`

它们可以读取 Round 1 的**汇总**与候选 M1-S 设计，但不能读取彼此未完成输出。主 Agent等待三份报告后，使用 `prompts/consolidate_final.md` 完成跨轮裁决。

只有以下条件都成立，`S2PCT02` 才能给出 `PROCEED_SHADOW`：

- 六份独立报告齐全；
- P0/P1 没有未裁决证据冲突；
- 候选不改变权威链、双平面、T2/T3 或 Required Check；
- 允许文件、测试、回滚和 Stop Conditions 已锁定；
- S1/S2 前后 Git 状态差异为零。

否则只允许 `FIX-ONE` 或 `STOP`。

## S3-S5：实施规则

- 测试先行；先让反例测试失败，再实现。
- S3 只做 shadow instrumentation：check plan、pre/post 零写入、compact stdout、完整临时 JSON、timing telemetry。
- 不允许候选影响 required pass/fail。
- S4 完成 legacy/candidate parity、故障注入、并发/取消/清理和至少两个真实变更样本。
- 任何 false negative 立即 STOP。
- S5 只有 Owner Gate 通过才允许有限激活；保持 workflow/job 名称不变。
- 所有完整证据放 runner temp、CI artifact 或 `.git/codex-review/`，不能提交运行缓存。

## 每个 Task 开始前必须输出

1. 实际 HEAD 与 base ref；
2. Task ID、numeric sequence、Acceptance；
3. 将读取和修改的文件；
4. 运行命令；
5. 风险、Stop Conditions、回滚；
6. 是否触及 EEI/arxiv（应为否）；
7. 预计输出与证据目录。

## 每个 Task 完成后必须输出

- `SHIP` / `FIX-ONE` / `STOP`；
- 实际 diff summary；
- 实际运行命令、退出码、耗时；
- legacy/candidate 差异；
- tracked 写入证明；
- P0-P3 问题状态；
- 回滚命令；
- 下一唯一 Task；
- 不得自动启动下一 Task。
