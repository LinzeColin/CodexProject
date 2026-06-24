# Codex Setup for Governed Development

This repository stores the review-3 governance framework in GitHub. Local Codex
Personalization and `~/.codex/config.toml` remain user-level settings, but the
canonical wording is backed up here so agents can reproduce the setup.

## Personalization

Recommended Codex Settings -> Personalization:

- Personality: `Pragmatic`
- Custom Instructions:

```text
所有非琐碎的软件开发任务默认进入 Governed Development 流程。

1. 开始前必须读取当前生效的全局与仓库 AGENTS.md。
2. 软件开发、重构、功能实现、模型调整、发布和多文件修复必须显式调用 $codex-dex。
3. 默认先进行 PLAN / READ-ONLY，限定一个项目、一个 TASK_ID 和一个 ACCEPTANCE_ID。
4. 修改前必须列出将读取的文件、将修改的文件、测试命令、风险和回滚方案。
5. 模型、公式、评分规则、权重、阈值、决策门禁、fallback 或业务计算逻辑发生变化时，必须同步更新项目治理文件。
6. 每次有意义的实现必须追加开发事件，更新任务状态、验收证据、版本矩阵和追踪矩阵。
7. 不得根据 commit 数虚构迭代轮数，不得虚构公式、参数、测试结果或历史版本。
8. Validator 或 focused tests 未通过时，任务只能保持 in_progress 或 blocked，不得标记 completed。
9. 每次只处理一个项目、一个任务和一个验收目标，不进行无关全仓扫描或顺手重构。
```

## User Config Template

Use `.codex/config.template.toml` as the repository-backed template for
`~/.codex/config.toml`. Do not set `model_instructions_file`; it replaces
instead of supplements the normal instruction stack.

## Repository Skill

The governed development skill lives at:

```text
.agents/skills/codex-dex/SKILL.md
```

Use `$codex-dex` for non-trivial implementation, refactoring, model changes,
release preparation, or multi-file engineering tasks.

## Stop Hook

The Stop Hook lives at:

```text
.codex/hooks.json
.codex/hooks/governance_stop.py
```

It runs:

```bash
python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic
```

Codex must trust this repository before project hooks are loaded. Recursive Stop
passes are still revalidated; the hook may stop after a bounded number of failed
repair loops, but it must not unconditionally pass a failed second Stop.

Run setup diagnostics with:

```bash
python3 scripts/governance_setup_doctor.py --json
```

The doctor can verify repository hook files. Local Codex trust and GitHub
no-bypass settings remain `UNVERIFIED` unless authenticated evidence is
available.

## GitHub Required CI

`.github/workflows/project-governance.yml` runs governance validation on PRs,
pushes to `main`, and manual all/project/changed-only scopes.

Pull requests run the changed-scope sync gate:

```bash
python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic
```

Pushes to `main` run the same changed-scope sync gate against
`github.event.before` before the all-project audit:

```bash
python3 scripts/validate_project_governance.py --changed-only --enforce-sync --semantic --base-ref "$GOVERNANCE_BASE_REF"
```

Pushes and manual full audits also run all-project semantic drift reporting:

```bash
python3 scripts/validate_project_governance.py --all --semantic --drift-report
python3 scripts/generate_governance_dashboard.py --write --all --root-artifact-dir /tmp/governance-generated-views
git diff --exit-code -- ':(glob)**/docs/governance/STATUS.md' ':(glob)**/docs/governance/OWNER_STATUS.md'
```

Successful CI writes and validates a post-commit attestation with:

```bash
python3 scripts/validate_ci_attestation.py write ...
python3 scripts/validate_ci_attestation.py validate --file <attestation.json>
```

The Project Governance workflow must upload that attestation and the setup
doctor report as a GitHub Actions artifact named
`project-governance-ci-attestation-<run_id>-<attempt>`. A runner-temp JSON file
alone is not durable delivery evidence.

Repository administrators must configure GitHub branch protection or rulesets
for `main` so `Project Governance / governance` is a required status check.
Without this repository setting, CI runs but cannot block merges by itself.
If branch protection cannot be verified through an authenticated API or UI
inspection, report it as `UNVERIFIED`; do not claim no-bypass enforcement.
