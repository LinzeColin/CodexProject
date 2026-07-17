# KMFA 恢复与本机清理交接说明（公开安全）

更新时间：2026-07-17（Australia/Sydney）

## 目的与边界

本文件用于本机大清理前的可接手性保全。它只记录可公开共享的代码、治理、测试、skill 与恢复定位信息；不授权业务发布、原始数据处理、私有运行态上传或任何外部业务动作。

`main` 仍是当前 KMFA v0.1.4 的正式公共基线。本文件记录的 v1.5 恢复分支是一个**独立、未合并、未验收**的恢复检查点，不能被当作当前产品状态或 merge-ready 变更。

## 已上云的公共安全资产

- 仓库与项目路径：`LinzeColin/CodexProject` 的 `KMFA/`
- `main` 基线：`12d10f63d15e41cec50026d5dfd2ea0fab5a0e69`
- 恢复分支：`recovery/kmfa-v15-fuzzy`
- 恢复提交：`1ee7fb111075225dc39039263d2681a0c0acd155`
- 不可变检查点 tag：`kmfa-v15-recovery-checkpoint-20260717`
- `main` 已包含的 KMFA skill：
  - `daily_routine_check_skill/`
  - `fund-weekly-analysis-skill/`
  - `kmfa-dingtalk-attendance-skill/`
  - `mgmt-monthly-report-skill/`

恢复提交相对其公共基线的范围为 764 个 KMFA 文件（738 新增、25 修改、1 删除）；四个 skill 中只有 `mgmt-monthly-report-skill/` 在该恢复检查点中有新增差异，其余三个已在 `main` 中保存。

## 已验证的恢复检查点性质

- `git diff --check`：通过。
- 新增/修改文件的 private-runtime、raw、inbox、credential、secret 与禁入二进制路径扫描：0 命中。
- 全分支受跟踪路径中的 4 个 private-runtime 命中均为允许提交的 `.gitkeep` / `README.md` 占位文件；没有大于 5 MiB 的 blob。
- 标准凭据模式扫描唯一命中是安全测试中的私钥 PEM 拒绝样例，不是凭据。
- Git 对象完整性检查：通过。

以上是保全前的静态安全检查，不等价于业务验收、正式报告授权或恢复分支运行通过。

## 已知恢复缺口（必须显式处理）

恢复分支当前无法完成最小治理测试：

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest \
  KMFA.tests.test_v015_s03_p3_public_repository_safety_governance -q
```

失败原因是 `KMFA.tools.v015_s03_p3_public_repository_safety` 缺失。静态 import 清点共发现 15 个未解析的 `KMFA.tools` 依赖：

```text
automation
build_v015_s02_p1_requirements_merge
build_v015_s03_p2_private_derived_runtime
build_v015_s20_stage_review
check_v015_s02_p1_requirements_merge
check_v015_s02_p2_end_to_end_traceability
check_v015_s06_p2_golden_baseline_lock
check_v015_s13_p1_indicator_registry
v015_roadmap_governance_sync
v015_s02_p2_formula_trace
v015_s02_p2_lineage_contract
v015_s02_p2_requirement_trace
v015_s03_p1_read_only_root_guard
v015_s03_p3_public_repository_safety
v015_s18_stage_review_contract
```

因此状态为：`RECOVERY_SOURCE_PRESERVED_NOT_MERGE_READY`。不得 rebase、force-push、合并或以此分支宣称 v1.5 已完成。

## 私有完整性条件

原始业务数据、私有运行态、私有导出物与受保护的大型恢复归档均不属于公开 GitHub 可提交范围。它们没有被上传、也没有被本文件描述为已备份。

在删除本机受保护内容前，owner 必须把该类资产存放到一个已批准的私有归档目标，并单独记录位置、加密/访问控制、校验值与恢复演练结果。未经新的明确授权，任何 agent 不得把它们提交到本公开仓库、公开 Release 或公开 Git LFS。

## 下一位 agent 的最小接手顺序

1. `git fetch origin --tags`，确认 `main`、恢复分支与 tag 均存在。
2. 在独立 worktree 检出 `recovery/kmfa-v15-fuzzy`；不要覆盖 `main`。
3. 复跑本文件列出的治理测试与未解析 import 清点，先恢复或重新实现缺失模块，再讨论合并策略。
4. 保持 `KMFA/docs/governance/RAW_DATA_BOUNDARY.md` 和当前 `HANDOFF.md` 的 public/private、NO_GO 与 phase 边界有效。
5. 只有在单独的受控 run 合同、完整验证和审查通过后，才可提出从恢复分支选择性迁移到 `main` 的 PR。

## 非目标

- 不替代当前 `HANDOFF.md`。
- 不改变 v0.1.4 的业务 NO_GO、数据质量、正式报告或 App reinstall 路由。
- 不授权原始数据、私有运行数据、凭据或受保护恢复包进入 GitHub。
