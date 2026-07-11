# KMFA HANDOFF

## 当前状态

- phase: `V014_S13_P2_POST_REMEDIATION_COLLECTION_RECEIVABLE_AGING`
- roadmap gate: `S13-P2｜回款应收账龄`
- task: `KMFA-V014-S13-P2-POST-REMEDIATION-COLLECTION-RECEIVABLE-AGING-20260711`
- status: `completed_validated_local_only_s13_p2_method_locked_business_items_unproven_upload_deferred`
- version: `0.1.4-s13-p2-post-remediation-collection-receivable-aging`
- decision: `NO_GO`
- data quality / report grade: `Q4 / D`
- pursuing_goal_status: `active`
- S13-P1 / S13-P2: `performed / performed`
- S13-P3 / Stage 13 review: `not performed / not performed`
- GitHub upload / app reinstall: `not performed / not performed`
- 下一步只能执行 S13-P3；不得执行 Stage 13 review 或 GitHub upload。

## S13-P2 结果

- 来源主题：回款表、应收账龄、客户账龄、日记账、开票计划，共 `5` 条。
- 三层状态：结构接入 `5/5`；私有容器可解析 `3/5`；行级绑定已证明 `0/5`。
- 四类问题：已开票未回款、完工未结算、结算未开票、超期应收的方法定义 `4/4`。
- 业务输出：已证明业务项 `0`、可执行回款优先级 `0`、已指派责任事项 `0`。
- 私有差异：2 个 WPS 私密容器，加上共享行键和期间口径，共 `4` 类；只保存在 ignored private runtime。
- 历史隔离：旧 S13-P2 的 `pending=12`、4 个静态优先级和 4 个静态责任项均非当前动态事实。
- 浏览器：baseline `54/54 PASS`，current `6/6 PASS`；viewports/issues/HTTP/navigation=`2/4/2/2`，console/overflow=`0/0`。
- raw：5 个文件在 phase 前后、跨 S13-P1 和当前快照一致。

## 关键边界

1. 结构接入、私有容器可解析和行级绑定是三种不同证据，不得互相替代。
2. 未证明共享行键和期间口径前，不得生成项目、客户、发票、回款、账龄或金额明细。
3. 4 个 review sequence 只是方法顺序，不是业务催收优先级；责任角色定义不是个人指派。
4. 当前 `Q4 / D / NO_GO / 3-9-2-1` 只能由后续独立 phase 的真实证据改变。
5. 原始目录只读；不修改、删除、移动、重命名、复制、覆盖或写入任何原始文件。
6. raw 文件名、字段、表头、项目、客户、金额、行列、来源指纹、截图和诊断只存在于 ignored private runtime。
7. 本 phase 不执行客户联络、催收、法律判断、开票、付款、银行或其他业务动作。
8. Stage 8-18 全部完成、最终整体复审并修复 findings 前，不得执行 GitHub upload 或 app reinstall。

## 证据

- manifest: `KMFA/stage_artifacts/V014_S13_P2_POST_REMEDIATION_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_manifest.json`
- summary: `KMFA/stage_artifacts/V014_S13_P2_POST_REMEDIATION_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_summary.json`
- matrix: `KMFA/stage_artifacts/V014_S13_P2_POST_REMEDIATION_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_acceptance_matrix.json`
- workbench: `KMFA/stage_artifacts/V014_S13_P2_POST_REMEDIATION_COLLECTION_RECEIVABLE_AGING/exports/html/collection_receivable_aging_workbench.html`
- validator: `KMFA/tools/check_v014_s13_p2_post_remediation_collection_receivable_aging.py`
- focused test: `KMFA/tests/test_v014_s13_p2_post_remediation_collection_receivable_aging.py`
- private raw/browser/difference evidence: `KMFA/.codex_private_runtime/v014_s13_p2_post_remediation_collection_receivable_aging/`

## 验证命令

- `KMFA_AUDIT_PYTHON=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s13_p2_post_remediation_collection_receivable_aging`
- `KMFA_AUDIT_PYTHON=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s13_p2_post_remediation_collection_receivable_aging.py --require-private-evidence --require-browser-evidence --require-final-evidence`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA --mode required`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA --mode required`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only`

## 原始数据边界

- 原始目录固定为 `/Users/linzezhang/Downloads/KMFA_MetaData`，Codex 只读。
- 当前 raw 快照没有差异；4 类解析/绑定差异已记录在 private runtime。若最终 goal 多次交叉验证仍无法解除，必须提供全中文最终差异报告。
- 不得提交 raw、zip、Excel、PDF、私有 CSV、凭据、银行流水、合同、薪资或税务材料。

## 未解决风险

- 两个原生 WPS 私密容器当前无法在不损伤原文件的前提下转换，相关两条主题只能保持结构接入。
- 五类来源的共享行级主键与跨来源期间口径未被证明，因此 4 类问题无法生成业务明细。
- 3 条开放接受差异、9 条非零差异和 1 条未完成比较仍未关闭。
- S13-P3 跨表复核尚未执行；Stage 13 不能整体复审。
- GitHub main 未上传，app 未重装；统一延期到 Stage 8-18 全部完成、最终整体复审并修复 findings 后一次性执行。

## 推荐下一轮 pursuing goal prompt

继续 KMFA，只执行一个 phase：`S13-P3｜跨表复核`；不得执行 Stage 13 整体复审或 GitHub upload。
先确认 git root、branch、remote、HEAD、status，并读取最新 HANDOFF、v1.4 Task Pack/Roadmap 的 S13-P3 契约。
以上游 `Q4 / D / NO_GO / 3-9-2-1`、S13-P1 的 `4/4 structure-connected / 0/4 current raw-value-bound` 与 S13-P2 的 `5/5 structure-connected / 3/5 private-container-parseable / 0/5 row-level-bound / 0 business items` 为边界。
执行项目、客户、金额、时间四维跨表一致性检查；无法证明的差异进入 public-safe 差异队列和 ignored private 中文诊断，不得猜测归属、补值、忽略 0.01 元或生成催收/开票/付款/银行动作。
验收必须包含 focused tests、strict validator、public-safe evidence、desktop/mobile 证据、raw 不变性、治理记录和 local commit。
本轮不得执行 Stage 13 review、GitHub upload、app reinstall、live connector、persistent business write 或 business execution。
