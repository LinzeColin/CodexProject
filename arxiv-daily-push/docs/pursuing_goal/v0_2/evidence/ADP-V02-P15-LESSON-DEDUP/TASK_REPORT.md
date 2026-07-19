# ADP-V02-P15 — 讲义八段跨段逐字去重（深度/权威修复）

状态: **CONFIRMED_SOUND**（独立对抗复核：亲手实跑全部承重项 + 2 项破坏测试——把 mechanism 改回 raw slice→验证器 FAIL、删 claimed→守卫 FAIL，证明验证器/守卫均承重；实施者未自签）
release_mode: **PRODUCTION** — `24ffba0cdecf` → `e6b266d0874b`（Version 337e0a80-94a7-4eca-9244-4828fe3ec628）

## 为什么（观察驱动，非臆造）
挑剔地看**线上** adp.linzezhang.com 今日讲义时发现：第 3 段「机制拆解」的最后一句
> INTSD contains street-level images spanning 41 traffic signboard classes…

与第 4 段「证据与数字」**一字不差重复**。根因在 `buildLesson`：各段从**重叠的句池**取句——
`机制拆解`=`sents.slice(2,5)`、`证据与数字`=含数字句、`领域脉络`(无类目时)=`sents.slice(2,3)`、
`反例与边界`=含局限词句。同一句同时命中两段就逐字重复。数字/局限句常落在摘要中段，故这是
**系统性、每篇都可能中**的内容质量缺陷，直接损「深度/权威」——权威系统里重复内容读作生成 bug。

## 做了什么（最小、确定性、不改模板结构）
一句只进它最专属的段落：`人话版`(开头两句) › `证据与数字`(数字句) › `反例与边界`(局限句) ›
`领域脉络` 位置回退句，依次写入 `claimed` 集合；`机制拆解`/`领域脉络` 取中段句时 `!claimed.has(s)`
排除已认领句。八段标题/顺序/回退文案/确定性全不变，仅修句子分配。数字/局限句也排除开头两句
（消除 `人话版`↔`证据与数字`、`人话版`↔`反例与边界` 的同类重复）。`template_ver` 不动（同模板 bugfix）。

## 验证器（承重再推导 + 负控）
`arxiv-daily-push/tools/verify_lesson_dedup.mjs`：从**已部署**的 worker_cloud.js 抽取
`splitSentences`+`buildLesson`（绝不复刻）实跑 3 夹具，断言无任何摘要原句出现在 ≥2 段。
**负控**：内联 pre-fix 旧逻辑跑同一夹具，证明它在每条路径上**确会**重复——
- INTSD：机制拆解↔证据与数字
- cats 为空：领域脉络↔机制拆解
- 数字句在开头：人话版↔证据与数字
三条负控全部触发 → 断言承重（夹具能判别；不是空跑）。

> 验证器在开发中**抓出我第一版修复的漏洞**：只认领了 numeric/limits，漏了 `领域脉络`(位置回退)↔
> `机制拆解` 这条路径，cats-空夹具仍重复。补 loreSents 先认领后才 3/3 过——部署前挡下不完整修复。

## CI 守卫（push 路径无 node，故静态 + 负控）
`tests/governance/test_adp_lesson_dedup.py`：`_dedup_violations()` 钉住去重机制在**线上源**存在
（claimed Set、机制拆解 `!claimed.has`、numeric 开头过滤、无裸 `机制拆解 sents.slice`）；
**负控** `test_negative_control_prefix_code_is_flagged` 在**逐字 pre-fix 源**上要求 4 项缺陷全部触发
（否则探测器欠检、可能空过回归 worker）。node 在场时另跑行为验证器（本地 4/4，CI 自动 skip 但静态仍跑）。

## 诚实边界
- 讲义从**存储的 sections_json** 渲染，修复对**今晚 20:30 UTC cron 起的新讲义**生效；07-18 及以前的
  历史讲义仍是旧存储内容（不回溯重写，属历史）。故本次不做「线上讲义肉眼验证」——线上证明是
  **抽取已部署代码实跑**（build 戳 e6b266d0874b 已确认线上一致）。
- 这是内容**去重**，不改抽取/选择/排程；纯 `buildLesson` 展示层确定性变换。

## 上线验证
`/build.json=e6b266d0874b`（= 部署 Version 337e0a80）；首页 200、footer `build e6b266d0874b`；
`/api/runhealth` 正常（07-18 run 590 候选、meta requested:12/matched:0 为干净 404 非 429、无 meta: 标记）。
验证器 exit 0（3/3 无重复 + 3 负控触发）；Python 守卫 4/4。

IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION（已完成：独立对抗复核 CONFIRMED_SOUND；已部署 e6b266d0874b）
