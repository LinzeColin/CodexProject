<!-- AGENT_LOOP_METADATA
{
  "agent_loop_version": 1,
  "source": "chatgpt-approved",
  "repository": "LinzeColin/CodexProject",
  "risk_tier": "T1",
  "auto_merge": true,
  "plan_required": false,
  "production_deploy": false,
  "project": "governance",
  "roadmap_task_id": "EXAMPLE-ESCAPE-SLASH-001",
  "acceptance_id": "AC-EXAMPLE-ESCAPE-SLASH-001",
  "allowed_paths": [
    "scripts/lean_governance.py"
  ],
  "forbidden_paths": [
    "AGENTS.md",
    "Alpha/**",
    "EEI/**",
    "FIFA/**",
    "KMFA/**",
    "MetaDatabase/**",
    "OpenAIDatabase/**",
    "OpMe_System/**",
    "PFI/**",
    "QBVS/**",
    "Serenity-Alipay/**",
    "arxiv-daily-push/**",
    "whkmSalary/**",
    ".env",
    ".env.*"
  ],
  "validation_commands": [
    "python3 -m py_compile scripts/lean_governance.py",
    "bash -lc 'printf \"%s\\n\" \"Not a directory: ./.git/codex-review/lean-governance\" | grep -q \"Not a directory: .*\\.git/codex-review/lean-governance\"'"
  ],
  "max_autofix_loops": 0,
  "executor_mode": "codex-one-shot",
  "enable_codex_review": false,
  "enable_architect_review": false,
  "max_paid_codex_calls": 1,
  "roi_budget_usd": 1.0,
  "value_score": 1,
  "debug_rerun_requires_artifact_review": true
}
END_AGENT_LOOP_METADATA -->

# Minimal T1 Escape Slash Fixture

## 1. Human Summary / 人类摘要

This fixture verifies escaped JSON backslashes and slash bilingual headings.

## 2. Background / 背景

Agent Loop Task Packs may include shell validation commands with regex escapes.

## 3. Scope / 范围

Only the metadata parser and section heading validator are in scope.

## 4. Files To Inspect / 允许读取的文件

- `scripts/agent_loop/autofill_taskpack_metadata.py`
- `scripts/agent_loop/validate_taskpack.py`

## 5. Files Allowed To Modify / 允许修改的文件

- `scripts/lean_governance.py`

## 6. Files Forbidden / 禁止修改的文件

- `AGENTS.md`
- Business project directories
- Secrets and environment files

## 7. Implementation Requirements / 实现要求

Preserve valid JSON escapes during metadata normalization and match bilingual headings only when they are Markdown level-two headings.

## 8. Acceptance Criteria / 验收标准

- Autofilled Task Pack metadata remains parseable JSON.
- `.*\\.git/codex-review/lean-governance` remains correctly escaped in the metadata JSON.
- Slash bilingual headings are accepted.

## 9. Validation Tests / 验证测试

- `python3 scripts/agent_loop/autofill_taskpack_metadata.py --input docs/governance/agent_loop/examples/minimal_t1_taskpack_escape_slash.md --output /tmp/escape_slash_normalized.md`
- `python3 scripts/agent_loop/validate_taskpack.py --taskpack /tmp/escape_slash_normalized.md`

## 10. Stop Conditions / 停止条件

Stop if metadata cannot be parsed or the fix requires modifying business project files.

## 11. Review Requirements / 复审要求

Review must confirm the change is limited to deterministic control-plane validation behavior.

## 12. Rollback Plan / 回滚方案

Revert the control-plane validation patch and remove this fixture.

## 13. Required Codex Result Pack / Codex 最终结果包

Report changed files, commands run, exact validation results, risks, and rollback.
