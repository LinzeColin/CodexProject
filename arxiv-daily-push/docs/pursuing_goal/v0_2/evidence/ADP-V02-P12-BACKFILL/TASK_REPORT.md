# ADP-V02-P12 — arXiv 历史回填（填覆盖债务）

状态: **CONFIRMED_SOUND**（独立对抗复核 2 轮：R1 BLOCK 属实且致命，R2 CONFIRMED_SOUND；实施者未自签）
release_mode: **PRODUCTION** — `dc91b5b221d0` → `e8491f75970f`（Version f9b79493-68ca-4b61-943e-2823610d3d36）

## 为什么
`/system` 覆盖网格实测 **时间覆盖率 1.5%**（69/4699 格，4630 格从未回填）。这是 P09 已量出的、
通往 goal「全面」的真实距离——不是来源不存在，是**我们从没抓过那些月份**（arXiv 自 1991、Nature 自 1869）。

## 做了什么
arXiv OAI-PMH 历史 datestamp 轴回填。每夜从 `cn_meta` 游标处取一页 `from/until` 历史窗口，
按论文真实 `<created>` 落进覆盖网格的正确格，游标**单调**前进。
★**独立 cron invocation**（`30 8 UTC`）★，独享子请求/CPU 预算，与当日流水线（`30 20 UTC`）完全隔离。

## 全部以实测为据（零假设，本轮零生产写入直到部署）
- arXiv 从边缘可达——生产 run_log 2026-07-17『arXiv 220』就是这个 OAI 端点抓的。
- OAI 历史 `from/until` 窗口返回记录——实测 http=200、420~1300 条。
- resumptionToken **无状态**、值里编码下一段 `from=YYYY-MM-DD` → 游标 = 持久化日期（token 当天过期，不依赖它）。

## ★设计关键：datestamp ≠ created★
OAI `from/until` 按 datestamp 过滤（≠ created）。一个 datestamp 窗口返回 `<created>` 跨多年的论文。
故回填**单调填真实空洞、不精确定向某一格**——条目按真实 created 落进正确的格，覆盖率照样爬（格有≥1条即翻绿）。设计已知，非缺陷。

## 复核（2 轮）
- **R1 BLOCK（属实且致命）**：回填原本链在 `runDaily` **同一个 invocation** 里。而 **D1 写算子请求**
  （Cloudflare 文档：『子请求 = 用 Fetch API 或对 R2/KV/D1 的请求』，免费档 50/invocation）。叠加会撞 50 上限
  → insert 抛 `Too many subrequests` → 被 try/catch + 外层 `.catch` 吞掉 → `setCursor` 永不执行
  → 游标永不推进 → 每夜补 0 条 → ★正是 P08 的病★。本地 node:sqlite 验证器**结构上看不见**（夹具无子请求上限）。
  R1 还抓到 `skip=` 被丢弃导致超密单日游标卡死的潜在 bug。
- **R1 修法**：★不靠赢下文档歧义（文档确实说不清 D1 算 50 还是单列 1000），靠让它无关★——
  把回填移到**独立 cron invocation**，两种读法都安全。`skip=` 卡死加 forward-progress 守卫。
- **R2 CONFIRMED_SOUND**：复核独立复验多 cron 路由（字节一致）、隔离后 ~21 子请求两种读法都安全、
  回填不依赖 `runDaily` 的 invocation 内状态（`source_id` 无 FK、独立 cn_meta 键、`_rawWrites` 只在 R2 双写路径）、
  两个守卫都 sabotage 承重。未自签。

## 负控 / 验证
`test-results/backfill_verify.mjs`：真 node:sqlite + 真 schema + mock OAI，**直接抽取 `//@P12-CORE` 测发货代码本体**。
**24 断言全绿**。承重由 sabotage 证明（见 `backfill_tests.txt`）：J1 防卡死、C2 单调、NC-D 落格。

## 已知残余（如实记）
- ★首夜 CPU/时长未实测★：保守 PAGES=1；一次超时**自愈**（独立 invocation + 幂等）。读 `/api/backfill` 的 `last_run.ms` 后再调。
- 超密单日（≥1300 条）丢尾部——守卫的代价，该格仍覆盖；复核实测峰值 ~627，极端边缘。
- 覆盖率爬升是**数月 cron**，任何 session 都填不完——物理，不是未完成。
- 游标方向从 2016 向今（OAI 原生方向）；近端已由当日 cron 覆盖。可逆，属 Owner。

## 上线验证（机制已 live）
`/build.json = e8491f75970f`；6 路由 200；`/api/backfill` 就绪（`cursor:null` 待首夜）；两 cron 已注册。
★首夜回填证据时间延迟到下一个 `30 8 UTC` cron★，读 `/api/backfill` 即得。

IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION（已完成：CONFIRMED_SOUND；已部署）
