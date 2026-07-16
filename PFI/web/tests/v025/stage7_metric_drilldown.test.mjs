import assert from "node:assert/strict";
import { createRequire } from "node:module";


const require = createRequire(import.meta.url);
const lineage = require("../../app/pages/stage7Lineage.js");
const routes = require("../../app/routes.js");


assert.equal(lineage.pageContracts.phaseId, "V025-S7-P7.3");
assert.equal(lineage.pageContracts.acceptanceId, "ACC-PFI-V025-S7-P73-METRIC-DRILLDOWN");
assert.equal(lineage.pages.length, 3);
assert.deepEqual(lineage.pages.map((page) => page.routeAlias), [
  "/data/interconnection",
  "/reports/metric-drilldown",
  "/settings/parameters",
]);
assert.equal(lineage.pageContracts.sidecarHtmlUsed, false);
assert.equal(routes.phase62RouteRegistry.canonicalSecondaryRoutes.length, 45);
assert.equal(routes.phase73RouteRegistry.canonicalSecondaryRoutes.length, 3);
assert.equal(routes.canonicalSecondaryRoutes.length, 48);

for (const [routeAlias, workspace] of [
  ["/settings/parameters?domain=currency", "settings"],
  ["/data/interconnection?node=economic_events", "sync"],
  ["/reports/metric-drilldown?metric=net_worth_cny", "insights"],
]) {
  const resolved = routes.resolveRouteAlias(routeAlias);
  assert.equal(resolved.status, "resolved");
  assert.equal(resolved.routeType, "secondary");
  assert.equal(resolved.routeAlias, routeAlias);
  assert.equal(resolved.workspace, workspace);
}

const parameterView = lineage.buildParameterCenterViewModel({
  status: "ready",
  domain_count: 2,
  parameter_count: 2,
  formula_count: 1,
  parameter_hash: `sha256:${"a".repeat(64)}`,
  formula_registry_hash: `sha256:${"b".repeat(64)}`,
  consistency_conflict_count: 0,
  write_enabled: false,
  domains: [
    { domain_id: "currency", label_zh: "货币", entry_count: 1, entries: [{ parameter_id: "base", label_zh: "主货币", value: "CNY" }] },
    { domain_id: "fx", label_zh: "汇率", entry_count: 1, entries: [{ parameter_id: "pair", label_zh: "汇率方向", value: "AUD/CNY" }] },
  ],
  formulas: [{ formula_id: "FORM-PFI-002", label_zh: "FX 有效业务日" }],
}, "fx");
assert.equal(parameterView.selectedDomain.label_zh, "汇率");
assert.equal(parameterView.writeEnabled, false);

const mapView = lineage.buildInterconnectionMapViewModel({
  status: "ready",
  nodes: [
    { node_id: "source", label_zh: "真实来源", count: 10 },
    { node_id: "events", label_zh: "经济事件", count: 8 },
  ],
  edges: [{ from: "source", to: "events", label_zh: "确定性关联" }],
  event_types: [],
}, "events");
assert.equal(mapView.selectedNode.node_id, "events");
assert.equal(mapView.selectedEdges.length, 1);

const metricView = lineage.buildMetricDrilldownViewModel({
  status: "ready",
  metric_count: 2,
  non_ready_false_zero_count: 0,
  metrics: [
    { metric_id: "blocked", label_zh: "阻断指标", status: "source_missing", value: null, currency: "CNY" },
    { metric_id: "ready", label_zh: "真实指标", status: "ready", value: "12.50", currency: "CNY" },
  ],
}, "blocked");
assert.equal(metricView.selectedValueZh, "指标阻断，不显示财务零值");
assert.equal(lineage.buildMetricDrilldownViewModel({
  status: "ready",
  metric_count: 1,
  metrics: [{ metric_id: "ready", label_zh: "真实指标", status: "ready", value: "12.50", currency: "CNY" }],
}, "ready").selectedValueZh, "CNY 12.50");

console.log("stage7 metric drilldown frontend contract: pass");
