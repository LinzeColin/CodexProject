# KMFA Handoff

更新时间: 2026-06-29

## 当前目标

Stage 2 数据治理内核与 metadata 协议。当前已完成 `S02-P1｜metadata目录协议` 和 `S02-P2｜不可污染原则`，下一步是 `S02-P3｜数据质量等级`。

## 当前状态

- `S01-P1` 已在前序工作目录完成，只读计划证据已迁移到 `KMFA/stage_artifacts/S01_P1_read_only_plan/`。
- `S01-P2` 已创建项目根、三中文入口、模型参数文件、Lean v2 与 v1 兼容治理文件、metadata 草案。
- `S01-P3` 已导入完整需求追溯矩阵、新增正式 `KMFA/tools/no_omission_check.py`、建立 18 Stage / 54 Phase / 162 Task 状态登记。
- Stage 1 总复审已通过，复审产物在 `KMFA/stage_artifacts/S01_STAGE_REVIEW/`。
- Stage 1 已上传到 GitHub main: `ff834578e640dc360e764ab18f9da2003c735e3e`。
- `S02-P1` 已建立 metadata 七类目录、标识符协议、公开仓库隐私边界和 `KMFA/tools/metadata_protocol_check.py`。
- `S02-P2` 已建立 raw manifest append-only 规范、派生版本协议、前端 raw 写入边界和 `KMFA/tools/immutability_policy_check.py`。
- `S02-P3` 尚未开始；Stage 2 尚未复审，尚未上传 GitHub。

## 关键决策

- canonical GitHub 目录为 `LinzeColin/CodexProject/KMFA`。
- 本地 canonical root 为仓库 README 指定的 `/Users/linzezhang/Documents/Codex/2026-06-19/current-phase-phase-0-goal-scope/work/CodexProject`。
- 公开仓库不保存原始敏感经营数据，只保存 hash、manifest、状态、证据索引和治理记录。
- 每次 run work 最多解决一个 Phase；中间 Phase 不上传 GitHub。
- Stage 完成后先整体复审，修复复审问题后再整体上传 GitHub。
- 当前 canonical checkout 仍有非 KMFA 脏改风险；Stage 2 继续使用隔离 worktree，最终上传必须 clean-worktree 验证。

## 已改/需看文件

- `KMFA/README.md`
- `KMFA/功能清单.md`
- `KMFA/开发记录.md`
- `KMFA/模型参数文件.md`
- `KMFA/docs/governance/*`
- `KMFA/metadata/*`
- `KMFA/stage_artifacts/S01_P1_read_only_plan/*`
- `KMFA/stage_artifacts/S01_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S02_P1_metadata_protocol/*`
- `KMFA/stage_artifacts/S02_P2_immutability_policy/*`
- `KMFA/metadata/protocol/*`
- `KMFA/metadata/{sources,imports,schema_maps,quality,lineage,reports,approvals}/*`
- `governance/projects.yaml`
- `README.md`

## 验证命令

```bash
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
git diff --check -- README.md governance/projects.yaml KMFA
```

## 未解决风险

- 当前 canonical repo 有大量与 KMFA 无关的脏改，不能直接提交或回滚。
- S02-P3 未完成，Stage 2 不能复审，不能上传 GitHub。
- 正式金额工具、zero-delta、lineage、report grade gate 尚未实现。

## 下一步

下一轮只执行 S02-P3，不做 Stage 2 复审。S02 三个 Phase 都完成后，再做 Stage 2 整体复审、修复问题、整体上传 GitHub。
