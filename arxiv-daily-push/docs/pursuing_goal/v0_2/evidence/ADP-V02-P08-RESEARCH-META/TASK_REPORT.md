# ADP V0.2 生产集成 · P08 / T063 — 研究元数据增强（PRODUCTION DEPLOY）

（本文件是补写的：P08 落地时漏了 TASK_REPORT.md —— P09 做证据包完整性审计时发现的。
 内容与 `known_gaps.md` / `cost_value.json` 一致，不新增任何未经验证的说法。）

## 交付
board1/board2 的论文条目获得 OpenAlex 研究元数据：**预印本/期刊、发表载体、被引次数、开放获取**。
此前 board1 的 302 篇 arXiv/bioRxiv/medRxiv 预印本与 board2 的期刊条目在页面上**无法区分**。

## T063 的两条验收
1. **预印本/期刊不混淆** ✅ `type=='preprint' || source.type=='repository'`。
   **必须是「或」不是「且」**：实测 eLife 是 preprint+**journal**（Reviewed Preprint 模式）。
2. **增强失败不阻塞原始论文** ✅ —— 部署时**在生产被真实执行**：cron 未跑、`cn_item_meta` 尚不存在，
   每次页面加载的 `attachMeta` 都真撞 D1 `no such table`，而所有路由仍 **200** 且渲染真实内容。

## 绝不声称「研究论文」
实测：Nature 新闻（`10.1038/d41586-*`）与 PNAS「In This Issue」（`10.1073/iti*`）在 OpenAlex 里
同样是 `type=article` / `is_paratext=false` / `venue=Nature|PNAS`，与真论文**完全无法区分**。
故只**逐字转述** OpenAlex 的字段。

## 独立对抗复核：6 轮
第 1 轮抓到 **6 条真实代码缺陷**（全部属实）。**第 2/3/4/5 轮 BLOCK 全部是证据造假**：
把参数错误当「承重」、贴了别条查询的 COVERING 计划、把「我测不出来」写成「不可能测出来」、
写入上界差 8 倍且与同文件自相矛盾、把自己的取值说成 API 强制上限（且该假话写进了发货代码注释）。
第 6 轮 **CONFIRMED_SOUND**，并用密码学方式确认唯一代码增量就是那条注释。**未自签。**

**每一次，证伪材料都已经在我自己的包里或一条命令之外。** 详见 `known_gaps.md` §9。

## DIR-007
外部子请求 20/50 → **21/50**；D1 内部操作最坏 **404/1000**（★上界是候选数不是 DOI 数★）；
读取约 600 行/晚。12 条负控全部承重。

release_mode: **PRODUCTION**。未自签。
Ends IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION.
