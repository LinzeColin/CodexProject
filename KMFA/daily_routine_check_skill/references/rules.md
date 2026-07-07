# 功能清单与规则清单

## A. 这版只有一个新增 automation

新增 automation/skill：

```text
Dingtalk-routine-check / 钉钉工作检查
```

它读取已有 DWS 输出目录，不设置、不创建、不替换上游 DWS 扫描 automation。
只保留这一个 automation，不为每条规则拆多个 automation。

北京时间触发窗口固定为：

```text
11:35 Asia/Shanghai -> morning_1135
17:05 Asia/Shanghai -> evening_1705
```

`due_time` 保留在 YAML 中作为业务参考，实际提醒窗口统一由上述两个 automation trigger 执行。每次运行必须记录 `run_at_beijing`、`check_date`、`trigger_window`、`rules_evaluated`、`rules_skipped`。

输入：

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip
```

zip 内需包含 `付款请示群` 和 `生产管理群` 的 `chat_records/chat_records.csv` 与 `_manifest/manifest.csv`；直接 `DWS_Outputs/` 群目录只作为 fallback。

输出：

```text
KMFA/metadata/daily_routine_check/private_runtime/daily_routine_check.sqlite
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/YYYYMM/*.jsonl
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/YYYYMM/*.log
钉钉机器人/私聊提醒 张霖泽
```

不输出汇总 Excel。

## B. 功能清单

### B1. DWS 输出读取

- 读取 `付款请示群` 和 `生产管理群` 的 `_manifest/manifest.csv`。
- 读取两个群的 `chat_records/chat_records.csv`。
- 读取 `chat_records/chat_records.jsonl` 和 `raw_messages.jsonl`，作为辅助证据。
- 建立 message/file/resource 的统一 source index。
- 使用 `message_id`、`sha256`、`message_time` 去重。
- 若某个路径缺失，生成 `SOURCE_MISSING` 数据质量事件，不直接崩溃。
- 若上游 DWS 输出最新消息早于 `check_date`，生成 `SOURCE_STALE` 数据质量事件。

### B2. 例行工作检查

- 按北京时间判断今日、周几、当月第三周周五。
- 按规则检查应发人、群、交付物、截止时间。
- 支持“多人任选其一”的交付规则，例如黄婷或李权智。
- 支持文本消息、图片消息、文件消息。
- 对图片消息可调用 OCR/LLM 判断图片标题和内容。
- 对未发、迟发、低置信度、疑似发错群、疑似发错表，生成事件。
- 通知张霖泽。
- 采用 idempotency key，避免同一个缺报事件反复刷屏。

异常类型固定为：

| abnormal_type | status | reminder_level | 含义 |
|---|---|---|---|
| `missing` | `MISSING` | `P0` | 到检查窗口仍未发现应发交付物 |
| `late` | `LATE` | `P1` | 已发现交付物，但消息时间晚于规则 `due_time` |
| `review` | `NEEDS_OCR_REVIEW` / `NEEDS_REVIEW` | `P1` | 图片、文件、OCR 或文本匹配置信度不足，需要人工确认 |
| `wrong` | `WRONG` | `P1` | 指定发送人发了互斥文档家族，例如把资金流水明细当成资金账户明细表 |
| `merged` | `MERGED_REVIEW` | `P1` | 同一条消息疑似同时满足多个必须独立的交付项，需要拆分或人工确认 |
| 空字符串 | `OK` | `P2` | 已按规则检测到交付物，只记录不提醒 |

### B3. 现金 OCR 监控

- 只监控付款请示群里杨婷发送的相关图片/文件。
- 分开识别 `资金账户明细表` 与 `资金流水明细/资金明细`。
- `资金账户明细表`：提取报表日期、公司/账户、昨日余额、今日收入、今日支出、今日余额、可用资金合计等。
- `资金流水明细/资金明细`：提取日期、事由、收/付款人、收支类别、收入、支出、银行、备注等流水行。
- 不把 `资金明细` 自动归到 `资金账户明细表`；默认归入 `资金流水明细` 家族，除非标题/表头特征强烈指向账户明细表。
- OCR 低置信度、标题冲突、数值不自洽时，通知张霖泽复核。

### B4. 现金风险判断

- 硬阈值：500000。
- 软阈值：1000000。
- P0 红色：总可用现金 < 500000，必须通知张霖泽。
- P1 黄色：500000 <= 总可用现金 < 1000000，通知张霖泽。
- P2 绿色：总可用现金 >= 1000000，只记录日志，不打扰。
- NO_DATA：到检查窗口仍未发现可用资金账户明细表，通知张霖泽。
- NEEDS_REVIEW：OCR/LLM 结果冲突或置信度低，通知张霖泽。

### B5. 日志与数据库

- 所有 run 写入 `run_log`。
- 所有检查结果写入 `routine_check_results`。
- 所有 OCR 任务写入 `ocr_jobs`。
- 所有 OCR 结构化结果写入 `ocr_extractions`。
- 资金账户结果写入 `cash_account_snapshots`。
- 资金流水结果写入 `cash_flow_entries`。
- 现金风险写入 `cash_risk_results`。
- 通知写入 `notification_events`。
- 数据质量问题写入 `data_quality_issues`。
- 每日 JSONL 日志同步到 OneDrive。
- 活跃 SQLite 定期 checkpoint/vacuum，定期镜像到 OneDrive，防止本机存储膨胀。

### B6. GitHub 同步治理

- 所有 skill/code/metadata/tests 改动必须自动或半自动同步到 `origin/main`。
- 不开 branch。
- 不开 PR。
- 不提交原始 DWS、SQLite、token、webhook、OCR 原文、截图、私有人员明细。
- 每次 push 前必须跑 validator 和 tests。
- 任意 agent 接手时，从 `SKILL.md`、`runbook.md`、`configuration.md`、`rules.md` 开始。

## C. 规则清单

### C1. 付款请示群：每日

| 规则 ID | 群 | 频率 | 截止时间 | 发送人 | 交付物 | 说明 |
|---|---|---:|---:|---|---|---|
| PAY_DAILY_CASH_ACCOUNT | 付款请示群 | 每日 | 10:30 | 杨婷 | 资金账户明细表 | 必须独立表；不能被资金流水明细替代 |
| PAY_DAILY_CASH_FLOW | 付款请示群 | 每日 | 10:30 | 杨婷 | 资金流水明细 / 资金明细 | 与资金账户明细表分开；资金明细归这个家族 |

### C2. 付款请示群：每周一

| 规则 ID | 群 | 频率 | 截止时间 | 发送人 | 交付物 |
|---|---|---:|---:|---|---|
| PAY_MON_EXISTING_BILLS | 付款请示群 | 每周一 | 11:30 | 杨婷 | 现存票据 |
| PAY_MON_DEPOSIT_COLLECTION | 付款请示群 | 每周一 | 11:30 | 杨婷 | 保证金回款表 |
| PAY_MON_COLLECTION_DETAIL | 付款请示群 | 每周一 | 11:30 | 杨婷 | 回款明细表 |

### C3. 付款请示群：每月第三周周五前

| 规则 ID | 群 | 频率 | 截止时间 | 发送人 | 交付物 |
|---|---|---:|---:|---|---|
| PAY_MONTHLY_TAX_RETURN | 付款请示群 | 每月第三周周五 | 17:00 | 吴云霞 | 纳税申报表 |
| PAY_MONTHLY_TAX_SETTLEMENT | 付款请示群 | 每月第三周周五 | 17:00 | 吴云霞 | 汇算清缴 |

### C4. 生产管理群：每日

| 规则 ID | 群 | 频率 | 截止时间 | 发送人 | 交付物 |
|---|---|---:|---:|---|---|
| PROD_DAILY_PERSONNEL | 生产管理群 | 每日 | 17:00 | 黄婷或李权智 | 每日人员表 |

### C5. 生产管理群：每周四

| 规则 ID | 群 | 频率 | 截止时间 | 发送人 | 交付物 |
|---|---|---:|---:|---|---|
| PROD_THU_FUND_PLAN | 生产管理群 | 每周四 | 17:30 | 黄婷或李权智 | 资金计划 |

### C6. 生产管理群：每周五

| 规则 ID | 群 | 频率 | 截止时间 | 发送人 | 交付物 |
|---|---|---:|---:|---|---|
| PROD_FRI_WORKER_HOURS | 生产管理群 | 每周五 | 17:30 | 黄婷 | 工人工时表 |
| PROD_FRI_PAYABLES | 生产管理群 | 每周五 | 17:30 | 黄婷 | 应付表 |

## D. OCR 分类原则

分类器不得只靠关键词硬判。Codex 应实现“配置化加权评分”：

```text
文本关键词得分
+ 标题区域 OCR 得分
+ 表头特征得分
+ 文件名/消息文本得分
+ 发送人/群/时间得分
- 互斥特征扣分
= document_type_score
```

分类结果应包含：

```json
{
  "document_type": "cash_account_statement | cash_flow_detail | routine_deliverable | unknown",
  "confidence": 0.0,
  "matched_features": [],
  "conflicts": [],
  "needs_review": false
}
```

资金账户明细表典型特征：

```text
资金账户明细表
账户明细
昨日余额
今日收入
今日支出
今日余额
银行存款
现金
承兑/票据
公司/账户维度
合计余额/可用资金
```

资金流水明细/资金明细典型特征：

```text
资金流水明细
资金明细
流水明细
日期
事由
收付款人/收款人/付款人
收支类别
收入
支出
转出
银行
备注
逐笔流水行
```

互斥原则：

- 强匹配 `今日余额/昨日余额/账户维度` 时倾向 `资金账户明细表`。
- 强匹配 `事由/收付款人/收支类别/逐笔流水行` 时倾向 `资金流水明细`。
- 同一消息不能同时满足两个每日独立交付项，除非明确存在两张附件且分别匹配。
