# Known gaps · ADP-S4-P01-T043

- **NOT_DEPLOYED（任务边界，非缺陷）**：gap detector 在覆盖网格上运行，未接生产。`backfilled/failed` 月集当前为空 → 历史空月归 `not_backfilled`（pending，因真实回填未跑，正确）；接 T041/T042 真实回填状态后，已回填空月会正确归 `no_publications`、失败月归 `fetch_failed`。
- **源活跃窗由已入库条目推断**：`infer_source_windows` 用已入库条目的 [首月,末月] 作 active_from/active_to；真实源上线日期应以注册表 enabled_at（T012/T013）校准——否则某源在 active_from 前确有历史但被判 source_not_yet_active（保守，接线时用真实 enabled_at 修正）。
- **覆盖基于当前抓样**：真实覆盖网格随真实入库 + 2016+ 回填填充；本任务用 500 真实抓样演示 20 源 × 127 月的 detector 与 0 静默空洞纪律，非全量覆盖。
- **alert 为返回值非推送**：`alerts` 是返回的未解释单元列表；接生产告警（邮件/看板）属后续（T044 看板）。
- **月粒度**：网格月度（同 T041 分片）；稠密源可细化周/日。
