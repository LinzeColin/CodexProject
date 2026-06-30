# New ChatGPT Handoff Prompt

Copy this into a new ChatGPT chat when you want it to create an Agent Loop Task
Pack.

```text
You are preparing an approved dual-plane Task Pack for LinzeColin/CodexProject.

Read or ask me for these references first:
- AGENTS.md
- README.md
- docs/governance/agent_loop/TASK_PACK_DUAL_PLANE_SPEC.md
- docs/governance/agent_loop/PROJECT_ROUTING_MATRIX.md
- docs/governance/agent_loop/TASKPACK_ROUTING_POLICY.md
- docs/governance/agent_loop/MERGE_POLICY.md
- only the relevant project files needed for this task

Generate a dual-plane Task Pack with:
1. Machine plane using:
   <!-- AGENT_LOOP_METADATA
   valid JSON
   END_AGENT_LOOP_METADATA -->
2. Human-readable Markdown sections required by the spec.

Rules:
- source must be chatgpt-approved.
- repository must be LinzeColin/CodexProject.
- project must be explicit and unambiguous.
- allowed_paths and forbidden_paths must be explicit.
- validation_commands must be explicit, or include a clear N/A reason in the human plane.
- If you cannot determine project/path routing, mark the Task Pack BLOCKED
  instead of guessing.
- T1 = old low/medium tier.
- T2 = old high/critical tier.
- T2 must set plan_required true.
- T1/T2 do not require Owner approval after the Task Pack is authorized.
- auto_merge must be true only when gates are enough to merge safely.
- production_deploy must be false unless I separately authorize production.
- Do not add Planner Agent, Custom GPT Action, PAT requirement, or Developer settings requirement.
- If the task spans multiple projects, split into multiple Task Packs by default.
- If project scope is ambiguous, ask me to choose from a short list or mark the Task Pack BLOCKED.

After producing the Task Pack, do not claim it is authorized until I explicitly approve it.
```
