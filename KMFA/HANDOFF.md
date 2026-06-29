# KMFA Handoff

更新时间: 2026-06-29

## 当前目标

Stage 1 只读启动与项目治理基线。当前已完成 `S01-P1/P2/P3` 并通过 Stage 1 整体复审，下一步是隔离 worktree 上传 GitHub。

## 当前状态

- `S01-P1` 已在前序工作目录完成，只读计划证据已迁移到 `KMFA/stage_artifacts/S01_P1_read_only_plan/`。
- `S01-P2` 已创建项目根、三中文入口、模型参数文件、Lean v2 与 v1 兼容治理文件、metadata 草案。
- `S01-P3` 已导入完整需求追溯矩阵、新增正式 `KMFA/tools/no_omission_check.py`、建立 18 Stage / 54 Phase / 162 Task 状态登记。
- Stage 1 总复审已通过，复审产物在 `KMFA/stage_artifacts/S01_STAGE_REVIEW/`。
- 尚未执行 GitHub upload；上传必须在 clean worktree 内完成。

## 关键决策

- canonical GitHub 目录为 `LinzeColin/CodexProject/KMFA`。
- 本地 canonical root 为仓库 README 指定的 `/Users/linzezhang/Documents/Codex/2026-06-19/current-phase-phase-0-goal-scope/work/CodexProject`。
- 公开仓库不保存原始敏感经营数据，只保存 hash、manifest、状态、证据索引和治理记录。
- 每次 run work 最多解决一个 Phase；中间 Phase 不上传 GitHub。
- Stage 完成后先整体复审，修复复审问题后再整体上传 GitHub。
- 当前 canonical checkout 落后 `origin/main` 且存在非 KMFA 脏改，Stage 1 上传必须使用隔离 worktree。

## 已改/需看文件

- `KMFA/README.md`
- `KMFA/功能清单.md`
- `KMFA/开发记录.md`
- `KMFA/模型参数文件.md`
- `KMFA/docs/governance/*`
- `KMFA/metadata/*`
- `KMFA/stage_artifacts/S01_P1_read_only_plan/*`
- `KMFA/stage_artifacts/S01_STAGE_REVIEW/*`
- `governance/projects.yaml`
- `README.md`

## 验证命令

```bash
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
git diff --check -- README.md governance/projects.yaml KMFA
```

## 未解决风险

- 当前 canonical repo 有大量与 KMFA 无关的脏改，且落后 `origin/main`，不能直接提交或回滚。
- GitHub upload 尚未执行；必须在基于 `origin/main` 的隔离 worktree 中重新验证。
- 正式金额工具、zero-delta、lineage、report grade gate 尚未实现。

## 下一步

本轮完成隔离上传后，下一轮才能进入 S02。若上传失败，先修 upload/worktree 问题，不进入 S02。
