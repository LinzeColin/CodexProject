# ChatGPT Start Here For Agent Loop

给任何新的 ChatGPT 对话使用本文件作为入口。目标是生成 Owner 可审阅、可授权、
可直接交给 Agent Loop 的 dual-plane Task Pack。

## 必读文件

新 ChatGPT 在生成 Task Pack 前应读取或要求 Owner 提供以下上下文：

- `AGENTS.md`
- `README.md`
- `docs/governance/agent_loop/TASK_PACK_DUAL_PLANE_SPEC.md`
- `docs/governance/agent_loop/PROJECT_ROUTING_MATRIX.md`
- `docs/governance/agent_loop/TASKPACK_ROUTING_POLICY.md`
- `docs/governance/agent_loop/MERGE_POLICY.md`
- 当前任务相关项目文件，只读最小必要集合

## 生成规则

- Always generate a dual-plane Task Pack.
- Machine plane must remain strict parseable JSON inside
  `AGENT_LOOP_METADATA`.
- Human plane may be Chinese, English, or bilingual, but it must still include
  every required canonical section from `TASK_PACK_DUAL_PLANE_SPEC.md`.
- Numbered headings such as `## 1. 人类摘要` are allowed.
- Always specify `project`.
- Always specify `allowed_paths`.
- Always specify `forbidden_paths`.
- Never let Codex guess project scope.
- If routing metadata is incomplete, Agent Loop may autofill only when the
  routing matrix gives one unambiguous project; otherwise it must block.
- If project is ambiguous, ask the Owner to pick from a short list or set the
  Task Pack to `BLOCKED`.
- For multi-project work, split into multiple Task Packs by default.
- T2 requires plan-first but no owner approval.
- T1 and T2 both auto-merge only after gates pass.
- Production deploy remains disabled unless a separate Task Pack explicitly
  authorizes it.
- Owner does not need to remember exact English section names; ChatGPT should
  still produce clear `##` headings so the repository validator can map them.

## 禁止

- 不要加入 Planner Agent。
- 不要要求 Custom GPT Action。
- 不要要求 GitHub Developer settings。
- 不要要求 Owner 创建 PAT。
- 不要让 GitHub Actions 从模糊 issue 重新推断需求。
