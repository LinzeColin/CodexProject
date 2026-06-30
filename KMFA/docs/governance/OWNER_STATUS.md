# KMFA Owner Status

更新时间: 2026-06-30

## 一句话状态

KMFA 已在 v1.2 FULL_HTML_NO_OMISSION 基线上完成 Stage 4 final GitHub upload、`S05-P1｜A0 文件登记` 和 `S05-P2｜字段级黄金基准` 本地验证。S05-P2 已生成 public-safe 字段合同和 45 条 A0 golden fixture 候选，并对 8 个 PDF 候选完成 40 条 hash-only 私有回填；剩余 Excel candidate 经私有 `销售绩效考核.zip`、`财务.zip` 只读复核后已由 owner/授权降级决策处理为 cross-source support only，不进入 Q4/Q5。项目仍不是可用业务系统。

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
- S05-P2 A0 golden fixture 候选已存在，共 45 条；其中 40 条 PDF 字段候选已保存 hash/source anchor，5 条 Excel 字段候选仍 pending。公开仓库只保存 private refs、hash/status 和 source anchor 状态，不保存真实字段值。
- Excel 候选已有机器复核记录、owner 决策包、专门 validator、owner 决策 intake validator、三种 public-safe 决策模板、application preview、active owner/授权降级决策和 completion gate ready 证据：当前 workbook 只能作为交叉来源支持，不能机器合成为单一 A0 项目基准，已被排除出 Q4/Q5 A0 baseline。

## 你现在不能信任什么

- 不能认为项目成本分析已经实现。
- 不能认为真实业务源解析、事实层或报告已经实现。
- 不能认为 S05-P2 已经 Q4/Q5 锁定真实合同额、支出合计、毛利、毛利率或成本分类；当前只是 S05-P2 本地完成，Excel candidate 已降级为 cross-source support only。
- 不能认为 A0 golden fixture 已经 Q4 人工确认或 Q5 可用于计算。
- 不能认为 zero-delta 或 lineage 完整检查已正式实现。
- 不能认为 Stage 1 已经实现业务功能。
- 不能把 S02-P3 的报告等级协议当成真实报告生成能力。
- 不能跳过 v1.2 HTML/报告样板门禁继续做 S10/S11/S12/S18。
- 不能把 v1.2 中的 `90_用户原始上传数据_仅本地私有_禁止提交GitHub/` 复制进公开仓库。

## 下一步

下一步只执行 `S05-P3｜权威基准锁定`；不扩大到 Stage 5 复审、UI、报告、事实层、zero-delta 或自动接口。
