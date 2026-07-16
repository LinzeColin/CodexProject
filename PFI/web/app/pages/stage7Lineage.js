(function attachPFIV025Stage7Lineage(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.PFI_V025_STAGE7_LINEAGE = api;
})(typeof window !== "undefined" ? window : globalThis, function buildPFIV025Stage7Lineage() {
  const pageSpecs = Object.freeze([
    Object.freeze({
      workspace: "sync",
      primaryRouteAlias: "/data",
      primaryLabel: "数据源与上传",
      routeAlias: "/data/interconnection",
      pageLabel: "Interconnection Map",
      title: "数据源与上传 · Interconnection Map",
      breadcrumb: Object.freeze(["数据源与上传", "Interconnection Map"]),
      jobToBeDone: "从真实来源记录逐层检查标准化、关联分组、经济事件、账本事件与指标关系。",
      layoutKind: "interconnection-map",
      primaryObject: "真实事件关联图",
      dataObject: "聚合事件 lineage",
      dataSource: "本机只读 Git source snapshot / runtime lineage API",
      primaryAction: "检查关联节点",
      stateKey: "sync:interconnection",
      pageKind: "interconnection",
    }),
    Object.freeze({
      workspace: "insights",
      primaryRouteAlias: "/reports",
      primaryLabel: "报告与洞察",
      routeAlias: "/reports/metric-drilldown",
      pageLabel: "指标下钻",
      title: "报告与洞察 · 指标下钻",
      breadcrumb: Object.freeze(["报告与洞察", "指标下钻"]),
      jobToBeDone: "核对指标的数据范围、公式、参数、数据/read-model hash、来源、事件与阻断。",
      layoutKind: "metric-drilldown",
      primaryObject: "指标 lineage",
      dataObject: "当前 metric state",
      dataSource: "本机 runtime read model / formula registry / event lineage",
      primaryAction: "选择指标下钻",
      stateKey: "insights:metric-drilldown",
      pageKind: "metric",
    }),
    Object.freeze({
      workspace: "settings",
      primaryRouteAlias: "/settings",
      primaryLabel: "设置",
      routeAlias: "/settings/parameters",
      pageLabel: "参数中心",
      title: "设置 · 参数中心",
      breadcrumb: Object.freeze(["设置", "参数中心"]),
      jobToBeDone: "按中文业务域查看当前参数值、作用、影响范围、可修改边界与公式版本。",
      layoutKind: "parameter-center",
      primaryObject: "参数与公式注册表",
      dataObject: "canonical 参数/公式配置",
      dataSource: "PFI canonical parameter and formula registries",
      primaryAction: "检查参数域",
      stateKey: "settings:parameters",
      pageKind: "parameters",
    }),
  ]);

  const pages = Object.freeze(pageSpecs.map((page) => Object.freeze({
    ...page,
    structuralSignature: `${page.layoutKind}:${page.pageKind}`,
    states: Object.freeze({
      loading: `正在读取${page.dataObject}，请稍候。`,
      empty: `${page.dataObject}尚未加载；页面保持阻断且不补造结果。`,
      error: `无法读取${page.dataObject}；请检查本机服务、来源和 hash 状态。`,
    }),
    focusTarget: "page_heading",
    scrollPolicy: "restore_per_canonical_route",
    noJsFallback: Object.freeze({ routeAlias: page.routeAlias, title: page.pageLabel, task: page.jobToBeDone }),
    phase73LineagePage: true,
  })));
  const pageGroups = Object.freeze({
    sync: Object.freeze([{ title: "Interconnection Map", routeAlias: "/data/interconnection" }]),
    insights: Object.freeze([{ title: "指标下钻", routeAlias: "/reports/metric-drilldown" }]),
    settings: Object.freeze([{ title: "参数中心", routeAlias: "/settings/parameters" }]),
  });
  const pageByRoute = Object.freeze(Object.fromEntries(pages.map((page) => [page.routeAlias, page])));
  const pageContracts = Object.freeze({
    schema: "PFIV025Stage7Phase73PageContractsV1",
    version: "v0.2.5",
    stage: 7,
    phase: "7.3",
    phaseId: "V025-S7-P7.3",
    acceptanceId: "ACC-PFI-V025-S7-P73-METRIC-DRILLDOWN",
    taskIds: Object.freeze(["S7-P3-T1", "S7-P3-T2", "S7-P3-T3", "S7-P3-T4"]),
    pages,
    pageGroups,
    pageByRoute,
    formalRouteCount: pages.length,
    sidecarHtmlUsed: false,
    wholeStageReviewStarted: false,
  });

  function buildParameterCenterViewModel(payload = {}, selectedDomainId = "") {
    const domains = Array.isArray(payload.domains) ? payload.domains : [];
    const selected = domains.find((item) => item.domain_id === selectedDomainId)
      || domains.find((item) => Number(item.entry_count || 0) > 0)
      || domains[0]
      || null;
    return Object.freeze({
      status: payload.status || "not_loaded",
      parameterHash: payload.parameter_hash || null,
      formulaRegistryHash: payload.formula_registry_hash || null,
      summaryZh: `${Number(payload.domain_count || 0)} 个参数域 · ${Number(payload.parameter_count || 0)} 项参数 · ${Number(payload.formula_count || 0)} 条公式`,
      consistencyZh: Number(payload.consistency_conflict_count || 0) === 0
        ? "参数与公式载体一致"
        : `${Number(payload.consistency_conflict_count || 0)} 项配置冲突，当前保持阻断`,
      domains: Object.freeze(domains.map((item) => Object.freeze({ ...item }))),
      selectedDomain: selected ? Object.freeze({ ...selected }) : null,
      formulas: Object.freeze((Array.isArray(payload.formulas) ? payload.formulas : []).map((item) => Object.freeze({ ...item }))),
      writeEnabled: payload.write_enabled === true,
    });
  }

  function buildInterconnectionMapViewModel(payload = {}, selectedNodeId = "") {
    const nodes = Array.isArray(payload.nodes) ? payload.nodes : [];
    const selected = nodes.find((item) => item.node_id === selectedNodeId) || nodes[0] || null;
    const connectedEdges = selected
      ? (Array.isArray(payload.edges) ? payload.edges : []).filter((edge) => edge.from === selected.node_id || edge.to === selected.node_id)
      : [];
    return Object.freeze({
      status: payload.status || "not_loaded",
      dataHash: payload.data_hash || null,
      readModelHash: payload.read_model_hash || null,
      lineageCompleteCount: payload.lineage_complete_count,
      lineageMissingCount: payload.lineage_missing_count,
      blockingReasonZh: payload.blocking_reason_zh || null,
      nodes: Object.freeze(nodes.map((item) => Object.freeze({ ...item }))),
      edges: Object.freeze((Array.isArray(payload.edges) ? payload.edges : []).map((item) => Object.freeze({ ...item }))),
      selectedNode: selected ? Object.freeze({ ...selected }) : null,
      selectedEdges: Object.freeze(connectedEdges.map((item) => Object.freeze({ ...item }))),
      eventTypes: Object.freeze((Array.isArray(payload.event_types) ? payload.event_types : []).map((item) => Object.freeze({ ...item }))),
    });
  }

  function buildMetricDrilldownViewModel(payload = {}, selectedMetricId = "") {
    const metrics = Array.isArray(payload.metrics) ? payload.metrics : [];
    const selected = metrics.find((item) => item.metric_id === selectedMetricId) || metrics[0] || null;
    const ready = selected && ["ready", "confirmed_zero"].includes(String(selected.status || ""));
    return Object.freeze({
      status: payload.status || "not_loaded",
      metricCount: Number(payload.metric_count || 0),
      nonReadyFalseZeroCount: Number(payload.non_ready_false_zero_count || 0),
      metrics: Object.freeze(metrics.map((item) => Object.freeze({ ...item }))),
      selectedMetric: selected ? Object.freeze({ ...selected }) : null,
      selectedValueZh: !selected
        ? "未加载"
        : ready && selected.value !== null && selected.value !== undefined
          ? `${selected.currency || ""} ${Number(selected.value).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`.trim()
          : "指标阻断，不显示财务零值",
    });
  }

  return Object.freeze({
    schema: "PFIV025Stage7Phase73FrontendV1",
    pageContracts,
    pages,
    pageGroups,
    pageByRoute,
    buildParameterCenterViewModel,
    buildInterconnectionMapViewModel,
    buildMetricDrilldownViewModel,
  });
});
