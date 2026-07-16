# Agent Loop Engineering

本目录定义 CodexProject 的 Automation C 控制面。它消费 Owner 已批准的
dual-plane Task Pack，不替代 `AGENTS.md`、`docs/governance/STANDARD.md` 或
项目级治理。

## 核心流程

| 步骤 | 责任方 | 产物 |
|---|---|---|
| 1 | Owner + planner | 明确范围并批准 dual-plane Task Pack |
| 2 | Local/read-only validator | 校验 machine plane、human plane、routing 和 V1/V2 ID binding |
| 3 | Isolated implementation | 生成已验证的单一临时 transaction branch |
| 4 | External authenticated publisher | 创建一个绑定 Task/Acceptance/head/base 的非 draft PR |
| 5 | `Project Governance / governance` | 只读验证 exact PR head；无 path filter |
| 6 | Trusted settlement | exact-head squash merge 或 terminal close，再删除 exact trusted ref |
| 7 | Janitor | 只处理 marker-bound stale/duplicate transaction |
| 8 | Owner/evidence | 验证 open PR、standalone Issue、transaction branch 均为 0 |

## 架构原则

- Task Pack 是范围与验收事实源。
- Issue 不用作 queue、lock、audit log 或运行状态。
- Publisher credential 不进入 repository workflow、secret 或 artifact。
- Required CI 只读；Settlement/Janitor 独立且不 checkout/执行 PR code。
- 所有 state transition 必须绑定 exact head/base SHA 和 transaction marker。
- 未知 actor、fork、draft、stale head/base、conflict、缺失 required check 均 fail closed。
- 本 bootstrap 禁止自动生产部署。
- Live ruleset 未激活时必须报告 `REMOTE_ACTIVATION_DEFERRED`。

## 入口文档

- `TASK_PACK_DUAL_PLANE_SPEC.md`: Task Pack contract。
- `TASK_PACK_TEMPLATE.md`: Owner/planner template。
- `RUN_APPROVED_TASKPACK.md`: read-only validation 与外部 publisher 操作。
- `AUTOMATION.md`: role separation、settlement 与 Zero-Open contract。
- `MERGE_POLICY.md`: terminal settlement gate。
- `AUTOMATION_C_BOOTSTRAP.md`: owner live-activation checklist。
- `VALIDATION_MATRIX.md`: validation coverage。
- `SCORECARD.md`、`RETROSPECTIVE_LOG.md`: historical evidence；其中旧 Issue 流程
  只代表当时事实，不是现行指令。
