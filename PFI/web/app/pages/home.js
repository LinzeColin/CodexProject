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
  const PHASE_ID = "V023-S5-P5.1";
  const PHASE_NAME = "首页信息架构";

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

  const DEFAULT_METRICS = Object.freeze([
    metric("net_worth_cny", "净资产", "CNY"),
    metric("cash_balance_cny", "现金余额", "CNY"),
    metric("investment_market_value_cny", "投资市值", "CNY"),
    metric("month_spend_cny", "本月支出", "CNY"),
  ]);

  function buildStage5Phase51Contract() {
    return Object.freeze({
      version: VERSION,
      stage: STAGE,
      phase_id: PHASE_ID,
      phase_name: PHASE_NAME,
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

  function buildStage5HomeViewModel(input = {}) {
    const metricStates = normalizeMetricStates(input.metric_states || input.metricStates || input.core_metric_states);
    const financialState = metricStates.map(buildFinancialCard);
    const readyCount = financialState.filter((item) => item.status === "ready" || item.status === "confirmed_zero").length;
    const blockedCount = financialState.length - readyCount;
    const recentChanges = normalizeRecentChanges(input.recent_changes || input.recentChanges);

    return Object.freeze({
      schema: "PFIV023Stage5HomeExperienceV1",
      version: VERSION,
      stage: STAGE,
      phase_id: PHASE_ID,
      current_phase_only: true,
      sections: HOME_SECTIONS.map((section) => ({ ...section })),
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
      home_cards: financialState.map((item) => [
        item.label,
        item.display_value,
        item.source ? `${item.status_label} · ${item.source}` : item.message_zh,
      ]),
      home_features: buildHomeInformationCards(financialState, readyCount, blockedCount, recentChanges),
      home_rows: buildHomeRows(financialState, readyCount, blockedCount, recentChanges),
      home_tasks: buildPhase51TaskRows(readyCount, blockedCount, recentChanges),
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

  function buildHomeInformationCards(financialState, readyCount, blockedCount, recentChanges) {
    const locationReady = financialState.filter((item) => item.source).length;
    return [
      {
        title: "财务状态摘要",
        status: blockedCount ? "需要复核" : "可用",
        source: "Stage 2 数据状态机",
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
    ];
  }

  function buildHomeRows(financialState, readyCount, blockedCount, recentChanges) {
    return [
      ["1", "财务状态摘要", `可显示 ${readyCount} 项`, blockedCount ? `${blockedCount} 项显示中文状态` : "核心指标可解释", blockedCount ? "复核" : "可用"],
      ["2", "钱在哪里", "账户、现金、投资", "按真实来源和状态拆分，不补写金额。", "可查看"],
      ["3", "数据健康", "Stage 2 状态", blockedCount ? "优先处理阻断状态。" : "状态完整。", blockedCount ? "有阻断" : "可用"],
      ["4", "最近变化", recentChanges[0]?.label || "最近变化", recentChanges[0]?.message || "等待真实变化记录。", recentChanges[0]?.state === "empty" ? "暂无记录" : "可用"],
    ];
  }

  function buildPhase51TaskRows(readyCount, blockedCount, recentChanges) {
    return [
      { title: "财务状态摘要", detail: `可显示 ${readyCount} 项，中文状态 ${blockedCount} 项`, status: blockedCount ? "review" : "ready" },
      { title: "钱在哪里", detail: "账户、现金和投资只按真实来源展示。", status: "ready" },
      { title: "最近变化", detail: recentChanges[0]?.message || "等待真实变化记录。", status: recentChanges[0]?.state === "empty" ? "queued" : "ready" },
    ];
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

  return Object.freeze({
    buildStage5Phase51Contract,
    buildStage5HomeViewModel,
    renderMetricValueZh,
    canDisplayFinancialValue,
  });
});
