# WDA Handoff

## Current Goal

Create a clean single-project WDA workspace and GitHub-tracked project shell.

## Current Status

- Local worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/WDA`
- Project directory: `WDA/`
- Branch: `codex/wda`
- Product scope: not defined
- Implementation status: no runtime code yet

## Key Decisions

- Keep WDA as one long-lived project worktree.
- Do not create a full CodexProject copy for each chat.
- Do not expand unrelated project directories into this worktree.
- Treat current WDA files as governance/bootstrap only, not product implementation.

## Files To Read First

- `AGENTS.md`
- `WDA/AGENTS.md`
- `WDA/README.md`
- `WDA/docs/HANDOFF.md`
- `WDA/功能清单.md`
- `WDA/开发记录.md`
- `WDA/模型参数文件.md`
- `WDA/docs/governance/project.yaml`
- `WDA/docs/governance/roadmap.yaml`

## Validation

Lightweight project check:

```bash
/usr/bin/python3 -B scripts/lean_governance.py check-render --project WDA
```

Do not expand unrelated projects to satisfy full monorepo validation unless the user explicitly asks for a root-governance run.

## Next Step

Define WDA requirements before implementation: product purpose, users, workflows, data boundaries, model/formula applicability, first stage roadmap, acceptance criteria, risks, and stop conditions.
