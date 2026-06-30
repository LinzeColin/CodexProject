# KMFA Owner Status

更新时间: 2026-06-30

## 一句话状态

KMFA 已在 v1.2 FULL_HTML_NO_OMISSION 基线上完成 Stage 4 final GitHub upload、Stage 5 全部 Phase/复审/upload、Stage 6 全部 Phase/复审/upload、Stage 7 全部 Phase/复审/upload，以及 S08-P1 项目组合键、S08-P2 业务实体模型、S08-P3 匹配质量测试、Stage 8 整体复审和 Stage 8 final GitHub upload。Stage 8 upload 已复跑 validators、治理检查、raw/secret scan、parse checks、evidence consistency checks、dry-run push、push 和 post-push parity；S09-P1 事实层、lineage 和报告仍未完成，项目仍不是可用业务系统。

## 你现在能信任什么

- 项目路径已经收敛到 `LinzeColin/CodexProject/KMFA`。
- 三中文入口已存在：`功能清单.md`、`开发记录.md`、`模型参数文件.md`。
- 项目治理文件和 metadata 草案已建立。
- 公开仓库隐私边界已写入。
- P0/P1 需求已绑定任务、验收、测试和证据，并通过正式 `no_omission` 检查。
- Stage 1 总复审已通过并已上传 GitHub main。
- metadata 七类目录已建立，并有机器检查器验证目录、标识符和隐私边界。
- raw manifest append-only 规范、派生数据版本协议、前端 raw 写入边界已建立，并有机器检查器验证。
- Q0-Q5 数据质量等级、A/B/C/D 报告可信等级和报告发布门禁已建立，并有机器检查器验证。
- v1.2 完整任务包位于 `KMFA/taskpack/v1_2/`。
- HTML/UIUX/报告验收样板已完整进入仓库可提交面：45 个 HTML，7 个核心样板。
- 原始私有数据没有进入公开仓库；公开仓库只保存 SHA256 登记和禁止提交规则。
- S03-P1 文件登记工具已存在，覆盖 `zip/xlsx/xls/csv/pdf` 登记、zip traversal 防护和 WPS/OLE 操作提示。
- S03-P2 数据源检查矩阵工具已存在，状态只允许 `已就绪`、`部分/阻塞`、`失败/不适用`、`已过期`、`人工复核`。
- S03-P3 源优先级工具已存在，固定 `raw_upload -> authorized_export -> raw_extracted_value -> staging_structured_row -> canonical_fact -> derived_metric -> report_reference -> frontend_display -> processed_data`，同源不一致失效重跑，跨源冲突不自动选边。
- Stage 3 整体复审已通过，发现的源优先级链路对齐问题已修复。
- Stage 3 已整体上传 GitHub main，reviewed content commit `39b0eef52424a12b6c0c8ad368bd878b46300be4`。
- S04-P1 金额工具已存在，覆盖元、万元、千元、千分位、负数、括号负数、float 禁止和异常输入不默认为 0。
- S04-P2 字段标准化工具已存在，覆盖字段别名、中文字段映射、日期/期间/主体/项目/客户/合同编号标准化，以及缺字段质量状态。
- S04-P3 基础工具测试已存在，覆盖金额小数、负数、万元、异常字符、中文日期、年月、空值，并生成工具函数测试报告。
- Stage 4 整体复审已通过，复审修复了 owner-readable 金额工具详情缺口，并留下 `KMFA/stage_artifacts/S04_STAGE_REVIEW/` 证据。
- Stage 4 final GitHub upload 证据已生成，upload record 和 manifest 位于 `KMFA/stage_artifacts/S04_STAGE_REVIEW/`。
- S05-P1 A0 文件登记已存在，登记了 `销售绩效考核.zip` 的 source package hash、8 个 PDF、1 个 Excel、A0 项目候选和 Q3/Q4 状态。
- S05-P2 public-safe 字段合同已存在，覆盖合同额、支出合计、毛利、毛利率、成本分类。
- S05-P2 A0 golden fixture 候选已存在，共 45 条；其中 40 条 PDF 字段候选已保存 hash/source anchor，5 条 Excel 字段候选已按 active owner/授权降级决策排除为 cross-source support only。公开仓库只保存 private refs、hash/status 和 source anchor 状态，不保存真实字段值。
- Excel 候选已有机器复核记录、owner 决策包、专门 validator、owner 决策 intake validator、三种 public-safe 决策模板、application preview、active owner/授权降级决策和 completion gate ready 证据：当前 workbook 只能作为交叉来源支持，不能机器合成为单一 A0 项目基准，已被排除出 Q4/Q5 A0 baseline。
- S05-P3 A0 authority baseline lock 已存在：40 条 PDF 字段 hash/source-anchor 记录被锁定，5 条 Excel 字段被排除；baseline version、content hash、锁定角色、锁定时间和 validator 均已记录。
- Stage 5 整体复审已本地通过：`KMFA/stage_artifacts/S05_STAGE_REVIEW/` 记录 review report、test results 和 machine manifest；raw/secret scan 未发现可提交 raw 文件或 secret。
- Stage 5 final GitHub upload 已完成并留下 upload record/manifest：`KMFA/stage_artifacts/S05_STAGE_REVIEW/human/github_upload_record.md`、`KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_upload_manifest.json`。
- S06-P1 零差异校验器已存在：`KMFA/tools/zero_delta_validator.py` 使用 public-safe 已结构化整数分 fixture，逐字段比较权威值和系统值，1 分差异失败，并生成包含来源、字段、权威值、系统值和差额的 mismatch report。
- S06-P2 跨源差异队列已存在：`KMFA/tools/cross_source_difference_queue.py` 使用 public-safe PDF/Excel synthetic fixture，1 分冲突进入人工队列；`KMFA/tools/check_s06_p2_difference_queue.py` 验证未关闭差异阻断 A 级报告。
- S06-P3 校验证据输出已存在：`KMFA/tools/validation_evidence_output.py` 输出 stage evidence 并写入 `metadata/quality`；`KMFA/tools/check_s06_p3_validation_evidence.py` 验证输出不新增字段明文或原始金额值。
- Stage 6 整体复审和 final GitHub upload 已完成：`KMFA/stage_artifacts/S06_STAGE_REVIEW/` 记录 S06-P1/P2/P3 复跑、治理 validator、raw/secret scan、evidence consistency check、dry-run push、push 和 post-push parity。
- S07-P1 财务文件适配已本地验证完成：`KMFA/tools/finance_file_adapter.py` 支持只读 `.xlsx` 结构解析并只输出 hash/private refs；`KMFA/tools/check_s07_p1_finance_file_adapter.py` 验证 9 类财务源、45 条字段候选、9 条字段报告、无来源表头明文、无 raw business values、WPS/红圈 scope 均为 false。
- S07-P2 WPS 文件适配已本地验证完成：`KMFA/tools/wps_file_adapter.py` 支持 WPS 导出转换后的 `.xlsx` 只读结构解析、原生 WPS 转换提示和版本化字段映射；`KMFA/tools/check_s07_p2_wps_file_adapter.py` 验证 4 类 WPS 导出、20 条字段映射、4 条转换提示、1 个 active mapping rule version、无来源表头明文、无 raw business values、财务/红圈 scope 边界。
- S07-P3 红圈导出后置策略已本地验证完成：`KMFA/tools/redcircle_postponement_policy.py` 只生成 public-safe 预留模板、source registry、connector postponement policy 和 rollback plan；`KMFA/tools/check_s07_p3_redcircle_postponement.py` 验证 4 类红圈模板、D15 自动接口禁止、只读/hash/rollback/manual approval 控制、无接口凭证、无字段明文、无 raw business values。
- Stage 7 整体复审和 final GitHub upload 已完成：`KMFA/stage_artifacts/S07_STAGE_REVIEW/` 记录 S07-P1/P2/P3 复跑、治理 validator、raw/secret scan、evidence consistency check、dry-run push、push 和 post-push parity。
- S08-P1 项目组合键已本地验证完成：合同编号、项目名称、对手方、主体、时间、金额签名、责任人、来源 hash 八个组件只保存 hash/private refs；强匹配阈值为 8500 bps，人工复核阈值为 7000 bps，低于强匹配阈值进入人工复核且不自动合并。
- S08-P2 业务实体模型已本地验证完成：customer、contract、project、cost_record、invoice、collection、receivable、tax_evidence 8 类实体只保存 public-safe schema/hash/ref/status/evidence metadata；14 条关系和 32 条生命周期状态已写入 metadata/schema_maps。
- S08-P3 匹配质量测试已本地验证完成：same-name project、multiple company entities、multiple accounts、multiple periods 4 类质量场景全部使用 public-safe refs/hash/status/evidence，3 条中高风险候选进入人工复核队列且 `auto_merge_allowed=false`，并输出 `entity_matching_report`。
- Stage 8 整体复审已本地通过：`KMFA/stage_artifacts/S08_STAGE_REVIEW/` 记录 review report、test results 和 machine manifest；raw/secret scan 未发现可提交 raw 文件或 high-signal secret。
- Stage 8 final GitHub upload 已完成：`KMFA/stage_artifacts/S08_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_upload_manifest.json` 记录 rebase、validators、raw/secret scan、dry-run push、push 和 post-push parity。

## 你现在不能信任什么

- 不能认为项目成本分析已经实现。
- 不能认为真实业务源解析、事实层或报告已经实现。
- 不能认为 S05-P3 已经提交真实合同额、支出合计、毛利、毛利率或成本分类明文；公开仓库只保存 public-safe hash/source-anchor baseline。
- 不能认为 A0 authority baseline 已经可以发布正式经营报告；lineage 和报告发布门禁尚未完成。
- 不能认为 Stage 6 upload、Stage 7 upload、S08-P1 project composite key、S08-P2 business entity model、S08-P3 matching quality test 或 Stage 8 upload 代表正式经营报告、事实层、lineage、自动接口或差异关闭能力已经实现。
- 不能认为 lineage 完整检查已正式实现。
- 不能认为 Stage 1 已经实现业务功能。
- 不能把 S02-P3 的报告等级协议当成真实报告生成能力。
- 不能跳过 v1.2 HTML/报告样板门禁继续做 S10/S11/S12/S18。
- 不能把 v1.2 中的 `90_用户原始上传数据_仅本地私有_禁止提交GitHub/` 复制进公开仓库。

## 下一步

下一步只执行 `S09-P1｜项目成本事实层`；不得扩大到 S09-P2、UI、正式报告、lineage 或自动接口。S09-P1 必须继续使用 public-safe metadata、整数分金额、A0 authority baseline、zero-delta/差异队列边界，不提交 raw business data。
