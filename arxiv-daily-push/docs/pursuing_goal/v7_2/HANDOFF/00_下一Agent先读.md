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
- 全局当前任务：`S2PMT07`
- 邮件 V1 workstream 状态：`EMAIL_LEARNING_V1_MERGED_TO_MAIN_NO_PRODUCTION_SIDE_EFFECTS`

## 强制规则

- 所有 Stage2 agent 在继续新任务前，必须按 V7.2 复审自己已完成的工作。
- 不满足 V7.2 的已完成工作必须先修复。
- Email V1 已在 main 上完成 T01-T05 状态收口；后续新增邮件入口必须继续走同一 Email V1 contract/readiness gate，不改公共 Schema、不改 connectors/queue/DB/scheduler/SMTP/Release/3+1 编排，且不得启用生产副作用。
- Stage 2 integrated acceptance 已记录并保持；当前事实以 `docs/pursuing_goal/CURRENT.yaml`、`FINAL_ACCEPTANCE_BUNDLE/manifest.json` 和 `FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json` 为准。
- S3/DAILY_OPERATION 仍未进入；当前实际阻断只剩 S3/DAILY_OPERATION 持久授权缺失，即 `persistent_daily_operation_authorization_missing` / `FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json` 不存在。
- 缺持久授权 artifact 时，只能继续 MVP 复审修补和证据同步；不得启用 SMTP、scheduler、Release、restore 或 DAILY_OPERATION。

## 唯一下一合同任务

当前全局入口仍是 `S2PMT07`，但不是旧 final gate precheck。下一可执行任务名为 `S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION`；在 owner 新的显式持久授权 artifact 出现前，只能做 MVP 复审修补、fail-closed 复核和证据同步。`S2PCT02` Science metadata-only no-send shadow evidence 是已完成历史记录，不再作为唯一下一任务。
