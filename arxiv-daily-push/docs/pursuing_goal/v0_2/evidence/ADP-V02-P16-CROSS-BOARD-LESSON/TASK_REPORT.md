# ADP-V02-P16 — 每板块每条目都有讲义（跨板块空盒修复）

状态: **CONFIRMED_SOUND**（独立对抗复核：亲手 curl 线上验证 board-2/3 revealBox 非空八段 + 破坏测试——删 itemPage 现算回退→验证器与 Python 守卫双 FAIL，证明静态断言承重；独立复算 content_tree_hash 逐字相等、自哈希自洽、无自签无造假；实施者未自签）
release_mode: **PRODUCTION** — `e6b266d0874b` → `e8d9f0c0fe59`（Version 531a40fe-bbea-4fc8-ab37-e0f521f98760）

> 计量口径（复核问及）：本报告的「482 字符」= board-3 revealBox **内层 HTML** 的字符数（= 证据 `test-results/live_board3_revealbox.html` 的 `len()`，可复现）；去标签的**可见文本**约 309 字。方向性结论（`<p></p>` 空盒 → 完整八段）已被复核独立线上证实。

## 为什么（观察驱动）
挑剔地看**线上**知识库时，点开 board-2(期刊)/board-3(政策) 条目的 item 页——「显示答案/讲义」揭示的是
**空盒 `<p></p>`**。对照 arXiv 条目 revealBox 有完整八段（1606 字符），政策/期刊条目是 7 字符空盒。
这些条目已在复习轮转（「学习中/复习 1 次」），用户对着**空内容做主动回忆**。

根因：`makeLesson` **只为每日 pick 生成讲义**（worker 949 行 `if (pick) { await makeLesson… }`），
非 pick 的板块二/三/四条目 `cn_lessons` 无行；itemPage/reviewPage 无讲义时退回 `<p>{summary}</p>`，
而政策/期刊源摘要为空 → `<p></p>`。这是「多板块/权威/深度」的系统性缺陷——非 arXiv 板块是多板块系统的一半意义。

## 做了什么（纯展示层、确定性）
itemPage 与 reviewPage 无存储讲义时**确定性现算**：
`const lesson = stored || { sections_json: JSON.stringify(buildLesson(item)) }`。
`buildLesson` 走 **P15 去重后**的版本；摘要为空时其八段各自回退为可读提示（如「本文标题：X。摘要过短，请点原文精读。」）。
复习页 SELECT 补 `i.categories, i.board_id`（buildLesson 需要，否则 领域脉络/板块 回退缺字段）。
**零 DB 写、零外部调用、确定性**；itemPage 的 `if (lesson)` 讲义卡也因此对每条目都显示。

## 与旧 P14 记录的对照（本会话老病：静默失败）
和 P08「静默空转」同形：功能"看着在跑"（复习流有评分按钮、卡片有标题），但复习的**内容是空的**，
没人注意因为没人点开看。这次靠**挑剔地实地点开**才发现——verify-not-live 的纪律。

## 验证（承重再推导 + 负控 + 线上即时验证）
- `tools/verify_item_lesson_fallback.mjs`：抽取**已部署** buildLesson 实跑 3 夹具——board-3 政策(无摘要)、
  board-2 期刊(无摘要)、board-1 arXiv(正常)——断言现算八段讲义**非空**（每段 ≥1 句，含回退）。
  **负控**：逐字复现旧的 reveal 选取逻辑，证明它对无摘要条目产出**空盒 `<p></p>`**（正是线上观察到的缺陷）。
  静态断言：发货源 itemPage+reviewPage 均含现算回退（≥2 处）。3/3 + 负控触发 + 静态过，exit 0。
- `tests/governance/test_adp_item_lesson_fallback.py`：静态钉两处 fallback + reviewPage SELECT 补字段；
  负控 `_fallback_violations` 在逐字 pre-fix 源上触发（缺 fallback + 瘦 JOIN）。node 在场另跑行为验证器。
- **线上即时验证**（本次不需等 cron，itemPage 现算渲染）：部署后 curl board-3 政策项，revealBox 从
  `<p></p>`(7 字符) → **482 字符完整八段**（人话版=「本文标题：国务院…批复。摘要过短，请点原文精读。」、
  领域脉络=「来源板块：板块三 · 中国政策法规。」等）；board-2 期刊同；board-1 arXiv 不变。存证见 test-results/。

## 诚实边界
- 现算讲义对**无摘要**条目是「可读回退提示」，不是从无到有编内容——buildLesson 抽不到就回退，绝不臆造。
- 只改渲染路径；不动抓取/选择/排程/DB。历史存储讲义（含 P15 前的重复）不受影响，但现算路径永远走最新 buildLesson。
- 未改 `makeLesson` 的「只为 pick 生成存储讲义」策略——现算回退已覆盖展示需求，无需为每条目写库（省 D1 写、避 DIR-007 子请求）。

## 上线验证
`/build.json=e8d9f0c0fe59`（=Version 531a40fe）；board-1/2/3 item 页 revealBox 均非空八段；语法 node --check 通过。

IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION（已完成：独立对抗复核 CONFIRMED_SOUND；已部署 e8d9f0c0fe59）
