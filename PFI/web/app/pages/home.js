(function attachPFIStage5Home(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V023_STAGE5_HOME = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage5Home() {
  const VERSION = "v0.2.3";
  const STAGE = "Stage 5";
  const PHASE51_ID = "V023-S5-P5.1";
  const PHASE51_NAME = "首页信息架构";
  const PHASE52_ID = "V023-S5-P5.2";
  const PHASE52_NAME = "下一步动作";
  const PHASE53_ID = "V023-S5-P5.3";
  const PHASE53_NAME = "去 AI 痕迹";
  const STAGE62_ID = "V023-S6-P6.2";

  const DISPLAY_VALUE_STATUSES = Object.freeze(["ready", "confirmed_zero"]);
  const STATUS_COPY_ZH = Object.freeze({
    ready: "真实数据已加载",
    confirmed_zero: "真实数据确认数值为零",
    not_loaded: "未加载真实数据",
    not_mounted: "真实数据源未挂链",
    path_error: "数据路径不可用",
    permission_error: "无权限读取，请检查本机文件权限",
    parse_error: "解析失败，请检查文件、行或字段",
    outdated: "使用旧快照，请查看快照日期",
    filter_empty: "当前筛选无结果",
    calculation_error: "指标计算失败",
    review_required: "需要人工复核",
  });

  const HOME_SECTIONS = Object.freeze([
    Object.freeze({
      id: "financial_state",
      title: "财务状态摘要",
      question: "我现在有多少钱",
    }),
    Object.freeze({
      id: "money_location",
      title: "钱在哪里",
      question: "钱分布在哪些账户、现金和投资状态里",
    }),
    Object.freeze({
      id: "data_health",
      title: "数据健康",
      question: "哪些真实数据可用，哪些被阻断",
    }),
    Object.freeze({
      id: "recent_changes",
      title: "最近变化",
      question: "最近真实记录发生了什么",
    }),
  ]);

  const HOME_VISIBLE_SECTIONS_PHASE53 = Object.freeze([
    "financial_state",
    "data_health",
    "next_actions",
    "recent_changes",
    "report_entry",
  ]);

  const HOME_FORBIDDEN_ARTIFACTS_PHASE53 = Object.freeze([
    "Task Pack",
    "运行边界",
    "AI 控制台",
    "反馈控制台",
    "证据抽屉",
    "系统能力面板",
    "参数面板",
    "PFI 功能入口",
    "Stage",
    "Phase",
    "workflow",
    "runtime",
    "console",
    "evidence drawer",
  ]);

  const HOME_SURFACE_POLICY_PHASE53 = Object.freeze({
    home_visible_sections: HOME_VISIBLE_SECTIONS_PHASE53,
    settings_feedback_isolated: true,
    evidence_parameters_routed_out: true,
    no_developer_stage_terms_on_home: true,
    evidence_route: Object.freeze({
      targetWorkspace: "insights",
      routeAlias: "/reports?tab=monthly",
      label: "查看报告",
    }),
    parameter_route: Object.freeze({
      targetWorkspace: "settings",
      routeAlias: "/settings?tab=data-system",
      label: "打开设置",
    }),
  });

  const DEFAULT_METRICS = Object.freeze([
    metric("net_worth_cny", "净资产", "CNY"),
    metric("cash_balance_cny", "现金余额", "CNY"),
    metric("investment_market_value_cny", "投资市值", "CNY"),
    metric("month_spend_cny", "本月支出", "CNY"),
  ]);

  const STAGE62_HOME_METRICS = Object.freeze([
    "net_worth_cny",
    "cash_balance_cny",
    "investment_market_value_cny",
    "life_consumption_cny",
    "total_consumption_outflow_cny",
    "data_health",
  ]);

  function buildStage5Phase51Contract() {
    return Object.freeze({
      version: VERSION,
      stage: STAGE,
      phase_id: PHASE51_ID,
      phase_name: PHASE51_NAME,
      current_phase_only: true,
      max_one_phase_per_run: true,
      uses_stage2_data_state_machine: true,
      home_sections: HOME_SECTIONS.map((section) => section.id),
      allowed_files: Object.freeze([
        "PFI/web/app/pages/home.js",
        "PFI/web/app/components/*.js",
        "PFI/web/styles.css",
        "PFI/tests/test_v023_stage5_home_experience.py",
        "PFI/docs/pfi_v023/STAGE5_HOME_EXPERIENCE.md",
        "PFI/reports/pfi_v023/stage_5/*",
        "PFI/web/app/shell.js (minimal runtime loader/application for the existing monolith shell)",
      ]),
      validation_commands: Object.freeze([
        "node --check PFI/web/app/pages/home.js",
        "node --check PFI/web/app/shell.js",
        "python3 -m pytest PFI/tests/test_v023_stage5_home_experience.py -q",
        "python3 -m pytest PFI/tests/test_v023_*.py -q",
      ]),
      evidence_files: Object.freeze([
        "PFI/docs/pfi_v023/STAGE5_HOME_EXPERIENCE.md",
        "PFI/reports/pfi_v023/stage_5/phase_5_1/evidence.json",
        "PFI/reports/pfi_v023/stage_5/phase_5_1/terminal.log",
        "PFI/reports/pfi_v023/stage_5/phase_5_1/changed_files.txt",
      ]),
      explicitly_not_done: Object.freeze([
        "Phase 5.2 下一步动作生成",
        "Phase 5.3 去 AI 痕迹全量清理",
        "Stage 6 核心财务指标 read model 接入",
        "Stage 5 whole-stage review",
        "GitHub main upload for intermediate phase",
      ]),
    });
  }

  function buildStage5Phase52Contract() {
    return Object.freeze({
      version: VERSION,
      stage: STAGE,
      phase_id: PHASE52_ID,
      phase_name: PHASE52_NAME,
      current_phase_only: true,
      max_one_phase_per_run: true,
      action_sources: Object.freeze(["data_status", "review_task"]),
      tasks: Object.freeze([
        "由数据状态生成动作",
        "由待复核生成动作",
        "动作可跳转",
        "阻断动作可解释",
      ]),
      allowed_files: Object.freeze([
        "PFI/web/app/pages/home.js",
        "PFI/web/app/components/*.js",
        "PFI/web/styles.css",
        "PFI/tests/test_v023_stage5_home_experience.py",
        "PFI/docs/pfi_v023/STAGE5_HOME_EXPERIENCE.md",
        "PFI/reports/pfi_v023/stage_5/*",
      ]),
      validation_commands: Object.freeze([
        "node --check PFI/web/app/pages/home.js",
        "python3 -m pytest PFI/tests/test_v023_stage5_home_experience.py -q",
        "python3 -m pytest PFI/tests/test_v023_*.py -q",
      ]),
      evidence_files: Object.freeze([
        "PFI/reports/pfi_v023/stage_5/phase_5_2/evidence.json",
        "PFI/reports/pfi_v023/stage_5/phase_5_2/action_sources.json",
        "PFI/reports/pfi_v023/stage_5/phase_5_2/terminal.log",
        "PFI/reports/pfi_v023/stage_5/phase_5_2/changed_files.txt",
      ]),
      explicitly_not_done: Object.freeze([
        "Phase 5.3 去 AI 痕迹全量清理",
        "Stage 5 whole-stage review",
        "Stage 6 核心财务指标 read model 接入",
        "GitHub main upload for intermediate phase",
      ]),
    });
  }

  function buildStage5Phase53Contract() {
    return Object.freeze({
      version: VERSION,
      stage: STAGE,
      phase_id: PHASE53_ID,
      phase_name: PHASE53_NAME,
      current_phase_only: true,
      max_one_phase_per_run: true,
      home_visible_sections: HOME_VISIBLE_SECTIONS_PHASE53,
      forbidden_home_artifacts: HOME_FORBIDDEN_ARTIFACTS_PHASE53,
      tasks: Object.freeze([
        "删除首页开发术语",
        "设置/反馈隔离",
        "证据/参数收纳到报告或详情",
        "禁止词测试",
      ]),
      allowed_files: Object.freeze([
        "PFI/web/app/pages/home.js",
        "PFI/web/app/shell.js (home-only surface isolation)",
        "PFI/tests/test_v023_stage5_home_experience.py",
        "PFI/docs/pfi_v023/STAGE5_HOME_EXPERIENCE.md",
        "PFI/reports/pfi_v023/stage_5/phase_5_3/*",
      ]),
      validation_commands: Object.freeze([
        "node --check PFI/web/app/pages/home.js",
        "node --check PFI/web/app/shell.js",
        "python3 -m pytest PFI/tests/test_v023_stage5_home_experience.py -q",
        "python3 -m pytest PFI/tests/test_v023_*.py -q",
      ]),
      evidence_files: Object.freeze([
        "PFI/reports/pfi_v023/stage_5/phase_5_3/evidence.json",
        "PFI/reports/pfi_v023/stage_5/phase_5_3/home_surface_policy.json",
        "PFI/reports/pfi_v023/stage_5/phase_5_3/terminal.log",
        "PFI/reports/pfi_v023/stage_5/phase_5_3/changed_files.txt",
      ]),
      explicitly_not_done: Object.freeze([
        "Stage 5 whole-stage review",
        "Stage 6 核心财务指标 read model 接入",
        "GitHub main upload for intermediate phase",
      ]),
    });
  }

  function buildStage5HomeViewModel(input = {}) {
    const metricStates = normalizeMetricStates(input.metric_states || input.metricStates || input.core_metric_states);
    const financialState = metricStates.map(buildFinancialCard);
    const readyCount = financialState.filter((item) => item.status === "ready" || item.status === "confirmed_zero").length;
    const blockedCount = financialState.length - readyCount;
    const recentChanges = normalizeRecentChanges(input.recent_changes || input.recentChanges);
    const reviewTasks = normalizeReviewTasks(input.review_tasks || input.reviewTasks);
    const nextActions = buildNextActions(financialState, reviewTasks);
    const reportEntry = buildReportEntry();

    return Object.freeze({
      schema: "PFIV023Stage5HomeExperienceV1",
      version: VERSION,
      stage: STAGE,
      phase_id: PHASE51_ID,
      phase_ids: Object.freeze([PHASE51_ID, PHASE52_ID, PHASE53_ID]),
      current_phase_only: true,
      sections: HOME_SECTIONS.map((section) => ({ ...section })),
      home_conclusion: "先看财务状态、数据健康、下一步动作、最近变化，再进入报告。",
      home_runtime_label: "财务状态与下一步动作",
      home_surface_policy: cloneSurfacePolicy(),
      financial_state: financialState,
      money_location: buildMoneyLocation(financialState),
      data_health: Object.freeze({
        title: "数据健康",
        uses_stage2_statuses: true,
        ready_count: readyCount,
        blocked_count: blockedCount,
        summary: blockedCount
          ? `${blockedCount} 个核心指标需要补齐真实数据状态`
          : "核心指标已带真实数据状态",
        statuses: financialState.map((item) => ({
          metric_id: item.metric_id,
          label: item.label,
          status: item.status,
          message_zh: item.message_zh,
          source: item.source,
          as_of: item.as_of,
          evidence_hash: item.evidence_hash,
        })),
      }),
      recent_changes: recentChanges,
      next_actions: nextActions,
      report_entry: reportEntry,
      home_cards: financialState.map((item) => [
        item.label,
        item.display_value,
        item.source ? `${item.status_label} · ${item.source}` : item.message_zh,
      ]),
      home_features: buildHomeInformationCards(financialState, readyCount, blockedCount, recentChanges, nextActions, reportEntry),
      home_rows: buildHomeRows(financialState, readyCount, blockedCount, recentChanges, reportEntry),
      home_tasks: buildHomeTaskRows(readyCount, blockedCount, recentChanges, nextActions, reportEntry),
    });
  }

  function buildStage6Phase62HomeMetricViewModel(readModel = {}) {
    const cards = stage6CoreMetricsApi().buildMetricCards(readModel, STAGE62_HOME_METRICS);
    const readyCount = cards.filter((card) => DISPLAY_VALUE_STATUSES.includes(card.status)).length;
    return Object.freeze({
      schema: "PFIV023Stage6PageMetricViewModelV1",
      version: VERSION,
      stage: "Stage 6",
      phase_id: STAGE62_ID,
      page: "home",
      title: "首页核心指标",
      cards,
      shell_cards: cards.map((card) => [card.label, card.display_value, card.detail]),
      summary_zh: `核心指标 ${readyCount} 项可显示，${cards.length - readyCount} 项保留中文状态。`,
    });
  }

  function normalizeMetricStates(metrics) {
    const source = Array.isArray(metrics) && metrics.length ? metrics : DEFAULT_METRICS;
    return source.map((item) => ({
      metric_id: safeText(item.metric_id, "metric"),
      label: safeText(item.label, "指标"),
      value: item.value ?? null,
      currency: item.currency || "CNY",
      status: STATUS_COPY_ZH[item.status] ? item.status : "not_loaded",
      source: item.source || null,
      as_of: item.as_of || null,
      evidence_hash: item.evidence_hash || null,
      message_zh: safeText(item.message_zh, STATUS_COPY_ZH[item.status] || STATUS_COPY_ZH.not_loaded),
    }));
  }

  function buildFinancialCard(item) {
    return Object.freeze({
      ...item,
      display_value: renderMetricValueZh(item),
      status_label: STATUS_COPY_ZH[item.status] || STATUS_COPY_ZH.not_loaded,
    });
  }

  function buildMoneyLocation(financialState) {
    return financialState.map((item) =>
      Object.freeze({
        metric_id: item.metric_id,
        label: item.label,
        status: item.status,
        display_value: item.display_value,
        source: item.source,
        message_zh: item.source
          ? `${item.label}来自${item.source}`
          : `${item.label}等待真实来源，不展示数值替代`,
      }),
      );
    }

  function normalizeRecentChanges(changes) {
    if (!Array.isArray(changes) || !changes.length) {
      return [
        Object.freeze({
          state: "empty",
          label: "最近变化",
          message: "未读取到真实变化记录；不会编写虚构变化。",
          source: null,
          as_of: null,
        }),
      ];
    }
    return changes.slice(0, 4).map((item) =>
      Object.freeze({
        state: "ready",
        label: safeText(item.label, "最近变化"),
        message: safeText(item.message, "已读取真实变化记录"),
        source: item.source || null,
        as_of: item.as_of || null,
      }),
    );
  }

  function normalizeReviewTasks(tasks) {
    if (!Array.isArray(tasks)) return [];
    return tasks
      .filter((item) => item && (item.task_id || item.taskId || item.label))
      .slice(0, 6)
      .map((item, index) => ({
        task_id: safeText(item.task_id || item.taskId, `review-task-${index + 1}`),
        label: safeText(item.label, "待复核任务"),
        reason: safeText(item.reason, "需要人工复核"),
        routeAlias: normalizeRouteAlias(item.routeAlias || item.route_alias || "/ledger?tab=review"),
        targetWorkspace: safeText(item.targetWorkspace || item.target_workspace, "ledger"),
        evidence_count: Number(item.evidence_count || item.evidenceCount || 0),
      }));
  }

  function buildNextActions(financialState, reviewTasks) {
    const dataActions = financialState
      .filter((item) => !canDisplayFinancialValue(item))
      .map(buildDataStatusAction);
    const reviewActions = reviewTasks.map(buildReviewTaskAction);
    return Object.freeze([...dataActions, ...reviewActions].slice(0, 6));
  }

  function buildDataStatusAction(item) {
    const target = actionTargetForStatus(item.status);
    return Object.freeze({
      action_id: `data-status-${item.metric_id}`,
      title: actionTitleForStatus(item),
      source_type: "data_status",
      source_metric_id: item.metric_id,
      source_task_id: null,
      generated_from: `metric:${item.metric_id}:${item.status}`,
      blocked: item.status !== "filter_empty",
      targetWorkspace: target.targetWorkspace,
      routeAlias: target.routeAlias,
      explanation_zh: `${item.label}：${item.message_zh || STATUS_COPY_ZH[item.status] || STATUS_COPY_ZH.not_loaded}。${target.reason}`,
    });
  }

  function buildReviewTaskAction(item) {
    return Object.freeze({
      action_id: `review-task-${item.task_id}`,
      title: item.label,
      source_type: "review_task",
      source_metric_id: null,
      source_task_id: item.task_id,
      generated_from: `review_task:${item.task_id}`,
      blocked: false,
      targetWorkspace: item.targetWorkspace,
      routeAlias: item.routeAlias,
      explanation_zh: item.evidence_count
        ? `${item.reason}，证据 ${item.evidence_count} 项。`
        : item.reason,
    });
  }

  function actionTargetForStatus(status) {
    const targets = {
      not_loaded: ["sync", "/sources-upload?tab=upload", "先进入上传中心补齐真实文件。"],
      not_mounted: ["sync", "/sources-upload?tab=sources", "先检查真实数据源是否挂链。"],
      path_error: ["sync", "/sources-upload?tab=sources", "先检查数据目录和来源路径。"],
      permission_error: ["settings", "/settings?tab=data-system", "先检查本机权限和数据目录。"],
      parse_error: ["sync", "/sources-upload?tab=review", "先处理解析失败和字段问题。"],
      outdated: ["sync", "/sources-upload?tab=history", "先检查快照日期和导入历史。"],
      filter_empty: ["ledger", "/ledger?tab=filter", "先调整筛选或查看数据范围。"],
      calculation_error: ["insights", "/reports?tab=monthly", "先查看报告阻断和公式输入。"],
      review_required: ["ledger", "/ledger?tab=review", "先处理待复核记录。"],
    };
    const [targetWorkspace, routeAlias, reason] = targets[status] || targets.not_loaded;
    return { targetWorkspace, routeAlias, reason };
  }

  function actionTitleForStatus(item) {
    if (item.status === "review_required") return `复核${item.label}`;
    if (item.status === "parse_error") return `处理${item.label}解析问题`;
    return `补齐${item.label}数据`;
  }

  function buildHomeInformationCards(financialState, readyCount, blockedCount, recentChanges, nextActions, reportEntry) {
    const locationReady = financialState.filter((item) => item.source).length;
    return [
      {
        title: "下一步动作",
        status: nextActions.length ? "待处理" : "暂无动作",
        source: nextActions[0]?.generated_from || "数据状态和待复核任务",
        detail: nextActions[0]?.explanation_zh || "当前没有由数据状态或待复核任务生成的动作。",
        target: nextActions[0]
          ? { workspace: nextActions[0].targetWorkspace, routeAlias: nextActions[0].routeAlias, label: "处理动作" }
          : { workspace: "home", routeAlias: "/home?tab=actions", label: "查看首页" },
      },
      {
        title: "财务状态摘要",
        status: blockedCount ? "需要复核" : "可用",
        source: "数据状态",
        detail: `核心指标 ${readyCount} 个可显示，${blockedCount} 个保留中文状态。`,
        target: { workspace: "home", routeAlias: "/home?tab=status", label: "查看状态" },
      },
      {
        title: "钱在哪里",
        status: locationReady ? "有来源" : "等待来源",
        source: "账户、现金、投资状态",
        detail: locationReady ? `${locationReady} 个指标带来源。` : "等待真实账户、现金或投资来源接入。",
        target: { workspace: "accounts", routeAlias: "/accounts?tab=overview", label: "查看账户" },
      },
      {
        title: "数据健康",
        status: blockedCount ? "有阻断" : "可用",
        source: "状态机",
        detail: blockedCount ? `${blockedCount} 个指标需要补齐来源、路径或解析状态。` : "核心指标状态可解释。",
        target: { workspace: "sync", routeAlias: "/sources-upload?tab=sources", label: "查看数据" },
      },
      {
        title: "最近变化",
        status: recentChanges[0]?.state === "empty" ? "暂无记录" : "可用",
        source: recentChanges[0]?.source || "真实变化记录",
        detail: recentChanges[0]?.message || "查看最近真实变化。",
        target: { workspace: "home", routeAlias: "/home?tab=reports", label: "查看变化" },
      },
      {
        title: reportEntry.title,
        status: "可查看",
        source: "报告与洞察",
        detail: reportEntry.detail,
        target: { workspace: reportEntry.targetWorkspace, routeAlias: reportEntry.routeAlias, label: reportEntry.label },
      },
    ];
  }

  function buildHomeRows(financialState, readyCount, blockedCount, recentChanges, reportEntry) {
    return [
      ["1", "财务状态摘要", `可显示 ${readyCount} 项`, blockedCount ? `${blockedCount} 项显示中文状态` : "核心指标可解释", blockedCount ? "复核" : "可用"],
      ["2", "钱在哪里", "账户、现金、投资", "按真实来源和状态拆分，不补写金额。", "可查看"],
      ["3", "数据健康", "数据状态", blockedCount ? "优先处理阻断状态。" : "状态完整。", blockedCount ? "有阻断" : "可用"],
      ["4", "最近变化", recentChanges[0]?.label || "最近变化", recentChanges[0]?.message || "等待真实变化记录。", recentChanges[0]?.state === "empty" ? "暂无记录" : "可用"],
      ["5", reportEntry.title, "报告与洞察", reportEntry.detail, "可查看"],
    ];
  }

  function buildHomeTaskRows(readyCount, blockedCount, recentChanges, nextActions, reportEntry) {
    const actionTasks = nextActions.slice(0, 3).map((action) => ({
      title: action.title,
      detail: action.explanation_zh,
      status: action.blocked ? "review" : "ready",
      source_type: action.source_type,
      routeAlias: action.routeAlias,
      targetWorkspace: action.targetWorkspace,
    }));
    return [
      ...actionTasks,
      { title: "财务状态摘要", detail: `可显示 ${readyCount} 项，中文状态 ${blockedCount} 项`, status: blockedCount ? "review" : "ready", source_type: "home_section" },
      { title: "钱在哪里", detail: "账户、现金和投资只按真实来源展示。", status: "ready", source_type: "home_section" },
      { title: "最近变化", detail: recentChanges[0]?.message || "等待真实变化记录。", status: recentChanges[0]?.state === "empty" ? "queued" : "ready", source_type: "home_section" },
      { title: reportEntry.title, detail: reportEntry.detail, status: "ready", source_type: "report_entry", routeAlias: reportEntry.routeAlias, targetWorkspace: reportEntry.targetWorkspace },
    ].slice(0, 6);
  }

  function buildReportEntry() {
    return Object.freeze({
      title: "报告入口",
      label: "打开报告与洞察",
      detail: "查看结论、数据范围、公式和报告状态。",
      targetWorkspace: "insights",
      routeAlias: "/reports?tab=monthly",
    });
  }

  function cloneSurfacePolicy() {
    return Object.freeze({
      home_visible_sections: [...HOME_SURFACE_POLICY_PHASE53.home_visible_sections],
      settings_feedback_isolated: HOME_SURFACE_POLICY_PHASE53.settings_feedback_isolated,
      evidence_parameters_routed_out: HOME_SURFACE_POLICY_PHASE53.evidence_parameters_routed_out,
      no_developer_stage_terms_on_home: HOME_SURFACE_POLICY_PHASE53.no_developer_stage_terms_on_home,
      evidence_route: { ...HOME_SURFACE_POLICY_PHASE53.evidence_route },
      parameter_route: { ...HOME_SURFACE_POLICY_PHASE53.parameter_route },
    });
  }

  function renderMetricValueZh(metricState) {
    if (!canDisplayFinancialValue(metricState)) {
      return metricState.message_zh || STATUS_COPY_ZH[metricState.status] || STATUS_COPY_ZH.not_loaded;
    }
    const currency = metricState.currency || "CNY";
    return `${currency} ${Number(metricState.value).toLocaleString("zh-CN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  function canDisplayFinancialValue(metricState) {
    if (!metricState || !DISPLAY_VALUE_STATUSES.includes(metricState.status)) return false;
    if (metricState.value === null || metricState.value === undefined) return false;
    if (!metricState.source || !metricState.as_of || !metricState.evidence_hash) return false;
    if (metricState.status === "confirmed_zero" && Number(metricState.value) !== 0) return false;
    return true;
  }

  function metric(metricId, label, currency) {
    return Object.freeze({
      metric_id: metricId,
      label,
      value: null,
      currency,
      status: "not_loaded",
      source: null,
      as_of: null,
      evidence_hash: null,
      message_zh: STATUS_COPY_ZH.not_loaded,
    });
  }

  function safeText(value, fallback) {
    const text = String(value ?? "").trim();
    return text || fallback;
  }

  function normalizeRouteAlias(routeAlias) {
    const route = String(routeAlias || "").trim();
    if (!route) return "/home";
    return route.startsWith("/") ? route : `/${route}`;
  }

  function stage6CoreMetricsApi() {
    if (typeof globalThis !== "undefined" && globalThis.PFI_STAGE6_CORE_METRICS) {
      return globalThis.PFI_STAGE6_CORE_METRICS;
    }
    if (typeof require === "function") {
      return require("../data/coreMetrics.js");
    }
    throw new Error("PFI_STAGE6_CORE_METRICS is required");
  }

  return Object.freeze({
    buildStage5Phase51Contract,
    buildStage5Phase52Contract,
    buildStage5Phase53Contract,
    buildStage5HomeViewModel,
    buildStage6Phase62HomeMetricViewModel,
    renderMetricValueZh,
    canDisplayFinancialValue,
  });
});
