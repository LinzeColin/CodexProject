# 云端原生迁移（Owner 2026-07-15 指令：网页即主体，整套系统跑云端）

## 指令与背景

Owner 原话（要点）：
- 「我的 arxiv 应该是全部 arxiv，不是只有 cs stat」——arXiv 覆盖所有领域。
- 「把影子改为正常入库」——bioRxiv 由影子转正式入库。
- 「这个就是正常的网页系统，本机只是后台，网页才是主体……目前感觉网页只是镜子，主体在本机，目前是错误的」——
  否定「本机为主、云端做镜像」的旧架构；要求整套系统跑在云端，网页即主体，不依赖 Mac 开机。
- 「所有板块都要进每日精选」——板块二～五的条目都进入每日选择候选池（不再只是浏览流）。

Owner 选定实现路径：**零成本重建到 Cloudflare 免费平台**（Workers + D1 + Cron），我分阶段重写。

## 目标架构

一个 Worker（`adp-cloud`）+ 一个 D1，把五环节全部放到云端：
抓取（全 arXiv + bioRxiv + 全板块）→ 跨全部板块选择 → 确定性讲义 → 主动回忆 → FSRS 排程。
每日 cron 自动跑；页面直接读写 D1；回忆评分即时进 FSRS（无回传队列，云端即真相）。
本机 Python 系统降级为可选后台，不再是主体。

## 分阶段

| 阶段 | 内容 | 状态 |
|---|---|---|
| Stage 1 | D1 云端 schema（cn_*）+ 每日流水线 + today/queue/radar/system 基础页 | **已完成并实测** |
| Stage 2 | 六主题全 UI 移植（从 base.html）+ 修复板块三来源 + 每板轮转 + 字符集感知抓取 | **已完成并实测** |
| Stage 3 | 切 adp.linzezhang.com 到 adp-cloud、退役隧道/镜像、复审+治理+合入收尾 | **已完成并实测** |
| Stage 3+ | 商用级功能拓展（学习数据面板/引导复习会话/板块浏览/搜索/往期/学任意条目）+ 打磨（meta/favicon/安全头/404/aria） | **已完成并实测** |
| Stage 3++ | ChatGPT 深度追问按钮（今天/条目/复习/搜索）+ 本地无用信息清理（退役隧道/镜像残留） | **已完成并实测** |
| Stage 3+++ | 主题选择器自愈修复（无效/原型键存储值不再让 6 主题变空） | **已完成并实测** |

## 主题选择器自愈修复（2026-07-15 追加）

Owner 反馈「网页的 6 个主题没了 / 还是没有恢复」。浏览器内复现根因：六主题切换器读取 localStorage 的 `adp-theme` 后**未校验就直接应用**——若存的是旧版本/无效值，或是 `constructor`/`__proto__`/`toString` 这类 Object 原型键，则：
- `data-theme` 被设成无效值 → 没有匹配的 `[data-theme=...]` CSS → 页面退回默认 warm 配色；
- 原生 `<select>` 的 `selectedIndex = -1` → **切换框显示空白**。

从 Owner 视角就是「6 个主题全没了、我选的主题也没恢复」。修复（`deploy/cloudflare/worker_cloud.js`）：HEAD_INIT 与 THEME_JS 都改为用 `Object.prototype.hasOwnProperty.call(THEMES, s)`（isTheme() 助手）校验，非六主题一律回退 `warm`，且 applyTheme 会把纠正后的值写回 localStorage——**坏值首次加载即自愈**。站上实测：存 `aurora`、`constructor` 都自愈为 warm（切换框显示「暖纸学习」）、选「森林河流」跨页保持。注：测试时 in-app 预览浏览器缓存了旧页（需加 cache-buster）；线上 HTML 为 no-cache，手机正常刷新即可拿到修复。

## ChatGPT 深度追问 + 本地清理（2026-07-15 追加）

Owner 指令：删除本地无用信息；增加跳转 ChatGPT 的功能，让 ChatGPT 全网遍历、深度思考、深度搜索并给一些 surprise、详细专业全面深度讲解对应内容。

- **ChatGPT 深度追问按钮**：今天/条目详情/复习页每条都加「🔮 让 ChatGPT 全网深度追问」——把该条的标题/作者/类目/原文链接/摘要拼成中文提示词，经 `https://chatgpt.com/?hints=search&q=` 新标签跳转；提示词明确要求：先联网深度搜索并交叉验证、附可核查来源；再深度思考讲清真问题/核心方法/关键假设/创新点/局限争议；面向想彻底学懂的人做详细专业全面有深度的讲解、复杂处用类比；给一些意料之外的 surprise；结尾给「继续深入该读什么/做什么」清单。搜索页另加「对当前主题的深度检索」。渲染侧 href 经 `esc`（encodeURIComponent 后仅余字面 `&`→`&amp;`），无注入面。实测 adp.linzezhang.com 今天/条目/复习/搜索四处均已上线，提示词解码正确（worst-case URL ~6.2KB，浏览器/ChatGPT 均可承载）。
- **本地清理**：Stage 3 切换后，本机 com.linze.adp.web（uvicorn 8787）与 com.linze.adp.tunnel（cloudflared）隧道/镜像架构已无域名指向。卸载并删除两 LaunchAgent 的已安装副本、`~/.cloudflared/adp-tunnel-token`、`var/bin/cloudflared`（38MB）与死日志；仓库内 `deploy/cloudflare/launchd/` 模板保留（可一键重装），无任何被跟踪文件变更。删后 adp.linzezhang.com 仍全路由 200，证明本机残留确为无用。

## Stage 3 + 商用级拓展实测（2026-07-15）

- **切域名**：adp.linzezhang.com 的 custom_domain 从旧 adp-mirror 解绑、绑到 adp-cloud；实测该域名全路由 200（today/review/radar/system/history/search/board），页脚证明为纯云端系统。旧 adp-mirror worker 与本机隧道/网页 LaunchAgent 已无域名指向（休眠，Owner 可自行删除/停用）。
- **学习数据面板（vitals）**：连续天数、待复习、已掌握、学习中、回忆达标率——首页顶部卡片 + 「开始复习」CTA。
- **引导复习会话 /review**：取最到期一张卡 → 显示答案/讲义 → 四档评分 → 自动进入下一张；下方附完整复习队列。
- **板块浏览 /board/:id**：每板全部条目分页，每条可「学这个」加入复习。
- **搜索 /search?q=**：候选库标题/摘要 LIKE 搜索（实测 policy → 命中）。
- **往期精选 /history**：历次每日精选（含弃权）归档。
- **条目详情 /item/:id**：标题/作者/类目/摘要/讲义 + 加入复习 + 回忆评分。
- **学任意条目 POST /api/study/:id**：把任一条目建卡进复习队列（不再只有每日一篇）——实测 study → /review 立刻出现该到期卡。
- **打磨**：meta description/og、theme-color 随主题、emoji favicon（data URI）、安全头（CSP/nosniff/referrer-policy）、API no-store、404/错误页（主题化）、robots.txt、aria 标签、搜索框。
- **对抗复审加固**：href 只放行 http/https（`safeHref`，防外部源 javascript:/data: 链接）；内联脚本里的条目 id 用 `jsStr` 转义 `</`（防 `</script>` 提前闭合）；搜索 LIKE 先转义反斜杠本身再转义 %/_（`\` 是 ESCAPE 字符）。保留上限删除保护被复习/精选/讲义引用的条目（否则复习卡变孤儿、待复习计数虚高、详情页 404）；待复习计数只算 item 仍在的卡。streak 与「每日一评」防重改按用户本地日（UTC+8）分桶，不再因 UTC 跨日误清零。评分按钮加去抖（防双击重复提交）；/item /board 不存在返回真 404；favicon 直出 SVG；板块五计数=各板之和。/api/study、/api/run 与全站一致为无登录（Owner 指令），私有化仍可叠 Cloudflare Access。
- **治理计数漂移修复**（Stage 1 遗留、被本轮 unittest 抓到）：模型参数文件 active_parameter_count 1106→1107；追踪链页补第 443 行（J5）并同步计数（全量 worktree 根校验器 0 错误）。

## Stage 2 实测（2026-07-15）

- **六主题全 UI**：warm/minimal/fresh/techno/cosmos/forest 六组令牌 + 三种导航结构（侧栏/顶栏/悬浮坞，由 data-nav 驱动）+ 主题下拉（localStorage 记忆）全部移植进 worker_cloud.js，实测页面含全部六主题与三导航。
- **板块三修复**：Google News 从数据中心 IP 被拦，换为可从云端抓的中文媒体 RSS（人民网时政/财经、中国新闻网、新浪国内焦点）；实测四源 active、板块三 75 条真实政策/时政条目，中文无乱码（学习卡/刘国中调研/科技金融/国台办…）。
- **每板轮转**：从"按天轮转"改为"每板取最久未抓取的 4 个"，保证每个板块每次都有覆盖（此前板块三会因排在其它未抓源之后被饿死）。
- **字符集感知抓取**：按 XML 声明选 TextDecoder（gb2312/gbk→gb18030），防未来中文源乱码。
- **孤儿源清理**：seedSources 删除注册表已移除的旧源与其条目（换掉的 Google News 不再残留）。
- 四板块条目：board1 270 / board2 121 / board3 75 / board4 140。
- **对抗复审修复**：主题应用移到 `<head>` 首绘前（消除颜色/导航闪烁）；localStorage 读写加 try/catch（隐私模式不卡死）；`item.official` 决定证据权重（http/https 同等，板块三 http 源不再被打低分）；停用源 3 天后自动重试（板块三不会被临时封而永久变黑）；孤儿源清理保护被选择/复习引用的条目；悬浮坞不再遮挡页脚；深色主题原生下拉用暗色配色；顶栏导航居中。复审后重跑「正常」无降级。

## Stage 1 实测（adp-cloud.linzezhang35.workers.dev，2026-07-15）

- 抓取：arXiv 全领域 220（含 econ/stat/cs 等所有领域，OAI-PMH）、bioRxiv 30（正常入库）、板块 feed 130（轮转 12 个/次，免费档子请求预算内）。
- 选择：跨全部板块 217~379 候选选 1（8 特征加权、弃权线 59.6）；实测选中 econ 论文 "Costly Attention and Retirement"。
- 讲义：确定性八段模板。
- 回忆+FSRS：/api/grade 实测评「良好」→ 下次复习 2026-07-18（间隔 3 天，证据态"学习中"），直接写 D1。
- 五态运行日志入 cn_run_log。
- 已知降级：板块三 5 条 Google News 源被数据中心 IP 拦（429/403），健康页如实标 degraded/disabled；Stage 2 换源修复。

## 免费档工程约束（关键）

Cloudflare 免费档单次 Worker 调用最多约 50 个子请求（fetch 与每个 D1 调用都算）。对策：
- D1 写入全部走 `batch()`（一次 batch = 一个子请求），分块 80 条。
- 板块 feed 按天轮转抓取（每次 12 个，2~3 天覆盖一轮）；arXiv 单次上限 220、页封顶 2。
- 单源失败只降级、连续 3 次自动停用并跳过。

## 代码

- `deploy/cloudflare/worker_cloud.js` —— 云端原生 Worker（注册表/解析/抓取/选择/讲义/FSRS/UI/入口）。
- `deploy/cloudflare/wrangler_cloud.jsonc` —— 部署配置（复用 D1 `adp-mirror`，cron 30 20 * * *，workers.dev）。
- `deploy/cloudflare/schema_cloud.sql` —— D1 云端表（cn_sources/cn_items/cn_selections/cn_lessons/cn_reviews/cn_events/cn_run_log/cn_meta）。

旧镜像/隧道架构在 Stage 3 切换后退役；Stage 1/2 期间 adp.linzezhang.com 仍走旧 worker，互不影响。
