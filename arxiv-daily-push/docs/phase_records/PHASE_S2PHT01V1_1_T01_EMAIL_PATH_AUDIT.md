# S2PHT01V1.1-T01 EMAIL_LEARNING_V1 只读 H/M 路径审计

- task_id: `S2PHT01V1.1-T01`
- acceptance_id: `ACC-S2PHT01V1.1-T01-PATH-AUDIT`
- contract: `ADP-PRODUCT-CONTRACT-V7.2`
- base_commit: `1566ab6c67742267b6b0f010993732adbc61a128`
- run_date: `2026-06-25`
- result: `PASS_WITH_NO_IMPLEMENTATION`

## 1. 结论

本次只完成 V7.2 要求的 EMAIL_LEARNING_V1 精确仓库路径审计，不实现模板、不改邮件生产代码、不改公共 Schema、不启用 SMTP/调度/Release。审计结论如下：

1. `M1-M4` 是 V7.1/V7.2 每日 `3+1` 邮件产品合同里的四个邮件产品，不是 Task Pack 的 `T01-T04`。
2. 当前 `main` 没有 `arxiv-daily-push/src/arxiv_daily_push/mail_templates.py`，也没有 `arxiv-daily-push/tests/test_mail_templates.py`；该路径只能作为未来实现候选，不能作为现行 runtime 事实。
3. 当前邮件前台由两条历史 runtime 路径承载：`stage1_b1_report.py` 的 B1 报告邮件，以及 `global_scan.py` 的 daily delivery 邮件。`lesson.py` 生成 frontstage 学习字段，`notifications.py` 定义通用邮件对象，`smtp_delivery.py` 与 `scheduled_execution.py` 属于传输/控制面，T01 不拥有写权限。
4. V7.2 的 EMAIL_LEARNING_V1 只能在后续实现任务中按本审计路径进入；T01 本身不解除 inherited V7.1 P0/P1 阻断，不构成 M1-M4、SMTP、scheduler、Release、Stage2 production 或 integrated production acceptance。

## 2. V7.2 读取凭证

本次开始前已按 V7.2 要求读取并确认：

| 文件 | T01 模式 | 结论 |
| --- | --- | --- |
| `arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml` | read-only | CURRENT 指向 `ADP-PRODUCT-CONTRACT-V7.2`。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml` | read-only | `email_v1_workstream_next` 为 `S2PHT01V1.1-T01`。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/HANDOFF/00_下一Agent先读.md` | read-only | 要求 T01 先做 exact H/M repository path audit。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/machine_readable/product_contract_v7_2.yaml` | read-only | 保留每日 `3+1` 邮件、深度理解、中文界面与双平面治理。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/machine_readable/migration_matrix_v7_1_to_v7_2.yaml` | read-only | EMAIL_LEARNING_V1 exact paths 状态仍为 `deferred_to_S2PHT01V1.1-T01`。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/machine_readable/dual_plane_governance_v7_2.yaml` | read-only | 未来实现必须保留 H/M 双平面 receipt、hash、rollback。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/machine_readable/email_learning_frontstage_overlay_v1.yaml` | read-only | 给出可见学习邮件模块与禁用可见模块。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_1/V7_1_ROOT_LOCK.yaml` | read-only history | V7.1 继续作为只读历史基线。 |

## 3. M1-M4 定义

| 邮件产品 | V7.1/V7.2 任务 | 含义 | 验收 |
| --- | --- | --- | --- |
| `M1` | `S2PKT02` | 科学与理论前沿邮件 | `ACC-S2PKT02-M1` |
| `M2` | `S2PKT03` | 工程、产品与产业前沿邮件 | `ACC-S2PKT03-M2` |
| `M3` | `S2PKT04` | 政策、资本与地缘前沿邮件 | `ACC-S2PKT04-M3` |
| `M4` | `S2PKT05` | 跨板块总览、错峰编排与水位线 | `ACC-S2PKT05-M4` |

边界：这些是每日 `3+1` 邮件产品线，不是 `S2PHT01V1.1-T01/T02/T03/T04`，也不是 Task Pack 的 `T01-T04`。

## 4. H 平面路径

| 路径 | owner | T01 模式 | 后续写入规则 | rollback/receipt |
| --- | --- | --- | --- | --- |
| `arxiv-daily-push/功能清单` | ADP governance | read-only evidence | 只允许治理生成/同步任务更新，不由邮件实现直接手写重复事实。 | dashboard/render sync receipt |
| `arxiv-daily-push/开发记录` | ADP governance | read-only evidence | 只允许治理生成/同步任务或任务 closeout 更新。 | development event + manifest |
| `arxiv-daily-push/模型参数文件` | ADP governance | read-only evidence | 只允许模型/参数注册任务更新；T01 不新增模型参数。 | semantic extractor receipt |
| `arxiv-daily-push/docs/governance/STATUS.md` | ADP governance | generated/read-only target | 可由 dashboard generator 更新状态视图。 | generator rerun + git revert |
| `arxiv-daily-push/docs/governance/OWNER_STATUS.md` | ADP governance | generated/read-only target | 可由 dashboard generator 更新 owner 视图。 | generator rerun + git revert |
| `arxiv-daily-push/docs/governance/ASSURANCE_STATUS.yaml` | ADP governance | generated/read-only target | 可由 dashboard generator 更新 assurance 视图。 | generator rerun + git revert |
| `arxiv-daily-push/docs/phase_records/PHASE_S2PHT01V1_1_T01_EMAIL_PATH_AUDIT.md` | S2PH T01 | write | 本任务唯一人读审计记录。 | revert this file |
| `governance/run_manifests/ADP-S2PHT01V1-1-T01-EMAIL-PATH-AUDIT-20260625.json` | S2PH T01 | write | 本任务机器读 receipt。 | revert this file |

## 5. M 平面路径

| 路径 | owner | T01 模式 | shared lock |
| --- | --- | --- | --- |
| `arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml` | V7.2 contract owner | read-only | 禁止 T01 修改；任意时刻只能有一个 CURRENT 产品合同。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml` | V7.2 contract owner | read-only | 禁止 T01 修改。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/machine_readable/product_contract_v7_2.yaml` | V7.2 contract owner | read-only | 禁止 T01 修改。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/machine_readable/migration_matrix_v7_1_to_v7_2.yaml` | V7.2 contract owner | read-only | T01 不回写 matrix；用本审计记录承接 exact path 结果。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/machine_readable/dual_plane_governance_v7_2.yaml` | V7.2 contract owner | read-only | 后续实现必须生成 apply/render/rollback receipts。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/machine_readable/email_learning_frontstage_overlay_v1.yaml` | V7.2 contract owner | read-only | 未来模板实现必须满足可见/禁用模块。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_2/machine_readable/current_pointer_registry_v7_2.yaml` | V7.2 contract owner | read-only | 禁止 T01 修改。 |
| `arxiv-daily-push/docs/pursuing_goal/v7_1/V7_1_ROOT_LOCK.yaml` | V7.1 historical owner | read-only history | 禁止覆盖、删除或迁移。 |

## 6. 现行 runtime 邮件路径

| 路径 | owner | 当前职责 | T01 模式 | 后续实现边界 |
| --- | --- | --- | --- | --- |
| `arxiv-daily-push/src/arxiv_daily_push/stage1_b1_report.py` | Stage1 B1 report/email | `build_b1_report_email_package`、`_render_email_plain`、`_render_email_html`、`_email_subject` 生成 B1 中文报告邮件。 | read-only | 未来若用于 M1/EMAIL_LEARNING_V1，必须由实现任务显式接管并更新测试，不得在 T01 修改。 |
| `arxiv-daily-push/src/arxiv_daily_push/global_scan.py` | daily delivery package | `build_daily_delivery_package`、`_daily_email`、`_daily_email_text`、`_daily_email_html`、`_frontstage_from_lesson`、`_daily_email_subject` 生成当前 daily delivery 邮件。 | read-only | 最可能的现行邮件前台集成点；后续必须避免生产副作用。 |
| `arxiv-daily-push/src/arxiv_daily_push/lesson.py` | lesson/frontstage model | `generate_lesson` 与 `_build_frontstage` 产出 decision、attention_score、evidence_level、reading time、first principles、domain mappings 等学习字段。 | read-only | EMAIL_LEARNING_V1 后续需重审 visible/forbidden modules，避免把禁用前台字段继续暴露。 |
| `arxiv-daily-push/src/arxiv_daily_push/notifications.py` | generic notification object | `EmailNotification` 与 `render_email` 定义通用状态邮件。 | read-only | 不是 M1-M4 学习邮件模板归属点。 |
| `arxiv-daily-push/src/arxiv_daily_push/smtp_delivery.py` | SMTP transport boundary | `deliver_notification`、`_email_message`、`validate_smtp_delivery_report`。 | locked/read-only | V7.1 inherited SMTP/outbox blockers 仍存在；T01/T02 不得启用或改写真实 SMTP。 |
| `arxiv-daily-push/src/arxiv_daily_push/scheduled_execution.py` | scheduler/control plane | `run_scheduled_execution` 连接 daily package 与 SMTP gate。 | locked/read-only | 后续邮件模板任务不得抢跑 scheduler、Release、production flags。 |
| `arxiv-daily-push/src/arxiv_daily_push/local_runner.py` | local production runner | 本地 runner 调用 daily delivery package 与 SMTP gate。 | read-only | Stage1 production strategy 仍是 local runner；T01 不触碰。 |
| `arxiv-daily-push/src/arxiv_daily_push/cli.py` | CLI entrypoints | `build-b1-report-email`、`render-email`、`send-notification`、`generate-lesson`、`run-scheduled-production`。 | read-only | 后续实现若新增命令必须有独立任务、测试、schema/receipt。 |
| `arxiv-daily-push/src/arxiv_daily_push/mail_templates.py` | UNKNOWN/future candidate | 当前 main 缺席。 | absent_on_main | 不能被当成当前实现；若后续创建，必须由实现任务登记 owner、tests、rollback。 |

## 7. 测试与 schema 路径

| 路径 | 当前覆盖点 | T01 模式 |
| --- | --- | --- |
| `arxiv-daily-push/tests/test_stage1_b1_report.py` | B1 报告邮件中文前台、subject、no ROI/no backend/no SMTP。 | read-only |
| `arxiv-daily-push/tests/test_global_scan.py` | daily delivery 邮件 subject/body/html、候选队列、Release/video/ROI 前台禁用。 | read-only |
| `arxiv-daily-push/tests/test_lesson.py` | lesson/frontstage 与 Claim Ledger 绑定。 | read-only |
| `arxiv-daily-push/tests/test_notifications.py` | notification/SMTP dry-run/HTML alternative/secrets 不泄露。 | read-only |
| `arxiv-daily-push/tests/test_scheduled_execution.py` | scheduler、SMTP gate、production readiness degrade/pass。 | read-only |
| `arxiv-daily-push/tests/test_manual_delivery_workflow.py` | manual delivery workflow 相关边界。 | read-only |
| `arxiv-daily-push/tests/test_mail_templates.py` | 当前 main 缺席。 | absent_on_main |
| `arxiv-daily-push/schemas/lesson.schema.json` | lesson/frontstage schema 边界。 | locked/read-only |
| `arxiv-daily-push/schemas/smtp_delivery.schema.json` | SMTP evidence report schema。 | locked/read-only |
| `arxiv-daily-push/schemas/scheduled_execution.schema.json` | scheduled execution report schema。 | locked/read-only |
| `arxiv-daily-push/schemas/daily_input.schema.json` | daily input source/claim/queue 输入边界。 | locked/read-only |

## 8. 禁止触碰清单

T01 和任何 EMAIL_LEARNING_V1 实现前置阶段不得触碰：

- 邮件生产发送代码、SMTP 授权、SMTP secrets、真实发送开关。
- scheduler、launchd/GitHub schedule 安装、production flags、Release 上传路径。
- 公共 Schema、queue/DB/state machine/ledger schema、migration。
- source adapters、ranking/ROI algorithm、Stage2 source inclusion、real restore、full replay acceptance。
- `CURRENT.yaml`、V7.2 shared contract files、V7.1 historical baseline files。

## 9. 后续任务最小读取集

开始 EMAIL_LEARNING_V1 下一步实现前，最小读取：

1. `arxiv-daily-push/docs/phase_records/PHASE_S2PHT01V1_1_T01_EMAIL_PATH_AUDIT.md`
2. `governance/run_manifests/ADP-S2PHT01V1-1-T01-EMAIL-PATH-AUDIT-20260625.json`
3. `arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml`
4. `arxiv-daily-push/docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml`
5. `arxiv-daily-push/docs/pursuing_goal/v7_2/machine_readable/email_learning_frontstage_overlay_v1.yaml`
6. `arxiv-daily-push/src/arxiv_daily_push/global_scan.py`
7. `arxiv-daily-push/src/arxiv_daily_push/stage1_b1_report.py`
8. `arxiv-daily-push/src/arxiv_daily_push/lesson.py`
9. `arxiv-daily-push/tests/test_global_scan.py`
10. `arxiv-daily-push/tests/test_stage1_b1_report.py`
11. `arxiv-daily-push/tests/test_lesson.py`

## 10. T01 验收

- exact H/M paths recorded: yes
- owners recorded: yes
- read/write modes recorded: yes
- rollback receipt target recorded: yes
- shared file locks recorded: yes
- runtime production code changed: no
- public schema changed: no
- SMTP/scheduler/Release changed: no
- V7.2 shared contract files changed: no
- `EMAIL_LEARNING_V1_ACCEPTED`: no
- `M1-M4_ACCEPTED`: no
- `INTEGRATED_PRODUCTION_ACCEPTED`: no

## 11. 验证证据

- V7.2 contract validator: PASS, errors 0, warnings 0
- ADP project governance: errors 0, warnings 0
- changed-only governance validate: errors 0, warnings 0
- lean check-render: drift_count 0, reference_issue_count 0
- focused mail-chain unittest: 32 tests OK
- semantic extractor: 66 formulas / 441 parameters checked
- JSON/JSONL/YAML parse: OK
- `git diff --check`: PASS

备注：`scripts/lean_governance.py ci --changed-only --base-ref origin/main` 的内部 validation 为 0/0，但该 CI wrapper 在本地存在预期未提交 diff 时返回非零；本 PR 使用 `validate --changed-only --enforce-sync --semantic --base-ref origin/main` 作为同步 gate。
