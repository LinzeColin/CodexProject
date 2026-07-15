# J4 · 板块二～五上线登记（Owner 指令，2026-07-15）

## 指令与口径

Owner 原话：「我其余的四个板块也需要上线，并且能支持看到每个板块的具体数据源信息源网站平台等」。

任务包 J4 原定每板块走「提案 → 接入 → 两周影子 → Owner 确认 → 上板」；本指令即 Owner 确认，
影子等待期按既定修订口径（不因等待时间延迟交付）压缩。**边界保持诚实**：

- 板块二～四为**雷达浏览流**——真实抓取、雷达可见、来源健康纳管；**不进入每日精选候选池**。
  池整合与多样性上限 10→17 是任务包明文的独立提案（提案→30 天回放→应用→回执），未启动。
- bioRxiv 上板仍是雷达页 Owner 专属按钮（R5 流程不变）。
- 板块三/四的专属评分维度仍保留在阈值注册表扩展区，未激活。

## 板块与数据源（唯一真相：config/boards_v0_3.yaml，PARAM-ADP-1123）

| 板块 | 状态 | 数据源（平台） |
|---|---|---|
| 一 · 研究前沿 | 精选闭环 | arXiv 官方 API；bioRxiv 官方 API（影子） |
| 二 · 顶级期刊 | 浏览流 | Nature / Science / Cell 官方 RSS |
| 三 · 中国政策法规 | 浏览流 | Google News RSS 聚合（gov.cn 无官方 RSS）；RSSHub 公共实例路由保留（当前限流，如实降级，自托管后恢复） |
| 四 · 美国科技金融 | 浏览流 | 美联储 / SEC 官方新闻稿 RSS |
| 五 · 跨板块总览 | 聚合 | 无独立来源，自动聚合一～四 |

雷达页每板块展示：来源名 / 平台 / 网站 / 订阅方式 / 官方或聚合 / 健康（连败计数）/ 累计条数 / 最近抓取。

## 机制

- `adp.boards`：自带超时下载 → feedparser 解析 → `board_items` 表（幂等：同源同链接一条，
  外部链接只收 http/https 防 javascript: 注入，未来日期丢弃）；逐源独立成败，网络 I/O 不与写库交叠；
  `record_source_health` 连续 3 次失败自动停用并**跳过后续抓取**（来源-002 继承，kill switch 真生效）。
- 每日 `adp run` 内抓取（失败只降级记 manifest，永不阻塞闭环；已停用源为稳态跳过不再拖降级）。
- 真实抓取（2026-07-15）：6/7 源成功、`board_items` 累计入库 138 条（重复运行幂等 new=0）；
  RSSHub 公共实例路由 403 连续失败已自动停用。报表：`data/boards_fetch_report.json`。

## 证据

- 代码 `src/adp/boards.py` · 注册表 `config/boards_v0_3.yaml` · 测试 `tests/test_adp_boards.py`（4 条保护测试）
- 回执 `data/config_changes.jsonl`（domain=boards.live_feed）
- 雷达页实测（本机与 adp.linzezhang.com 直连均 200，数据源明细与真实条目可见）
