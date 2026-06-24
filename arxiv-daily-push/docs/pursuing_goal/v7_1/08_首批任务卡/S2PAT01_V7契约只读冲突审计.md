# Task Card：S2PAT01 V7 契约只读冲突审计

## 唯一目标

在不修改仓库的前提下，确认 V5/V6、当前代码配置、三基文件、Root/Project AGENTS 与 V7 Owner 决策之间的全部冲突和迁移落位。

## 允许读取

- 根 `AGENTS.md`、`docs/governance/STANDARD.md`；
- `arxiv-daily-push/AGENTS.md`、README；
- V5/V6 pursuing_goal 文件；
- `功能清单`、`开发记录`、`模型参数文件`；
- `config/owner_controls.yaml`；
- `docs/owner/*`；
- 与治理生成器、Schema、邮件编排直接有关的文件。

## 禁止

- 修改文件；
- 全仓扫描其他项目；
- 重写历史事件；
- 猜测未读取的实现。

## 必须输出

1. V6→V7 概念/任务/文件迁移矩阵；
2. 旧五封邮件、旧 B1–B5、英文界面、真实队列缺失等冲突；
3. 将创建/修改的精确文件；
4. focused tests、治理检查、回滚；
5. 唯一下一任务 `S2PAT02` 是否解锁。

## Stop Gate

`ACC-S2PAT01-V7-AUDIT`：冲突矩阵完整，所有 UNKNOWN 都绑定解决任务。

## Stop Conditions

`R-CONFLICT`、越界扫描、无法确定唯一事实源。
