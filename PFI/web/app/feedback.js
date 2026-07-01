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
  const V024_TARGET_VERSION = "v0.2.4";
  const STAGE6_PHASE62_ID = "6.2";
  const PHASE92_ID = "V023-S9-P9.2";
  const PHASE93_ID = "V023-S9-P9.3";

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

  const HAPTIC_LEVELS = Object.freeze([
    Object.freeze({
      level_id: "select",
      label_zh: "选择反馈",
      intent_zh: "切换标签、打开二级入口或选中轻量控件。",
      pattern_ms: Object.freeze([12]),
    }),
    Object.freeze({
      level_id: "confirm",
      label_zh: "确认反馈",
      intent_zh: "保存设置、完成导入检查或生成可复核结果。",
      pattern_ms: Object.freeze([24, 20, 24]),
    }),
    Object.freeze({
      level_id: "warning",
      label_zh: "警示反馈",
      intent_zh: "数据过期、字段缺失或需要复核。",
      pattern_ms: Object.freeze([36, 18, 36]),
    }),
    Object.freeze({
      level_id: "blocked",
      label_zh: "阻断反馈",
      intent_zh: "真实数据缺失、路径不可读或操作被阻断。",
      pattern_ms: Object.freeze([60, 30, 60]),
    }),
  ]);

  const V024_PHASE62_FEEDBACK_STATES = Object.freeze([
    Object.freeze({
      state: "loading",
      label_zh: "正在加载",
      action_zh: "显示骨架屏和当前步骤，避免空白等待。",
      aria_live: "polite",
      max_motion_ms: 180,
      css_selector: '[data-v024-motion-state="loading"]',
    }),
    Object.freeze({
      state: "progress",
      label_zh: "正在处理",
      action_zh: "显示保存、刷新或报告生成的进度状态。",
      aria_live: "polite",
      max_motion_ms: 180,
      css_selector: '[data-v024-motion-state="progress"]',
    }),
    Object.freeze({
      state: "success",
      label_zh: "已完成",
      action_zh: "用轻量视觉确认保留下一步入口。",
      aria_live: "polite",
      max_motion_ms: 180,
      css_selector: '[data-v024-motion-state="success"]',
    }),
    Object.freeze({
      state: "error",
      label_zh: "处理失败",
      action_zh: "高亮失败原因和可重试动作。",
      aria_live: "assertive",
      max_motion_ms: 200,
      css_selector: '[data-v024-motion-state="error"]',
    }),
    Object.freeze({
      state: "blocked",
      label_zh: "已阻断",
      action_zh: "说明缺失数据、路径或权限阻断，不补造结果。",
      aria_live: "assertive",
      max_motion_ms: 200,
      css_selector: '[data-v024-motion-state="blocked"]',
    }),
  ]);

  function buildStage6Phase62MotionContract() {
    return Object.freeze({
      schema: "PFIV024Stage6Phase62MotionContractV1",
      target_version: V024_TARGET_VERSION,
      source_package_version: "v0.2.3-repair",
      stage: "Stage 6",
      phase_id: STAGE6_PHASE62_ID,
      phase_name: "动效反馈",
      current_phase_only: true,
      max_one_phase_per_run: true,
      task_ids: Object.freeze(["T6.2.1", "T6.2.2", "T6.2.3", "T6.2.4"]),
      stage_contract: Object.freeze({
        phase_6_1_complete: true,
        phase_6_2_complete: true,
        phase_6_3_started: false,
        stage_6_whole_review_complete: false,
        github_main_uploaded: false,
      }),
      changed_in_this_phase: Object.freeze([
        "PFI/web/index.html",
        "PFI/web/styles.css",
        "PFI/web/app/shell.js",
        "PFI/web/app/feedback.js",
        "PFI/tests/test_v024_stage6_phase62_motion_feedback.py",
        "PFI/docs/pfi_v024/STAGE6_MOTION_FEEDBACK.md",
        "PFI/reports/pfi_v024/stage_6/phase_6_2/*",
      ]),
      explicitly_not_done: Object.freeze([
        "Phase 6.3 haptics and settings isolation",
        "Stage 6 whole-stage review",
        "GitHub main upload",
        "App bundle reinstall",
        "Financial data mutation or synthesis",
      ]),
    });
  }

  function buildStage6Phase62ReportProgressViewModel() {
    return Object.freeze({
      schema: "PFIV024Stage6Phase62ReportProgressV1",
      target_version: V024_TARGET_VERSION,
      stage: "Stage 6",
      phase_id: STAGE6_PHASE62_ID,
      title_zh: "报告生成进度",
      steps: Object.freeze([
        Object.freeze({
          step_id: "scope",
          label_zh: "准备报告范围",
          state: "loading",
          detail_zh: "确认报告类型、时间范围、账户和数据对象。",
        }),
        Object.freeze({
          step_id: "data_status",
          label_zh: "检查真实数据状态",
          state: "blocked",
          detail_zh: "识别未加载、来源缺失、过期快照、路径错误和需要复核状态。",
        }),
        Object.freeze({
          step_id: "formula_parameters",
          label_zh: "计算公式与参数",
          state: "loading",
          detail_zh: "展示公式、参数、数据范围和样本量，不补齐缺失财务值。",
        }),
        Object.freeze({
          step_id: "reviewable_output",
          label_zh: "生成可复核结果",
          state: "success",
          detail_zh: "输出结论、缺口、异常项和下一步动作。",
        }),
      ]),
    });
  }

  function buildStage6Phase62MotionFeedbackModel() {
    return Object.freeze({
      schema: "PFIV024Stage6Phase62MotionFeedbackModelV1",
      target_version: V024_TARGET_VERSION,
      source_package_version: "v0.2.3-repair",
      stage: "Stage 6",
      phase_id: STAGE6_PHASE62_ID,
      phase_name: "动效反馈",
      page_transition: Object.freeze({
        duration_ms: 180,
        max_duration_ms: 220,
        easing: "cubic-bezier(0.2, 0, 0, 1)",
        route_state_attribute: "data-v024-route-transition",
        enter_value: "enter",
        exit_value: "exit",
      }),
      loading_skeleton: Object.freeze({
        css_selector: ".v024-skeleton-row",
        delay_ms: 300,
        purpose_zh: "加载超过 300ms 时显示结构骨架，避免空白页面。",
      }),
      feedback_states: V024_PHASE62_FEEDBACK_STATES,
      report_generation_progress: buildStage6Phase62ReportProgressViewModel(),
      reduced_motion: Object.freeze({
        supported: true,
        selectors: Object.freeze(["@media (prefers-reduced-motion: reduce)", "body.reduce-motion"]),
        disables: Object.freeze(["page transition", "skeleton sheen", "progress step pulse"]),
      }),
      phase_6_3_haptics_settings_started: false,
    });
  }

  function buildStage6Phase63HapticsContract() {
    return Object.freeze({
      schema: "PFIV024Stage6Phase63HapticsContractV1",
      target_version: V024_TARGET_VERSION,
      source_package_version: "v0.2.3-repair",
      stage: "Stage 6",
      phase_id: "6.3",
      phase_name: "触感与设置隔离",
      current_phase_only: true,
      max_one_phase_per_run: true,
      task_ids: Object.freeze(["T6.3.1", "T6.3.2", "T6.3.3"]),
      stage_contract: Object.freeze({
        phase_6_1_complete: true,
        phase_6_2_complete: true,
        phase_6_3_complete: true,
        stage_6_whole_review_complete: false,
        github_main_uploaded: false,
      }),
      changed_in_this_phase: Object.freeze([
        "PFI/web/index.html",
        "PFI/web/app/feedback.js",
        "PFI/web/app/pages/settings.js",
        "PFI/web/app/shell.js",
        "PFI/tests/test_v024_stage6_phase63_haptics_settings.py",
        "PFI/docs/pfi_v024/STAGE6_HAPTICS_SETTINGS.md",
        "PFI/reports/pfi_v024/stage_6/phase_6_3/*",
      ]),
      explicitly_not_done: Object.freeze([
        "Stage 6 whole-stage review",
        "GitHub main upload",
        "App bundle reinstall",
        "Financial data mutation or synthesis",
      ]),
    });
  }

  function detectStage6Phase63HapticCapability(environment = {}) {
    const nav =
      environment.navigator ||
      (typeof navigator !== "undefined" && typeof navigator === "object" ? navigator : null);
    const canVibrate = Boolean(nav && typeof nav.vibrate === "function");
    return Object.freeze({
      source: "navigator.vibrate",
      can_vibrate: canVibrate,
      supported_device_only: true,
      reason_zh: canVibrate ? "当前浏览器支持 navigator.vibrate。" : "当前浏览器不支持触感震动，静默降级为视觉反馈。",
    });
  }

  function buildStage6Phase63HapticsModel(environment = {}) {
    const capability = detectStage6Phase63HapticCapability(environment);
    return Object.freeze({
      schema: "PFIV024Stage6Phase63HapticsModelV1",
      target_version: V024_TARGET_VERSION,
      source_package_version: "v0.2.3-repair",
      stage: "Stage 6",
      phase_id: "6.3",
      phase_name: "触感与设置隔离",
      capability,
      supported_device_only: true,
      levels: HAPTIC_LEVELS,
      preferences: Object.freeze({
        can_disable: true,
        default_enabled: true,
        stored_in: "settings_feedback_preferences",
        setting_route: "/settings?tab=feedback",
        off_state_zh: "关闭后保留视觉状态与文字反馈。",
      }),
      silent_degradation: Object.freeze({
        enabled: true,
        degrade_to: "visual_feedback",
        reason_zh: capability.can_vibrate ? "支持设备使用触感反馈。" : "不支持设备不报错、不提示失败，只保留视觉反馈。",
      }),
      settings_isolation: Object.freeze({
        visible_on_workspaces: Object.freeze(["settings"]),
        business_pages_show_feedback_console: false,
        settings_route: "/settings?tab=feedback",
      }),
    });
  }

  function buildStage9Phase92Contract() {
    return Object.freeze({
      version: VERSION,
      stage: "Stage 9",
      phase_id: PHASE92_ID,
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
      phase_id: PHASE92_ID,
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

  function buildStage9Phase93Contract() {
    return Object.freeze({
      version: VERSION,
      stage: "Stage 9",
      phase_id: PHASE93_ID,
      phase_name: "触感与设置隔离",
      current_phase_only: true,
      max_one_phase_per_run: true,
      task_ids: Object.freeze(["T9.3.1", "T9.3.2", "T9.3.3", "T9.3.4"]),
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
        "PFI/web/app/feedback.js",
        "PFI/web/app/pages/settings.js",
        "PFI/tests/test_v023_stage9_visual_feedback.py",
        "PFI/docs/pfi_v023/STAGE9_VISUAL_FEEDBACK.md",
        "PFI/reports/pfi_v023/stage_9/phase_9_3/*",
      ]),
      stage_contract: Object.freeze({
        phase_9_1_design_system_done: true,
        phase_9_2_motion_feedback_done: true,
        phase_9_3_haptics_settings_done: true,
        stage_9_whole_review_done: false,
        github_main_upload_done: false,
      }),
      explicitly_not_done: Object.freeze([
        "Stage 9 whole-stage review",
        "GitHub main upload for intermediate phase",
        "Stage 10 end-to-end app and browser acceptance",
      ]),
    });
  }

  function detectHapticCapability(environment = {}) {
    const nav =
      environment.navigator ||
      (typeof navigator !== "undefined" && typeof navigator === "object" ? navigator : null);
    const canVibrate = Boolean(nav && typeof nav.vibrate === "function");
    return Object.freeze({
      source: "navigator.vibrate",
      can_vibrate: canVibrate,
      reason_zh: canVibrate ? "当前浏览器支持触感震动能力。" : "当前浏览器不支持触感震动，自动降级为视觉反馈。",
    });
  }

  function buildHapticFeedbackModel(environment = {}) {
    return Object.freeze({
      schema: "PFIV023Stage9Phase93HapticModelV1",
      version: VERSION,
      stage: "Stage 9",
      phase_id: PHASE93_ID,
      phase_name: "触感与设置隔离",
      capability: detectHapticCapability(environment),
      levels: HAPTIC_LEVELS,
      preferences: Object.freeze({
        can_disable: true,
        default_enabled: true,
        stored_in: "settings_feedback_preferences",
        setting_route: "/settings?tab=feedback",
        off_state_zh: "关闭后保留视觉状态与文字反馈。",
      }),
      degrade_to: "visual_feedback",
      settings_isolation: Object.freeze({
        visible_on_workspaces: Object.freeze(["settings"]),
        business_pages_show_feedback_console: false,
        settings_route: "/settings?tab=feedback",
      }),
    });
  }

  return Object.freeze({
    buildStage6Phase62MotionContract,
    buildStage6Phase62MotionFeedbackModel,
    buildStage6Phase62ReportProgressViewModel,
    buildStage6Phase63HapticsContract,
    buildStage6Phase63HapticsModel,
    detectStage6Phase63HapticCapability,
    buildStage9Phase92Contract,
    buildStage9Phase92FeedbackModel,
    buildStage9Phase93Contract,
    buildHapticFeedbackModel,
    buildReportProgressViewModel,
    buildFeedbackComponentState,
    detectHapticCapability,
  });
});
