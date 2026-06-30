# Agent Loop Engineering

本目录定义 CodexProject 的 Agent Loop 自动化脚手架。它只覆盖 Owner 已批准
的 dual-plane Task Pack 执行流程，不替代现有 `AGENTS.md`、
`docs/governance/STANDARD.md` 或项目级治理。

## 核心流程

| 步骤 | 责任方 | 产物 |
|---|---|---|
| 1 | Owner + ChatGPT | 讨论需求并形成 dual-plane Task Pack |
| 2 | Owner | 明确授权 Task Pack |
| 3 | Owner / automation | 选择 workflow paste、issue label 或 repository_dispatch 入口 |
| 4 | GitHub Actions | 把批准的 Task Pack 统一写入 `/tmp/agent_loop/taskpack.md` |
| 5 | 脚本 | 校验 Task Pack 的 machine plane 和 human plane |
| 6 | GitHub Actions | 创建 audit issue 记录批准文本和 run link |
| 7 | Codex | plan-first，生成计划但不得改文件 |
| 8 | 脚本 | 验证 plan、确认 plan 阶段 git diff 为空 |
| 9 | Codex | 按 Task Pack 实现 |
| 10 | 脚本/命令 | 运行 validation commands 和 changed-files policy |
| 11 | GitHub Actions | 创建 PR |
| 12 | Codex | 自动 review |
| 13 | Architect Review | 可行时运行 ChatGPT-style 架构复审，不可行时报告 N/A |
| 14 | Codex | 在有限次数内 autofix |
| 15 | 脚本 | 执行 merge policy |
| 16 | GitHub Actions | gates 通过后 squash merge，关闭 audit issue |

## 架构原则

- Task Pack 是唯一事实源。
- GitHub Action 不创建 Planner Agent。
- GitHub Action 不从模糊 issue 文本推断或重新生成 Task Pack。
- 支持 `workflow_dispatch` 手动粘贴作为 fallback。
- 支持 `issues:labeled`：issue body 必须就是已批准 Task Pack。
- 支持 `repository_dispatch` 的 `agent_loop_taskpack` 事件，为未来 ChatGPT/connector/webhook 集成预留。
- 不需要 Custom GPT Action。
- 不需要 GitHub Developer settings。
- 不需要 PAT；默认使用 `GITHUB_TOKEN`。
- T1 和 T2 都不需要 Owner 在 plan 与 implementation 之间再次批准。
- T2 必须 plan-first，但 plan 验证通过后可继续自动实现。
- 本 bootstrap 禁止自动生产部署。

## 目录

- `TASK_PACK_DUAL_PLANE_SPEC.md`: dual-plane Task Pack 规范。
- `TASK_PACK_TEMPLATE.md`: Owner/ChatGPT 可复制模板。
- `RUN_APPROVED_TASKPACK.md`: Owner 使用三种入口的步骤。
- `AUTOMATION.md`: 自动化架构和安全边界。
- `MERGE_POLICY.md`: T1/T2 自动合并规则。
- `RELEASE_GATE.md`: merge、staging、production、acceptance、rollback 的边界。
- `VALIDATION_MATRIX.md`: 校验项矩阵。
- `SCORECARD.md`: PR/audit scorecard。
- `RETROSPECTIVE_LOG.md`: retrospective 手工记录入口。
