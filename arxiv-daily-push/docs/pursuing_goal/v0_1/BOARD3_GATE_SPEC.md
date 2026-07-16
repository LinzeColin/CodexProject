# Board 3 Eligibility Gate Spec · ADP-S3-P03-T037

**排序前**把只有官方原文的政策文档准入 Board 3（政策视图），**排除新闻噪声**，并识别四类效力日期
（成文/发布/施行/失效）与状态。工具：`tools/board3_gate.py`，基于 T033 身份 + T034 政策日期 + T036 分类。**NOT_DEPLOYED**。

## 准入门（eligibility gate）

`is_eligible(source_authority, doc_type)`：准入当且仅当
- **source 官方**（T033 → authority ∈ {A0, A1}）**且**
- **doc_type 为官方原文 primary**（∈ {formal 正式文件, consultation 征求意见}）。

**媒体/搜索/聚合源**（chinanews/people/sina 等）→ 非官方 → **拒**；**新闻/解读**类型 → 非 primary → **拒**（可作 discovery 线索，T038 回溯官方原文）。→ 政策视图**排序前**即无新闻噪声。

## 效力日期与状态抽取

`extract_dates_status(html, title)` → `PolicyDates{written 成文, published 发布, effective 施行, expired 失效, status}`：
- **成文/发布**：元信息表 成文日期/发布日期（复用 T034）。
- **施行**：`自YYYY年MM月DD日起施行` / 施行日期 / 自公布之日起施行（=发布日）。
- **失效**：`自YYYY年MM月DD日起废止` / 失效日期 / 废止日期。
- **status**：现行有效/已废止/失效/尚未施行；有失效日→已废止，有施行无失效→现行有效。

日期归一化 `norm_date`（中文→YYYY-MM-DD，不臆造，缺失=None）。

## 验收（`test-results/gate_tests.txt`，PASS）

200 条政策视图抽样 = **85 条真实 board3 媒体新闻**（chinanews/people/sina，如「国台办：…」「胡萝卜素是黄桃的22倍…」）+ **115 条合成官方政策文档**（已知成文/发布/施行/失效日期）：
- **污染率 <1%**：门准入 115（全官方）、拒 85（全媒体）→ 准入视图新闻污染 **0/115 = 0.000%**。
- **关键日期准确率 ≥99%**：准入官方文档的成文/发布/施行/失效/状态抽取 **115/115 = 100%**。

## 边界

真实 board3 当前 100% 媒体（DRIFT-FACT-006）→ 门全拒，政策视图靠官方适配器（T034-T036）填充；本任务的官方样本为合成已知日期（真实各站日期在适配器 fixtures）。门未接 worker ranker（NOT_DEPLOYED）。
