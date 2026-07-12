# 数据合同

## 输入槽位

本 skill 使用 7 个用户输入槽位：

| 槽位 | 业务含义 | 必需 |
|---|---|---|
| `collection_2026` | 2026 年回款表 | 是 |
| `invoice_tax_cash` | 开票纳税资金汇总表 | 是 |
| `receivable_contract` | 应收账款合同登记 | 是 |
| `aging` | 应收账龄表 | 是 |
| `deposit` | 2026 年保证金 | 是 |
| `three_major_projects` | 三大项目 | 是 |
| `project_status_contracts` | 生产项目状态表与红圈主合同 | 是 |

任务包原文中的“6 个业务输入包”仍保留为计算口径，其中项目合同状态包可以由多个物理
文件构成。本 skill 的 7 槽位是为了让非专业使用者更容易检查每月文件是否齐全。

## 输出

正式输出仅有两个：

| 类型 | 文件名 |
|---|---|
| Excel | `经营管理分析报表 YYYYMM.xlsx` |
| PDF | `董事会经营分析摘要 YYYYMM.pdf` |

`自动验收报告 YYYYMM.json` 是内部治理文件，不是正式交付报告。

## 数据登记

每个输入文件至少登记以下治理字段：

- input slot
- required/recommended 状态
- SHA256
- byte size
- extension
- symlink flag
- sheet names count and sheet hash
- matched pattern
- owner authorized plaintext upload flag
- upload manifest ref when plaintext is committed

默认不登记原始敏感业务明细；如提交源表正文或明文报告，必须先登记 owner 授权、
secret 扫描结果和 `KMFA/metadata/` 下的 repo path。
