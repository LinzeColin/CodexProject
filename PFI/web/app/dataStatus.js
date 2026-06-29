(function attachDataStatusContract(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_STAGE2_DATA_STATUS = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildDataStatusContract() {
  const statuses = Object.freeze([
    "ready",
    "confirmed_zero",
    "not_loaded",
    "not_mounted",
    "path_error",
    "permission_error",
    "parse_error",
    "outdated",
    "filter_empty",
    "calculation_error",
    "review_required",
  ]);

  const requiredFields = Object.freeze([
    "metric_id",
    "label",
    "value",
    "currency",
    "status",
    "source",
    "as_of",
    "evidence_hash",
    "message_zh",
  ]);

  const statusCopyZh = Object.freeze({
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

  const coreMetricDefaults = Object.freeze([
    Object.freeze({ metric_id: "net_worth_cny", label: "净资产", currency: "CNY" }),
    Object.freeze({ metric_id: "cash_balance_cny", label: "现金余额", currency: "CNY" }),
    Object.freeze({ metric_id: "investment_market_value_cny", label: "投资市值", currency: "CNY" }),
  ]);

  const errorStates = Object.freeze([
    Object.freeze({
      id: "path_error",
      label: "路径错误",
      message: "真实数据目录不存在、未挂载或不在允许路径内。",
      action: "检查数据目录",
    }),
    Object.freeze({
      id: "permission_error",
      label: "权限失败",
      message: "当前进程无法读取已发现的数据文件。",
      action: "检查本机文件权限",
    }),
    Object.freeze({
      id: "parse_error",
      label: "解析失败",
      message: "数据文件结构无法被当前读取合同解析。",
      action: "查看文件、行或字段",
    }),
  ]);

  function canDisplayFinancialValue(metric) {
    return Boolean(
      metric &&
        (metric.status === "ready" || metric.status === "confirmed_zero") &&
        metric.value !== null &&
        metric.value !== undefined,
    );
  }

  function renderMetricValueZh(metric) {
    if (!canDisplayFinancialValue(metric)) {
      return metric && metric.message_zh ? metric.message_zh : "数据状态未知";
    }
    const currency = metric.currency || "CNY";
    return `${currency} ${Number(metric.value).toLocaleString("zh-CN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  function buildDataGateViewModel(audit) {
    const normalizedAudit = audit && typeof audit === "object" ? audit : {};
    const gateStatus = normalizedAudit.audit_status || "not_loaded";
    const blockingReasons = Array.isArray(normalizedAudit.blocking_reasons)
      ? normalizedAudit.blocking_reasons
      : [];
    const metrics = normalizeMetrics(normalizedAudit.core_metric_states, gateStatus);

    return {
      title: "真实数据门禁",
      gateStatus,
      gateMessage: blockingReasons[0] || statusCopyZh[gateStatus] || "数据状态未知",
      metrics,
      checks: buildCheckRows(normalizedAudit),
      errorStates: errorStates.map((item) => ({ ...item })),
    };
  }

  function renderDataGateHTML(audit) {
    const view = buildDataGateViewModel(audit);
    const metricsHTML = view.metrics
      .map(
        (metric) => `
          <article class="pfi-data-gate__metric" data-status="${escapeHTML(metric.status)}">
            <div class="pfi-data-gate__metric-label">${escapeHTML(metric.label)}</div>
            <div class="pfi-data-gate__metric-value">${escapeHTML(renderMetricValueZh(metric))}</div>
            <div class="pfi-data-gate__metric-meta">${escapeHTML(metric.source || metric.status)}</div>
          </article>`,
      )
      .join("");
    const checksHTML = view.checks
      .map(
        (row) => `
          <div class="pfi-data-gate__check">
            <span>${escapeHTML(row.label)}</span>
            <strong>${escapeHTML(row.value)}</strong>
          </div>`,
      )
      .join("");
    const errorsHTML = view.errorStates
      .map(
        (item) => `
          <article class="pfi-data-gate__error" data-error-id="${escapeHTML(item.id)}">
            <strong>${escapeHTML(item.label)}</strong>
            <span>${escapeHTML(item.message)}</span>
            <em>${escapeHTML(item.action)}</em>
          </article>`,
      )
      .join("");

    return `
      <section class="pfi-data-gate" data-gate-status="${escapeHTML(view.gateStatus)}">
        <header class="pfi-data-gate__header">
          <p class="pfi-data-gate__eyebrow">PFI v0.2.3 Stage 2</p>
          <h2>${escapeHTML(view.title)}</h2>
          <p>${escapeHTML(view.gateMessage)}</p>
        </header>
        <div class="pfi-data-gate__metrics">${metricsHTML}</div>
        <section class="pfi-data-gate__checks" aria-label="数据检查板">
          <h3>数据检查板</h3>
          ${checksHTML}
        </section>
        <section class="pfi-data-gate__errors" aria-label="错误状态">
          <h3>错误状态</h3>
          ${errorsHTML}
        </section>
      </section>`;
  }

  function mountDataGate(container, audit) {
    if (!container) {
      throw new Error("container is required");
    }
    container.innerHTML = renderDataGateHTML(audit);
    return buildDataGateViewModel(audit);
  }

  function normalizeMetrics(metrics, gateStatus) {
    const input = Array.isArray(metrics) && metrics.length ? metrics : coreMetricDefaults;
    return input.map((metric) => {
      const status = metric.status || (gateStatus === "ready" ? "review_required" : gateStatus);
      return {
        metric_id: metric.metric_id,
        label: metric.label,
        value: canDisplayFinancialValue(metric) ? metric.value : null,
        currency: metric.currency || "CNY",
        status,
        source: metric.source || null,
        as_of: metric.as_of || null,
        evidence_hash: metric.evidence_hash || null,
        message_zh: metric.message_zh || messageForStatus(status),
      };
    });
  }

  function buildCheckRows(audit) {
    return [
      { label: "文件数", value: countOrUnavailable(audit.file_count) },
      { label: "原始记录数", value: countOrUnavailable(audit.raw_record_count) },
      { label: "标准化记录数", value: countOrUnavailable(audit.standardized_record_count) },
      { label: "账户数", value: countOrUnavailable(audit.account_count) },
      { label: "持仓数", value: countOrUnavailable(audit.holding_count) },
      { label: "read model hash", value: audit.read_model_hash || "未生成" },
      { label: "as of", value: audit.as_of || "未提供" },
    ];
  }

  function countOrUnavailable(value) {
    return Number.isFinite(value) ? String(value) : "未统计";
  }

  function messageForStatus(status) {
    if (status === "not_mounted") {
      return "未挂载真实个人财务数据源";
    }
    return statusCopyZh[status] || "数据状态未知";
  }

  function escapeHTML(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  return Object.freeze({
    statuses,
    requiredFields,
    statusCopyZh,
    coreMetricDefaults,
    buildDataGateViewModel,
    canDisplayFinancialValue,
    mountDataGate,
    renderDataGateHTML,
    renderMetricValueZh,
  });
});
