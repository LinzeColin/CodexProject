# PFI v0.2.4 Post-Overall Consistency Remediation

## Run Boundary

本轮只执行 `post-overall consistency remediation / Phase R1`。

- 不执行 overall re-review。
- 不执行 GitHub upload。
- 不重装 app bundle。
- 不展开 `MetaDatabase/` sparse 路径。
- 不写入、复制、清理、删除或改写真实财务数据。

## Findings

1. Cloudflare L2 canonical render 将三份 owner 入口重生成为当前事实视图，v0.2.4 overall closeout 历史未进入 `project.yaml` 和 `roadmap.yaml`，导致 v0.2.4 overall regression 失败。
2. v0.2.3/v0.2.4 read model 只支持 filesystem `MetaDatabase/PFI`；长期 PFI sparse worktree 未展开该路径时，当前 Git tree 中已跟踪的真实数据被误判为 `source_missing`。

## Remediation Contract

- v0.2.4 closeout 历史必须写入 canonical governance，再由既有 renderer 生成三份 owner 入口。
- 默认真实数据路径不存在但当前 Git tree 含完整数据时，read model 只读 `HEAD:MetaDatabase/PFI`。
- 显式 `data_root` 不允许自动回退到 Git tree。
- Git-tree 模式先把 `HEAD` 固定为不可变 commit OID，并设置 `GIT_NO_LAZY_FETCH=1`；缺失 object 必须 fail closed，不得隐式联网补取或写入 object store。
- filesystem 与 Git-tree 均以 `MetaDatabase/PFI` 相对路径和原始 bytes 计算同一 canonical evidence hash。
- filesystem 与 git-tree 模式必须得到同一真实数据合同：4 个 raw CSV、8815 条 processed 记录、as of `2026-06-03`。
- R1 是 feature/evidence/roadmap acceptance，不是独立模型；模型登记继续只有 `MOD-PFI-001`。

## TDD Red Evidence

- `test_v024_overall_project_review.py::test_docs_status_stop_after_overall_upload`：owner 入口缺少 v0.2.4 closeout facts。
- `test_v023_stage6_core_metrics.py::test_phase61_input_discovers_current_metadatabase_real_files`：得到 `not_mounted`，预期 `ready`。
- `test_v024_stage4_phase42_read_model_link.py::test_read_model_status_uses_real_metadatabase_and_preserves_blocked_states`：缺少 `storage_mode`。

## Current Status

Phase R1 local gate: pass。

- Focused remediation tests: `33 passed`。
- v0.2.3 compatibility regression: `200 passed`。
- v0.2.4 regression: `219 passed`。
- Python compile、Node syntax、`git diff --check -- PFI`: pass。
- `check-render --project PFI`: `drift_count=0`、`reference_issue_count=0`。
- 独立只读复核：`APPROVED`，Critical/Important/Minor 均为零；前一轮 5 项 finding 全部关闭。
- 当前 Git tree 真实数据合同：`storage_mode=git_tree`、4 个 raw CSV、8815 条 processed 记录、as of `2026-06-03`。

## Next Gate

停止在本地 Phase R1。下一轮只执行 v0.2.4 overall re-review；本轮未 commit、未 push、未重装 app。
