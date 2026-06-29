# KMFA S01-P1 Rollback Plan

更新时间: 2026-06-29

## 1. 本轮变更性质

本轮只新增 S01-P1 计划和证据文件，不修改业务代码、不修改原始下载包、不创建正式 `KMFA/` 项目骨架、不配置 remote、不提交、不 push。

## 2. 回滚命令

如需完全回滚本轮文件:

```bash
rm -rf stage_artifacts/S01_P1_read_only_plan
```

如需保留人类可读文件、删除机器可读 manifest:

```bash
rm -rf stage_artifacts/S01_P1_read_only_plan/machine
```

## 3. 不需要回滚的内容

`/tmp/kmfa_s01p1_pack` 是临时解包目录，可随时删除:

```bash
rm -rf /tmp/kmfa_s01p1_pack
```

下载目录中的 TaskPack、Roadmap、zip 未被修改。

## 4. S01-P2 前回滚判断

如果后续决定直接在 `LinzeColin/CodexProject/KMFA` 创建正式项目，本轮 `stage_artifacts/S01_P1_read_only_plan` 可以:

1. 移入 `KMFA/stage_artifacts/S01_P1_read_only_plan`；或
2. 作为当前空仓库的证据留存；或
3. 删除后由 S01-P2 重新登记。

优先建议: 在 S01-P2 确定 canonical checkout 后迁移到正式 `KMFA/` 内。
