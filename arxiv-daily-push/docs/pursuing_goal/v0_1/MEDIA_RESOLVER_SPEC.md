# Media-Lead Resolver Spec · ADP-S3-P03-T038

媒体可**发现线索**，但线索必须**回到发布机关官方原文**才能带官方权重，且同一事件的转载**合并为一个 canonical 事件**；
无原文则 **ABSTAIN（UNKNOWN）**，**绝不冒充官方**。工具：`tools/media_resolver.py`，基于 T024 身份。**NOT_DEPLOYED**。

## Resolver（媒体线索 → 官方原文）

`resolve_lead(lead, by_num, by_title)`：
1. **发文字号**：媒体正文/标题中出现的 `发文字号`（白名单前缀 国发/国办发/国办函/发改/网信发/国令第…〔YYYY〕N号）若命中官方索引 → **绑定官方原文**（authority=A0，signal=docnum）。
2. **referenced_title**：媒体引用的官方标题归一化后命中官方索引 → 绑定（signal=title）。
3. **都不命中** → **ABSTAIN**（status=ABSTAIN，authority=media_lead，`official_canonical_id=None`）。

`impersonates_official` **恒为 False**——未解析线索永不声称官方。发文字号抽取用**白名单前缀**精确匹配，避免把句中「印发」等误并入字号。

## Canonical 事件去重（合并转载）

`group_events`：已绑定线索按**官方 canonical_id** 分组（多家媒体转载同一官方文件 → 一个 official-backed 事件，`repost_count` 计转载数）；ABSTAIN 线索按其标题的 `ttl:` 分组（重复新闻仍收拢，但保持 ABSTAIN、不带 A0）。

## 验收（`test-results/resolver_tests.txt`，PASS）

50 媒体线索 = 28 可解析（20 引用发文字号 + 8 引用官方标题，含同一官方文件的多家转载）+ 22 真实 board3 纯新闻（无官方原文）：
- **有原文则绑定原文**：28 条绑定到对应 `doi:gov/*`（authority=A0，signal docnum/title）；同一官方文件（doi:gov/1）转载 4 家 → **合并为 1 事件 repost_count=4**。
- **无原文则 UNKNOWN/ABSTAIN**：22 条纯新闻 → ABSTAIN（authority=media_lead）。
- **不冒充官方**：**impersonations=0**；ABSTAIN 事件均不带 A0。
- 50/50 解析正确；8 official-backed 事件 + 22 abstained 事件。

## 边界

发文字号白名单需随新央源扩充；标题匹配为归一化相等（复杂改写标题可能不命中 → 保守 ABSTAIN，不误绑）。resolver 未接 worker（NOT_DEPLOYED）；真实媒体→官方的模糊匹配（实体/日期近似）留待需要时增强，本任务用确定性发文字号/标题信号。
