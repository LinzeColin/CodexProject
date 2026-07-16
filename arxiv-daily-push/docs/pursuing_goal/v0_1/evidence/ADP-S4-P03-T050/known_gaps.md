# Known gaps · ADP-S4-P03-T050（分批回填 31 省级行政区, SHADOW）

目标：按 cohort 分批扩展省级政策/统计/专业主管部门数据；每批过后才进下批；失败省隔离不阻塞全局。诚实边界：

1. **本批实际覆盖 3 省 / 2 批**：用 T049 A1 family 从 dev-env 实抓——批 0（art-cms：江苏、山东，各 3 真实文档）+ 批 1（beijing-zhengce：北京 3 文档）= **9 真实 A1 文档**。**广东**（gd.gov.cn，从服务器环境 TLS/连接被挡）作为**失败省隔离演示**纳入批 0：真实抓不到 → 记入 isolated_failures、**不阻塞批 0**（江苏+山东过 → gate PASS → 进批 1）。「31 省级行政区」是全量范围；server-rendered 省（江苏/山东/北京）本批已回填，其余 JS 渲染/TLS 挡的省需 headless fetcher（承 T049 已知边界）分批接入。

2. **每批 max_docs=3（代表批）**：本 SHADOW 批每省抓最近 3 篇证明批处理/门/隔离/幂等机制；全量按 T041 planner 分片跨真实时间累计。文档经 T049 normalize（内容寻址 canonical_id `ttl:` + A1 + 正确文档日期[非 Maketime 渲染时间戳] + 月份）。

3. **批门语义**：批门 = 该批 ≥1 省产出 ≥1 合格 A1 文档（canonical_id+A1+month）才算过；过了才进下批。**负控制证明真门**：整批失败（空 fetcher → 0 文档）→ halted_at=0、下批不跑。失败省隔离 ≠ 阻塞：隔离省记录但不拉低批门。

4. **dev-env 实抓，生产未触**：LiveFetcher 走开发环境（浏览器 UA + 宽松 TLS 以在服务器环境可达；非生产安全姿态，仅 dev 可达性）。非 worker → 0 云成本、DIR-007 不受影响、live build 仍 b189d3cc0703（==T040）、六主题/MVP 不变。SHADOW。

5. **coverage/cost/health 报告**：coverage_report(省×月网格 + 门 + 隔离)、cost_report(0 云)、health_report(每省可达/解析)。省级全域完整度与 as-of 随 T056 底座 + 更多批次累计。
