# 独立对抗复核 — ADP V0.2 P04 board3 A0 官方原文接入每日 cron

复核者：独立 general-purpose skeptic（非实施者；实施者不自签）。这是迄今风险最高的一批——**改的是每日 cron**。

## 实施者自查先抓到的（未等复核）
`parseA0` 初版正则 `<a\s([^>]*?)href=...>([\s\S]{0,300}?)<\/a>` 在**未闭合 `<a`** 洪水下**二次回溯**：2000→5.1ms、4000→20.3ms、8000→**81ms**（翻倍→4×）。真实页面无事（209KB 仅 0.53ms）**只因格式良好**；改版/畸形 HTML 会打进 **cron 的 CPU 预算**。改为**有界属性 + 不要求闭合 `</a>`**（取到下一个 `<`）→ **线性**（8000→11.11ms，翻倍→2×），**抽取结果逐条不变**。

## 第一轮：BLOCK —— 两条,都真,都是实施者的错

复核明确：**「the actual cron wiring is sound … but the change ships two verifiably false assertions」**——即判的是**诚实性**，不是功能。

1. **★未鉴权写回归★**：实施者把 canary 的裸 `fetch()` 换成 `fetchFeedText`，**静默继承了它的 R2 双写**（`RAW_DUALWRITE=true` 且 `RAW` 桶已绑定）。于是一个自称 `non_destructive:true`／`writes nothing`／「只读」的**未鉴权**端点，冷启动每次命中执行 **15 次持久化写**（3 R2 PUT + 3 `cn_artifacts` INSERT + 9 `cn_meta` 计数，复核用录制 mock 实跑确认），并污染 `_rawWrites/_rawUsage`（模块级，只在 `runDaily` 重置）。**在 Owner 签署的 $0 预算上，一个谎报自身副作用的决策仪器。**
2. **★ndrc 排除理由事实错误★**：实施者写「整页无日期 → 非日更源」。复核证伪：**28 个 `<span>2026/07/16</span>` 斜杠格式日期**、**103 条（去重 81）发改委自有 `t{YYYYMMDD}_` 政策链接**（正是 `stats-gov` 的日期解析器已能处理的形态），其中 15 条在弹窗**之外**。实施者的检验有两处错：只 grep 了短横线格式、且只看 gov.cn 链接。

**第一轮同时确认（皆执行验证）**：DIR-007 **20/50** 外部子请求（并**纠正了实施者注释的事实错误**——原注释把 D1/R2 并入这 50，实际 internal services 另有 **1000/次**独立额度）；单源失败/超时/垃圾 HTML **均不中断 cron**（`Promise.allSettled` 用法正确）；**零日期编造**（6 条 `/202607/` 全部 `published=null`）；**幂等**（两次运行 id 集合一致、`first_seen_at` 保留）；**board3 不会被清空或挤掉**（`BOARD3_A0_ONLY=false`；105+32=137 远低于 `KEEP_PER_BOARD=300`；prune 保护被复习/精选/讲义引用的条目）；XSS 走既有 `esc/safeHref` 无新汇聚点；BUILD 自哈希一致。

## 修复
1. `fetchFeedText(s.list, env, null)` —— 命中既有 `&& sourceId` 守卫（复核自己提的一字修复）。
2. **不是删掉假声称，而是把 `ndrc-gov` 真正接入**为第 4 个源（它恰是带**文号**的官方原文来源）；`A0_PER_RUN` 3→4。

## 第二轮：CONFIRMED_SOUND
- **FIX1 已解**：`sourceId===null` 在 `dualWriteArtifact` 之前短路；**所有**写入都在该函数内（R2 PUT / `cn_artifacts` INSERT / `r2Bump`）→ 冷启动**零写入**；`_rawWrites/_rawUsage` 亦在其内，故不再污染 `runDaily` 共享的模块状态；编解码路径只读 `buf`、不碰 `sourceId`，故解码不受影响。
- **FIX2 已验**：对**线上真实页面**跑真实代码路径：**parsed=20、with_date=20/20、unique=20**，抽样解析后 URL **全部 200**（如 `t20260716_1406539.html` = 海水淡化产业发展行动方案，**发改环资〔2026〕1062号**），**真官方原文、无垃圾、无重复**。`[a-z/]+` 字符类**漏掉 0 条**（补集为空）。
- **正则无法逃逸 host**：`.` 不在 `[a-z/]` 内 → `../` 遍历结构上不可能；`^`/`$` 锚定；`:`/`@`/大写/query/fragment 全在类外。**11 个恶意 href 全被拒**；即便匹配也只能落在 `https://www.ndrc.gov.cn/xxgk/` 之后的 path。
- **四源实测**：gov-cn-policy 13/7 dated（`/202607/` 年月形态诚实为 `null`）、stats 15/15、cac 4/4、ndrc 20/20，各自解析到**自己的 host**。
- **DIR-007 复算确认**：按 REGISTRY 编程计数 RSS = 13（`min(n,4)` 逐板求和）+ arxiv 2 + biorxiv 1 + A0 4 = **20/50**；新注释**事实正确**。
- **排除项仍属实**：`gov-cn-fagui` **HTTP 403**；`nda-gov` **恰好 193 字节**，正文是 `<script>window.location.href='/sjj/index_pc.html';</script>`。
- BUILD 戳一致；`node --check` 通过；此前 PASS 未被扰动；**无新缺陷**。

**终判：VERDICT: CONFIRMED_SOUND**

## 复核放行后，实施者又主动收紧一处
`gov-cn-policy` 的 `match` 原为 `^https?:\/\/[^"']*\/zhengce\/content\/`——**未钉 host**；而 `a0Board3Eligible` 按 `source_id` 白名单放行、**不再校验 hostname**，故 gov.cn 列表页上的**站外**链接会被当作「官方原文」入库。复核将其列为「不阻塞、需控制 gov.cn HTML 才能利用」而未重开；但 P04 的全部前提就是**权威原文**，故实施者仍**钉住 host**。负控制：`evil.com/zhengce/content/...` 伪装 → **拒（0）**；真 `www.gov.cn/zhengce/content/...` → **通过（1）**；四源产出不变。

## ★上线后才暴露的最危险一个：我的安全仪器曾恒真★
边缘探测发现 canary 报 **`board3: 总105 | 官方A0 105 | 媒体 0`、`safe_to_flip_flag: true`**——与事实相反（当时库里 **0 条**官方）。
根因：canary 的 board3 查询**漏选 `board_id`**，而 `a0Board3Eligible` 首行是 `if (it.board_id !== 'board3') return true` → `undefined !== 'board3'` → **每行恒真通过**。
**后果**：若有人信了 `safe_to_flip_flag` 去翻开关，**board3 会被清空**——正是该 flag 存在要阻止的灾难。
**且 T040 原版 canary 同样漏选**，其 `board3_media_demoted_to_discovery: 0` 从来是**空跑**（从未真正检验过那道门）——与 T086 抓到的「恒真永不判 blocker」同类。
已修（补 `board_id`）。**负控制证明该门现在真会判**：媒体行→`false`、官方行→`true`、漏 `board_id` 的行→`true`（复现 bug）。修复后线上实测 `总162 | 官方37 | 媒体125`、`safe_to_flip` 随真实 A0 数变化。
