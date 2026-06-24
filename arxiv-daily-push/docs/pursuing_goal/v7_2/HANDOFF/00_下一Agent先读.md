# V7.2 下一 Agent 先读

## 必读顺序

1. `docs/pursuing_goal/CURRENT.yaml`
2. `docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml`
3. `docs/pursuing_goal/v7_2/machine_readable/product_contract_v7_2.yaml`
4. `docs/pursuing_goal/v7_2/machine_readable/migration_matrix_v7_1_to_v7_2.yaml`
5. `docs/pursuing_goal/v7_2/AUDIT/00_V7_2_终审摘要.md`
6. `docs/pursuing_goal/v7_1/V7_1_ROOT_LOCK.yaml`

## 当前合同

- CURRENT 产品合同：`ADP-PRODUCT-CONTRACT-V7.2`
- V7.1：只读历史基线，不覆盖、不删除。
- 全局当前任务：`S2PCT02`
- 邮件 V1 workstream 下一任务：`S2PHT01V1.1-T01`

## 强制规则

- 所有 Stage2 agent 在继续新任务前，必须按 V7.2 复审自己已完成的工作。
- 不满足 V7.2 的已完成工作必须先修复。
- `S2PHT01V1.1-T01` 通过前，不改邮件生产代码、不改公共 Schema、不改 connectors/queue/DB/scheduler/SMTP/Release/3+1 编排。
- 无共享文件冲突的 Stage2 Shadow 数据源开发可以继续。

## 唯一下一合同任务

`S2PHT01V1.1-T01`：只读调用链与 H/M 精确落位审计。
