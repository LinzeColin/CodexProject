import { Activity, Blocks, CalendarDays, Cloud, Home, LayoutDashboard, Network, Orbit, RefreshCw, Search } from "lucide-react";
import type { ComponentType } from "react";
import type { AtlasFilters, AtlasNode, ViewKey } from "../../types";
import { zhCNCopy } from "../../i18n/zh-CN";
import universeStateSample from "../../fixtures/universe_state.sample.json";
import { mapAtlasNodesToStarfield, mapUniverseStateSnapshotToStarfield, type StarfieldMappingResult } from "../../models/starfieldMapping";
import type { UniverseStateSnapshot } from "../../models/universeState";



export const uiCopy = zhCNCopy;


export const DEFAULT_MEMORY_ATLAS_VIEW: ViewKey = "home";


export const MEMORY_OVERVIEW_STRUCTURE_VERSION = "memory_overview_default_home.v1_1_7_stage3_phase1" as const;


export const MEMORY_OVERVIEW_OPERATION_VERSION = "memory_overview_detail_operations.v1_1_7_stage3_phase2" as const;


export const HOME_ARRIVAL_BRIEFING_VERSION = "home_arrival_briefing.v1_2_s10_p1" as const;


export const GLOBAL_CHINESE_UX_VERSION = "global_chinese_ux.v1_2_s10_p2" as const;


export const MACHINE_DETAIL_FOLDING_VERSION = "machine_detail_folding.v1_2_s10_p3" as const;


export const PRODUCT_IDENTITY_VERSION = "memory_atlas_product_identity.v1_2_r2" as const;


export const CLIO_LIKE_VISUALS_VERSION = "clio_like_visuals.v1_2_s11_p1" as const;


export const ECONOMIC_LIKE_VISUALS_VERSION = "economic_like_visuals.v1_2_s11_p2" as const;


export const WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION = "workflow_latent_governance_visuals.v1_2_s11_p3" as const;


export const HUMAN_QUESTION_MAP_VERSION = "human_question_map.v1_2_s11_p4" as const;


export const COMMAND_PALETTE_VERSION = "command_palette.v1_2_s12_p1" as const;


export const COMMAND_WORKFLOW_VERSION = "real_command_workflows.v1_2_r3" as const;


export const COMMAND_API_VERSION = "memory_atlas_command_api.v1_2_r3" as const;


export const PROPOSAL_WORKFLOW_VERSION = "memory_atlas_proposal_workflow.v1_2_r4" as const;


export const PROPOSAL_API_VERSION = "memory_atlas_proposal_api.v1_2_r4" as const;


export const OWNER_DAILY_UI_VERSION = "memory_atlas_owner_daily_ui.v1_2_r5" as const;


export const OWNER_DAILY_API_VERSION = "memory_atlas_owner_daily_api.v1_2_r5" as const;


export const OWNER_DAILY_RESULT_VERSION = "memory_atlas_owner_daily_result.v1_2_r5" as const;


export const LOCAL_APP_HANDOFF_URL = "http://127.0.0.1:4177" as const;


export const HOME_ACTION_SECTION_VERSION = "top_actions_section.v1_1_7_stage3_phase2" as const;


export const HOME_LEVEL_ASSET_SECTION_VERSION = "level_assets_section.v1_1_7_stage3_phase2" as const;


export const HOME_THEME_CATEGORY_SECTION_VERSION = "theme_categories_section.v1_1_7_stage3_phase2" as const;


export const STARFIELD_INTEGRATION_VERSION = "memory_starfield_integration.v1_1_7_stage4_phase3" as const;


export const DATA_MAP_STRUCTURE_MODEL_VERSION = "data_map_structure_model.v1_1_7_stage6_phase1" as const;


export const DATA_MAP_RELATION_EXPLANATION_VERSION = "data_map_relation_explanation.v1_1_7_stage6_phase1" as const;


export const DATA_MAP_DETAIL_PANEL_VERSION = "data_map_detail_panel.v1_1_7_stage6_phase2" as const;


export const DATA_MAP_PROPOSAL_ENTRY_VERSION = "data_map_proposal_entry.v1_1_7_stage6_phase2" as const;


export const SEARCH_2_0_RUNTIME_VERSION = "search_2_0_runtime.v1_1_7_stage7_phase1" as const;


export const SEARCH_2_0_SESSION_SUMMARY_VERSION = "search_2_0_session_summary.v1_1_7_stage7_phase1" as const;


export const REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION = "review_summary_iteration_runtime.v1_1_7_stage7_phase2" as const;


export const REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION = "memory_atlas_review_summary.v1_1_7_stage7_phase2" as const;


export const SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION = "summary_iteration_closure_runtime.v1_1_7_stage8_phase1" as const;


export const SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION = "memory_atlas_summary_closure.v1_1_7_stage8_phase1" as const;


export const CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION = "cross_board_shared_state.v1_1_7_stage9_phase1" as const;


export const INSPECTOR_EXPLANATION_LAYER_VERSION = "inspector_explanation_layer.v1_1_7_stage9_phase1" as const;


export const CROSS_BOARD_SHARED_STATE_SURFACES = [
  "home",
  "galaxy",
  "notion",
  "roi",
  "obsidian",
  "timeline",
  "contribution",
  "wordcloud",
  "search",
  "summary",
] as const;



export type CrossBoardSharedStateSurface = (typeof CROSS_BOARD_SHARED_STATE_SURFACES)[number];



export const MEMORY_OVERVIEW_SECTION_ORDER = [
  { id: "arrival_briefing", label: "上次来以后发生了什么" },
  { id: "status_summary", label: "状态摘要" },
  { id: "suggested_actions", label: "行动建议" },
  { id: "behavior_intelligence", label: "行为智能" },
  { id: "clio_like_visuals", label: "多维图谱" },
  { id: "economic_like_visuals", label: "经济图谱" },
  { id: "workflow_latent_governance_visuals", label: "治理图谱" },
  { id: "human_question_map", label: "问题地图" },
  { id: "weather", label: "记忆天气" },
  { id: "black_holes", label: "风险黑洞" },
  { id: "proto_stars", label: "新生机会" },
  { id: "assets", label: "层级资产" },
  { id: "themes", label: "主题结构" },
  { id: "entry_points", label: "探索入口" },
] as const;



export const HOME_LEVEL_ASSET_GROUPS = [
  { id: "core_profile", label: "核心画像" },
  { id: "project", label: "项目" },
  { id: "decision", label: "决策" },
  { id: "temporary", label: "临时" },
  { id: "stale", label: "过期" },
] as const;



export const HOME_THEME_CATEGORY_STATES = [
  { id: "rising", label: "上升" },
  { id: "declining", label: "下降" },
  { id: "conflict", label: "冲突" },
  { id: "opportunity", label: "机会" },
  { id: "stable", label: "稳定" },
] as const;



export const HOME_ARRIVAL_CATEGORY_LABELS = {
  new_material: "新增重要资料",
  strengthened: "增强结论",
  weakened: "减弱或过期结论",
  pending_proposal: "待授权提案",
  sync_failure: "同步失败",
} as const;



export const S12_P1_ACCEPTED_CORE_COMMAND_IDS = [
  "sync_chatgpt",
  "sync_codex",
  "generate_weekly_report",
  "view_pending_proposals",
] as const;


export const S12_P1_PERSONALIZATION_COMMAND_ID = "generate_personalization_prompt" as const;


export const S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID = "chatgpt_deep_explore" as const;


export const S12_P3_CHATGPT_DEEP_EXPLORE_VERSION = "chatgpt_deep_explore.v1_2_s12_p3" as const;


export const S12_P1_COMMAND_IDS = [...S12_P1_ACCEPTED_CORE_COMMAND_IDS, S12_P1_PERSONALIZATION_COMMAND_ID, S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID] as const;


export const S12_P1_PERSONALIZATION_TARGETS = ["chatgpt", "codex", "other_agent"] as const;


export const OWNER_DAILY_STEP_IDS = [
  "sync",
  "analyze",
  "build-atlas",
  "audit",
  "push",
  "proposals",
  "generate-personalization-prompt",
  "deep-explore",
] as const;



export type S12P1CoreCommandId = (typeof S12_P1_ACCEPTED_CORE_COMMAND_IDS)[number];


export type S12P1CommandId = (typeof S12_P1_COMMAND_IDS)[number];


export type OwnerDailyStepId = (typeof OWNER_DAILY_STEP_IDS)[number];



export interface CommandPaletteCommand {
  id: S12P1CommandId;
  label: string;
  description: string;
  humanAction: string;
  dryRunCommand: string;
  status: string;
  viewTarget: ViewKey | null;
  personalizationTargets?: typeof S12_P1_PERSONALIZATION_TARGETS;
}



export interface CommandPaletteModel {
  version: typeof COMMAND_PALETTE_VERSION;
  commands: CommandPaletteCommand[];
  commandIds: S12P1CommandId[];
  acceptedCoreCommandIds: S12P1CoreCommandId[];
  personalizationTargets: typeof S12_P1_PERSONALIZATION_TARGETS;
  pendingProposalCount: number;
  weeklyReportNodeCount: number;
  latestDateLabel: string;
}



export type CommandExecutionStatus = "idle" | "running" | "success" | "needs_input" | "error" | "local_required";



export interface CommandWorkflowAction {
  type: "reload_atlas" | "navigate_view" | "open_url";
  view?: ViewKey;
  url?: string;
}



export interface CommandWorkflowResult {
  schema_version: "memory_atlas_command_result.v1_2_r3";
  command_id: S12P1CommandId;
  status: "success" | "needs_input" | "error";
  title_zh: string;
  message_zh: string;
  outputs: string[];
  input_hint_zh?: string;
  action?: CommandWorkflowAction;
  proposal_review?: ProposalReviewPayload;
  safety: {
    sends_to_chatgpt: false;
    auto_submit?: false;
    canonical_repo_mutation?: false;
  };
}



export interface OwnerDailyStepResult {
  step_id: OwnerDailyStepId;
  order: number;
  label_zh: string;
  status: "pass" | "failed";
  conclusion_zh: string;
  failure_zh: string;
  retryable: boolean;
  duration_ms: number;
  invocation: string[];
  metrics: Record<string, string | number | boolean | Array<string | number | boolean>>;
}



export interface OwnerDailyResult {
  schema_version: typeof OWNER_DAILY_RESULT_VERSION;
  api_version: typeof OWNER_DAILY_API_VERSION;
  action: "run" | "retry";
  requested_step_id?: OwnerDailyStepId;
  status: "PASS" | "PARTIAL_FAILURE";
  profile: "owner-daily";
  dry_run: true;
  conclusion_zh: string;
  completed_count: number;
  failed_count: number;
  retryable_step_ids: OwnerDailyStepId[];
  steps: OwnerDailyStepResult[];
  safety: {
    writes_files: false;
    remote_push: false;
    raw_mutation: false;
    sends_to_chatgpt: false;
    proposal_apply_execution: false;
    canonical_repo_mutation: false;
  };
}



export interface ProposalNarrator {
  what_changed_zh: string;
  why_changed_zh: string;
  affected_surfaces_zh: string;
  how_to_verify_zh: string;
  how_to_rollback_zh: string;
}



export interface ProposalReviewItem {
  proposal_id: string;
  current_state: string;
  target_type: string;
  target_files: string[];
  risk_level: string;
  expires_at: string;
  action_half_life: string;
  human_reason_zh: string;
  narrator: ProposalNarrator;
  validation_ids: string[];
  rollback_plan_zh: string;
  apply_ready: boolean;
  blocked_reason_zh: string;
  review_token?: string;
}



export interface ProposalReviewTransaction {
  transaction_id: string;
  proposal_id: string;
  state: "committed" | "manual_rollback_required";
  target_files: string[];
  rollback_token: string;
}



export interface ProposalReviewPayload {
  schema_version: "memory_atlas_proposal_review.v1_2_r4";
  status: "success";
  proposal_api_version: typeof PROPOSAL_API_VERSION;
  proposals: ProposalReviewItem[];
  transactions: ProposalReviewTransaction[];
  summary: {
    proposal_count: number;
    apply_ready_count: number;
    review_only_count: number;
    rollback_available_count: number;
    interrupted_recovery_count: number;
    manual_recovery_required_count: number;
  };
  safety: {
    raw_mutation: false;
    canonical_repo_mutation: false;
    remote_push: false;
    operation_content_returned: false;
  };
}



export interface ProposalActionResult {
  schema_version: "memory_atlas_proposal_result.v1_2_r4";
  action: "approve_apply" | "rollback";
  status: "success" | "validation_failed_rolled_back";
  state: "committed" | "rollback_or_needs_revision" | "rolled_back_by_human";
  proposal_id: string;
  transaction_id: string;
  message_zh: string;
  state_history?: string[];
  validation_ids?: string[];
  validation_results?: Array<{ validation_id: string; status: "PASS" | "FAIL" }>;
  automatic_rollback?: boolean;
  rollback_available?: boolean;
  rollback_token?: string;
  safety: {
    human_approval_required: true;
    raw_mutation: false;
    canonical_repo_mutation: false;
    remote_push: false;
  };
}



export interface CommandExecutionState {
  commandId: S12P1CommandId | null;
  status: CommandExecutionStatus;
  title: string;
  message: string;
  outputs: string[];
  inputHint: string;
  fallbackUrl: string;
  navigationView: ViewKey | null;
}



export const views: Array<{ key: ViewKey; label: string; icon: ComponentType<{ size?: number }> }> = [
  { key: "home", label: uiCopy.navigation.views.home, icon: Home },
  { key: "galaxy", label: uiCopy.navigation.views.galaxy, icon: Orbit },
  { key: "notion", label: uiCopy.navigation.views.notion, icon: Blocks },
  { key: "roi", label: uiCopy.navigation.views.roi, icon: LayoutDashboard },
  { key: "obsidian", label: uiCopy.navigation.views.obsidian, icon: Network },
  { key: "timeline", label: uiCopy.navigation.views.timeline, icon: CalendarDays },
  { key: "contribution", label: uiCopy.navigation.views.contribution, icon: Activity },
  { key: "wordcloud", label: uiCopy.navigation.views.wordcloud, icon: Cloud },
  { key: "search", label: uiCopy.navigation.views.search, icon: Search },
  { key: "summary", label: uiCopy.navigation.views.summary, icon: RefreshCw },
];



export const navigationGroups: Array<{
  id: "judgment" | "exploration" | "reflection";
  label: string;
  question: string;
  viewKeys: ViewKey[];
}> = [
  { id: "judgment", label: "判断", question: "我现在应该先判断什么", viewKeys: ["home", "summary"] },
  { id: "exploration", label: "探索", question: "我需要从哪里找证据", viewKeys: ["galaxy", "notion", "timeline", "search"] },
  { id: "reflection", label: "复盘", question: "哪里值得投入或降噪", viewKeys: ["roi", "obsidian", "contribution", "wordcloud"] },
];



export const visualFocusViews: ViewKey[] = ["home", "galaxy", "notion", "roi", "obsidian", "timeline", "contribution", "wordcloud", "summary"];



export const defaultFilters: AtlasFilters = {
  query: "",
  source: "all",
  tier: "all",
  category: "all",
  theme: "all",
};



export function buildGalaxyStarfieldMapping(nodes: AtlasNode[]): StarfieldMappingResult {
  try {
    return mapUniverseStateSnapshotToStarfield(universeStateSample as UniverseStateSnapshot, nodes); // source: "universe_state_snapshot"
  } catch {
    return mapAtlasNodesToStarfield(nodes); // source: "atlas_nodes"
  }
}
