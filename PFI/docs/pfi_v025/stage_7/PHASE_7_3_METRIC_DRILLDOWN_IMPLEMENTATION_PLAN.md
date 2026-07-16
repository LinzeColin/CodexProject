# v0.2.5 Stage 7 Phase 7.3：指标、参数与关联下钻

## 执行合同

- 唯一范围：`S7-P3-T1..T4`。
- 唯一 Acceptance：`ACC-PFI-V025-S7-P73-METRIC-DRILLDOWN`（项目治理分配；源 Roadmap/Task Pack 未提供 Phase 级 ACC-*）。
- 目标：把参数中心、Interconnection Map 与指标 lineage 作为正式 Shell 二级页接入；每个指标明确数据范围、公式/参数/数据/read-model hash、来源、经济事件 lineage 与阻断原因。
- 非范围：Stage 7 独立整阶段审查、Stage 8、GitHub push、PFI.app install、production/final human acceptance。

## 实现

`metric_lineage_drilldown.py` 只读组合参数注册表、公式注册表、Stage 3 真实来源 reconciliation、Stage 4 统一 read model 与 Stage 5 私有 runtime surface。Runtime API 暴露 `/api/lineage`；正式 Shell 新增 `/settings/parameters`、`/data/interconnection`、`/reports/metric-drilldown` 三条可深链路由，不使用 sidecar HTML。

参数中心按 15 个中文域展示 96 个参数和 20 个公式，并显示参数/公式 registry hash。Interconnection Map 以 7 个可点击节点、6 条描述性边展示真实来源记录、待复核、标准化交易、关联分组、经济事件和指标 lineage；聚合计数为 8,815 source records、6,879 complete lineage、1,936 review queue、0 silent drop。

指标下钻覆盖 11 个指标。ready 指标来自当前 runtime，并显示数据范围与四类 hash；not-ready 指标保持 `value=null` 并显示中文阻断原因，不以 `0` 冒充结果。持久 evidence 只保存 aggregate/hash/status，不保存财务值或私有标识。

## 验证结果

- 聚焦 Phase 7.3：`5 passed`；release identity、Stage 6 active-route compatibility、Stage 7 Phase 7.1/7.2/7.3 组合回归：`44 passed`。
- Node identity/cache/Phase 7.3：`29 passed`；相关 JavaScript `node --check` 通过。
- 正式 Shell cached Playwright/local Chrome：`21/21`；深链刷新、参数中心、可点击互联图、ready/blocked 指标与 fail-closed API 均通过。
- console/page/HTTP/external-network errors=0；截图已纯工具目视检查。
- trace 在写盘后重写清洗：472 个 JSON value 字段、2 个绝对路径和 3 个 CNY 文本被替换；复扫绝对路径与 numeric value 命中均为 0。

## 风险、回滚与停止条件

风险集中在旁路页面、历史/当前事实混用、read-model 多次计入同一经济事件、not-ready 假零、query 深链丢失与 trace 捕获私有值。回滚方式是 revert 本 Phase 单一提交；功能完全只读，不执行数据库 migration，不改 canonical 财务源。任何来源/hash/事件 lineage 缺失、非 ready 值非 null、证据含私有值、使用 Finder/外网、或提前进入整阶段审查都必须停止。

## 当前结论

`ACC-PFI-V025-S7-P73-METRIC-DRILLDOWN` 为 `candidate_pass`。v0.2.5 进度 `96/156 = 61.54%`；Stage 7 phase tasks 为 `12/12 = 100% candidate_complete`，但 Stage 7 仍 `in_progress`，独立 whole-stage review 与 human acceptance 均 `not_started`。
