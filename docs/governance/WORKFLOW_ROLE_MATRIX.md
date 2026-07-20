# Workflow Role Matrix

- Policy: `CodexProject-workflow-security-v1`
- Owner: `@LinzeColin`
- Action pins resolved: `2026-07-15T14:21:17Z`

## Active root workflows

| Workflow | Role | Purpose | Triggers | Permissions | Jobs | Trust boundary | Failure behavior |
|---|---|---|---|---|---|---|---|
| `.github/workflows/agent-loop-retrospective.yml` | `transaction_retrospective` | Create an advisory post-close retrospective and PR comment; never settlement evidence. | `pull_request`, `workflow_dispatch` | `contents:read, pull-requests:write` | `retrospective` | `untrusted_prompt_readonly_sandbox` | N/A output without the model secret; comment and artifact remain advisory. |
| `.github/workflows/agent-loop-review-existing-pr.yml` | `advisory_pr_review` | Review a PR in a read-only Codex sandbox and publish an advisory comment. | `pull_request`, `workflow_dispatch` | `contents:read, pull-requests:write` | `review-existing-pr` | `untrusted_prompt_readonly_sandbox` | Fail before review when the model secret is unavailable; no merge authority. |
| `.github/workflows/agent-loop-run-approved-taskpack.yml` | `taskpack_validation` | Validate an explicitly supplied Task Pack without branch, PR, Issue, or merge mutation. | `workflow_dispatch` | `contents:read` | `validate-taskpack` | `manual_input_via_environment_readonly` | Validation failure stops without creating a transaction object. |
| `.github/workflows/agent-loop-settlement.yml` | `transaction_settlement` | Settle or janitor one marker-bound transaction using trusted default-branch code and live APIs only. | `schedule`, `workflow_dispatch`, `workflow_run` | `actions:read, checks:read, contents:write, issues:write, pull-requests:write` | `janitor`, `settlement` | `trusted_default_branch_live_api_only` | Fail closed; close/delete only exact authorized objects, and never execute PR code or artifacts. |
| `.github/workflows/linze-golden-path.reusable.yml` | `golden_path_coolify_deploy` | 可复用(workflow_call)golden-path 模板:各服务 caller 调用它,verify→触发 Coolify 部署→home 跳转同步(PR #285 的统一部署骨架)。 | `workflow_call` | `contents:read` | `deploy`, `home-sync`, `smoke`, `verify` | `reusable_workflow_call_only;Coolify secrets 由 caller 经 secrets 传入,不硬编码;不可信 inputs 走 env 不拼进 run` | verify 失败阻断部署;部署未入队 job 失败;仅被显式 caller 调用,不自触发。 |
| `.github/workflows/project-governance.yml` | `transaction_ci` | Run the one required read-only transaction CI role and scheduled/manual full governance. | `pull_request`, `push`, `schedule`, `workflow_dispatch` | `contents:read` | `governance` | `required_ci_executes_pr_code_readonly` | Any policy, validation, semantic, artifact, or supply-chain failure blocks settlement. |

## Resolved third-party action pins

| Repository | Requested tag | Commit SHA | Resolution source |
|---|---|---|---|
| `actions/checkout` | `v4` | `34e114876b0b11c390a56381ad16ebd13914f8d5` | https://api.github.com/repos/actions/checkout/git/ref/tags/v4 |
| `actions/checkout` | `v5` | `93cb6efe18208431cddfb8368fd83d5badbf9bfd` | https://api.github.com/repos/actions/checkout/git/ref/tags/v5 |
| `actions/setup-node` | `v4` | `49933ea5288caeca8642d1e84afbd3f7d6820020` | https://api.github.com/repos/actions/setup-node/git/ref/tags/v4 |
| `actions/setup-python` | `v5` | `a26af69be951a213d495a4c3e4e4022e16d87065` | https://api.github.com/repos/actions/setup-python/git/ref/tags/v5 |
| `actions/setup-python` | `v6` | `ece7cb06caefa5fff74198d8649806c4678c61a1` | https://api.github.com/repos/actions/setup-python/git/ref/tags/v6 |
| `actions/upload-artifact` | `v4` | `ea165f8d65b6e75b540449e92b4886f43607fa02` | https://api.github.com/repos/actions/upload-artifact/git/ref/tags/v4 |
| `actions/upload-artifact` | `v7` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | https://api.github.com/repos/actions/upload-artifact/git/ref/tags/v7 |
| `openai/codex-action` | `v1` | `52fe01ec70a42f454c9d2ebd47598f9fd6893d56` | https://api.github.com/repos/openai/codex-action/git/ref/tags/v1 |

## Merged or retired workflow paths

- `OpenAIDatabase/.github/workflows/ci.yml` → `LinzeColin/AgentDatabase:.github/workflows/dual-plane.yml`: MERGED_AND_DELETE_INVALID_NESTED_WORKFLOW. GitHub does not execute nested project workflows; unique Memory Atlas jobs were preserved in the root workflow. 该根工作流已随 OpenAIDatabase 于 2026-07-17 迁往 AgentDatabase。 替代物在 LinzeColin/AgentDatabase 仓内的 Dual-Plane Governance 工作流。
- `.github/workflows/kmfa-dual-plane.yml` → `LinzeColin/KMOS:.github/workflows/dual-plane.yml`: MIGRATED_WITH_PROJECT. KMFA 已于 2026-07-17 迁往 LinzeColin/KMOS（仓库拆分第6波，权限隔离）；项目专属工作流随项目一并迁走，本仓不再持有。 替代物在 LinzeColin/KMOS 仓内的 Dual-Plane Governance 工作流。
- `.github/workflows/openai-database-ci.yml` → `LinzeColin/AgentDatabase:.github/workflows/dual-plane.yml`: MIGRATED_WITH_PROJECT. OpenAIDatabase 已于 2026-07-17 迁往 LinzeColin/AgentDatabase（仓库拆分第6波，权限隔离）；项目专属工作流随项目一并迁走，本仓不再持有。 替代物在 LinzeColin/AgentDatabase 仓内的 Dual-Plane Governance 工作流。
- `.github/workflows/arxiv-daily-push-liveness.yml` → `LinzeColin/MetaDatabase:.github/workflows/arxiv-daily-push-liveness.yml`: MIGRATED_WITH_PROJECT_TO_ANOTHER_REPOSITORY. arxiv-daily-push 于 2026-07-20 随仓库拆分迁往 LinzeColin/MetaDatabase（tree sha 位级一致、完整历史保留）；本工作流随项目迁走，并在目标仓实跑验证（stage1-bootstrap 已 success）。本仓不再持有其代码路径，故此处退休、替代物指向目标仓同名工作流。
- `.github/workflows/arxiv-daily-push-manual-delivery-test.yml` → `LinzeColin/MetaDatabase:.github/workflows/arxiv-daily-push-manual-delivery-test.yml`: MIGRATED_WITH_PROJECT_TO_ANOTHER_REPOSITORY. arxiv-daily-push 于 2026-07-20 随仓库拆分迁往 LinzeColin/MetaDatabase（tree sha 位级一致、完整历史保留）；本工作流随项目迁走，并在目标仓实跑验证（stage1-bootstrap 已 success）。本仓不再持有其代码路径，故此处退休、替代物指向目标仓同名工作流。
- `.github/workflows/arxiv-daily-push-phase12-cloud-dry-run.yml` → `LinzeColin/MetaDatabase:.github/workflows/arxiv-daily-push-phase12-cloud-dry-run.yml`: MIGRATED_WITH_PROJECT_TO_ANOTHER_REPOSITORY. arxiv-daily-push 于 2026-07-20 随仓库拆分迁往 LinzeColin/MetaDatabase（tree sha 位级一致、完整历史保留）；本工作流随项目迁走，并在目标仓实跑验证（stage1-bootstrap 已 success）。本仓不再持有其代码路径，故此处退休、替代物指向目标仓同名工作流。
- `.github/workflows/arxiv-daily-push-production-trial.yml` → `LinzeColin/MetaDatabase:.github/workflows/arxiv-daily-push-production-trial.yml`: MIGRATED_WITH_PROJECT_TO_ANOTHER_REPOSITORY. arxiv-daily-push 于 2026-07-20 随仓库拆分迁往 LinzeColin/MetaDatabase（tree sha 位级一致、完整历史保留）；本工作流随项目迁走，并在目标仓实跑验证（stage1-bootstrap 已 success）。本仓不再持有其代码路径，故此处退休、替代物指向目标仓同名工作流。
- `.github/workflows/arxiv-daily-push-provisioning-audit.yml` → `LinzeColin/MetaDatabase:.github/workflows/arxiv-daily-push-provisioning-audit.yml`: MIGRATED_WITH_PROJECT_TO_ANOTHER_REPOSITORY. arxiv-daily-push 于 2026-07-20 随仓库拆分迁往 LinzeColin/MetaDatabase（tree sha 位级一致、完整历史保留）；本工作流随项目迁走，并在目标仓实跑验证（stage1-bootstrap 已 success）。本仓不再持有其代码路径，故此处退休、替代物指向目标仓同名工作流。
- `.github/workflows/arxiv-daily-push-real-backfill.yml` → `LinzeColin/MetaDatabase:.github/workflows/arxiv-daily-push-real-backfill.yml`: MIGRATED_WITH_PROJECT_TO_ANOTHER_REPOSITORY. arxiv-daily-push 于 2026-07-20 随仓库拆分迁往 LinzeColin/MetaDatabase（tree sha 位级一致、完整历史保留）；本工作流随项目迁走，并在目标仓实跑验证（stage1-bootstrap 已 success）。本仓不再持有其代码路径，故此处退休、替代物指向目标仓同名工作流。
- `.github/workflows/arxiv-daily-push-scheduled.yml` → `LinzeColin/MetaDatabase:.github/workflows/arxiv-daily-push-scheduled.yml`: MIGRATED_WITH_PROJECT_TO_ANOTHER_REPOSITORY. arxiv-daily-push 于 2026-07-20 随仓库拆分迁往 LinzeColin/MetaDatabase（tree sha 位级一致、完整历史保留）；本工作流随项目迁走，并在目标仓实跑验证（stage1-bootstrap 已 success）。本仓不再持有其代码路径，故此处退休、替代物指向目标仓同名工作流。
- `.github/workflows/arxiv-daily-push-stage1-bootstrap.yml` → `LinzeColin/MetaDatabase:.github/workflows/arxiv-daily-push-stage1-bootstrap.yml`: MIGRATED_WITH_PROJECT_TO_ANOTHER_REPOSITORY. arxiv-daily-push 于 2026-07-20 随仓库拆分迁往 LinzeColin/MetaDatabase（tree sha 位级一致、完整历史保留）；本工作流随项目迁走，并在目标仓实跑验证（stage1-bootstrap 已 success）。本仓不再持有其代码路径，故此处退休、替代物指向目标仓同名工作流。
- `.github/workflows/arxiv-daily-push-trial-start.yml` → `LinzeColin/MetaDatabase:.github/workflows/arxiv-daily-push-trial-start.yml`: MIGRATED_WITH_PROJECT_TO_ANOTHER_REPOSITORY. arxiv-daily-push 于 2026-07-20 随仓库拆分迁往 LinzeColin/MetaDatabase（tree sha 位级一致、完整历史保留）；本工作流随项目迁走，并在目标仓实跑验证（stage1-bootstrap 已 success）。本仓不再持有其代码路径，故此处退休、替代物指向目标仓同名工作流。
- `.github/workflows/arxiv-daily-push-visual-gate.yml` → `LinzeColin/MetaDatabase:.github/workflows/arxiv-daily-push-visual-gate.yml`: MIGRATED_WITH_PROJECT_TO_ANOTHER_REPOSITORY. arxiv-daily-push 于 2026-07-20 随仓库拆分迁往 LinzeColin/MetaDatabase（tree sha 位级一致、完整历史保留）；本工作流随项目迁走，并在目标仓实跑验证（stage1-bootstrap 已 success）。本仓不再持有其代码路径，故此处退休、替代物指向目标仓同名工作流。

## Hard gates

- Every root workflow has one owner, purpose, unique role, trigger set, exact permissions, timeout, concurrency, and failure behavior.
- Third-party actions use allowlisted 40-character commit SHAs; movable tags are comments only.
- `pull_request_target` and nested project workflows are forbidden.
- Untrusted strings enter shell only through environment variables; prompt-bearing workflows use a read-only Codex sandbox.
- The one Settlement role uses trusted default-branch code and live APIs only; it never checks out PR code or consumes artifacts/caches.
