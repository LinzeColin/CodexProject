# arXiv Daily Push V7.2 先读

V7.2 是 V7.1 的窄补丁合同，不覆盖、不删除、不改写 `docs/pursuing_goal/v7_1/`。V7.1 保持只读历史基线，V7.2 将 V1.1 Task Pack 中已确认的新要求合入当前产品合同。

## 当前结论

- CURRENT 产品合同：`ADP-PRODUCT-CONTRACT-V7.2`
- 父级历史合同：`ADP-PRODUCT-CONTRACT-V7.1`
- Stage 2 integrated acceptance 已记录并保持；当前事实以 `docs/pursuing_goal/CURRENT.yaml`、`FINAL_ACCEPTANCE_BUNDLE/manifest.json` 和 `FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json` 为准。
- S3/DAILY_OPERATION 仍未进入；当前实际阻断只剩 `persistent_daily_operation_authorization_missing`，即 `FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json` 不存在。
- V1.1 输入包：`arxiv_email_learning_v1_1_codex_task_pack.zip`
- V1.1 输入 hash：`8edbae035da904fe7b465142f90c64f1690a9d36fb24d2a5100fd699e6592eff`
- V7.1/V1.1 再审查报告 hash：`dac6bcab86e9e7dd04da0cb069fe2443517b56d52fce0cdd3ce3686e2f2b6d1b`

## 如何阅读 baseline 文件

- `V7_2_ROOT_LOCK.yaml`、`machine_readable/roadmap_v7_2.yaml` 和 `machine_readable/product_contract_v7_2.yaml` 是 V7.2 baseline 发布快照，不是后续 S2PMT07 / S3 状态机的唯一当前态来源。
- baseline 发布快照不能反向覆盖 `CURRENT.yaml`、`HANDOFF/00_下一Agent先读.md`、`HANDOFF/01_当前状态与唯一下一任务.md` 或 `FINAL_ACCEPTANCE_BUNDLE/` 中已经记录的当前事实。
- 若 baseline 文件中仍能看到 `production_accepted: false`、`S2PMT07_FINAL_GATE_PRECHECK_BLOCKED` 或 `NONE_WHILE_S2PMT07_BLOCKED`，只能解释 V7.2 baseline 发布时的历史 stop-gate 条件，不能据此回退 Stage 2 integrated acceptance，也不能据此重开已消费的 Stage2 Shadow 或 final-gate precheck 工作。
- 当前读取顺序：`CURRENT.yaml` -> `HANDOFF/00_下一Agent先读.md` -> `HANDOFF/01_当前状态与唯一下一任务.md` -> `FINAL_ACCEPTANCE_BUNDLE/` -> baseline 文件。
- 缺持久授权 artifact 时只能继续 MVP 复审修补、fail-closed 复核和证据同步；不得启用 SMTP、scheduler、Release、restore 或 DAILY_OPERATION。

## V7.2 改变什么

1. 合并 V7.1 的有效系统要求和 V1.1 的邮件学习前台要求。
2. 正式发布 `EMAIL_LEARNING_V1_FRONTSTAGE_OVERLAY`，替换 V7.1 旧邮件前台中与 V1.1 冲突的可见模块。
3. 正式引入 H/M 双平面权威矩阵、单向桥、`plane_revision_id`、apply/render/rollback receipt 和漂移 Gate。
4. 将 CURRENT 产品合同指向 V7.2，同时保留 `global_current_task`、`email_v1_workstream_next`、`shadow_source_next` 的上下文分层。
5. 要求所有 Stage2 agent 先按 V7.2 复审已完成工作；不满足的先修复，再继续新任务。

## V7.2 不改变什么

- 不修改邮件生产代码。
- 不修改公共 Schema。
- 不修改数据源 connector、queue、database、scheduler、SMTP、Release、backup/restore 或 3+1 编排。
- V7.2 baseline publication 本身不等于 S3/DAILY_OPERATION，也不授权 SMTP、scheduler、Release、restore 或持久运行。
- 无共享文件冲突的 Stage2 Shadow 数据源开发如需继续，必须先以 `CURRENT.yaml` 和当前 S3 授权边界重新确认，不得绕过持久授权缺失门。

## 下一任务

Email V1 T01-T05 已完成并合入 main，当前状态为 `EMAIL_LEARNING_V1_MERGED_TO_MAIN_NO_PRODUCTION_SIDE_EFFECTS`。当前全局入口仍是 `S2PMT07`，下一可执行任务是 `S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION`。在新的显式 owner 持久授权 artifact 出现前，只能继续 MVP 复审修补、fail-closed 复核和证据同步，不得启用 SMTP、scheduler、Release、restore 或 DAILY_OPERATION。
