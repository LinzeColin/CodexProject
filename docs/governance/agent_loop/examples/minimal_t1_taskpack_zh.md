<!-- AGENT_LOOP_METADATA
{
  "agent_loop_version": "1.0",
  "source": "chatgpt-approved",
  "repository": "LinzeColin/CodexProject",
  "risk_tier": "T1",
  "auto_merge": true,
  "plan_required": false,
  "production_deploy": false,
  "project": "agent-loop",
  "roadmap_task_id": "AGENT-LOOP-ZH-T01",
  "acceptance_id": "AGENT-LOOP-ZH-A01",
  "allowed_paths": [
    "docs/governance/agent_loop/RETROSPECTIVE_LOG.md"
  ],
  "forbidden_paths": [
    "AGENTS.md",
    ".github/workflows/**",
    ".github/ISSUE_TEMPLATE/**",
    ".github/PULL_REQUEST_TEMPLATE/**",
    ".github/CODEOWNERS",
    "scripts/**",
    "Alpha/**",
    "EEI/**",
    "FIFA/**",
    "KMFA/**",
    "MetaDatabase/**",
    "OpenAIDatabase/**",
    "KM_IDSystem/**",
    "PFI/**",
    "QBVS/**",
    "Serenity-Alipay/**",
    "arxiv-daily-push/**",
    "whkmSalary/**",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    ".env",
    ".env.*"
  ],
  "validation_commands": [
    "python3 -m py_compile scripts/agent_loop/*.py",
    "python3 scripts/agent_loop/validate_taskpack.py --taskpack docs/governance/agent_loop/examples/minimal_t1_taskpack.md",
    "python3 scripts/agent_loop/validate_taskpack.py --taskpack docs/governance/agent_loop/examples/minimal_t1_taskpack_zh.md",
    "git diff --check"
  ],
  "max_autofix_loops": 0,
  "executor_mode": "codex-one-shot",
  "enable_codex_review": false,
  "enable_architect_review": false,
  "max_paid_codex_calls": 1,
  "roi_budget_usd": 2.0,
  "value_score": 1,
  "debug_rerun_requires_artifact_review": true
}
END_AGENT_LOOP_METADATA -->

# Codex Task Pack：中文 T1 最小样例

## 1. 人类摘要

| 项目 | 内容 |
|---|---|
| Project | agent-loop |
| Risk Tier | T1 |
| Production Deploy | false |

## 2. 背景

这个样例用于验证 Agent Loop 可以接受中文优先、编号式的人类可读 Task Pack。

## 3. 范围

仅用于本地 validator 回归测试，不要求真实执行自动化修改。

## 4. 允许读取的文件

- `docs/governance/agent_loop/RETROSPECTIVE_LOG.md`
- `docs/governance/agent_loop/TASK_PACK_DUAL_PLANE_SPEC.md`

## 5. 允许修改的文件

- `docs/governance/agent_loop/RETROSPECTIVE_LOG.md`

## 6. 禁止修改的文件

- `AGENTS.md`
- `.github/workflows/**`
- `scripts/**`
- 所有业务项目目录。

## 7. 实现要求

- 不加入 Planner Agent。
- 不部署生产。
- 不修改业务项目目录。

## 8. 验收标准

- 中文编号 heading 可以通过 Task Pack validator。
- metadata 仍然严格校验。
- 只允许 agent-loop 范围内的文档任务。

## 9. Validation Tests

- `python3 -m py_compile scripts/agent_loop/*.py`
- `python3 scripts/agent_loop/validate_taskpack.py --taskpack docs/governance/agent_loop/examples/minimal_t1_taskpack_zh.md`
- `git diff --check`

## 10. Stop Conditions

- 如果需要修改业务项目目录，必须停止。
- 如果需要生产部署，必须停止。
- 如果 project scope 不明确，必须停止。

## 11. Review Requirements

- 检查 scope drift。
- 检查是否只在允许路径内修改。
- 检查是否仍符合 T1/T2 策略。

## 12. Rollback Plan

如真实执行后需要回滚，使用 `git revert <merge_commit>`。

## 13. Codex 最终结果包

最终报告必须包含 summary、files changed、commands run、exact results、
known risks 和 rollback plan。
