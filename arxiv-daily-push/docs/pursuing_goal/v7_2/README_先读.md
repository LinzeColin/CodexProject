# arXiv Daily Push V7.2 先读

V7.2 是 V7.1 的窄补丁合同，不覆盖、不删除、不改写 `docs/pursuing_goal/v7_1/`。V7.1 保持只读历史基线，V7.2 将 V1.1 Task Pack 中已确认的新要求合入当前产品合同。

## 当前结论

- CURRENT 产品合同：`ADP-PRODUCT-CONTRACT-V7.2`
- 父级历史合同：`ADP-PRODUCT-CONTRACT-V7.1`
- V1.1 输入包：`arxiv_email_learning_v1_1_codex_task_pack.zip`
- V1.1 输入 hash：`8edbae035da904fe7b465142f90c64f1690a9d36fb24d2a5100fd699e6592eff`
- V7.1/V1.1 再审查报告 hash：`dac6bcab86e9e7dd04da0cb069fe2443517b56d52fce0cdd3ce3686e2f2b6d1b`

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
- 不宣称 `STAGE2_PRODUCTION_ACCEPTED`、`D2_SOURCE_DOMAIN_ACCEPTED` 或 `INTEGRATED_PRODUCTION_ACCEPTED`。
- 不阻塞无共享文件冲突的 Stage2 Shadow 数据源开发。

## 下一任务

`S2PHT01V1.1-T01`：只读调用链与 H/M 精确落位审计。T01 之前不得让实现 Agent 猜测 product contract、feature registry、roadmap/task registry 或 receipt 的仓库路径。
