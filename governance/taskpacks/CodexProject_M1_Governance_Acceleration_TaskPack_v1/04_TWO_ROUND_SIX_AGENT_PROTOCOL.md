# 两轮六 Agent 独立审查协议

## 独立性

- Round 1：Agent 1/2/3 使用三个独立上下文，同时只读。
- Round 2：Agent 4/5/6 必须是全新上下文，不复用 Round 1 Agent。
- 同轮 Agent 不得相互读取结果。
- Round 2 只读取 Round 1 consolidated summary，不读取未裁决原始讨论。
- 子 Agent 不得递归 spawn。
- 主 Agent/Integrator 只在全员完成后汇总。

## 证据纪律

每项 finding 必须包含：

```text
finding_id
round
agent_role
category
title
severity: P0/P1/P2/P3
confidence: high/medium/low
merge_blocking: true/false/conditional
evidence: file + symbol/line + command/output
reproduction
impact
recommended_fix
required_tests
status: VERIFIED/PARTIALLY_VERIFIED/PROPOSED/UNKNOWN/CONTRADICTED
```

没有证据的 P0/P1 不得直接宣称已证实；若无法测试但风险高，标为 `UNKNOWN + BLOCKED`，并给出解锁任务。

## 严重度

- P0 Critical：可能破坏仓库、泄露凭据、绕过发布门禁或造成不可逆数据损失；阻塞。
- P1 High：可能出现 false negative、错误合并、范围越界、竞态、持续 CI 失败或事实漂移；阻塞。
- P2 Medium：显著影响速度、可维护性、可读性或可定位性；通常不单独阻塞，但需排期。
- P3 Low：局部改善；不阻塞。

## 汇总规则

1. 先重放证据，再去重。
2. 同源问题保留所有 Agent 的独立确认。
3. 严重度冲突时记录双方理由，不用多数票掩盖证据。
4. 合并阻塞以实际影响与可复现性决定。
5. 汇总输出：问题、严重度、是否阻塞、建议修复、测试、Owner 决策。
6. 最终只允许 `PROCEED_SHADOW`、`FIX-ONE` 或 `STOP`。

## 输出目录

```text
.git/codex-review/m1/<run_id>/
├── baseline.json
├── round1/
│   ├── agent1.json
│   ├── agent2.json
│   └── agent3.json
├── round1_consolidated.json
├── candidate_m1s.json
├── round2/
│   ├── agent4.json
│   ├── agent5.json
│   └── agent6.json
└── final_adjudication.json
```

该目录必须保持 untracked；CI 使用 runner temp/artifact。
