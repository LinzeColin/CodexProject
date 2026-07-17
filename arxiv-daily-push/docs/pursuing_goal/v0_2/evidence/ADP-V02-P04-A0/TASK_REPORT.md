# ADP V0.2 生产集成 · P04 — board3 A0 官方原文接入每日 cron（PRODUCTION DEPLOY）

## 为什么这是 V0.2 最关键的一批
board3「中国政策法规」此前**只抓媒体 RSS**（人民网/中新网/新浪）——即库里全是**关于**政策的**报道**，**没有一条政府官方原文**。这也是 P03「标识符匹配」徽章无法升级成「权威原文命中」的根因。S3（T031–T040）建好了 A0 适配器却**从未接进生产 cron**（NOT_DEPLOYED），T040 只留下一个**只读**canary。P04 把它真正接上。

## 交付
1. **4 个 A0 官方源接入 REGISTRY(board3, `method:'a0'`)**，与 RSS 共用同一套纪律（健康/连续失败 3 次自动停用/3 天后自愈重试）：
   | source | 列表页 | 性质 |
   |---|---|---|
   | `stats-gov` | stats.gov.cn/sj/zxfb/ | 及时，实测 15 条、日期真实（2026-07-16） |
   | `cac-gov` | cac.gov.cn/ | 及时，含法规征求意见稿原文 |
   | `ndrc-gov` | ndrc.gov.cn/xxgk/ | 及时，实测 20 条 **20/20 带真实日期**，标题常含**文号** |
   | `gov-cn-policy` | gov.cn/zhengce/xxgk/ | **权威但不及时**（静态索引 → 基础性法规，2019/2020） |
2. **`parseA0` 共享解析器** + 每源 `match/resolve/date` 配置；**日期只在能从 URL 真实读出时才给**（新版 gov.cn `/content/YYYYMM/` 无「日」→ `published_at=null`，**不编造**）。
3. **`/api/a0-canary` 升级为真实的逐源边缘可达性探针**，复用**同一个** `parseA0`（替掉 T040 那段重复的内联正则——它只认旧链接形态，这正是它一直只吐 2019/2020 老文件的原因），并给出翻开关的前置条件 `safe_to_flip_flag`。
4. **`BOARD3_A0_ONLY` 仍为 `false`**：本次只做摄取，不翻开关（详见 known_gaps §1——库里没有 A0 之前翻开关会**清空 board3**）。

## 我自己先抓到的缺陷（未等复核）
`parseA0` 初版正则 `<a\s([^>]*?)href=...>([\s\S]{0,300}?)<\/a>` 在**未闭合 `<a`** 洪水下是**二次回溯**：2000→5.1ms、4000→20.3ms、8000→**81ms**（翻倍→4×）。真实页面无事（209KB 仅 0.53ms）只因格式良好；改版/畸形 HTML 会打进 **cron 的 CPU 预算**。**改为有界属性 + 不要求 `</a>`（取到下一个 `<`）→ 线性**：2000→2.68、4000→5.56、8000→11.11、16000→22.14ms（翻倍→2×），且**抽取结果逐条不变**。

## 独立对抗复核：BLOCK ——两条都真，都是我的错
1. **★未鉴权写回归★**：我把 canary 的裸 `fetch()` 换成 `fetchFeedText` 时**静默继承了它的 R2 双写**。于是一个自称 `non_destructive:true`／「writes nothing」的**未鉴权**端点，冷启动每次命中**真写 15 次**（3 R2 PUT + 3 `cn_artifacts` INSERT + 9 `cn_meta` 计数），并污染只在 `runDaily` 重置的 `_rawWrites/_rawUsage` 预算计数——**在 Owner 签署的 $0 预算上，一个谎报自身副作用的决策仪器**。**修复**：`fetchFeedText(s.list, env, null)`，命中既有 `&& sourceId` 守卫 → 真正只读。
2. **★我的 ndrc 排除理由事实错误★**：我写「整页无日期 → 非日更源」。复核证伪：**28 个 `<span>2026/07/16</span>`**（斜杠格式，我只 grep 了短横线格式）、**103 条（去重 81）发改委自有 `t{YYYYMMDD}_` 政策链接**（我只看了 gov.cn 链接）。我不仅**删掉假声称**，而是**把 ndrc-gov 真正接了进来**——它恰是**带文号的官方原文**来源。

复核同时确认（皆为执行验证）：DIR-007 **20/50 外部子请求**（且指出我原注释把 D1/R2 错并入这 50——internal services 另有 1000 独立额度，注释已改正）；单源失败/超时**不会中断 cron**（`Promise.allSettled` 用法正确）；**零日期编造**（6 条 `/202607/` 全部 `published=null`）；**幂等**（`id='a0:'+sha1(source|url)` + `ON CONFLICT`，两次运行 id 集合一致、`first_seen_at` 保留）；**board3 不会被清空/挤掉**（`BOARD3_A0_ONLY=false`；105 媒体 + 32 A0 = 137 远低于 `KEEP_PER_BOARD=300`；prune 保护被复习/精选/讲义引用的条目）；XSS 走既有 `esc/safeHref` 无新汇聚点。

## 诚实边界
见 `known_gaps.md`：不翻开关；`gov-cn-fagui` **403**、`nda-gov` **193 字节空壳**故不接；只取列表页元数据（无正文 → A0 的 `summary` 为空）；**A0 原始字节实际未归档 R2**（RSS 先耗尽 `RAW_MAX_PER_RUN=3`）故不声称；`kind:'official'` 新枚举与 `seedSources` 清理的孤儿风险。

release_mode: **PRODUCTION**。未自签。
Ends IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION.
