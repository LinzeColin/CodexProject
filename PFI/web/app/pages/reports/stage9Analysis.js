(function attachPFIV025Stage9Analysis(root, factory) {
  const nodeRequire = typeof require === "function" ? require : null;
  const reviewedData = root?.PFI_V025_STAGE9_REVIEWED_ANALYSIS_DATA
    || (nodeRequire ? nodeRequire("./stage9AnalysisData.js") : null);
  const api = factory(reviewedData);
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.PFI_V025_STAGE9_ANALYSIS = api;
})(typeof window !== "undefined" ? window : globalThis, function buildPFIV025Stage9Analysis(reviewedData) {
  "use strict";

  function deepFreeze(value) {
    if (!value || typeof value !== "object" || Object.isFrozen(value)) return value;
    Object.values(value).forEach(deepFreeze);
    return Object.freeze(value);
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function canonicalJsonForComparison(value) {
    return JSON.stringify(value);
  }

  const REQUIRED_REPORT_STATUSES = Object.freeze({
    net_worth: "blocked",
    cash: "blocked",
    investment: "blocked",
    consumption: "partial",
    cashflow: "partial",
  });
  const LEGACY_SNAPSHOT_BINDING = deepFreeze({
    schema: "PFIV025Stage9Phase92SnapshotBindingV1",
    phaseId: "V025-S9-P9.2",
    observedAt: "2026-07-15T16:00:00+10:00",
    packHash: "sha256:c3df8b878038bffdb28bfe4112d9a875e43e5d41cb910f86b6482768223a19e9",
    snapshotPath: "PFI/config/reports/v025_phase92_analysis_snapshot.json",
  });
  const LEGACY_EMBEDDED_UI_CONTRACT = deepFreeze(
  {
    "automatic_trading_allowed": false,
    "contains_private_values": false,
    "financial_values_emitted": 0,
    "formula_cards": [
      {
        "formula_id": "FORM-PFI-015",
        "label_zh": "双消费与投资活动组件",
        "limitation": "Published real events validate living consumption and investment allocation; unresolved transfer/refund pools prevent full funding/refund coverage.",
        "parameters": [
          "PARAM-PFI-081",
          "PARAM-PFI-082",
          "PARAM-PFI-083",
          "PARAM-PFI-084",
          "PARAM-PFI-085"
        ],
        "report_types": [
          "consumption",
          "cashflow"
        ],
        "review_route": "/reports/metric-drilldown?formula=FORM-PFI-015",
        "validation_status": "validated_real_snapshot"
      },
      {
        "formula_id": "FORM-PFI-016",
        "label_zh": "净资产、现金与投资重配置不变量",
        "limitation": "Account balance, liability, holding, price and FX snapshots are not loaded.",
        "parameters": [
          "PARAM-PFI-081"
        ],
        "report_types": [
          "net_worth",
          "cash"
        ],
        "review_route": "/reports/metric-drilldown?formula=FORM-PFI-016",
        "validation_status": "blocked_missing_required_sources"
      },
      {
        "formula_id": "FORM-PFI-017",
        "label_zh": "投资收益、成本与拖累",
        "limitation": "Holdings, cost basis, point-in-time price, fee, tax and FX lineage are incomplete.",
        "parameters": [
          "PARAM-PFI-081"
        ],
        "report_types": [
          "investment"
        ],
        "review_route": "/reports/metric-drilldown?formula=FORM-PFI-017",
        "validation_status": "blocked_missing_required_sources"
      },
      {
        "formula_id": "FORM-PFI-018",
        "label_zh": "日期感知投资 XIRR",
        "limitation": "No complete dated funding/return/terminal-value chain is available for real XIRR.",
        "parameters": [
          "PARAM-PFI-081",
          "PARAM-PFI-089",
          "PARAM-PFI-090",
          "PARAM-PFI-091",
          "PARAM-PFI-092"
        ],
        "report_types": [
          "investment"
        ],
        "review_route": "/reports/metric-drilldown?formula=FORM-PFI-018",
        "validation_status": "blocked_insufficient_chain"
      },
      {
        "formula_id": "FORM-PFI-019",
        "label_zh": "七窗口外部现金流",
        "limitation": "Seven real lookback windows and empty-window false-zero boundaries pass; date precision remains daily.",
        "parameters": [
          "PARAM-PFI-081",
          "PARAM-PFI-086"
        ],
        "report_types": [
          "cash",
          "cashflow"
        ],
        "review_route": "/reports/metric-drilldown?formula=FORM-PFI-019",
        "validation_status": "validated_real_snapshot"
      },
      {
        "formula_id": "FORM-PFI-020",
        "label_zh": "分类与标签治理规则",
        "limitation": "Taxonomy structure passes, but classification accuracy lacks labels and out-of-sample ground truth.",
        "parameters": [
          "PARAM-PFI-081",
          "PARAM-PFI-087",
          "PARAM-PFI-088"
        ],
        "report_types": [
          "consumption"
        ],
        "review_route": "/reports/metric-drilldown?formula=FORM-PFI-020",
        "validation_status": "validated_structure_only"
      }
    ],
    "hashes": {
      "base_report_manifest_hash": "sha256:ad0208b30a895e902c86b226a1186840a5a8c1f2747062f406f4debea48dabf4",
      "data_manifest_hash": "sha256:f960dc36a23ce8e283eef7e76a8098164718410415ed54374bf18bf34309f658",
      "formula_registry_hash": "sha256:65098b8f10602070639c3e42a128c0fed8bcabddb3b9400cf1436c0f2f85d8cd",
      "parameter_hash": "sha256:d6aacff83da3e7c4945b1376d62da72f7f1edd88999972645eba9488f90db433",
      "read_model_hash": "sha256:f1962e376536611ab43f60a95c9789510b52ee11f627de7037046dc71b73e4b6"
    },
    "model_cards": [
      {
        "counter_evidence_count": 3,
        "historical_out_of_sample_status": "blocked_insufficient_ground_truth",
        "invariant_status": "partial_pass_with_blocked_components",
        "limitation_count": 6,
        "metamorphic_status": "pass",
        "model_id": "MOD-PFI-010",
        "model_version": "pfi-v0.2.5-financial-models-v1",
        "status": "partial_validated_with_blocked_components"
      }
    ],
    "phase_9_3_started": false,
    "phase_id": "V025-S9-P9.2",
    "report_cards": [
      {
        "data_range": {
          "end": "2026-06-03",
          "start": "2022-06-06"
        },
        "financial_values_emitted": 0,
        "formula_ids": [
          "FORM-PFI-016"
        ],
        "parameter_ids": [
          "PARAM-PFI-081"
        ],
        "primary_review_route": "/accounts/reconcile",
        "report_id": "pfi-v025-net-worth",
        "report_type": "net_worth",
        "review_entry_ids": [
          "REVIEW-SRC-ACCOUNT-BALANCES",
          "REVIEW-SRC-LIABILITIES",
          "REVIEW-SRC-HOLDINGS",
          "REVIEW-SRC-MARKET-PRICES",
          "REVIEW-SRC-FX-SNAPSHOT",
          "REVIEW-ECONOMIC-EVENT-ADAPTER"
        ],
        "scope_explanation_zh": "当前报告只使用已验证的真实来源覆盖，不把缺失输入解释为零。",
        "status": "blocked",
        "status_statement_zh": "关键真实输入未 ready；只展示公式、限制与复核入口。",
        "status_zh": "已阻断",
        "title_zh": "净资产报告",
        "transaction_record_count": 8815
      },
      {
        "data_range": {
          "end": "2026-06-03",
          "start": "2022-06-06"
        },
        "financial_values_emitted": 0,
        "formula_ids": [
          "FORM-PFI-016",
          "FORM-PFI-019"
        ],
        "parameter_ids": [
          "PARAM-PFI-081",
          "PARAM-PFI-086"
        ],
        "primary_review_route": "/accounts/reconcile",
        "report_id": "pfi-v025-cash",
        "report_type": "cash",
        "review_entry_ids": [
          "REVIEW-SRC-ACCOUNT-BALANCES",
          "REVIEW-SRC-LIABILITIES",
          "REVIEW-ECONOMIC-EVENT-ADAPTER"
        ],
        "scope_explanation_zh": "当前报告只使用已验证的真实来源覆盖，不把缺失输入解释为零。",
        "status": "blocked",
        "status_statement_zh": "关键真实输入未 ready；只展示公式、限制与复核入口。",
        "status_zh": "已阻断",
        "title_zh": "现金报告",
        "transaction_record_count": 8815
      },
      {
        "data_range": {
          "end": "2026-06-03",
          "start": "2022-06-06"
        },
        "financial_values_emitted": 0,
        "formula_ids": [
          "FORM-PFI-017",
          "FORM-PFI-018"
        ],
        "parameter_ids": [
          "PARAM-PFI-081",
          "PARAM-PFI-089",
          "PARAM-PFI-090",
          "PARAM-PFI-091",
          "PARAM-PFI-092"
        ],
        "primary_review_route": "/investment/holdings",
        "report_id": "pfi-v025-investment",
        "report_type": "investment",
        "review_entry_ids": [
          "REVIEW-SRC-HOLDINGS",
          "REVIEW-SRC-MARKET-PRICES",
          "REVIEW-SRC-FX-SNAPSHOT",
          "REVIEW-ECONOMIC-EVENT-ADAPTER"
        ],
        "scope_explanation_zh": "当前报告只使用已验证的真实来源覆盖，不把缺失输入解释为零。",
        "status": "blocked",
        "status_statement_zh": "关键真实输入未 ready；只展示公式、限制与复核入口。",
        "status_zh": "已阻断",
        "title_zh": "投资报告",
        "transaction_record_count": 8815
      },
      {
        "data_range": {
          "end": "2026-06-03",
          "start": "2022-06-06"
        },
        "financial_values_emitted": 0,
        "formula_ids": [
          "FORM-PFI-015",
          "FORM-PFI-020"
        ],
        "parameter_ids": [
          "PARAM-PFI-081",
          "PARAM-PFI-082",
          "PARAM-PFI-083",
          "PARAM-PFI-084",
          "PARAM-PFI-085",
          "PARAM-PFI-087",
          "PARAM-PFI-088"
        ],
        "primary_review_route": "/data/sources",
        "report_id": "pfi-v025-consumption",
        "report_type": "consumption",
        "review_entry_ids": [
          "REVIEW-SRC-TRANSACTIONS-ALIPAY",
          "REVIEW-ECONOMIC-EVENT-ADAPTER"
        ],
        "scope_explanation_zh": "消费总流出是用户定义的 gross activity 口径；生活消费、投资资金流出与投资域内配置必须拆分展示，投资活动不等于净资产损失。",
        "status": "partial",
        "status_statement_zh": "部分可算：只展示真实来源覆盖与非金额敏感性。",
        "status_zh": "部分可算",
        "title_zh": "消费报告",
        "transaction_record_count": 8815
      },
      {
        "data_range": {
          "end": "2026-06-03",
          "start": "2022-06-06"
        },
        "financial_values_emitted": 0,
        "formula_ids": [
          "FORM-PFI-019",
          "FORM-PFI-015"
        ],
        "parameter_ids": [
          "PARAM-PFI-081",
          "PARAM-PFI-082",
          "PARAM-PFI-083",
          "PARAM-PFI-084",
          "PARAM-PFI-085",
          "PARAM-PFI-086"
        ],
        "primary_review_route": "/data/sources",
        "report_id": "pfi-v025-cashflow",
        "report_type": "cashflow",
        "review_entry_ids": [
          "REVIEW-SRC-TRANSACTIONS-ALIPAY",
          "REVIEW-ECONOMIC-EVENT-ADAPTER"
        ],
        "scope_explanation_zh": "当前报告只使用已验证的真实来源覆盖，不把缺失输入解释为零。",
        "status": "partial",
        "status_statement_zh": "部分可算：只展示真实来源覆盖与非金额敏感性。",
        "status_zh": "部分可算",
        "title_zh": "现金流报告",
        "transaction_record_count": 8815
      }
    ],
    "report_count": 5,
    "review_cards": [
      {
        "action_label_zh": "复核交易来源覆盖与待复核队列",
        "label_zh": "支付宝交易流水（历史 Git object 只读来源）",
        "review_id": "REVIEW-SRC-TRANSACTIONS-ALIPAY",
        "review_route": "/data/sources",
        "status": "ready"
      },
      {
        "action_label_zh": "挂接并复核账户余额快照",
        "label_zh": "账户余额与期初/期末快照",
        "review_id": "REVIEW-SRC-ACCOUNT-BALANCES",
        "review_route": "/accounts/reconcile",
        "status": "not_loaded"
      },
      {
        "action_label_zh": "挂接并复核负债余额快照",
        "label_zh": "负债余额快照",
        "review_id": "REVIEW-SRC-LIABILITIES",
        "review_route": "/accounts/reconcile",
        "status": "not_loaded"
      },
      {
        "action_label_zh": "挂接并复核真实持仓快照",
        "label_zh": "真实持仓快照",
        "review_id": "REVIEW-SRC-HOLDINGS",
        "review_route": "/investment/holdings",
        "status": "not_loaded"
      },
      {
        "action_label_zh": "挂接并复核估值价格快照",
        "label_zh": "持仓估值价格快照",
        "review_id": "REVIEW-SRC-MARKET-PRICES",
        "review_route": "/investment/holdings",
        "status": "not_loaded"
      },
      {
        "action_label_zh": "挂接并复核生产 FX snapshot",
        "label_zh": "生产 FX snapshot",
        "review_id": "REVIEW-SRC-FX-SNAPSHOT",
        "review_route": "/settings/data-system",
        "status": "not_loaded"
      },
      {
        "action_label_zh": "复核 Economic Event 映射与缺失 lineage",
        "label_zh": "Economic Event lineage",
        "review_id": "REVIEW-ECONOMIC-EVENT-ADAPTER",
        "review_route": "/data/interconnection",
        "status": "blocked"
      }
    ],
    "schema": "PFIV025Stage9Phase92UIContractV1",
    "sensitivity_cards": [
      {
        "impact_summary_zh": "窗口增大时覆盖记录数单调不减；可比较覆盖变化与指纹。",
        "impact_visible": true,
        "observation_count": 7,
        "parameter_ids": [
          "PARAM-PFI-086"
        ],
        "review_route": "/reports/metric-drilldown?formula=FORM-PFI-019",
        "sensitivity_id": "SENS-CASHFLOW-WINDOW",
        "status": "partial_ready_nonfinancial_impact",
        "title_zh": "现金流窗口敏感性"
      },
      {
        "impact_summary_zh": "缺少逐笔 score vector 与 ground-truth labels，调整影响不可验证。",
        "impact_visible": false,
        "observation_count": 0,
        "parameter_ids": [
          "PARAM-PFI-087"
        ],
        "review_route": "/settings/parameters?parameter=PARAM-PFI-087",
        "sensitivity_id": "SENS-CLASSIFICATION-THRESHOLD",
        "status": "blocked_missing_scores",
        "title_zh": "分类阈值敏感性"
      },
      {
        "impact_summary_zh": "缺完整 dated funding/return/terminal-value chain，不预演 XIRR 数值。",
        "impact_visible": false,
        "observation_count": 0,
        "parameter_ids": [
          "PARAM-PFI-089",
          "PARAM-PFI-090",
          "PARAM-PFI-091",
          "PARAM-PFI-092"
        ],
        "review_route": "/reports/metric-drilldown?formula=FORM-PFI-018",
        "sensitivity_id": "SENS-XIRR-POLICY",
        "status": "blocked_insufficient_chain",
        "title_zh": "XIRR 参数敏感性"
      },
      {
        "impact_summary_zh": "余额、持仓、价格与 FX 未加载，不生成金额精度调整影响。",
        "impact_visible": false,
        "observation_count": 0,
        "parameter_ids": [
          "PARAM-PFI-081"
        ],
        "review_route": "/settings/parameters?parameter=PARAM-PFI-081",
        "sensitivity_id": "SENS-MONEY-QUANTUM",
        "status": "blocked_missing_required_sources",
        "title_zh": "金额精度与核心财务边界"
      }
    ],
    "subtitle_zh": "只展示当前可计算内容；公式、参数影响、模型限制与来源复核入口保持可见。",
    "title_zh": "财务分析与模型验证",
    "version": "v0.2.5"
  }
  );
  const SNAPSHOT_BINDING = deepFreeze(reviewedData?.snapshotBinding || LEGACY_SNAPSHOT_BINDING);
  const EMBEDDED_UI_CONTRACT = deepFreeze(reviewedData?.uiContract || LEGACY_EMBEDDED_UI_CONTRACT);

  function validatePhase92ViewModel(contract = EMBEDDED_UI_CONTRACT) {
    const errors = [];
    const reports = Array.isArray(contract?.report_cards) ? contract.report_cards : [];
    const formulas = Array.isArray(contract?.formula_cards) ? contract.formula_cards : [];
    const sensitivities = Array.isArray(contract?.sensitivity_cards) ? contract.sensitivity_cards : [];
    const models = Array.isArray(contract?.model_cards) ? contract.model_cards : [];
    const reviews = Array.isArray(contract?.review_cards) ? contract.review_cards : [];
    const components = Array.isArray(contract?.component_cards) ? contract.component_cards : [];
    if (contract?.schema !== "PFIV025Stage9ReviewedAnalysisUIContractV1") errors.push("schema mismatch");
    if (contract?.phase_id !== "V025-S9-WHOLE-REVIEW") errors.push("phase mismatch");
    if (contract?.version !== "v0.2.5") errors.push("version mismatch");
    if (contract?.report_count !== 5 || reports.length !== 5) errors.push("five reports required");
    if (formulas.length !== 6) errors.push("six formula cards required");
    if (sensitivities.length !== 4) errors.push("four sensitivity cards required");
    if (models.length !== 1) errors.push("one model card required");
    if (reviews.length !== 7) errors.push("seven review cards required");
    if (contract?.component_count !== 4 || components.length !== 4) errors.push("four component cards required");
    if (contract?.phase_9_3_candidate_complete !== true) errors.push("Phase 9.3 current state mismatch");
    if (contract?.stage_9_whole_stage_review_done !== false) errors.push("whole-stage review scope leak");
    if (contract?.stage_10_started !== false) errors.push("Stage 10 scope leak");
    if (contract?.automatic_trading_allowed !== false) errors.push("automatic trading is forbidden");
    if (contract?.financial_values_emitted !== 0) errors.push("financial values emitted");
    if (contract?.contains_private_values !== false) errors.push("private values emitted");

    const reportTypes = new Set();
    reports.forEach((report) => {
      const reportType = String(report?.report_type || "");
      if (reportTypes.has(reportType)) errors.push(`duplicate report type: ${reportType}`);
      reportTypes.add(reportType);
      if (REQUIRED_REPORT_STATUSES[reportType] !== report?.status) {
        errors.push(`truth status mismatch: ${reportType}`);
      }
      if (!String(report?.primary_review_route || "").startsWith("/")) {
        errors.push(`review route missing: ${reportType}`);
      }
      if (report?.financial_values_emitted !== 0) {
        errors.push(`report emitted financial values: ${reportType}`);
      }
    });
    Object.keys(REQUIRED_REPORT_STATUSES).forEach((reportType) => {
      if (!reportTypes.has(reportType)) errors.push(`report missing: ${reportType}`);
    });
    const requiredComponents = [
      "total_consumption_outflow_cny",
      "living_consumption_cny",
      "investment_funding_outflow_cny",
      "investment_allocation_amount_cny",
    ];
    if (canonicalJsonForComparison(components.map((item) => item?.metric_id).sort()) !== canonicalJsonForComparison([...requiredComponents].sort())) {
      errors.push("component identities mismatch");
    }
    components.forEach((item) => {
      if (item?.status !== "ready" || item?.financial_values_emitted !== 0 || item?.contains_private_values !== false) {
        errors.push(`component state invalid: ${item?.metric_id}`);
      }
      if (!String(item?.review_route || "").startsWith("/")) errors.push(`component review route missing: ${item?.metric_id}`);
    });
    for (const collection of [formulas, sensitivities, reviews]) {
      collection.forEach((item) => {
        if (!String(item?.review_route || "").startsWith("/")) {
          errors.push("actionable review route missing");
        }
      });
    }
    const hashes = contract?.hashes && typeof contract.hashes === "object" ? contract.hashes : {};
    for (const key of [
      "data_manifest_hash",
      "read_model_hash",
      "formula_registry_hash",
      "parameter_hash",
      "base_report_manifest_hash",
    ]) {
      if (!/^sha256:[0-9a-f]{64}$/.test(String(hashes[key] || ""))) {
        errors.push(`invalid hash: ${key}`);
      }
    }
    const serialized = JSON.stringify(contract);
    if (/\bCNY\s+-?[0-9]/.test(serialized)) errors.push("financial amount rendered");
    if (/"(?:value|amount|financial_value)"\s*:/.test(serialized)) errors.push("financial value field rendered");
    if (/"[a-z0-9_]+_cny"\s*:/.test(serialized)) errors.push("financial metric value rendered");

    return deepFreeze({
      schema: "PFIV025Stage9Phase92UIViewValidationV1",
      phaseId: "V025-S9-P9.2",
      status: errors.length ? "fail" : "pass",
      errors,
      reportCount: reports.length,
      formulaCount: formulas.length,
      sensitivityCount: sensitivities.length,
      modelCount: models.length,
      reviewCount: reviews.length,
      componentCount: components.length,
      blockedCount: reports.filter((item) => item.status === "blocked").length,
      partialCount: reports.filter((item) => item.status === "partial").length,
      financialValuesEmitted: Number(contract?.financial_values_emitted || 0),
      containsPrivateValues: contract?.contains_private_values === true,
    });
  }

  function buildPhase92ViewModel(contract = EMBEDDED_UI_CONTRACT) {
    const normalized = clone(contract);
    const validation = validatePhase92ViewModel(normalized);
    if (validation.status !== "pass") {
      throw new Error(`invalid PFI v0.2.5 Stage 9 Phase 9.2 UI contract: ${validation.errors.join("; ")}`);
    }
    return deepFreeze({
      ...normalized,
      page: "reports",
      kicker_zh: "Stage 9 整体审查 · 财务分析与模型验证",
      summary_zh: `5 份财务报告：${validation.blockedCount} 份阻断，${validation.partialCount} 份部分可算；${validation.componentCount} 项活动组件、6 条公式、4 组敏感性、1 张模型卡和 7 个来源复核入口可见。`,
      warning_zh: "缺失来源不解释为零；部分可算仅代表覆盖与非金额敏感性可验证，不等于完整财务结论。",
      validation,
      snapshot_binding: SNAPSHOT_BINDING,
    });
  }

  return deepFreeze({
    schema: "PFIV025Stage9ReviewedAnalysisUIAPIv1",
    version: "v0.2.5",
    phaseId: "V025-S9-WHOLE-REVIEW",
    embeddedSnapshot: () => EMBEDDED_UI_CONTRACT,
    snapshotBinding: SNAPSHOT_BINDING,
    buildPhase92ViewModel,
    validatePhase92ViewModel,
  });
});
