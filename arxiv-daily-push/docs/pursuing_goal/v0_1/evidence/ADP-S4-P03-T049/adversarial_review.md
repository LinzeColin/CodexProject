# 对抗复核记录 · ADP-S4-P03-T049（A1 省级 adapter family 自审→修复→复验）

用独立 skeptic 对 adapter family 做对抗复核（试图证明「验收 PASS 而宣称的解析为假」）。

## 发现（HOLE_FOUND，真实缺陷）
首版 `normalize()` 的日期抽取 `date_re.search(html)` 取**页面首个日期串**。中文政府 CMS 文章页在真实文档 `PubDate/pubdate` meta **之前**先出现 `<meta name='Maketime'>`（页面**渲染/抓取时间戳**）——于是抽到的是渲染时间戳，非文档发布日期：
- 山东：报 `2026-07-16`（Maketime），真实 pubdate `2026-07-09`（且 URL `/art/2026/7/9/` 佐证），成文 `2026年7月6日`。
- 江苏：报 `2026-07-15`（Maketime），真实 `2026-07-14`（URL `/art/2026/7/14/` 佐证）。
- 北京：偶然正确（无 Maketime，首个日期恰是 PubDate `2026-07-14`）。
`has_date` 只查真值 → gate 误 PASS，contract_report 把渲染时间戳当文档日期，3 省中 2 省的「抽到 doc_date」宣称为假。

## 修复
- `_extract_date(html)`：①剥离 `<meta Maketime>` ②优先 CMS `pubdate/PubDate/publishdate` meta ③回退 `发布/成文日期` label ④再回退 profile.date_re。
- `run_contract` 加 **3 个交叉校验**（会捕获该 bug）：`date_not_render_timestamp`（doc_date≠Maketime）、`date_matches_url_path`（art-cms 与 `/art/Y/M/D/` 一致）、`date_matches_pubdate_meta`（与 pubdate meta 一致，绑定北京）。

## 复验（第二个 skeptic）→ CONFIRMED_SOUND
- 三省 doc_date 均为真实发布日期：江苏 2026-07-14、山东 2026-07-09、北京 2026-07-14（皆对齐 pubdate meta / URL 路径）。
- Maketime 剥离对真实 fixture 生效，无泄漏。
- `date_matches_url_path` 对 art-cms 非平凡（url_date 非空；回归到 Maketime 会令两项交叉校验翻 False，gate FAIL）——真判别。
- 无「gate PASS 而日期错误」的残留场景。

**结论：缺陷已修，三省日期正确且三重交叉校验。** 实现者不自签任务 PASS —— 交独立复核。
