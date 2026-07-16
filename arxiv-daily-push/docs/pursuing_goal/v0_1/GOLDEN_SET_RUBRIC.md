# Golden Set 人工评分标准（Human Rubric）· ADP-S1-P03-T020

> 500 条 Golden Set（`golden_set_500.json`）的**人工评分标准**。按 Owner 2026-07-16 决策，当前为 **provisional_machine**（机器基准），Owner/复核者按本 rubric 抽查升级为 `human_verified`。

## P0 事实（每条必检，准确率目标 ≥99%）
| 字段 | 判据 | 通过 |
|---|---|---|
| 标题 title | 与原文标题逐字一致 | 是/否 |
| 日期 date | = 原文 published_at 的日期（YYYY-MM-DD），无则 null | 是/否 |
| DOI | board1/2：与原文 DOI 一致或（原文无 DOI）为 null；不得编造 | 是/否 |
| 文号 doc_number | board3 政策原文：与原文文号一致；媒体报道无文号则 null | 是/否 |

- **准确 = 与原始证据（L3）一致，或如实为 null**。捧造任何字段 = 不通过。

## 关键声明证据（100% 目标）
- 人话版 L0/L1 中每个关键数字/日期/结果，必须能通过 locator 回到 factsheet 字段与 item_id。
- 抽查：随机点 5 条声明，确认 locator 指向的字段确实支持该声明。

## 空章节 / 模板泄漏（0 目标）
- L0/L1 不得为空、不得为模板套话（暂无/占位/TBD）。
- L2 若已生成，不得为模板 stub 或与他项重复。

## 语言（中文 UI）
- L0/L1 无未解释大段英文；英文原文只在 L3「原始证据（未加工）」显式标注。

## 事实/解释/推断
- L2（深度）须显式区分【事实】（可回 locator）/【解释】/【推断】（标注不确定）。

## 评分流程
1. 机器先跑 `content_release_gate.py`（key evidence 100% / 空·模板 0 / P0 fidelity）。
2. 人工按上表抽查 ≥50 条（10%），记录 P0 准确率；达 ≥99% 且关键声明证据 100%、空·模板 0，则 Golden Set 升 `human_verified`。
3. 未达标：记录不通过项到 item_id，回到抽取/契约修复，不放松阈值。
