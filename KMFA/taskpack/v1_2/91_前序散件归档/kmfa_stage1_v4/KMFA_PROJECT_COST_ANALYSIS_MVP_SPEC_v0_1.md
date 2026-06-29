# KMFA 项目成本分析 MVP 规格 v0.1

## 1. 目标

把当前人工项目成本分析流程，转化为 15 天内可上线的可追溯、可复核、可生成报告的系统流程。

MVP 不追求完全自动化，追求：

```text
文件可导入
字段可映射
成本可归集
差异可复核
报告可生成
关键数字可追溯
```

---

## 2. 项目成本主线

```text
客户
  ↓
合同 / 订单
  ↓
项目
  ↓
收入确认 / 开票 / 回款
  ↓
人工 / 材料 / 机械 / 外协 / 运输 / 差旅 / 税费 / 质保
  ↓
项目真实成本
  ↓
项目真实毛利 / 现金毛利 / 风险等级
  ↓
经营分析报告
```

---

## 3. P0 字段字典

| 字段 | 类型 | 必填 | 来源 | 说明 |
|---|---|---|---|---|
| company_entity | text | 是 | 银行/财务/合同 | 公司主体 |
| project_id | text | 是 | 红圈/WPS/人工表 | 项目唯一标识；没有则生成临时 ID |
| project_name | text | 是 | 红圈/WPS/合同 | 项目名称 |
| customer_name | text | 是 | 红圈/WPS/合同 | 客户名称，报告中可脱敏 |
| contract_amount_tax_included | amount | 是 | 合同/红圈/WPS | 含税合同金额 |
| tax_rate | percent | 条件必填 | 合同/发票/税务 | 税率 |
| project_status | enum | 是 | 红圈/WPS | 在制/完工/结算中/已结算/暂停 |
| revenue_recognized | amount | 条件必填 | 金蝶/财务 | 已确认收入 |
| invoice_amount | amount | 条件必填 | 开票/税务 | 已开票金额 |
| cash_collected | amount | 是 | 银行/WPS回款 | 已回款金额 |
| cost_labor | amount | 可选 | 财务/人工表 | 人工成本 |
| cost_material | amount | 可选 | 财务/采购 | 材料成本 |
| cost_machine | amount | 可选 | 项目/财务 | 机械设备成本 |
| cost_subcontract | amount | 可选 | 外协费用 | 外协/委外成本 |
| cost_transport_travel | amount | 可选 | 费用/日记账 | 运输、差旅、吊装等 |
| cost_tax_fee | amount | 可选 | 税务/财务 | 税费影响 |
| cost_other | amount | 可选 | 财务/人工调整 | 其他成本 |
| management_adjustment | amount | 可选 | 人工复核 | 管理调整 |
| adjustment_reason | text | 条件必填 | 人工复核 | 有调整时必填 |
| source_confidence | enum | 是 | 系统生成 | HIGH/MEDIUM/LOW/MANUAL_REVIEW |

---

## 4. 核心公式

```text
合同不含税收入 = 含税合同金额 / (1 + 税率)

已回款率 = 已回款金额 / 含税合同金额

已开票率 = 已开票金额 / 含税合同金额

项目已归集成本 = 人工 + 材料 + 机械 + 外协 + 运输差旅 + 税费 + 其他

管理口径项目成本 = 项目已归集成本 + 管理调整

项目真实毛利 = 管理口径收入 - 管理口径项目成本

项目真实毛利率 = 项目真实毛利 / 管理口径收入

项目现金毛利 = 已回款金额 - 已现金支付成本

成本完整度 = 已匹配成本来源数 / 应有成本来源数

项目风险等级 = f(毛利率, 回款率, 账龄, 成本完整度, 税务匹配, 项目状态)
```

---

## 5. 风险规则 MVP

| 规则 | 触发条件 | 状态 |
|---|---|---|
| 毛利异常 | 毛利率 < 目标阈值，或由正转负 | MANUAL_REVIEW |
| 回款异常 | 到期未回款或账龄超过阈值 | PARTIAL / MANUAL_REVIEW |
| 成本缺失 | 项目有收入但成本来源不足 | PARTIAL |
| 税率不匹配 | 合同税率、发票税率、账务税率不一致 | MANUAL_REVIEW |
| 项目名称匹配失败 | 不同来源项目名无法自动匹配 | MANUAL_REVIEW |
| 资金无法核销 | 回款无法匹配到合同/项目 | MANUAL_REVIEW |
| 源数据过期 | P0 文件超过 freshness 阈值 | OUTDATED |

---

## 6. MVP 输出表

| 输出表 | 用途 |
|---|---|
| project_cost_summary | 每个项目的收入、成本、毛利、回款、风险 |
| project_cost_detail | 成本分项明细与来源 |
| project_revenue_collection | 合同、开票、回款、应收 |
| project_tax_match | 合同税率、发票税率、账务税率匹配 |
| project_adjustment_log | 人工调整与理由 |
| project_review_queue | 需要人工复核的问题列表 |
| project_report_export | 报告用汇总表 |

---

## 7. MVP 验收标准

1. 至少支持 3 个实际项目样本跑通完整流程。
2. 每个项目能生成收入、成本、毛利、回款、税务、风险状态。
3. 每个关键金额能追溯到文件、sheet/table、字段、导入批次。
4. 不能匹配的项目、金额、税率、回款进入人工复核，不得静默忽略。
5. 报告中不出现“AI猜测值”；估算值必须标注为估算或人工调整。
6. 缺 P0 数据时，报告必须显示 PARTIAL 或 OUTDATED，不得显示为完整报告。
