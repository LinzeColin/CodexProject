(function attachPFIStage9Settings(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V023_STAGE9_SETTINGS = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage9Settings() {
  const VERSION = "v0.2.3";
  const PHASE_ID = "V023-S9-P9.3";

  const TOGGLES = Object.freeze({
    haptic: Object.freeze({
      toggle_id: "haptic",
      label_zh: "触感反馈",
      default_enabled: true,
      off_state_zh: "关闭后保留视觉状态与文字反馈。",
      owner_visible_zh: "选择、确认、警示和阻断动作使用不同触感层级。",
    }),
    sound: Object.freeze({
      toggle_id: "sound",
      label_zh: "声音反馈",
      default_enabled: false,
      off_state_zh: "默认静音，不主动播放声音。",
      owner_visible_zh: "需要时只在设置页开启。",
    }),
    motion: Object.freeze({
      toggle_id: "motion",
      label_zh: "动效反馈",
      default_enabled: true,
      off_state_zh: "关闭后启用减少动画模式。",
      owner_visible_zh: "页面转场、加载和状态变化保持轻量。",
    }),
  });

  function buildStage9Phase93FeedbackSettingsViewModel() {
    return Object.freeze({
      schema: "PFIV023Stage9Phase93FeedbackSettingsViewModelV1",
      version: VERSION,
      stage: "Stage 9",
      phase_id: PHASE_ID,
      phase_name: "触感与设置隔离",
      page: "settings",
      route_alias: "/settings?tab=feedback",
      visible_on_workspaces: Object.freeze(["settings"]),
      business_pages_show_feedback_console: false,
      toggle_ids: Object.freeze(Object.keys(TOGGLES)),
      toggles: TOGGLES,
      isolation_policy: Object.freeze({
        feedback_preferences_surface_zh: "设置页反馈偏好",
        owner_path_zh: "设置 > 反馈偏好",
        action_zh: "在设置页管理触感、声音和动效开关。",
        hidden_outside_settings: true,
      }),
    });
  }

  function buildStage6Phase63FeedbackSettingsViewModel() {
    const toggles = Object.freeze({
      haptic: Object.freeze({
        ...TOGGLES.haptic,
        can_disable: true,
        unsupported_behavior: "silent_visual_degradation",
        capability_source: "navigator.vibrate",
      }),
      sound: Object.freeze({
        ...TOGGLES.sound,
        can_disable: true,
        unsupported_behavior: "silent_noop",
      }),
      motion: Object.freeze({
        ...TOGGLES.motion,
        can_disable: true,
        unsupported_behavior: "reduce_motion_visual_state",
      }),
    });
    return Object.freeze({
      schema: "PFIV024Stage6Phase63FeedbackSettingsViewModelV1",
      target_version: "v0.2.4",
      source_package_version: "v0.2.3-repair",
      stage: "Stage 6",
      phase_id: "6.3",
      phase_name: "触感与设置隔离",
      page: "settings",
      route_alias: "/settings?tab=feedback",
      visible_on_workspaces: Object.freeze(["settings"]),
      business_pages_show_feedback_console: false,
      toggle_ids: Object.freeze(Object.keys(toggles)),
      toggles,
      isolation_policy: Object.freeze({
        feedback_preferences_surface_zh: "设置页反馈偏好",
        owner_path_zh: "设置 > 反馈偏好",
        action_zh: "在设置页管理触感、声音和动效开关。",
        hidden_outside_settings: true,
      }),
    });
  }

  return Object.freeze({
    buildStage9Phase93FeedbackSettingsViewModel,
    buildStage6Phase63FeedbackSettingsViewModel,
  });
});
