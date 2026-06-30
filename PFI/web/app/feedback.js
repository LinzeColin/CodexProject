(function attachPFIStage9Feedback(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V023_STAGE9_FEEDBACK = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage9Feedback() {
  const VERSION = "v0.2.3";
  const PHASE_ID = "V023-S9-P9.2";

  const FEEDBACK_STATES = Object.freeze([
    Object.freeze({
      state: "loading",
      label_zh: "处理中",
      action_zh: "显示骨架屏、当前步骤和可返回入口。",
      aria_live: "polite",
      css_selector: '[data-feedback-state="loading"]',
    }),
    Object.freeze({
      state: "success",
      label_zh: "已完成",
      action_zh: "显示结果摘要，并保留可撤销或返回入口。",
      aria_live: "polite",
      css_selector: '[data-feedback-state="success"]',
    }),
    Object.freeze({
      state: "error",
      label_zh: "处理失败",
      action_zh: "高亮错误区域，显示中文原因和下一步动作。",
      aria_live: "assertive",
      css_selector: '[data-feedback-state="error"]',
    }),
    Object.freeze({
      state: "blocked",
      label_zh: "已阻断",
      action_zh: "聚焦阻断卡片，说明缺失数据、过期状态或权限问题。",
      aria_live: "assertive",
      css_selector: '[data-feedback-state="blocked"]',
    }),
  ]);

  function buildStage9Phase92Contract() {
    return Object.freeze({
      version: VERSION,
      stage: "Stage 9",
      phase_id: PHASE_ID,
      phase_name: "动效反馈",
      current_phase_only: true,
      max_one_phase_per_run: true,
      task_ids: Object.freeze(["T9.2.1", "T9.2.2", "T9.2.3", "T9.2.4"]),
      allowed_files: Object.freeze([
        "PFI/web/styles.css",
        "PFI/web/app/theme.js",
        "PFI/web/app/feedback.js",
        "PFI/web/app/pages/settings.js",
        "PFI/tests/test_v023_stage9_visual_feedback.py",
        "PFI/docs/pfi_v023/STAGE9_VISUAL_FEEDBACK.md",
        "PFI/reports/pfi_v023/stage_9/*",
      ]),
      changed_in_this_phase: Object.freeze([
        "PFI/web/styles.css",
        "PFI/web/app/feedback.js",
        "PFI/tests/test_v023_stage9_visual_feedback.py",
        "PFI/docs/pfi_v023/STAGE9_VISUAL_FEEDBACK.md",
        "PFI/reports/pfi_v023/stage_9/phase_9_2/*",
      ]),
      stage_contract: Object.freeze({
        phase_9_1_design_system_done: true,
        phase_9_2_motion_feedback_done: true,
        phase_9_3_haptics_settings_done: false,
        stage_9_whole_review_done: false,
        github_main_upload_done: false,
      }),
      explicitly_not_done: Object.freeze([
        "Phase 9.3 触感与设置隔离",
        "Stage 9 whole-stage review",
        "GitHub main upload for intermediate phase",
      ]),
    });
  }

  function buildStage9Phase92FeedbackModel() {
    return Object.freeze({
      schema: "PFIV023Stage9Phase92FeedbackModelV1",
      version: VERSION,
      stage: "Stage 9",
      phase_id: PHASE_ID,
      phase_name: "动效反馈",
      page_transition: Object.freeze({
        duration_ms: 180,
        max_duration_ms: 220,
        easing: "cubic-bezier(0.2, 0, 0, 1)",
        route_state_attribute: "data-route-transition",
        enter_value: "enter",
        exit_value: "exit",
        css_selectors: Object.freeze([
          '.workspace[data-route-transition="enter"]',
          '.workspace[data-route-transition="exit"]',
        ]),
      }),
      feedback_states: FEEDBACK_STATES,
      report_generation_progress: buildReportProgressViewModel(),
      reduced_motion: Object.freeze({
        prefers_reduced_motion_supported: true,
        media_query: "(prefers-reduced-motion: reduce)",
        selectors: Object.freeze(["@media (prefers-reduced-motion: reduce)", "body.reduce-motion"]),
        disables: Object.freeze(["page transition", "skeleton pulse", "progress step animation"]),
      }),
      phase_9_3_haptics_settings_started: false,
    });
  }

  function buildReportProgressViewModel() {
    return Object.freeze({
      schema: "PFIV023ReportProgressV1",
      title_zh: "报告生成进度",
      states: Object.freeze(["loading", "success", "error", "blocked"]),
      steps: Object.freeze([
        Object.freeze({
          step_id: "scope",
          label_zh: "准备报告范围",
          state: "loading",
          detail_zh: "确认报告类型、时间范围和目标页面。",
        }),
        Object.freeze({
          step_id: "data_status",
          label_zh: "检查真实数据状态",
          state: "blocked",
          detail_zh: "识别未加载、过期、解析失败、路径错误和需要复核状态。",
        }),
        Object.freeze({
          step_id: "formula_parameters",
          label_zh: "计算公式与参数",
          state: "loading",
          detail_zh: "展示公式、参数、数据范围和样本量，不补齐缺失财务值。",
        }),
        Object.freeze({
          step_id: "reviewable_report",
          label_zh: "生成可复核报告",
          state: "success",
          detail_zh: "输出结论、缺口、异常项和下一步动作。",
        }),
      ]),
    });
  }

  function normalizeFeedbackState(state) {
    return FEEDBACK_STATES.some((item) => item.state === state) ? state : "loading";
  }

  function buildFeedbackComponentState(state, messageZh) {
    const normalizedState = normalizeFeedbackState(state);
    const config = FEEDBACK_STATES.find((item) => item.state === normalizedState);
    return Object.freeze({
      state: normalizedState,
      label_zh: config.label_zh,
      message_zh: messageZh || config.action_zh,
      role: normalizedState === "error" || normalizedState === "blocked" ? "alert" : "status",
      aria_live: config.aria_live,
      css_selector: config.css_selector,
    });
  }

  return Object.freeze({
    buildStage9Phase92Contract,
    buildStage9Phase92FeedbackModel,
    buildReportProgressViewModel,
    buildFeedbackComponentState,
  });
});
