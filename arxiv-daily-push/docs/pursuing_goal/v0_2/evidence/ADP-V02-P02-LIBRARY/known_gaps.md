# Known gaps · ADP-V02-P02-LIBRARY（诚实边界）

## 只交付了 T067 的一部分
T067 = **Library + 笔记 + 全 provenance 导出**。本次**只上线 Library 只读视图**。

- **笔记（未做）**：需要新增 `cn_notes` D1 表 + 写入端点 + UI。本 phase 刻意不做——保持增量小、可验证、零 schema 变更。
- **全 provenance 导出（未做，且现在做会被自己的规则拒绝）**：`library_export.py` 要求
  `source_url, version, fetched_at, claim_evidence, license` **全齐才允许导出，缺一即 REFUSE**。
  线上 `cn_items` 只有 `source_url`、`fetched_at`；**`version` 与 `license` 属 S2 版本层，尚未部署**。
  故导出必须等 S2 版本层上线；**绝不臆造 provenance 来凑齐字段**。

## 语义边界
- "知识库"= `cn_reviews` 里有记录的条目（即你点过「学这个」或进过复习流）。含 `reps=0`（已加入未开始学）的卡片——列表用 `复习 0 次` 徽章如实标注，不含糊其辞。
- 顶部 `共 N 条` 是**未筛选总数**；分面芯片各自带本facet计数。筛选时列表变、总数不变（分面计数即为筛选后规模）。
- 列表上限 100 条（最近优先），超出时页面明示"仅显示最近 100 条"，不静默截断。

## 成本
纯读、无新增表、无新增抓取、不改 cron。修复后每次访问的 D1 读取量与 `cn_items` 规模**解耦**（只 `SCAN cn_reviews` + 按主键索引查 `cn_items`），符合 DIR-007 免费档；recurring $0/mo。

## 未做
- 不改 hero/动效/主题（T078 gate PASS 佐证）。
- 不改每日流水线、不改任何既有路由行为。
