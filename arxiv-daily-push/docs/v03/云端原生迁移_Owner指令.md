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
| Stage 3 | 切 adp.linzezhang.com 到 adp-cloud、退役隧道/镜像、复审+治理+合入收尾 | 待做 |

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
