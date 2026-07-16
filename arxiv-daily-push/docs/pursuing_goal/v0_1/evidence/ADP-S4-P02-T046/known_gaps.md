# Known gaps · ADP-S4-P02-T046

- **SHADOW，代表性 Wave-1 批次（任务边界，非缺陷）**：本次回填是**真实但代表性**的 Wave-1 批次——从 gov.cn xxgk 列表实抓 **7 篇真实 A0 政策原文跨 6 个月（2019-2022）**（列表当前仅暴露这些 content URL）。**字面 2016+ 全量月份覆盖**随适配器接 worker cron + 真实时间累计（SHADOW，同 T023/T039 shadow 需跨日历时间）。2016-2018 更早文档需更深列表分页/zhengceku 入口，属后续 wave。
- **走开发环境，非 worker（有意）**：Wave-1 从**开发环境** urllib 实抓（~8 子请求），**生产 worker/cron 未触**→ 0 云成本、DIR-007 不受影响、**实时无回归**（live build 仍 T040 b189d3cc0703、六主题 6/6）。真正把回填接进 worker cron（跑在 T042 backfill 车道 + DIR-007 每 run 上限）是后续接线。
- **raw/version 未落生产 R2/D1**：回填的 raw_key/version 链在**隔离处理**（幂等验证），未写生产 R2/D1（同 SHADOW 纪律）；真实落库随 worker 接线 + 内容寻址幂等（T021/T022/T024）。
- **附件数少**：本批 7 文档共 1 附件（多数政策页附件在正文链接，解析器抓 pdf/doc/wps/xls）；真实附件覆盖随更多文档回填提升。
- **月份覆盖 6 个月**：代表性；gap detector（T043）会把未回填月标 not_backfilled，随 Wave 推进转 covered/no_publications。
