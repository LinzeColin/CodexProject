(function attachPFIV024Stage3Navigation(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V024_STAGE3_NAVIGATION = api;
    root.PFI_V024_STAGE3_NAV = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIV024Stage3Navigation() {
  const officialPrimaryEntries = Object.freeze([
    Object.freeze({ index: 1, label: "首页总览", workspace: "home", routeAlias: "/home", icon: "⌂" }),
    Object.freeze({ index: 2, label: "账户与资产", workspace: "accounts", routeAlias: "/accounts", icon: "◫" }),
    Object.freeze({ index: 3, label: "账本流水", workspace: "ledger", routeAlias: "/ledger", icon: "≋" }),
    Object.freeze({ index: 4, label: "投资管理", workspace: "investment", routeAlias: "/investment", icon: "↗" }),
    Object.freeze({ index: 5, label: "消费管理", workspace: "consumption", routeAlias: "/consumption", icon: "◌" }),
    Object.freeze({ index: 6, label: "数据源与上传", workspace: "sync", routeAlias: "/sources-upload", icon: "⇄" }),
    Object.freeze({ index: 7, label: "建议与复盘", workspace: "recommendations", routeAlias: "/review", icon: "✦" }),
    Object.freeze({ index: 8, label: "报告与洞察", workspace: "insights", routeAlias: "/reports", icon: "▣" }),
    Object.freeze({ index: 9, label: "市场与研究", workspace: "market_research", routeAlias: "/market-research", icon: "⌁" }),
    Object.freeze({ index: 10, label: "设置", workspace: "settings", routeAlias: "/settings", icon: "⚙" }),
  ]);

  const legacyAliasEntries = Object.freeze([
    Object.freeze({
      taskId: "T3.1.2",
      label: "首页",
      targetWorkspace: "home",
      routeAlias: "/home/today",
      resolvedRouteAlias: "/home",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
    Object.freeze({
      taskId: "T3.1.2",
      label: "市场",
      targetWorkspace: "market_research",
      routeAlias: "/market/watch",
      resolvedRouteAlias: "/market-research?tab=market",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
    Object.freeze({
      taskId: "T3.1.2",
      label: "研究",
      targetWorkspace: "market_research",
      routeAlias: "/market/research",
      resolvedRouteAlias: "/market-research?tab=research",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
    Object.freeze({
      taskId: "T3.1.2",
      label: "持仓",
      targetWorkspace: "investment",
      routeAlias: "/investment/holdings",
      resolvedRouteAlias: "/investment?tab=holdings",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
    Object.freeze({
      taskId: "T3.1.2",
      label: "策略实验室",
      targetWorkspace: "market_research",
      routeAlias: "/market/lab",
      resolvedRouteAlias: "/market-research/strategy-lab",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
    Object.freeze({
      taskId: "T3.1.2",
      label: "数据与系统",
      targetWorkspace: "settings",
      routeAlias: "/settings/data",
      resolvedRouteAlias: "/settings?tab=data-system",
      aliasClass: "secondary_or_command_alias",
      primaryEntryAllowed: false,
    }),
  ]);

  const legacyRouteAliasTargets = Object.freeze(Object.fromEntries(
    legacyAliasEntries.map((entry) => [entry.routeAlias, entry.resolvedRouteAlias])
  ));
  const primaryRouteAliases = Object.freeze(Object.fromEntries(
    officialPrimaryEntries.map((entry) => [entry.routeAlias, entry.workspace])
  ));
  const activeStateRules = Object.freeze({
    navIndexSequence: Object.freeze(officialPrimaryEntries.map((entry) => entry.index)),
    singleActivePrimaryEntry: true,
    desktopAndMobileActiveStateShareWorkspace: true,
    legacyAliasPrimaryEntryAllowed: false,
    legacyAliasResolvesBeforeActiveWorkspace: true,
  });

  function resolveLegacyRouteAlias(routeAlias) {
    const clean = String(routeAlias || "").trim();
    return legacyRouteAliasTargets[clean] || clean;
  }

  function activeWorkspaceFromRoute(routeAlias) {
    const resolved = resolveLegacyRouteAlias(routeAlias).split("?")[0];
    return primaryRouteAliases[resolved] || null;
  }

  return Object.freeze({
    schema: "PFIV024Stage3NavigationContractV1",
    version: "v0.2.4",
    sourcePackageVersion: "v0.2.3-repair",
    repairLabel: "PFI v0.2.3 Repair",
    stage: "Stage 3",
    phaseId: "3.1",
    phaseName: "导航合同",
    taskIds: Object.freeze(["T3.1.1", "T3.1.2", "T3.1.3", "T3.1.4"]),
    navigationContractVersion: "PFI-V024-STAGE3-PHASE31-NAVIGATION",
    officialPrimaryEntries,
    legacyAliasEntries,
    legacyRouteAliasTargets,
    primaryRouteAliases,
    legacyAliasLabels: Object.freeze(legacyAliasEntries.map((entry) => entry.label)),
    activeStateRules,
    resolveLegacyRouteAlias,
    activeWorkspaceFromRoute,
    phase31Complete: true,
    phase32Complete: false,
    phase33Complete: false,
    stage3Complete: false,
    browserHistoryValidationDone: false,
    githubMainUploadAllowed: false,
  });
});

(function attachPFIV025Stage6PageContracts(root, factory) {
  const v024Compatibility = typeof module !== "undefined" && module.exports
    ? module.exports
    : root?.PFI_V024_STAGE3_NAVIGATION || Object.freeze({});
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = Object.freeze({ ...v024Compatibility, v025PageContracts: api });
  }
  if (root) root.PFI_V025_STAGE6_PAGE_CONTRACTS = api;
})(typeof window !== "undefined" ? window : globalThis, function buildPFIV025Stage6PageContracts() {
  const groupSpecs = Object.freeze([
    Object.freeze({
      workspace: "home", primaryRouteAlias: "/overview", primaryLabel: "首页总览", pages: Object.freeze([
        ["status", "财务状态", "overview-status-command", "财务状态快照", "检查财务状态", "确认当前财务状态、数据新鲜度与阻断项。"],
        ["todo", "待办事项", "overview-priority-queue", "优先待办队列", "处理首页待办", "按影响与阻断程度处理财务工作待办。"],
        ["actions", "快捷操作", "overview-action-launcher", "可执行动作注册表", "执行快捷操作", "从已满足前置条件的动作中进入下一项工作。"],
        ["reports", "最近报告", "overview-report-timeline", "最近报告索引", "打开最近报告", "核对最近报告的数据范围、状态与证据。"],
      ]),
    }),
    Object.freeze({
      workspace: "accounts", primaryRouteAlias: "/accounts", primaryLabel: "账户与资产", pages: Object.freeze([
        ["overview", "账户地图", "accounts-source-map", "账户来源地图", "核对账户来源", "确认账户、来源、币种与更新时间的覆盖关系。"],
        ["list", "账户清单", "accounts-balance-table", "账户余额清单", "打开账户明细", "筛选账户并查看余额、来源和数据状态。"],
        ["trend", "资产趋势", "accounts-asset-timeseries", "资产趋势序列", "查看趋势缺口", "检查资产时间序列的覆盖范围与缺口。"],
        ["reconcile", "账户对账", "accounts-reconciliation-matrix", "账户对账差异", "处理对账差异", "比较平台快照与本机账本并处理差异。"],
      ]),
    }),
    Object.freeze({
      workspace: "ledger", primaryRouteAlias: "/ledger", primaryLabel: "账本流水", pages: Object.freeze([
        ["list", "流水列表", "ledger-evidence-table", "标准化流水记录", "打开流水证据", "逐笔查看流水、来源批次与证据链。"],
        ["filter", "筛选搜索", "ledger-query-builder", "流水筛选结果", "保存筛选条件", "组合条件定位需要核验的真实流水。"],
        ["review", "分类复核", "ledger-review-workbench", "低置信度复核队列", "保存分类复核", "复核低置信度分类并记录决策理由。"],
        ["export", "导出流水", "ledger-export-scope", "流水导出范围", "生成导出文件", "确认范围与格式后导出当前真实结果。"],
      ]),
    }),
    Object.freeze({
      workspace: "investment", primaryRouteAlias: "/investment", primaryLabel: "投资管理", pages: Object.freeze([
        ["overview", "投资总览", "investment-allocation-overview", "投资配置快照", "查看资产配置", "核对投资市值、现金仓位与配置集中度。"],
        ["holdings", "持仓", "investment-holdings-editor", "真实持仓快照", "编辑持仓快照", "查看或维护持仓，并保留持久化状态。"],
        ["trades", "交易记录", "investment-trade-ledger", "投资交易记录", "核对交易证据", "核对买卖、费用、税费与汇率证据。"],
        ["returns", "收益分析", "investment-attribution-analysis", "投资收益归因", "检查收益归因", "基于持仓与交易证据解释收益和风险。"],
      ]),
    }),
    Object.freeze({
      workspace: "consumption", primaryRouteAlias: "/consumption", primaryLabel: "消费管理", pages: Object.freeze([
        ["overview", "消费总览", "consumption-dual-metric-overview", "消费双口径汇总", "检查消费口径", "对照现金流与行为口径理解消费结构。"],
        ["category", "分类分析", "consumption-category-drilldown", "消费分类明细", "下钻消费分类", "从分类汇总下钻到真实流水与证据。"],
        ["budget", "预算", "consumption-budget-control", "预算执行状态", "维护预算边界", "比较预算与真实支出并处理超支项。"],
        ["subscription", "订阅", "consumption-subscription-register", "周期扣费清单", "复核订阅项目", "识别周期扣费并复核订阅状态。"],
        ["anomaly", "异常消费", "consumption-anomaly-review", "异常消费队列", "处理消费异常", "复核大额、重复或异常时段消费。"],
      ]),
    }),
    Object.freeze({
      workspace: "sync", primaryRouteAlias: "/data", primaryLabel: "数据源与上传", pages: Object.freeze([
        ["upload", "上传中心", "data-upload-dropzone", "待上传文件队列", "选择本机文件", "选择文件并在解析前确认格式与隐私边界。"],
        ["import", "导入中心", "data-import-pipeline", "导入批次状态", "启动受控导入", "查看批次解析、映射、失败和待复核状态。"],
        ["sources", "数据源管理", "data-source-registry", "数据源注册表", "维护数据源", "核对来源、账户映射、格式与更新时间。"],
        ["review", "待复核", "data-quality-review", "数据质量复核队列", "处理数据复核", "处理解析、映射与质量门禁产生的复核项。"],
        ["history", "导入历史", "data-import-timeline", "导入历史记录", "打开导入证据", "追踪导入批次、结果、版本与证据。"],
      ]),
    }),
    Object.freeze({
      workspace: "recommendations", primaryRouteAlias: "/review", primaryLabel: "建议与复盘", pages: Object.freeze([
        ["list", "建议列表", "review-evidence-inbox", "证据化建议队列", "整理建议优先级", "按证据、影响与可执行性整理建议。"],
        ["detail", "建议详情", "review-recommendation-case", "单项建议证据包", "复核建议详情", "核对建议依据、代价、失效条件与行动。"],
        ["decision", "决策记录", "review-decision-journal", "建议决策日志", "记录建议决策", "记录接受、暂缓或忽略建议的理由。"],
        ["history", "复盘记录", "review-outcome-timeline", "建议结果复盘", "打开复盘记录", "比较建议执行结果与原始预期并形成复盘。"],
      ]),
    }),
    Object.freeze({
      workspace: "insights", primaryRouteAlias: "/reports", primaryLabel: "报告与洞察", pages: Object.freeze([
        ["monthly", "月报", "reports-monthly-close", "月度报告草稿", "生成月报草稿", "在月度数据门禁通过后生成可追溯草稿。"],
        ["quarterly", "季报", "reports-quarter-comparison", "季度报告草稿", "生成季报草稿", "比较季度覆盖与变化并保留不可比项。"],
        ["yearly", "年报", "reports-year-close", "年度报告草稿", "生成年报草稿", "核对全年覆盖与关闭状态后形成年度草稿。"],
        ["custom", "自定义报告", "reports-scope-builder", "自定义报告查询", "配置报告范围", "组合数据域与筛选条件构建受控报告。"],
        ["export", "报告导出", "reports-export-gate", "报告导出清单", "导出报告文件", "在证据检查通过后选择格式与目标位置。"],
      ]),
    }),
    Object.freeze({
      workspace: "market_research", primaryRouteAlias: "/market-research", primaryLabel: "市场与研究", pages: Object.freeze([
        ["market", "市场观察", "research-market-watchlist", "市场观察清单", "打开观察清单", "组织指数、ETF、主题与自选观察对象。"],
        ["research", "研究笔记", "research-citation-notebook", "研究证据笔记", "整理研究笔记", "按主题整理研究证据、引用与反方条件。"],
        ["company", "公司研究", "research-company-dossier", "公司研究档案", "打开公司档案", "核对公司资料、关键假设、证据与风险。"],
        ["fund", "基金研究", "research-fund-exposure", "基金研究资料", "核对基金资料", "检查基金持仓、费用、风格与披露来源。"],
        ["strategy-lab", "策略实验室", "research-strategy-experiment", "策略实验定义", "进入策略实验", "配置研究实验并保留参数、结果与失效条件。"],
      ]),
    }),
    Object.freeze({
      workspace: "settings", primaryRouteAlias: "/settings", primaryLabel: "设置", pages: Object.freeze([
        ["account", "账户偏好", "settings-account-preferences", "账户显示偏好", "保存账户偏好", "管理显示币种、默认账户与界面偏好。"],
        ["data-system", "数据与系统", "settings-system-health", "数据系统状态", "检查数据系统", "核对本机数据路径、服务与质量状态。"],
        ["privacy", "隐私与本地存储", "settings-privacy-boundary", "本地隐私边界", "检查隐私边界", "确认本地存储、忽略规则与敏感数据边界。"],
        ["feedback", "反馈偏好", "settings-feedback-controls", "交互反馈偏好", "调整反馈偏好", "管理视觉、声音、触感与无障碍反馈。"],
        ["backup", "备份恢复", "settings-backup-recovery", "备份恢复检查点", "检查备份恢复", "核对备份完整性、恢复点与操作风险。"],
      ]),
    }),
  ]);

  const historicalPrimaryByWorkspace = Object.freeze({ home: "/home", sync: "/sources-upload" });
  const pages = Object.freeze(groupSpecs.flatMap((group) => group.pages.map((spec) => {
    const [slug, pageLabel, layoutKind, dataObject, primaryAction, jobToBeDone] = spec;
    const routeAlias = `${group.primaryRouteAlias}/${slug}`;
    const historicalPrimary = historicalPrimaryByWorkspace[group.workspace] || group.primaryRouteAlias;
    return Object.freeze({
      workspace: group.workspace,
      primaryRouteAlias: group.primaryRouteAlias,
      primaryLabel: group.primaryLabel,
      routeAlias,
      legacyRouteAlias: `${historicalPrimary}?tab=${slug}`,
      pageLabel,
      title: `${group.primaryLabel} · ${pageLabel}`,
      breadcrumb: Object.freeze([group.primaryLabel, pageLabel]),
      jobToBeDone,
      layoutKind,
      structuralSignature: `${layoutKind}:${slug}`,
      primaryObject: pageLabel,
      dataObject,
      dataSource: `${dataObject} / 本机 read-model`,
      primaryAction,
      stateKey: `${group.workspace}:${slug}`,
      states: Object.freeze({
        loading: `正在读取${dataObject}，页面操作暂不可用。`,
        empty: `尚无可用的${dataObject}；保留页面结构并说明下一步。`,
        error: `无法读取${dataObject}；请检查本机来源、权限与证据状态。`,
      }),
      focusTarget: "page_heading",
      scrollPolicy: "restore_per_canonical_route",
      noJsFallback: Object.freeze({ routeAlias, title: pageLabel, task: jobToBeDone }),
    });
  })));
  const pageByRoute = Object.freeze(Object.fromEntries(pages.map((page) => [page.routeAlias, page])));
  const historicalRouteTargets = Object.freeze(Object.fromEntries(pages.map((page) => [page.legacyRouteAlias, page.routeAlias])));
  const pageGroups = Object.freeze(Object.fromEntries(groupSpecs.map((group) => [
    group.workspace,
    Object.freeze(pages.filter((page) => page.workspace === group.workspace).map((page) => Object.freeze({
      title: page.pageLabel,
      routeAlias: page.routeAlias,
    }))),
  ])));

  return Object.freeze({
    schema: "PFIV025Stage6Phase62PageContractsV1",
    version: "v0.2.5",
    stage: "Stage 6",
    phaseId: "6.2",
    phaseName: "独立二级页面合同",
    acceptanceId: "ACC-PFI-V025-S6-P62-PAGE-CONTRACTS",
    taskIds: Object.freeze(["S6-P2-T1", "S6-P2-T2", "S6-P2-T3", "S6-P2-T4"]),
    pages,
    pageByRoute,
    pageGroups,
    historicalRouteTargets,
    totalPageCount: pages.length,
    phase62CandidateComplete: true,
    phase63Complete: false,
    stage6Complete: false,
  });
});
