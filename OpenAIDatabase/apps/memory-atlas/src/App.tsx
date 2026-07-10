import {
  Activity,
  Blocks,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Cloud,
  Crosshair,
  Download,
  FilterX,
  GitBranch,
  Home,
  LayoutDashboard,
  Network,
  Orbit,
  Pause,
  Play,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import type { ComponentType, CSSProperties, KeyboardEvent, PointerEvent, ReactNode, WheelEvent } from "react";
import { Suspense, lazy, useCallback, useEffect, useMemo, useReducer, useState } from "react";
import {
  emptyAtlas,
  filterMemoryNodes,
  getMemoryNodes,
  getNodeMap,
  getThemeNodes,
  loadMemoryAtlas,
  metricValues,
  normalizeMemoryTier,
  uniqueSorted,
  visibleGraphFor,
} from "./data/atlas";
import {
  DEFAULT_TIMELINE_RENDERER_MODE,
  getInitialGalaxyRendererMode,
  getInitialTimelineRendererMode,
  persistGalaxyRendererMode,
  persistTimelineRendererMode,
  TIMELINE_RENDERER_FEATURE_FLAG_VERSION,
  type GalaxyRendererMode,
  type TimelineRendererMode,
} from "./config/visualFlags";
import type { ActivityBucket, AtlasEdge, AtlasFilters, AtlasMetric, AtlasNode, DataSourceSummary, MemoryAtlas, ViewKey } from "./types";
import {
  atlasFiltersFromSharedState,
  createSharedAtlasState,
  sharedAtlasReducer,
  sharedContributionSelection,
  type SharedAtlasState,
  type SharedTimelineTimeRangeSelection,
} from "./state/sharedAtlasState";
import { EmptyState } from "./components/EmptyState";
import { ErrorState } from "./components/ErrorState";
import { ActionDetailDrawer, type HomeActionDetail } from "./components/ActionDetailDrawer";
import { AssetDetailPanel, type TierAssetDetail } from "./components/AssetDetailPanel";
import { ProposalEditor } from "./components/ProposalEditor";
import { ThemeDetailPanel, type TopicClassificationDetail } from "./components/ThemeDetailPanel";
import { MemoryAtlasHelpPanel } from "./components/help/MemoryAtlasHelpPanel";
import { zhCNCopy } from "./i18n/zh-CN";
import universeStateSample from "./fixtures/universe_state.sample.json";
import {
  mapAtlasNodesToStarfield,
  mapUniverseStateSnapshotToStarfield,
  STARFIELD_MAPPING_VERSION,
  type StarfieldMappingResult,
} from "./models/starfieldMapping";
import type { UniverseStateSnapshot } from "./models/universeState";

const GalaxyScene = lazy(() => import("./components/GalaxyScene").then((module) => ({ default: module.GalaxyScene })));
const ObsidianGraphScene = lazy(() => import("./components/ObsidianGraphScene").then((module) => ({ default: module.ObsidianGraphScene })));

const uiCopy = zhCNCopy;
const DEFAULT_MEMORY_ATLAS_VIEW: ViewKey = "home";
const MEMORY_OVERVIEW_STRUCTURE_VERSION = "memory_overview_default_home.v1_1_7_stage3_phase1" as const;
const MEMORY_OVERVIEW_OPERATION_VERSION = "memory_overview_detail_operations.v1_1_7_stage3_phase2" as const;
const HOME_ARRIVAL_BRIEFING_VERSION = "home_arrival_briefing.v1_2_s10_p1" as const;
const GLOBAL_CHINESE_UX_VERSION = "global_chinese_ux.v1_2_s10_p2" as const;
const MACHINE_DETAIL_FOLDING_VERSION = "machine_detail_folding.v1_2_s10_p3" as const;
const PRODUCT_IDENTITY_VERSION = "memory_atlas_product_identity.v1_2_r2" as const;
const CLIO_LIKE_VISUALS_VERSION = "clio_like_visuals.v1_2_s11_p1" as const;
const ECONOMIC_LIKE_VISUALS_VERSION = "economic_like_visuals.v1_2_s11_p2" as const;
const WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION = "workflow_latent_governance_visuals.v1_2_s11_p3" as const;
const HUMAN_QUESTION_MAP_VERSION = "human_question_map.v1_2_s11_p4" as const;
const COMMAND_PALETTE_VERSION = "command_palette.v1_2_s12_p1" as const;
const COMMAND_WORKFLOW_VERSION = "real_command_workflows.v1_2_r3" as const;
const COMMAND_API_VERSION = "memory_atlas_command_api.v1_2_r3" as const;
const LOCAL_APP_HANDOFF_URL = "http://127.0.0.1:4177" as const;
const HOME_ACTION_SECTION_VERSION = "top_actions_section.v1_1_7_stage3_phase2" as const;
const HOME_LEVEL_ASSET_SECTION_VERSION = "level_assets_section.v1_1_7_stage3_phase2" as const;
const HOME_THEME_CATEGORY_SECTION_VERSION = "theme_categories_section.v1_1_7_stage3_phase2" as const;
const STARFIELD_INTEGRATION_VERSION = "memory_starfield_integration.v1_1_7_stage4_phase3" as const;
const DATA_MAP_STRUCTURE_MODEL_VERSION = "data_map_structure_model.v1_1_7_stage6_phase1" as const;
const DATA_MAP_RELATION_EXPLANATION_VERSION = "data_map_relation_explanation.v1_1_7_stage6_phase1" as const;
const DATA_MAP_DETAIL_PANEL_VERSION = "data_map_detail_panel.v1_1_7_stage6_phase2" as const;
const DATA_MAP_PROPOSAL_ENTRY_VERSION = "data_map_proposal_entry.v1_1_7_stage6_phase2" as const;
const SEARCH_2_0_RUNTIME_VERSION = "search_2_0_runtime.v1_1_7_stage7_phase1" as const;
const SEARCH_2_0_SESSION_SUMMARY_VERSION = "search_2_0_session_summary.v1_1_7_stage7_phase1" as const;
const REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION = "review_summary_iteration_runtime.v1_1_7_stage7_phase2" as const;
const REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION = "memory_atlas_review_summary.v1_1_7_stage7_phase2" as const;
const SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION = "summary_iteration_closure_runtime.v1_1_7_stage8_phase1" as const;
const SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION = "memory_atlas_summary_closure.v1_1_7_stage8_phase1" as const;
const CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION = "cross_board_shared_state.v1_1_7_stage9_phase1" as const;
const INSPECTOR_EXPLANATION_LAYER_VERSION = "inspector_explanation_layer.v1_1_7_stage9_phase1" as const;
const CROSS_BOARD_SHARED_STATE_SURFACES = [
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

type CrossBoardSharedStateSurface = (typeof CROSS_BOARD_SHARED_STATE_SURFACES)[number];

declare global {
  interface Window {
    __memoryAtlasStage4Phase3?: () => {
      integrationVersion: typeof STARFIELD_INTEGRATION_VERSION;
      mappingVersion: typeof STARFIELD_MAPPING_VERSION;
      rendererMode: GalaxyRendererMode;
      mappingSource: StarfieldMappingResult["source"];
      mappedParticleCount: number;
      snapshotMappedCount: number;
      fallbackCount: number;
      safety: StarfieldMappingResult["safety"];
      formulas: StarfieldMappingResult["formulas"];
    };
    __memoryAtlasStage5Phase3?: () => {
      integrationVersion: typeof TIMELINE_RENDERER_FEATURE_FLAG_VERSION;
      rendererMode: TimelineRendererMode;
      defaultRendererMode: typeof DEFAULT_TIMELINE_RENDERER_MODE;
      legacyRollbackEnabled: true;
      visibleEventCount: number;
      totalEventCount: number;
      selectedRangeActive: boolean;
      selectedRange: TimelineTimeRangeSelection | null;
      evidenceLayers: string[];
      levelCounts: Record<string, number>;
      feedback: {
        reducedMotion: boolean;
        pseudoHaptic: boolean;
        audio: boolean;
      };
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasStage6Phase1?: () => {
      structureModelVersion: typeof DATA_MAP_STRUCTURE_MODEL_VERSION;
      relationExplanationVersion: typeof DATA_MAP_RELATION_EXPLANATION_VERSION;
      layers: DataMapStructureLayerId[];
      visibleNodeCount: number;
      relationCount: number;
      selectedRelationId: string | null;
      defaultCollapsed: true;
      boundary: "No Phase 6.2 editing";
      rawPrivateDataIncluded: false;
      directActiveMemoryWriteback: false;
      proposalWrite: false;
    };
    __memoryAtlasStage6Phase2?: () => {
      detailPanelVersion: typeof DATA_MAP_DETAIL_PANEL_VERSION;
      proposalEntryVersion: typeof DATA_MAP_PROPOSAL_ENTRY_VERSION;
      selectedNodeId: string | null;
      selectedNodeKind: AtlasNode["kind"] | null;
      detailFields: string[];
      proposalOnly: true;
      directActiveMemoryWriteback: false;
      rawPrivateDataIncluded: false;
    };
    __memoryAtlasStage7Phase1?: () => {
      runtimeVersion: typeof SEARCH_2_0_RUNTIME_VERSION;
      sessionSummaryVersion: typeof SEARCH_2_0_SESSION_SUMMARY_VERSION;
      query: string;
      resultCount: number;
      hasMatchedReason: boolean;
      hasEvidenceRefs: boolean;
      jumpActions: Array<"starfield" | "river" | "inspector">;
      zeroResultRecoveryVisible: boolean;
      proposalCandidateCount: number;
      directActiveMemoryWriteback: false;
      rawPrivateDataIncluded: false;
    };
    __memoryAtlasStage7Phase2?: () => {
      runtimeVersion: typeof REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION;
      reviewSchemaVersion: typeof REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION;
      questionCount: number;
      panelIds: ReviewPanelId[];
      iterationItemCount: number;
      proposalCandidate: boolean;
      hasEvidenceRefs: boolean;
      directActiveMemoryWriteback: false;
      rawPrivateDataIncluded: false;
    };
    __memoryAtlasStage8Phase1?: () => {
      runtimeVersion: typeof SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION;
      closureSchemaVersion: typeof SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION;
      sourceReviewSchemaVersion: typeof REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION;
      panelIds: SummaryClosurePanelId[];
      changeComparisonCount: number;
      staleConflictSignalCount: number;
      proposalCandidateCount: number;
      proposalOnly: true;
      directActiveMemoryWriteback: false;
      rawPrivateDataIncluded: false;
      proposalWrite: false;
    };
    __memoryAtlasStage9Phase1?: () => {
      runtimeVersion: typeof CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION;
      inspectorLayerVersion: typeof INSPECTOR_EXPLANATION_LAYER_VERSION;
      sharedStateSchemaVersion: SharedAtlasState["schema_version"];
      activeView: ViewKey;
      surfaces: CrossBoardSharedStateSurface[];
      surfaceCount: number;
      synchronizedFilters: SharedAtlasState["filters"];
      shared_state_filters: true;
      synchronized_filters: true;
      focus: SharedAtlasState["focus"];
      sync: SharedAtlasState["sync"];
      visibleNodeCount: number;
      selectedNodeId: string | null;
      inspector_explanation_layer: {
        mounted: boolean;
        formulaCount: number;
        evidenceCount: number;
        safetyNoteCount: number;
        source: "redacted_derived_snapshot";
      };
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS10Phase2?: () => {
      globalChineseUxVersion: typeof GLOBAL_CHINESE_UX_VERSION;
      coreUiDefaultChinese: true;
      machineTermsRequireChineseExplanation: true;
      chineseUxAudit: "atlasctl audit --check chinese-ux";
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS10Phase3?: () => {
      machineDetailFoldingVersion: typeof MACHINE_DETAIL_FOLDING_VERSION;
      defaultHumanReadableFirst: true;
      machineFieldsDefaultCollapsed: true;
      advancedDetailsEntryVisible: true;
      foldedSurfaces: Array<"home_arrival" | "search_session" | "search_result" | "review_session" | "summary_closure" | "inspector">;
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS11Phase1?: () => {
      clioLikeVisualsVersion: typeof CLIO_LIKE_VISUALS_VERSION;
      visualIds: ClioLikeVisualId[];
      visualCount: number;
      clusterCount: number;
      supportsFilters: ["source", "time", "project", "task"];
      activeFilters: {
        source: string;
        time: string;
        project: string;
        task: string;
      };
      chartsAreStaticDecoration: false;
      humanQuestionMapPartial: true;
      pendingLaterVisuals: ["S11 P2", "S11 P3", "S11 P4"];
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS11Phase2?: () => {
      economicLikeVisualsVersion: typeof ECONOMIC_LIKE_VISUALS_VERSION;
      visualIds: EconomicLikeVisualId[];
      visualCount: number;
      taskCount: number;
      supportsFilters: ["source", "time", "project", "task"];
      activeFilters: {
        source: string;
        time: string;
        project: string;
        task: string;
      };
      chartsAreStaticDecoration: false;
      humanQuestionMapPartial: true;
      pendingLaterVisuals: ["S11 P3", "S11 P4"];
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS11Phase3?: () => {
      workflowLatentGovernanceVisualsVersion: typeof WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION;
      visualIds: WorkflowLatentGovernanceVisualId[];
      visualCount: number;
      sankeyLinkCount: number;
      frictionCellCount: number;
      latentAxisCount: number;
      evidenceEventCount: number;
      formulaParameterCount: number;
      supportsFilters: ["source", "time", "project", "task"];
      activeFilters: {
        source: string;
        time: string;
        project: string;
        task: string;
      };
      chartsAreStaticDecoration: false;
      humanQuestionMapPartial: true;
      pendingLaterVisuals: ["S11 P4"];
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS11Phase4?: () => {
      humanQuestionMapVersion: typeof HUMAN_QUESTION_MAP_VERSION;
      visualIds: HumanQuestionMapVisualId[];
      visualCount: number;
      p0VisualCount: number;
      failedP0Count: number;
      excludedCandidateCount: number;
      supportsFilters: ["source", "time", "project", "task"];
      activeFilters: {
        source: string;
        time: string;
        project: string;
        task: string;
      };
      visualRoiGatePassAllP0: true;
      allP0HaveHumanQuestionAndAction: true;
      chartsAreStaticDecoration: false;
      humanQuestionMapComplete: true;
      pendingLaterVisuals: ["S11 Review"];
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS12Phase1?: () => {
      commandPaletteVersion: typeof COMMAND_PALETTE_VERSION;
      commandIds: S12P1CommandId[];
      commandCount: number;
      acceptedCoreCommandIds: S12P1CoreCommandId[];
      personalizationCommandId: "generate_personalization_prompt";
      personalizationTargets: ["chatgpt", "codex", "other_agent"];
      userTriggerRequired: true;
      automaticSendEnabled: false;
      chatgptDeepExploreEnabled: false;
      unacceptedCommandCount: 0;
      selectedCommandId: S12P1CommandId;
      pendingLaterWork: ["S12 P2", "S12 P3"];
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalApplyExecution: false;
        sendsCookiesTokensSecrets: false;
      };
    };
    __memoryAtlasS12Phase3?: () => {
      taskId: "MA-V12-S12P3";
      acceptanceId: "ACC-MA-V12-S12P3";
      contractVersion: typeof S12_P3_CHATGPT_DEEP_EXPLORE_VERSION;
      commandId: typeof S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID;
      commandVisible: boolean;
      defaultMode: "prefill_only";
      allowedModes: ["prefill_only", "auto_submit"];
      dryRunCommand: string;
      openCommand: string;
      userTriggerRequired: true;
      noSilentSend: true;
      autoSubmitRequiresExplicitConfig: true;
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalApplyExecution: false;
        sendsCookiesTokensSecrets: false;
      };
    };
    __memoryAtlasR3CommandWorkflows?: () => {
      workflowVersion: typeof COMMAND_WORKFLOW_VERSION;
      commandApiVersion: typeof COMMAND_API_VERSION;
      commandIds: S12P1CommandId[];
      runtimeAvailable: boolean;
      selectedCommandId: S12P1CommandId;
      executionStatus: CommandExecutionStatus;
      hostedStaticReadOnly: boolean;
      localAppHandoff: typeof LOCAL_APP_HANDOFF_URL;
      noSilentSend: true;
      canonicalRepoMutation: false;
    };
  }
}

const MEMORY_OVERVIEW_SECTION_ORDER = [
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

const HOME_LEVEL_ASSET_GROUPS = [
  { id: "core_profile", label: "核心画像" },
  { id: "project", label: "项目" },
  { id: "decision", label: "决策" },
  { id: "temporary", label: "临时" },
  { id: "stale", label: "过期" },
] as const;

const HOME_THEME_CATEGORY_STATES = [
  { id: "rising", label: "上升" },
  { id: "declining", label: "下降" },
  { id: "conflict", label: "冲突" },
  { id: "opportunity", label: "机会" },
  { id: "stable", label: "稳定" },
] as const;

const HOME_ARRIVAL_CATEGORY_LABELS = {
  new_material: "新增重要资料",
  strengthened: "增强结论",
  weakened: "减弱或过期结论",
  pending_proposal: "待授权提案",
  sync_failure: "同步失败",
} as const;

const S12_P1_ACCEPTED_CORE_COMMAND_IDS = [
  "sync_chatgpt",
  "sync_codex",
  "generate_weekly_report",
  "view_pending_proposals",
] as const;
const S12_P1_PERSONALIZATION_COMMAND_ID = "generate_personalization_prompt" as const;
const S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID = "chatgpt_deep_explore" as const;
const S12_P3_CHATGPT_DEEP_EXPLORE_VERSION = "chatgpt_deep_explore.v1_2_s12_p3" as const;
const S12_P1_COMMAND_IDS = [...S12_P1_ACCEPTED_CORE_COMMAND_IDS, S12_P1_PERSONALIZATION_COMMAND_ID, S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID] as const;
const S12_P1_PERSONALIZATION_TARGETS = ["chatgpt", "codex", "other_agent"] as const;

type S12P1CoreCommandId = (typeof S12_P1_ACCEPTED_CORE_COMMAND_IDS)[number];
type S12P1CommandId = (typeof S12_P1_COMMAND_IDS)[number];

interface CommandPaletteCommand {
  id: S12P1CommandId;
  label: string;
  description: string;
  humanAction: string;
  dryRunCommand: string;
  status: string;
  viewTarget: ViewKey | null;
  personalizationTargets?: typeof S12_P1_PERSONALIZATION_TARGETS;
}

interface CommandPaletteModel {
  version: typeof COMMAND_PALETTE_VERSION;
  commands: CommandPaletteCommand[];
  commandIds: S12P1CommandId[];
  acceptedCoreCommandIds: S12P1CoreCommandId[];
  personalizationTargets: typeof S12_P1_PERSONALIZATION_TARGETS;
  pendingProposalCount: number;
  weeklyReportNodeCount: number;
  latestDateLabel: string;
}

type CommandExecutionStatus = "idle" | "running" | "success" | "needs_input" | "error" | "local_required";

interface CommandWorkflowAction {
  type: "reload_atlas" | "navigate_view" | "open_url";
  view?: ViewKey;
  url?: string;
}

interface CommandWorkflowResult {
  schema_version: "memory_atlas_command_result.v1_2_r3";
  command_id: S12P1CommandId;
  status: "success" | "needs_input" | "error";
  title_zh: string;
  message_zh: string;
  outputs: string[];
  input_hint_zh?: string;
  action?: CommandWorkflowAction;
  safety: {
    sends_to_chatgpt: false;
    auto_submit?: false;
    canonical_repo_mutation?: false;
  };
}

interface CommandExecutionState {
  commandId: S12P1CommandId | null;
  status: CommandExecutionStatus;
  title: string;
  message: string;
  outputs: string[];
  inputHint: string;
  fallbackUrl: string;
  navigationView: ViewKey | null;
}

const views: Array<{ key: ViewKey; label: string; icon: ComponentType<{ size?: number }> }> = [
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

const navigationGroups: Array<{
  id: "judgment" | "exploration" | "reflection";
  label: string;
  question: string;
  viewKeys: ViewKey[];
}> = [
  { id: "judgment", label: "判断", question: "我现在应该先判断什么", viewKeys: ["home", "summary"] },
  { id: "exploration", label: "探索", question: "我需要从哪里找证据", viewKeys: ["galaxy", "notion", "timeline", "search"] },
  { id: "reflection", label: "复盘", question: "哪里值得投入或降噪", viewKeys: ["roi", "obsidian", "contribution", "wordcloud"] },
];

const visualFocusViews: ViewKey[] = ["home", "galaxy", "notion", "roi", "obsidian", "timeline", "contribution", "wordcloud", "summary"];

const defaultFilters: AtlasFilters = {
  query: "",
  source: "all",
  tier: "all",
  category: "all",
  theme: "all",
};

function buildGalaxyStarfieldMapping(nodes: AtlasNode[]): StarfieldMappingResult {
  try {
    return mapUniverseStateSnapshotToStarfield(universeStateSample as UniverseStateSnapshot, nodes); // source: "universe_state_snapshot"
  } catch {
    return mapAtlasNodesToStarfield(nodes); // source: "atlas_nodes"
  }
}

type ContributionScale = "day" | "week" | "month" | "year";
type WritebackAction = "update_statement" | "add_context" | "change_tier" | "flag_conflict" | "rollback_to_version";
type FilterKey = keyof AtlasFilters;
type TimelineInteractionMode = "pan" | "brush";

interface TimelineEvent {
  date: string;
  node_id: string;
  memory_id: string;
  label: string;
  memory_tier: string;
  category: string;
  importance: string;
}

interface TimelineLayoutControls {
  zoom: number;
  center: number;
  cursor: number;
}

type MemoryRiverLevel = "Macro" | "Meso" | "Micro";

interface TimelineDisplayEvent {
  id: string;
  source: TimelineEvent;
  node: AtlasNode | undefined;
  day: Date;
  utcDate: string;
  x: number;
  y: number;
  radius: number;
  color: string;
  major: boolean;
  future: boolean;
  shortLabel: string;
}

type TimelineTimeRangeSelection = SharedTimelineTimeRangeSelection;

interface TimelineBrushDraft {
  pointerId: number;
  startX: number;
  endX: number;
}

interface TimelinePanDraft {
  pointerId: number;
  startX: number;
  startCenter: number;
}

interface TimelineFeedbackSettings {
  reducedMotion: boolean;
  pseudoHaptic: boolean;
  audio: boolean;
}

interface MemoryRiverLevelBand {
  level: MemoryRiverLevel;
  note: string;
  y: number;
}

interface MemoryRiverLane {
  id: string;
  groupKey: string;
  level: MemoryRiverLevel;
  label: string;
  count: number;
  path: string;
  color: string;
  gradientId: string;
  strokeWidth: number;
  labelX: number;
  labelY: number;
  y: number;
}

interface MemoryRiverMarker {
  id: string;
  kind: "black-hole" | "proto-star" | "memory-event";
  event: TimelineDisplayEvent;
  title: string;
  x: number;
  y: number;
  radius: number;
}

type MemoryRiverEvidenceKind = "black-hole-lifecycle" | "proto-star-lifecycle" | "stale-deprecated";

interface MemoryRiverEvidencePoint {
  id: string;
  x: number;
  y: number;
  radius: number;
  label: string;
}

interface MemoryRiverEvidenceSegment {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  strength: number;
}

interface MemoryRiverEvidenceLayer {
  id: string;
  kind: MemoryRiverEvidenceKind;
  label: string;
  detail: string;
  startX: number;
  endX: number;
  labelX: number;
  labelY: number;
  count: number;
  path?: string;
  points: MemoryRiverEvidencePoint[];
  segments: MemoryRiverEvidenceSegment[];
}

interface MemoryRiverRoiGradientBand {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  score: number;
  color: string;
  label: string;
}

interface MemoryRiverRoiGradient {
  label: string;
  signal: string;
  averageRoiScore: number;
  highLeverageCount: number;
  capabilityGrowthCount: number;
  bands: MemoryRiverRoiGradientBand[];
}

interface MemoryRiverLayout {
  levels: MemoryRiverLevelBand[];
  lanes: MemoryRiverLane[];
  evidenceLayers: MemoryRiverEvidenceLayer[];
  roiGradient: MemoryRiverRoiGradient;
  markers: MemoryRiverMarker[];
  levelCounts: Record<MemoryRiverLevel, number>;
}

interface DeltaStats {
  totalFiltered: number;
  totalMemory: number;
  recentCount: number;
  previousCount: number;
  deltaCount: number;
  deltaRate: number | null;
  recentDecisionCount: number;
  recentCoreCount: number;
  topCategory: string;
  latestDate: string;
}

interface FilteredAtlasSlice {
  memoryNodes: AtlasNode[];
  graphNodes: AtlasNode[];
  graphEdges: AtlasEdge[];
  timeline: TimelineEvent[];
  visibleNodeIds: Set<string>;
  deltaStats: DeltaStats;
  filterActive: boolean;
}

type ReviewPeriodId = "last_30_days" | "last_90_days" | "all";

type ReviewPanelId =
  | "review_period_selector"
  | "theme_change_panel"
  | "opportunity_panel"
  | "low_value_loop_panel"
  | "decision_change_panel"
  | "next_action_panel"
  | "proposal_decision_panel"
  | "iteration_backlog";

type ReviewQuestionId =
  | "dominant_topics"
  | "strengthening_topics"
  | "declining_topics"
  | "new_opportunities"
  | "low_value_loops"
  | "decision_changes"
  | "next_actions"
  | "proposal_decision";

interface ReviewSignalRow {
  title: string;
  summary: string;
  count: number;
  evidence_refs: string[];
}

interface ReviewNextAction {
  action_id: string;
  title: string;
  reason: string;
  priority: "high" | "medium" | "low";
  source_scope: "redacted_atlas_snapshot" | "agent_recommendations_redacted";
  evidence_refs: string[];
  acceptance_hint: string;
}

interface ReviewIterationItem {
  item_id: string;
  title: string;
  why_it_matters: string;
  next_step: string;
  acceptance_hint: string;
  priority: "high" | "medium" | "low";
}

interface ReviewQuestionAnswer {
  question_id: ReviewQuestionId;
  panel_id: ReviewPanelId;
  question: string;
  answer: string;
  evidence_refs: string[];
}

interface ReviewSummaryIterationOutput {
  review_id: string;
  review_schema_version: typeof REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION;
  time_window: {
    period_id: ReviewPeriodId;
    label: string;
    range_start: string;
    range_end: string;
    node_count: number;
  };
  source_scope: "redacted_atlas_snapshot";
  dominant_topics: ReviewSignalRow[];
  strengthening_topics: ReviewSignalRow[];
  declining_topics: ReviewSignalRow[];
  new_opportunities: ReviewSignalRow[];
  low_value_loops: ReviewSignalRow[];
  decision_changes: ReviewSignalRow[];
  next_actions: ReviewNextAction[];
  proposal_candidate: {
    should_generate: boolean;
    proposal_decision: "generate_proposal" | "review_only";
    target_type: "memory_update_candidate" | "review_only_note";
    reason: string;
    rollback_hint: string;
    requires_conflict_check: true;
    requires_agent_or_human_apply: true;
  };
  evidence_refs: string[];
  confidence: "high" | "medium" | "low";
  iteration: {
    iteration_backlog: ReviewIterationItem[];
    review_again_at: string;
    proposal_only: true;
    directActiveMemoryWriteback: false;
    rawPrivateDataIncluded: false;
  };
  questions: ReviewQuestionAnswer[];
  panelIds: ReviewPanelId[];
}

type SummaryClosurePanelId = "change_comparison" | "stale_conflict_signals" | "proposal_candidates";

interface SummaryClosureChangeRow {
  signal_id: string;
  title: string;
  summary: string;
  current_count: number;
  previous_count: number;
  delta: number;
  evidence_refs: string[];
}

interface SummaryClosureSignal {
  signal_id: string;
  signal_type: "stale" | "conflict";
  severity: "high" | "medium" | "low";
  title: string;
  summary: string;
  evidence_refs: string[];
  proposal_hint: string;
  rollback_hint: string;
}

interface SummaryClosureProposalCandidate {
  proposal_id: string;
  title: string;
  target_type: "memory_update_candidate" | "review_only_note";
  reason: string;
  evidence_refs: string[];
  rollback_hint: string;
  requires_conflict_check: true;
  requires_agent_or_human_apply: true;
  proposal_only: true;
}

interface SummaryIterationClosureOutput {
  closure_id: string;
  closure_schema_version: typeof SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION;
  source_review_schema_version: typeof REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION;
  source_scope: "redacted_atlas_snapshot";
  change_comparison: SummaryClosureChangeRow[];
  stale_conflict_signals: SummaryClosureSignal[];
  proposal_candidates: SummaryClosureProposalCandidate[];
  closure_summary: string;
  safety: {
    proposal_only: true;
    directActiveMemoryWriteback: false;
    rawPrivateDataIncluded: false;
    proposalWrite: false;
  };
  panelIds: SummaryClosurePanelId[];
}

interface SourceOption {
  id: string;
  label: string;
  description: string;
  node_count: number;
}

interface PeriodCounts {
  date: string;
  label: string;
  activityScore: number;
  activityLevel: number;
  globalActivityScore: number;
  conversationCount: number;
  messageCount: number;
  memoryCount: number;
  decisionCount: number;
  coreMemoryCount: number;
  midLongMemoryCount: number;
  shortMemoryCount: number;
  filteredMemoryCount: number;
  filteredDecisionCount: number;
  filteredCoreCount: number;
  toolCallCount?: number;
  errorEventCount?: number;
  abortCount?: number;
  delta?: number;
  previousLabel?: string;
}

type TrendSlot = Pick<PeriodCounts, "activityLevel" | "activityScore"> | null;

interface ContributionPeriodDetail {
  scale: ContributionScale;
  bucket: PeriodCounts;
  relatedNodes: AtlasNode[];
}

interface HumanOverview {
  topicRows: Array<{ label: string; count: number }>;
  tierRows: Array<{ label: string; count: number }>;
  categoryRows: Array<{ label: string; count: number }>;
  rememberItems: string[];
  actionItems: string[];
  opportunityItems: string[];
  riskItems: string[];
}

interface HomeSignalCard {
  id: string;
  title: string;
  value: string;
  note: string;
  tone: "weather" | "dominant" | "rising" | "declining" | "black-hole" | "proto-star";
}

type HomeArrivalBriefingCardId = keyof typeof HOME_ARRIVAL_CATEGORY_LABELS;

interface HomeArrivalBriefingCard {
  id: HomeArrivalBriefingCardId;
  label: string;
  value: string;
  summary: string;
  evidence: string;
  nextStep: string;
  targetView: ViewKey;
  node: AtlasNode | null;
  icon: ComponentType<{ size?: number }>;
  tone: "new-material" | "strengthened" | "weakened" | "proposal" | "sync";
  machineSignal: string;
}

interface HomeAction extends HomeActionDetail {
  id: string;
  targetView: ViewKey;
  node: AtlasNode | null;
}

interface HomeTierAsset extends TierAssetDetail {
  id: string;
  targetView: ViewKey;
  node: AtlasNode | null;
}

interface HomeTopicDetail extends TopicClassificationDetail {
  id: string;
  targetView: ViewKey;
  node: AtlasNode | null;
  nodes: AtlasNode[];
}

type ClioLikeVisualId = "cluster_tree" | "bubble_map" | "topic_cluster_explorer";

interface ClioClusterDatum {
  id: string;
  label: string;
  count: number;
  recentCount: number;
  riskCount: number;
  roiScore: number;
  evidenceCount: number;
  dominantCategory: string;
  sourceCount: number;
  color: string;
  x: number;
  y: number;
  radius: number;
  node: AtlasNode | null;
  nodes: AtlasNode[];
}

interface ClioTreeBranch {
  id: string;
  label: string;
  count: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  node: AtlasNode | null;
}

interface ClioLikeVisualCopy {
  id: ClioLikeVisualId;
  title: string;
  insightHeader: string;
  humanQuestion: string;
  actionValue: string;
}

interface ClioLikeVisualModel {
  schemaVersion: typeof CLIO_LIKE_VISUALS_VERSION;
  activeFilters: {
    source: string;
    time: string;
    project: string;
    task: string;
  };
  visualCopy: ClioLikeVisualCopy[];
  clusters: ClioClusterDatum[];
  treeBranches: ClioTreeBranch[];
  explorerRows: ClioClusterDatum[];
  summary: string;
}

type EconomicLikeVisualId = "task_treemap" | "automation_vs_augmentation" | "roi_scatter" | "opportunity_radar";

interface EconomicLikeVisualCopy {
  id: EconomicLikeVisualId;
  title: string;
  insightHeader: string;
  humanQuestion: string;
  actionValue: string;
}

interface EconomicTaskDatum {
  id: string;
  label: string;
  count: number;
  roiScore: number;
  automationShare: number;
  augmentationShare: number;
  opportunityScore: number;
  riskScore: number;
  recentCount: number;
  sourceCount: number;
  color: string;
  x: number;
  y: number;
  radius: number;
  width: number;
  height: number;
  node: AtlasNode | null;
  nodes: AtlasNode[];
}

interface EconomicRadarAxis {
  id: string;
  label: string;
  value: number;
}

interface EconomicLikeVisualModel {
  schemaVersion: typeof ECONOMIC_LIKE_VISUALS_VERSION;
  activeFilters: {
    source: string;
    time: string;
    project: string;
    task: string;
  };
  visualCopy: EconomicLikeVisualCopy[];
  taskRows: EconomicTaskDatum[];
  scatterPoints: EconomicTaskDatum[];
  radarAxes: EconomicRadarAxis[];
  automationAverage: number;
  augmentationAverage: number;
  summary: string;
}

type WorkflowLatentGovernanceVisualId =
  | "agent_decision_sankey"
  | "friction_heatmap"
  | "latent_radar"
  | "evidence_timeline"
  | "formula_explorer";

interface WorkflowLatentGovernanceVisualCopy {
  id: WorkflowLatentGovernanceVisualId;
  title: string;
  insightHeader: string;
  humanQuestion: string;
  actionValue: string;
}

interface WorkflowSankeyLinkDatum {
  id: string;
  sourceLabel: string;
  targetLabel: string;
  value: number;
  width: number;
  y: number;
  color: string;
  node: AtlasNode | null;
}

interface FrictionHeatmapCellDatum {
  id: string;
  rowLabel: string;
  columnLabel: string;
  count: number;
  intensity: number;
  action: string;
  node: AtlasNode | null;
}

interface LatentRadarDatum {
  id: string;
  label: string;
  value: number;
  confidenceLabel: string;
  evidenceBadge: string;
  node: AtlasNode | null;
}

interface EvidenceTimelineDatum {
  id: string;
  label: string;
  dateLabel: string;
  x: number;
  evidenceCount: number;
  sourceLabel: string;
  node: AtlasNode | null;
}

interface FormulaInspectorDatum {
  id: string;
  label: string;
  value: string;
  description: string;
  sourcePath: string;
  node: AtlasNode | null;
}

interface WorkflowLatentGovernanceVisualModel {
  schemaVersion: typeof WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION;
  activeFilters: {
    source: string;
    time: string;
    project: string;
    task: string;
  };
  visualCopy: WorkflowLatentGovernanceVisualCopy[];
  sankeyLinks: WorkflowSankeyLinkDatum[];
  frictionCells: FrictionHeatmapCellDatum[];
  latentAxes: LatentRadarDatum[];
  evidenceEvents: EvidenceTimelineDatum[];
  formulaRows: FormulaInspectorDatum[];
  summary: string;
}

type HumanQuestionMapVisualId = ClioLikeVisualId | EconomicLikeVisualId | WorkflowLatentGovernanceVisualId;
type HumanQuestionMapFamilyId = "clio_like" | "economic_like" | "workflow_governance";

interface HumanQuestionMapEntry {
  id: HumanQuestionMapVisualId;
  familyId: HumanQuestionMapFamilyId;
  familyLabel: string;
  title: string;
  insightHeader: string;
  humanQuestion: string;
  actionValue: string;
  targetView: ViewKey;
  gateReason: string;
  visualRoiGatePass: true;
  p0Included: true;
}

interface HumanQuestionMapExcludedCandidate {
  id: string;
  title: string;
  reason: string;
  visualRoiGatePass: false;
  p0Included: false;
}

interface HumanQuestionMapModel {
  schemaVersion: typeof HUMAN_QUESTION_MAP_VERSION;
  activeFilters: {
    source: string;
    time: string;
    project: string;
    task: string;
  };
  entries: HumanQuestionMapEntry[];
  excludedCandidates: HumanQuestionMapExcludedCandidate[];
  p0VisualCount: number;
  failedP0Count: number;
  strongestGateLabel: string;
  summary: string;
}

interface MemoryWeatherV2 {
  label: string;
  summary: string;
  tone: HomeSignalCard["tone"];
  stabilityScore: number;
  momentumScore: number;
  riskScore: number;
  opportunityScore: number;
  confidenceScore: number;
  signals: string[];
}

interface MiniStarfieldPoint {
  id: string;
  label: string;
  x: number;
  y: number;
  radius: number;
  color: string;
  node: AtlasNode;
}

interface RiverPulseSegment {
  id: string;
  label: string;
  recentCount: number;
  previousCount: number;
  delta: number;
  intensity: number;
  node: AtlasNode | null;
}

interface HomeInspectorLink {
  id: string;
  title: string;
  meta: string;
  node: AtlasNode | null;
}

type Search2TierFilter = "all" | "core_profile" | "project" | "decision" | "workflow" | "knowledge" | "opportunity" | "stale";
type Search2RecencyFilter = "all" | "recent" | "active" | "stale" | "archival";
type Search2ImportanceFilter = "all" | "low" | "medium" | "high" | "critical";

interface Search2Filters {
  query: string;
  tier: Search2TierFilter;
  topic: string;
  recency: Search2RecencyFilter;
  importance: Search2ImportanceFilter;
  evidenceOnly: boolean;
}

interface Search2Result {
  result_id: string;
  title: string;
  summary: string;
  source: string;
  tier: Exclude<Search2TierFilter, "all">;
  topic: string;
  recency: Exclude<Search2RecencyFilter, "all">;
  importance: Exclude<Search2ImportanceFilter, "all">;
  matched_reason: string;
  evidence_refs: string[];
  jump_to_starfield: string;
  jump_to_river: string;
  open_inspector: string;
  proposal_candidate: boolean;
  score: number;
  node: AtlasNode;
}

interface Search2SessionSummary {
  query: string;
  result_count: number;
  dominant_topics: string[];
  high_importance_hits: string[];
  stale_or_black_hole_hits: string[];
  missing_evidence: string[];
  next_step: string;
  proposal_candidate: boolean;
}

interface SemanticInsight {
  label: string;
  count: number;
  roiScore: number;
  recentCount: number;
  nodes: AtlasNode[];
}

interface SemanticMatrixCell {
  topic: string;
  tier: string;
  count: number;
  nodes: AtlasNode[];
}

interface WordCloudItem {
  label: string;
  count: number;
  score: number;
  x: number;
  y: number;
  rotate: number;
  nodes: AtlasNode[];
}

interface WritebackProposal {
  schema_version: string;
  proposal_id: string;
  created_at: string;
  status: "draft_pending_agent_apply";
  target_ref: {
    node_id: string;
    memory_id: string;
    label: string;
    source_file: string;
    base_date: string;
  };
  action: WritebackAction;
  payload: {
    proposed_text: string;
    reason: string;
    current_tier: string;
    current_category: string;
  };
  version: {
    revision: number;
    parent_proposal_id: string | null;
    rollback_unit: string;
    supersedes_proposal_id?: string | null;
  };
  diff?: {
    base_text: string;
    proposed_text: string;
    length_delta: number;
    changed_segments: number;
    summary: string;
  };
  rollback?: {
    rollback_to_proposal_id: string;
    rollback_to_revision: number;
    rollback_text: string;
    rollback_reason: string;
  };
  review?: {
    human_summary: string;
    agent_next_step: string;
    conflict_policy: string;
    apply_status: "proposal_only_pending_agent_apply";
  };
  safety: {
    direct_frontend_mutation_of_active_memory: false;
    requires_conflict_check: true;
    requires_agent_or_human_apply: true;
    forbidden_payload: string[];
  };
}

interface InspectorFormulaRow {
  label: string;
  value: string;
  formula: string;
  parameters: string;
}

interface InspectorEvidenceRow {
  label: string;
  value: string;
}

interface InspectorExplanation {
  summary: string;
  formulas: InspectorFormulaRow[];
  evidence: InspectorEvidenceRow[];
  safetyNotes: string[];
}

interface WritebackProposalDraftInput {
  policy: MemoryAtlas["source_contract"]["writeback_policy"];
  node: AtlasNode;
  action: WritebackAction;
  proposedText: string;
  reason: string;
  baseText: string;
  latest: WritebackProposal | null;
  proposalCount: number;
  now: string;
  proposalIdPrefix: "atlas" | "atlas_preview";
}

interface HeatStop {
  stop: number;
  rgb: readonly [number, number, number];
}

interface RuntimeState {
  runStartedAt: Date;
  snapshotLoadedAt: Date | null;
  lifecycle: "载入中" | "已同步" | "读取失败";
  serverMode: "检测中" | "本地自释放" | "静态托管";
  commandApiAvailable: boolean;
}

const WRITEBACK_QUEUE_KEY = "memory-atlas.writeback.proposals.v1";
const TIMELINE_FEEDBACK_SETTINGS_KEY = "memory-atlas.timeline.feedback";
const TRANSIENT_STORAGE_PREFIXES = ["memory-atlas.runtime.", "memory-atlas.cache.", "memory-atlas.temp.", "memory-atlas.view."];
const TRANSIENT_CACHE_PREFIXES = ["memory-atlas", "memory_atlas", "vite-memory-atlas"];
const LOCAL_RUNTIME_HEARTBEAT_MS = 10_000;
const INITIAL_COMMAND_EXECUTION_STATE: CommandExecutionState = {
  commandId: null,
  status: "idle",
  title: "",
  message: "",
  outputs: [],
  inputHint: "",
  fallbackUrl: "",
  navigationView: null,
};
const NEXT_ACTION_TOP_LIMIT = 5;
const NEXT_ACTION_SORT_WEIGHTS = {
  roi_weight: 0.4,
  urgency_weight: 0.25,
  confidence_weight: 0.25,
  effort_penalty_weight: 0.1,
};
const TIER_ASSET_TOP_LIMIT = 7;
const TIER_ASSET_SORT_WEIGHTS = {
  value_weight: 0.35,
  importance_weight: 0.25,
  confidence_weight: 0.25,
  staleness_penalty_weight: 0.15,
};
const TOPIC_CLASSIFICATION_TOP_LIMIT = 10;
const TOPIC_CLASSIFICATION_STATES: TopicClassificationDetail["topic_state"][] = [
  "dominant",
  "rising",
  "declining",
  "emerging",
  "conflict",
  "black_hole",
  "stale",
];
const TOPIC_CLASSIFICATION_SORT_WEIGHTS = {
  strength_weight: 0.38,
  trend_weight: 0.24,
  confidence_weight: 0.22,
  conflict_penalty_weight: 0.16,
};
const MEMORY_RIVER_MIN_X = 80;
const MEMORY_RIVER_MAX_X = 960;
const MEMORY_RIVER_WIDTH = MEMORY_RIVER_MAX_X - MEMORY_RIVER_MIN_X;
const weekdayLabels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
const heatStops: HeatStop[] = [
  { stop: 0, rgb: [15, 17, 22] },
  { stop: 0.1, rgb: [23, 34, 58] },
  { stop: 0.24, rgb: [29, 63, 119] },
  { stop: 0.4, rgb: [31, 109, 178] },
  { stop: 0.58, rgb: [31, 155, 209] },
  { stop: 0.76, rgb: [72, 199, 232] },
  { stop: 0.9, rgb: [126, 224, 248] },
  { stop: 1, rgb: [167, 236, 255] },
];
const heatLevelAnchors = [0, 0.16, 0.34, 0.54, 0.74, 0.93] as const;
const emptyHeatColor = "#0f1116";

const writebackActionLabels: Record<WritebackAction, string> = {
  update_statement: uiCopy.proposal.actions.update_statement,
  add_context: uiCopy.proposal.actions.add_context,
  change_tier: uiCopy.proposal.actions.change_tier,
  flag_conflict: uiCopy.proposal.actions.flag_conflict,
  rollback_to_version: uiCopy.proposal.actions.rollback_to_version,
};

function buildCommandPaletteModel(atlas: MemoryAtlas, slice: FilteredAtlasSlice, runtimeState: RuntimeState): CommandPaletteModel {
  const pendingProposalCount = slice.memoryNodes.filter((node) => {
    const text = `${node.label} ${node.statement ?? ""} ${node.category ?? ""}`.toLowerCase();
    return node.category === "pending_proposal" || /proposal|待授权|提案|pending/.test(text);
  }).length;
  const latestDate = parseDay(slice.deltaStats.latestDate);
  const latestDateLabel = latestDate ? formatChineseDate(latestDate) : formatUpdatedAt(atlas.overview.generated_at);
  const weeklyReportNodeCount = slice.memoryNodes.filter((node) => {
    const day = parseDay(node.date);
    if (!day || !latestDate) return false;
    return day >= addDays(latestDate, -6) && day <= latestDate;
  }).length || slice.deltaStats.recentCount;
  const sourceCount = new Map((atlas.data_sources ?? []).map((source) => [source.id, source.node_count]));
  const commands: CommandPaletteCommand[] = [
    {
      id: "sync_chatgpt",
      label: "同步 ChatGPT",
      description: "从固定本地导入箱读取一个官方导出，并刷新脱敏后的页面数据。",
      humanAction: "只接受 Application Support 导入箱中的一个官方 ZIP；不读取浏览器 cookies、tokens 或登录状态。",
      dryRunCommand: "python3 scripts/atlasctl.py sync --source chatgpt --official-export <fixed-local-inbox>",
      status: `${(sourceCount.get("memory_atlas") ?? 0).toLocaleString()} 条 ChatGPT/Memory Atlas 节点可复核`,
      viewTarget: null,
    },
    {
      id: "sync_codex",
      label: "同步 Codex",
      description: "读取本机 Codex sessions 的脱敏摘要，并刷新当前页面快照。",
      humanAction: "只读取 sessions 与 session index；不读取 auth、cookies 或明文凭据文件。",
      dryRunCommand: "python3 scripts/atlasctl.py sync --source codex --codex-home <configured-local-home>",
      status: `${(sourceCount.get("codex") ?? 0).toLocaleString()} 条 Codex 节点可复核`,
      viewTarget: null,
    },
    {
      id: "generate_weekly_report",
      label: "生成本周报告",
      description: "从当前脱敏快照汇总近七天变化、决策、提案与建议。",
      humanAction: "用户明确执行后，只在本地安装副本生成一份 Markdown 周报。",
      dryRunCommand: "python3 scripts/build_memory_atlas_weekly_report.py --database-dir <installed-source>",
      status: `${weeklyReportNodeCount.toLocaleString()} 条近周/近期节点 · 最新 ${latestDateLabel}`,
      viewTarget: "summary",
    },
    {
      id: "view_pending_proposals",
      label: "查看待授权提案",
      description: "集中查看待授权提案候选；这里只做判断，不直接应用变更。",
      humanAction: "读取 proposal 状态机并打开总结视图；不会执行 apply 或 rollback。",
      dryRunCommand: "python3 scripts/atlasctl.py proposals --dry-run",
      status: `${pendingProposalCount.toLocaleString()} 条候选线索需要人工判断`,
      viewTarget: "summary",
    },
    {
      id: "generate_personalization_prompt",
      label: "生成个性化提示",
      description: "准备供 ChatGPT、Codex 和其他 agent 使用的最新个性化提示入口。",
      humanAction: "在本地安装副本生成 ChatGPT、Codex 和其他 agent 的中文说明及机器可复制文本。",
      dryRunCommand: "python3 scripts/atlasctl.py generate-personalization-prompt --target all",
      status: `覆盖 ChatGPT / Codex / 其他代理 · 运行状态 ${runtimeState.lifecycle}`,
      viewTarget: "summary",
      personalizationTargets: S12_P1_PERSONALIZATION_TARGETS,
    },
    {
      id: "chatgpt_deep_explore",
      label: "打开 ChatGPT 深度探索",
      description: "把最新记忆分析报告和探索提示转成 ChatGPT 预填充入口。",
      humanAction: "用户明确执行后生成最新提示，并由浏览器打开仅预填页面；不会自动发送。",
      dryRunCommand: "python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only",
      status: "默认仅预填 · 自动发送受控",
      viewTarget: null,
    },
  ];
  return {
    version: COMMAND_PALETTE_VERSION,
    commands,
    commandIds: [...S12_P1_COMMAND_IDS],
    acceptedCoreCommandIds: [...S12_P1_ACCEPTED_CORE_COMMAND_IDS],
    personalizationTargets: S12_P1_PERSONALIZATION_TARGETS,
    pendingProposalCount,
    weeklyReportNodeCount,
    latestDateLabel,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isCommandWorkflowResult(value: unknown): value is CommandWorkflowResult {
  if (!isRecord(value) || value.schema_version !== "memory_atlas_command_result.v1_2_r3") return false;
  if (!S12_P1_COMMAND_IDS.includes(value.command_id as S12P1CommandId)) return false;
  if (!(["success", "needs_input", "error"] as const).includes(value.status as "success" | "needs_input" | "error")) return false;
  if (typeof value.title_zh !== "string" || typeof value.message_zh !== "string" || !Array.isArray(value.outputs)) return false;
  if (!isRecord(value.safety) || value.safety.sends_to_chatgpt !== false) return false;
  if (!value.outputs.every((output) => typeof output === "string")) return false;
  if (value.action !== undefined) {
    if (!isRecord(value.action)) return false;
    const action = value.action;
    if (!(["reload_atlas", "navigate_view", "open_url"] as const).includes(action.type as CommandWorkflowAction["type"])) return false;
    if (action.type === "navigate_view" && (typeof action.view !== "string" || !views.some((view) => view.key === action.view))) return false;
    if (action.type === "open_url" && typeof action.url !== "string") return false;
  }
  return true;
}

function safeChatGPTPrefillUrl(value: string | undefined): string {
  if (!value) return "";
  try {
    const url = new URL(value);
    if (
      url.protocol !== "https:"
      || url.hostname !== "chatgpt.com"
      || url.port
      || url.username
      || url.password
      || (url.pathname !== "/" && url.pathname !== "")
      || url.hash
      || !url.searchParams.get("q")?.trim()
    ) {
      return "";
    }
    return url.toString();
  } catch {
    return "";
  }
}

async function clearTransientBrowserState(): Promise<void> {
  try {
    window.sessionStorage.clear();
  } catch {
    // Browser privacy settings may block storage access during page release.
  }
  try {
    for (let index = window.localStorage.length - 1; index >= 0; index -= 1) {
      const key = window.localStorage.key(index);
      if (!key || key === WRITEBACK_QUEUE_KEY) continue;
      if (TRANSIENT_STORAGE_PREFIXES.some((prefix) => key.startsWith(prefix))) {
        window.localStorage.removeItem(key);
      }
    }
  } catch {
    // Keep release best-effort; the server shutdown signal is still sent.
  }
  try {
    if ("caches" in window) {
      const cacheKeys = await caches.keys();
      await Promise.all(
        cacheKeys
          .filter((key) => TRANSIENT_CACHE_PREFIXES.some((prefix) => key.startsWith(prefix)))
          .map((key) => caches.delete(key)),
      );
    }
  } catch {
    // Cache Storage may be unavailable for static previews or blocked profiles.
  }
  try {
    if ("serviceWorker" in navigator) {
      const registrations = await navigator.serviceWorker.getRegistrations();
      await Promise.all(
        registrations
          .filter((registration) => registration.scope.includes("memory-atlas") || registration.scope.includes("127.0.0.1"))
          .map((registration) => registration.unregister()),
      );
    }
  } catch {
    // Memory Atlas does not depend on a service worker; unregister is best-effort cleanup.
  }
}

export function App() {
  const [sharedState, dispatchSharedState] = useReducer(
    sharedAtlasReducer,
    undefined,
    () => createSharedAtlasState({ activeView: DEFAULT_MEMORY_ATLAS_VIEW, filters: defaultFilters }),
  );
  const activeView = sharedState.mode.activeView;
  const filters = useMemo(() => atlasFiltersFromSharedState(sharedState), [sharedState]);
  const timelineTimeRange = sharedState.filters.timeRange;
  const [atlas, setAtlas] = useState<MemoryAtlas>(emptyAtlas);
  const [selectedContributionPeriod, setSelectedContributionPeriod] = useState<ContributionPeriodDetail | null>(null);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [loadError, setLoadError] = useState("");
  const [helpOpen, setHelpOpen] = useState(false);
  const [selectedCommandId, setSelectedCommandId] = useState<S12P1CommandId>("sync_chatgpt");
  const [commandExecution, setCommandExecution] = useState<CommandExecutionState>(INITIAL_COMMAND_EXECUTION_STATE);
  const [runtimeState, setRuntimeState] = useState<RuntimeState>(() => ({
    runStartedAt: new Date(),
    snapshotLoadedAt: null,
    lifecycle: "载入中",
    serverMode: "检测中",
    commandApiAvailable: false,
  }));

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    const runStartedAt = new Date();
    setRuntimeState((current) => ({ ...current, runStartedAt, snapshotLoadedAt: null, lifecycle: "载入中" }));
    loadMemoryAtlas(controller.signal)
      .then((loadedAtlas) => {
        if (cancelled) return;
        setAtlas(loadedAtlas);
        const firstNode = getMemoryNodes(loadedAtlas)[0] ?? loadedAtlas.nodes[0] ?? null;
        if (firstNode) {
          dispatchSharedState({ type: "select_node", node: firstNode, source: "startup" });
        }
        setLoadState("ready");
        setRuntimeState((current) => ({ ...current, snapshotLoadedAt: new Date(), lifecycle: "已同步" }));
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        if (cancelled) return;
        setLoadError(error instanceof Error ? error.message : "未知 Memory Atlas 读取错误");
        setLoadState("error");
        setRuntimeState((current) => ({ ...current, snapshotLoadedAt: null, lifecycle: "读取失败" }));
      });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    let heartbeatTimer = 0;
    let heartbeatEnabled = false;
    let released = false;

    const release = (reason: "page_release" | "react_unmount" = "page_release") => {
      if (!heartbeatEnabled || released) return;
      released = true;
      window.clearInterval(heartbeatTimer);
      void clearTransientBrowserState();
      const payload = new Blob([JSON.stringify({ reason, at: new Date().toISOString() })], {
        type: "application/json",
      });
      if (navigator.sendBeacon) {
        navigator.sendBeacon("/__memory_atlas_release", payload);
        return;
      }
      void fetch("/__memory_atlas_release", { method: "POST", body: payload, keepalive: true }).catch(() => undefined);
    };

    const handlePageRelease = () => release("page_release");

    const heartbeat = () => {
      if (!heartbeatEnabled) return;
      void fetch("/__memory_atlas_heartbeat", {
        method: "POST",
        cache: "no-store",
        keepalive: true,
      }).catch(() => undefined);
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") heartbeat();
    };

    fetch("/__memory_atlas_runtime_state", { cache: "no-store" })
      .then(async (response) => {
        if (cancelled || !response.ok) return;
        const payload: unknown = await response.json().catch(() => null);
        if (!isRecord(payload) || payload.status !== "running") return;
        const commandApiAvailable = isRecord(payload) && payload.command_api_version === COMMAND_API_VERSION;
        heartbeatEnabled = true;
        setRuntimeState((current) => ({ ...current, serverMode: "本地自释放", commandApiAvailable }));
        heartbeat();
        heartbeatTimer = window.setInterval(heartbeat, LOCAL_RUNTIME_HEARTBEAT_MS);
        window.addEventListener("pagehide", handlePageRelease);
        window.addEventListener("beforeunload", handlePageRelease);
        document.addEventListener("visibilitychange", handleVisibilityChange);
      })
      .catch(() => {
        if (!cancelled) {
          setRuntimeState((current) => ({ ...current, serverMode: "静态托管", commandApiAvailable: false }));
        }
      });

    const fallbackTimer = window.setTimeout(() => {
      if (!heartbeatEnabled && !cancelled) {
        setRuntimeState((current) => ({ ...current, serverMode: "静态托管", commandApiAvailable: false }));
      }
    }, 1200);

    return () => {
      cancelled = true;
      window.clearInterval(heartbeatTimer);
      window.clearTimeout(fallbackTimer);
      window.removeEventListener("pagehide", handlePageRelease);
      window.removeEventListener("beforeunload", handlePageRelease);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      release("react_unmount");
    };
  }, []);

  const memoryNodes = useMemo(() => getMemoryNodes(atlas), [atlas]);
  const sourceMemoryNodes = useMemo(
    () => memoryNodes.filter((node) => sourceMatchesNode(node, filters.source)),
    [filters.source, memoryNodes],
  );
  const scopedAtlas = useMemo(
    () => buildSourceScopedAtlas(atlas, sourceMemoryNodes, filters.source),
    [atlas, filters.source, sourceMemoryNodes],
  );
  const themeNodes = useMemo(() => getThemeNodes(scopedAtlas), [scopedAtlas]);
  const nodeMap = useMemo(() => getNodeMap(scopedAtlas), [scopedAtlas]);
  const selectedNode = useMemo(() => {
    const selectedNodeId = sharedState.selection.nodeId;
    if (!selectedNodeId) return null;
    return nodeMap.get(selectedNodeId) ?? atlas.nodes.find((node) => node.id === selectedNodeId) ?? null;
  }, [atlas.nodes, nodeMap, sharedState.selection.nodeId]);
  const sourceOptions = useMemo(() => buildSourceOptions(atlas, memoryNodes), [atlas, memoryNodes]);
  const categories = useMemo(() => uniqueSorted(sourceMemoryNodes.map((node) => node.category)), [sourceMemoryNodes]);
  const tiers = useMemo(() => uniqueSorted(sourceMemoryNodes.map((node) => normalizeMemoryTier(node.memory_tier))), [sourceMemoryNodes]);
  const themeOptions = useMemo(
    () =>
      themeNodes
        .map((node) => ({ id: node.visual?.cluster ?? node.id.replace("theme:", ""), label: node.label }))
        .sort((a, b) => a.label.localeCompare(b.label, "zh-CN")),
    [themeNodes],
  );
  const filteredMemoryNodes = useMemo(() => filterMemoryNodes(sourceMemoryNodes, filters), [sourceMemoryNodes, filters]);
  const slice = useMemo(
    () => buildFilteredSlice(scopedAtlas, filteredMemoryNodes, filters),
    [scopedAtlas, filteredMemoryNodes, filters],
  );
  const clioLikeVisualModel = useMemo(
    () => buildClioLikeVisualModel(slice.memoryNodes, filters, sharedState, slice.deltaStats),
    [filters, sharedState, slice.deltaStats, slice.memoryNodes],
  );
  const economicLikeVisualModel = useMemo(
    () => buildEconomicLikeVisualModel(slice.memoryNodes, filters, sharedState, slice.deltaStats),
    [filters, sharedState, slice.deltaStats, slice.memoryNodes],
  );
  const workflowLatentGovernanceVisualModel = useMemo(
    () => buildWorkflowLatentGovernanceVisualModel(slice.memoryNodes, slice.graphEdges, filters, sharedState, slice.deltaStats),
    [filters, sharedState, slice.deltaStats, slice.graphEdges, slice.memoryNodes],
  );
  const humanQuestionMapModel = useMemo(
    () => buildHumanQuestionMapModel(clioLikeVisualModel, economicLikeVisualModel, workflowLatentGovernanceVisualModel),
    [clioLikeVisualModel, economicLikeVisualModel, workflowLatentGovernanceVisualModel],
  );
  const commandPaletteModel = useMemo(
    () => buildCommandPaletteModel(scopedAtlas, slice, runtimeState),
    [runtimeState, scopedAtlas, slice],
  );

  const handleSelectNode = useCallback((node: AtlasNode) => {
    setSelectedContributionPeriod(null);
    dispatchSharedState({ type: "select_node", node, source: activeView });
  }, [activeView]);
  const handleSelectContributionPeriod = useCallback((detail: ContributionPeriodDetail) => {
    setSelectedContributionPeriod(detail);
    dispatchSharedState({
      type: "select_contribution_period",
      period: sharedContributionSelection({
        id: `${detail.scale}:${detail.bucket.date}`,
        scale: detail.scale,
        label: detail.bucket.label,
        activityScore: detail.bucket.activityScore,
        filteredMemoryCount: detail.bucket.filteredMemoryCount,
      }),
      source: "contribution",
    });
  }, []);
  const handleSelectTimelineRange = useCallback((range: TimelineTimeRangeSelection) => {
    dispatchSharedState({ type: "select_time_range", range, source: "timeline" });
  }, []);
  const clearTimelineRange = useCallback(() => {
    dispatchSharedState({ type: "clear_time_range", source: activeView });
  }, [activeView]);
  const updateFilters = useCallback((updater: (current: AtlasFilters) => AtlasFilters) => {
    setSelectedContributionPeriod(null);
    dispatchSharedState({ type: "set_filters", filters: updater(filters), source: activeView });
  }, [activeView, filters]);
  const switchView = useCallback((view: ViewKey) => {
    if (view !== "contribution") {
      setSelectedContributionPeriod(null);
    }
    dispatchSharedState({ type: "switch_view", view, source: activeView });
  }, [activeView]);
  const openHelpView = useCallback((view: ViewKey) => {
    switchView(view);
    setHelpOpen(false);
  }, [switchView]);
  const handleCommandPaletteAction = useCallback((command: CommandPaletteCommand) => {
    setSelectedCommandId(command.id);
    setCommandExecution((current) => current.status === "running" ? current : INITIAL_COMMAND_EXECUTION_STATE);
  }, []);
  const handleExecuteCommand = useCallback(async (command: CommandPaletteCommand) => {
    if (commandExecution.status === "running") return;
    if (runtimeState.serverMode !== "本地自释放" || !runtimeState.commandApiAvailable) {
      setCommandExecution({
        commandId: command.id,
        status: "local_required",
        title: runtimeState.serverMode === "本地自释放" ? "需要更新本地 app" : "需要本地 app",
        message: runtimeState.serverMode === "本地自释放"
          ? "当前本地运行服务不支持受控命令，请在最终交付后更新 Memory Atlas app。"
          : "此操作仅在本地 Memory Atlas app 执行。",
        outputs: [],
        inputHint: "",
        fallbackUrl: LOCAL_APP_HANDOFF_URL,
        navigationView: null,
      });
      return;
    }

    let chatgptWindow: Window | null = null;
    if (command.id === "chatgpt_deep_explore") {
      chatgptWindow = window.open("about:blank", "_blank");
      if (chatgptWindow) {
        try {
          chatgptWindow.opener = null;
          chatgptWindow.document.title = "正在准备 ChatGPT 深度探索";
          chatgptWindow.document.body.textContent = "正在准备仅预填的 ChatGPT 页面...";
        } catch {
          // The fallback link remains available if a browser blocks this temporary page.
        }
      }
    }

    setCommandExecution({
      commandId: command.id,
      status: "running",
      title: `正在执行：${command.label}`,
      message: "本地受控操作正在运行，请稍候。",
      outputs: [],
      inputHint: "",
      fallbackUrl: "",
      navigationView: null,
    });

    try {
      const response = await fetch("/__memory_atlas_command", {
        method: "POST",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command_id: command.id }),
      });
      const payload: unknown = await response.json().catch(() => null);
      if (!response.ok) {
        const message = isRecord(payload) && typeof payload.message_zh === "string"
          ? payload.message_zh
          : `本地命令请求失败（HTTP ${response.status}）。`;
        throw new Error(message);
      }
      if (!isCommandWorkflowResult(payload) || payload.command_id !== command.id) {
        throw new Error("本地命令返回格式未通过校验，已停止后续动作。");
      }

      let fallbackUrl = "";
      let navigationView: ViewKey | null = null;
      if (payload.status === "success" && payload.action?.type === "reload_atlas") {
        const loadedAtlas = await loadMemoryAtlas();
        setAtlas(loadedAtlas);
        const firstNode = getMemoryNodes(loadedAtlas)[0] ?? loadedAtlas.nodes[0] ?? null;
        if (firstNode) {
          dispatchSharedState({ type: "select_node", node: firstNode, source: "startup" });
        }
        setRuntimeState((current) => ({ ...current, snapshotLoadedAt: new Date(), lifecycle: "已同步" }));
      }
      if (payload.status === "success" && payload.action?.type === "navigate_view" && payload.action.view) {
        navigationView = payload.action.view;
      }
      if (payload.status === "success" && payload.action?.type === "open_url") {
        const safeUrl = safeChatGPTPrefillUrl(payload.action.url);
        if (!safeUrl) {
          throw new Error("ChatGPT 预填充地址未通过浏览器安全校验，已停止打开。");
        }
        fallbackUrl = safeUrl;
        if (chatgptWindow && !chatgptWindow.closed) {
          chatgptWindow.location.replace(safeUrl);
          fallbackUrl = "";
        }
      } else if (chatgptWindow && !chatgptWindow.closed) {
        chatgptWindow.close();
      }

      setCommandExecution({
        commandId: command.id,
        status: payload.status,
        title: payload.title_zh,
        message: payload.message_zh,
        outputs: payload.outputs,
        inputHint: payload.input_hint_zh ?? "",
        fallbackUrl,
        navigationView,
      });
    } catch (error) {
      if (chatgptWindow && !chatgptWindow.closed) chatgptWindow.close();
      setCommandExecution({
        commandId: command.id,
        status: "error",
        title: "操作未完成",
        message: error instanceof Error ? error.message : "本地操作失败，请查看 Memory Atlas 本机日志。",
        outputs: [],
        inputHint: "",
        fallbackUrl: "",
        navigationView: null,
      });
    }
  }, [commandExecution.status, runtimeState.commandApiAvailable, runtimeState.serverMode]);
  const focusSelectedTheme = useCallback(() => {
    const theme = selectedNode?.visual?.cluster;
    if (!theme) return;
    setSelectedContributionPeriod(null);
    dispatchSharedState({ type: "set_filter", key: "theme", value: theme, source: activeView });
  }, [activeView, selectedNode?.visual?.cluster]);
  const clearFilter = useCallback(
    (key: FilterKey) => {
      setSelectedContributionPeriod(null);
      dispatchSharedState({ type: "clear_filter", key, source: activeView });
    },
    [activeView],
  );
  const resetFilters = useCallback(() => {
    setSelectedContributionPeriod(null);
    dispatchSharedState({ type: "reset_filters", source: activeView });
  }, [activeView]);
  const selectAdjacentNode = useCallback(
    (direction: -1 | 1) => {
      const candidates = selectableLensNodes(slice, selectedNode);
      if (candidates.length < 2) return;
      const currentIndex = candidates.findIndex((node) => node.id === selectedNode?.id);
      if (currentIndex < 0) return;
      const nextIndex = (currentIndex + direction + candidates.length) % candidates.length;
      handleSelectNode(candidates[nextIndex]);
    },
    [handleSelectNode, selectedNode, slice],
  );
  useEffect(() => {
    if (loadState !== "ready") return;
    if (selectedNode && selectionStillVisible(selectedNode, slice)) return;
    const fallbackNode = slice.memoryNodes[0] ?? slice.graphNodes[0] ?? scopedAtlas.nodes[0] ?? null;
    if (fallbackNode) {
      dispatchSharedState({ type: "select_node", node: fallbackNode, source: "system" });
    } else if (sharedState.selection.nodeId) {
      dispatchSharedState({ type: "clear_focus", source: "system" });
    }
  }, [loadState, scopedAtlas.nodes, selectedNode, sharedState.selection.nodeId, slice.filterActive, slice.graphNodes, slice.memoryNodes, slice.visibleNodeIds]);

  const generatedAt = atlas.overview.generated_at
    ? new Date(atlas.overview.generated_at).toLocaleString("zh-CN")
    : uiCopy.states.notLoaded;
  const loadedAt = runtimeState.snapshotLoadedAt ? runtimeState.snapshotLoadedAt.toLocaleString("zh-CN") : uiCopy.states.loading;
  const runtimeStatus = `${runtimeState.lifecycle} / ${runtimeState.serverMode}`;
  const selectedTitle = views.find((view) => view.key === activeView)?.label ?? uiCopy.app.fallbackTitle;
  const wideView = visualFocusViews.includes(activeView);
  const workspaceClassName = wideView ? `workspace visual-focus-workspace ${activeView}-workspace` : "workspace";
  const showSideInspector = activeView === "contribution" || !wideView;
  const stage9InspectorExplanation = selectedNode
    ? buildInspectorExplanation(selectedNode, edgeCountFor(selectedNode.id, scopedAtlas.edges), sharedState)
    : null;

  useEffect(() => {
    window.__memoryAtlasStage9Phase1 = () => ({
      runtimeVersion: CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION,
      inspectorLayerVersion: INSPECTOR_EXPLANATION_LAYER_VERSION,
      sharedStateSchemaVersion: sharedState.schema_version,
      activeView,
      surfaces: [...CROSS_BOARD_SHARED_STATE_SURFACES],
      surfaceCount: CROSS_BOARD_SHARED_STATE_SURFACES.length,
      synchronizedFilters: sharedState.filters,
      shared_state_filters: true,
      synchronized_filters: true,
      focus: sharedState.focus,
      sync: sharedState.sync,
      visibleNodeCount: slice.memoryNodes.length,
      selectedNodeId: selectedNode?.id ?? null,
      inspector_explanation_layer: {
        mounted: Boolean(stage9InspectorExplanation),
        formulaCount: stage9InspectorExplanation?.formulas.length ?? 0,
        evidenceCount: stage9InspectorExplanation?.evidence.length ?? 0,
        safetyNoteCount: stage9InspectorExplanation?.safetyNotes.length ?? 0,
        source: "redacted_derived_snapshot",
      },
      safety: {
        rawPrivateDataIncluded: false,
        directActiveMemoryWriteback: false,
        proposalWrite: false,
      },
    });
    return () => {
      delete window.__memoryAtlasStage9Phase1;
    };
  }, [activeView, selectedNode?.id, sharedState, slice.memoryNodes.length, stage9InspectorExplanation]);

  useEffect(() => {
    window.__memoryAtlasS10Phase2 = () => ({
      globalChineseUxVersion: GLOBAL_CHINESE_UX_VERSION,
      coreUiDefaultChinese: true,
      machineTermsRequireChineseExplanation: true,
      chineseUxAudit: "atlasctl audit --check chinese-ux",
      safety: {
        rawPrivateDataIncluded: false,
        directActiveMemoryWriteback: false,
        proposalWrite: false,
      },
    });
    return () => {
      delete window.__memoryAtlasS10Phase2;
    };
  }, []);

  useEffect(() => {
    window.__memoryAtlasS10Phase3 = () => ({
      machineDetailFoldingVersion: MACHINE_DETAIL_FOLDING_VERSION,
      defaultHumanReadableFirst: true,
      machineFieldsDefaultCollapsed: true,
      advancedDetailsEntryVisible: true,
      foldedSurfaces: ["home_arrival", "search_session", "search_result", "review_session", "summary_closure", "inspector"],
      safety: {
        rawPrivateDataIncluded: false,
        directActiveMemoryWriteback: false,
        proposalWrite: false,
      },
    });
    return () => {
      delete window.__memoryAtlasS10Phase3;
    };
  }, []);

  useEffect(() => {
    window.__memoryAtlasS11Phase1 = () => ({
      clioLikeVisualsVersion: CLIO_LIKE_VISUALS_VERSION,
      visualIds: ["cluster_tree", "bubble_map", "topic_cluster_explorer"],
      visualCount: clioLikeVisualModel.visualCopy.length,
      clusterCount: clioLikeVisualModel.clusters.length,
      supportsFilters: ["source", "time", "project", "task"],
      activeFilters: clioLikeVisualModel.activeFilters,
      chartsAreStaticDecoration: false,
      humanQuestionMapPartial: true,
      pendingLaterVisuals: ["S11 P2", "S11 P3", "S11 P4"],
      safety: {
        rawPrivateDataIncluded: false,
        directActiveMemoryWriteback: false,
        proposalWrite: false,
      },
    });
    return () => {
      delete window.__memoryAtlasS11Phase1;
    };
  }, [clioLikeVisualModel]);

  useEffect(() => {
    window.__memoryAtlasS11Phase2 = () => ({
      economicLikeVisualsVersion: ECONOMIC_LIKE_VISUALS_VERSION,
      visualIds: ["task_treemap", "automation_vs_augmentation", "roi_scatter", "opportunity_radar"],
      visualCount: economicLikeVisualModel.visualCopy.length,
      taskCount: economicLikeVisualModel.taskRows.length,
      supportsFilters: ["source", "time", "project", "task"],
      activeFilters: economicLikeVisualModel.activeFilters,
      chartsAreStaticDecoration: false,
      humanQuestionMapPartial: true,
      pendingLaterVisuals: ["S11 P3", "S11 P4"],
      safety: {
        rawPrivateDataIncluded: false,
        directActiveMemoryWriteback: false,
        proposalWrite: false,
      },
    });
    return () => {
      delete window.__memoryAtlasS11Phase2;
    };
  }, [economicLikeVisualModel]);

  useEffect(() => {
    window.__memoryAtlasS11Phase3 = () => ({
      workflowLatentGovernanceVisualsVersion: WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION,
      visualIds: ["agent_decision_sankey", "friction_heatmap", "latent_radar", "evidence_timeline", "formula_explorer"],
      visualCount: workflowLatentGovernanceVisualModel.visualCopy.length,
      sankeyLinkCount: workflowLatentGovernanceVisualModel.sankeyLinks.length,
      frictionCellCount: workflowLatentGovernanceVisualModel.frictionCells.length,
      latentAxisCount: workflowLatentGovernanceVisualModel.latentAxes.length,
      evidenceEventCount: workflowLatentGovernanceVisualModel.evidenceEvents.length,
      formulaParameterCount: workflowLatentGovernanceVisualModel.formulaRows.length,
      supportsFilters: ["source", "time", "project", "task"],
      activeFilters: workflowLatentGovernanceVisualModel.activeFilters,
      chartsAreStaticDecoration: false,
      humanQuestionMapPartial: true,
      pendingLaterVisuals: ["S11 P4"],
      safety: {
        rawPrivateDataIncluded: false,
        directActiveMemoryWriteback: false,
        proposalWrite: false,
      },
    });
    return () => {
      delete window.__memoryAtlasS11Phase3;
    };
  }, [workflowLatentGovernanceVisualModel]);

  useEffect(() => {
    window.__memoryAtlasS11Phase4 = () => ({
      humanQuestionMapVersion: HUMAN_QUESTION_MAP_VERSION,
      visualIds: humanQuestionMapModel.entries.map((entry) => entry.id),
      visualCount: humanQuestionMapModel.entries.length,
      p0VisualCount: humanQuestionMapModel.p0VisualCount,
      failedP0Count: humanQuestionMapModel.failedP0Count,
      excludedCandidateCount: humanQuestionMapModel.excludedCandidates.length,
      supportsFilters: ["source", "time", "project", "task"],
      activeFilters: humanQuestionMapModel.activeFilters,
      visualRoiGatePassAllP0: true,
      allP0HaveHumanQuestionAndAction: true,
      chartsAreStaticDecoration: false,
      humanQuestionMapComplete: true,
      pendingLaterVisuals: ["S11 Review"],
      safety: {
        rawPrivateDataIncluded: false,
        directActiveMemoryWriteback: false,
        proposalWrite: false,
      },
    });
    return () => {
      delete window.__memoryAtlasS11Phase4;
    };
  }, [humanQuestionMapModel]);

  useEffect(() => {
    window.__memoryAtlasS12Phase1 = () => ({
      commandPaletteVersion: COMMAND_PALETTE_VERSION,
      commandIds: [...commandPaletteModel.commandIds],
      commandCount: commandPaletteModel.commands.length,
      acceptedCoreCommandIds: [...commandPaletteModel.acceptedCoreCommandIds],
      personalizationCommandId: S12_P1_PERSONALIZATION_COMMAND_ID,
      personalizationTargets: [...S12_P1_PERSONALIZATION_TARGETS],
      userTriggerRequired: true,
      automaticSendEnabled: false,
      chatgptDeepExploreEnabled: false,
      unacceptedCommandCount: 0,
      selectedCommandId,
      pendingLaterWork: ["S12 P2", "S12 P3"],
      safety: {
        rawPrivateDataIncluded: false,
        directActiveMemoryWriteback: false,
        proposalApplyExecution: false,
        sendsCookiesTokensSecrets: false,
      },
    });
    window.__memoryAtlasS12Phase3 = () => ({
      taskId: "MA-V12-S12P3",
      acceptanceId: "ACC-MA-V12-S12P3",
      contractVersion: S12_P3_CHATGPT_DEEP_EXPLORE_VERSION,
      commandId: S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID,
      commandVisible: commandPaletteModel.commandIds.includes(S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID),
      defaultMode: "prefill_only",
      allowedModes: ["prefill_only", "auto_submit"],
      dryRunCommand: "python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only --dry-run",
      openCommand: "python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only --open",
      userTriggerRequired: true,
      noSilentSend: true,
      autoSubmitRequiresExplicitConfig: true,
      safety: {
        rawPrivateDataIncluded: false,
        directActiveMemoryWriteback: false,
        proposalApplyExecution: false,
        sendsCookiesTokensSecrets: false,
      },
    });
    return () => {
      delete window.__memoryAtlasS12Phase1;
      delete window.__memoryAtlasS12Phase3;
    };
  }, [commandPaletteModel, selectedCommandId]);

  useEffect(() => {
    window.__memoryAtlasR3CommandWorkflows = () => ({
      workflowVersion: COMMAND_WORKFLOW_VERSION,
      commandApiVersion: COMMAND_API_VERSION,
      commandIds: [...commandPaletteModel.commandIds],
      runtimeAvailable: runtimeState.serverMode === "本地自释放" && runtimeState.commandApiAvailable,
      selectedCommandId,
      executionStatus: commandExecution.status,
      hostedStaticReadOnly: runtimeState.serverMode === "静态托管",
      localAppHandoff: LOCAL_APP_HANDOFF_URL,
      noSilentSend: true,
      canonicalRepoMutation: false,
    });
    return () => {
      delete window.__memoryAtlasR3CommandWorkflows;
    };
  }, [commandExecution.status, commandPaletteModel.commandIds, runtimeState.commandApiAvailable, runtimeState.serverMode, selectedCommandId]);

  return (
    <div
      className="app-shell"
      data-default-route-view={DEFAULT_MEMORY_ATLAS_VIEW}
      data-memory-overview-default-route="true"
      data-r2-release-identity={PRODUCT_IDENTITY_VERSION}
      data-s10-p2-global-chinese-ux={GLOBAL_CHINESE_UX_VERSION}
      data-s10-p3-machine-detail-folding={MACHINE_DETAIL_FOLDING_VERSION}
      data-stage9-phase1-shared-state={CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION}
      data-stage9-inspector-explanation={INSPECTOR_EXPLANATION_LAYER_VERSION}
      data-stage9-synchronized-filters="shared_state_filters synchronized_filters inspector_explanation_layer"
      data-stage9-safety-boundary="No direct active-memory writeback; No proposal queue write"
      data-stage9-surface-count={CROSS_BOARD_SHARED_STATE_SURFACES.length}
      data-s12-p1-command-palette={COMMAND_PALETTE_VERSION}
      data-s12-p3-chatgpt-deep-explore={S12_P3_CHATGPT_DEEP_EXPLORE_VERSION}
      data-s12-p3-chatgpt-deep-explore-boundary="prefill_only default; auto_submit gated; No silent send; No cookie/token/secret export"
      data-r3-command-workflows={COMMAND_WORKFLOW_VERSION}
      data-r3-command-api-available={runtimeState.commandApiAvailable ? "true" : "false"}
    >
      <aside className="sidebar" aria-label={uiCopy.app.navigationAria}>
        <div className="brand">
          <GitBranch size={22} />
          <div>
            <strong>{uiCopy.app.brandTitle}</strong>
            <span>{uiCopy.app.productName}</span>
          </div>
        </div>
        <nav className="nav-list">
          {navigationGroups.map((group) => (
            <div className="nav-group" data-nav-question-group={group.id} key={group.id}>
              <div className="nav-group-heading">
                <span className="nav-group-label">{group.label}</span>
                <small className="nav-group-question">{group.question}</small>
              </div>
              <div className="nav-group-items">
                {group.viewKeys.map((viewKey) => {
                  const view = views.find((candidate) => candidate.key === viewKey);
                  if (!view) return null;
                  const Icon = view.icon;
                  return (
                    <button
                      aria-label={view.label}
                      className={activeView === view.key ? "nav-item active" : "nav-item"}
                      data-nav-view={view.key}
                      key={view.key}
                      onClick={() => switchView(view.key)}
                      onFocus={(event) => event.currentTarget.scrollIntoView({ block: "nearest", inline: "nearest" })}
                      title={view.label}
                      type="button"
                    >
                      <Icon size={18} />
                      <span>{view.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <MachineFieldDetails title="数据状态" className="sidebar-data-status">
            <dl>
              <div><dt>{uiCopy.app.snapshotGeneratedAt}</dt><dd>{generatedAt}</dd></div>
              <div><dt>{uiCopy.app.snapshotLoadedAt}</dt><dd>{loadedAt}</dd></div>
              <div><dt>{uiCopy.app.runtimeStatus}</dt><dd>{runtimeStatus}</dd></div>
            </dl>
          </MachineFieldDetails>
        </div>
      </aside>

      <main className={workspaceClassName}>
        <header className="topbar">
          <div>
            <p className="eyebrow">{uiCopy.app.topbarEyebrow}</p>
            <h1>{selectedTitle}</h1>
          </div>
          <div className="topbar-actions">
            <div className="stat-strip" aria-label="星图总览">
              <Metric label={uiCopy.metrics.memory} value={scopedAtlas.overview.active_memory_count} />
              <Metric label={uiCopy.metrics.nodes} value={scopedAtlas.overview.node_count} />
              <Metric label={uiCopy.metrics.edges} value={scopedAtlas.overview.edge_count} />
              <Metric label={uiCopy.metrics.activity} value={scopedAtlas.overview.conversation_count} />
            </div>
            <button className="help-launch-button" onClick={() => setHelpOpen(true)} title={uiCopy.help.buttonLabel} type="button">
              <CircleHelp size={17} />
              <span>{uiCopy.help.buttonLabel}</span>
            </button>
          </div>
        </header>

        {loadState === "error" ? (
          <ErrorState
            compact
            className="load-banner"
            dataState="load-failed-banner"
            description={uiCopy.states.loadFailedDescription}
            details={loadError}
            title={uiCopy.states.loadFailedTitle}
          />
        ) : null}

        <section className="controls" aria-label={uiCopy.filters.ariaLabel}>
          <label className="search-box">
            <Search size={18} />
            <input
              value={filters.query}
              onChange={(event) => updateFilters((current) => ({ ...current, query: event.target.value }))}
              placeholder={uiCopy.filters.searchPlaceholder}
            />
          </label>
          <label className="select-filter source-filter">
            <span>{uiCopy.filters.sourceLabel}</span>
            <select
              value={filters.source}
              onChange={(event) =>
                updateFilters((current) => ({
                  ...current,
                  source: event.target.value,
                  tier: "all",
                  category: "all",
                  theme: "all",
                }))
              }
            >
              {sourceOptions.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.label}
                </option>
              ))}
            </select>
          </label>
          <SelectFilter
            label={uiCopy.filters.tierLabel}
            value={filters.tier}
            options={tiers}
            onChange={(value) => updateFilters((current) => ({ ...current, tier: value }))}
          />
          <SelectFilter
            label={uiCopy.filters.categoryLabel}
            value={filters.category}
            options={categories}
            formatOption={humanCategoryLabel}
            onChange={(value) => updateFilters((current) => ({ ...current, category: value }))}
          />
          <label className="select-filter">
            <span>{uiCopy.filters.topicLabel}</span>
            <select value={filters.theme} onChange={(event) => updateFilters((current) => ({ ...current, theme: event.target.value }))}>
              <option value="all">{uiCopy.filters.allOption}</option>
              {themeOptions.map((theme) => (
                <option key={theme.id} value={theme.id}>
                  {theme.label}
                </option>
              ))}
            </select>
          </label>
        </section>

        <InteractionLens
          activeView={activeView}
          filters={filters}
          sharedState={sharedState}
          selectedContributionPeriod={activeView === "contribution" ? selectedContributionPeriod : null}
          selectedNode={selectedNode}
          slice={slice}
          sourceOptions={sourceOptions}
          timelineTimeRange={timelineTimeRange}
          onClearFilter={clearFilter}
          onClearTimelineRange={clearTimelineRange}
          onFocusTheme={focusSelectedTheme}
          onResetFilters={resetFilters}
          onSelectAdjacent={selectAdjacentNode}
        />

        <CommandPalettePanel
          execution={commandExecution}
          model={commandPaletteModel}
          onExecuteCommand={handleExecuteCommand}
          onNavigateView={switchView}
          selectedCommandId={selectedCommandId}
          onSelectCommand={handleCommandPaletteAction}
        />

        <div className={wideView ? "content-grid wide-view" : "content-grid"} data-view={activeView}>
          <section className="view-surface">
            <ViewRouter
              activeView={activeView}
              atlas={scopedAtlas}
              filters={filters}
              clioLikeVisualModel={clioLikeVisualModel}
              economicLikeVisualModel={economicLikeVisualModel}
              workflowLatentGovernanceVisualModel={workflowLatentGovernanceVisualModel}
              humanQuestionMapModel={humanQuestionMapModel}
              sharedState={sharedState}
              slice={slice}
              nodeMap={nodeMap}
              selectedNode={selectedNode}
              loadState={loadState}
              loadError={loadError}
              timelineTimeRange={timelineTimeRange}
              onSelectNode={handleSelectNode}
              onSelectContributionPeriod={handleSelectContributionPeriod}
              onSelectTimelineRange={handleSelectTimelineRange}
              onClearTimelineRange={clearTimelineRange}
              onResetFilters={resetFilters}
              onShowHelp={() => setHelpOpen(true)}
              onSwitchView={switchView}
            />
          </section>
          {showSideInspector ? (
            activeView === "contribution" && selectedContributionPeriod ? (
              <ContributionPeriodInspector detail={selectedContributionPeriod} onSelectNode={handleSelectNode} />
            ) : (
              <NodeInspector atlas={scopedAtlas} node={selectedNode} edgeCount={edgeCountFor(selectedNode?.id, scopedAtlas.edges)} sharedState={sharedState} />
            )
          ) : null}
        </div>
        <MemoryAtlasHelpPanel copy={uiCopy.help} onClose={() => setHelpOpen(false)} onSelectView={openHelpView} open={helpOpen} />
      </main>
    </div>
  );
}

function CommandPalettePanel({
  execution,
  model,
  onExecuteCommand,
  onNavigateView,
  selectedCommandId,
  onSelectCommand,
}: {
  execution: CommandExecutionState;
  model: CommandPaletteModel;
  onExecuteCommand: (command: CommandPaletteCommand) => void;
  onNavigateView: (view: ViewKey) => void;
  selectedCommandId: S12P1CommandId;
  onSelectCommand: (command: CommandPaletteCommand) => void;
}) {
  const selectedCommand = model.commands.find((command) => command.id === selectedCommandId) ?? model.commands[0];
  const selectedExecution = execution.commandId === selectedCommand.id ? execution : INITIAL_COMMAND_EXECUTION_STATE;
  return (
    <section
      className="command-palette"
      aria-label="Memory Atlas 命令面板"
      data-s12-p1-command-palette={model.version}
      data-s12-p1-command-count={model.commands.length}
      data-s12-p1-personalization-targets={model.personalizationTargets.join(",")}
      data-s12-p1-safety-boundary="S12 dry-run: No automatic send; No raw mutation; No proposal apply execution"
      data-s12-p3-chatgpt-deep-explore={S12_P3_CHATGPT_DEEP_EXPLORE_VERSION}
      data-s12-p3-chatgpt-deep-explore-command="chatgpt_deep_explore"
      data-r3-command-workflows={COMMAND_WORKFLOW_VERSION}
      data-r3-execution-status={selectedExecution.status}
      data-r3-write-scope="Application Support installed source copy; redacted sync and derived outputs only; no canonical repo mutation"
    >
      <div className="command-palette-heading">
        <div>
          <p className="eyebrow">快捷操作</p>
          <h2>接下来可以做什么</h2>
        </div>
        <span>{model.commands.length} 个可选动作</span>
      </div>
      <div className="command-palette-grid">
        {model.commands.map((command) => {
          const Icon = commandPaletteIcon(command.id);
          return (
            <button
              className={command.id === selectedCommand.id ? "command-palette-action active" : "command-palette-action"}
              data-s12-p1-command-id={command.id}
              disabled={execution.status === "running"}
              key={command.id}
              onClick={() => onSelectCommand(command)}
              title={command.description}
              type="button"
            >
              <Icon size={18} />
              <span>{command.label}</span>
              <small>{command.status}</small>
            </button>
          );
        })}
      </div>
      <div className="command-palette-detail">
        <div className="command-palette-detail-copy">
          <strong>{selectedCommand.label}</strong>
          <p>{selectedCommand.description}</p>
        </div>
        <button
          className="command-execute-button"
          data-r3-command-execute={selectedCommand.id}
          disabled={execution.status === "running"}
          onClick={() => onExecuteCommand(selectedCommand)}
          type="button"
        >
          {selectedExecution.status === "running" ? <RefreshCw aria-hidden="true" className="command-running-icon" size={15} /> : <Play aria-hidden="true" size={15} />}
          <span>{selectedExecution.status === "running" ? "正在执行" : "执行此操作"}</span>
        </button>
      </div>
      {selectedExecution.status !== "idle" ? (
        <div
          aria-live="polite"
          className={`command-result command-result-${selectedExecution.status}`}
          data-r3-command-result={selectedCommand.id}
          data-r3-command-result-status={selectedExecution.status}
          role="status"
        >
          <strong>{selectedExecution.title}</strong>
          <p>{selectedExecution.message}</p>
          {selectedExecution.inputHint ? <code>{selectedExecution.inputHint}</code> : null}
          {selectedExecution.outputs.length > 0 ? (
            <ul>
              {selectedExecution.outputs.map((output) => <li key={output}><code>{output}</code></li>)}
            </ul>
          ) : null}
          {selectedExecution.fallbackUrl ? (
            <a href={selectedExecution.fallbackUrl} rel="noreferrer" target="_blank">
              {selectedExecution.status === "local_required" ? "打开本地 Memory Atlas" : "打开 ChatGPT 预填充页面"}
            </a>
          ) : null}
          {selectedExecution.navigationView ? (
            <button
              className="command-result-action"
              data-r3-command-navigate={selectedExecution.navigationView}
              onClick={() => onNavigateView(selectedExecution.navigationView as ViewKey)}
              type="button"
            >
              查看总结
            </button>
          ) : null}
        </div>
      ) : null}
      <MachineFieldDetails title="运行边界与技术详情" className="command-technical-details">
        <div className="command-palette-technical-content">
          <small>{selectedCommand.humanAction}</small>
          <code>{selectedCommand.dryRunCommand}</code>
          <div className="command-palette-safety">
            <span>No automatic send</span>
            <span>No silent send</span>
            <span>No canonical repo mutation</span>
            <span>Application Support source copy only</span>
            <span>No proposal apply execution</span>
            <span>No cookie/token/secret export</span>
            <span>ChatGPT / Codex / other agent personalization prompt</span>
            <span>prefill_only / auto_submit</span>
          </div>
        </div>
      </MachineFieldDetails>
    </section>
  );
}

function commandPaletteIcon(commandId: S12P1CommandId): ComponentType<{ size?: number }> {
  if (commandId === "sync_chatgpt") return RefreshCw;
  if (commandId === "sync_codex") return Download;
  if (commandId === "generate_weekly_report") return CalendarDays;
  if (commandId === "view_pending_proposals") return Save;
  if (commandId === "chatgpt_deep_explore") return Crosshair;
  return Crosshair;
}

function ViewRouter({
  activeView,
  atlas,
  filters,
  clioLikeVisualModel,
  economicLikeVisualModel,
  workflowLatentGovernanceVisualModel,
  humanQuestionMapModel,
  sharedState,
  slice,
  nodeMap,
  selectedNode,
  loadState,
  loadError,
  timelineTimeRange,
  onSelectNode,
  onSelectContributionPeriod,
  onSelectTimelineRange,
  onClearTimelineRange,
  onResetFilters,
  onShowHelp,
  onSwitchView,
}: {
  activeView: ViewKey;
  atlas: MemoryAtlas;
  filters: AtlasFilters;
  clioLikeVisualModel: ClioLikeVisualModel;
  economicLikeVisualModel: EconomicLikeVisualModel;
  workflowLatentGovernanceVisualModel: WorkflowLatentGovernanceVisualModel;
  humanQuestionMapModel: HumanQuestionMapModel;
  sharedState: SharedAtlasState;
  slice: FilteredAtlasSlice;
  nodeMap: Map<string, AtlasNode>;
  selectedNode: AtlasNode | null;
  loadState: "loading" | "ready" | "error";
  loadError: string;
  timelineTimeRange: TimelineTimeRangeSelection | null;
  onSelectNode: (node: AtlasNode) => void;
  onSelectContributionPeriod: (detail: ContributionPeriodDetail) => void;
  onSelectTimelineRange: (range: TimelineTimeRangeSelection) => void;
  onClearTimelineRange: () => void;
  onResetFilters: () => void;
  onShowHelp: () => void;
  onSwitchView: (view: ViewKey) => void;
}) {
  const starfieldMapping = useMemo(() => buildGalaxyStarfieldMapping(slice.graphNodes), [slice.graphNodes]);

  if (loadState === "loading") {
    return <div className="galaxy-loading">{uiCopy.states.loadingGalaxy}</div>;
  }
  if (loadState === "error") {
    return (
      <ErrorState
        dataState="load-failed"
        description={uiCopy.states.loadFailedDescription}
        details={loadError}
        title={uiCopy.states.loadFailedTitle}
      />
    );
  }

  const emptyState = viewEmptyState(atlas, slice);
  if (emptyState === "empty-atlas") {
    return (
      <EmptyState
        actionLabel={uiCopy.states.emptyAtlasAction}
        dataState="empty-atlas"
        description={uiCopy.states.emptyAtlasDescription}
        onAction={onShowHelp}
        title={uiCopy.states.emptyAtlasTitle}
      />
    );
  }
  if (emptyState === "no-filtered-results") {
    return (
      <EmptyState
        actionLabel={uiCopy.states.noFilteredResultsAction}
        dataState="no-filtered-results"
        description={uiCopy.states.noFilteredResultsDescription}
        onAction={onResetFilters}
        title={uiCopy.states.noFilteredResultsTitle}
      />
    );
  }

  if (activeView === "home") {
    return (
      <HomeOverviewView
        atlas={atlas}
        nodes={slice.memoryNodes}
        graphEdges={slice.graphEdges}
        clioLikeVisualModel={clioLikeVisualModel}
        economicLikeVisualModel={economicLikeVisualModel}
        workflowLatentGovernanceVisualModel={workflowLatentGovernanceVisualModel}
        humanQuestionMapModel={humanQuestionMapModel}
        deltaStats={slice.deltaStats}
        selectedNode={selectedNode}
        sharedState={sharedState}
        timelineTimeRange={timelineTimeRange}
        onSelectNode={onSelectNode}
        onSwitchView={onSwitchView}
      />
    );
  }
  if (activeView === "galaxy") {
    return (
      <GalaxyView
        graphNodes={slice.graphNodes}
        graphEdges={slice.graphEdges}
        memoryCount={slice.memoryNodes.length}
        selectedNode={selectedNode}
        sharedState={sharedState}
        deltaStats={slice.deltaStats}
        timelineTimeRange={timelineTimeRange}
        starfieldMapping={starfieldMapping}
        onSelectNode={onSelectNode}
      />
    );
  }
  if (activeView === "notion") {
    return (
      <DataGuideMap
        nodes={slice.graphNodes}
        edges={slice.graphEdges}
        selectedNode={selectedNode}
        deltaStats={slice.deltaStats}
        parentSnapshotId={atlas.overview.generated_at || atlas.schema_version}
        onSelectNode={onSelectNode}
      />
    );
  }
  if (activeView === "roi") {
    return <RoiDashboard atlas={atlas} nodes={slice.memoryNodes} deltaStats={slice.deltaStats} onSelectNode={onSelectNode} />;
  }
  if (activeView === "obsidian") {
    return <ObsidianGraph nodes={slice.graphNodes} edges={slice.graphEdges} selectedNode={selectedNode} sharedState={sharedState} deltaStats={slice.deltaStats} onSelectNode={onSelectNode} />;
  }
  if (activeView === "timeline") {
    return (
      <TimelineView
        timeline={slice.timeline}
        nodeMap={nodeMap}
        selectedNode={selectedNode}
        sharedState={sharedState}
        selectedTimelineRange={timelineTimeRange}
        deltaStats={slice.deltaStats}
        onSelectNode={onSelectNode}
        onSelectTimelineRange={onSelectTimelineRange}
        onClearTimelineRange={onClearTimelineRange}
      />
    );
  }
  if (activeView === "contribution") {
    return (
      <ContributionGrid
        atlas={atlas}
        nodes={slice.memoryNodes}
        filters={filters}
        deltaStats={slice.deltaStats}
        onSelectPeriod={onSelectContributionPeriod}
      />
    );
  }
  if (activeView === "wordcloud") {
    return <WordCloudView nodes={slice.memoryNodes} deltaStats={slice.deltaStats} onSelectNode={onSelectNode} />;
  }
  if (activeView === "summary") {
    return <SummaryIterationView atlas={atlas} nodes={slice.memoryNodes} deltaStats={slice.deltaStats} />;
  }
  return (
    <SearchReview
      atlas={atlas}
      filters={filters}
      nodes={slice.memoryNodes}
      deltaStats={slice.deltaStats}
      onSelectNode={onSelectNode}
      onSwitchView={onSwitchView}
    />
  );
}

function viewEmptyState(atlas: MemoryAtlas, slice: FilteredAtlasSlice): "empty-atlas" | "no-filtered-results" | null {
  if (slice.memoryNodes.length || slice.graphNodes.length) return null;
  if (slice.filterActive) return "no-filtered-results";
  const hasSnapshotData =
    atlas.nodes.length > 0 ||
    atlas.edges.length > 0 ||
    atlas.timeline.length > 0 ||
    atlas.overview.active_memory_count > 0;
  return hasSnapshotData ? null : "empty-atlas";
}

function MachineFieldDetails({ title, className = "", children }: { title: string; className?: string; children: ReactNode }) {
  return (
    <details
      className={`machine-field-details${className ? ` ${className}` : ""}`}
      data-s10-p3-machine-fields="collapsed-by-default"
    >
      <summary>
        <GitBranch size={14} />
        <span>{title}</span>
      </summary>
      {children}
    </details>
  );
}

function EvidenceRefsDetails({ refs }: { refs: string[] }) {
  return (
    <MachineFieldDetails title={`高级详情：证据字段（${refs.length.toLocaleString()} 条）`} className="inline-machine-field-details">
      <p className="machine-field-help">默认折叠。这里仅给 ChatGPT / Codex 核验证据引用，不作为首屏阅读内容。</p>
      <small>evidence_refs：{refs.join(" / ") || "none"}</small>
    </MachineFieldDetails>
  );
}

function BehaviorIntelligencePanel({ summary }: { summary: MemoryAtlas["behavior_intelligence"] }) {
  if (!summary || !summary.counts) return null;
  const clusters = summary.clusters.slice(0, 3);
  const loops = summary.low_value_loops.slice(0, 3);
  const opportunities = summary.opportunities.slice(0, 3);
  if (clusters.length === 0 && loops.length === 0 && opportunities.length === 0) return null;
  return (
    <section
      className="home-behavior-intelligence-panel"
      aria-label="S06 行为智能"
      data-home-section="behavior_intelligence"
      data-s06-review-display="behavior-clusters-low-value-loops-opportunities"
      data-s06-review-schema={summary.schema_version}
      data-s06-cluster-count={summary.counts.clusters}
      data-s06-loop-count={summary.counts.low_value_loops}
      data-s06-opportunity-count={summary.counts.opportunities}
    >
      <div className="panel-title-row">
        <h3>哪些行为模式值得调整</h3>
        <span>已完成行为归纳</span>
      </div>
      <div className="home-behavior-count-row" aria-label="S06 行为智能计数">
        <span><strong>{summary.counts.clusters.toLocaleString()}</strong>主题/层级簇</span>
        <span><strong>{summary.counts.low_value_loops.toLocaleString()}</strong>低价值循环</span>
        <span><strong>{summary.counts.opportunities.toLocaleString()}</strong>机会线索</span>
      </div>
      <div className="home-behavior-card-grid">
        <article className="home-behavior-card">
          <span>主题簇</span>
          {clusters.map((cluster) => (
            <div className="home-behavior-item" key={cluster.cluster_id}>
              <strong>{cluster.label_zh || cluster.cluster_id}</strong>
              <p>{cluster.summary_zh}</p>
              <small>{cluster.evidence_refs.length} 条证据引用 · {cluster.event_count.toLocaleString()} 条事件</small>
            </div>
          ))}
        </article>
        <article className="home-behavior-card">
          <span>低价值循环</span>
          {loops.map((loop) => (
            <div className="home-behavior-item" key={loop.loop_id}>
              <strong>{loop.label_zh || loop.loop_type}</strong>
              <p>{loop.summary_zh}</p>
              <small>{loop.decision_debt?.suggested_closure_question || `${loop.action_half_life_days ?? 0} 天行动半衰期`}</small>
            </div>
          ))}
        </article>
        <article className="home-behavior-card">
          <span>机会线索</span>
          {opportunities.map((opportunity) => (
            <div className="home-behavior-item" key={opportunity.opportunity_id}>
              <strong>{opportunity.label_zh || opportunity.opportunity_type}</strong>
              <p>{opportunity.summary_zh}</p>
              <small>{opportunity.next_step_zh || opportunity.why_not_now_card?.reason_zh}</small>
            </div>
          ))}
        </article>
      </div>
    </section>
  );
}

function ClioLikeVisualPanel({
  model,
  onSelectNode,
  onSwitchView,
}: {
  model: ClioLikeVisualModel;
  onSelectNode: (node: AtlasNode) => void;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [selectedClusterId, setSelectedClusterId] = useState(model.clusters[0]?.id ?? "");
  const selectedCluster = model.clusters.find((cluster) => cluster.id === selectedClusterId) ?? model.clusters[0] ?? null;
  const visualCopyById = new Map(model.visualCopy.map((visual) => [visual.id, visual]));
  const treeCopy = visualCopyById.get("cluster_tree");
  const bubbleCopy = visualCopyById.get("bubble_map");
  const explorerCopy = visualCopyById.get("topic_cluster_explorer");

  function openCluster(cluster: ClioClusterDatum | ClioTreeBranch | null, targetView: ViewKey) {
    if (!cluster) return;
    setSelectedClusterId(cluster.id);
    if (cluster.node) onSelectNode(cluster.node);
    onSwitchView(targetView);
  }

  return (
    <section
      className="clio-visual-panel"
      aria-label="S11 P1 Clio-like 多维可视化"
      data-home-section="clio_like_visuals"
      data-s11-p1-clio-like-visuals={CLIO_LIKE_VISUALS_VERSION}
      data-s11-p1-filter-source={model.activeFilters.source}
      data-s11-p1-filter-time={model.activeFilters.time}
      data-s11-p1-filter-project={model.activeFilters.project}
      data-s11-p1-filter-task={model.activeFilters.task}
    >
      <div className="panel-title-row">
        <div>
          <h3>主题如何聚合与变化</h3>
          <p>{model.summary}</p>
        </div>
        <span>{model.clusters.length.toLocaleString()} 个筛选后主题簇</span>
      </div>
      <div className="clio-filter-strip" aria-label="S11 P1 图谱过滤维度">
        <span><strong>来源</strong>{model.activeFilters.source}</span>
        <span><strong>时间</strong>{model.activeFilters.time}</span>
        <span><strong>项目</strong>{model.activeFilters.project}</span>
        <span><strong>任务</strong>{model.activeFilters.task}</span>
      </div>
      <div className="clio-visual-grid">
        <article
          className="clio-visual-card"
          data-s11-p1-action-value={treeCopy?.actionValue}
          data-s11-p1-human-question={treeCopy?.humanQuestion}
          data-s11-p1-interactive="true"
          data-s11-p1-visual-id="cluster_tree"
        >
          <div className="clio-visual-heading">
            <span>{treeCopy?.title}</span>
            <strong data-s11-p1-insight-header={treeCopy?.insightHeader}>{treeCopy?.insightHeader}</strong>
            <p>{treeCopy?.humanQuestion}</p>
            <em>{treeCopy?.actionValue}</em>
          </div>
          <svg className="cluster-tree-svg" viewBox="0 0 440 260" role="img" aria-label="层级簇树">
            <line className="cluster-tree-trunk" x1="70" y1="130" x2="174" y2="130" />
            <circle className="cluster-tree-root" cx="70" cy="130" r="30" />
            <text x="70" y="126" textAnchor="middle">当前</text>
            <text x="70" y="144" textAnchor="middle">筛选</text>
            {model.treeBranches.map((branch) => (
              <g
                className={branch.id === selectedCluster?.id ? "cluster-tree-branch active" : "cluster-tree-branch"}
                key={branch.id}
                onClick={() => openCluster(branch, "galaxy")}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") openCluster(branch, "galaxy");
                }}
                role="button"
                tabIndex={0}
              >
                <title>{`${branch.label}，${branch.count} 条记忆`}</title>
                <line x1={branch.x1} y1={branch.y1} x2={branch.x2} y2={branch.y2} />
                <circle cx={branch.x2} cy={branch.y2} r={Math.max(14, Math.min(30, branch.count + 12))} />
                <text x={branch.x2 + 36} y={branch.y2 - 4}>{branch.label}</text>
                <text x={branch.x2 + 36} y={branch.y2 + 14}>{branch.count} 条</text>
              </g>
            ))}
          </svg>
        </article>

        <article
          className="clio-visual-card"
          data-s11-p1-action-value={bubbleCopy?.actionValue}
          data-s11-p1-human-question={bubbleCopy?.humanQuestion}
          data-s11-p1-interactive="true"
          data-s11-p1-visual-id="bubble_map"
        >
          <div className="clio-visual-heading">
            <span>{bubbleCopy?.title}</span>
            <strong data-s11-p1-insight-header={bubbleCopy?.insightHeader}>{bubbleCopy?.insightHeader}</strong>
            <p>{bubbleCopy?.humanQuestion}</p>
            <em>{bubbleCopy?.actionValue}</em>
          </div>
          <svg className="bubble-map-svg" viewBox="0 0 440 260" role="img" aria-label="Bubble Map">
            <line className="bubble-axis" x1="56" y1="210" x2="396" y2="210" />
            <line className="bubble-axis" x1="56" y1="42" x2="56" y2="210" />
            <text className="bubble-axis-label" x="260" y="238">近期活跃度</text>
            <text className="bubble-axis-label" x="20" y="132" transform="rotate(-90 20 132)">ROI</text>
            {model.clusters.map((cluster) => (
              <g
                className={cluster.id === selectedCluster?.id ? "semantic-bubble active" : "semantic-bubble"}
                key={cluster.id}
                onClick={() => openCluster(cluster, "galaxy")}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") openCluster(cluster, "galaxy");
                }}
                role="button"
                tabIndex={0}
              >
                <title>{`${cluster.label}，ROI ${formatScore(cluster.roiScore)}，${cluster.count} 条记忆`}</title>
                <circle cx={cluster.x} cy={cluster.y} r={cluster.radius} fill={cluster.color} />
                <text x={cluster.x} y={cluster.y + cluster.radius + 14} textAnchor="middle">{cluster.label.slice(0, 8)}</text>
              </g>
            ))}
          </svg>
        </article>

        <article
          className="clio-visual-card topic-cluster-explorer"
          data-s11-p1-action-value={explorerCopy?.actionValue}
          data-s11-p1-human-question={explorerCopy?.humanQuestion}
          data-s11-p1-interactive="true"
          data-s11-p1-visual-id="topic_cluster_explorer"
        >
          <div className="clio-visual-heading">
            <span>{explorerCopy?.title}</span>
            <strong data-s11-p1-insight-header={explorerCopy?.insightHeader}>{explorerCopy?.insightHeader}</strong>
            <p>{explorerCopy?.humanQuestion}</p>
            <em>{explorerCopy?.actionValue}</em>
          </div>
          <div className="topic-cluster-explorer-list" aria-label="Topic Cluster Explorer">
            {model.explorerRows.map((cluster) => (
              <button
                className={cluster.id === selectedCluster?.id ? "active" : ""}
                data-clio-cluster-id={cluster.id}
                key={cluster.id}
                onClick={() => openCluster(cluster, "search")}
                type="button"
              >
                <strong>{cluster.label}</strong>
                <span>{cluster.count} 条 · ROI {formatScore(cluster.roiScore)}</span>
                <small>{cluster.dominantCategory} · {cluster.recentCount} 条近期 · {cluster.evidenceCount} 证据</small>
              </button>
            ))}
          </div>
          {selectedCluster ? (
            <div className="clio-selected-cluster" aria-label="选中簇行动说明">
              <span>{selectedCluster.label}</span>
              <strong>{selectedCluster.count} 条记忆，{selectedCluster.sourceCount} 个来源</strong>
              <p>下一步：打开查找与核对，复核代表记录后再比较投入回报。</p>
            </div>
          ) : null}
        </article>
      </div>
    </section>
  );
}

function EconomicLikeVisualPanel({
  model,
  onSelectNode,
  onSwitchView,
}: {
  model: EconomicLikeVisualModel;
  onSelectNode: (node: AtlasNode) => void;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [selectedTaskId, setSelectedTaskId] = useState(model.taskRows[0]?.id ?? "");
  const selectedTask = model.taskRows.find((task) => task.id === selectedTaskId) ?? model.taskRows[0] ?? null;
  const visualCopyById = new Map(model.visualCopy.map((visual) => [visual.id, visual]));
  const treemapCopy = visualCopyById.get("task_treemap");
  const automationCopy = visualCopyById.get("automation_vs_augmentation");
  const scatterCopy = visualCopyById.get("roi_scatter");
  const radarCopy = visualCopyById.get("opportunity_radar");
  const radarPoints = model.radarAxes
    .map((axis, index) => {
      const angle = -Math.PI / 2 + (index / Math.max(1, model.radarAxes.length)) * Math.PI * 2;
      const radius = 24 + axis.value * 76;
      return `${140 + Math.cos(angle) * radius},${120 + Math.sin(angle) * radius}`;
    })
    .join(" ");

  function openTask(task: EconomicTaskDatum | null, targetView: ViewKey) {
    if (!task) return;
    setSelectedTaskId(task.id);
    if (task.node) onSelectNode(task.node);
    onSwitchView(targetView);
  }

  return (
    <section
      className="economic-visual-panel"
      aria-label="S11 P2 Economic-like 多维可视化"
      data-home-section="economic_like_visuals"
      data-s11-p2-economic-like-visuals={ECONOMIC_LIKE_VISUALS_VERSION}
      data-s11-p2-filter-source={model.activeFilters.source}
      data-s11-p2-filter-time={model.activeFilters.time}
      data-s11-p2-filter-project={model.activeFilters.project}
      data-s11-p2-filter-task={model.activeFilters.task}
    >
      <div className="panel-title-row">
        <div>
          <h3>时间和精力投在哪里</h3>
          <p>{model.summary}</p>
        </div>
        <span>{model.taskRows.length.toLocaleString()} 个筛选后任务面</span>
      </div>
      <div className="economic-filter-strip" aria-label="S11 P2 图谱过滤维度">
        <span><strong>来源</strong>{model.activeFilters.source}</span>
        <span><strong>时间</strong>{model.activeFilters.time}</span>
        <span><strong>项目</strong>{model.activeFilters.project}</span>
        <span><strong>任务</strong>{model.activeFilters.task}</span>
      </div>
      <div className="economic-visual-grid">
        <article
          className="economic-visual-card task-treemap-card"
          data-s11-p2-action-value={treemapCopy?.actionValue}
          data-s11-p2-human-question={treemapCopy?.humanQuestion}
          data-s11-p2-interactive="true"
          data-s11-p2-visual-id="task_treemap"
        >
          <div className="economic-visual-heading">
            <span>{treemapCopy?.title}</span>
            <strong data-s11-p2-insight-header={treemapCopy?.insightHeader}>{treemapCopy?.insightHeader}</strong>
            <p>{treemapCopy?.humanQuestion}</p>
            <em>{treemapCopy?.actionValue}</em>
          </div>
          <div className="task-treemap" role="list" aria-label="Task Treemap">
            {model.taskRows.map((task) => (
              <button
                className={task.id === selectedTask?.id ? "active" : ""}
                key={task.id}
                onClick={() => openTask(task, "roi")}
                style={{ flexBasis: `${task.width}px`, minHeight: `${task.height}px`, borderColor: task.color }}
                type="button"
              >
                <strong>{task.label}</strong>
                <span>{task.count} 条 · ROI {formatScore(task.roiScore)}</span>
                <small>{task.sourceCount} 来源 · {task.recentCount} 近期</small>
              </button>
            ))}
          </div>
        </article>

        <article
          className="economic-visual-card automation-augmentation-card"
          data-s11-p2-action-value={automationCopy?.actionValue}
          data-s11-p2-human-question={automationCopy?.humanQuestion}
          data-s11-p2-interactive="true"
          data-s11-p2-visual-id="automation_vs_augmentation"
        >
          <div className="economic-visual-heading">
            <span>{automationCopy?.title}</span>
            <strong data-s11-p2-insight-header={automationCopy?.insightHeader}>{automationCopy?.insightHeader}</strong>
            <p>{automationCopy?.humanQuestion}</p>
            <em>{automationCopy?.actionValue}</em>
          </div>
          <div className="automation-augmentation-chart" aria-label="Automation vs Augmentation">
            {model.taskRows.slice(0, 5).map((task) => (
              <button
                className={task.id === selectedTask?.id ? "active" : ""}
                key={task.id}
                onClick={() => openTask(task, "search")}
                type="button"
              >
                <strong>{task.label}</strong>
                <span>
                  <i style={{ width: `${Math.round(task.automationShare * 100)}%` }} />
                  <b style={{ width: `${Math.round(task.augmentationShare * 100)}%` }} />
                </span>
                <small>自动化 {formatScore(task.automationShare)} · 增强 {formatScore(task.augmentationShare)}</small>
              </button>
            ))}
          </div>
        </article>

        <article
          className="economic-visual-card"
          data-s11-p2-action-value={scatterCopy?.actionValue}
          data-s11-p2-human-question={scatterCopy?.humanQuestion}
          data-s11-p2-interactive="true"
          data-s11-p2-visual-id="roi_scatter"
        >
          <div className="economic-visual-heading">
            <span>{scatterCopy?.title}</span>
            <strong data-s11-p2-insight-header={scatterCopy?.insightHeader}>{scatterCopy?.insightHeader}</strong>
            <p>{scatterCopy?.humanQuestion}</p>
            <em>{scatterCopy?.actionValue}</em>
          </div>
          <svg className="roi-scatter-svg" viewBox="0 0 440 260" role="img" aria-label="ROI Scatter">
            <line className="economic-axis" x1="58" y1="214" x2="398" y2="214" />
            <line className="economic-axis" x1="58" y1="44" x2="58" y2="214" />
            <text className="economic-axis-label" x="250" y="240">近期活跃度</text>
            <text className="economic-axis-label" x="22" y="132" transform="rotate(-90 22 132)">ROI</text>
            {model.scatterPoints.map((task) => (
              <g
                className={task.id === selectedTask?.id ? "roi-scatter-point active" : "roi-scatter-point"}
                key={task.id}
                onClick={() => openTask(task, "roi")}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") openTask(task, "roi");
                }}
                role="button"
                tabIndex={0}
              >
                <title>{`${task.label}，ROI ${formatScore(task.roiScore)}，机会 ${formatScore(task.opportunityScore)}`}</title>
                <circle cx={task.x} cy={task.y} fill={task.color} r={task.radius} />
              </g>
            ))}
          </svg>
        </article>

        <article
          className="economic-visual-card opportunity-radar-card"
          data-s11-p2-action-value={radarCopy?.actionValue}
          data-s11-p2-human-question={radarCopy?.humanQuestion}
          data-s11-p2-interactive="true"
          data-s11-p2-visual-id="opportunity_radar"
        >
          <div className="economic-visual-heading">
            <span>{radarCopy?.title}</span>
            <strong data-s11-p2-insight-header={radarCopy?.insightHeader}>{radarCopy?.insightHeader}</strong>
            <p>{radarCopy?.humanQuestion}</p>
            <em>{radarCopy?.actionValue}</em>
          </div>
          <svg className="opportunity-radar-svg" viewBox="0 0 280 240" role="img" aria-label="Opportunity Radar">
            <circle cx="140" cy="120" r="96" />
            <circle cx="140" cy="120" r="56" />
            <polygon points={radarPoints} />
            {model.radarAxes.map((axis, index) => {
              const angle = -Math.PI / 2 + (index / Math.max(1, model.radarAxes.length)) * Math.PI * 2;
              const x = 140 + Math.cos(angle) * 108;
              const y = 120 + Math.sin(angle) * 108;
              return (
                <g key={axis.id}>
                  <line x1="140" y1="120" x2={x} y2={y} />
                  <text x={x} y={y}>{axis.label}</text>
                </g>
              );
            })}
          </svg>
          {selectedTask ? (
            <button className="economic-selected-task" onClick={() => openTask(selectedTask, "summary")} type="button">
              <span>{selectedTask.label}</span>
              <strong>机会 {formatScore(selectedTask.opportunityScore)} · 风险 {formatScore(selectedTask.riskScore)}</strong>
              <small>打开总结闭环复核是否继续投入。</small>
            </button>
          ) : null}
        </article>
      </div>
    </section>
  );
}

function WorkflowLatentGovernanceVisualPanel({
  model,
  onSelectNode,
  onSwitchView,
}: {
  model: WorkflowLatentGovernanceVisualModel;
  onSelectNode: (node: AtlasNode) => void;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [selectedAxisId, setSelectedAxisId] = useState(model.latentAxes[0]?.id ?? "");
  const selectedAxis = model.latentAxes.find((axis) => axis.id === selectedAxisId) ?? model.latentAxes[0] ?? null;
  const visualCopyById = new Map(model.visualCopy.map((visual) => [visual.id, visual]));
  const sankeyCopy = visualCopyById.get("agent_decision_sankey");
  const heatmapCopy = visualCopyById.get("friction_heatmap");
  const radarCopy = visualCopyById.get("latent_radar");
  const timelineCopy = visualCopyById.get("evidence_timeline");
  const formulaCopy = visualCopyById.get("formula_explorer");
  const radarPoints = model.latentAxes
    .map((axis, index) => {
      const angle = -Math.PI / 2 + (index / Math.max(1, model.latentAxes.length)) * Math.PI * 2;
      const radius = 28 + axis.value * 78;
      return `${150 + Math.cos(angle) * radius},${126 + Math.sin(angle) * radius}`;
    })
    .join(" ");

  function openNode(node: AtlasNode | null, targetView: ViewKey) {
    if (node) onSelectNode(node);
    onSwitchView(targetView);
  }

  return (
    <section
      className="workflow-governance-visual-panel"
      aria-label="S11 P3 Workflow/latent/governance 多维可视化"
      data-home-section="workflow_latent_governance_visuals"
      data-s11-p3-workflow-latent-governance-visuals={WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION}
      data-s11-p3-filter-source={model.activeFilters.source}
      data-s11-p3-filter-time={model.activeFilters.time}
      data-s11-p3-filter-project={model.activeFilters.project}
      data-s11-p3-filter-task={model.activeFilters.task}
    >
      <div className="panel-title-row">
        <div>
          <h3>执行链路哪里需要治理</h3>
          <p>{model.summary}</p>
        </div>
        <span>{model.visualCopy.length.toLocaleString()} 张决策图</span>
      </div>
      <div className="workflow-governance-filter-strip" aria-label="S11 P3 图谱过滤维度">
        <span><strong>来源</strong>{model.activeFilters.source}</span>
        <span><strong>时间</strong>{model.activeFilters.time}</span>
        <span><strong>项目</strong>{model.activeFilters.project}</span>
        <span><strong>任务</strong>{model.activeFilters.task}</span>
      </div>
      <div className="workflow-governance-visual-grid">
        <article
          className="workflow-governance-visual-card sankey-card"
          data-s11-p3-action-value={sankeyCopy?.actionValue}
          data-s11-p3-human-question={sankeyCopy?.humanQuestion}
          data-s11-p3-interactive="true"
          data-s11-p3-visual-id="agent_decision_sankey"
        >
          <div className="workflow-governance-visual-heading">
            <span>{sankeyCopy?.title}</span>
            <strong data-s11-p3-insight-header={sankeyCopy?.insightHeader}>{sankeyCopy?.insightHeader}</strong>
            <p>{sankeyCopy?.humanQuestion}</p>
            <em>{sankeyCopy?.actionValue}</em>
          </div>
          <svg className="workflow-sankey-svg" viewBox="0 0 520 250" role="img" aria-label="Codex/Agent Decision Sankey">
            <text x="24" y="36">人类目标</text>
            <text x="160" y="36">Codex 执行</text>
            <text x="300" y="36">验证复审</text>
            <text x="426" y="36">治理/授权</text>
            {model.sankeyLinks.map((link, index) => {
              const y = link.y;
              const startX = 48 + index * 78;
              const endX = startX + 124;
              return (
                <g
                  className="workflow-sankey-link"
                  key={link.id}
                  onClick={() => openNode(link.node, "summary")}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") openNode(link.node, "summary");
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <title>{`${link.sourceLabel} 到 ${link.targetLabel}：${link.value} 条证据`}</title>
                  <path
                    d={`M ${startX} ${y} C ${startX + 48} ${y - 34}, ${endX - 48} ${y + 34}, ${endX} ${y}`}
                    stroke={link.color}
                    strokeWidth={link.width}
                  />
                  <circle cx={startX} cy={y} r="7" />
                  <circle cx={endX} cy={y} r="7" />
                  <text x={startX - 16} y={y + 31}>{link.sourceLabel}</text>
                  <text x={endX - 18} y={y - 22}>{link.targetLabel}</text>
                </g>
              );
            })}
          </svg>
        </article>

        <article
          className="workflow-governance-visual-card"
          data-s11-p3-action-value={heatmapCopy?.actionValue}
          data-s11-p3-human-question={heatmapCopy?.humanQuestion}
          data-s11-p3-interactive="true"
          data-s11-p3-visual-id="friction_heatmap"
        >
          <div className="workflow-governance-visual-heading">
            <span>{heatmapCopy?.title}</span>
            <strong data-s11-p3-insight-header={heatmapCopy?.insightHeader}>{heatmapCopy?.insightHeader}</strong>
            <p>{heatmapCopy?.humanQuestion}</p>
            <em>{heatmapCopy?.actionValue}</em>
          </div>
          <div className="friction-heatmap-grid" aria-label="Friction Heatmap">
            {model.frictionCells.map((cell) => (
              <button
                key={cell.id}
                onClick={() => openNode(cell.node, "search")}
                style={{ "--heat": cell.intensity, "--cell-color": workflowHeatColor(cell.intensity) } as CSSProperties}
                type="button"
              >
                <strong>{cell.rowLabel}</strong>
                <span>{cell.columnLabel}</span>
                <small>{cell.count} 条 · {cell.action}</small>
              </button>
            ))}
          </div>
        </article>

        <article
          className="workflow-governance-visual-card latent-radar-card"
          data-s11-p3-action-value={radarCopy?.actionValue}
          data-s11-p3-human-question={radarCopy?.humanQuestion}
          data-s11-p3-interactive="true"
          data-s11-p3-visual-id="latent_radar"
        >
          <div className="workflow-governance-visual-heading">
            <span>{radarCopy?.title}</span>
            <strong data-s11-p3-insight-header={radarCopy?.insightHeader}>{radarCopy?.insightHeader}</strong>
            <p>{radarCopy?.humanQuestion}</p>
            <em>{radarCopy?.actionValue}</em>
          </div>
          <svg className="latent-radar-svg" viewBox="0 0 300 260" role="img" aria-label="Latent Radar">
            <circle cx="150" cy="126" r="106" />
            <circle cx="150" cy="126" r="66" />
            <polygon points={radarPoints} />
            {model.latentAxes.map((axis, index) => {
              const angle = -Math.PI / 2 + (index / Math.max(1, model.latentAxes.length)) * Math.PI * 2;
              const x = 150 + Math.cos(angle) * 118;
              const y = 126 + Math.sin(angle) * 118;
              return (
                <g
                  className={axis.id === selectedAxis?.id ? "latent-radar-axis active" : "latent-radar-axis"}
                  key={axis.id}
                  onClick={() => {
                    setSelectedAxisId(axis.id);
                    openNode(axis.node, "summary");
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      setSelectedAxisId(axis.id);
                      openNode(axis.node, "summary");
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <line x1="150" y1="126" x2={x} y2={y} />
                  <text x={x} y={y}>{axis.label}</text>
                </g>
              );
            })}
          </svg>
          {selectedAxis ? (
            <button className="latent-radar-selected" onClick={() => openNode(selectedAxis.node, "summary")} type="button">
              <span>{selectedAxis.label}</span>
              <strong>{formatScore(selectedAxis.value)} · {selectedAxis.confidenceLabel} · 证据 {selectedAxis.evidenceBadge}</strong>
              <small>打开总结闭环，验证或降权这条潜性信号。</small>
            </button>
          ) : null}
        </article>

        <article
          className="workflow-governance-visual-card"
          data-s11-p3-action-value={timelineCopy?.actionValue}
          data-s11-p3-human-question={timelineCopy?.humanQuestion}
          data-s11-p3-interactive="true"
          data-s11-p3-visual-id="evidence_timeline"
        >
          <div className="workflow-governance-visual-heading">
            <span>{timelineCopy?.title}</span>
            <strong data-s11-p3-insight-header={timelineCopy?.insightHeader}>{timelineCopy?.insightHeader}</strong>
            <p>{timelineCopy?.humanQuestion}</p>
            <em>{timelineCopy?.actionValue}</em>
          </div>
          <div className="evidence-timeline-track" aria-label="Evidence Timeline">
            {model.evidenceEvents.map((event) => (
              <button
                key={event.id}
                onClick={() => openNode(event.node, "timeline")}
                style={{ left: `${event.x}%` }}
                type="button"
              >
                <strong>{event.dateLabel}</strong>
                <span>{event.label}</span>
                <small>{event.sourceLabel} · 证据 {event.evidenceCount}</small>
              </button>
            ))}
          </div>
        </article>

        <article
          className="workflow-governance-visual-card"
          data-s11-p3-action-value={formulaCopy?.actionValue}
          data-s11-p3-human-question={formulaCopy?.humanQuestion}
          data-s11-p3-interactive="true"
          data-s11-p3-visual-id="formula_explorer"
        >
          <div className="workflow-governance-visual-heading">
            <span>{formulaCopy?.title}</span>
            <strong data-s11-p3-insight-header={formulaCopy?.insightHeader}>{formulaCopy?.insightHeader}</strong>
            <p>{formulaCopy?.humanQuestion}</p>
            <em>{formulaCopy?.actionValue}</em>
          </div>
          <MachineFieldDetails title="查看公式参数与来源" className="formula-technical-details">
            <div className="formula-explorer-list" aria-label="Formula Explorer/Parameter Inspector">
              {model.formulaRows.map((row) => (
                <button key={row.id} onClick={() => openNode(row.node, "roi")} type="button">
                  <span>{row.label}</span>
                  <strong>{row.value}</strong>
                  <small>{row.description}</small>
                  <em>{row.sourcePath}</em>
                </button>
              ))}
            </div>
          </MachineFieldDetails>
        </article>
      </div>
    </section>
  );
}

function HumanQuestionMapPanel({
  model,
  onSwitchView,
}: {
  model: HumanQuestionMapModel;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [familyFilter, setFamilyFilter] = useState<HumanQuestionMapFamilyId | "all">("all");
  const visibleEntries = familyFilter === "all" ? model.entries : model.entries.filter((entry) => entry.familyId === familyFilter);
  const familyOptions: Array<{ id: HumanQuestionMapFamilyId | "all"; label: string; count: number }> = [
    { id: "all", label: "全部问题", count: model.entries.length },
    { id: "clio_like", label: "主题/簇", count: model.entries.filter((entry) => entry.familyId === "clio_like").length },
    { id: "economic_like", label: "ROI/任务", count: model.entries.filter((entry) => entry.familyId === "economic_like").length },
    { id: "workflow_governance", label: "工作流/治理", count: model.entries.filter((entry) => entry.familyId === "workflow_governance").length },
  ];

  return (
    <section
      className="human-question-map-panel"
      aria-label="S11 P4 Human Question Map"
      data-home-section="human_question_map"
      data-s11-p4-human-question-map={HUMAN_QUESTION_MAP_VERSION}
      data-s11-p4-filter-source={model.activeFilters.source}
      data-s11-p4-filter-time={model.activeFilters.time}
      data-s11-p4-filter-project={model.activeFilters.project}
      data-s11-p4-filter-task={model.activeFilters.task}
    >
      <div className="panel-title-row">
        <div>
          <h3>问题如何连接到行动</h3>
          <p>{model.summary}</p>
        </div>
        <span>{model.p0VisualCount.toLocaleString()} 张可行动图谱</span>
      </div>
      <div className="human-question-map-gate-row" aria-label="S11 P4 Visual ROI Gate 汇总">
        <span><strong>{model.p0VisualCount.toLocaleString()}</strong>已纳入</span>
        <span><strong>{model.failedP0Count.toLocaleString()}</strong>未通过</span>
        <span><strong>{model.excludedCandidates.length.toLocaleString()}</strong>候选排除</span>
        <span><strong>{model.strongestGateLabel}</strong>最强决策族</span>
      </div>
      <div className="human-question-map-filter-strip" aria-label="S11 P4 图谱过滤维度">
        <span><strong>来源</strong>{model.activeFilters.source}</span>
        <span><strong>时间</strong>{model.activeFilters.time}</span>
        <span><strong>项目</strong>{model.activeFilters.project}</span>
        <span><strong>任务</strong>{model.activeFilters.task}</span>
      </div>
      <div className="human-question-map-family-tabs" aria-label="Human Question Map family filter">
        {familyOptions.map((option) => (
          <button
            className={familyFilter === option.id ? "active" : ""}
            key={option.id}
            onClick={() => setFamilyFilter(option.id)}
            type="button"
          >
            <span>{option.label}</span>
            <strong>{option.count.toLocaleString()}</strong>
          </button>
        ))}
      </div>
      <div className="human-question-map-grid">
        {visibleEntries.map((entry) => (
          <button
            className="human-question-map-entry"
            data-s11-p4-action-value={entry.actionValue}
            data-s11-p4-family={entry.familyId}
            data-s11-p4-human-question={entry.humanQuestion}
            data-s11-p4-interactive="true"
            data-s11-p4-map-entry="true"
            data-s11-p4-p0-included={entry.p0Included ? "true" : "false"}
            data-s11-p4-visual-id={entry.id}
            data-s11-p4-visual-roi-gate={entry.visualRoiGatePass ? "pass" : "fail"}
            key={entry.id}
            onClick={() => onSwitchView(entry.targetView)}
            type="button"
          >
            <span>{entry.familyLabel}</span>
            <strong>{entry.title}</strong>
            <em>{entry.insightHeader}</em>
            <p>{entry.humanQuestion}</p>
            <small>{entry.actionValue}</small>
            <b>{entry.gateReason}</b>
          </button>
        ))}
      </div>
      <div className="human-question-map-exclusion-list" aria-label="Visual ROI Gate 未进 P0 候选">
        {model.excludedCandidates.map((candidate) => (
          <span data-s11-p4-p0-included="false" data-s11-p4-visual-roi-gate="fail" key={candidate.id}>
            <strong>{candidate.title}</strong>
            <small>{candidate.reason}</small>
          </span>
        ))}
      </div>
    </section>
  );
}

function HomeOverviewView({
  atlas,
  nodes,
  graphEdges,
  clioLikeVisualModel,
  economicLikeVisualModel,
  workflowLatentGovernanceVisualModel,
  humanQuestionMapModel,
  deltaStats,
  selectedNode,
  sharedState,
  timelineTimeRange,
  onSelectNode,
  onSwitchView,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  graphEdges: AtlasEdge[];
  clioLikeVisualModel: ClioLikeVisualModel;
  economicLikeVisualModel: EconomicLikeVisualModel;
  workflowLatentGovernanceVisualModel: WorkflowLatentGovernanceVisualModel;
  humanQuestionMapModel: HumanQuestionMapModel;
  deltaStats: DeltaStats;
  selectedNode: AtlasNode | null;
  sharedState: SharedAtlasState;
  timelineTimeRange: TimelineTimeRangeSelection | null;
  onSelectNode: (node: AtlasNode) => void;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [selectedActionDetail, setSelectedActionDetail] = useState<HomeActionDetail | null>(null);
  const [selectedTierAsset, setSelectedTierAsset] = useState<TierAssetDetail | null>(null);
  const [selectedTopicDetail, setSelectedTopicDetail] = useState<TopicClassificationDetail | null>(null);
  const model = useMemo(
    () => buildHomeOverviewModel(nodes, graphEdges, deltaStats),
    [deltaStats, graphEdges, nodes],
  );
  const actionStatusChips = buildHomeActionStatusChips(model.actions);
  const levelAssetGroupChips = buildLevelAssetGroupChips(model.tierAssets);
  const themeCategoryChips = buildThemeCategoryChips(model.topicDetails);
  const behaviorIntelligence = atlas.behavior_intelligence;
  const arrivalBriefing = useMemo(
    () => buildHomeArrivalBriefing(atlas, nodes, model, deltaStats),
    [atlas, deltaStats, model, nodes],
  );

  function runAction(action: HomeActionDetail) {
    const runtimeAction = model.actions.find((item) => item.action_id === action.action_id);
    if (!runtimeAction) return;
    if (runtimeAction.node) onSelectNode(runtimeAction.node);
    onSwitchView(runtimeAction.targetView);
  }

  function openActionDetail(action: HomeAction) {
    setSelectedActionDetail(action);
  }

  function openActionTarget(action: HomeActionDetail) {
    runAction(action);
  }

  function closeActionDetail() {
    setSelectedActionDetail(null);
  }

  function openTierAsset(asset: HomeTierAsset) {
    setSelectedTierAsset(asset);
  }

  function openTierAssetTarget(asset: TierAssetDetail) {
    const runtimeAsset = model.tierAssets.find((item) => item.asset_id === asset.asset_id);
    if (!runtimeAsset) return;
    if (runtimeAsset.node) onSelectNode(runtimeAsset.node);
    onSwitchView(runtimeAsset.targetView);
  }

  function closeTierAsset() {
    setSelectedTierAsset(null);
  }

  function openTopicDetail(topic: HomeTopicDetail) {
    setSelectedTopicDetail(topic);
  }

  function openTopicTarget(topic: TopicClassificationDetail) {
    const runtimeTopic = model.topicDetails.find((item) => item.topic_id === topic.topic_id);
    if (!runtimeTopic) return;
    if (runtimeTopic.node) onSelectNode(runtimeTopic.node);
    onSwitchView(runtimeTopic.targetView);
  }

  function closeTopicDetail() {
    setSelectedTopicDetail(null);
  }

  function jumpToPreview(node: AtlasNode | null, targetView: ViewKey) {
    if (node) onSelectNode(node);
    onSwitchView(targetView);
  }

  return (
    <div
      className="home-overview-view visual-workspace"
      data-memory-overview-operations={MEMORY_OVERVIEW_OPERATION_VERSION}
      data-memory-overview-structure={MEMORY_OVERVIEW_STRUCTURE_VERSION}
      data-shared-state={sharedState.schema_version}
      data-shared-focus-node={sharedState.focus.home.nodeId ?? ""}
      data-shared-cluster={sharedState.focus.home.clusterId ?? ""}
      data-shared-time-range={sharedState.focus.home.timeRangeId ?? ""}
    >
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">{uiCopy.overview.eyebrow}</p>
          <h2>{uiCopy.overview.title}</h2>
        </div>
        <span>{timelineRangeSummary(timelineTimeRange) ?? `${nodes.length.toLocaleString()} 条筛选记忆 · ${uiCopy.overview.defaultEntry}`}</span>
      </div>
      <section
        className="home-arrival-briefing"
        aria-labelledby="home-arrival-briefing-title"
        data-home-arrival-question={uiCopy.overview.arrivalQuestion}
        data-home-section="arrival_briefing"
        data-s10-p1-home-arrival-briefing={HOME_ARRIVAL_BRIEFING_VERSION}
      >
        <div className="arrival-briefing-heading">
          <div>
            <span>{uiCopy.overview.arrivalQuestion}</span>
            <h3 id="home-arrival-briefing-title">{uiCopy.overview.arrivalTitle}</h3>
            <p>{uiCopy.overview.arrivalDescription}</p>
          </div>
          <button type="button" onClick={() => onSwitchView("summary")}>
            <LayoutDashboard size={16} />
            <span>{uiCopy.overview.arrivalSummaryAction}</span>
          </button>
        </div>
        <div className="arrival-briefing-grid">
          {arrivalBriefing.map((card) => {
            const Icon = card.icon;
            return (
              <button
                className={`arrival-briefing-card ${card.tone}`}
                data-home-arrival-category={card.id}
                data-home-arrival-machine-signal={card.machineSignal}
                key={card.id}
                onClick={() => jumpToPreview(card.node, card.targetView)}
                type="button"
              >
                <span className="arrival-briefing-card-label">
                  <Icon size={16} />
                  {card.label}
                </span>
                <strong>{card.value}</strong>
                <p>{card.summary}</p>
                <small>{card.evidence}</small>
                <em className="arrival-briefing-next-step">下一步：{card.nextStep}</em>
              </button>
            );
          })}
        </div>
        <MachineFieldDetails title={uiCopy.overview.arrivalMachineDetails} className="arrival-briefing-machine-details">
          <p className="machine-field-help">默认折叠。这里仅用于核验首页 arrival briefing 合约、快照时间和 no-apply 边界。</p>
          <dl>
            <div><dt>contract / 合约版本</dt><dd>{HOME_ARRIVAL_BRIEFING_VERSION}</dd></div>
            <div><dt>snapshot / 快照时间</dt><dd>{atlas.overview.generated_at || "not_loaded"}</dd></div>
            <div><dt>rawMutation / raw 修改</dt><dd>false</dd></div>
            <div><dt>proposalApply / 提案应用</dt><dd>false</dd></div>
          </dl>
        </MachineFieldDetails>
      </section>
      <nav className="home-structure-rail" aria-label="记忆总览默认页结构">
        {MEMORY_OVERVIEW_SECTION_ORDER.map((section) => (
          <span data-home-section-anchor={section.id} key={section.id}>{section.label}</span>
        ))}
      </nav>
      <section className="home-shared-focus-strip" aria-label="共享焦点" data-home-section="status_summary">
        <span>当前判断焦点</span>
        <strong>{selectedNode ? humanNodeDisplayTitle(selectedNode) : uiCopy.overview.defaultFocus}</strong>
        <small>{sharedState.focus.home.clusterId ?? uiCopy.overview.noTopic} · 证据已同步</small>
      </section>
      <section className="home-primary-band" aria-label="当前认知状态">
        <article
          className={`home-weather-panel ${model.weatherV2.tone}`}
          data-home-section="weather"
          data-memory-weather-v2="true"
          data-weather-confidence={model.weatherV2.confidenceScore.toFixed(2)}
          data-weather-risk={model.weatherV2.riskScore.toFixed(2)}
        >
          <span>{uiCopy.overview.weatherTitle}</span>
          <strong>{model.weatherV2.label}</strong>
          <p>{model.weatherV2.summary}</p>
          <dl className="home-weather-v2-scores" aria-label="记忆天气 v2 评分信号">
            <div><dt>稳定度</dt><dd>{formatScore(model.weatherV2.stabilityScore)}</dd></div>
            <div><dt>动量</dt><dd>{formatScore(model.weatherV2.momentumScore)}</dd></div>
            <div><dt>风险</dt><dd>{formatScore(model.weatherV2.riskScore)}</dd></div>
            <div><dt>机会</dt><dd>{formatScore(model.weatherV2.opportunityScore)}</dd></div>
          </dl>
          <ul className="home-weather-v2-signals">
            {model.weatherV2.signals.map((signal) => (
              <li key={signal}>{signal}</li>
            ))}
          </ul>
        </article>
        <div className="home-weather-metrics">
          <div data-home-section="themes"><Metric label="主导主题" value={model.topicRows[0]?.count ?? 0} /></div>
          <div data-home-section="proto_stars"><Metric label="上升机会" value={model.protoStarCount} /></div>
          <div data-home-section="black_holes"><Metric label="风险循环" value={model.blackHoleCount} /></div>
          <div data-home-section="status_summary"><Metric label="近期增量" value={deltaStats.recentCount} /></div>
        </div>
      </section>
      <section className="home-status-grid" aria-label="当前判断状态卡片">
        {model.signals.map((signal) => (
          <article className={`home-status-card ${signal.tone}`} key={signal.id}>
            <span>{signal.title}</span>
            <strong>{signal.value}</strong>
            <p>{signal.note}</p>
          </article>
        ))}
      </section>
      <BehaviorIntelligencePanel summary={behaviorIntelligence} />
      <ClioLikeVisualPanel model={clioLikeVisualModel} onSelectNode={onSelectNode} onSwitchView={onSwitchView} />
      <EconomicLikeVisualPanel model={economicLikeVisualModel} onSelectNode={onSelectNode} onSwitchView={onSwitchView} />
      <WorkflowLatentGovernanceVisualPanel model={workflowLatentGovernanceVisualModel} onSelectNode={onSelectNode} onSwitchView={onSwitchView} />
      <HumanQuestionMapPanel model={humanQuestionMapModel} onSwitchView={onSwitchView} />
      <section className="home-preview-grid" aria-label={uiCopy.overview.previewAria} data-home-section="entry_points">
        <button
          className="home-preview-card mini-starfield-preview"
          onClick={() => jumpToPreview(model.miniStarfieldFocus, "galaxy")}
          type="button"
        >
          <div className="panel-title-row">
            <h3>{uiCopy.overview.miniStarfieldTitle}</h3>
            <span>{uiCopy.overview.miniStarfieldAction}</span>
          </div>
          <svg viewBox="0 0 420 190" role="img" aria-label={uiCopy.overview.miniStarfieldAria}>
            <defs>
              <radialGradient id="homeStarfieldGlow" cx="50%" cy="50%" r="60%">
                <stop offset="0%" stopColor="rgba(126, 232, 212, 0.38)" />
                <stop offset="54%" stopColor="rgba(72, 199, 232, 0.11)" />
                <stop offset="100%" stopColor="rgba(2, 3, 8, 0)" />
              </radialGradient>
            </defs>
            <rect className="home-starfield-nebula" x="10" y="10" width="400" height="170" rx="18" />
            <ellipse className="home-starfield-disk" cx="210" cy="96" rx="170" ry="58" />
            {model.miniStarfieldPoints.map((point) => (
              <g className="home-star-point" key={point.id}>
                <title>{point.label}</title>
                <circle cx={point.x} cy={point.y} r={point.radius + 5} fill={point.color} opacity="0.08" />
                <circle cx={point.x} cy={point.y} r={point.radius} fill={point.color} />
              </g>
            ))}
          </svg>
          <small>{model.miniStarfieldSummary}</small>
        </button>
        <button
          className="home-preview-card river-pulse-preview"
          onClick={() => jumpToPreview(model.riverPulseFocus, "timeline")}
          type="button"
        >
          <div className="panel-title-row">
            <h3>{uiCopy.overview.riverPulseTitle}</h3>
            <span>{uiCopy.overview.riverPulseAction}</span>
          </div>
          <div className="river-pulse-lanes" aria-label="近期主题增强和衰退">
            {model.riverPulseSegments.map((segment) => (
              <div className={segment.delta >= 0 ? "river-pulse-row rising" : "river-pulse-row declining"} key={segment.id}>
                <span>{segment.label}</span>
                <i style={{ "--pulse-width": `${segment.intensity}%` } as CSSProperties} aria-hidden="true" />
                <b>{formatSigned(segment.delta)}</b>
              </div>
            ))}
          </div>
          <small>{uiCopy.overview.riverPulseNote}</small>
        </button>
      </section>
      <section
        className="home-action-panel"
        aria-label="下一步行动建议"
        data-home-operation-mode="proposal_only"
        data-home-operation-section="top_actions"
        data-home-section="suggested_actions"
        data-top-actions-section={HOME_ACTION_SECTION_VERSION}
      >
        <div className="panel-title-row">
          <h3>{uiCopy.overview.nextBestActionsTitle}</h3>
          <span>{uiCopy.overview.proposalOnlyLabel}</span>
        </div>
        <div className="home-section-summary-row" aria-label="Top Actions Section fields">
          <span className="home-operation-chip" data-top-actions-field="suggestion">
            <strong>建议</strong>
            <small>{model.actions.length.toLocaleString()} 条行动建议</small>
          </span>
          <span className="home-operation-chip" data-top-actions-field="reason">
            <strong>依据</strong>
            <small>来自当前快照的派生分析</small>
          </span>
          <span className="home-operation-chip" data-top-actions-field="priority">
            <strong>优先级</strong>
            <small>{humanPriorityLabel(model.actions[0]?.priority)}</small>
          </span>
          <span className="home-operation-chip" data-top-actions-field="status">
            <strong>状态</strong>
            <small>{actionStatusChips.map((chip) => `${chip.label}:${chip.count}`).join(" / ")}</small>
          </span>
        </div>
        <div className="home-action-list">
          {model.actions.map((action) => (
            <button
              data-next-action-card={action.action_id}
              data-next-action-detail-entry="ActionDetailDrawer"
              data-next-action-roi={action.roi_score.toFixed(2)}
              data-next-action-status={action.status}
              data-next-action-urgency={action.urgency}
              key={action.id}
              onClick={() => openActionDetail(action)}
              type="button"
            >
              <span>{humanPriorityLabel(action.priority)}</span>
              <strong>{action.title}</strong>
              <div className="home-action-meta-grid" aria-label="建议动作排序信号">
                <i>ROI {formatScore(action.roi_score)}</i>
                <i>{humanEffortLabel(action.effort_cost)}</i>
                <i>{humanUrgencyLabel(action.urgency)}</i>
                <i className="home-action-status">{humanActionStatusLabel(action.status)}</i>
                <i>{action.evidence_count} 证据</i>
              </div>
              <small>{action.reason}</small>
              <em className="home-action-next-step">{action.next_step}</em>
            </button>
          ))}
        </div>
        <div data-action-detail-drawer-host="true" data-top-action-detail-host="ActionDetailDrawer">
          <ActionDetailDrawer action={selectedActionDetail} onClose={closeActionDetail} onOpenTarget={openActionTarget} />
        </div>
      </section>
      <section className="home-inspector-panel" aria-label={uiCopy.overview.inspectorTitle} data-home-section="entry_points">
        <div className="panel-title-row">
          <h3>{uiCopy.overview.inspectorTitle}</h3>
          <span>{uiCopy.overview.inspectorHint}</span>
        </div>
        <div className="home-inspector-link-list">
          {model.inspectorLinks.map((link) => (
            <button key={link.id} onClick={() => jumpToPreview(link.node, "search")} type="button">
              <strong>{link.title}</strong>
              <span>{link.meta}</span>
            </button>
          ))}
        </div>
      </section>
      <section
        className="home-tier-asset-panel"
        aria-label="层级资产明细"
        data-home-operation-mode="proposal_only"
        data-home-operation-section="level_assets"
        data-home-section="assets"
        data-level-assets-section={HOME_LEVEL_ASSET_SECTION_VERSION}
      >
        <div className="panel-title-row">
          <h3>层级资产明细</h3>
          <span>仅生成提案</span>
        </div>
        <div className="home-operation-chip-grid" aria-label="Level Assets Section groups">
          {levelAssetGroupChips.map((group) => (
            <span
              className="home-operation-chip"
              data-level-asset-count={group.count}
              data-level-asset-group={group.id}
              key={group.id}
            >
              <strong>{group.label}</strong>
              <small>{group.count.toLocaleString()} 项资产</small>
            </span>
          ))}
        </div>
        {model.tierAssets.length ? (
          <div className="home-tier-asset-grid">
            {model.tierAssets.map((asset) => (
              <button
                className="home-tier-asset-card"
                data-tier-asset-card={asset.asset_id}
                data-tier-asset-detail-entry="AssetDetailPanel"
                data-tier-asset-staleness={asset.staleness_status}
                data-tier-asset-value={asset.value_score.toFixed(2)}
                key={asset.id}
                onClick={() => openTierAsset(asset)}
                type="button"
              >
                <span>{asset.asset_tier}</span>
                <strong>{asset.title}</strong>
                <div className="tier-asset-meta-grid" aria-label="层级资产排序信号">
                  <i>{asset.theme}</i>
                  <i>价值 {formatScore(asset.value_score)}</i>
                  <i>{asset.importance}</i>
                  <i>{asset.staleness_status}</i>
                </div>
                <small>{asset.summary}</small>
                <em>{asset.evidence_count} 证据 · {asset.recommended_asset_action}</em>
              </button>
            ))}
          </div>
        ) : (
          <div className="home-tier-asset-empty">当前筛选下没有足够的层级资产明细；请放宽筛选或等待新的 redacted snapshot。</div>
        )}
        <div data-asset-detail-host="AssetDetailPanel" data-asset-detail-panel-host="true">
          <AssetDetailPanel asset={selectedTierAsset} onClose={closeTierAsset} onOpenTarget={openTierAssetTarget} />
        </div>
      </section>
      <section
        className="home-topic-detail-panel"
        aria-label="主题分类明细"
        data-home-operation-mode="proposal_only"
        data-home-operation-section="theme_categories"
        data-home-section="themes"
        data-theme-categories-section={HOME_THEME_CATEGORY_SECTION_VERSION}
      >
        <div className="panel-title-row">
          <h3>主题分类明细</h3>
          <span>仅生成提案</span>
        </div>
        <div className="home-operation-chip-grid" aria-label="Theme Categories Section states">
          {themeCategoryChips.map((state) => (
            <span
              className="home-operation-chip"
              data-theme-category-count={state.count}
              data-theme-category-state={state.id}
              key={state.id}
            >
              <strong>{state.label}</strong>
              <small>{state.count.toLocaleString()} 个主题</small>
            </span>
          ))}
        </div>
        {model.topicDetails.length ? (
          <div className="home-topic-detail-grid">
            {model.topicDetails.map((topic) => (
              <button
                className="home-topic-detail-card"
                data-theme-category-detail-entry="ThemeDetailPanel"
                data-topic-detail-card={topic.topic_id}
                data-topic-state={topic.topic_state}
                data-topic-strength={topic.topic_strength.toFixed(2)}
                key={topic.id}
                onClick={() => openTopicDetail(topic)}
                type="button"
              >
                <span>{topic.topic_state}</span>
                <strong>{topic.topic_label}</strong>
                <div className="topic-detail-meta-grid" aria-label="主题分类排序信号">
                  <i>{topic.category}</i>
                  <i>强度 {formatScore(topic.topic_strength)}</i>
                  <i>{topic.trend}</i>
                  <i>{topic.record_count} 条记录</i>
                </div>
                <small>{topic.matched_reason}</small>
                <em>{topic.evidence_refs.length} 证据 · {topic.starfield_handoff}</em>
              </button>
            ))}
          </div>
        ) : (
          <div className="home-tier-asset-empty">当前筛选下没有足够的主题分类明细；请放宽筛选或等待新的 redacted snapshot。</div>
        )}
        <div data-theme-category-detail-host="ThemeDetailPanel" data-theme-detail-panel-host="true">
          <ThemeDetailPanel topic={selectedTopicDetail} onClose={closeTopicDetail} onOpenTarget={openTopicTarget} />
        </div>
      </section>
      <section className="home-topic-strip" aria-label="主导主题趋势">
        <MiniBarList title={uiCopy.overview.dominantTopics} rows={model.topicRows} />
        <MiniBarList title={uiCopy.overview.memoryTiers} rows={model.tierRows} />
        <MiniBarList title={uiCopy.overview.semanticCategories} rows={model.categoryRows} />
      </section>
    </div>
  );
}

function buildHomeActionStatusChips(actions: HomeAction[]): Array<{ id: HomeActionDetail["status"]; label: string; count: number }> {
  const statuses: HomeActionDetail["status"][] = ["proposed", "review", "blocked", "done_safe"];
  return statuses.map((status) => ({
    count: actions.filter((action) => action.status === status).length,
    id: status,
    label: humanActionStatusLabel(status),
  }));
}

function humanPriorityLabel(priority?: string): string {
  return ({ P0: "立即判断", P1: "优先处理", P2: "随后处理", P3: "持续观察" } as Record<string, string>)[priority ?? ""] ?? "待判断";
}

function humanActionStatusLabel(status: HomeActionDetail["status"]): string {
  return ({ proposed: "待判断", review: "待复核", blocked: "受阻", done_safe: "已安全完成" } as Record<HomeActionDetail["status"], string>)[status];
}

function humanEffortLabel(effort: HomeActionDetail["effort_cost"]): string {
  return ({ low: "低投入", medium: "中等投入", high: "高投入" } as Record<HomeActionDetail["effort_cost"], string>)[effort];
}

function humanUrgencyLabel(urgency: HomeActionDetail["urgency"]): string {
  return ({ low: "低紧迫", medium: "中等紧迫", high: "高紧迫" } as Record<HomeActionDetail["urgency"], string>)[urgency];
}

type HomeLevelAssetGroupId = (typeof HOME_LEVEL_ASSET_GROUPS)[number]["id"];
type HomeThemeCategoryStateId = (typeof HOME_THEME_CATEGORY_STATES)[number]["id"];

function buildLevelAssetGroupChips(assets: HomeTierAsset[]): Array<{ id: HomeLevelAssetGroupId; label: string; count: number }> {
  return HOME_LEVEL_ASSET_GROUPS.map((group) => ({
    count: assets.filter((asset) => homeLevelAssetGroupFor(asset) === group.id).length,
    id: group.id,
    label: group.label,
  }));
}

function homeLevelAssetGroupFor(asset: TierAssetDetail): HomeLevelAssetGroupId {
  if (asset.asset_tier === "core_profile") return "core_profile";
  if (asset.asset_tier === "project") return "project";
  if (asset.asset_tier === "decision") return "decision";
  if (asset.asset_tier === "stale" || asset.staleness_status === "stale") return "stale";
  return "temporary";
}

function buildThemeCategoryChips(topics: HomeTopicDetail[]): Array<{ id: HomeThemeCategoryStateId; label: string; count: number }> {
  return HOME_THEME_CATEGORY_STATES.map((state) => ({
    count: topics.filter((topic) => homeThemeCategoryFor(topic) === state.id).length,
    id: state.id,
    label: state.label,
  }));
}

function homeThemeCategoryFor(topic: TopicClassificationDetail): HomeThemeCategoryStateId {
  if (topic.topic_state === "rising") return "rising";
  if (topic.topic_state === "declining" || topic.topic_state === "stale" || topic.topic_state === "black_hole") return "declining";
  if (topic.topic_state === "conflict") return "conflict";
  if (topic.topic_state === "emerging" || (topic.roi_score >= 0.58 && topic.trend !== "down")) return "opportunity";
  return "stable";
}

function GalaxyView({
  graphNodes,
  graphEdges,
  memoryCount,
  selectedNode,
  sharedState,
  deltaStats,
  timelineTimeRange,
  starfieldMapping,
  onSelectNode,
}: {
  graphNodes: AtlasNode[];
  graphEdges: AtlasEdge[];
  memoryCount: number;
  selectedNode: AtlasNode | null;
  sharedState: SharedAtlasState;
  deltaStats: DeltaStats;
  timelineTimeRange: TimelineTimeRangeSelection | null;
  starfieldMapping: StarfieldMappingResult;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const [galaxyRendererMode, setGalaxyRendererMode] = useState<GalaxyRendererMode>(() => getInitialGalaxyRendererMode());

  function updateGalaxyRendererMode(mode: GalaxyRendererMode) {
    setGalaxyRendererMode(mode);
    persistGalaxyRendererMode(mode);
  }

  useEffect(() => {
    window.__memoryAtlasStage4Phase3 = () => ({
      integrationVersion: STARFIELD_INTEGRATION_VERSION,
      mappingVersion: STARFIELD_MAPPING_VERSION,
      rendererMode: galaxyRendererMode,
      mappingSource: starfieldMapping.source,
      mappedParticleCount: starfieldMapping.particleCount,
      snapshotMappedCount: starfieldMapping.snapshotMappedCount,
      fallbackCount: starfieldMapping.fallbackCount,
      safety: starfieldMapping.safety,
      formulas: starfieldMapping.formulas,
    });
    return () => {
      delete window.__memoryAtlasStage4Phase3;
    };
  }, [galaxyRendererMode, starfieldMapping]);

  return (
    <div
      className="galaxy-view"
      data-stage4-phase3-integration={STARFIELD_INTEGRATION_VERSION}
      data-starfield-mapping-version={starfieldMapping.version}
      data-starfield-mapping-source={starfieldMapping.source}
      data-shared-state={sharedState.schema_version}
      data-shared-focus-node={sharedState.focus.galaxy.nodeId ?? ""}
      data-shared-cluster={sharedState.focus.galaxy.clusterId ?? ""}
    >
      <div className="surface-heading">
        <div>
          <p className="eyebrow">语义银河 / 记忆关系 / 增量观察</p>
          <h2>按主题关系探索记忆密度、局部邻域和近期增量</h2>
        </div>
        <div className="galaxy-heading-actions">
          <span>{memoryCount} 条记忆 / {graphNodes.length} 个节点 / {graphEdges.length} 条连接</span>
          {timelineTimeRange ? <span className="timeline-sync-pill">时间河选择 · {timelineTimeRange.label}</span> : null}
          <div className="galaxy-renderer-toggle" aria-label="Galaxy renderer feature flag">
            <button
              aria-pressed={galaxyRendererMode === "memory-starfield"}
              onClick={() => updateGalaxyRendererMode("memory-starfield")}
              type="button"
            >
              Flow Field
            </button>
            <button
              aria-pressed={galaxyRendererMode === "legacy"}
              onClick={() => updateGalaxyRendererMode("legacy")}
              type="button"
            >
              Legacy
            </button>
          </div>
        </div>
      </div>
      <DeltaStrip stats={deltaStats} />
      <Suspense fallback={<div className="galaxy-loading">正在载入 Three.js 银河...</div>}>
        <GalaxyScene nodes={graphNodes} edges={graphEdges} rendererMode={galaxyRendererMode} selectedNode={selectedNode} starfieldMapping={starfieldMapping} onSelectNode={onSelectNode} />
      </Suspense>
    </div>
  );
}

function DataGuideMap({
  nodes,
  edges,
  selectedNode,
  deltaStats,
  parentSnapshotId,
  onSelectNode,
}: {
  nodes: AtlasNode[];
  edges: AtlasEdge[];
  selectedNode: AtlasNode | null;
  deltaStats: DeltaStats;
  parentSnapshotId: string;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const display = useMemo(() => buildDataGuideLayout(nodes, edges, 64), [nodes, edges]);
  const [selectedDataMapRelationId, setSelectedDataMapRelationId] = useState<string | null>(null);
  const selectedRelation = useMemo(
    () => display.edges.find((edge) => edge.id === selectedDataMapRelationId) ?? null,
    [display.edges, selectedDataMapRelationId],
  );

  useEffect(() => {
    window.__memoryAtlasStage6Phase1 = () => ({
      structureModelVersion: DATA_MAP_STRUCTURE_MODEL_VERSION,
      relationExplanationVersion: DATA_MAP_RELATION_EXPLANATION_VERSION,
      layers: DATA_MAP_STRUCTURE_LAYERS.map((layer) => layer.id),
      visibleNodeCount: display.visibleNodeCount,
      relationCount: display.edgeCount,
      selectedRelationId: selectedDataMapRelationId,
      defaultCollapsed: true,
      boundary: "No Phase 6.2 editing",
      rawPrivateDataIncluded: false,
      directActiveMemoryWriteback: false,
      proposalWrite: false,
    });
    return () => {
      delete window.__memoryAtlasStage6Phase1;
    };
  }, [display.edgeCount, display.visibleNodeCount, selectedDataMapRelationId]);

  useEffect(() => {
    window.__memoryAtlasStage6Phase2 = () => ({
      detailPanelVersion: DATA_MAP_DETAIL_PANEL_VERSION,
      proposalEntryVersion: DATA_MAP_PROPOSAL_ENTRY_VERSION,
      selectedNodeId: selectedNode?.id ?? null,
      selectedNodeKind: selectedNode?.kind ?? null,
      detailFields: ["asset", "theme", "suggested_action", "importance", "priority"],
      proposalOnly: true,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
    });
    return () => {
      delete window.__memoryAtlasStage6Phase2;
    };
  }, [selectedNode?.id, selectedNode?.kind]);

  return (
    <div
      className="visual-workspace data-guide-map"
      data-data-map-structure-model={DATA_MAP_STRUCTURE_MODEL_VERSION}
      data-data-map-relation-version={DATA_MAP_RELATION_EXPLANATION_VERSION}
      data-default-collapsed="true"
      data-no-phase-6-2="No Phase 6.2 editing"
      data-proposal-write="false"
      data-direct-active-memory-writeback="false"
      data-raw-private-data-included="false"
    >
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">数据导图 / 框架关系 / 行动入口</p>
          <h2>把当前数据切片整理成来源、画像、项目决策和下一步行动的框架导图</h2>
        </div>
        <span>{display.visibleNodeCount} 个可见节点 / {display.edgeCount} 条框架连接</span>
      </div>
      <GraphUsageStrip
        items={[
          { label: "读法", value: "从左到右" },
          { label: "框架", value: "来源 → 画像 → 项目 → 行动" },
          { label: "点击关系", value: "解释为什么连接" },
        ]}
      />
      <div className="data-map-layer-strip" aria-label="Stage 6 Phase 6.1 四层结构">
        {DATA_MAP_STRUCTURE_LAYERS.map((layer) => (
          <span key={layer.id} data-data-map-layer={layer.id}>
            <b>{layer.label}</b>
            <em>{layer.nodeTypes.join(" / ")}</em>
          </span>
        ))}
      </div>
      <DeltaStrip stats={deltaStats} compact />
      <svg className="data-guide-canvas" viewBox="0 0 1000 620" role="img" aria-label="数据导图框架">
        <defs>
          <filter id="dataGuideGlow">
            <feGaussianBlur stdDeviation="2.2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <marker id="dataGuideArrow" markerHeight="8" markerWidth="8" orient="auto" refX="7" refY="4">
            <path d="M0,0 L8,4 L0,8 Z" fill="rgba(244, 241, 232, 0.42)" />
          </marker>
        </defs>
        <path className="data-guide-flow" d="M78 76 C260 46 420 46 594 76 S824 108 930 78" />
        {display.frames.map((frame) => (
          <g
            className="data-guide-frame"
            key={frame.id}
            data-data-map-layer={frame.structureLayerId}
            data-node-types={frame.nodeTypes.join(",")}
            data-fields={frame.fields.join(",")}
            data-interaction={frame.interaction}
            data-detail-entry={frame.detailEntry}
          >
            <rect x={frame.x} y={frame.y} width={frame.w} height={frame.h} rx="14" fill={frame.color} opacity="0.035" />
            <rect x={frame.x} y={frame.y} width={frame.w} height={frame.h} rx="14" fill="none" stroke={frame.color} opacity="0.34" />
            <text x={frame.x + 18} y={frame.y + 30} className="data-guide-frame-title">{frame.title}</text>
            <text x={frame.x + 18} y={frame.y + 52} className="data-guide-frame-subtitle">{frame.subtitle}</text>
            <text x={frame.x + frame.w - 18} y={frame.y + 30} textAnchor="end" className="data-guide-frame-count">{frame.count}</text>
          </g>
        ))}
        <g className="data-guide-links">
          {display.edges.map((edge) => {
            const selected = edge.id === selectedDataMapRelationId;
            return (
              <g key={edge.id}>
                <path
                  className={selected ? "data-guide-link selected" : "data-guide-link"}
                  d={edge.path}
                  stroke={edge.color}
                  strokeWidth={edge.strokeWidth}
                />
                <path
                  className="data-guide-relation-hitbox"
                  d={edge.path}
                  role="button"
                  tabIndex={0}
                  aria-label={`关系解释：${edge.explanation.sourceLabel} 到 ${edge.explanation.targetLabel}`}
                  data-data-map-relation-explanation={DATA_MAP_RELATION_EXPLANATION_VERSION}
                  data-selected={selected ? "true" : "false"}
                  data-relation-source={edge.explanation.source}
                  data-relation-strength={edge.explanation.strength}
                  data-relation-evidence={edge.explanation.evidence}
                  data-relation-time={edge.explanation.time}
                  onClick={() => setSelectedDataMapRelationId(edge.id)}
                  onKeyDown={(event) => {
                    if (isActivationKey(event)) setSelectedDataMapRelationId(edge.id);
                  }}
                >
                  <title>{edge.explanation.reason}</title>
                </path>
              </g>
            );
          })}
        </g>
        {display.nodes.map((item) => (
          <DataGuideSvgNode
            key={item.node.id}
            item={item}
            selected={item.node.id === selectedNode?.id}
            onSelectNode={onSelectNode}
          />
        ))}
      </svg>
      <div className="map-legend">
        <LegendItem color="#8fd3ff" label="数据源与主题" />
        <LegendItem color="#7ee8d4" label="个人画像与偏好" />
        <LegendItem color="#f48fb1" label="项目、决策、规则" />
        <LegendItem color="#94a3b8" label="行动、机会、待整理" />
      </div>
      <DataMapRelationPanel relation={selectedRelation} />
      <DataMapNodeDetailPanel node={selectedNode} edges={edges} parentSnapshotId={parentSnapshotId} />
    </div>
  );
}

function DataMapRelationPanel({ relation }: { relation: DataGuideEdge | null }) {
  const explanation = relation?.explanation;
  return (
    <section
      className={relation ? "data-map-relation-panel active" : "data-map-relation-panel"}
      aria-label="关系解释"
      data-selected-relation-id={relation?.id ?? ""}
      data-relation-source={explanation?.source ?? "默认折叠"}
      data-relation-strength={explanation?.strength ?? "默认折叠"}
      data-relation-evidence={explanation?.evidence ?? "默认折叠"}
      data-relation-time={explanation?.time ?? "默认折叠"}
    >
      <div className="panel-title-row">
        <h2>关系解释</h2>
        <span>为什么连接 / source / strength / evidence / time</span>
      </div>
      {explanation ? (
        <>
          <p className="data-map-relation-reason">{explanation.reason}</p>
          <div className="data-map-relation-grid">
            <span>
              <b>来源</b>
              <em>{explanation.source}</em>
            </span>
            <span>
              <b>强度</b>
              <em>{explanation.strength}</em>
            </span>
            <span>
              <b>证据</b>
              <em>{explanation.evidence}</em>
            </span>
            <span>
              <b>时间</b>
              <em>{explanation.time}</em>
            </span>
          </div>
        </>
      ) : (
        <p className="data-map-relation-reason">默认折叠。点击任意关系线查看为什么连接、来源、强度、证据和时间。</p>
      )}
      <p className="data-map-relation-safe-flags">
        No Phase 6.2 editing · proposalWrite: false · directActiveMemoryWriteback: false · rawPrivateDataIncluded: false
      </p>
    </section>
  );
}

function DataMapNodeDetailPanel({
  node,
  edges,
  parentSnapshotId,
}: {
  node: AtlasNode | null;
  edges: AtlasEdge[];
  parentSnapshotId: string;
}) {
  const detail = useMemo(() => buildDataMapNodeDetail(node, edges), [edges, node]);
  return (
    <section
      className={node ? "data-map-node-detail-panel active" : "data-map-node-detail-panel"}
      aria-label="数据导图详情面板"
      data-data-map-detail-panel={DATA_MAP_DETAIL_PANEL_VERSION}
      data-selected-node-id={node?.id ?? ""}
      data-node-kind={node?.kind ?? ""}
      data-asset={detail.asset}
      data-theme={detail.theme}
      data-suggested-action={detail.suggestedAction}
      data-importance={detail.importance}
      data-priority={detail.priority}
      data-evidence-count={detail.evidenceRefs.length}
    >
      <div className="panel-title-row">
        <h2>数据导图详情面板</h2>
        <span>{DATA_MAP_DETAIL_PANEL_VERSION}</span>
      </div>
      {node ? (
        <>
          <div className="data-map-node-detail-heading">
            <span>{translateKind(node.kind)} / {detail.layerLabel}</span>
            <h3>{humanNodeDisplayTitle(node)}</h3>
            <p>{detail.summary}</p>
          </div>
          <dl className="data-map-node-detail-grid">
            <div><dt>资产</dt><dd>{detail.asset}</dd></div>
            <div><dt>主题</dt><dd>{detail.theme}</dd></div>
            <div><dt>建议动作</dt><dd>{detail.suggestedAction}</dd></div>
            <div><dt>重要性</dt><dd>{detail.importance}</dd></div>
            <div><dt>优先级</dt><dd>{detail.priority}</dd></div>
            <div><dt>状态</dt><dd>{detail.status}</dd></div>
          </dl>
          <section className="data-map-node-detail-section" aria-label="证据摘要">
            <span>证据</span>
            <ul className="data-map-node-evidence-list">
              {detail.evidenceRefs.map((ref) => (
                <li key={ref}>{ref}</li>
              ))}
            </ul>
          </section>
          <div className="data-map-detail-safety-strip" aria-label="Data Map Phase 6.2 safety">
            <span>仅生成提案</span>
            <span>不直接写长期记忆</span>
            <span>不执行 Stage 6 review</span>
          </div>
          <div
            className="data-map-proposal-entry"
            data-data-map-proposal-entry={DATA_MAP_PROPOSAL_ENTRY_VERSION}
            data-proposal-mode="proposal_only"
            data-proposal-only="true"
            data-active-memory-mutation="false"
            data-direct-active-memory-writeback="false"
            data-source-surface="data_guide_detail_panel"
          >
            <div className="panel-title-row">
              <h3>数据导图 proposal 入口</h3>
              <span>{DATA_MAP_PROPOSAL_ENTRY_VERSION}</span>
            </div>
            <ProposalEditor
              node={node}
              parentSnapshotId={parentSnapshotId}
              sourceSurface="data_guide_detail_panel"
            />
          </div>
        </>
      ) : (
        <p className="data-map-node-detail-empty">点击数据导图节点查看资产、主题、建议动作、重要性和优先级；编辑入口只导出 proposal。</p>
      )}
    </section>
  );
}

function RoiDashboard({
  atlas,
  nodes,
  deltaStats,
  onSelectNode,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const tierValues = filteredMetricValues(nodes, "memory_tier");
  const categoryValues = filteredMetricValues(nodes, "category");
  const globalTierValues = metricValues(atlas, "tier");
  const tierRows = topRows(tierValues, 4);
  const categoryRows = topRows(remapValues(categoryValues, humanCategoryLabel), 8);
  const actionRows = topRows(countBy(nodes, (node) => translateAction(node.metrics?.roi?.recommended_action)), 5);
  const highLeverage = [...nodes]
    .sort((a, b) => (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0))
    .slice(0, 12);
  return (
    <div className="dashboard-grid">
      <InsightCard title="当前切片密度" value={nodes.length} note={`全库 ${atlas.overview.active_memory_count.toLocaleString()} 条中的筛选结果`} />
      <InsightCard title="长期资产密度" value={sumValues(tierValues, ["核心画像", "一般"])} note="当前筛选中的核心画像 + 一般" />
      <InsightCard title="临时信息池" value={tierValues["临时"] ?? 0} note={`全局临时 ${globalTierValues["临时"] ?? 0} 条；保留但低权重召回`} />
      <InsightCard title="近期增量" value={deltaStats.recentCount} note={`近 30 天较前 30 天 ${formatSigned(deltaStats.deltaCount)} 条`} />
      <section className="wide-panel roi-visual-strip" aria-label="ROI 视觉密度分布">
        <div className="panel-title-row">
          <h2>ROI 视觉分布</h2>
          <span>层级、分类和建议动作同步当前筛选</span>
        </div>
        <div className="roi-mini-bars">
          <MiniBarList title="层级资产" rows={tierRows} />
          <MiniBarList title="主题分类" rows={categoryRows} />
          <MiniBarList title="建议动作" rows={actionRows} />
        </div>
      </section>
      <section className="wide-panel">
        <div className="panel-title-row">
          <h2>优先观察的高杠杆记忆</h2>
          <span>当前分类热点：{topEntry(categoryValues)?.[0] ?? "暂无"}</span>
        </div>
        <ol>
          {highLeverage.map((node) => (
            <li key={node.id}>
              <button onClick={() => onSelectNode(node)} type="button">
                <strong>{formatScore(node.metrics?.roi?.leverage_score)}</strong>
                <span>{node.label}</span>
                <small>{translateAction(node.metrics?.roi?.recommended_action)} / {translateStaleness(node.metrics?.roi?.staleness_status)}</small>
              </button>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function ObsidianGraph({
  nodes,
  edges,
  selectedNode,
  sharedState,
  deltaStats,
  onSelectNode,
}: {
  nodes: AtlasNode[];
  edges: AtlasEdge[];
  selectedNode: AtlasNode | null;
  sharedState: SharedAtlasState;
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  return (
    <Suspense fallback={<div className="galaxy-loading">正在载入 Obsidian 动态图谱...</div>}>
      <ObsidianGraphScene nodes={nodes} edges={edges} selectedNode={selectedNode} sharedFocus={sharedState.focus} deltaStats={deltaStats} onSelectNode={onSelectNode} />
    </Suspense>
  );
}

function TimelineView({
  timeline,
  nodeMap,
  selectedNode,
  sharedState,
  selectedTimelineRange,
  deltaStats,
  onSelectNode,
  onSelectTimelineRange,
  onClearTimelineRange,
}: {
  timeline: TimelineEvent[];
  nodeMap: Map<string, AtlasNode>;
  selectedNode: AtlasNode | null;
  sharedState: SharedAtlasState;
  selectedTimelineRange: TimelineTimeRangeSelection | null;
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
  onSelectTimelineRange: (range: TimelineTimeRangeSelection) => void;
  onClearTimelineRange: () => void;
}) {
  const [timelineZoom, setTimelineZoom] = useState(1);
  const [timelineCenter, setTimelineCenter] = useState(0.5);
  const [timelineCursor, setTimelineCursor] = useState(1);
  const [timelinePlaying, setTimelinePlaying] = useState(false);
  const [hoveredEventId, setHoveredEventId] = useState<string | null>(null);
  const [lockedEventId, setLockedEventId] = useState<string | null>(null);
  const [interactionMode, setInteractionMode] = useState<TimelineInteractionMode>("pan");
  const [brushDraft, setBrushDraft] = useState<TimelineBrushDraft | null>(null);
  const [panDraft, setPanDraft] = useState<TimelinePanDraft | null>(null);
  const [feedbackSettings, setFeedbackSettings] = useState<TimelineFeedbackSettings>(() => getInitialTimelineFeedbackSettings());
  const [timelineRendererMode, setTimelineRendererMode] = useState<TimelineRendererMode>(() => getInitialTimelineRendererMode());
  const display = useMemo(
    () => buildTimelineLayout(timeline, nodeMap, { zoom: timelineZoom, center: timelineCenter, cursor: timelineCursor }),
    [timeline, nodeMap, timelineCenter, timelineCursor, timelineZoom],
  );
  const riverDisplay = useMemo(() => buildMemoryRiverLayout(display.events, display.cursorX), [display.cursorX, display.events]);
  const selectedRangeOverlay = useMemo(() => buildMemoryRiverRangeOverlay(selectedTimelineRange, display), [display, selectedTimelineRange]);
  const brushDraftOverlay = brushDraft ? buildMemoryRiverDraftOverlay(brushDraft) : null;
  const lockedEvent = useMemo(() => display.events.find((event) => event.id === lockedEventId) ?? null, [display.events, lockedEventId]);
  const hoveredRiverEvent = useMemo(() => display.events.find((event) => event.id === hoveredEventId) ?? null, [display.events, hoveredEventId]);
  const hoveredEvent = useMemo(
    () => hoveredRiverEvent ?? display.events.find((event) => event.source.node_id === selectedNode?.id) ?? display.events[display.events.length - 1] ?? null,
    [display.events, hoveredRiverEvent, selectedNode?.id],
  );
  const activeRiverEvent = lockedEvent ?? hoveredRiverEvent;

  useEffect(() => {
    window.__memoryAtlasStage5Phase3 = () => ({
      integrationVersion: TIMELINE_RENDERER_FEATURE_FLAG_VERSION,
      rendererMode: timelineRendererMode,
      defaultRendererMode: DEFAULT_TIMELINE_RENDERER_MODE,
      legacyRollbackEnabled: true,
      visibleEventCount: display.visibleCount,
      totalEventCount: display.totalCount,
      selectedRangeActive: Boolean(selectedTimelineRange),
      selectedRange: selectedTimelineRange,
      evidenceLayers: [...riverDisplay.evidenceLayers.map((layer) => layer.kind), "roi-gradient"],
      levelCounts: riverDisplay.levelCounts,
      feedback: {
        reducedMotion: feedbackSettings.reducedMotion,
        pseudoHaptic: feedbackSettings.pseudoHaptic,
        audio: feedbackSettings.audio,
      },
      safety: {
        rawPrivateDataIncluded: false,
        directActiveMemoryWriteback: false,
        proposalWrite: false,
      },
    });
    return () => {
      delete window.__memoryAtlasStage5Phase3;
    };
  }, [
    display.totalCount,
    display.visibleCount,
    feedbackSettings.audio,
    feedbackSettings.pseudoHaptic,
    feedbackSettings.reducedMotion,
    riverDisplay.evidenceLayers,
    riverDisplay.levelCounts,
    selectedTimelineRange,
    timelineRendererMode,
  ]);

  useEffect(() => {
    setTimelinePlaying(false);
    setTimelineCursor(1);
  }, [timeline.length]);

  useEffect(() => {
    if (!timelinePlaying || feedbackSettings.reducedMotion) return undefined;
    const timer = window.setInterval(() => {
      setTimelineCursor((current) => {
        if (current >= 0.995) {
          setTimelinePlaying(false);
          return 1;
        }
        return Math.min(1, current + 0.012);
      });
    }, 180);
    return () => window.clearInterval(timer);
  }, [feedbackSettings.reducedMotion, timelinePlaying]);

  useEffect(() => {
    if (feedbackSettings.reducedMotion) setTimelinePlaying(false);
    persistTimelineFeedbackSettings(feedbackSettings);
  }, [feedbackSettings]);

  const clampTimelineCenter = useCallback((value: number) => {
    setTimelineCenter(Math.min(1, Math.max(0, value)));
  }, []);
  const clampTimelineZoom = useCallback((value: number) => {
    setTimelineZoom(Math.min(8, Math.max(1, Number(value.toFixed(2)))));
  }, []);
  const handleTimelineWheel = useCallback((event: WheelEvent<SVGSVGElement>) => {
    event.preventDefault();
    clampTimelineZoom(timelineZoom + (event.deltaY < 0 ? 0.45 : -0.45));
  }, [clampTimelineZoom, timelineZoom]);
  const handleMemoryRiverPointerDown = useCallback((event: PointerEvent<SVGSVGElement>) => {
    if (timelineRendererMode !== "memory-river") return;
    event.preventDefault();
    const x = memoryRiverPointerX(event);
    setTimelinePlaying(false);
    if (interactionMode === "brush") {
      setBrushDraft({ pointerId: event.pointerId, startX: x, endX: x });
    } else {
      setPanDraft({ pointerId: event.pointerId, startX: x, startCenter: timelineCenter });
    }
    event.currentTarget.setPointerCapture(event.pointerId);
  }, [interactionMode, timelineCenter, timelineRendererMode]);
  const handleMemoryRiverPointerMove = useCallback((event: PointerEvent<SVGSVGElement>) => {
    if (timelineRendererMode !== "memory-river") return;
    const x = memoryRiverPointerX(event);
    if (brushDraft && event.pointerId === brushDraft.pointerId) {
      event.preventDefault();
      setBrushDraft({ ...brushDraft, endX: x });
      return;
    }
    if (panDraft && event.pointerId === panDraft.pointerId) {
      event.preventDefault();
      const deltaRatio = (x - panDraft.startX) / MEMORY_RIVER_WIDTH / Math.max(1, timelineZoom);
      clampTimelineCenter(panDraft.startCenter - deltaRatio);
    }
  }, [brushDraft, clampTimelineCenter, panDraft, timelineRendererMode, timelineZoom]);
  const handleMemoryRiverPointerUp = useCallback((event: PointerEvent<SVGSVGElement>) => {
    if (timelineRendererMode !== "memory-river") return;
    if (brushDraft && event.pointerId === brushDraft.pointerId) {
      event.preventDefault();
      const endX = memoryRiverPointerX(event);
      const nextDraft = { ...brushDraft, endX };
      const selection = buildTimelineRangeSelection(display, nextDraft.startX, nextDraft.endX);
      if (selection) {
        onSelectTimelineRange(selection);
        setTimelineCursor(memoryRiverXToRatio((clampMemoryRiverX(nextDraft.startX) + clampMemoryRiverX(nextDraft.endX)) / 2));
        emitTimelineFeedback(feedbackSettings, "brush");
      }
      setBrushDraft(null);
      event.currentTarget.releasePointerCapture(event.pointerId);
      return;
    }
    if (panDraft && event.pointerId === panDraft.pointerId) {
      event.preventDefault();
      setPanDraft(null);
      emitTimelineFeedback(feedbackSettings, "pan");
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }, [brushDraft, display, feedbackSettings, onSelectTimelineRange, panDraft, timelineRendererMode]);
  const handleMemoryRiverPointerCancel = useCallback((event: PointerEvent<SVGSVGElement>) => {
    if (brushDraft?.pointerId === event.pointerId) setBrushDraft(null);
    if (panDraft?.pointerId === event.pointerId) setPanDraft(null);
  }, [brushDraft?.pointerId, panDraft?.pointerId]);

  function resetTimelineView() {
    setTimelineZoom(1);
    setTimelineCenter(0.5);
    setTimelineCursor(1);
    setTimelinePlaying(false);
    setBrushDraft(null);
    setPanDraft(null);
    setLockedEventId(null);
    onClearTimelineRange();
  }

  function updateTimelineRendererMode(mode: TimelineRendererMode) {
    setTimelineRendererMode(mode);
    persistTimelineRendererMode(mode);
  }

  function updateFeedbackSettings(patch: Partial<TimelineFeedbackSettings>) {
    setFeedbackSettings((current) => {
      const next = { ...current, ...patch };
      if (next.reducedMotion) setTimelinePlaying(false);
      return next;
    });
  }

  function lockMemoryRiverEvent(event: TimelineDisplayEvent) {
    setLockedEventId(event.id);
    setHoveredEventId(event.id);
    if (event.node) onSelectNode(event.node);
    emitTimelineFeedback(feedbackSettings, "event");
  }

  return (
    <div
      className="visual-workspace timeline-map"
      data-timeline-renderer={timelineRendererMode}
      data-default-timeline-renderer={DEFAULT_TIMELINE_RENDERER_MODE}
      data-stage5-phase3-integration={TIMELINE_RENDERER_FEATURE_FLAG_VERSION}
      data-shared-state={sharedState.schema_version}
      data-shared-focus-node={sharedState.focus.timeline.nodeId ?? ""}
      data-shared-time-range={sharedState.focus.timeline.timeRangeId ?? ""}
    >
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">{timelineRendererMode === "memory-river" ? "记忆时间河 / UTC Time Scale / Theme Lanes" : "时间轴 / 动态窗口 / 事件密度"}</p>
          <h2>{timelineRendererMode === "memory-river" ? "按 Macro / Meso / Micro 河道观察主题、项目和记忆如何增强、衰退和迁移" : "按真实日期播放、缩放和定位记忆、决策、项目事件"}</h2>
        </div>
        <span>{display.visibleCount} / {display.totalCount} 个事件 · {display.rangeLabel}</span>
      </div>
      <DeltaStrip stats={deltaStats} compact />
      <div className="timeline-control-bar" aria-label="时间轴控制">
        <div className="timeline-renderer-toggle" aria-label="Timeline renderer feature flag">
          <button
            aria-pressed={timelineRendererMode === "memory-river"}
            onClick={() => updateTimelineRendererMode("memory-river")}
            type="button"
          >
            Memory River
          </button>
          <button
            aria-pressed={timelineRendererMode === "legacy"}
            onClick={() => updateTimelineRendererMode("legacy")}
            type="button"
          >
            Legacy
          </button>
        </div>
        <button aria-label={timelinePlaying ? "暂停时间轴播放" : "播放时间轴"} className="icon-control" onClick={() => setTimelinePlaying((value) => !value)} disabled={feedbackSettings.reducedMotion} type="button">
          {timelinePlaying ? <Pause size={15} /> : <Play size={15} />}
        </button>
        <button aria-label="缩小时间窗口" className="icon-control" onClick={() => clampTimelineZoom(timelineZoom - 0.5)} disabled={timelineZoom <= 1} type="button">
          <ZoomOut size={15} />
        </button>
        <button aria-label="放大时间窗口" className="icon-control" onClick={() => clampTimelineZoom(timelineZoom + 0.5)} disabled={timelineZoom >= 8} type="button">
          <ZoomIn size={15} />
        </button>
        <label className="timeline-range-control">
          <span>窗口</span>
          <input aria-label="时间窗口中心" max="1" min="0" onChange={(event) => clampTimelineCenter(Number(event.target.value))} step="0.01" type="range" value={timelineCenter} />
        </label>
        <label className="timeline-range-control">
          <span>游标</span>
          <input aria-label="时间播放游标" max="1" min="0" onChange={(event) => setTimelineCursor(Number(event.target.value))} step="0.01" type="range" value={timelineCursor} />
        </label>
        <button className="segmented" onClick={resetTimelineView} type="button">
          <RotateCcw size={14} />
          重置
        </button>
        <span className="timeline-zoom-readout">{timelineZoom.toFixed(1)}x · {display.cursorLabel}</span>
      </div>
      <div
        className="memory-river-interaction-bar"
        data-interaction-mode={interactionMode}
        data-reduced-motion={feedbackSettings.reducedMotion ? "true" : "false"}
        data-feedback-pseudo-haptic={feedbackSettings.pseudoHaptic ? "enabled" : "disabled"}
        data-feedback-audio={feedbackSettings.audio ? "enabled" : "disabled"}
        data-feedback-defaults={feedbackSettings.pseudoHaptic || feedbackSettings.audio ? "opted-in" : "silent-by-default"}
        aria-label="记忆时间河交互设置"
      >
        <div className="river-mode-tabs" role="group" aria-label="记忆时间河交互模式">
          <button aria-pressed={interactionMode === "pan"} onClick={() => setInteractionMode("pan")} type="button">
            Pan
          </button>
          <button aria-pressed={interactionMode === "brush"} onClick={() => setInteractionMode("brush")} type="button">
            Brush
          </button>
        </div>
        <span className="timeline-range-readout">
          {selectedTimelineRange
            ? `${selectedTimelineRange.label} · ${selectedTimelineRange.eventCount.toLocaleString()} 事件 · ${selectedTimelineRange.topTheme}`
            : interactionMode === "brush"
              ? "拖拽选择时间段；选择会同步到首页、星系和交互焦点"
              : "在河道区域横向拖拽平移；滚轮缩放，选择不会丢失"}
        </span>
        <label className="feedback-toggle">
          <input
            checked={feedbackSettings.reducedMotion}
            onChange={(event) => updateFeedbackSettings({ reducedMotion: event.target.checked })}
            type="checkbox"
          />
          <span>Reduced Motion</span>
        </label>
        <label className="feedback-toggle">
          <input
            checked={feedbackSettings.pseudoHaptic}
            onChange={(event) => updateFeedbackSettings({ pseudoHaptic: event.target.checked })}
            type="checkbox"
          />
          <span>伪触感</span>
        </label>
        <label className="feedback-toggle">
          <input
            checked={feedbackSettings.audio}
            onChange={(event) => updateFeedbackSettings({ audio: event.target.checked })}
            type="checkbox"
          />
          <span>音频</span>
        </label>
        <button className="segmented" disabled={!selectedTimelineRange} onClick={onClearTimelineRange} type="button">
          清除区间
        </button>
      </div>
      <div className="timeline-summary-grid" aria-label="时间轴摘要">
        <div><span>窗口事件</span><strong>{display.visibleCount.toLocaleString()}</strong></div>
        <div><span>{timelineRendererMode === "memory-river" ? "Macro 河道" : "高重要/决策"}</span><strong>{timelineRendererMode === "memory-river" ? riverDisplay.levelCounts.Macro.toLocaleString() : display.importantCount.toLocaleString()}</strong></div>
        <div><span>{timelineRendererMode === "memory-river" ? "Meso 河道" : "核心画像"}</span><strong>{timelineRendererMode === "memory-river" ? riverDisplay.levelCounts.Meso.toLocaleString() : display.coreCount.toLocaleString()}</strong></div>
        <div><span>{timelineRendererMode === "memory-river" ? "Micro 河道" : "密度峰值"}</span><strong>{timelineRendererMode === "memory-river" ? riverDisplay.levelCounts.Micro.toLocaleString() : display.peakDensity.toLocaleString()}</strong></div>
      </div>
      <div className="timeline-density-track" aria-label="时间密度轨">
        {display.densityBands.map((band) => (
          <button
            aria-label={`${band.label} · ${band.count} 个事件`}
            className={band.active ? "timeline-density-band active" : "timeline-density-band"}
            key={band.key}
            onClick={() => clampTimelineCenter(band.center)}
            style={{ "--band-height": `${Math.max(8, band.intensity * 100)}%` } as CSSProperties}
            title={`${band.label} · ${band.count} 个事件`}
            type="button"
          />
        ))}
      </div>
      {timelineRendererMode === "memory-river" ? (
        <svg
          className="memory-river-canvas timeline-canvas"
          data-stage5-phase3-memory-river={TIMELINE_RENDERER_FEATURE_FLAG_VERSION}
          data-legacy-rollback="timelineRenderer=legacy"
          data-utc-time-scale="true"
          data-interaction-mode={interactionMode}
          data-selected-time-range={selectedTimelineRange ? "true" : "false"}
          data-feedback-reduced-motion={feedbackSettings.reducedMotion ? "true" : "false"}
          data-feedback-pseudo-haptic={feedbackSettings.pseudoHaptic ? "enabled" : "disabled"}
          data-feedback-audio={feedbackSettings.audio ? "enabled" : "disabled"}
          data-evidence-layers="black-hole-lifecycle proto-star-lifecycle stale-deprecated roi-gradient"
          data-roi-gradient="capability-growth"
          viewBox="0 0 1000 640"
          role="img"
          aria-label="记忆时间河 Macro Meso Micro UTC 河道"
          onPointerCancel={handleMemoryRiverPointerCancel}
          onPointerDown={handleMemoryRiverPointerDown}
          onPointerMove={handleMemoryRiverPointerMove}
          onPointerUp={handleMemoryRiverPointerUp}
          onWheel={handleTimelineWheel}
        >
          <defs>
            <filter id="memoryRiverGlow">
              <feGaussianBlur stdDeviation="4.4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            {riverDisplay.lanes.map((lane) => (
              <linearGradient id={lane.gradientId} key={lane.gradientId} x1="0%" x2="100%" y1="0%" y2="0%">
                <stop offset="0%" stopColor={lane.color} stopOpacity="0.16" />
                <stop offset="45%" stopColor={lane.color} stopOpacity="0.72" />
                <stop offset="100%" stopColor={lane.color} stopOpacity="0.28" />
              </linearGradient>
            ))}
          </defs>
          {display.densityBars.map((band) => (
            <rect className="timeline-density-backdrop" height={band.height} key={band.key} width={band.width} x={band.x} y={band.y} />
          ))}
          <g className="memory-river-roi-gradient" data-roi-gradient="capability-growth">
            <title>{`${riverDisplay.roiGradient.label} · ${riverDisplay.roiGradient.signal}`}</title>
            {riverDisplay.roiGradient.bands.map((band) => (
              <rect
                data-roi-gradient-band={band.id}
                fill={band.color}
                height={band.height}
                key={band.id}
                width={band.width}
                x={band.x}
                y={band.y}
              >
                <title>{band.label}</title>
              </rect>
            ))}
            <text x="82" y="92">{riverDisplay.roiGradient.label}</text>
            <text x="82" y="108">{riverDisplay.roiGradient.signal}</text>
          </g>
          {display.ticks.map((tick) => (
            <g key={tick.label}>
              <line x1={tick.x} x2={tick.x} y1="58" y2="552" stroke="rgba(244,241,232,0.08)" />
              <text x={tick.x} y="574" textAnchor="middle" className="axis-label">{tick.label}</text>
            </g>
          ))}
          {riverDisplay.levels.map((level) => (
            <g className="memory-river-level" key={level.level}>
              <text x="30" y={level.y - 18} className="memory-river-level-label">{level.level}</text>
              <text x="30" y={level.y} className="memory-river-level-note">{level.note}</text>
              <line x1="80" x2="960" y1={level.y + 12} y2={level.y + 12} />
            </g>
          ))}
          {riverDisplay.lanes.map((lane) => (
            <g className={`memory-river-lane level-${lane.level.toLowerCase()}`} key={lane.id}>
              <title>{`${lane.level} · ${lane.label} · ${lane.count} 个事件 · UTC scale`}</title>
              <path className="memory-river-lane-shadow" d={lane.path} strokeWidth={lane.strokeWidth + 10} />
              <path className="memory-river-lane-flow" d={lane.path} stroke={`url(#${lane.gradientId})`} strokeWidth={lane.strokeWidth} />
              <text x={lane.labelX} y={lane.labelY} className="memory-river-lane-label">{lane.label}</text>
            </g>
          ))}
          {riverDisplay.evidenceLayers.map((layer) => (
            <g className={`memory-river-evidence-layer ${layer.kind}`} data-evidence-layer={layer.kind} key={layer.id}>
              <title>{`${layer.label} · ${layer.count} 个 redacted derived signals · ${layer.detail}`}</title>
              {layer.segments.map((segment) => (
                <rect
                  data-evidence-segment={layer.kind}
                  height={segment.height}
                  key={segment.id}
                  rx="8"
                  width={segment.width}
                  x={segment.x}
                  y={segment.y}
                >
                  <title>{segment.label}</title>
                </rect>
              ))}
              {layer.path ? <path d={layer.path} /> : null}
              {layer.points.map((point) => (
                <circle cx={point.x} cy={point.y} key={point.id} r={point.radius}>
                  <title>{point.label}</title>
                </circle>
              ))}
              <text x={layer.labelX} y={layer.labelY}>{layer.label}</text>
            </g>
          ))}
          {selectedRangeOverlay ? (
            <g className="memory-river-selected-range" data-selected-time-range="active">
              <rect x={selectedRangeOverlay.x} y="64" width={selectedRangeOverlay.width} height="486" />
              <text x={selectedRangeOverlay.labelX} y="86" textAnchor="middle">{selectedRangeOverlay.label}</text>
            </g>
          ) : null}
          {brushDraftOverlay ? (
            <g className="memory-river-brush-draft" data-brush-range="draft">
              <rect x={brushDraftOverlay.x} y="64" width={brushDraftOverlay.width} height="486" />
            </g>
          ) : null}
          {display.eventTicks.map((tick) => (
            <g className="event-date-tick memory-river-date-tick" key={tick.date}>
              <title>{`${tick.date} UTC · ${tick.count} 个真实事件`}</title>
              <line x1={tick.x} x2={tick.x} y1="528" y2="552" />
              <text x={tick.x} y={tick.stagger ? 612 : 594} textAnchor="middle" className="event-axis-label">{tick.label}</text>
            </g>
          ))}
          {riverDisplay.markers.map((marker) => (
            <g
              className={`memory-river-marker ${marker.kind}${marker.event.id === lockedEventId ? " locked" : ""}`}
              key={marker.id}
              role="button"
              tabIndex={marker.event.node ? 0 : -1}
              onClick={(event) => {
                event.stopPropagation();
                lockMemoryRiverEvent(marker.event);
              }}
              onKeyDown={(keyboardEvent) => {
                if (marker.event.node && isActivationKey(keyboardEvent)) lockMemoryRiverEvent(marker.event);
              }}
              onPointerDown={(event) => event.stopPropagation()}
              onPointerEnter={() => setHoveredEventId(marker.event.id)}
              onPointerLeave={() => {
                if (marker.event.id !== lockedEventId) setHoveredEventId(null);
              }}
            >
              <title>{marker.title}</title>
              <circle cx={marker.x} cy={marker.y} r={marker.radius + 6} />
              <circle cx={marker.x} cy={marker.y} r={marker.radius} />
            </g>
          ))}
          <g className="timeline-cursor memory-river-cursor">
            <line x1={display.cursorX} x2={display.cursorX} y1="58" y2="552" />
            <text x={display.cursorX} y="50" textAnchor="middle">UTC {display.cursorLabel}</text>
          </g>
        </svg>
      ) : (
        <svg className="timeline-canvas" viewBox="0 0 1000 640" role="img" aria-label="动态记忆时间轴" onWheel={handleTimelineWheel}>
          <defs>
            <filter id="softGlow">
              <feGaussianBlur stdDeviation="3.2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          {display.densityBars.map((band) => (
            <rect className="timeline-density-backdrop" height={band.height} key={band.key} width={band.width} x={band.x} y={band.y} />
          ))}
          <line x1="80" x2="960" y1="540" y2="540" stroke="rgba(244,241,232,0.28)" strokeWidth="2" />
          {display.ticks.map((tick) => (
            <g key={tick.label}>
              <line x1={tick.x} x2={tick.x} y1="70" y2="548" stroke="rgba(244,241,232,0.08)" />
              <text x={tick.x} y="570" textAnchor="middle" className="axis-label">{tick.label}</text>
            </g>
          ))}
          {display.eventTicks.map((tick) => (
            <g className="event-date-tick" key={tick.date}>
              <title>{`${tick.date} · ${tick.count} 个真实事件`}</title>
              <line x1={tick.x} x2={tick.x} y1="528" y2="552" />
              <text x={tick.x} y={tick.stagger ? 612 : 594} textAnchor="middle" className="event-axis-label">{tick.label}</text>
            </g>
          ))}
          {display.lanes.map((lane) => (
            <g key={lane.key}>
              <line x1="80" x2="960" y1={lane.y} y2={lane.y} stroke={lane.color} opacity="0.2" />
              <text x="28" y={lane.y + 4} className="lane-label">{lane.label}</text>
            </g>
          ))}
          <g className="timeline-cursor">
            <line x1={display.cursorX} x2={display.cursorX} y1="58" y2="552" />
            <text x={display.cursorX} y="50" textAnchor="middle">{display.cursorLabel}</text>
          </g>
          {display.events.map((event) => {
            const node = event.node;
            const selected = event.source.node_id === selectedNode?.id;
            const hovered = event.id === hoveredEventId;
            const statusClass = event.future ? "future" : "past";
            return (
              <g
                className={`timeline-event ${statusClass}${selected ? " selected" : ""}${hovered ? " hovered" : ""}`}
                aria-label={`${event.source.date} · ${normalizeMemoryTier(event.source.memory_tier)} · ${event.source.label}`}
                key={event.id}
                role="button"
                tabIndex={node ? 0 : -1}
                onClick={() => {
                  if (node) onSelectNode(node);
                }}
                onMouseEnter={() => setHoveredEventId(event.id)}
                onMouseLeave={() => setHoveredEventId(null)}
                onKeyDown={(keyboardEvent) => {
                  if (node && isActivationKey(keyboardEvent)) onSelectNode(node);
                }}
              >
                <line x1={event.x} x2={event.x} y1={event.y} y2="540" stroke={event.color} opacity="0.28" />
                <circle cx={event.x} cy={event.y} r={event.radius} fill={event.color} filter="url(#softGlow)" />
                {(event.major || selected || hovered) ? (
                  <text x={Math.min(930, event.x + 10)} y={event.y - 10} className="timeline-point-label">{event.shortLabel}</text>
                ) : null}
              </g>
            );
          })}
        </svg>
      )}
      {timelineRendererMode === "memory-river" && activeRiverEvent ? (
        <div className={`memory-river-event-card${lockedEvent ? " locked" : ""}`} data-event-card={lockedEvent ? "locked" : "hover"}>
          <div>
            <span>{activeRiverEvent.utcDate} UTC · {normalizeMemoryTier(activeRiverEvent.source.memory_tier)} · {humanCategoryLabel(activeRiverEvent.source.category)}</span>
            <strong>{humanizeStatement(activeRiverEvent.node?.statement) || activeRiverEvent.source.label}</strong>
            <small>redacted derived event · {activeRiverEvent.source.importance || "普通"} · {activeRiverEvent.node ? humanThemeLabel(activeRiverEvent.node) : "未连接节点"}</small>
          </div>
          <div className="event-card-actions">
            <button disabled={!activeRiverEvent.node} onClick={() => activeRiverEvent.node && onSelectNode(activeRiverEvent.node)} type="button">
              同步 Inspector
            </button>
            <button onClick={() => lockedEvent ? setLockedEventId(null) : lockMemoryRiverEvent(activeRiverEvent)} type="button">
              {lockedEvent ? "解除锁定" : "锁定事件"}
            </button>
          </div>
        </div>
      ) : null}
      <div className="timeline-event-detail-strip" aria-label="时间轴事件详情">
        {hoveredEvent ? (
          <>
            <div>
              <span>{hoveredEvent.source.date} · {normalizeMemoryTier(hoveredEvent.source.memory_tier)} · {humanCategoryLabel(hoveredEvent.source.category)}</span>
              <strong>{humanizeStatement(hoveredEvent.node?.statement) || hoveredEvent.source.label}</strong>
            </div>
            <button disabled={!hoveredEvent.node} onClick={() => hoveredEvent.node && onSelectNode(hoveredEvent.node)} type="button">
              同步详情
            </button>
          </>
        ) : (
          <p>移动到事件点查看内容；点击事件同步右侧详情。滚轮缩放，窗口滑块定位年份内局部阶段。</p>
        )}
      </div>
    </div>
  );
}

function ContributionGrid({
  atlas,
  nodes,
  filters,
  deltaStats,
  onSelectPeriod,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  filters: AtlasFilters;
  deltaStats: DeltaStats;
  onSelectPeriod: (detail: ContributionPeriodDetail) => void;
}) {
  const [scale, setScale] = useState<ContributionScale>("day");
  const availableYears = useMemo(() => contributionYears(atlas, nodes), [atlas, nodes]);
  const [selectedYear, setSelectedYear] = useState(() => availableYears[availableYears.length - 1] ?? new Date().getUTCFullYear());
  useEffect(() => {
    if (!availableYears.length) return;
    if (!availableYears.includes(selectedYear)) {
      setSelectedYear(availableYears[availableYears.length - 1]);
    }
  }, [availableYears, selectedYear]);
  const periodData = useMemo(() => buildContributionPeriods(atlas, nodes, filters, selectedYear), [atlas, nodes, filters, selectedYear]);
  const [selectedPeriod, setSelectedPeriod] = useState("");
  const selected = periodData.periods.get(selectedPeriod) ?? periodData.defaultPeriod;
  const selectedDetail = useMemo(
    () => buildContributionPeriodDetail(scale, selected, nodes),
    [nodes, scale, selected],
  );
  const isDayOrWeek = scale === "day" || scale === "week";
  const dayWeekModeClass = scale === "week" ? "week-mode" : "day-mode";

  useEffect(() => {
    setSelectedPeriod(defaultPeriodKeyForScale(scale, periodData));
  }, [periodData, scale]);

  useEffect(() => {
    onSelectPeriod(selectedDetail);
  }, [onSelectPeriod, selectedDetail]);

  return (
    <div className="contribution-view visual-workspace">
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">使用强度 / 记忆增量 / 时间尺度对比</p>
          <h2>按日、周、月、年观察交互强度和记忆增量</h2>
        </div>
        <span>{periodData.year} 年 / 数据 {atlas.contribution.range_start || "暂无"}-{atlas.contribution.range_end || "暂无"}</span>
      </div>
      <div className="contribution-toolbar">
        <DeltaStrip stats={deltaStats} compact />
        <div className="scale-tabs" role="group" aria-label="贡献网格尺度">
          {(["day", "week", "month", "year"] as ContributionScale[]).map((item) => (
            <button className={scale === item ? "segmented active" : "segmented"} key={item} onClick={() => setScale(item)} type="button">
              {scaleLabel(item)}
            </button>
          ))}
        </div>
        <label className="year-picker">
          <span>年份</span>
          <select value={selectedYear} onChange={(event) => setSelectedYear(Number(event.target.value))}>
            {availableYears.map((yearOption) => (
              <option key={yearOption} value={yearOption}>
                {yearOption}
              </option>
            ))}
          </select>
        </label>
      </div>
      <HeatLegend />
      {isDayOrWeek ? (
        <div className={`year-heatmap-wrap ${scale === "week" ? "week-scale" : "day-scale"}`}>
          <div className="year-heatmap-body">
            <div className="weekday-label-column" aria-hidden="true">
              {weekdayLabels.map((label) => (
                <span key={label}>{label}</span>
              ))}
            </div>
            <div
              className={`year-heatmap ${dayWeekModeClass}`}
              style={{
                "--week-columns": periodData.weekColumns,
              } as CSSProperties}
            >
              {scale === "week"
                ? periodData.weekCells.map((cell) => {
                    const active = selectedPeriod === cell.weekKey;
                    return (
                      <button
                        className={`week-cell level-${cell.activityLevel}${active ? " selected" : ""}`}
                        key={cell.weekKey}
                        onClick={() => setSelectedPeriod(cell.weekKey)}
                        style={
                          {
                            ...heatCellStyle(cell, periodData.weekMaxActivityScore),
                            gridColumn: cell.weekColumn + 1,
                            gridRow: "1 / span 7",
                            "--trend-gradient": trendGradient(cell.daySlots, "180deg", periodData.dayMaxActivityScore),
                          } as CSSProperties
                        }
                        title={contributionTitle(cell)}
                        type="button"
                      >
                        <div className="cell-trend week-trend smooth-trend" aria-hidden="true">
                          {cell.daySlots.map((slot, index) => (
                            <i
                              className={`trend-segment level-${slot?.activityLevel ?? 0}${slot ? "" : " empty"}`}
                              key={slot?.date ?? index}
                              style={trendSegmentStyle(slot, periodData.dayMaxActivityScore)}
                            />
                          ))}
                        </div>
                        <span>{cell.label}</span>
                      </button>
                    );
                  })
                : periodData.dailyCells.map((cell) => {
                    const active = selectedPeriod === cell.date;
                    return (
                      <button
                        className={`heat-cell level-${cell.activityLevel}${active ? " selected" : ""}`}
                        key={cell.date}
                        onClick={() => setSelectedPeriod(cell.date)}
                        style={{ ...heatCellStyle(cell, periodData.dayMaxActivityScore), gridColumn: cell.weekColumn + 1, gridRow: cell.weekday + 1 }}
                        title={contributionTitle(cell)}
                        type="button"
                      >
                        <span>{cell.date}</span>
                      </button>
                    );
                  })}
            </div>
          </div>
          <div className="week-label-shell">
            <span aria-hidden="true" />
            <div className="week-label-row" style={{ "--week-columns": periodData.weekColumns } as CSSProperties}>
              {Array.from({ length: periodData.weekColumns }, (_, index) => (
                <span key={index}>{index % 2 === 0 ? `W${index + 1}` : ""}</span>
              ))}
            </div>
          </div>
        </div>
      ) : scale === "year" ? (
        <div className="year-trend-grid year-comparison-trend">
          {periodData.yearCells.map((cell) => {
            const periodKey = String(cell.year);
            const active = selectedPeriod === periodKey;
            return (
              <button
                aria-label={`${cell.year} 年，活动得分 ${cell.activityScore}，环比 ${formatSigned(cell.delta ?? 0)}`}
                className={`year-cell year-summary-card level-${cell.activityLevel}${active ? " selected" : ""}`}
                key={periodKey}
                onClick={() => setSelectedPeriod(periodKey)}
                style={yearCellStyle(cell, periodData.yearMaxActivityScore)}
                title={contributionTitle(cell)}
                type="button"
              >
                <div className="year-card-header">
                  <strong>{cell.year}</strong>
                  <span>{cell.activityScore.toLocaleString()} 分</span>
                </div>
                <div className="year-month-track" aria-hidden="true">
                  {cell.monthSlots.map((slot) => (
                    <i className={`year-month-bar level-${slot.activityLevel}`} key={slot.date} style={monthBarStyle(slot, cell.monthSlots)} />
                  ))}
                </div>
                <div className="year-month-axis" aria-hidden="true">
                  <span>Q1</span>
                  <span>Q2</span>
                  <span>Q3</span>
                  <span>Q4</span>
                </div>
                <div className="year-card-footer">
                  <span>消息 {cell.messageCount.toLocaleString()}</span>
                  <span>记忆 {cell.filteredMemoryCount.toLocaleString()}</span>
                  <span className={(cell.delta ?? 0) >= 0 ? "positive" : "negative"}>{formatSigned(cell.delta ?? 0)}</span>
                </div>
                <span>{cell.label}</span>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="month-heatmap">
          {periodData.monthCells.map((cell) => {
            const periodKey = cell.date;
            const active = selectedPeriod === periodKey;
            const monthTrendMax = maxActivityScore(cell.daySlots);
            return (
              <button
                className={`month-cell level-${cell.activityLevel}${active ? " selected" : ""}`}
                key={cell.date}
                onClick={() => setSelectedPeriod(periodKey)}
                style={
                  {
                    ...heatCellStyle(cell, periodData.monthMaxActivityScore),
                    "--trend-gradient": trendGradient(cell.daySlots, "180deg", monthTrendMax),
                    "--month-days": cell.daySlots.length,
                  } as CSSProperties
                }
                title={contributionTitle(cell)}
                type="button"
              >
                <div className="cell-trend month-trend smooth-trend" aria-hidden="true">
                  {cell.daySlots.map((slot) => (
                    <i className={`trend-segment level-${slot.activityLevel}`} key={slot.date} style={trendSegmentStyle(slot, monthTrendMax)} />
                  ))}
                </div>
                <strong>{cell.monthLabel}</strong>
                <span>{cell.year}</span>
              </button>
            );
          })}
        </div>
      )}
      <div className="contribution-analysis">
        <InsightCard title="当前对象" value={selected.activityScore} note={`${selected.label}；活动得分`} />
        <InsightCard title="筛选记忆增量" value={selected.filteredMemoryCount} note={`当前筛选命中；决策 ${selected.filteredDecisionCount} 条`} />
        <InsightCard title="全局交互量" value={selected.messageCount} note={`对话 ${selected.conversationCount} 个；消息 ${selected.messageCount} 条`} />
        <InsightCard title="环比变化" value={selected.delta} note={`${selected.previousLabel} 对比 ${formatSigned(selected.delta)} 分`} />
      </div>
      <p className="note">
        说明：当前分析对象的真实数据范围显示在标题右侧；全年空格代表该对象当天为 0，不代表存在使用记录。层级/分类/主题筛选后的贡献增量来自当前筛选记忆节点日期聚合，避免伪造主题级消息数。
      </p>
    </div>
  );
}

function HeatLegend() {
  return (
    <div className="heat-legend" aria-label="贡献网格热度标尺">
      <span>热度趋势</span>
      <div className="heat-legend-gradient" role="img" aria-label="热度从 0、低频、中频到高频逐步增强">
        <b>0</b>
        <i aria-hidden="true" />
        <b>高</b>
      </div>
    </div>
  );
}

function WordCloudView({
  nodes,
  deltaStats,
  onSelectNode,
}: {
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const semantic = useMemo(() => buildSemanticInsights(nodes), [nodes]);
  const maxTopicCount = Math.max(1, ...semantic.topics.map((topic) => topic.count));
  const maxWordScore = Math.max(1, ...semantic.wordCloud.map((item) => item.score));

  function jumpToBestNode(candidates: AtlasNode[]) {
    const target = selectRepresentativeNode(candidates);
    if (target) onSelectNode(target);
  }

  return (
    <div className="visual-workspace semantic-workspace">
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">词云 / 语义热力 / 主题气泡</p>
          <h2>把当前筛选切片转成可点击的主题密度、关键词和机会信号</h2>
        </div>
        <span>{nodes.length.toLocaleString()} 条记忆 / {semantic.topics.length.toLocaleString()} 个主题</span>
      </div>
      <DeltaStrip stats={deltaStats} compact />
      <div className="semantic-dashboard" aria-label="词云洞察">
        <section className="semantic-panel semantic-heatmap" aria-label="主题层级热力图">
          <div className="panel-title-row">
            <h3>主题 x 层级 Heatmap</h3>
            <span>{semantic.tiers.join(" / ")}</span>
          </div>
          <div
            className="semantic-matrix"
            style={{ gridTemplateColumns: `minmax(76px, 1.1fr) repeat(${semantic.tiers.length}, minmax(42px, 0.7fr))` }}
          >
            <span className="semantic-axis-corner" aria-hidden="true" />
            {semantic.tiers.map((tier) => (
              <strong className="semantic-axis-label" key={tier}>{tier}</strong>
            ))}
            {semantic.matrixRows.map((topic) => (
              <div className="semantic-row" key={topic}>
                <b title={topic}>{topic}</b>
                {semantic.tiers.map((tier) => {
                  const cell = semantic.matrix.get(`${topic}::${tier}`) ?? { topic, tier, count: 0, nodes: [] };
                  return (
                    <button
                      aria-label={`${topic} / ${tier} / ${cell.count} 条`}
                      className="semantic-heat-cell"
                      disabled={!cell.nodes.length}
                      key={`${topic}-${tier}`}
                      onClick={() => jumpToBestNode(cell.nodes)}
                      style={semanticHeatStyle(cell.count, maxTopicCount)}
                      title={`${topic} · ${tier} · ${cell.count} 条`}
                      type="button"
                    >
                      <span>{cell.count}</span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </section>

        <section className="semantic-panel semantic-bubbles" aria-label="主题气泡图">
          <div className="panel-title-row">
            <h3>Bubble Chart</h3>
            <span>横轴 ROI / 纵轴近期增量</span>
          </div>
          <svg className="semantic-bubble-canvas" viewBox="0 0 520 330" role="img" aria-label="主题 ROI 与近期增量气泡图">
            <line x1="48" x2="494" y1="286" y2="286" />
            <line x1="48" x2="48" y1="28" y2="286" />
            <text x="494" y="312" textAnchor="end">ROI</text>
            <text x="12" y="38" transform="rotate(-90 12 38)">近期</text>
            {semantic.topics.slice(0, 18).map((topic, index) => {
              const radius = 10 + Math.sqrt(topic.count / maxTopicCount) * 28;
              const x = 62 + Math.min(1, Math.max(0, topic.roiScore)) * 406;
              const y = 270 - Math.min(1, topic.recentCount / Math.max(1, deltaStats.recentCount || topic.count)) * 218 - stableUnit(topic.label, "bubble-y") * 18;
              const color = semanticColor(index);
              return (
                <g
                  className="semantic-bubble"
                  key={topic.label}
                  role="button"
                  tabIndex={0}
                  onClick={() => jumpToBestNode(topic.nodes)}
                  onKeyDown={(event) => {
                    if (isActivationKey(event)) jumpToBestNode(topic.nodes);
                  }}
                >
                  <title>{`${topic.label} · ${topic.count} 条 · ROI ${topic.roiScore.toFixed(2)} · 近期 ${topic.recentCount}`}</title>
                  <circle cx={x} cy={y} r={radius} fill={color} />
                  <text x={x} y={y + 3} textAnchor="middle">{truncate(topic.label, radius > 28 ? 8 : 5)}</text>
                </g>
              );
            })}
          </svg>
        </section>

        <section className="semantic-panel semantic-cloud" aria-label="词云">
          <div className="panel-title-row">
            <h3>Word Cloud</h3>
            <span>点击词条跳转代表记忆</span>
          </div>
          <div className="word-cloud-field">
            {semantic.wordCloud.map((item) => (
              <button
                className="word-cloud-token"
                key={item.label}
                onClick={() => jumpToBestNode(item.nodes)}
                style={wordCloudStyle(item, maxWordScore)}
                title={`${item.label} · ${item.count} 条`}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function InteractionLens({
  activeView,
  filters,
  sharedState,
  selectedContributionPeriod,
  selectedNode,
  slice,
  sourceOptions,
  timelineTimeRange,
  onClearFilter,
  onClearTimelineRange,
  onFocusTheme,
  onResetFilters,
  onSelectAdjacent,
}: {
  activeView: ViewKey;
  filters: AtlasFilters;
  sharedState: SharedAtlasState;
  selectedContributionPeriod: ContributionPeriodDetail | null;
  selectedNode: AtlasNode | null;
  slice: FilteredAtlasSlice;
  sourceOptions: SourceOption[];
  timelineTimeRange: TimelineTimeRangeSelection | null;
  onClearFilter: (key: FilterKey) => void;
  onClearTimelineRange: () => void;
  onFocusTheme: () => void;
  onResetFilters: () => void;
  onSelectAdjacent: (direction: -1 | 1) => void;
}) {
  const candidates = useMemo(() => selectableLensNodes(slice, selectedNode), [selectedNode, slice]);
  const selectedIndex = selectedNode ? candidates.findIndex((node) => node.id === selectedNode.id) : -1;
  const canStep = selectedIndex >= 0 && candidates.length > 1;
  const chips = useMemo(() => activeFilterChips(filters, sourceOptions), [filters, sourceOptions]);
  const focusTheme = selectedNode?.visual?.cluster;
  const viewLabel = views.find((view) => view.key === activeView)?.label ?? "当前视图";
  const focusTitle = selectedContributionPeriod
    ? `${scaleLabel(selectedContributionPeriod.scale)} · ${selectedContributionPeriod.bucket.label}`
    : selectedNode
      ? humanNodeDisplayTitle(selectedNode)
      : "暂无焦点";
  const focusMeta = selectedContributionPeriod
    ? `活动 ${selectedContributionPeriod.bucket.activityScore.toLocaleString()} / 筛选记忆 ${selectedContributionPeriod.bucket.filteredMemoryCount.toLocaleString()} / 环比 ${formatSigned(selectedContributionPeriod.bucket.delta ?? 0)}`
    : selectedNode
      ? `${normalizeMemoryTier(selectedNode.memory_tier)} / ${humanCategoryLabel(selectedNode.category)} / ${selectedNode.date || "未知日期"}`
      : "选择节点、事件或时间格后同步更新";

  return (
    <section
      className="interaction-lens"
      aria-label="当前交互焦点"
      data-shared-state={sharedState.schema_version}
      data-stage9-phase1-shared-state={CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION}
      data-stage9-synchronized-filters="shared_state_filters synchronized_filters"
      data-sync-revision={sharedState.sync.revision}
      data-sync-source={sharedState.sync.updatedBy}
      data-sync-action={sharedState.sync.lastAction}
      data-shared-focus-node={sharedState.focus.inspector.nodeId ?? ""}
      data-shared-cluster={sharedState.focus.inspector.clusterId ?? ""}
      data-shared-time-range={sharedState.focus.inspector.timeRangeId ?? ""}
    >
      <div className="lens-focus">
        <span className="lens-badge">{viewLabel}</span>
        <div>
          <strong>{focusTitle}</strong>
          <span>{focusMeta}</span>
        </div>
      </div>
      <div className="lens-stepper" aria-label="焦点切换">
        <button aria-label="上一个焦点" disabled={!canStep} onClick={() => onSelectAdjacent(-1)} title="上一个焦点" type="button">
          <ChevronLeft size={16} />
        </button>
        <span>{selectedIndex >= 0 ? `${selectedIndex + 1}/${candidates.length}` : `0/${candidates.length}`}</span>
        <button aria-label="下一个焦点" disabled={!canStep} onClick={() => onSelectAdjacent(1)} title="下一个焦点" type="button">
          <ChevronRight size={16} />
        </button>
      </div>
      <div className="lens-actions">
        <button disabled={!focusTheme || filters.theme === focusTheme} onClick={onFocusTheme} type="button">
          <Crosshair size={15} />
          <span>聚焦主题</span>
        </button>
        <button disabled={!chips.length} onClick={onResetFilters} type="button">
          <FilterX size={15} />
          <span>重置筛选</span>
        </button>
      </div>
      <MachineFieldDetails title="焦点技术详情" className="lens-technical-details">
        <div className="lens-state-strip" aria-label="宇宙状态（Universe State）快照">
          <span>宇宙状态（Universe State）</span>
          <strong>信号 {sharedState.selection.signal}</strong>
          <em>来源 {sharedState.sync.updatedBy} · r{sharedState.sync.revision}</em>
        </div>
      </MachineFieldDetails>
      <div className="filter-chip-row" aria-label="活跃筛选">
        {chips.length || timelineTimeRange ? (
          <>
          {timelineTimeRange ? (
            <button className="timeline-range-chip" onClick={onClearTimelineRange} title="清除时间河选择" type="button">
              <span>时间河</span>
              <strong>{timelineTimeRange.label}</strong>
              <em aria-hidden="true">×</em>
            </button>
          ) : null}
          {chips.map((chip) => (
            <button key={chip.key} onClick={() => onClearFilter(chip.key)} title={`清除${chip.label}`} type="button">
              <span>{chip.label}</span>
              <strong>{chip.value}</strong>
              <em aria-hidden="true">×</em>
            </button>
          ))}
          </>
        ) : (
          <span className="filter-empty">全部数据</span>
        )}
      </div>
    </section>
  );
}

function selectableLensNodes(slice: FilteredAtlasSlice, selectedNode: AtlasNode | null): AtlasNode[] {
  if (selectedNode && slice.memoryNodes.some((node) => node.id === selectedNode.id)) return slice.memoryNodes;
  if (slice.memoryNodes.length && !selectedNode) return slice.memoryNodes;
  return slice.graphNodes;
}

function activeFilterChips(filters: AtlasFilters, sourceOptions: SourceOption[]): Array<{ key: FilterKey; label: string; value: string }> {
  const chips: Array<{ key: FilterKey; label: string; value: string }> = [];
  if (filters.source !== "all") chips.push({ key: "source", label: "对象", value: sourceOptions.find((source) => source.id === filters.source)?.label ?? filters.source });
  if (filters.query.trim()) chips.push({ key: "query", label: "搜索", value: filters.query.trim() });
  if (filters.tier !== "all") chips.push({ key: "tier", label: "层级", value: filters.tier });
  if (filters.category !== "all") chips.push({ key: "category", label: "分类", value: humanCategoryLabel(filters.category) });
  if (filters.theme !== "all") chips.push({ key: "theme", label: "主题", value: themeLabelFromCluster(filters.theme) });
  return chips;
}

function trendGradient(slots: TrendSlot[], direction: "90deg" | "180deg", maxScore = maxActivityScore(slots)) {
  const colors = fluidTrendIntensities(slots.map((slot) => trendIntensity(slot, maxScore)))
    .map(trendColorFromIntensity);
  if (!colors.length) return `linear-gradient(${direction}, ${trendColor(0)}, ${trendColor(0)})`;
  if (colors.length === 1) return `linear-gradient(${direction}, ${colors[0]}, ${colors[0]})`;
  const lastIndex = colors.length - 1;
  const stops = colors.map((color, index) => {
    const position = Number(((index / lastIndex) * 100).toFixed(2));
    return `${color} ${position}%`;
  });
  return `linear-gradient(${direction}, ${stops.join(", ")})`;
}

function trendIntensity(slot: TrendSlot, maxScore: number) {
  if (!slot) return 0;
  const score = Number(slot.activityScore ?? 0);
  if (score <= 0 && slot.activityLevel <= 0) return 0;
  return heatIntensityForScore(score, maxScore, slot.activityLevel);
}

function smoothTrendIntensities(values: number[]) {
  if (!values.some((value) => value > 0)) return values;
  return values.map((value, index) => {
    const previous = values[index - 1] ?? value;
    const next = values[index + 1] ?? value;
    const interpolated = previous * 0.2 + value * 0.6 + next * 0.2;
    return Math.min(1, Math.max(interpolated, value * 0.72));
  });
}

function fluidTrendIntensities(values: number[]) {
  if (values.length <= 1 || !values.some((value) => value > 0)) return values;
  const anchors = smoothTrendIntensities(values);
  const sampleCount = Math.max(anchors.length * 7, 18);
  const lastIndex = anchors.length - 1;
  return Array.from({ length: sampleCount }, (_, sampleIndex) => {
    const scaled = (sampleIndex / (sampleCount - 1)) * lastIndex;
    const index = Math.min(lastIndex - 1, Math.max(0, Math.floor(scaled)));
    const t = smoothStep(scaled - index);
    const p0 = anchors[Math.max(0, index - 1)];
    const p1 = anchors[index];
    const p2 = anchors[Math.min(lastIndex, index + 1)];
    const p3 = anchors[Math.min(lastIndex, index + 2)];
    return clamp(catmullRom(p0, p1, p2, p3, t), 0, 1);
  });
}

function smoothStep(value: number) {
  const t = clamp(value, 0, 1);
  return t * t * (3 - 2 * t);
}

function catmullRom(p0: number, p1: number, p2: number, p3: number, t: number) {
  const t2 = t * t;
  const t3 = t2 * t;
  return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3);
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function trendColorFromIntensity(value: number) {
  return value <= 0 ? emptyHeatColor : interpolateHeatColor(value);
}

function trendColor(slotOrLevel: TrendSlot | number, maxScore = 0) {
  if (slotOrLevel === null) return "rgba(9, 10, 13, 0.44)";
  const score = typeof slotOrLevel === "number" ? 0 : Number(slotOrLevel.activityScore ?? 0);
  const level = typeof slotOrLevel === "number" ? slotOrLevel : slotOrLevel.activityLevel;
  if (score <= 0 && level <= 0) return emptyHeatColor;
  return heatColorForScore(score, maxScore, level);
}

function trendSegmentStyle(slot: TrendSlot, maxScore: number): CSSProperties {
  const base = !slot
    ? heatCellStyle({ activityScore: 0, activityLevel: 0 }, maxScore)
    : heatCellStyle({ activityScore: Number(slot.activityScore ?? 0), activityLevel: slot.activityLevel }, maxScore);
  return {
    ...base,
    "--segment-color": trendColor(slot, maxScore),
  } as CSSProperties;
}

function heatCellStyle(bucket: Pick<PeriodCounts, "activityScore" | "activityLevel">, maxScore: number): CSSProperties {
  const color = heatColorForScore(bucket.activityScore, maxScore, bucket.activityLevel);
  const strong = bucket.activityScore > 0 || bucket.activityLevel > 0;
  return {
    "--heat-bg": strong
      ? `linear-gradient(145deg, ${withAlpha(color, 0.82)} 0%, ${color} 100%)`
      : "rgba(15, 17, 22, 0.96)",
    "--heat-border": strong ? withAlpha(color, 0.72) : "rgba(244, 241, 232, 0.08)",
    "--heat-shadow": strong ? `0 0 16px ${withAlpha(color, 0.24)}, inset 0 0 0 1px rgba(255, 255, 255, 0.05)` : "inset 0 0 0 1px rgba(244, 241, 232, 0.04)",
  } as CSSProperties;
}

function yearCellStyle(bucket: Pick<PeriodCounts, "activityScore" | "activityLevel">, maxScore: number): CSSProperties {
  return {
    ...heatCellStyle(bucket, maxScore),
    "--year-accent": heatColorForScore(bucket.activityScore, maxScore, bucket.activityLevel),
  } as CSSProperties;
}

function monthBarStyle(slot: Pick<PeriodCounts, "activityScore" | "activityLevel">, slots: Array<Pick<PeriodCounts, "activityScore">>): CSSProperties {
  const maxScore = maxActivityScore(slots);
  const score = Math.max(0, slot.activityScore);
  const ratio = maxScore > 0 ? score / maxScore : 0;
  const height = score > 0 ? Math.round(24 + Math.sqrt(ratio) * 76) : 9;
  return {
    "--month-color": trendColor(slot, maxScore),
    "--month-height": `${height}%`,
  } as CSSProperties;
}

function heatColorForScore(score: number, maxScore: number, fallbackLevel: number) {
  if (score <= 0 && fallbackLevel <= 0) return emptyHeatColor;
  return interpolateHeatColor(heatIntensityForScore(score, maxScore, fallbackLevel));
}

function heatIntensityForScore(score: number, maxScore: number, fallbackLevel: number) {
  const level = Math.max(0, Math.min(5, Math.round(fallbackLevel)));
  const levelAnchor = heatLevelAnchors[level] ?? heatLevelAnchors[1];
  const rawRatio = maxScore > 0 ? Math.min(1, Math.max(0.001, score / maxScore)) : 0;
  const logRatio = maxScore > 0 ? Math.log1p(Math.max(0, score)) / Math.log1p(maxScore) : levelAnchor;
  const ratio = Math.max(levelAnchor, logRatio * 0.82 + rawRatio * 0.18);
  return Math.min(1, Math.max(0.08, 0.04 + ratio * 0.96));
}

function interpolateHeatColor(value: number) {
  const bounded = Math.min(1, Math.max(0, value));
  let left = heatStops[0];
  let right = heatStops[heatStops.length - 1];
  for (let index = 1; index < heatStops.length; index += 1) {
    if (bounded <= heatStops[index].stop) {
      right = heatStops[index];
      left = heatStops[index - 1];
      break;
    }
  }
  const span = Math.max(0.001, right.stop - left.stop);
  const local = (bounded - left.stop) / span;
  const rgb = left.rgb.map((part, index) => Math.round(part + (right.rgb[index] - part) * local));
  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

function withAlpha(color: string, alpha: number) {
  const match = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
  if (!match) return color;
  return `rgba(${match[1]}, ${match[2]}, ${match[3]}, ${alpha})`;
}

function SearchReview({
  atlas,
  filters,
  nodes,
  deltaStats,
  onSelectNode,
  onSwitchView,
}: {
  atlas: MemoryAtlas;
  filters: AtlasFilters;
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [searchFilters, setSearchFilters] = useState<Search2Filters>(() => ({
    query: filters.query,
    tier: "all",
    topic: "all",
    recency: "all",
    importance: "all",
    evidenceOnly: true,
  }));
  useEffect(() => {
    setSearchFilters((current) => (
      current.query === filters.query ? current : { ...current, query: filters.query }
    ));
  }, [filters.query]);
  const searchVisualRows = useMemo(() => buildSearchVisualRows(nodes), [nodes]);
  const topicOptions = useMemo(() => uniqueSorted(nodes.map((node) => humanThemeLabel(node))).slice(0, 24), [nodes]);
  const searchResults = useMemo(() => buildSearch2Results(atlas, nodes, searchFilters), [atlas, nodes, searchFilters]);
  const sessionSummary = useMemo(() => buildSearch2SessionSummary(searchResults, searchFilters.query), [searchFilters.query, searchResults]);
  const visibleResults = searchResults.slice(0, 50);

  useEffect(() => {
    window.__memoryAtlasStage7Phase1 = () => ({
      runtimeVersion: SEARCH_2_0_RUNTIME_VERSION,
      sessionSummaryVersion: SEARCH_2_0_SESSION_SUMMARY_VERSION,
      query: searchFilters.query,
      resultCount: searchResults.length,
      hasMatchedReason: searchResults.some((result) => result.matched_reason.length > 0),
      hasEvidenceRefs: searchResults.some((result) => result.evidence_refs.length > 0),
      jumpActions: ["starfield", "river", "inspector"],
      zeroResultRecoveryVisible: searchResults.length === 0,
      proposalCandidateCount: searchResults.filter((result) => result.proposal_candidate).length,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
    });
    return () => {
      delete window.__memoryAtlasStage7Phase1;
    };
  }, [searchFilters.query, searchResults]);

  function updateSearchFilter(patch: Partial<Search2Filters>) {
    setSearchFilters((current) => ({ ...current, ...patch }));
  }

  function resetSearchFilters() {
    setSearchFilters({
      query: "",
      tier: "all",
      topic: "all",
      recency: "all",
      importance: "all",
      evidenceOnly: true,
    });
  }

  function jumpToSearchTarget(result: Search2Result, target: "starfield" | "river" | "inspector") {
    onSelectNode(result.node);
    if (target === "starfield") onSwitchView("galaxy");
    if (target === "river") onSwitchView("timeline");
  }

  return (
    <div className="search-review search-2-runtime" data-search-2-0-runtime={SEARCH_2_0_RUNTIME_VERSION}>
      <DeltaStrip stats={deltaStats} compact />
      <HumanOverviewPanel nodes={nodes} deltaStats={deltaStats} />
      <section className="search-2-controls" aria-label="Search 2.0 query_input">
        <label className="search-2-query">
          <span>query_input</span>
          <div className="search-2-input-frame">
            <Search size={16} />
            <input
              data-search-query-input="true"
              value={searchFilters.query}
              onChange={(event) => updateSearchFilter({ query: event.target.value })}
              placeholder="搜索主题、层级、行动、证据"
            />
          </div>
        </label>
        <div className="search-2-filter-grid">
          <label>
            <span>tier</span>
            <select value={searchFilters.tier} onChange={(event) => updateSearchFilter({ tier: event.target.value as Search2TierFilter })}>
              <option value="all">all</option>
              <option value="core_profile">core_profile</option>
              <option value="project">project</option>
              <option value="decision">decision</option>
              <option value="workflow">workflow</option>
              <option value="knowledge">knowledge</option>
              <option value="opportunity">opportunity</option>
              <option value="stale">stale</option>
            </select>
          </label>
          <label>
            <span>topic</span>
            <select value={searchFilters.topic} onChange={(event) => updateSearchFilter({ topic: event.target.value })}>
              <option value="all">all</option>
              {topicOptions.map((topic) => (
                <option key={topic} value={topic}>{topic}</option>
              ))}
            </select>
        </label>
        <label>
            <span>时效</span>
            <select value={searchFilters.recency} onChange={(event) => updateSearchFilter({ recency: event.target.value as Search2RecencyFilter })}>
              <option value="all">全部</option>
              <option value="recent">近期</option>
              <option value="active">活跃</option>
              <option value="stale">过期</option>
              <option value="archival">归档</option>
            </select>
          </label>
          <label>
            <span>重要性</span>
            <select value={searchFilters.importance} onChange={(event) => updateSearchFilter({ importance: event.target.value as Search2ImportanceFilter })}>
              <option value="all">全部</option>
              <option value="low">低</option>
              <option value="medium">中</option>
              <option value="high">高</option>
              <option value="critical">关键</option>
            </select>
          </label>
          <label className="search-2-checkbox">
            <input
              type="checkbox"
              checked={searchFilters.evidenceOnly}
              onChange={(event) => updateSearchFilter({ evidenceOnly: event.target.checked })}
            />
            <span>仅看有证据结果</span>
          </label>
          <button className="search-2-reset" onClick={resetSearchFilters} type="button">
            <FilterX size={14} />
            <span>重置</span>
          </button>
        </div>
        <div
          className="search-2-filter-state"
          data-search-filter-state="search_2_0"
          data-result-count={searchResults.length}
          data-evidence-only={String(searchFilters.evidenceOnly)}
        >
          <span>筛选状态</span>
          <b>{searchResults.length.toLocaleString()} 条结果</b>
          <small>{search2FilterStateLabel(searchFilters)}</small>
        </div>
      </section>
      <section className="search-visual-summary" aria-label="搜索结果视觉摘要">
        <div className="panel-title-row">
          <h3>当前结果分布</h3>
          <span>{searchResults.length.toLocaleString()} 条</span>
        </div>
        <div className="search-topic-bars">
          <MiniBarList title="高频主题" rows={searchVisualRows.topics} />
          <MiniBarList title="记忆层级" rows={searchVisualRows.tiers} />
          <MiniBarList title="近期/决策" rows={searchVisualRows.signals} />
        </div>
      </section>
      <section
        className="search-2-session-summary"
        data-search-session-summary={SEARCH_2_0_SESSION_SUMMARY_VERSION}
        data-proposal-candidate={String(sessionSummary.proposal_candidate)}
      >
        <div className="panel-title-row">
          <h3>搜索会话摘要</h3>
          <span>{sessionSummary.result_count.toLocaleString()} 条结果</span>
        </div>
        <p>默认只看结果数量、分布和下一步；会话字段已收进高级详情。</p>
        <MachineFieldDetails title="高级详情：搜索会话字段" className="search-machine-details">
          <p className="machine-field-help">默认折叠。这里给 agent 核验 query、dominant topics、missing evidence 和 proposal candidate，不作为默认阅读层。</p>
          <dl>
            <div><dt>query / 查询词</dt><dd>{sessionSummary.query || "all redacted memory"}</dd></div>
            <div><dt>dominant_topics / 主导主题</dt><dd>{sessionSummary.dominant_topics.join(" / ") || "none"}</dd></div>
            <div><dt>high_importance_hits / 高重要命中</dt><dd>{sessionSummary.high_importance_hits.join(" / ") || "none"}</dd></div>
            <div><dt>stale_or_black_hole_hits / 过期或低价值命中</dt><dd>{sessionSummary.stale_or_black_hole_hits.join(" / ") || "none"}</dd></div>
            <div><dt>missing_evidence / 缺证据项</dt><dd>{sessionSummary.missing_evidence.join(" / ") || "none"}</dd></div>
            <div><dt>next_step / 下一步</dt><dd>{sessionSummary.next_step}</dd></div>
            <div><dt>proposal_candidate / 提案候选</dt><dd>{sessionSummary.proposal_candidate ? "true" : "false"}</dd></div>
          </dl>
        </MachineFieldDetails>
      </section>
      <div className="writeback-banner">
        <strong>写回策略</strong>
        <span>Search 2.0 只产生 proposal_candidate 判断和 Inspector 跳转；任何改动仍必须走 proposal-only handoff，不直接写长期记忆。</span>
      </div>
      {visibleResults.length ? (
        <section className="search-2-result-list" aria-label="Search 2.0 result_list">
          {visibleResults.map((result) => (
            <article
              className="search-2-result-card"
              data-search-result="true"
              data-result-id={result.result_id}
              data-result-tier={result.tier}
              data-result-topic={result.topic}
              data-result-recency={result.recency}
              data-result-importance={result.importance}
              data-matched-reason={result.matched_reason}
              data-evidence-ref={result.evidence_refs.join(",")}
              data-proposal-candidate={String(result.proposal_candidate)}
              key={result.result_id}
            >
              <header>
                <div>
                  <strong>{result.title}</strong>
                  <span>{result.source} / {result.tier} / {result.topic}</span>
                </div>
                <b>{result.importance}</b>
              </header>
              <p>{result.summary}</p>
              <MachineFieldDetails title="高级详情：结果字段" className="search-2-result-schema inline-machine-field-details">
                <dl>
                  <div><dt>matched_reason / 匹配原因</dt><dd>{result.matched_reason}</dd></div>
                  <div><dt>evidence_refs / 证据引用</dt><dd>{result.evidence_refs.join(" / ")}</dd></div>
                  <div><dt>proposal_candidate / 提案候选</dt><dd>{result.proposal_candidate ? "true" : "false"}</dd></div>
                </dl>
              </MachineFieldDetails>
              <div className="search-2-result-actions" aria-label="搜索结果操作">
                <button
                  data-search-jump="starfield"
                  data-starfield-target={result.jump_to_starfield}
                  onClick={() => jumpToSearchTarget(result, "starfield")}
                  type="button"
                >
                  <Orbit size={14} />
                  <span>跳到星图</span>
                </button>
                <button
                  data-search-jump="river"
                  data-river-target={result.jump_to_river}
                  onClick={() => jumpToSearchTarget(result, "river")}
                  type="button"
                >
                  <CalendarDays size={14} />
                  <span>跳到时间河</span>
                </button>
                <button
                  data-search-jump="inspector"
                  data-inspector-target={result.open_inspector}
                  onClick={() => jumpToSearchTarget(result, "inspector")}
                  type="button"
                >
                  <Crosshair size={14} />
                  <span>同步详情</span>
                </button>
              </div>
            </article>
          ))}
        </section>
      ) : (
        <section className="search-2-zero-recovery" data-zero-result-recovery="search_2_0">
          <div className="panel-title-row">
            <h3>无结果恢复</h3>
            <span>0 条</span>
          </div>
          <ul>
            <li>扩大查询：减少关键词或改用主题词。</li>
            <li>移除筛选：放宽层级、主题、时效、重要性或仅证据限制。</li>
            <li>相关主题：回到全部主题后查看相邻主题。</li>
            <li>过期/归档：切换过期或归档记忆查找历史线索。</li>
            <li>后续复盘提示：总结与迭代只作为复盘入口，本 phase 不执行提案应用。</li>
          </ul>
        </section>
      )}
    </div>
  );
}

function MiniBarList({ title, rows }: { title: string; rows: Array<{ label: string; count: number }> }) {
  const max = Math.max(1, ...rows.map((row) => row.count));
  return (
    <div className="mini-bar-list">
      <strong>{title}</strong>
      {rows.length ? (
        rows.map((row) => (
          <div className="mini-bar-row" key={`${title}-${row.label}`}>
            <span>{row.label}</span>
            <i style={{ "--bar-width": `${Math.max(4, Math.round((row.count / max) * 100))}%` } as CSSProperties} aria-hidden="true" />
            <b>{row.count.toLocaleString()}</b>
          </div>
        ))
      ) : (
        <p>暂无</p>
      )}
    </div>
  );
}

function buildSearch2Results(atlas: MemoryAtlas, nodes: AtlasNode[], filters: Search2Filters): Search2Result[] {
  const latest = maxNodeDate(nodes) ?? new Date();
  const query = normalizeSearch2Text(filters.query);
  return nodes
    .map((node) => buildSearch2Result(atlas, node, latest, query))
    .filter((result) => {
      if (filters.tier !== "all" && result.tier !== filters.tier) return false;
      if (filters.topic !== "all" && result.topic !== filters.topic) return false;
      if (filters.recency !== "all" && result.recency !== filters.recency) return false;
      if (filters.importance !== "all" && result.importance !== filters.importance) return false;
      if (filters.evidenceOnly && result.evidence_refs.length === 0) return false;
      if (!query) return true;
      return search2CandidateFields(result, result.node).some((value) => normalizeSearch2Text(value).includes(query));
    })
    .map((result) => ({
      ...result,
      matched_reason: buildSearch2MatchedReason(result, query),
      score: search2Score(result, query),
    }))
    .sort((a, b) => b.score - a.score || (b.node.date ?? "").localeCompare(a.node.date ?? "") || a.title.localeCompare(b.title, "zh-CN"));
}

function buildSearch2Result(atlas: MemoryAtlas, node: AtlasNode, latest: Date, query: string): Search2Result {
  const duplicateCount = duplicateCountForNode(nodesForDuplicateCount(atlas), node);
  const preview = buildSearchResultPreview(node, duplicateCount);
  const topic = humanThemeLabel(node);
  const evidenceRefs = buildSearch2EvidenceRefs(atlas, node);
  const recency = search2RecencyForNode(node, latest);
  const importance = search2ImportanceForNode(node);
  const tier = search2TierForNode(node, recency);
  return {
    result_id: node.id,
    title: preview.title,
    summary: preview.summary,
    source: node.source_label || node.data_source || atlas.source_contract.export_profile || "redacted snapshot",
    tier,
    topic,
    recency,
    importance,
    matched_reason: query ? "matched_reason pending query scoring" : "matched_reason default ranking by importance, recency and evidence",
    evidence_refs: evidenceRefs,
    jump_to_starfield: node.visual?.cluster ? `cluster:${node.visual.cluster}` : node.id,
    jump_to_river: node.date ? `date:${node.date}` : "no_river_event_ref",
    open_inspector: node.id,
    proposal_candidate: search2ProposalCandidate(node, importance, recency),
    score: 0,
    node,
  };
}

function nodesForDuplicateCount(atlas: MemoryAtlas): AtlasNode[] {
  return getMemoryNodes(atlas);
}

function duplicateCountForNode(nodes: AtlasNode[], node: AtlasNode): number {
  const title = humanNodeDisplayTitle(node);
  const summary = humanizeStatement(node.statement);
  const key = normalizeDisplayKey(`${node.kind}|${node.category}|${title}|${summary || node.label}`);
  return nodes.filter((candidate) => {
    const candidateKey = normalizeDisplayKey(`${candidate.kind}|${candidate.category}|${humanNodeDisplayTitle(candidate)}|${humanizeStatement(candidate.statement) || candidate.label}`);
    return candidateKey === key;
  }).length || 1;
}

function buildSearch2EvidenceRefs(atlas: MemoryAtlas, node: AtlasNode): string[] {
  const refs = atlas.edges
    .filter((edge) => edge.source === node.id || edge.target === node.id)
    .slice(0, 4)
    .map((edge) => edge.id);
  if (node.memory_id) refs.unshift(`memory:${node.memory_id}`);
  return Array.from(new Set(refs.length ? refs : [`node:${node.id}`])).slice(0, 4);
}

function buildSearch2MatchedReason(result: Search2Result, query: string): string {
  const matchedFields = search2CandidateFields(result, result.node)
    .filter((value) => query && normalizeSearch2Text(value).includes(query))
    .slice(0, 3);
  if (matchedFields.length) {
    return `query matched ${matchedFields.map((value) => truncate(value, 36)).join(" / ")}; ranked by ${result.importance} importance, ${result.recency} recency and ${result.evidence_refs.length} evidence_refs.`;
  }
  return `default workflow match: ${result.topic}; ranked by ${result.importance} importance, ${result.recency} recency and ${result.evidence_refs.length} evidence_refs.`;
}

function search2CandidateFields(result: Search2Result, node: AtlasNode): string[] {
  return [
    result.title,
    result.summary,
    result.source,
    result.tier,
    result.topic,
    result.recency,
    result.importance,
    result.matched_reason,
    node.label,
    node.statement,
    node.category,
    node.memory_tier,
    node.source_label,
    node.data_source,
    node.metrics?.roi?.recommended_action,
  ].filter((value): value is string => Boolean(value));
}

function search2Score(result: Search2Result, query: string): number {
  const queryScore = query
    ? search2CandidateFields(result, result.node).some((value) => normalizeSearch2Text(value).includes(query)) ? 80 : 0
    : 20;
  const importanceWeight: Record<Search2Result["importance"], number> = {
    critical: 50,
    high: 40,
    medium: 24,
    low: 8,
  };
  const recencyWeight: Record<Search2Result["recency"], number> = {
    recent: 28,
    active: 20,
    stale: 14,
    archival: 8,
  };
  const evidenceScore = Math.min(18, result.evidence_refs.length * 6);
  const proposalScore = result.proposal_candidate ? 10 : 0;
  return queryScore + importanceWeight[result.importance] + recencyWeight[result.recency] + evidenceScore + proposalScore;
}

function buildSearch2SessionSummary(results: Search2Result[], query: string): Search2SessionSummary {
  const dominantTopics = topRows(countBy(results, (result) => result.topic), 3).map((row) => row.label).filter((label) => label !== "暂无数据");
  const highImportanceHits = results
    .filter((result) => result.importance === "high" || result.importance === "critical")
    .slice(0, 3)
    .map((result) => result.title);
  const staleHits = results
    .filter((result) => result.recency === "stale" || result.tier === "stale")
    .slice(0, 3)
    .map((result) => result.title);
  const missingEvidence = results
    .filter((result) => result.evidence_refs.length === 0)
    .slice(0, 3)
    .map((result) => result.title);
  return {
    query,
    result_count: results.length,
    dominant_topics: dominantTopics,
    high_importance_hits: highImportanceHits,
    stale_or_black_hole_hits: staleHits,
    missing_evidence: missingEvidence,
    next_step: results.length
      ? "Open Inspector for the strongest matched_reason, then use proposal-only handoff if a change is needed."
      : "Use zero_result_recovery before opening a later review workflow hint.",
    proposal_candidate: results.some((result) => result.proposal_candidate),
  };
}

function search2FilterStateLabel(filters: Search2Filters): string {
  return [
    `query=${filters.query || "all"}`,
    `tier=${filters.tier}`,
    `topic=${filters.topic}`,
    `recency=${filters.recency}`,
    `importance=${filters.importance}`,
    `evidence=${filters.evidenceOnly ? "required" : "optional"}`,
  ].join(" / ");
}

function search2TierForNode(node: AtlasNode, recency: Search2Result["recency"]): Search2Result["tier"] {
  const tier = normalizeMemoryTier(node.memory_tier);
  if (node.category === "deprecated_info" || recency === "stale") return "stale";
  if (tier.includes("核心") || node.category === "preference") return "core_profile";
  if (node.category === "decision" || node.kind === "decision") return "decision";
  if (node.category === "workflow") return "workflow";
  if (node.category === "project_context" || node.kind === "project") return "project";
  if (node.metrics?.roi?.recommended_action || /机会|opportunity/i.test(`${node.label} ${node.statement ?? ""}`)) return "opportunity";
  return "knowledge";
}

function search2RecencyForNode(node: AtlasNode, latest: Date): Search2Result["recency"] {
  if (node.category === "deprecated_info" || /过期|deprecated|stale/i.test(`${node.validity ?? ""} ${node.metrics?.roi?.staleness_status ?? ""}`)) {
    return "stale";
  }
  const day = node.date ? new Date(node.date) : null;
  if (!day || Number.isNaN(day.getTime())) return "archival";
  if (isNodeBetween(node, addDays(latest, -30), latest)) return "recent";
  if (isNodeBetween(node, addDays(latest, -180), latest)) return "active";
  return "archival";
}

function search2ImportanceForNode(node: AtlasNode): Search2Result["importance"] {
  const value = `${node.importance ?? ""} ${node.metrics?.weight_score ?? ""}`.toLowerCase();
  if (/critical|最高|关键|紧急/.test(value)) return "critical";
  if (/high|高/.test(value)) return "high";
  if (/low|低/.test(value)) return "low";
  return "medium";
}

function search2ProposalCandidate(
  node: AtlasNode,
  importance: Search2Result["importance"],
  recency: Search2Result["recency"],
): boolean {
  const text = `${node.label} ${node.statement ?? ""} ${node.metrics?.roi?.recommended_action ?? ""}`;
  return (
    importance === "critical" ||
    (importance === "high" && recency !== "archival") ||
    /下一步|继续|需要|建议|todo|action|优化|修正|降权|隐藏|补充/i.test(text)
  );
}

function normalizeSearch2Text(value: string): string {
  return value.toLowerCase().replace(/\s+/g, " ").trim();
}

const REVIEW_PERIOD_OPTIONS: Array<{ id: ReviewPeriodId; label: string; days: number | null }> = [
  { id: "last_30_days", label: "最近 30 天", days: 30 },
  { id: "last_90_days", label: "最近 90 天", days: 90 },
  { id: "all", label: "全部 redacted snapshot", days: null },
];

const REVIEW_PANEL_IDS: ReviewPanelId[] = [
  "review_period_selector",
  "theme_change_panel",
  "opportunity_panel",
  "low_value_loop_panel",
  "decision_change_panel",
  "next_action_panel",
  "proposal_decision_panel",
  "iteration_backlog",
];

function buildReviewSummaryIteration(
  atlas: MemoryAtlas,
  nodes: AtlasNode[],
  deltaStats: DeltaStats,
  periodId: ReviewPeriodId,
): ReviewSummaryIterationOutput {
  const latest = parseDay(deltaStats.latestDate) ?? parseDay(atlas.contribution.range_end) ?? maxNodeDate(nodes) ?? new Date();
  const period = REVIEW_PERIOD_OPTIONS.find((option) => option.id === periodId) ?? REVIEW_PERIOD_OPTIONS[0];
  const start = period.days === null ? parseDay(atlas.contribution.range_start) ?? maxNodeDate(nodes) ?? latest : addDays(latest, -(period.days - 1));
  const scopedNodes = period.days === null ? nodes : nodes.filter((node) => isNodeBetween(node, start, latest));
  const reviewNodes = scopedNodes.length ? scopedNodes : nodes;
  const dominant_topics = reviewTopicRows(atlas, reviewNodes, 4);
  const strengthening_topics = reviewStrengtheningRows(atlas, nodes, latest);
  const declining_topics = reviewDecliningRows(atlas, nodes, latest);
  const new_opportunities = reviewOpportunityRows(atlas, reviewNodes);
  const low_value_loops = reviewLowValueLoopRows(atlas, reviewNodes);
  const decision_changes = reviewDecisionRows(atlas, reviewNodes);
  const evidence_refs = reviewEvidenceRefs(atlas, [
    ...dominant_topics,
    ...strengthening_topics,
    ...declining_topics,
    ...new_opportunities,
    ...low_value_loops,
    ...decision_changes,
  ]);
  const next_actions = reviewNextActions(atlas, reviewNodes, evidence_refs);
  const proposalReason = low_value_loops.length
    ? `发现 ${low_value_loops[0].title}，建议生成 proposal-only update candidate，先处理低价值循环。`
    : new_opportunities.length
      ? `发现 ${new_opportunities[0].title}，可以生成 proposal-only update candidate 汇总机会。`
      : "本期没有强制写回条件，保留 review-only note 等待下一轮复盘。";
  const shouldGenerateProposal = low_value_loops.some((item) => item.count > 0) || new_opportunities.some((item) => item.count > 0);
  const iteration_backlog = reviewIterationBacklog(next_actions, low_value_loops, new_opportunities, dominant_topics);
  const review_again_at = toDayKey(addDays(latest, 7));
  const output: ReviewSummaryIterationOutput = {
    review_id: `review_${periodId}_${toDayKey(latest)}`,
    review_schema_version: REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION,
    time_window: {
      period_id: periodId,
      label: `${period.label}（${toDayKey(start)} 至 ${toDayKey(latest)}）`,
      range_start: toDayKey(start),
      range_end: toDayKey(latest),
      node_count: reviewNodes.length,
    },
    source_scope: "redacted_atlas_snapshot",
    dominant_topics,
    strengthening_topics,
    declining_topics,
    new_opportunities,
    low_value_loops,
    decision_changes,
    next_actions,
    proposal_candidate: {
      should_generate: shouldGenerateProposal,
      proposal_decision: shouldGenerateProposal ? "generate_proposal" : "review_only",
      target_type: shouldGenerateProposal ? "memory_update_candidate" : "review_only_note",
      reason: proposalReason,
      rollback_hint: "proposal-only 交接；若人工复核不成立，丢弃 proposal 草稿即可，不会修改长期记忆。",
      requires_conflict_check: true,
      requires_agent_or_human_apply: true,
    },
    evidence_refs,
    confidence: reviewNodes.length >= 20 && evidence_refs.length >= 3 ? "high" : reviewNodes.length >= 5 ? "medium" : "low",
    iteration: {
      iteration_backlog,
      review_again_at,
      proposal_only: true,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
    },
    questions: [],
    panelIds: REVIEW_PANEL_IDS,
  };
  output.questions = buildReviewQuestions(output);
  return output;
}

function buildSummaryIterationClosure(review: ReviewSummaryIterationOutput): SummaryIterationClosureOutput {
  const change_comparison: SummaryClosureChangeRow[] = [
    ...review.strengthening_topics.slice(0, 3).map((row, index) =>
      summaryClosureChangeRow(row, `strengthening:${index}`, Math.max(row.count, 0), 0),
    ),
    ...review.declining_topics.slice(0, 3).map((row, index) =>
      summaryClosureChangeRow(row, `declining:${index}`, 0, Math.max(row.count, 0)),
    ),
  ];
  if (change_comparison.length < 3) {
    review.dominant_topics.slice(0, 3 - change_comparison.length).forEach((row, index) => {
      change_comparison.push(summaryClosureChangeRow(row, `dominant:${index}`, Math.max(row.count, 0), Math.max(row.count, 0)));
    });
  }

  const staleSignals = review.low_value_loops.slice(0, 2).map<SummaryClosureSignal>((row, index) => ({
    signal_id: `stale:${index}`,
    signal_type: "stale",
    severity: row.count > 0 ? "high" : "low",
    title: row.title,
    summary: row.summary,
    evidence_refs: row.evidence_refs.length ? row.evidence_refs : review.evidence_refs.slice(0, 2),
    proposal_hint: row.count > 0 ? "生成 proposal-only cleanup candidate，人工确认后再降权、合并或删除。" : "保留观察，不生成直接写回。",
    rollback_hint: "如果复核发现 stale 判断不成立，丢弃 candidate；长期记忆不会被前端修改。",
  }));
  const conflictSignals = review.decision_changes.slice(0, 2).map<SummaryClosureSignal>((row, index) => ({
    signal_id: `conflict:${index}`,
    signal_type: "conflict",
    severity: row.count > 0 ? "medium" : "low",
    title: row.title,
    summary: row.summary,
    evidence_refs: row.evidence_refs.length ? row.evidence_refs : review.evidence_refs.slice(0, 2),
    proposal_hint: "进入人工 conflict check；只有确认新决策覆盖旧背景后才生成长期记忆修改。",
    rollback_hint: "若冲突未确认，保留 review-only note，不写 proposal queue 或长期记忆。",
  }));
  const stale_conflict_signals = [...staleSignals, ...conflictSignals].slice(0, 4);

  const proposal_candidates = review.next_actions.slice(0, 3).map<SummaryClosureProposalCandidate>((action, index) => ({
    proposal_id: `summary_closure_candidate:${index + 1}`,
    title: action.title,
    target_type: review.proposal_candidate.target_type,
    reason: action.reason,
    evidence_refs: action.evidence_refs.length ? action.evidence_refs : review.evidence_refs.slice(0, 2),
    rollback_hint: "proposal-only candidate；人工或 agent 复核前不写长期记忆，回滚方式是丢弃候选。",
    requires_conflict_check: true,
    requires_agent_or_human_apply: true,
    proposal_only: true,
  }));

  return {
    closure_id: `summary_closure_${review.time_window.period_id}_${review.time_window.range_end}`,
    closure_schema_version: SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION,
    source_review_schema_version: REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION,
    source_scope: "redacted_atlas_snapshot",
    change_comparison,
    stale_conflict_signals,
    proposal_candidates,
    closure_summary: `change_comparison=${change_comparison.length}; stale_conflict_signals=${stale_conflict_signals.length}; proposal_candidates=${proposal_candidates.length}; all outputs remain proposal-only.`,
    safety: {
      proposal_only: true,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
      proposalWrite: false,
    },
    panelIds: ["change_comparison", "stale_conflict_signals", "proposal_candidates"],
  };
}

function summaryClosureChangeRow(
  row: ReviewSignalRow,
  signalId: string,
  currentCount: number,
  previousCount: number,
): SummaryClosureChangeRow {
  return {
    signal_id: signalId,
    title: row.title,
    summary: row.summary,
    current_count: currentCount,
    previous_count: previousCount,
    delta: currentCount - previousCount,
    evidence_refs: row.evidence_refs,
  };
}

function reviewQuestionAnswerById(output: ReviewSummaryIterationOutput, questionId: ReviewQuestionId): ReviewQuestionAnswer {
  return output.questions.find((item) => item.question_id === questionId) ?? {
    question_id: questionId,
    panel_id: "theme_change_panel",
    question: "本期主导主题是什么",
    answer: "当前 review 输出尚未生成足够证据，保持观察。",
    evidence_refs: output.evidence_refs.slice(0, 2),
  };
}

function buildReviewQuestions(output: ReviewSummaryIterationOutput): ReviewQuestionAnswer[] {
  return [
    {
      question_id: "dominant_topics",
      panel_id: "theme_change_panel",
      question: "本期主导主题是什么",
      answer: reviewRowSentence(output.dominant_topics, "主导主题"),
      evidence_refs: output.dominant_topics[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "strengthening_topics",
      panel_id: "theme_change_panel",
      question: "哪些主题增强",
      answer: reviewRowSentence(output.strengthening_topics, "增强主题"),
      evidence_refs: output.strengthening_topics[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "declining_topics",
      panel_id: "theme_change_panel",
      question: "哪些主题衰退",
      answer: reviewRowSentence(output.declining_topics, "衰退主题"),
      evidence_refs: output.declining_topics[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "new_opportunities",
      panel_id: "opportunity_panel",
      question: "哪些新机会出现",
      answer: reviewRowSentence(output.new_opportunities, "新机会"),
      evidence_refs: output.new_opportunities[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "low_value_loops",
      panel_id: "low_value_loop_panel",
      question: "哪些低价值循环出现",
      answer: reviewRowSentence(output.low_value_loops, "低价值循环"),
      evidence_refs: output.low_value_loops[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "decision_changes",
      panel_id: "decision_change_panel",
      question: "哪些决策变化",
      answer: reviewRowSentence(output.decision_changes, "决策变化"),
      evidence_refs: output.decision_changes[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "next_actions",
      panel_id: "next_action_panel",
      question: "下一步动作是什么",
      answer: output.next_actions.map((item) => `${item.title}：${item.reason}`).slice(0, 3).join("；"),
      evidence_refs: output.next_actions[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "proposal_decision",
      panel_id: "proposal_decision_panel",
      question: "是否需要生成 proposal",
      answer: `${output.proposal_candidate.proposal_decision}；${output.proposal_candidate.reason}`,
      evidence_refs: output.evidence_refs.slice(0, 3),
    },
  ];
}

function reviewTopicRows(atlas: MemoryAtlas, nodes: AtlasNode[], limit: number): ReviewSignalRow[] {
  const rows = topRows(countBy(nodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)), limit);
  return rows.map((row) => {
    const topicNodes = nodes.filter((node) => (compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)) === row.label);
    return reviewSignalRow(atlas, row.label, `${row.label} 在当前窗口内出现 ${row.count.toLocaleString()} 次，是复盘优先入口。`, row.count, topicNodes);
  });
}

function reviewStrengtheningRows(atlas: MemoryAtlas, nodes: AtlasNode[], latest: Date): ReviewSignalRow[] {
  const recentStart = addDays(latest, -29);
  const previousStart = addDays(latest, -59);
  const previousEnd = addDays(latest, -30);
  const recentNodes = nodes.filter((node) => isNodeBetween(node, recentStart, latest));
  const previousNodes = nodes.filter((node) => isNodeBetween(node, previousStart, previousEnd));
  const recentCounts = countBy(recentNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category));
  const previousCounts = countBy(previousNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category));
  const rows = Object.keys(recentCounts)
    .map((title) => ({ title, count: recentCounts[title] - (previousCounts[title] ?? 0) }))
    .filter((row) => row.count > 0)
    .sort((left, right) => right.count - left.count || left.title.localeCompare(right.title, "zh-CN"))
    .slice(0, 3);
  const fallback = rows.length ? rows : topRows(recentCounts, 3).map((row) => ({ title: row.label, count: row.count }));
  return fallback.map((row) => {
    const topicNodes = recentNodes.filter((node) => (compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)) === row.title);
    return reviewSignalRow(atlas, row.title, `${row.title} 近 30 天净增 ${formatSigned(row.count)} 条，优先检查是否进入下一轮任务。`, row.count, topicNodes);
  });
}

function reviewDecliningRows(atlas: MemoryAtlas, nodes: AtlasNode[], latest: Date): ReviewSignalRow[] {
  const recentStart = addDays(latest, -29);
  const previousStart = addDays(latest, -59);
  const previousEnd = addDays(latest, -30);
  const recentNodes = nodes.filter((node) => isNodeBetween(node, recentStart, latest));
  const previousNodes = nodes.filter((node) => isNodeBetween(node, previousStart, previousEnd));
  const recentCounts = countBy(recentNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category));
  const previousCounts = countBy(previousNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category));
  const rows = Object.keys(previousCounts)
    .map((title) => ({ title, count: previousCounts[title] - (recentCounts[title] ?? 0) }))
    .filter((row) => row.count > 0)
    .sort((left, right) => right.count - left.count || left.title.localeCompare(right.title, "zh-CN"))
    .slice(0, 3);
  const staleNodes = nodes.filter((node) => node.category === "deprecated_info" || node.metrics?.roi?.staleness_status);
  const fallback = rows.length
    ? rows
    : topRows(countBy(staleNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)), 3).map((row) => ({
        title: row.label,
        count: row.count,
      }));
  return fallback.map((row) => {
    const topicNodes = previousNodes.concat(staleNodes).filter((node) => (compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)) === row.title);
    return reviewSignalRow(atlas, row.title, `${row.title} 当前动能下降或带有 stale 信号，需要降权、合并或标注时效。`, row.count, topicNodes);
  });
}

function reviewOpportunityRows(atlas: MemoryAtlas, nodes: AtlasNode[]): ReviewSignalRow[] {
  const opportunityNodes = nodes
    .filter((node) => /机会|opportunity|下一步|继续|action|proposal|优化|扩展/i.test(`${node.label} ${node.statement ?? ""} ${node.metrics?.roi?.recommended_action ?? ""}`))
    .sort(reviewNodeSort);
  const rows = opportunityNodes.slice(0, 3).map((node) =>
    reviewSignalRow(atlas, humanNodeDisplayTitle(node), recommendedActionForNode(node), 1, [node]),
  );
  if (rows.length) return rows;
  return reviewTopicRows(atlas, nodes, 1).map((row) => ({
    ...row,
    title: `机会待确认：${row.title}`,
    summary: "当前窗口没有明显机会信号，先从主导主题里人工确认是否值得推进。",
    count: 0,
  }));
}

function reviewLowValueLoopRows(atlas: MemoryAtlas, nodes: AtlasNode[]): ReviewSignalRow[] {
  const lowValueNodes = nodes.filter((node) => {
    const tier = normalizeMemoryTier(node.memory_tier);
    return (
      tier === "临时" ||
      node.category === "temporary_or_sensitive" ||
      node.category === "deprecated_info" ||
      /临时|过期|stale|低权重|重复|噪音/i.test(`${node.label} ${node.statement ?? ""} ${node.validity ?? ""} ${node.metrics?.roi?.staleness_status ?? ""}`)
    );
  });
  const rows = topRows(countBy(lowValueNodes, (node) => humanCategoryLabel(node.category) || normalizeMemoryTier(node.memory_tier)), 3)
    .filter((row) => row.count > 0)
    .map((row) => {
      const rowNodes = lowValueNodes.filter((node) => (humanCategoryLabel(node.category) || normalizeMemoryTier(node.memory_tier)) === row.label);
      return reviewSignalRow(atlas, row.label, `${row.label} 出现 ${row.count.toLocaleString()} 次；建议压缩、降权或转成有时效标记的背景。`, row.count, rowNodes);
    });
  return rows.length
    ? rows
    : [reviewSignalRow(atlas, "低价值循环未显著出现", "当前窗口没有明显短期噪音或过期信息，可先保持观察。", 0, nodes.slice(0, 1))];
}

function reviewDecisionRows(atlas: MemoryAtlas, nodes: AtlasNode[]): ReviewSignalRow[] {
  const decisionNodes = nodes
    .filter((node) => node.category === "decision" || node.kind === "decision" || /决策|决定|选择|批准|停止/i.test(`${node.label} ${node.statement ?? ""}`))
    .sort(reviewNodeSort);
  const rows = decisionNodes.slice(0, 3).map((node) =>
    reviewSignalRow(atlas, humanNodeDisplayTitle(node), humanizeStatement(node.statement) || recommendedActionForNode(node), 1, [node]),
  );
  return rows.length
    ? rows
    : [reviewSignalRow(atlas, "决策变化未显著出现", "当前窗口没有新的 decision 类节点；后续若出现新证据再生成修改 proposal。", 0, nodes.slice(0, 1))];
}

function reviewNextActions(atlas: MemoryAtlas, nodes: AtlasNode[], evidenceRefs: string[]): ReviewNextAction[] {
  const recommendationItems = atlas.agent_recommendations
    ? [
        ...atlas.agent_recommendations.memory.added,
        ...atlas.agent_recommendations.memory.modified.map((item) => item.after),
        ...atlas.agent_recommendations.meta_data.added,
        ...atlas.agent_recommendations.meta_data.modified.map((item) => item.after),
      ]
    : [];
  const recommendationActions = recommendationItems.slice(0, 3).map<ReviewNextAction>((item, index) => ({
    action_id: `agent_recommendation:${item.id || index}`,
    title: item.title,
    reason: item.reason || item.statement,
    priority: item.importance === "high" ? "high" : "medium",
    source_scope: "agent_recommendations_redacted",
    evidence_refs: item.source ? [`recommendation:${item.source}`] : evidenceRefs.slice(0, 2),
    acceptance_hint: "人工确认后进入 proposal-only handoff，不由前端直接写长期记忆。",
  }));
  if (recommendationActions.length) return recommendationActions;

  return [...nodes]
    .sort((left, right) => (right.metrics?.roi?.leverage_score ?? 0) - (left.metrics?.roi?.leverage_score ?? 0))
    .slice(0, 3)
    .map<ReviewNextAction>((node, index) => ({
      action_id: `review_action:${node.id || index}`,
      title: humanNodeDisplayTitle(node),
      reason: recommendedActionForNode(node),
      priority: search2ImportanceForNode(node) === "critical" ? "high" : "medium",
      source_scope: "redacted_atlas_snapshot",
      evidence_refs: buildSearch2EvidenceRefs(atlas, node),
      acceptance_hint: "进入下一阶段前需要可审查记录、回滚提示和 validator 证明。",
    }));
}

function reviewIterationBacklog(
  nextActions: ReviewNextAction[],
  lowValueLoops: ReviewSignalRow[],
  opportunities: ReviewSignalRow[],
  dominantTopics: ReviewSignalRow[],
): ReviewIterationItem[] {
  const items: ReviewIterationItem[] = [
    {
      item_id: "iteration_backlog:proposal_triage",
      title: "Proposal triage",
      why_it_matters: nextActions[0]?.reason || "需要把本期结论转成可审查、可回滚的候选更新。",
      next_step: nextActions[0]?.title || "选择最高价值 review action",
      acceptance_hint: "生成 proposal-only 候选，不直接写长期记忆。",
      priority: nextActions[0]?.priority || "medium",
    },
    {
      item_id: "iteration_backlog:low_value_loop",
      title: "Low-value loop cleanup",
      why_it_matters: lowValueLoops[0]?.summary || "低价值循环会污染长期召回，需要周期性压缩或降权。",
      next_step: lowValueLoops[0]?.title || "复核低价值循环",
      acceptance_hint: "保留证据 refs，人工确认后再修改记忆权重。",
      priority: lowValueLoops[0]?.count ? "high" : "low",
    },
    {
      item_id: "iteration_backlog:opportunity_capture",
      title: "Opportunity capture",
      why_it_matters: opportunities[0]?.summary || dominantTopics[0]?.summary || "主导主题需要被转成下一步动作，否则只停留在可视化层。",
      next_step: opportunities[0]?.title || dominantTopics[0]?.title || "复核主导主题",
      acceptance_hint: "下一轮 validator 应能看到 evidence_refs 和 decision/proposal 边界。",
      priority: opportunities[0]?.count ? "high" : "medium",
    },
  ];
  return items;
}

function reviewSignalRow(
  atlas: MemoryAtlas,
  title: string,
  summary: string,
  count: number,
  nodes: AtlasNode[],
): ReviewSignalRow {
  return {
    title,
    summary,
    count,
    evidence_refs: reviewNodeEvidenceRefs(atlas, nodes),
  };
}

function reviewNodeEvidenceRefs(atlas: MemoryAtlas, nodes: AtlasNode[]): string[] {
  const refs = nodes.flatMap((node) => buildSearch2EvidenceRefs(atlas, node));
  return Array.from(new Set(refs.length ? refs : ["source:redacted_atlas_snapshot"])).slice(0, 4);
}

function reviewEvidenceRefs(atlas: MemoryAtlas, rows: ReviewSignalRow[]): string[] {
  const refs = rows.flatMap((row) => row.evidence_refs);
  return Array.from(new Set(refs.length ? refs : [`source:${atlas.source_contract.export_profile}`])).slice(0, 8);
}

function reviewRowSentence(rows: ReviewSignalRow[], fallbackLabel: string): string {
  const activeRows = rows.filter((row) => row.count > 0);
  const displayRows = activeRows.length ? activeRows : rows;
  return displayRows.length
    ? displayRows.slice(0, 3).map((row) => `${row.title}（${row.count.toLocaleString()}）：${row.summary}`).join("；")
    : `${fallbackLabel} 暂无足够证据，保持观察。`;
}

function reviewNodeSort(left: AtlasNode, right: AtlasNode): number {
  const scoreDelta = (right.metrics?.roi?.leverage_score ?? 0) - (left.metrics?.roi?.leverage_score ?? 0);
  if (scoreDelta) return scoreDelta;
  return (right.date ?? "").localeCompare(left.date ?? "") || humanNodeDisplayTitle(left).localeCompare(humanNodeDisplayTitle(right), "zh-CN");
}

function SummaryIterationView({
  atlas,
  nodes,
  deltaStats,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
}) {
  const recommendations = atlas.agent_recommendations;
  const updatedAt = formatUpdatedAt(recommendations?.generated_at || atlas.overview.generated_at);
  const highlights = useMemo(() => buildIterationHighlights(nodes, deltaStats), [nodes, deltaStats]);
  const [reviewPeriod, setReviewPeriod] = useState<ReviewPeriodId>("last_30_days");
  const reviewSummary = useMemo(
    () => buildReviewSummaryIteration(atlas, nodes, deltaStats, reviewPeriod),
    [atlas, nodes, deltaStats, reviewPeriod],
  );
  const summaryClosure = useMemo(() => buildSummaryIterationClosure(reviewSummary), [reviewSummary]);
  const dominantAnswer = reviewQuestionAnswerById(reviewSummary, "dominant_topics");
  const strengtheningAnswer = reviewQuestionAnswerById(reviewSummary, "strengthening_topics");
  const decliningAnswer = reviewQuestionAnswerById(reviewSummary, "declining_topics");
  const opportunityAnswer = reviewQuestionAnswerById(reviewSummary, "new_opportunities");
  const lowValueAnswer = reviewQuestionAnswerById(reviewSummary, "low_value_loops");
  const decisionAnswer = reviewQuestionAnswerById(reviewSummary, "decision_changes");
  const nextActionAnswer = reviewQuestionAnswerById(reviewSummary, "next_actions");
  const proposalAnswer = reviewQuestionAnswerById(reviewSummary, "proposal_decision");
  const schemaQuestionLine = reviewSummary.questions.map((item) => item.question).join(" / ");

  useEffect(() => {
    window.__memoryAtlasStage7Phase2 = () => ({
      runtimeVersion: REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION,
      reviewSchemaVersion: REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION,
      questionCount: reviewSummary.questions.length,
      panelIds: reviewSummary.panelIds,
      iterationItemCount: reviewSummary.iteration.iteration_backlog.length,
      proposalCandidate: reviewSummary.proposal_candidate.should_generate,
      hasEvidenceRefs: reviewSummary.evidence_refs.length > 0,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
    });
    return () => {
      delete window.__memoryAtlasStage7Phase2;
    };
  }, [reviewSummary]);

  useEffect(() => {
    window.__memoryAtlasStage8Phase1 = () => ({
      runtimeVersion: SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION,
      closureSchemaVersion: SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION,
      sourceReviewSchemaVersion: REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION,
      panelIds: summaryClosure.panelIds,
      changeComparisonCount: summaryClosure.change_comparison.length,
      staleConflictSignalCount: summaryClosure.stale_conflict_signals.length,
      proposalCandidateCount: summaryClosure.proposal_candidates.length,
      proposalOnly: true,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
      proposalWrite: false,
    });
    return () => {
      delete window.__memoryAtlasStage8Phase1;
    };
  }, [summaryClosure]);

  return (
    <div
      className="summary-iteration-view visual-workspace review-summary-runtime"
      data-review-summary-iteration-runtime={REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION}
      data-review-schema-version={REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION}
    >
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">总结与迭代</p>
          <h2>把当前记忆切片转成可更新的 Personalization、Agents.md 和 Memory 建议</h2>
        </div>
        <span>更新时间：{updatedAt}</span>
      </div>
      <section className="review-period-selector" data-review-period-selector="true" data-review-panel="review_period_selector">
        <label>
          <span>复盘窗口</span>
          <select value={reviewPeriod} onChange={(event) => setReviewPeriod(event.target.value as ReviewPeriodId)}>
            {REVIEW_PERIOD_OPTIONS.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <p>{reviewSummary.time_window.label} · {reviewSummary.time_window.node_count.toLocaleString()} 条 redacted 节点</p>
      </section>
      <section
        className="review-session-output"
        data-review-output-schema={REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION}
        data-proposal-candidate={String(reviewSummary.proposal_candidate.should_generate)}
        data-evidence-ref={reviewSummary.evidence_refs.join(",")}
      >
        <div className="panel-title-row">
          <h3>复盘会话输出</h3>
          <span>置信度：{reviewSummary.confidence}</span>
        </div>
        <p>默认层只回答八个复盘问题；schema、panel id 和 evidence refs 已收进高级详情。</p>
        <MachineFieldDetails title="高级详情：复盘 schema 与字段" className="review-machine-details">
          <p className="machine-field-help">
            review_schema_version={reviewSummary.review_schema_version}; dominant_topics; strengthening_topics;
            declining_topics; new_opportunities; low_value_loops; decision_changes; next_actions; proposal_candidate;
            evidence_refs; iteration_backlog. Questions: {schemaQuestionLine}
          </p>
          <div className="review-output-grid">
            <span>review_id：{reviewSummary.review_id}</span>
            <span>source_scope：{reviewSummary.source_scope}</span>
            <span>proposal_decision：{reviewSummary.proposal_candidate.proposal_decision}</span>
            <span>panels：{reviewSummary.panelIds.join(", ")}</span>
          </div>
        </MachineFieldDetails>
      </section>
      <DeltaStrip stats={deltaStats} compact />
      <div className="summary-signal-grid" aria-label="总结与迭代关键结论">
        {highlights.map((item) => (
          <SummarySignalCard key={item.label} label={item.label} value={item.value} note={item.note} />
        ))}
      </div>
      <section className="review-question-grid" aria-label="Review / Summary / Iteration 八个问题">
        <article className="review-question-card" data-review-question="dominant_topics" data-review-panel="theme_change_panel">
          <strong>{dominantAnswer.question}</strong>
          <p>{dominantAnswer.answer}</p>
          <EvidenceRefsDetails refs={dominantAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="strengthening_topics" data-review-panel="theme_change_panel">
          <strong>{strengtheningAnswer.question}</strong>
          <p>{strengtheningAnswer.answer}</p>
          <EvidenceRefsDetails refs={strengtheningAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="declining_topics" data-review-panel="theme_change_panel">
          <strong>{decliningAnswer.question}</strong>
          <p>{decliningAnswer.answer}</p>
          <EvidenceRefsDetails refs={decliningAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="new_opportunities" data-review-panel="opportunity_panel">
          <strong>{opportunityAnswer.question}</strong>
          <p>{opportunityAnswer.answer}</p>
          <EvidenceRefsDetails refs={opportunityAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="low_value_loops" data-review-panel="low_value_loop_panel">
          <strong>{lowValueAnswer.question}</strong>
          <p>{lowValueAnswer.answer}</p>
          <EvidenceRefsDetails refs={lowValueAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="decision_changes" data-review-panel="decision_change_panel">
          <strong>{decisionAnswer.question}</strong>
          <p>{decisionAnswer.answer}</p>
          <EvidenceRefsDetails refs={decisionAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="next_actions" data-review-panel="next_action_panel">
          <strong>{nextActionAnswer.question}</strong>
          <p>{nextActionAnswer.answer}</p>
          <EvidenceRefsDetails refs={nextActionAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="proposal_decision" data-review-panel="proposal_decision_panel">
          <strong>{proposalAnswer.question}</strong>
          <p>{proposalAnswer.answer}</p>
          <EvidenceRefsDetails refs={proposalAnswer.evidence_refs} />
        </article>
      </section>
      <section className="review-runtime-panels" aria-label="Review / Summary / Iteration 运行面板">
        <article className="proposal-decision-panel" data-review-panel="proposal_decision_panel">
          <div className="panel-title-row">
            <h3>提案判断</h3>
            <span>{reviewSummary.proposal_candidate.target_type}</span>
          </div>
          <strong>{reviewSummary.proposal_candidate.should_generate ? "建议生成提案" : "暂不生成提案"}</strong>
          <p>{reviewSummary.proposal_candidate.reason}</p>
          <small>{reviewSummary.proposal_candidate.rollback_hint}</small>
        </article>
        <article className="iteration-backlog" data-review-panel="iteration_backlog">
          <div className="panel-title-row">
            <h3>迭代待办</h3>
            <span>{reviewSummary.iteration.review_again_at}</span>
          </div>
          <ol>
            {reviewSummary.iteration.iteration_backlog.map((item) => (
              <li key={item.item_id}>
                <strong>{item.title}</strong>
                <p>{item.why_it_matters}</p>
                <small>{item.next_step} · {item.acceptance_hint}</small>
              </li>
            ))}
          </ol>
        </article>
      </section>
      <section
        className="summary-closure-runtime"
        data-summary-iteration-closure-runtime={SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION}
        data-summary-closure-schema-version={SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION}
        data-source-review-schema-version={REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION}
      >
        <div className="panel-title-row">
          <h3>总结与迭代闭环</h3>
          <span>仅生成提案</span>
        </div>
        <p className="summary-closure-schema-line">默认显示变化、冲突和提案候选的中文解释；schema 与机器字段在高级详情中核验。</p>
        <MachineFieldDetails title="高级详情：闭环 schema 与机器字段" className="summary-closure-machine-details">
          <p className="machine-field-help">
            closure_schema_version={summaryClosure.closure_schema_version}; source_review_schema_version={summaryClosure.source_review_schema_version};
            change_comparison; stale_conflict_signals; proposal_candidates; requires_conflict_check; requires_agent_or_human_apply.
            {summaryClosure.closure_summary}
          </p>
        </MachineFieldDetails>
        <div className="summary-closure-grid">
          <article className="summary-closure-card" data-summary-closure-panel="change_comparison">
            <div className="panel-title-row">
              <h4>变化对比</h4>
              <span>{summaryClosure.change_comparison.length} 条信号</span>
            </div>
            <ol>
              {summaryClosure.change_comparison.map((item) => (
                <li key={item.signal_id}>
                  <strong>{item.title}</strong>
                  <p>{formatSigned(item.delta)} · 当前 {item.current_count} / 上期 {item.previous_count}</p>
                  <small>{item.summary}</small>
                  <EvidenceRefsDetails refs={item.evidence_refs} />
                </li>
              ))}
            </ol>
          </article>
          <article className="summary-closure-card" data-summary-closure-panel="stale_conflict_signals">
            <div className="panel-title-row">
              <h4>过期与冲突信号</h4>
              <span>{summaryClosure.stale_conflict_signals.length} 条检查</span>
            </div>
            <ol>
              {summaryClosure.stale_conflict_signals.map((item) => (
                <li key={item.signal_id} data-summary-signal-type={item.signal_type}>
                  <strong>{item.signal_type}:{item.severity} · {item.title}</strong>
                  <p>{item.summary}</p>
                  <small>{item.proposal_hint} · {item.rollback_hint}</small>
                </li>
              ))}
            </ol>
          </article>
        </div>
        <article className="summary-closure-proposals" data-summary-closure-panel="proposal_candidates">
          <div className="panel-title-row">
            <h4>提案候选</h4>
            <span>{summaryClosure.proposal_candidates.length} 个候选</span>
          </div>
          <div>
            {summaryClosure.proposal_candidates.map((item) => (
              <section key={item.proposal_id}>
                <strong>{item.title}</strong>
                <p>{item.reason}</p>
                <small>需要冲突检查：{item.requires_conflict_check ? "是" : "否"}；应用方式：人工或受控代理；证据引用 {item.evidence_refs.length.toLocaleString()} 条</small>
                <MachineFieldDetails title="高级详情：提案候选字段" className="inline-machine-field-details">
                  <p className="machine-field-help">
                    proposal_id={item.proposal_id}; target_type={item.target_type}; requires_conflict_check={String(item.requires_conflict_check)};
                    requires_agent_or_human_apply={String(item.requires_agent_or_human_apply)}; evidence_refs={item.evidence_refs.join(" / ")}
                  </p>
                </MachineFieldDetails>
              </section>
            ))}
          </div>
        </article>
        <div className="summary-closure-safety">
          <span>仅生成提案：是</span>
          <span>直接写长期记忆：否</span>
          <span>包含 raw 私有数据：否</span>
          <span>前端写入 proposal：否</span>
        </div>
      </section>
      <HumanOverviewPanel nodes={nodes} deltaStats={deltaStats} />
      <section className="iteration-panels" aria-label="给 ChatGPT 和 Codex 使用的更新建议">
        <AgentRecommendationsPanel atlas={atlas} />
        <ConfigMemoryPanel atlas={atlas} updatedAt={updatedAt} />
      </section>
    </div>
  );
}

function SummarySignalCard({ label, value, note }: { label: string; value: string | number; note: string }) {
  return (
    <article className="summary-signal-card">
      <span>{label}</span>
      <strong>{typeof value === "number" ? value.toLocaleString() : value}</strong>
      <p>{note}</p>
    </article>
  );
}

function AgentRecommendationsPanel({ atlas }: { atlas: MemoryAtlas }) {
  const recommendations = atlas.agent_recommendations;
  if (!recommendations) {
    return null;
  }
  return (
    <section className="agent-recommendations" aria-label="建议写入 ChatGPT 与 Codex 的内容">
      <div className="panel-title-row">
        <h3>Personalization / Agents.md 建议</h3>
        <span>{formatUpdatedAt(recommendations.generated_at)}</span>
      </div>
      <div className="recommendation-columns">
        <RecommendationBucket title="Memory / Personalization" section={recommendations.memory} />
        <RecommendationBucket title="Agents.md / 执行规则" section={recommendations.meta_data} />
      </div>
    </section>
  );
}

function ConfigMemoryPanel({ atlas, updatedAt }: { atlas: MemoryAtlas; updatedAt: string }) {
  const recommendations = atlas.agent_recommendations;
  const memoryCurrent = recommendations?.memory.current ?? [];
  const metaCurrent = recommendations?.meta_data.current ?? [];
  const configItems = [
    {
      title: "config.toml",
      statement: "保留中文优先、真实验证、低上下文成本、每轮输出进度/风险/下一步；写库必须走提案与版本回滚。",
      count: metaCurrent.length,
    },
    {
      title: "Memory",
      statement: "优先装载核心画像、长期偏好、项目历史、决策日志和回答规则；短期信息保留但低权重召回。",
      count: memoryCurrent.length,
    },
    {
      title: "新增/删除/修改",
      statement: `新增 ${recommendations?.memory.added.length ?? 0} / 修改 ${recommendations?.memory.modified.length ?? 0} / 降权 ${recommendations?.memory.deleted.length ?? 0}；Meta 同步显示在上方。`,
      count: (recommendations?.memory.added.length ?? 0) + (recommendations?.memory.modified.length ?? 0) + (recommendations?.memory.deleted.length ?? 0),
    },
  ];
  return (
    <section className="config-memory-panel" aria-label="config.toml 和 Memory 建议">
      <div className="panel-title-row">
        <h3>config.toml / Memory</h3>
        <span>更新时间：{updatedAt}</span>
      </div>
      <div className="config-memory-grid">
        {configItems.map((item) => (
          <article key={item.title}>
            <strong>{item.title}</strong>
            <p>{item.statement}</p>
            <small>{item.count.toLocaleString()} 条相关建议</small>
          </article>
        ))}
      </div>
    </section>
  );
}

function RecommendationBucket({
  title,
  section,
}: {
  title: string;
  section: NonNullable<MemoryAtlas["agent_recommendations"]>["memory"];
}) {
  return (
    <article className="recommendation-bucket">
      <strong>{title}</strong>
      <RecommendationList label="新增" items={section.added} />
      <RecommendationList label="修改" items={section.modified.map((item) => item.after)} />
      <RecommendationList label="降权/不再默认使用" items={section.deleted} />
      <RecommendationList label="当前有效" items={section.current} limit={6} />
    </article>
  );
}

function RecommendationList({
  label,
  items,
  limit = 4,
}: {
  label: string;
  items: Array<{ id: string; title: string; statement: string; evidence_count?: number; reason?: string }>;
  limit?: number;
}) {
  const displayItems = useMemo(() => dedupeRecommendationItems(items).slice(0, limit), [items, limit]);
  return (
    <div className="recommendation-list">
      <span>{label}</span>
      {displayItems.length ? (
        <ul>
          {displayItems.map(({ item, duplicateCount }) => (
            <li key={`${label}-${item.id}`}>
              <b>{humanizeRecommendationTitle(item.title)}</b>
              <small>{humanizeStatement(item.statement)}</small>
              <em>{recommendationMeta(item, duplicateCount)}</em>
            </li>
          ))}
        </ul>
      ) : (
        <p>暂无</p>
      )}
    </div>
  );
}

function NodeInspector({
  atlas,
  node,
  edgeCount,
  sharedState,
}: {
  atlas: MemoryAtlas;
  node: AtlasNode | null;
  edgeCount: number;
  sharedState: SharedAtlasState;
}) {
  const [debugOpen, setDebugOpen] = useState(false);
  const memoryNodes = useMemo(() => getMemoryNodes(atlas), [atlas]);
  const overviewNodes = memoryNodes.length ? memoryNodes : atlas.nodes;
  useEffect(() => {
    setDebugOpen(false);
  }, [node?.id]);
  if (!node) {
    return (
      <aside
        className="inspector"
        data-shared-state={sharedState.schema_version}
        data-stage9-inspector-explanation={INSPECTOR_EXPLANATION_LAYER_VERSION}
        data-shared-focus-node=""
        data-shared-cluster=""
      >
        <h2>{uiCopy.inspector.emptyTitle}</h2>
        <p>{uiCopy.inspector.emptyDescription}</p>
        <HumanOverviewPanel nodes={overviewNodes} deltaStats={buildDeltaStats(atlas, memoryNodes)} compact />
      </aside>
    );
  }
  const humanNode = buildHumanNodeSummary(node, edgeCount);
  const explanation = buildInspectorExplanation(node, edgeCount, sharedState);
  return (
    <aside
      className="inspector"
      data-shared-state={sharedState.schema_version}
      data-stage9-inspector-explanation={INSPECTOR_EXPLANATION_LAYER_VERSION}
      data-shared-focus-node={sharedState.focus.inspector.nodeId ?? ""}
      data-shared-cluster={sharedState.focus.inspector.clusterId ?? ""}
      data-shared-record={sharedState.focus.inspector.recordId ?? ""}
      data-debug-lite={debugOpen ? "open" : "closed"}
      data-default-raw-summary="hidden"
    >
      <HumanOverviewPanel nodes={overviewNodes} deltaStats={buildDeltaStats(atlas, memoryNodes)} compact />
      <p className="eyebrow">{humanNode.scope}</p>
      <h2>{humanNode.title}</h2>
      <p className="human-node-subtitle">{humanNode.subtitle}</p>
      <section className="human-node-card">
        <div className="human-node-section">
          <strong>{uiCopy.inspector.meaningTitle}</strong>
          <ul>
            {humanNode.meaning.map((item, index) => (
              <li key={`meaning-${index}-${item}`}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="human-node-section">
          <strong>{uiCopy.inspector.impactTitle}</strong>
          <p>{humanNode.impact}</p>
        </div>
        <div className="human-node-section">
          <strong>{uiCopy.inspector.futureUseTitle}</strong>
          <ul>
            {humanNode.futureUse.map((item, index) => (
              <li key={`future-${index}-${item}`}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="human-node-section">
          <strong>{uiCopy.inspector.relatedTopicsTitle}</strong>
          <div className="human-node-topics">
            {humanNode.topics.map((topic, index) => (
              <span key={`topic-${index}-${topic}`}>{topic}</span>
            ))}
          </div>
        </div>
      </section>
      <InspectorExplanationPanel explanation={explanation} />
      <dl className="human-node-status">
        {humanNode.statusRows.map((row, index) => (
          <div key={`status-${index}-${row.label}`}><dt>{row.label}</dt><dd>{row.value}</dd></div>
        ))}
      </dl>
      <button
        className="inspector-debug-toggle"
        type="button"
        aria-expanded={debugOpen}
        aria-controls="inspector-debug-panel"
        aria-label="显示或隐藏高级详情机器字段"
        data-s10-p3-machine-fields="collapsed-by-default"
        data-s10-p3-advanced-details-entry="inspector"
        onClick={() => setDebugOpen((open) => !open)}
      >
        <Search size={15} />
        {debugOpen ? uiCopy.inspector.debugHide : uiCopy.inspector.debugShow}
      </button>
      {debugOpen ? (
        <section
          id="inspector-debug-panel"
          className="agent-structured-fields inspector-debug-panel"
          data-debug-panel="true"
          data-s10-p3-machine-fields="advanced-details-open"
        >
          <div className="panel-title-row">
            <h3>{uiCopy.inspector.debugTitle}</h3>
            <span>{uiCopy.inspector.debugDefaultHidden}</span>
          </div>
          <div className="agent-field-grid">
            <section>
              <strong>Memory（给 ChatGPT / Codex Personalization）</strong>
              <p>{humanNode.agentMemory}</p>
            </section>
            <section>
              <strong>Meta Data（给 ChatGPT / Codex Agents.md）</strong>
              <p>{humanNode.agentMeta}</p>
            </section>
          </div>
          {node.statement ? (
            <div className="raw-summary-inline">
              <strong>{uiCopy.inspector.lowSensitivitySummary}</strong>
              <p>{node.statement}</p>
            </div>
          ) : null}
          <dl>
            <div><dt>类型</dt><dd>{translateKind(node.kind)}</dd></div>
            <div><dt>连接数</dt><dd>{edgeCount.toLocaleString()}</dd></div>
            <div><dt>日期</dt><dd>{node.date || "未知"}</dd></div>
            <div><dt>分类</dt><dd>{node.category || "未知"}</dd></div>
            <div><dt>重要性</dt><dd>{node.importance || "未知"}</dd></div>
            <div><dt>有效期</dt><dd>{node.validity || "未知"}</dd></div>
            <div><dt>置信度</dt><dd>{node.confidence || "未知"}</dd></div>
            <div><dt>ROI</dt><dd>{formatScore(node.metrics?.roi?.leverage_score)}</dd></div>
          </dl>
        </section>
      ) : null}
      <WritebackProposalPanel atlas={atlas} node={node} />
    </aside>
  );
}

function InspectorExplanationPanel({ explanation }: { explanation: InspectorExplanation }) {
  return (
    <section
      className="inspector-explanation-panel"
      data-stage9-inspector-explanation={INSPECTOR_EXPLANATION_LAYER_VERSION}
      data-inspector-layer-marker="inspector_explanation_layer"
      data-raw-display="false"
      aria-label="解释面板"
    >
      <div className="panel-title-row">
        <h3>{uiCopy.inspector.explanationTitle}</h3>
        <span>{uiCopy.inspector.explanationMeta}</span>
      </div>
      <p>{explanation.summary}</p>
      <div className="inspector-formula-grid" aria-label="公式与参数">
        {explanation.formulas.map((row) => (
          <article key={row.label} className="inspector-formula-card">
            <span>{row.label}</span>
            <strong>{row.value}</strong>
            <code>{row.formula}</code>
            <small>{row.parameters}</small>
          </article>
        ))}
      </div>
      <dl className="inspector-evidence-grid" aria-label="脱敏证据摘要">
        {explanation.evidence.map((row) => (
          <div key={row.label}>
            <dt>{row.label}</dt>
            <dd>{row.value}</dd>
          </div>
        ))}
      </dl>
      <ul className="inspector-safety-list" aria-label="安全边界">
        {explanation.safetyNotes.map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
    </section>
  );
}

function ContributionPeriodInspector({
  detail,
  onSelectNode,
}: {
  detail: ContributionPeriodDetail;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const bucket = detail.bucket;
  const relatedNodes = detail.relatedNodes.slice(0, 18);
  const periodLabel = scaleLabel(detail.scale);
  return (
    <aside className="inspector contribution-period-inspector">
      <p className="eyebrow">时间段详情 · {periodLabel}</p>
      <h2>{bucket.label}</h2>
      <p>
        这个对象来自贡献网格，重点是看某个时间单位里的交互强度、记忆增量、决策密度和环比变化。
      </p>
      <section className="human-node-card">
        <div className="human-node-section">
          <strong>这段时间说明了什么</strong>
          <ul>
            <li>{periodMeaningLine(bucket, detail.scale)}</li>
            <li>当前筛选命中 {bucket.filteredMemoryCount.toLocaleString()} 条记忆，其中决策 {bucket.filteredDecisionCount.toLocaleString()} 条，核心画像 {bucket.filteredCoreCount.toLocaleString()} 条。</li>
            <li>全局交互包含 {bucket.conversationCount.toLocaleString()} 个对话、{bucket.messageCount.toLocaleString()} 条消息。</li>
          </ul>
        </div>
        <div className="human-node-section">
          <strong>为什么重要</strong>
          <p>{periodImpactLine(bucket, detail.relatedNodes.length)}</p>
        </div>
        <div className="human-node-section">
          <strong>建议怎么用</strong>
          <ul>
            <li>把这个时间段和相邻周期对比，判断是一次性高峰、持续投入，还是记忆整理遗漏。</li>
            <li>优先点开下方相关记忆，查看具体话题、决策和需要继续做的事情。</li>
          </ul>
        </div>
      </section>
      <dl className="human-node-status">
        <div><dt>活动得分</dt><dd>{bucket.activityScore.toLocaleString()}</dd></div>
        <div><dt>环比变化</dt><dd>{formatSigned(bucket.delta ?? 0)} / {bucket.previousLabel ?? "上一周期"}</dd></div>
        <div><dt>全局消息</dt><dd>{bucket.messageCount.toLocaleString()}</dd></div>
        <div><dt>工具调用</dt><dd>{(bucket.toolCallCount ?? 0).toLocaleString()}</dd></div>
        <div><dt>筛选记忆</dt><dd>{bucket.filteredMemoryCount.toLocaleString()}</dd></div>
        <div><dt>核心画像</dt><dd>{bucket.filteredCoreCount.toLocaleString()}</dd></div>
        <div><dt>决策</dt><dd>{bucket.filteredDecisionCount.toLocaleString()}</dd></div>
        <div><dt>错误/中断</dt><dd>{(bucket.errorEventCount ?? 0).toLocaleString()} / {(bucket.abortCount ?? 0).toLocaleString()}</dd></div>
      </dl>
      <section className="period-related-list" aria-label="这个时间段对应的记忆">
        <div className="panel-title-row">
          <h3>对应记忆</h3>
          <span>{detail.relatedNodes.length.toLocaleString()} 条</span>
        </div>
        {relatedNodes.length ? (
          relatedNodes.map((node) => (
            <button key={node.id} onClick={() => onSelectNode(node)} type="button">
              <strong>{humanNodeTitle(node)}</strong>
              <span>{humanizeStatement(node.statement) || node.label}</span>
              <small>{normalizeMemoryTier(node.memory_tier)} / {humanCategoryLabel(node.category)} / {node.date || "未知日期"}</small>
            </button>
          ))
        ) : (
          <p>当前筛选下没有具体记忆节点；这个格子主要来自全局交互统计。切换筛选条件或年份后可继续查看。</p>
        )}
      </section>
    </aside>
  );
}

function WritebackProposalPanel({ atlas, node }: { atlas: MemoryAtlas; node: AtlasNode }) {
  const [action, setAction] = useState<WritebackAction>("update_statement");
  const [draftText, setDraftText] = useState(node.statement ?? node.label);
  const [reason, setReason] = useState("");
  const [proposals, setProposals] = useState<WritebackProposal[]>(() => loadWritebackProposals());

  const policy = atlas.source_contract.writeback_policy;
  const editable = policy.frontend_can_request_writeback && policy.writeback_must_use_proposals && !policy.direct_frontend_mutation_of_active_memory;
  const nodeProposals = useMemo(
    () => proposals.filter((proposal) => proposal.target_ref.node_id === node.id),
    [node.id, proposals],
  );
  const latest = nodeProposals[nodeProposals.length - 1] ?? null;
  const previous = nodeProposals[nodeProposals.length - 2] ?? null;
  const baseText = node.statement ?? node.label;
  const draftDiff = useMemo(() => buildProposalDiff(baseText, draftText), [baseText, draftText]);
  const versionChain = useMemo(() => [...nodeProposals].reverse().slice(0, 6), [nodeProposals]);
  const proposalPreview = useMemo(
    () => buildWritebackProposalDraft({
      policy,
      node,
      action,
      proposedText: draftText,
      reason,
      baseText,
      latest,
      proposalCount: nodeProposals.length,
      now: new Date().toISOString(),
      proposalIdPrefix: "atlas_preview",
    }),
    [action, baseText, draftText, latest, node, nodeProposals.length, policy, reason],
  );
  const proposalJsonPreview = useMemo(() => JSON.stringify(proposalPreview, null, 2), [proposalPreview]);

  useEffect(() => {
    setDraftText(node.statement ?? node.label);
    setReason("");
    setAction("update_statement");
  }, [node.id, node.label, node.statement]);

  function persist(next: WritebackProposal[]) {
    setProposals(next);
    saveWritebackProposals(next);
  }

  function saveProposal() {
    const text = draftText.trim();
    if (!editable || !text) return;
    const now = new Date().toISOString();
    const proposal = buildWritebackProposalDraft({
      policy,
      node,
      action,
      proposedText: text,
      reason,
      baseText,
      latest,
      proposalCount: nodeProposals.length,
      now,
      proposalIdPrefix: "atlas",
    });
    persist([...proposals, proposal]);
  }

  function createRollbackProposal() {
    if (!editable || !latest) return;
    const target = previous ?? latest;
    const now = new Date().toISOString();
    const rollbackText = target.payload.proposed_text || baseText;
    const rollbackReason = `回滚到版本 ${target.version.revision}：${target.proposal_id}`;
    const proposal: WritebackProposal = {
      schema_version: policy.proposal_schema_version || "memory_change_proposal.v1",
      proposal_id: `atlas_${compactTimestamp(now)}_${stableHash(`${node.id}:rollback:${latest.proposal_id}:${nodeProposals.length + 1}`)}`,
      created_at: now,
      status: "draft_pending_agent_apply",
      target_ref: {
        node_id: node.id,
        memory_id: node.memory_id ?? node.id,
        label: node.label,
        source_file: node.source_label ?? node.data_source ?? "visual_snapshot",
        base_date: node.date ?? "",
      },
      action: "rollback_to_version",
      payload: {
        proposed_text: rollbackText,
        reason: rollbackReason,
        current_tier: normalizeMemoryTier(node.memory_tier),
        current_category: node.category ?? "",
      },
      diff: buildProposalDiff(latest.payload.proposed_text || baseText, rollbackText),
      version: {
        revision: (latest.version.revision ?? 0) + 1,
        parent_proposal_id: latest.proposal_id,
        rollback_unit: policy.rollback_unit || "per_memory_version",
        supersedes_proposal_id: latest.proposal_id,
      },
      rollback: {
        rollback_to_proposal_id: target.proposal_id,
        rollback_to_revision: target.version.revision,
        rollback_text: rollbackText,
        rollback_reason: rollbackReason,
      },
      review: {
        human_summary: `建议把当前写回提案回滚到版本 ${target.version.revision}。`,
        agent_next_step: "重新读取当前主动记忆库，核对冲突与敏感字段后，写入提案历史，并用 git commit 建立回滚点。",
        conflict_policy: "若当前库已存在更新版本，先生成冲突报告，不可直接覆盖。",
        apply_status: "proposal_only_pending_agent_apply",
      },
      safety: {
        direct_frontend_mutation_of_active_memory: false,
        requires_conflict_check: true,
        requires_agent_or_human_apply: true,
        forbidden_payload: policy.frontend_payload_contract?.forbidden_payload ?? [
          "plaintext secrets",
          "raw conversation text",
          "record hashes",
          "local absolute paths",
        ],
      },
    };
    persist([...proposals, proposal]);
  }

  function rollbackDraft() {
    if (!previous) return;
    setAction(previous.action);
    setDraftText(previous.payload.proposed_text);
    setReason(`回滚到 ${previous.proposal_id}`);
  }

  function exportLatest() {
    if (!latest) return;
    downloadJson(`${latest.proposal_id}.json`, latest);
  }

  function exportProposalHistory() {
    if (!nodeProposals.length) return;
    downloadJson(`memory_atlas_writeback_history_${node.id}.json`, {
      schema_version: "memory_atlas_writeback_history.v1",
      exported_at: new Date().toISOString(),
      target_ref: {
        node_id: node.id,
        memory_id: node.memory_id ?? node.id,
        label: node.label,
      },
      proposals: nodeProposals,
    });
  }

  return (
    <section
      className="writeback-panel"
      aria-label="长期记忆写回提案"
      data-proposal-only="true"
      data-active-memory-mutation="false"
      data-proposal-schema={policy.proposal_schema_version || "memory_change_proposal.v1"}
    >
      <div className="panel-title-row">
        <h3>{uiCopy.proposal.panelTitle}</h3>
        <span>{nodeProposals.length} {uiCopy.proposal.versionSuffix}</span>
      </div>
      <p>{uiCopy.proposal.description}</p>
      <div className="writeback-safety-strip" aria-label="proposal-only safety contract">
        <span>{uiCopy.proposal.safetyProposalOnly}</span>
        <span>{uiCopy.proposal.safetyNoDirectMutation}</span>
        <span>{uiCopy.proposal.safetyNeedsApply}</span>
      </div>
      <ProposalEditor
        node={node}
        parentSnapshotId={atlas.overview.generated_at || atlas.schema_version}
        sourceSurface="inspector_writeback_panel"
      />
      {!editable ? (
        <ErrorState
          compact
          className="proposal-unavailable-state"
          dataState="proposal-not-writable"
          description={uiCopy.states.proposalUnavailableDescription}
          details={uiCopy.states.proposalUnavailableAction}
          title={uiCopy.states.proposalUnavailableTitle}
        />
      ) : null}
      <div className="writeback-diff-grid" aria-label="当前草稿差异">
        <div><span>{uiCopy.proposal.diffLength}</span><strong>{draftDiff.length_delta > 0 ? "+" : ""}{draftDiff.length_delta}</strong></div>
        <div><span>{uiCopy.proposal.diffSegments}</span><strong>{draftDiff.changed_segments}</strong></div>
        <div><span>{uiCopy.proposal.rollbackUnit}</span><strong>{policy.rollback_unit || "per_memory_version"}</strong></div>
      </div>
      <label>
        {uiCopy.proposal.actionLabel}
        <select value={action} onChange={(event) => setAction(event.target.value as WritebackAction)} disabled={!editable}>
          {(Object.keys(writebackActionLabels) as WritebackAction[]).map((key) => (
            <option key={key} value={key}>{writebackActionLabels[key]}</option>
          ))}
        </select>
      </label>
      <label>
        {uiCopy.proposal.draftLabel}
        <textarea
          value={draftText}
          onChange={(event) => setDraftText(event.target.value)}
          disabled={!editable}
          rows={5}
        />
      </label>
      <label>
        {uiCopy.proposal.reasonLabel}
        <textarea
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          disabled={!editable}
          rows={3}
          placeholder={uiCopy.proposal.reasonPlaceholder}
        />
      </label>
      <div className="writeback-actions">
        <button type="button" onClick={saveProposal} disabled={!editable || !draftText.trim()}>
          <Save size={15} />
          {uiCopy.proposal.buttons.save}
        </button>
        <button type="button" onClick={exportLatest} disabled={!latest}>
          <Download size={15} />
          {uiCopy.proposal.buttons.exportLatest}
        </button>
        <button type="button" onClick={exportProposalHistory} disabled={!nodeProposals.length}>
          <GitBranch size={15} />
          {uiCopy.proposal.buttons.exportHistory}
        </button>
        <button type="button" onClick={rollbackDraft} disabled={!previous}>
          <RotateCcw size={15} />
          {uiCopy.proposal.buttons.loadPrevious}
        </button>
        <button type="button" onClick={createRollbackProposal} disabled={!latest}>
          <RotateCcw size={15} />
          {uiCopy.proposal.buttons.createRollback}
        </button>
      </div>
      <details className="writeback-json-preview">
        <summary>
          <GitBranch size={14} />
          {uiCopy.proposal.buttons.jsonPreview}
        </summary>
        <pre>{proposalJsonPreview}</pre>
      </details>
      {versionChain.length ? (
        <div className="writeback-version-chain" aria-label="写回提案版本链">
          {versionChain.map((proposal) => (
            <button key={proposal.proposal_id} onClick={() => {
              setAction(proposal.action);
              setDraftText(proposal.payload.proposed_text);
              setReason(proposal.payload.reason);
            }} type="button">
              <strong>v{proposal.version.revision} · {writebackActionLabels[proposal.action]}</strong>
              <span>{proposal.diff?.summary ?? "旧版本无差异摘要"} · {new Date(proposal.created_at).toLocaleString("zh-CN")}</span>
              <small>{proposal.version.parent_proposal_id ? `parent ${proposal.version.parent_proposal_id}` : "root proposal"}</small>
            </button>
          ))}
        </div>
      ) : null}
      <small>
        {latest
          ? `${uiCopy.proposal.latestVersionPrefix} ${latest.version.revision} · ${new Date(latest.created_at).toLocaleString("zh-CN")} · 待受控代理应用`
          : uiCopy.proposal.emptyVersion}
      </small>
    </section>
  );
}

function DeltaStrip({ stats, compact = false }: { stats: DeltaStats; compact?: boolean }) {
  return (
    <div className={compact ? "delta-strip compact" : "delta-strip"}>
      <div>
        <span>当前切片</span>
        <strong>{stats.totalFiltered.toLocaleString()}</strong>
      </div>
      <div>
        <span>近 30 天</span>
        <strong>{stats.recentCount.toLocaleString()}</strong>
      </div>
      <div>
        <span>较前 30 天</span>
        <strong className={stats.deltaCount >= 0 ? "positive" : "negative"}>{formatSigned(stats.deltaCount)}</strong>
      </div>
      <div>
        <span>新增决策/核心</span>
        <strong>{stats.recentDecisionCount}/{stats.recentCoreCount}</strong>
      </div>
      <div>
        <span>热点分类</span>
        <strong>{stats.topCategory}</strong>
      </div>
    </div>
  );
}

function HumanOverviewPanel({
  nodes,
  deltaStats,
  compact = false,
}: {
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  compact?: boolean;
}) {
  const overview = useMemo(() => buildHumanOverview(nodes, deltaStats), [nodes, deltaStats]);
  return (
    <section className={compact ? "human-overview compact" : "human-overview"} aria-label="人类可读记忆摘要">
      <div className="panel-title-row">
        <h3>目前记录了什么</h3>
        <span>{nodes.length.toLocaleString()} 条</span>
      </div>
      <div className="human-overview-grid">
        <div>
          <strong>主要话题</strong>
          <HumanPillList rows={overview.topicRows} />
        </div>
        <div>
          <strong>记忆层级</strong>
          <HumanPillList rows={overview.tierRows} />
        </div>
      </div>
      <div className="human-lists">
        <HumanBulletList title="需要做什么" items={overview.actionItems} />
        <HumanBulletList title="记得做什么" items={overview.rememberItems} />
        <HumanBulletList title="机会/增长方向" items={overview.opportunityItems} />
        <HumanBulletList title="需要留意" items={overview.riskItems} />
      </div>
    </section>
  );
}

function HumanPillList({ rows }: { rows: Array<{ label: string; count: number }> }) {
  return (
    <div className="human-pill-list">
      {rows.slice(0, 5).map((row) => (
        <span key={row.label}>
          {row.label}
          <b>{row.count}</b>
        </span>
      ))}
    </div>
  );
}

function HumanBulletList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="human-bullet-list">
      <strong>{title}</strong>
      <ul>
        {items.map((item, index) => (
          <li key={`${title}-${index}-${item}`}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function GraphSvgNode({
  item,
  selected,
  onSelectNode,
}: {
  item: LayoutNode;
  selected: boolean;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const radius = selected ? item.r + 5 : item.r;
  const isParent = isGraphParentNode(item.node);
  return (
    <g
      className={`${selected ? "graph-node selected" : "graph-node"}${isParent ? " parent-node" : ""}`}
      aria-label={`${translateKind(item.node.kind)} · ${item.node.label}`}
      role="button"
      tabIndex={0}
      onClick={() => onSelectNode(item.node)}
      onKeyDown={(event) => {
        if (isActivationKey(event)) onSelectNode(item.node);
      }}
    >
      <title>{`${translateKind(item.node.kind)} · ${item.node.label}`}</title>
      <circle className="graph-node-halo" cx={item.x} cy={item.y} r={radius + (isParent ? 8 : 5)} fill={item.color} opacity={isParent ? 0.1 : 0.045} />
      <circle className="graph-node-core" cx={item.x} cy={item.y} r={radius} fill={item.color} filter="url(#softGlow)" />
    </g>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value.toLocaleString()}</strong>
    </div>
  );
}

function SelectFilter({
  label,
  value,
  options,
  formatOption = (option) => option,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  formatOption?: (option: string) => string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="select-filter">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="all">{uiCopy.filters.allOption}</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {formatOption(option)}
          </option>
        ))}
      </select>
    </label>
  );
}

function InsightCard({ title, value, note }: { title: string; value: number; note: string }) {
  return (
    <article className="insight-card">
      <span>{title}</span>
      <strong>{value.toLocaleString()}</strong>
      <p>{note}</p>
    </article>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span>
      <i style={{ background: color }} />
      {label}
    </span>
  );
}

function GraphUsageStrip({ items }: { items: Array<{ label: string; value: string }> }) {
  return (
    <div className="graph-usage-strip" aria-label="图谱读法">
      {items.map((item) => (
        <span key={`${item.label}-${item.value}`}>
          <b>{item.label}</b>
          <em>{item.value}</em>
        </span>
      ))}
    </div>
  );
}

function DataGuideSvgNode({
  item,
  selected,
  onSelectNode,
}: {
  item: DataGuideNode;
  selected: boolean;
  onSelectNode: (node: AtlasNode) => void;
}) {
  return (
    <g
      className={selected ? "data-guide-node selected" : "data-guide-node"}
      aria-label={`${item.frameTitle} · ${item.typeLabel} · ${item.node.label}`}
      role="button"
      tabIndex={0}
      data-data-map-node-detail-entry={DATA_MAP_DETAIL_PANEL_VERSION}
      data-node-id={item.node.id}
      data-node-kind={item.node.kind}
      data-node-importance={item.node.importance ?? ""}
      data-node-priority={dataMapPriorityForNode(item.node)}
      onClick={() => onSelectNode(item.node)}
      onKeyDown={(event) => {
        if (isActivationKey(event)) onSelectNode(item.node);
      }}
    >
      <title>{`${item.frameTitle} · ${item.typeLabel} · ${item.node.label}`}</title>
      <rect className="data-guide-node-card" x={item.x} y={item.y} width={item.w} height={item.h} rx="8" fill={item.color} />
      <rect className="data-guide-node-border" x={item.x} y={item.y} width={item.w} height={item.h} rx="8" fill="none" stroke={item.color} />
      <text x={item.x + 9} y={item.y + 15} className="data-guide-node-type">{item.typeLabel}</text>
      <text x={item.x + 9} y={item.y + 32} className="data-guide-node-title">{item.title}</text>
      <text x={item.x + 9} y={item.y + 48} className="data-guide-node-meta">{item.meta}</text>
      <circle cx={item.x + item.w - 12} cy={item.y + 13} r={Math.max(3, item.signalRadius)} fill={item.color} filter="url(#dataGuideGlow)" />
    </g>
  );
}

interface LayoutNode {
  node: AtlasNode;
  x: number;
  y: number;
  r: number;
  color: string;
  label: string;
  degree: number;
}

interface LayoutEdge {
  id: string;
  source: LayoutNode;
  target: LayoutNode;
  weight: number;
  color: string;
}

interface LayoutGroup {
  id: string;
  label: string;
  x: number;
  y: number;
  r: number;
  color: string;
}

type DataGuideFrameId = "source" | "profile" | "project" | "action";
type DataMapStructureLayerId = "source_layer" | "profile_layer" | "project_decision_layer" | "action_opportunity_layer";

const DATA_MAP_STRUCTURE_LAYERS: Array<{
  id: DataMapStructureLayerId;
  frameId: DataGuideFrameId;
  label: string;
  title: string;
  subtitle: string;
  nodeTypes: string[];
  fields: string[];
  interaction: string;
  detailEntry: string;
  defaultCollapsed: true;
}> = [
  {
    id: "source_layer",
    frameId: "source",
    label: "来源层",
    title: "来源层",
    subtitle: "来源 / 主题簇 / 分类索引",
    nodeTypes: ["theme", "tier", "category"],
    fields: ["data_source", "source_label", "category", "date"],
    interaction: "select_source_or_topic_node",
    detailEntry: "open_source_or_topic_detail",
    defaultCollapsed: true,
  },
  {
    id: "profile_layer",
    frameId: "profile",
    label: "画像层",
    title: "画像层",
    subtitle: "核心画像 / taste / 规则",
    nodeTypes: ["memory:preference", "memory:answering_rule", "memory:security_boundary"],
    fields: ["memory_tier", "category", "importance", "confidence"],
    interaction: "select_profile_node",
    detailEntry: "open_profile_detail",
    defaultCollapsed: true,
  },
  {
    id: "project_decision_layer",
    frameId: "project",
    label: "项目决策层",
    title: "项目决策层",
    subtitle: "项目背景 / 决策 / 工作流",
    nodeTypes: ["project", "decision", "memory:project_context", "memory:workflow"],
    fields: ["project", "decision", "validity", "importance"],
    interaction: "select_project_decision_node",
    detailEntry: "open_project_decision_detail",
    defaultCollapsed: true,
  },
  {
    id: "action_opportunity_layer",
    frameId: "action",
    label: "行动机会层",
    title: "行动机会层",
    subtitle: "行动 / 机会 / 待整理",
    nodeTypes: ["memory:temporary", "memory:recommended_action", "memory:roi_opportunity"],
    fields: ["recommended_action", "leverage_score", "staleness_status", "date"],
    interaction: "select_action_opportunity_node",
    detailEntry: "open_action_opportunity_detail",
    defaultCollapsed: true,
  },
];

interface DataGuideFrame {
  id: DataGuideFrameId;
  structureLayerId: DataMapStructureLayerId;
  title: string;
  subtitle: string;
  nodeTypes: string[];
  fields: string[];
  interaction: string;
  detailEntry: string;
  x: number;
  y: number;
  w: number;
  h: number;
  color: string;
  count: number;
}

interface DataGuideNode {
  node: AtlasNode;
  frameId: DataGuideFrameId;
  frameTitle: string;
  x: number;
  y: number;
  w: number;
  h: number;
  color: string;
  title: string;
  typeLabel: string;
  meta: string;
  signalRadius: number;
  score: number;
}

interface DataGuideEdge {
  id: string;
  source: DataGuideNode;
  target: DataGuideNode;
  path: string;
  color: string;
  strokeWidth: number;
  explanation: DataGuideRelationExplanation;
}

interface DataGuideRelationExplanation {
  source: string;
  sourceLabel: string;
  targetLabel: string;
  strength: string;
  evidence: string;
  time: string;
  reason: string;
}

interface DataMapNodeDetail {
  asset: string;
  theme: string;
  suggestedAction: string;
  importance: string;
  priority: string;
  status: string;
  layerLabel: string;
  summary: string;
  evidenceRefs: string[];
}

function buildFilteredSlice(atlas: MemoryAtlas, filteredMemoryNodes: AtlasNode[], filters: AtlasFilters): FilteredAtlasSlice {
  const visibleGraph = visibleGraphFor(atlas, filteredMemoryNodes);
  const visibleNodeIds = new Set(visibleGraph.nodes.map((node) => node.id));
  const memoryIds = new Set(filteredMemoryNodes.map((node) => node.memory_id).filter(Boolean));
  const timeline = atlas.timeline.filter((event) => visibleNodeIds.has(event.node_id) || memoryIds.has(event.memory_id));
  return {
    memoryNodes: filteredMemoryNodes,
    graphNodes: visibleGraph.nodes,
    graphEdges: visibleGraph.edges,
    timeline,
    visibleNodeIds,
    deltaStats: buildDeltaStats(atlas, filteredMemoryNodes),
    filterActive:
      filters.query !== "" || filters.source !== "all" || filters.tier !== "all" || filters.category !== "all" || filters.theme !== "all",
  };
}

function selectionStillVisible(node: AtlasNode, slice: FilteredAtlasSlice): boolean {
  if (!slice.visibleNodeIds.has(node.id)) return false;
  if (!slice.filterActive) return true;
  if (node.kind === "memory") {
    return slice.memoryNodes.some((memoryNode) => memoryNode.id === node.id);
  }
  return true;
}

function buildSourceOptions(atlas: MemoryAtlas, memoryNodes: AtlasNode[]): SourceOption[] {
  if (atlas.data_sources?.length) {
    return atlas.data_sources
      .filter((source) => ["all", "memory_atlas", "codex"].includes(source.id))
      .map((source) => ({
        id: source.id,
        label: sourceDisplayLabel(source.id, source.label),
        description: source.description,
        node_count: source.node_count,
      }));
  }
  const counts = memoryNodes.reduce<Record<string, number>>((acc, node) => {
    const id = node.data_source ?? "memory_atlas";
    acc[id] = (acc[id] ?? 0) + 1;
    return acc;
  }, {});
  return [
    { id: "all", label: "总数据源", description: "所有数据来源放在一起", node_count: memoryNodes.length },
    ...Object.entries(counts)
      .filter(([id]) => ["memory_atlas", "codex"].includes(id))
      .map(([id, count]) => ({
        id,
        label: sourceDisplayLabel(id, id),
        description: "自动识别的数据源",
        node_count: count,
      })),
  ];
}

function sourceDisplayLabel(sourceId: string, fallback: string): string {
  if (sourceId === "all") return "总数据源";
  if (sourceId === "memory_atlas") return "ChatGPT";
  if (sourceId === "codex") return "Codex";
  return fallback;
}

function sourceMatchesNode(node: AtlasNode, sourceId: string): boolean {
  return sourceId === "all" || (node.data_source ?? "memory_atlas") === sourceId;
}

function buildSourceScopedAtlas(atlas: MemoryAtlas, sourceMemoryNodes: AtlasNode[], sourceId: string): MemoryAtlas {
  if (sourceId === "all") return atlas;
  const graph = visibleGraphFor(atlas, sourceMemoryNodes);
  const visibleNodeIds = new Set(graph.nodes.map((node) => node.id));
  const memoryIds = new Set(sourceMemoryNodes.map((node) => node.memory_id).filter(Boolean));
  const timeline = atlas.timeline.filter((event) => visibleNodeIds.has(event.node_id) || memoryIds.has(event.memory_id));
  const sourceSummary = atlas.data_sources?.find((source) => source.id === sourceId);
  const contribution = buildSourceScopedContribution(atlas, sourceMemoryNodes, sourceId);
  return {
    ...atlas,
    overview: {
      ...atlas.overview,
      active_memory_count: sourceMemoryNodes.length,
      memory_node_count: sourceMemoryNodes.length,
      node_count: graph.nodes.length,
      edge_count: graph.edges.length,
      conversation_count: sourceSummary?.activity_count ?? contribution.daily.length,
    },
    nodes: graph.nodes,
    edges: graph.edges,
    timeline,
    contribution,
    metrics: buildSourceScopedMetrics(sourceMemoryNodes),
    agent_recommendations: sourceId === "codex" ? atlas.agent_recommendations : undefined,
  };
}

function buildSourceScopedContribution(atlas: MemoryAtlas, sourceMemoryNodes: AtlasNode[], sourceId: string): MemoryAtlas["contribution"] {
  const nodeDaily = aggregateFilteredNodes(sourceMemoryNodes, "day");
  const dailyByDate = new Map<string, ActivityBucket>();

  if (sourceId === "codex") {
    for (const row of atlas.contribution.daily) {
      if ((row.codex_session_count ?? 0) <= 0 && (row.tool_call_count ?? 0) <= 0) continue;
      dailyByDate.set(row.date, normalizeActivityBucket(row));
    }
  }

  for (const [dateKey, nodeBucket] of nodeDaily) {
    const target = dailyByDate.get(dateKey) ?? blankBucket(dateKey);
    target.memory_count = nodeBucket.memory_count;
    target.decision_count = nodeBucket.decision_count;
    target.core_memory_count = nodeBucket.core_memory_count;
    target.mid_long_memory_count = nodeBucket.mid_long_memory_count;
    target.short_memory_count = nodeBucket.short_memory_count;
    target.activity_score = Math.max(target.activity_score, nodeBucket.activity_score);
    target.activity_level = levelFromScore(target.activity_score);
    dailyByDate.set(dateKey, target);
  }

  const daily = Array.from(dailyByDate.values()).sort((a, b) => a.date.localeCompare(b.date));
  const maxActivity = Math.max(0, ...daily.map((row) => row.activity_score));
  return {
    ...atlas.contribution,
    range_start: daily[0]?.date ?? "",
    range_end: daily[daily.length - 1]?.date ?? "",
    max_activity_score: maxActivity,
    quantiles: {},
    daily,
    weekly: aggregateActivityBuckets(daily, "week"),
    monthly: aggregateActivityBuckets(daily, "month"),
    yearly: aggregateActivityBuckets(daily, "year"),
  };
}

function normalizeActivityBucket(row: ActivityBucket): ActivityBucket {
  return {
    ...blankBucket(row.date),
    ...row,
    tool_call_count: row.tool_call_count ?? 0,
    error_event_count: row.error_event_count ?? 0,
    abort_count: row.abort_count ?? 0,
    codex_session_count: row.codex_session_count ?? 0,
  };
}

function aggregateActivityBuckets(rows: ActivityBucket[], period: "week" | "month" | "year"): ActivityBucket[] {
  const buckets = new Map<string, ActivityBucket>();
  for (const row of rows) {
    const periodKey = activityPeriodKey(row.date, period);
    if (!periodKey) continue;
    const target = buckets.get(periodKey) ?? blankBucket(periodKey);
    for (const key of activityBucketNumericKeys) {
      target[key] = (target[key] ?? 0) + (row[key] ?? 0);
    }
    target.activity_level = levelFromScore(target.activity_score);
    buckets.set(periodKey, target);
  }
  return Array.from(buckets.values()).sort((a, b) => a.date.localeCompare(b.date));
}

function activityPeriodKey(dateKey: string, period: "week" | "month" | "year"): string {
  const day = parseDay(dateKey);
  if (!day) return "";
  if (period === "month") return `${day.getUTCFullYear()}-${String(day.getUTCMonth() + 1).padStart(2, "0")}`;
  if (period === "year") return String(day.getUTCFullYear());
  const startWeekday = mondayWeekdayIndex(new Date(Date.UTC(day.getUTCFullYear(), 0, 1)));
  return calendarWeekKey(day.getUTCFullYear(), Math.floor((dayOfYearIndex(day) + startWeekday) / 7));
}

const activityBucketNumericKeys = [
  "conversation_count",
  "message_count",
  "user_message_count",
  "assistant_message_count",
  "memory_count",
  "candidate_count",
  "decision_count",
  "core_memory_count",
  "mid_long_memory_count",
  "short_memory_count",
  "tool_call_count",
  "error_event_count",
  "abort_count",
  "codex_session_count",
  "activity_score",
] as const;

function buildSourceScopedMetrics(nodes: AtlasNode[]): AtlasMetric[] {
  return [
    { kind: "tier", values: filteredMetricValues(nodes, "memory_tier") },
    { kind: "category", values: filteredMetricValues(nodes, "category") },
  ];
}

function buildDeltaStats(atlas: MemoryAtlas, nodes: AtlasNode[]): DeltaStats {
  const latest = parseDay(atlas.contribution.range_end) ?? maxNodeDate(nodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const previousStart = addDays(latest, -59);
  const previousEnd = addDays(latest, -30);
  const recentNodes = nodes.filter((node) => isNodeBetween(node, recentStart, latest));
  const previousNodes = nodes.filter((node) => isNodeBetween(node, previousStart, previousEnd));
  const categoryCounts = filteredMetricValues(nodes, "category");
  const topCategory = topEntry(categoryCounts)?.[0] ?? "暂无";
  const deltaCount = recentNodes.length - previousNodes.length;
  return {
    totalFiltered: nodes.length,
    totalMemory: atlas.overview.active_memory_count,
    recentCount: recentNodes.length,
    previousCount: previousNodes.length,
    deltaCount,
    deltaRate: previousNodes.length ? deltaCount / previousNodes.length : null,
    recentDecisionCount: recentNodes.filter((node) => node.category === "decision").length,
    recentCoreCount: recentNodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length,
    topCategory,
    latestDate: toDayKey(latest),
  };
}

function buildHumanOverview(nodes: AtlasNode[], deltaStats: DeltaStats): HumanOverview {
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const topicRows = topRows(countBy(memoryNodes, (node) => humanThemeLabel(node)), 6);
  const tierRows = topRows(countBy(memoryNodes, (node) => normalizeMemoryTier(node.memory_tier)), 4);
  const categoryRows = topRows(countBy(memoryNodes, (node) => humanCategoryLabel(node.category)), 6);
  const topTopic = topicRows[0]?.label ?? "当前筛选主题";
  const highLeverage = [...memoryNodes]
    .sort((a, b) => (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0))
    .slice(0, 4);
  const staleShortCount = memoryNodes.filter(
    (node) => normalizeMemoryTier(node.memory_tier) === "临时" || node.metrics?.roi?.staleness_status === "stale_short_term",
  ).length;
  const coreCount = memoryNodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length;
  const decisionCount = memoryNodes.filter((node) => node.category === "decision").length;
  const securityCount = memoryNodes.filter((node) => node.category === "security_boundary").length;

  const rememberItems = highLeverage.length
    ? dedupeDisplayItems(highLeverage.map((node) => `${humanNodeDisplayTitle(node)}：${recommendedActionForNode(node)}`), 4)
    : ["暂无高杠杆记忆；先选择主题或层级后查看更具体的事项。"];

  return {
    topicRows,
    tierRows,
    categoryRows,
    actionItems: [
      `优先复核「${topTopic}」：这是当前记忆密度最高的主题，适合先转成下一步任务清单。`,
      `把 ${coreCount.toLocaleString()} 条核心画像沉淀成可复制的 personalization / agent 启动上下文。`,
      staleShortCount
        ? `清理但不删除 ${staleShortCount.toLocaleString()} 条临时信息：压缩成低权重背景，避免干扰长期判断。`
        : "当前短期噪音较低，下一步可以集中补齐项目索引和决策日志。",
    ],
    rememberItems,
    opportunityItems: buildOpportunityItems(topicRows, categoryRows, deltaStats),
    riskItems: [
      securityCount
        ? `${securityCount.toLocaleString()} 条安全边界需要持续遵守；涉及交易、secret、外部部署时不能跳过确认。`
        : "当前筛选没有明显安全边界，但外部写入和账户操作仍需人工确认。",
      decisionCount
        ? `${decisionCount.toLocaleString()} 条决策应进入后续默认上下文，避免重复讨论。`
        : "当前筛选决策较少，后续应把重要选择明确写入决策日志。",
      `近 30 天较前 30 天 ${formatSigned(deltaStats.deltaCount)} 条，增量变化需要和实际任务成果一起复盘。`,
    ],
  };
}

function buildClioLikeVisualModel(
  nodes: AtlasNode[],
  filters: AtlasFilters,
  sharedState: SharedAtlasState,
  deltaStats: DeltaStats,
): ClioLikeVisualModel {
  const visualCopy: ClioLikeVisualCopy[] = [
    {
      id: "cluster_tree",
      title: "层级簇树",
      insightHeader: "主导主题先看树干，不从散点开始",
      humanQuestion: "我最近主要在关注哪些主题层级？",
      actionValue: "先定位主题重心，再决定进入搜索、星图还是后续 ROI 图谱。",
    },
    {
      id: "bubble_map",
      title: "气泡分布",
      insightHeader: "大气泡显示高频和高 ROI 的交汇点",
      humanQuestion: "高频、机会、风险如何分布？",
      actionValue: "优先打开高 ROI 且近期活跃的簇，低 ROI 高频簇进入降噪复盘。",
    },
    {
      id: "topic_cluster_explorer",
      title: "主题簇探索",
      insightHeader: "先打开证据最多的簇再行动",
      humanQuestion: "哪个主题簇最值得继续追问？",
      actionValue: "用代表记录进入搜索视图，复核证据后再生成下一步 proposal。",
    },
  ];
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const latest = parseDay(deltaStats.latestDate) ?? maxNodeDate(memoryNodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const clusterMap = new Map<string, AtlasNode[]>();

  for (const node of memoryNodes) {
    const key = node.visual?.cluster || node.category || "unclustered";
    const bucket = clusterMap.get(key) ?? [];
    bucket.push(node);
    clusterMap.set(key, bucket);
  }

  const palette = ["#7ee8d4", "#8fd3ff", "#f6c56f", "#f08fa3", "#b6a2ff", "#93df8f"];
  const clusters = Array.from(clusterMap.entries())
    .map(([id, clusterNodes], index): ClioClusterDatum => {
      const representative = selectRepresentativeNode(clusterNodes);
      const roiScore = average(clusterNodes.map((node) => normalizedNodeRoi(node)));
      const recentCount = clusterNodes.filter((node) => isNodeBetween(node, recentStart, latest)).length;
      const riskCount = clusterNodes.filter((node) => isBlackHoleCandidate(node)).length;
      const dominantCategory = topEntry(countBy(clusterNodes, (node) => humanCategoryLabel(node.category)))?.[0] ?? "未归类任务";
      const sourceCount = new Set(clusterNodes.map((node) => node.data_source ?? "memory_atlas")).size;
      const gridColumn = index % 3;
      const gridRow = Math.floor(index / 3);
      return {
        id,
        label: compactClioClusterLabel(id, representative),
        count: clusterNodes.length,
        recentCount,
        riskCount,
        roiScore,
        evidenceCount: Math.max(1, Math.round(clusterNodes.length + clusterNodes.reduce((total, node) => total + edgeCountHintForNode(node), 0))),
        dominantCategory,
        sourceCount,
        color: palette[index % palette.length],
        x: 94 + gridColumn * 146,
        y: 72 + gridRow * 82,
        radius: clamp(18 + clusterNodes.length * 1.8 + roiScore * 18, 22, 54),
        node: representative,
        nodes: clusterNodes,
      };
    })
    .sort((a, b) => b.count + b.roiScore * 4 - (a.count + a.roiScore * 4))
    .slice(0, 6)
    .map((cluster, index) => ({
      ...cluster,
      x: 94 + (index % 3) * 146,
      y: 72 + Math.floor(index / 3) * 82,
    }));

  const fallbackCluster: ClioClusterDatum = {
    id: "empty",
    label: "暂无筛选簇",
    count: 0,
    recentCount: 0,
    riskCount: 0,
    roiScore: 0,
    evidenceCount: 0,
    dominantCategory: "无",
    sourceCount: 0,
    color: "#8fd3ff",
    x: 220,
    y: 130,
    radius: 24,
    node: null,
    nodes: [],
  };
  const visibleClusters = clusters.length ? clusters : [fallbackCluster];
  const treeBranches = visibleClusters.slice(0, 5).map((cluster, index) => {
    const y = 48 + index * 42;
    return {
      id: cluster.id,
      label: cluster.label,
      count: cluster.count,
      x1: 174,
      y1: 130,
      x2: 228 + (index % 2) * 40,
      y2: y,
      node: cluster.node,
    };
  });

  const activeFilters = {
    source: filters.source === "all" ? "全部来源" : sourceDisplayLabel(filters.source, filters.source),
    time: sharedState.filters.timeRange?.label ?? "全部时间",
    project: filters.theme === "all" ? "全部项目/主题" : filters.theme,
    task: filters.category === "all" ? "全部任务类别" : humanCategoryLabel(filters.category),
  };
  const topCluster = visibleClusters[0];
  const summary = topCluster.count
    ? `当前筛选下，${topCluster.label} 是最大簇，包含 ${topCluster.count.toLocaleString()} 条记忆；图谱已按来源、时间、项目和任务过滤。`
    : "当前筛选下没有可视化簇；请放宽过滤条件后再查看。";

  return {
    schemaVersion: CLIO_LIKE_VISUALS_VERSION,
    activeFilters,
    visualCopy,
    clusters: visibleClusters,
    treeBranches,
    explorerRows: visibleClusters,
    summary,
  };
}

function buildEconomicLikeVisualModel(
  nodes: AtlasNode[],
  filters: AtlasFilters,
  sharedState: SharedAtlasState,
  deltaStats: DeltaStats,
): EconomicLikeVisualModel {
  const visualCopy: EconomicLikeVisualCopy[] = [
    {
      id: "task_treemap",
      title: "任务占比分布",
      insightHeader: "任务面积显示 AI 使用最集中的地方",
      humanQuestion: "我的 AI 使用集中在哪些任务？",
      actionValue: "把最大面积任务先和 ROI 对齐，避免把时间继续投给低回报任务。",
    },
    {
      id: "automation_vs_augmentation",
      title: "自动化与辅助判断",
      insightHeader: "自动化和增强必须分开决策",
      humanQuestion: "哪些任务是 AI 自动化，哪些只是增强？",
      actionValue: "自动化高的任务优先固化流程；增强高的任务保留人工判断和复盘入口。",
    },
    {
      id: "roi_scatter",
      title: "投入回报分布",
      insightHeader: "右上角任务才值得继续加码",
      humanQuestion: "哪些任务最值得继续？",
      actionValue: "优先打开高 ROI 且近期活跃的任务；低 ROI 高频任务进入停止或降噪判断。",
    },
    {
      id: "opportunity_radar",
      title: "机会雷达",
      insightHeader: "机会不只看数量，还要看新鲜度和复用价值",
      humanQuestion: "哪些方向有机会但还需要证据？",
      actionValue: "用雷达缺口选择下一步验证问题，不把机会清单变成压力清单。",
    },
  ];
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const latest = parseDay(deltaStats.latestDate) ?? maxNodeDate(memoryNodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const taskMap = new Map<string, AtlasNode[]>();

  for (const node of memoryNodes) {
    const taskKey = economicTaskKey(node);
    const bucket = taskMap.get(taskKey) ?? [];
    bucket.push(node);
    taskMap.set(taskKey, bucket);
  }

  const palette = ["#7ee8d4", "#f6c56f", "#8fd3ff", "#f08fa3", "#93df8f", "#b6a2ff"];
  const rawRows = Array.from(taskMap.entries())
    .map(([id, taskNodes], index): EconomicTaskDatum => {
      const representative = selectRepresentativeNode(taskNodes);
      const roiScore = average(taskNodes.map((node) => normalizedNodeRoi(node)));
      const automationShare = average(taskNodes.map((node) => nodeAutomationLikelihood(node)));
      const augmentationShare = clamp(1 - automationShare * 0.72, 0.12, 1);
      const recentCount = taskNodes.filter((node) => isNodeBetween(node, recentStart, latest)).length;
      const opportunityScore = average(taskNodes.map((node) => economicOpportunityScore(node, recentStart, latest)));
      const riskScore = average(taskNodes.map((node) => (isBlackHoleCandidate(node) ? 1 : node.metrics?.roi?.staleness_status ? 0.62 : 0.22)));
      const sourceCount = new Set(taskNodes.map((node) => node.data_source ?? "memory_atlas")).size;
      return {
        id,
        label: economicTaskLabel(id, representative),
        count: taskNodes.length,
        roiScore,
        automationShare,
        augmentationShare,
        opportunityScore,
        riskScore,
        recentCount,
        sourceCount,
        color: palette[index % palette.length],
        x: 72 + clamp(recentCount / Math.max(1, taskNodes.length), 0, 1) * 315,
        y: 214 - roiScore * 160,
        radius: clamp(13 + Math.sqrt(taskNodes.length) * 4 + opportunityScore * 10, 18, 46),
        width: 1,
        height: 1,
        node: representative,
        nodes: taskNodes,
      };
    })
    .sort((a, b) => b.count + b.roiScore * 5 + b.opportunityScore * 4 - (a.count + a.roiScore * 5 + a.opportunityScore * 4))
    .slice(0, 6);

  const fallbackRow: EconomicTaskDatum = {
    id: "empty",
    label: "暂无筛选任务",
    count: 0,
    roiScore: 0,
    automationShare: 0,
    augmentationShare: 0,
    opportunityScore: 0,
    riskScore: 0,
    recentCount: 0,
    sourceCount: 0,
    color: "#8fd3ff",
    x: 220,
    y: 132,
    radius: 20,
    width: 1,
    height: 1,
    node: null,
    nodes: [],
  };
  const taskRows = (rawRows.length ? rawRows : [fallbackRow]).map((row, index, rows) => {
    const total = rows.reduce((sum, item) => sum + Math.max(1, item.count), 0);
    const share = Math.max(0.12, Math.max(1, row.count) / Math.max(1, total));
    const column = index % 3;
    const rowIndex = Math.floor(index / 3);
    return {
      ...row,
      width: clamp(118 + share * 250, 118, 250),
      height: clamp(54 + row.roiScore * 44 + share * 68, 64, 136),
      x: 72 + clamp(row.recentCount / Math.max(1, row.count), 0, 1) * 315,
      y: 214 - row.roiScore * 160,
      radius: clamp(row.radius, 18, 46),
      color: row.color || palette[(column + rowIndex) % palette.length],
    };
  });

  const automationAverage = average(taskRows.map((row) => row.automationShare));
  const augmentationAverage = average(taskRows.map((row) => row.augmentationShare));
  const radarAxes: EconomicRadarAxis[] = [
    { id: "roi", label: "ROI", value: average(taskRows.map((row) => row.roiScore)) },
    { id: "automation", label: "自动化", value: automationAverage },
    { id: "augmentation", label: "增强", value: augmentationAverage },
    { id: "opportunity", label: "机会", value: average(taskRows.map((row) => row.opportunityScore)) },
    { id: "freshness", label: "新鲜度", value: average(taskRows.map((row) => clamp(row.recentCount / Math.max(1, row.count), 0, 1))) },
    { id: "risk", label: "风险", value: average(taskRows.map((row) => row.riskScore)) },
  ];

  const activeFilters = {
    source: filters.source === "all" ? "全部来源" : sourceDisplayLabel(filters.source, filters.source),
    time: sharedState.filters.timeRange?.label ?? "全部时间",
    project: filters.theme === "all" ? "全部项目/主题" : filters.theme,
    task: filters.category === "all" ? "全部任务类别" : humanCategoryLabel(filters.category),
  };
  const topTask = taskRows[0];
  const summary = topTask.count
    ? `当前筛选下，${topTask.label} 是最大的投入任务面，平均 ROI ${formatScore(topTask.roiScore)}；图谱已按来源、时间、项目和任务过滤。`
    : "当前筛选下没有可计算的经济任务；请放宽过滤条件后再查看。";

  return {
    schemaVersion: ECONOMIC_LIKE_VISUALS_VERSION,
    activeFilters,
    visualCopy,
    taskRows,
    scatterPoints: taskRows,
    radarAxes,
    automationAverage,
    augmentationAverage,
    summary,
  };
}

function average(values: number[]): number {
  const valid = values.filter((value) => Number.isFinite(value));
  if (!valid.length) return 0;
  return valid.reduce((total, value) => total + value, 0) / valid.length;
}

function normalizedNodeRoi(node: AtlasNode): number {
  const leverage = node.metrics?.roi?.leverage_score;
  if (typeof leverage === "number") return clamp(leverage > 1 ? leverage / 100 : leverage, 0, 1);
  const weight = node.metrics?.weight_score;
  if (typeof weight === "number") return clamp(weight > 1 ? weight / 100 : weight, 0, 1);
  return 0.35;
}

function edgeCountHintForNode(node: AtlasNode): number {
  const visualSize = node.visual?.size;
  if (typeof visualSize === "number") return Math.max(1, Math.round(visualSize));
  return node.memory_id ? 1 : 0;
}

function compactClioClusterLabel(clusterId: string, representative: AtlasNode | null): string {
  const themeLabel = representative ? compactThemeLabel(humanThemeLabel(representative)) : "";
  if (themeLabel && themeLabel !== "未归类主题") return themeLabel;
  return clusterId
    .replace(/^cluster[-_:]/, "")
    .replace(/^theme[-_:]/, "")
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .slice(0, 22) || "未归类主题";
}

function economicTaskKey(node: AtlasNode): string {
  if (node.category) return node.category;
  const label = `${node.label} ${node.statement ?? ""}`.toLowerCase();
  if (/sync|同步|archive|归档|backup|备份|automation|自动化|script|脚本/.test(label)) return "workflow_automation";
  if (/review|复盘|审核|验证|validator|gate|门禁/.test(label)) return "review_validation";
  if (/proposal|决策|decision|roadmap|计划|stage|phase/.test(label)) return "decision_planning";
  if (/visual|ui|图谱|可视化|dashboard/.test(label)) return "visualization";
  return "knowledge_work";
}

function economicTaskLabel(taskId: string, representative: AtlasNode | null): string {
  const categoryLabel = humanCategoryLabel(taskId);
  if (categoryLabel && categoryLabel !== taskId) return categoryLabel;
  if (representative) return compactThemeLabel(humanThemeLabel(representative));
  return taskId.replace(/[-_]+/g, " ").replace(/\b\w/g, (char) => char.toUpperCase()).slice(0, 24) || "未归类任务";
}

function nodeAutomationLikelihood(node: AtlasNode): number {
  const text = `${node.label} ${node.statement ?? ""} ${node.category ?? ""} ${node.metrics?.roi?.recommended_action ?? ""}`.toLowerCase();
  if (/自动化|automation|script|cron|scheduled|cli|validator|sync|同步|backup|备份|archive|归档|apply|pipeline/.test(text)) return 0.82;
  if (/codex|agent|tool|run|build|test|audit|门禁|验收/.test(text)) return 0.62;
  if (/review|复盘|判断|decision|决策|proposal|研究|写作|planning|计划/.test(text)) return 0.34;
  return 0.48;
}

function economicOpportunityScore(node: AtlasNode, recentStart: Date, latest: Date): number {
  const roi = normalizedNodeRoi(node);
  const recentBoost = isNodeBetween(node, recentStart, latest) ? 0.18 : 0;
  const opportunityText = /机会|opportunity|继续|next|下一步|增长|复用|capability|能力/i.test(`${node.label} ${node.statement ?? ""} ${node.metrics?.roi?.recommended_action ?? ""}`)
    ? 0.18
    : 0;
  return clamp(roi * 0.64 + recentBoost + opportunityText, 0, 1);
}

function buildWorkflowLatentGovernanceVisualModel(
  nodes: AtlasNode[],
  graphEdges: AtlasEdge[],
  filters: AtlasFilters,
  sharedState: SharedAtlasState,
  deltaStats: DeltaStats,
): WorkflowLatentGovernanceVisualModel {
  const visualCopy: WorkflowLatentGovernanceVisualCopy[] = [
    {
      id: "agent_decision_sankey",
      title: "执行决策流",
      insightHeader: "Agent 路径要看入口、验收和回滚是否连起来",
      humanQuestion: "Codex/Agent 执行路径哪里失真？",
      actionValue: "把断点转成下一轮 run contract、validator 或人工授权判断。",
    },
    {
      id: "friction_heatmap",
      title: "返工摩擦热区",
      insightHeader: "返工热区优先处理证据缺口和 scope creep",
      humanQuestion: "我在哪些地方反复浪费时间？",
      actionValue: "把高热区转成停止条件、验收门禁或降噪规则。",
    },
    {
      id: "latent_radar",
      title: "潜在信号雷达",
      insightHeader: "潜在信号必须能被证据验证或降权",
      humanQuestion: "哪些潜在信号正在增强？",
      actionValue: "只继续验证可反驳、有证据 badge、有下一步的问题。",
    },
    {
      id: "evidence_timeline",
      title: "证据时间线",
      insightHeader: "结论要能沿时间线追到证据来源",
      humanQuestion: "这个结论从哪些记录来？",
      actionValue: "打开时间线复核证据新鲜度，避免旧结论继续驱动行动。",
    },
    {
      id: "formula_explorer",
      title: "公式解释",
      insightHeader: "公式权重只解释 proxy，不直接代表真实收益",
      humanQuestion: "这个分数为什么这样算？",
      actionValue: "检查参数、边界和仅提案规则，再决定是否继续进入授权流程。",
    },
  ];
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const latest = parseDay(deltaStats.latestDate) ?? maxNodeDate(memoryNodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const edgeCountByNode = graphEdges.reduce<Map<string, number>>((acc, edge) => {
    acc.set(edge.source, (acc.get(edge.source) ?? 0) + 1);
    acc.set(edge.target, (acc.get(edge.target) ?? 0) + 1);
    return acc;
  }, new Map<string, number>());

  const sankeyDefinitions = [
    {
      id: "human_to_codex",
      sourceLabel: "人类目标",
      targetLabel: "Codex 执行",
      patterns: ["goal", "task", "stage", "phase", "roadmap", "目标", "任务", "计划"],
      color: "#72d9d0",
    },
    {
      id: "codex_to_review",
      sourceLabel: "Codex 执行",
      targetLabel: "验证复审",
      patterns: ["validator", "validate", "test", "build", "audit", "验收", "测试", "复审"],
      color: "#8fd3ff",
    },
    {
      id: "review_to_rework",
      sourceLabel: "验证复审",
      targetLabel: "返工降噪",
      patterns: ["rework", "loop", "scope", "debt", "返工", "循环", "范围", "债"],
      color: "#f08fa3",
    },
    {
      id: "review_to_governance",
      sourceLabel: "验证复审",
      targetLabel: "治理记录",
      patterns: ["governance", "handoff", "record", "evidence", "机器治理", "记录", "证据"],
      color: "#f6c56f",
    },
    {
      id: "governance_to_authorization",
      sourceLabel: "治理记录",
      targetLabel: "授权下一步",
      patterns: ["proposal", "apply", "authorization", "next", "授权", "下一步", "门禁"],
      color: "#b6a2ff",
    },
  ];
  const sankeyLinks = sankeyDefinitions.map((definition, index): WorkflowSankeyLinkDatum => {
    const matching = memoryNodes.filter((node) => nodeTextMatches(node, definition.patterns));
    const value = Math.max(1, matching.length || Math.round(memoryNodes.length / Math.max(5, sankeyDefinitions.length + index)));
    return {
      id: definition.id,
      sourceLabel: definition.sourceLabel,
      targetLabel: definition.targetLabel,
      value,
      width: clamp(6 + Math.sqrt(value) * 4, 8, 30),
      y: 72 + index * 34,
      color: definition.color,
      node: selectRepresentativeNode(matching.length ? matching : memoryNodes),
    };
  });

  const frictionRows = [
    { id: "scope", label: "范围漂移", patterns: ["scope", "范围", "越界", "drift"], action: "先收口 run contract" },
    { id: "evidence", label: "证据缺口", patterns: ["evidence", "missing", "gap", "证据", "核验"], action: "补证据或降权" },
    { id: "rework", label: "返工循环", patterns: ["rework", "loop", "debt", "返工", "循环", "债"], action: "建立停止条件" },
    { id: "auth", label: "授权边界", patterns: ["auth", "apply", "raw", "credential", "授权", "凭证"], action: "保持 proposal-only" },
    { id: "formula", label: "公式维护", patterns: ["formula", "parameter", "weight", "公式", "参数", "权重"], action: "检查参数解释" },
  ];
  const frictionColumns = [
    { id: "planning", label: "规划", patterns: ["plan", "roadmap", "goal", "stage", "phase", "计划", "目标"] },
    { id: "execution", label: "执行", patterns: ["run", "build", "implement", "script", "执行", "开发"] },
    { id: "review", label: "复审", patterns: ["review", "audit", "validate", "test", "复审", "测试", "验收"] },
    { id: "governance", label: "治理", patterns: ["governance", "record", "handoff", "policy", "机器治理", "记录"] },
  ];
  const rawFrictionCells = frictionRows.flatMap((row) =>
    frictionColumns.map((column) => {
      const matching = memoryNodes.filter((node) => nodeTextMatches(node, row.patterns) && nodeTextMatches(node, column.patterns));
      const fallback = matching.length ? matching : memoryNodes.filter((node) => nodeTextMatches(node, row.patterns));
      return {
        id: `${row.id}_${column.id}`,
        rowLabel: row.label,
        columnLabel: column.label,
        count: matching.length,
        intensity: 0,
        action: row.action,
        node: selectRepresentativeNode(fallback.length ? fallback : memoryNodes),
      };
    }),
  );
  const maxFriction = Math.max(1, ...rawFrictionCells.map((cell) => cell.count));
  const frictionCells = rawFrictionCells.map((cell) => ({
    ...cell,
    intensity: clamp(cell.count / maxFriction, 0, 1),
  }));

  const latentAxisDefinitions = [
    { id: "asset_compounding", label: "资产复利", patterns: ["asset", "reuse", "handoff", "github", "恢复", "资产", "复用"] },
    { id: "automation_potential", label: "自动化势能", patterns: ["automation", "script", "validator", "sync", "自动化", "脚本"] },
    { id: "evidence_strength", label: "证据强度", patterns: ["evidence", "manifest", "audit", "证据", "核验"] },
    { id: "collaboration_clarity", label: "协作清晰", patterns: ["codex", "agent", "run contract", "协作", "任务包"] },
    { id: "governance_safety", label: "治理安全", patterns: ["governance", "raw", "credential", "proposal", "治理", "凭证", "授权"] },
  ];
  const latentAxes = latentAxisDefinitions.map((axis): LatentRadarDatum => {
    const matching = memoryNodes.filter((node) => nodeTextMatches(node, axis.patterns));
    const recentShare = matching.length
      ? matching.filter((node) => isNodeBetween(node, recentStart, latest)).length / Math.max(1, matching.length)
      : 0;
    const roi = matching.length ? average(matching.map((node) => normalizedNodeRoi(node))) : average(memoryNodes.map((node) => normalizedNodeRoi(node))) * 0.55;
    const density = matching.length / Math.max(1, Math.min(memoryNodes.length, 24));
    const value = clamp(density * 0.52 + roi * 0.3 + recentShare * 0.18, 0.12, 1);
    return {
      id: axis.id,
      label: axis.label,
      value,
      confidenceLabel: value >= 0.66 ? "高置信" : value >= 0.42 ? "中置信" : "待验证",
      evidenceBadge: value >= 0.66 ? "A" : value >= 0.34 ? "B" : "C",
      node: selectRepresentativeNode(matching.length ? matching : memoryNodes),
    };
  });

  const datedNodes = memoryNodes
    .filter((node) => parseDay(node.date))
    .sort((a, b) => (a.date ?? "").localeCompare(b.date ?? ""))
    .slice(-6);
  const firstDate = parseDay(datedNodes[0]?.date) ?? recentStart;
  const lastDate = parseDay(datedNodes[datedNodes.length - 1]?.date) ?? latest;
  const dateSpan = Math.max(1, lastDate.getTime() - firstDate.getTime());
  const evidenceEvents = (datedNodes.length ? datedNodes : memoryNodes.slice(0, 6)).map((node, index): EvidenceTimelineDatum => {
    const day = parseDay(node.date);
    const x = day ? 8 + ((day.getTime() - firstDate.getTime()) / dateSpan) * 84 : 10 + index * 15;
    const evidenceCount = Math.max(1, edgeCountByNode.get(node.id) ?? edgeCountHintForNode(node));
    return {
      id: node.id,
      label: compactThemeLabel(humanNodeDisplayTitle(node)).slice(0, 28),
      dateLabel: day ? formatChineseDate(day) : "无日期",
      x: clamp(x, 6, 92),
      evidenceCount,
      sourceLabel: sourceDisplayLabel(node.data_source ?? "memory_atlas", node.source_label ?? "memory_atlas"),
      node,
    };
  });

  const formulaNode = selectRepresentativeNode(memoryNodes.filter((node) => nodeTextMatches(node, ["formula", "parameter", "roi", "公式", "参数", "权重"]))) ?? selectRepresentativeNode(memoryNodes);
  const formulaRows: FormulaInspectorDatum[] = [
    {
      id: "time_saved_weight",
      label: "time_saved_weight",
      value: `${Math.round(average(memoryNodes.map((node) => normalizedNodeRoi(node))) * 100)}% proxy`,
      description: "时间节省权重来自内部信息 ROI proxy，不是精确收入预测。",
      sourcePath: "机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json",
      node: formulaNode,
    },
    {
      id: "reuse_value_weight",
      label: "reuse_value_weight",
      value: `${latentAxes.find((axis) => axis.id === "asset_compounding")?.evidenceBadge ?? "B"} badge`,
      description: "复用价值要能被 GitHub 可恢复资产或 handoff 证据支撑。",
      sourcePath: "data/derived/economic_proxy/formula_what_if_preview.json",
      node: formulaNode,
    },
    {
      id: "rework_cost_weight",
      label: "rework_cost_weight",
      value: `${frictionCells.filter((cell) => cell.rowLabel === "返工循环").reduce((sum, cell) => sum + cell.count, 0)} hits`,
      description: "返工成本用于扣减 proxy 分，帮助识别需要降噪的工作流。",
      sourcePath: "data/derived/behavior_intelligence/decision_debt_ledger.json",
      node: formulaNode,
    },
    {
      id: "proposal_required_before_apply",
      label: "proposal_required_before_apply",
      value: "true",
      description: "参数变化只进入 proposal，不直接写 active config 或 raw。",
      sourcePath: "data/derived/agent_collaboration/agent_authorization_boundary_report.json",
      node: formulaNode,
    },
  ];

  const activeFilters = {
    source: filters.source === "all" ? "全部来源" : sourceDisplayLabel(filters.source, filters.source),
    time: sharedState.filters.timeRange?.label ?? "全部时间",
    project: filters.theme === "all" ? "全部项目/主题" : filters.theme,
    task: filters.category === "all" ? "全部任务类别" : humanCategoryLabel(filters.category),
  };
  const hottestCell = [...frictionCells].sort((a, b) => b.count - a.count)[0];
  const strongestAxis = [...latentAxes].sort((a, b) => b.value - a.value)[0];
  const summary = memoryNodes.length
    ? `当前筛选下，${hottestCell?.rowLabel ?? "摩擦"} 在${hottestCell?.columnLabel ?? "流程"}最需要降噪，${strongestAxis?.label ?? "潜在信号"}是最强潜性轴；图谱已按来源、时间、项目和任务过滤。`
    : "当前筛选下没有可计算的工作流/潜性/治理信号；请放宽过滤条件后再查看。";

  return {
    schemaVersion: WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION,
    activeFilters,
    visualCopy,
    sankeyLinks,
    frictionCells,
    latentAxes,
    evidenceEvents,
    formulaRows,
    summary,
  };
}

function buildHumanQuestionMapModel(
  clioModel: ClioLikeVisualModel,
  economicModel: EconomicLikeVisualModel,
  workflowModel: WorkflowLatentGovernanceVisualModel,
): HumanQuestionMapModel {
  const clioTargets: Record<ClioLikeVisualId, ViewKey> = {
    cluster_tree: "galaxy",
    bubble_map: "galaxy",
    topic_cluster_explorer: "search",
  };
  const economicTargets: Record<EconomicLikeVisualId, ViewKey> = {
    task_treemap: "roi",
    automation_vs_augmentation: "search",
    roi_scatter: "roi",
    opportunity_radar: "summary",
  };
  const workflowTargets: Record<WorkflowLatentGovernanceVisualId, ViewKey> = {
    agent_decision_sankey: "summary",
    friction_heatmap: "search",
    latent_radar: "summary",
    evidence_timeline: "timeline",
    formula_explorer: "roi",
  };
  const gateReasons: Record<HumanQuestionMapVisualId, string> = {
    cluster_tree: "问题能定位主题层级，行动能进入 galaxy/search 复核。",
    bubble_map: "问题能比较高频、机会和风险，行动能优先打开高 ROI 簇。",
    topic_cluster_explorer: "问题能决定继续追问哪个簇，行动能进入搜索复核证据。",
    task_treemap: "问题能识别 AI 使用集中任务，行动能与 ROI 对齐。",
    automation_vs_augmentation: "问题能区分自动化和增强，行动能选择固化流程或保留人工判断。",
    roi_scatter: "问题能识别值得继续加码的任务，行动能处理低 ROI 高频任务。",
    opportunity_radar: "问题能识别机会缺口，行动能选择下一步验证问题。",
    agent_decision_sankey: "问题能发现 Agent 执行路径失真，行动能转成 run contract 或授权判断。",
    friction_heatmap: "问题能定位反复浪费时间的位置，行动能转成停止条件或降噪规则。",
    latent_radar: "问题能追踪增强的潜在信号，行动能验证或降权。",
    evidence_timeline: "问题能追溯结论来源，行动能复核证据新鲜度。",
    formula_explorer: "问题能解释 proxy 分数，行动能检查参数和 proposal-only 边界。",
  };

  const entries: HumanQuestionMapEntry[] = [
    ...clioModel.visualCopy.map((copy) =>
      buildHumanQuestionMapEntry(copy, "clio_like", "主题/簇图谱", clioTargets[copy.id], gateReasons[copy.id]),
    ),
    ...economicModel.visualCopy.map((copy) =>
      buildHumanQuestionMapEntry(copy, "economic_like", "ROI/任务图谱", economicTargets[copy.id], gateReasons[copy.id]),
    ),
    ...workflowModel.visualCopy.map((copy) =>
      buildHumanQuestionMapEntry(copy, "workflow_governance", "工作流/治理图谱", workflowTargets[copy.id], gateReasons[copy.id]),
    ),
  ];
  const excludedCandidates: HumanQuestionMapExcludedCandidate[] = [
    {
      id: "decorative_density_cloud",
      title: "装饰性密度云",
      reason: "只有视觉密度，没有可回答的人类问题和行动入口，因此不纳入默认决策图谱。",
      visualRoiGatePass: false,
      p0Included: false,
    },
    {
      id: "raw_conversation_heat_glow",
      title: "Raw conversation heat glow",
      reason: "依赖原始私有语料且不能提升验收决策，因此保留为排除候选。",
      visualRoiGatePass: false,
      p0Included: false,
    },
  ];
  const p0VisualCount = entries.filter((entry) => entry.p0Included && entry.visualRoiGatePass).length;
  const failedP0Count = entries.filter((entry) => !entry.p0Included || !entry.visualRoiGatePass).length;
  const familyCounts = countBy(entries, (entry) => entry.familyLabel);
  const strongestGateLabel = topRows(familyCounts, 1)[0]?.label ?? "问题行动图谱";
  return {
    schemaVersion: HUMAN_QUESTION_MAP_VERSION,
    activeFilters: workflowModel.activeFilters,
    entries,
    excludedCandidates,
    p0VisualCount,
    failedP0Count,
    strongestGateLabel,
    summary: `${entries.length.toLocaleString()} 张图谱已统一到人类问题、行动价值和可验收判断；当前筛选沿用来源、时间、项目和任务，${failedP0Count.toLocaleString()} 张图谱未通过纳入标准。`,
  };
}

function buildHumanQuestionMapEntry(
  copy: ClioLikeVisualCopy | EconomicLikeVisualCopy | WorkflowLatentGovernanceVisualCopy,
  familyId: HumanQuestionMapFamilyId,
  familyLabel: string,
  targetView: ViewKey,
  gateReason: string,
): HumanQuestionMapEntry {
  return {
    id: copy.id,
    familyId,
    familyLabel,
    title: copy.title,
    insightHeader: copy.insightHeader,
    humanQuestion: copy.humanQuestion,
    actionValue: copy.actionValue,
    targetView,
    gateReason,
    visualRoiGatePass: true,
    p0Included: true,
  };
}

function nodeTextMatches(node: AtlasNode, patterns: string[]): boolean {
  const haystack = `${node.label} ${node.statement ?? ""} ${node.category ?? ""} ${node.memory_tier ?? ""} ${node.metrics?.roi?.recommended_action ?? ""}`.toLowerCase();
  return patterns.some((pattern) => haystack.includes(pattern.toLowerCase()));
}

function workflowHeatColor(intensity: number): string {
  if (intensity >= 0.72) return "#f08fa3";
  if (intensity >= 0.42) return "#f6c56f";
  if (intensity > 0) return "#8fd3ff";
  return "#2c3440";
}

function buildHomeOverviewModel(
  nodes: AtlasNode[],
  graphEdges: AtlasEdge[],
  deltaStats: DeltaStats,
): {
  weatherLabel: string;
  weatherNote: string;
  weatherTone: HomeSignalCard["tone"];
  weatherV2: MemoryWeatherV2;
  topicRows: Array<{ label: string; count: number }>;
  tierRows: Array<{ label: string; count: number }>;
  categoryRows: Array<{ label: string; count: number }>;
  protoStarCount: number;
  blackHoleCount: number;
  signals: HomeSignalCard[];
  actions: HomeAction[];
  tierAssets: HomeTierAsset[];
  topicDetails: HomeTopicDetail[];
  miniStarfieldPoints: MiniStarfieldPoint[];
  miniStarfieldFocus: AtlasNode | null;
  miniStarfieldSummary: string;
  riverPulseSegments: RiverPulseSegment[];
  riverPulseFocus: AtlasNode | null;
  inspectorLinks: HomeInspectorLink[];
} {
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const topicRows = topRows(countBy(memoryNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "未归类主题"), 6);
  const tierRows = topRows(countBy(memoryNodes, (node) => normalizeMemoryTier(node.memory_tier)), 4);
  const categoryRows = topRows(countBy(memoryNodes, (node) => humanCategoryLabel(node.category)), 6);
  const latest = parseDay(deltaStats.latestDate) ?? maxNodeDate(memoryNodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const previousStart = addDays(latest, -89);
  const recentNodes = memoryNodes.filter((node) => isNodeBetween(node, recentStart, latest));
  const olderComparableNodes = memoryNodes.filter((node) => isNodeBetween(node, previousStart, addDays(recentStart, -1)));
  const staleNodes = memoryNodes.filter((node) => isBlackHoleCandidate(node));
  const protoStarNodes = memoryNodes.filter((node) => isProtoStarCandidate(node, recentStart, latest));
  const decliningRows = findDecliningTopicRows(recentNodes, olderComparableNodes);
  const weather = homeWeatherFor(deltaStats, staleNodes.length, protoStarNodes.length);
  const weatherV2 = buildMemoryWeatherV2(memoryNodes, deltaStats, staleNodes, protoStarNodes, topicRows, decliningRows);
  const topTopic = topicRows[0] ?? { label: "暂无主题", count: 0 };
  const risingTopic = topRows(countBy(recentNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "近期主题"), 1)[0] ?? {
    label: "暂无近期增量",
    count: 0,
  };
  const decliningTopic = decliningRows[0] ?? { label: "暂无明显冷却", count: 0 };
  const blackHoleNode = selectRepresentativeNode(staleNodes);
  const protoStarNode = selectRepresentativeNode(protoStarNodes);
  const highLeverageNode = selectRepresentativeNode(memoryNodes);
  const decisionCount = memoryNodes.filter((node) => node.category === "decision").length;
  const coreCount = memoryNodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length;
  const miniStarfieldPoints = buildMiniStarfieldPreview(memoryNodes, graphEdges);
  const riverPulseSegments = buildRiverPulsePreview(recentNodes, olderComparableNodes);
  const riverPulseFocus = riverPulseSegments.find((segment) => segment.node)?.node ?? protoStarNode ?? highLeverageNode;
  const actions = buildNextActionDetails({
    blackHoleNode,
    coreCount,
    decisionCount,
    deltaStats,
    graphEdges,
    highLeverageNode,
    memoryNodes,
    protoStarNode,
    protoStarNodes,
    recentNodes,
    staleNodes,
    topTopic,
  });
  const tierAssets = buildTierAssetDetails({
    actions,
    graphEdges,
    latest,
    memoryNodes,
    protoStarNodes,
    staleNodes,
    topTopic,
  });

  return {
    weatherLabel: weather.label,
    weatherNote: weather.note,
    weatherTone: weather.tone,
    weatherV2,
    topicRows,
    tierRows,
    categoryRows,
    protoStarCount: protoStarNodes.length,
    blackHoleCount: staleNodes.length,
    signals: [
      {
        id: "weather",
        title: "认知天气",
        value: weather.label,
        note: weather.note,
        tone: weather.tone,
      },
      {
        id: "dominant",
        title: "主导主题",
        value: topTopic.label,
        note: `${topTopic.count.toLocaleString()} 条记忆集中在这个主题，可作为本轮复盘入口。`,
        tone: "dominant",
      },
      {
        id: "rising",
        title: "上升机会",
        value: risingTopic.label,
        note: `${risingTopic.count.toLocaleString()} 条近期记录；优先检查是否可以转成项目、技能或行动。`,
        tone: "rising",
      },
      {
        id: "declining",
        title: "冷却轨道",
        value: decliningTopic.label,
        note: decliningTopic.count
          ? `近 30 天降温 ${decliningTopic.count.toLocaleString()} 条；适合压缩、降权或补充新证据。`
          : "当前没有明显降温主题；继续观察低频但重要的长期资产。",
        tone: "declining",
      },
      {
        id: "black-hole",
        title: "Black Hole 风险",
        value: staleNodes.length.toLocaleString(),
        note: blackHoleNode
          ? `${humanNodeDisplayTitle(blackHoleNode)}：${recommendedActionForNode(blackHoleNode)}`
          : "未发现明显低价值循环；仍需保持 proposal-only 写回边界。",
        tone: "black-hole",
      },
      {
        id: "proto-star",
        title: "Proto-Star 机会",
        value: protoStarNodes.length.toLocaleString(),
        note: protoStarNode
          ? `${humanNodeDisplayTitle(protoStarNode)}：ROI ${formatScore(protoStarNode.metrics?.roi?.leverage_score)}`
          : "近期机会信号不足；先从主导主题中寻找可执行切口。",
        tone: "proto-star",
      },
    ],
    actions,
    tierAssets,
    topicDetails: buildTopicClassificationDetails({
      actions,
      graphEdges,
      memoryNodes,
      protoStarNodes,
      recentNodes,
      olderComparableNodes,
      staleNodes,
      tierAssets,
    }),
    miniStarfieldPoints,
    miniStarfieldFocus: miniStarfieldPoints[0]?.node ?? highLeverageNode,
    miniStarfieldSummary: `${miniStarfieldPoints.length.toLocaleString()} 个轻量静态星点，按 ROI、连接和层级压缩显示，不加载 WebGL。`,
    riverPulseSegments,
    riverPulseFocus,
    inspectorLinks: buildHomeInspectorLinks([protoStarNode, blackHoleNode, highLeverageNode], memoryNodes, graphEdges),
  };
}

function buildHomeArrivalBriefing(
  atlas: MemoryAtlas,
  nodes: AtlasNode[],
  model: ReturnType<typeof buildHomeOverviewModel>,
  deltaStats: DeltaStats,
): HomeArrivalBriefingCard[] {
  const latest = parseDay(deltaStats.latestDate) ?? maxNodeDate(nodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const recentNodes = nodes
    .filter((node) => node.kind === "memory" && isNodeBetween(node, recentStart, latest))
    .sort((a, b) => (Date.parse(b.date ?? "") || 0) - (Date.parse(a.date ?? "") || 0));
  const newestImportantNode = recentNodes
    .slice()
    .sort((a, b) => (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0))
    .at(0) ?? recentNodes.at(0) ?? model.miniStarfieldFocus;
  const strengtheningSegment = model.riverPulseSegments.find((segment) => segment.delta > 0) ?? model.riverPulseSegments[0];
  const weakeningSegment = model.riverPulseSegments.find((segment) => segment.delta < 0);
  const recommendationCount = pendingProposalCandidateCount(atlas.agent_recommendations);
  const proposedActionCount = model.actions.filter((action) => action.status === "proposed" || action.status === "review").length;
  const pendingProposalCount = Math.max(recommendationCount, proposedActionCount);
  const failedSources = syncFailureSources(atlas);
  const latestSource = latestDataSource(atlas);
  const topAction = model.actions[0];

  return [
    {
      id: "new_material",
      label: HOME_ARRIVAL_CATEGORY_LABELS.new_material,
      value: `${deltaStats.recentCount.toLocaleString()} 条`,
      summary: newestImportantNode
        ? `最近新增或活跃的高价值线索是「${humanNodeDisplayTitle(newestImportantNode)}」。`
        : "当前筛选下没有新的高价值资料；先保持观察，不生成伪增量。",
      evidence: `近 30 天 ${deltaStats.recentCount.toLocaleString()} 条，上一窗口 ${deltaStats.previousCount.toLocaleString()} 条。`,
      nextStep: newestImportantNode ? "打开星图核对证据和关联主题" : "放宽筛选或等待下一次同步",
      targetView: "galaxy",
      node: newestImportantNode,
      icon: Download,
      tone: "new-material",
      machineSignal: `delta=${deltaStats.deltaCount}`,
    },
    {
      id: "strengthened",
      label: HOME_ARRIVAL_CATEGORY_LABELS.strengthened,
      value: strengtheningSegment ? strengtheningSegment.label : model.topicRows[0]?.label ?? "暂无",
      summary: strengtheningSegment
        ? `这个结论在近期窗口增强 ${formatSigned(strengtheningSegment.delta)} 条。`
        : "没有稳定增强信号；先看主导主题是否仍有决策价值。",
      evidence: strengtheningSegment
        ? `近期 ${strengtheningSegment.recentCount.toLocaleString()} 条，对比窗口 ${strengtheningSegment.previousCount.toLocaleString()} 条。`
        : `主导主题 ${model.topicRows[0]?.count ?? 0} 条。`,
      nextStep: "进入时间轴查看增强发生在哪些记录上",
      targetView: "timeline",
      node: strengtheningSegment?.node ?? model.riverPulseFocus,
      icon: Activity,
      tone: "strengthened",
      machineSignal: `strengthened_delta=${strengtheningSegment?.delta ?? 0}`,
    },
    {
      id: "weakened",
      label: HOME_ARRIVAL_CATEGORY_LABELS.weakened,
      value: model.blackHoleCount.toLocaleString(),
      summary: weakeningSegment
        ? `「${weakeningSegment.label}」近期减弱 ${formatSigned(weakeningSegment.delta)} 条，需要确认是过期还是沉淀完成。`
        : `${model.blackHoleCount.toLocaleString()} 条风险循环或过期候选需要保留在复盘视野里。`,
      evidence: weakeningSegment
        ? `近期 ${weakeningSegment.recentCount.toLocaleString()} 条，对比窗口 ${weakeningSegment.previousCount.toLocaleString()} 条。`
        : "根据时效和低价值循环信号综合判断。",
      nextStep: "先复核，不直接降权或删除",
      targetView: "summary",
      node: weakeningSegment?.node ?? topAction?.node ?? null,
      icon: FilterX,
      tone: "weakened",
      machineSignal: `black_holes=${model.blackHoleCount}`,
    },
    {
      id: "pending_proposal",
      label: HOME_ARRIVAL_CATEGORY_LABELS.pending_proposal,
      value: `${pendingProposalCount.toLocaleString()} 项`,
      summary: pendingProposalCount
        ? "有代理建议或下一步行动可转成提案候选，仍需人工授权。"
        : "当前没有待授权提案；系统继续保持仅生成提案，不直接应用。",
      evidence: `代理建议 ${recommendationCount.toLocaleString()} 项，行动建议 ${proposedActionCount.toLocaleString()} 项。`,
      nextStep: pendingProposalCount ? "进入决定下一步，逐项人工判断" : "保留仅生成提案的边界",
      targetView: "summary",
      node: topAction?.node ?? null,
      icon: Save,
      tone: "proposal",
      machineSignal: `pending_proposals=${pendingProposalCount}`,
    },
    {
      id: "sync_failure",
      label: HOME_ARRIVAL_CATEGORY_LABELS.sync_failure,
      value: `${failedSources.length.toLocaleString()} 个`,
      summary: failedSources.length
        ? `需要处理的数据源：${failedSources.map((source) => source.label).join("、")}。`
        : `当前未看到同步失败；最新活跃数据源是 ${latestSource?.label ?? "未知数据源"}。`,
      evidence: latestSource ? `最新数据源「${latestSource.label}」已纳入本次快照。` : "当前没有可用的数据源状态。",
      nextStep: failedSources.length ? "先修同步，再相信新增结论" : "继续用当前快照判断",
      targetView: "search",
      node: null,
      icon: Cloud,
      tone: "sync",
      machineSignal: `sync_failures=${failedSources.length}`,
    },
  ];
}

function pendingProposalCandidateCount(recommendations: MemoryAtlas["agent_recommendations"]): number {
  if (!recommendations) return 0;
  return (
    recommendations.memory.added.length +
    recommendations.memory.modified.length +
    recommendations.meta_data.added.length +
    recommendations.meta_data.modified.length
  );
}

function syncFailureSources(atlas: MemoryAtlas): DataSourceSummary[] {
  return (atlas.data_sources ?? []).filter((source) => {
    if (source.id === "all") return false;
    const status = `${source.status ?? ""} ${source.ingestion_status ?? ""}`.toLowerCase();
    return /fail|error|stale|blocked|missing|denied|timeout|失败|过期|阻塞/.test(status) || !/active|merged/.test(status);
  });
}

function latestDataSource(atlas: MemoryAtlas): DataSourceSummary | null {
  return (atlas.data_sources ?? [])
    .filter((source) => source.id !== "all")
    .slice()
    .sort((a, b) => (b.latest_date || "").localeCompare(a.latest_date || ""))
    .at(0) ?? null;
}

function buildTierAssetDetails({
  actions,
  graphEdges,
  latest,
  memoryNodes,
  protoStarNodes,
  staleNodes,
  topTopic,
}: {
  actions: HomeAction[];
  graphEdges: AtlasEdge[];
  latest: Date;
  memoryNodes: AtlasNode[];
  protoStarNodes: AtlasNode[];
  staleNodes: AtlasNode[];
  topTopic: { label: string; count: number };
}): HomeTierAsset[] {
  const assetTiers: HomeTierAsset["asset_tier"][] = [
    "core_profile",
    "project",
    "decision",
    "workflow",
    "knowledge",
    "opportunity",
    "stale",
  ];
  const assets = assetTiers
    .map((asset_tier) => {
      const candidates = tierAssetCandidatesFor(asset_tier, memoryNodes, protoStarNodes, staleNodes);
      const node = selectRepresentativeNode(candidates);
      return node ? createTierAssetDetail(asset_tier, node, actions, graphEdges, latest, topTopic.label) : null;
    })
    .filter((asset): asset is HomeTierAsset => Boolean(asset));

  return assets
    .sort((left, right) => tierAssetSortScore(right) - tierAssetSortScore(left))
    .slice(0, TIER_ASSET_TOP_LIMIT);
}

function tierAssetCandidatesFor(
  assetTier: HomeTierAsset["asset_tier"],
  memoryNodes: AtlasNode[],
  protoStarNodes: AtlasNode[],
  staleNodes: AtlasNode[],
): AtlasNode[] {
  if (assetTier === "core_profile") {
    return memoryNodes.filter((node) => {
      const category = normalizedNodeCategory(node);
      return (
        normalizeMemoryTier(node.memory_tier) === "核心画像" ||
        category.includes("preference") ||
        category.includes("answering_rule") ||
        category.includes("security_boundary")
      );
    });
  }
  if (assetTier === "project") {
    return memoryNodes.filter((node) => textSignalsForNode(node).some((value) => value.includes("project") || value.includes("项目")));
  }
  if (assetTier === "decision") {
    return memoryNodes.filter((node) => node.category === "decision" || textSignalsForNode(node).some((value) => value.includes("决策")));
  }
  if (assetTier === "workflow") {
    return memoryNodes.filter((node) =>
      textSignalsForNode(node).some((value) =>
        ["workflow", "process", "automation", "run_contract", "流程", "工作流", "规则"].some((token) => value.includes(token)),
      ),
    );
  }
  if (assetTier === "opportunity") return protoStarNodes;
  if (assetTier === "stale") return staleNodes;

  const reserved = new Set([
    ...tierAssetCandidatesFor("core_profile", memoryNodes, protoStarNodes, staleNodes).map((node) => node.id),
    ...tierAssetCandidatesFor("project", memoryNodes, protoStarNodes, staleNodes).map((node) => node.id),
    ...tierAssetCandidatesFor("decision", memoryNodes, protoStarNodes, staleNodes).map((node) => node.id),
    ...tierAssetCandidatesFor("workflow", memoryNodes, protoStarNodes, staleNodes).map((node) => node.id),
    ...protoStarNodes.map((node) => node.id),
    ...staleNodes.map((node) => node.id),
  ]);
  return memoryNodes.filter((node) => !reserved.has(node.id));
}

function createTierAssetDetail(
  asset_tier: HomeTierAsset["asset_tier"],
  node: AtlasNode,
  actions: HomeAction[],
  graphEdges: AtlasEdge[],
  latest: Date,
  fallbackTopic: string,
): HomeTierAsset {
  const value_score = roiScoreForNode(node, 0.48);
  const confidence = confidenceForAction(node, 0.62);
  const theme = compactThemeLabel(humanThemeLabel(node)) || fallbackTopic || "未归类主题";
  const updated_at = node.date || latest.toISOString().slice(0, 10);
  const staleness_status = stalenessStatusForAsset(asset_tier, node, latest);
  const evidence_refs = evidenceRefsForNode(node, graphEdges, `level-asset:${asset_tier}`);
  const linked_action_ids = actions
    .filter((action) => action.linked_asset_ids.includes(node.id) || action.linked_topic_ids.includes(`topic:${theme}`))
    .map((action) => action.action_id);
  const recommended_asset_action = recommendedAssetActionFor(asset_tier, staleness_status, value_score, confidence);
  const title = humanNodeDisplayTitle(node);

  return {
    asset_id: `${asset_tier}:${node.id}`,
    asset_tier,
    confidence,
    evidence_count: evidence_refs.length,
    evidence_refs,
    id: `${asset_tier}:${node.id}`,
    importance: importanceForAsset(value_score),
    last_seen_range: lastSeenRangeForAsset(node, latest),
    linked_action_ids,
    linked_topic_ids: [`topic:${theme}`],
    node,
    priority: priorityForAsset(asset_tier, staleness_status, value_score),
    proposal_hint: recommended_asset_action === "keep" && confidence >= 0.7 ? "proposal_not_needed" : "proposal_recommended",
    proposal_only: true,
    recommended_asset_action,
    rollback_hint: "若资产判断不成立，只关闭面板或撤销后续 proposal 草稿；Phase 1.3 不写长期记忆。",
    source_scope: "redacted_atlas_snapshot",
    staleness_status,
    summary: `${title} 属于 ${asset_tier} 层级资产；主题 ${theme}，当前仅使用 redacted label、层级、分类、日期、ROI 与连接数生成说明。`,
    targetView: "search",
    theme,
    title,
    updated_at,
    value_score,
  };
}

function tierAssetSortScore(asset: TierAssetDetail): number {
  return (
    asset.value_score * TIER_ASSET_SORT_WEIGHTS.value_weight +
    importanceScore(asset.importance) * TIER_ASSET_SORT_WEIGHTS.importance_weight +
    asset.confidence * TIER_ASSET_SORT_WEIGHTS.confidence_weight -
    stalenessPenalty(asset.staleness_status) * TIER_ASSET_SORT_WEIGHTS.staleness_penalty_weight
  );
}

function textSignalsForNode(node: AtlasNode): string[] {
  return [node.kind, node.category, node.label, node.source_label, humanCategoryLabel(node.category), normalizeMemoryTier(node.memory_tier)]
    .filter((value): value is string => Boolean(value))
    .map((value) => value.toLowerCase());
}

function normalizedNodeCategory(node: AtlasNode): string {
  return (node.category || "").toLowerCase();
}

function stalenessStatusForAsset(
  assetTier: HomeTierAsset["asset_tier"],
  node: AtlasNode,
  latest: Date,
): HomeTierAsset["staleness_status"] {
  if (assetTier === "stale" || node.metrics?.roi?.staleness_status?.includes("stale")) return "stale";
  const day = parseDay(node.date);
  if (!day) return "unknown";
  const ageDays = Math.max(0, Math.round((latest.getTime() - day.getTime()) / 86_400_000));
  return ageDays > 120 ? "needs_review" : "current";
}

function lastSeenRangeForAsset(node: AtlasNode, latest: Date): string {
  const seen = node.date || "unknown";
  return `${seen}..${latest.toISOString().slice(0, 10)}`;
}

function importanceForAsset(valueScore: number): HomeTierAsset["importance"] {
  if (valueScore >= 0.72) return "high";
  if (valueScore >= 0.45) return "medium";
  return "low";
}

function importanceScore(importance: TierAssetDetail["importance"]): number {
  if (importance === "high") return 1;
  if (importance === "medium") return 0.62;
  return 0.32;
}

function priorityForAsset(
  assetTier: HomeTierAsset["asset_tier"],
  stalenessStatus: HomeTierAsset["staleness_status"],
  valueScore: number,
): HomeTierAsset["priority"] {
  if (stalenessStatus === "stale") return "p1";
  if (assetTier === "core_profile" || valueScore >= 0.78) return "p0";
  if (assetTier === "decision" || assetTier === "project" || valueScore >= 0.58) return "p1";
  if (stalenessStatus === "needs_review") return "p2";
  return "watch";
}

function stalenessPenalty(stalenessStatus: TierAssetDetail["staleness_status"]): number {
  if (stalenessStatus === "stale") return 0.85;
  if (stalenessStatus === "needs_review") return 0.45;
  if (stalenessStatus === "unknown") return 0.25;
  return 0.05;
}

function recommendedAssetActionFor(
  assetTier: HomeTierAsset["asset_tier"],
  stalenessStatus: HomeTierAsset["staleness_status"],
  valueScore: number,
  confidence: number,
): HomeTierAsset["recommended_asset_action"] {
  if (stalenessStatus === "stale") return "lower_priority";
  if (stalenessStatus === "needs_review") return "review";
  if (assetTier === "opportunity") return "validate";
  if (assetTier === "workflow") return "consolidate";
  if (confidence < 0.5) return "review";
  if (valueScore < 0.35) return "defer";
  return "keep";
}

function buildTopicClassificationDetails({
  actions,
  graphEdges,
  memoryNodes,
  protoStarNodes,
  recentNodes,
  olderComparableNodes,
  staleNodes,
  tierAssets,
}: {
  actions: HomeAction[];
  graphEdges: AtlasEdge[];
  memoryNodes: AtlasNode[];
  protoStarNodes: AtlasNode[];
  recentNodes: AtlasNode[];
  olderComparableNodes: AtlasNode[];
  staleNodes: AtlasNode[];
  tierAssets: HomeTierAsset[];
}): HomeTopicDetail[] {
  const groups = new Map<string, AtlasNode[]>();
  memoryNodes.forEach((node) => {
    const topic_label = compactThemeLabel(humanThemeLabel(node)) || "未归类主题";
    groups.set(topic_label, [...(groups.get(topic_label) ?? []), node]);
  });
  const topCount = Math.max(1, ...Array.from(groups.values()).map((nodes) => nodes.length));

  return Array.from(groups.entries())
    .map(([topic_label, nodes]) =>
      createTopicClassificationDetail(
        topic_label,
        nodes,
        topCount,
        actions,
        graphEdges,
        protoStarNodes,
        recentNodes,
        olderComparableNodes,
        staleNodes,
        tierAssets,
      ),
    )
    .sort((left, right) => topicClassificationSortScore(right) - topicClassificationSortScore(left))
    .slice(0, TOPIC_CLASSIFICATION_TOP_LIMIT);
}

function createTopicClassificationDetail(
  topic_label: string,
  nodes: AtlasNode[],
  topCount: number,
  actions: HomeAction[],
  graphEdges: AtlasEdge[],
  protoStarNodes: AtlasNode[],
  recentNodes: AtlasNode[],
  olderComparableNodes: AtlasNode[],
  staleNodes: AtlasNode[],
  tierAssets: HomeTierAsset[],
): HomeTopicDetail {
  const topic_id = `topic:${topic_label}`;
  const representative = selectRepresentativeNode(nodes);
  const recent_count = nodes.filter((node) => recentNodes.some((recent) => recent.id === node.id)).length;
  const previous_count = nodes.filter((node) => olderComparableNodes.some((older) => older.id === node.id)).length;
  const stale_count = nodes.filter((node) => staleNodes.some((stale) => stale.id === node.id)).length;
  const proto_count = nodes.filter((node) => protoStarNodes.some((proto) => proto.id === node.id)).length;
  const topic_state = topicStateForTopic(topic_label, nodes.length, topCount, recent_count, previous_count, stale_count, proto_count);
  const trend = trendForTopic(recent_count, previous_count, proto_count, stale_count);
  const roi_score = averageNodeScore(nodes, (node) => roiScoreForNode(node, 0.45));
  const confidence = averageNodeScore(nodes, (node) => confidenceForAction(node, 0.58));
  const conflict_score = topic_state === "conflict" ? 0.72 : clampActionScore(stale_count / Math.max(1, nodes.length));
  const topic_strength = clampActionScore((nodes.length / topCount) * 0.5 + roi_score * 0.3 + recent_count / Math.max(1, nodes.length) * 0.2);
  const linked_action_ids = actions
    .filter((action) => action.linked_topic_ids.includes(topic_id) || action.reason.includes(topic_label))
    .map((action) => action.action_id);
  const linked_asset_ids = tierAssets
    .filter((asset) => asset.linked_topic_ids.includes(topic_id) || asset.theme === topic_label)
    .map((asset) => asset.asset_id);
  const evidence_refs = evidenceRefsForNode(representative, graphEdges, `topic-classification:${topic_label}`).concat(
    `record_count:${nodes.length}`,
    `recent_count:${recent_count}`,
  );

  return {
    category: topCategoryForNodes(nodes),
    confidence,
    conflict_score,
    evidence_refs,
    id: topic_id,
    linked_action_ids,
    linked_asset_ids,
    matched_reason: `${topic_label} has ${nodes.length.toLocaleString()} redacted records, ${recent_count.toLocaleString()} recent records, ROI ${formatScore(roi_score)} and state ${topic_state}.`,
    node: representative,
    nodes,
    parent_topic: parentTopicForTopic(topic_label),
    proposal_hint: topic_state === "dominant" && confidence >= 0.7 ? "proposal_not_needed" : "proposal_recommended",
    proposal_only: true,
    recent_count,
    record_count: nodes.length,
    representative_record_ids: nodes.slice(0, 5).map((node) => node.id),
    river_handoff: `memory_river:theme_lane:${topic_label}:recent_count:${recent_count}`,
    rollback_hint: "若主题判断不成立，只关闭面板或撤销后续 proposal 草稿；Phase 1.4 不写长期记忆。",
    roi_score,
    starfield_handoff: `memory_starfield:focus_topic:${topic_label}`,
    targetView: topic_state === "declining" || topic_state === "stale" || topic_state === "black_hole" ? "timeline" : "galaxy",
    topic_id,
    topic_label,
    topic_state,
    topic_strength,
    trend,
  };
}

function topicClassificationSortScore(topic: TopicClassificationDetail): number {
  return (
    topic.topic_strength * TOPIC_CLASSIFICATION_SORT_WEIGHTS.strength_weight +
    trendScore(topic.trend) * TOPIC_CLASSIFICATION_SORT_WEIGHTS.trend_weight +
    topic.confidence * TOPIC_CLASSIFICATION_SORT_WEIGHTS.confidence_weight -
    topic.conflict_score * TOPIC_CLASSIFICATION_SORT_WEIGHTS.conflict_penalty_weight
  );
}

function topicStateForTopic(
  topicLabel: string,
  recordCount: number,
  topCount: number,
  recentCount: number,
  previousCount: number,
  staleCount: number,
  protoCount: number,
): TopicClassificationDetail["topic_state"] {
  const lower = topicLabel.toLowerCase();
  if (lower.includes("conflict") || lower.includes("冲突")) return "conflict";
  if (staleCount >= Math.max(2, recordCount * 0.5)) return "black_hole";
  if (recordCount === topCount) return "dominant";
  if (recentCount > previousCount + 1) return "rising";
  if (protoCount > 0 || (recordCount <= 2 && recentCount > 0)) return "emerging";
  if (previousCount > recentCount + 1) return "declining";
  if (staleCount > 0) return "stale";
  return TOPIC_CLASSIFICATION_STATES.includes("dominant") ? "dominant" : "emerging";
}

function trendForTopic(
  recentCount: number,
  previousCount: number,
  protoCount: number,
  staleCount: number,
): TopicClassificationDetail["trend"] {
  if (recentCount > previousCount + 1 || protoCount > 0) return "up";
  if (previousCount > recentCount + 1 || staleCount > recentCount) return "down";
  return "stable";
}

function trendScore(trend: TopicClassificationDetail["trend"]): number {
  if (trend === "up") return 1;
  if (trend === "stable") return 0.62;
  return 0.35;
}

function topCategoryForNodes(nodes: AtlasNode[]): string {
  return topRows(countBy(nodes, (node) => humanCategoryLabel(node.category)), 1)[0]?.label ?? "未分类";
}

function parentTopicForTopic(topicLabel: string): string {
  const lower = topicLabel.toLowerCase();
  if (lower.includes("memory") || topicLabel.includes("记忆")) return "Memory Atlas";
  if (lower.includes("codex") || lower.includes("workflow") || topicLabel.includes("工作流")) return "Delivery System";
  if (lower.includes("visual") || topicLabel.includes("可视化")) return "Visual System";
  return "General";
}

function averageNodeScore(nodes: AtlasNode[], score: (node: AtlasNode) => number): number {
  if (!nodes.length) return 0;
  return clampActionScore(nodes.reduce((sum, node) => sum + score(node), 0) / nodes.length);
}

function buildNextActionDetails({
  blackHoleNode,
  coreCount,
  decisionCount,
  deltaStats,
  graphEdges,
  highLeverageNode,
  memoryNodes,
  protoStarNode,
  protoStarNodes,
  recentNodes,
  staleNodes,
  topTopic,
}: {
  blackHoleNode: AtlasNode | null;
  coreCount: number;
  decisionCount: number;
  deltaStats: DeltaStats;
  graphEdges: AtlasEdge[];
  highLeverageNode: AtlasNode | null;
  memoryNodes: AtlasNode[];
  protoStarNode: AtlasNode | null;
  protoStarNodes: AtlasNode[];
  recentNodes: AtlasNode[];
  staleNodes: AtlasNode[];
  topTopic: { label: string; count: number };
}): HomeAction[] {
  const topNodeEvidence = evidenceRefsForNode(highLeverageNode, graphEdges, "highest-leverage");
  const coreDecisionEvidence = [
    `core_memory_count:${coreCount}`,
    `decision_count:${decisionCount}`,
    `dominant_topic:${topTopic.label}`,
  ];
  const staleEvidence = evidenceRefsForNode(blackHoleNode, graphEdges, "black-hole").concat(
    `stale_candidate_count:${staleNodes.length}`,
  );
  const riverEvidence = evidenceRefsForNode(protoStarNode ?? highLeverageNode, graphEdges, "time-river").concat(
    `recent_count:${deltaStats.recentCount}`,
    `delta_count:${deltaStats.deltaCount}`,
  );
  const protoEvidence = evidenceRefsForNode(protoStarNode, graphEdges, "proto-star").concat(
    `proto_star_count:${protoStarNodes.length}`,
    `recent_memory_count:${recentNodes.length}`,
  );

  const candidates: HomeAction[] = [
    {
      action_id: "inspect-roi",
      action_type: "continue",
      confidence: confidenceForAction(highLeverageNode, 0.78),
      effort_cost: "low",
      evidence_count: topNodeEvidence.length,
      evidence_refs: topNodeEvidence,
      id: "inspect-roi",
      linked_asset_ids: assetIdsForAction(highLeverageNode),
      linked_topic_ids: topicIdsForAction(highLeverageNode, topTopic.label),
      matched_reason: highLeverageNode
        ? `${humanNodeDisplayTitle(highLeverageNode)} 同时具备较高 ROI 与 ${edgeCountFor(highLeverageNode.id, graphEdges).toLocaleString()} 个连接。`
        : "当前筛选下缺少可直接执行的高杠杆记忆，需要先放宽筛选条件。",
      next_step: "打开 ROI Dashboard，核对该记忆是否应进入本轮复盘或 proposal 调整。",
      node: highLeverageNode,
      priority: "P1",
      proposal_hint: "proposal_recommended",
      proposal_only: true,
      reason: highLeverageNode
        ? `${humanNodeDisplayTitle(highLeverageNode)} · ${edgeCountFor(highLeverageNode.id, graphEdges).toLocaleString()} 个连接`
        : "当前筛选下暂无可选记忆，先放宽筛选条件。",
      recommended_time_window: highLeverageNode ? "now" : "later",
      rollback_hint: "若判断不成立，仅关闭 Drawer 或撤销 proposal 草稿；本阶段不会写入长期记忆。",
      roi_score: roiScoreForNode(highLeverageNode, 0.62),
      source: "home_overview.high_leverage",
      status: highLeverageNode ? "proposed" : "review",
      targetView: "roi",
      title: "查看最高杠杆记忆",
      urgency: highLeverageNode ? "high" : "low",
    },
    {
      action_id: "review-core",
      action_type: "review",
      confidence: clampActionScore(coreCount || decisionCount ? 0.82 : 0.54),
      effort_cost: "medium",
      evidence_count: coreDecisionEvidence.length,
      evidence_refs: coreDecisionEvidence,
      id: "review-core",
      linked_asset_ids: memoryNodes
        .filter((node) => node.category === "decision" || normalizeMemoryTier(node.memory_tier) === "核心画像")
        .slice(0, 5)
        .map((node) => node.id),
      linked_topic_ids: [`topic:${topTopic.label}`],
      matched_reason: `${coreCount.toLocaleString()} 条核心画像与 ${decisionCount.toLocaleString()} 条决策是 Summary & Iteration 的主要复核输入。`,
      next_step: "进入 Summary & Iteration，检查核心画像、规则与决策是否仍然支持当前目标。",
      node: null,
      priority: coreCount + decisionCount ? "P1" : "P2",
      proposal_hint: "proposal_recommended",
      proposal_only: true,
      reason: `${coreCount.toLocaleString()} 条核心画像、${decisionCount.toLocaleString()} 条决策适合进入 Summary & Iteration 复核。`,
      recommended_time_window: "today",
      rollback_hint: "如果复核没有发现变更，保留只读结论，不生成 proposal。",
      roi_score: clampActionScore(0.58 + Math.min(0.28, (coreCount + decisionCount) / 80)),
      source: "home_overview.core_decision_counts",
      status: "review",
      targetView: "summary",
      title: "同步核心画像与规则",
      urgency: coreCount + decisionCount ? "medium" : "low",
    },
    {
      action_id: "compress-black-hole",
      action_type: staleNodes.length ? "consolidate" : "defer",
      confidence: confidenceForAction(blackHoleNode, staleNodes.length ? 0.76 : 0.5),
      effort_cost: staleNodes.length > 12 ? "high" : "medium",
      evidence_count: staleEvidence.length,
      evidence_refs: staleEvidence,
      id: "compress-black-hole",
      linked_asset_ids: assetIdsForAction(blackHoleNode).concat(staleNodes.slice(0, 4).map((node) => node.id)),
      linked_topic_ids: topicIdsForAction(blackHoleNode, "Black Hole"),
      matched_reason: staleNodes.length
        ? `${staleNodes.length.toLocaleString()} 条历史、临时或过时信号被标记为 Black Hole 候选。`
        : "当前没有明显 Black Hole 候选，保留为定期低价值循环检查。",
      next_step: staleNodes.length
        ? "打开 Search Review，检查是否需要降权、隐藏到期窗口或补充新证据。"
        : "本轮跳过压缩动作，只在复盘中保留低价值循环观察项。",
      node: blackHoleNode,
      priority: staleNodes.length ? "P2" : "P3",
      proposal_hint: staleNodes.length ? "proposal_recommended" : "proposal_not_needed",
      proposal_only: true,
      reason: staleNodes.length
        ? `${staleNodes.length.toLocaleString()} 条历史、临时或过时信号需要降权或补证。`
        : "当前没有明显 Black Hole；保留这一步作为定期检查。",
      recommended_time_window: staleNodes.length ? "this_week" : "later",
      rollback_hint: "任何降权、隐藏或 stale override 都只能生成 proposal JSON，不直接修改长期记忆。",
      roi_score: staleNodes.length ? clampActionScore(0.52 + Math.min(0.3, staleNodes.length / 60)) : 0.28,
      source: "home_overview.black_hole_candidates",
      status: staleNodes.length ? "proposed" : "review",
      targetView: "search",
      title: "压缩低价值循环",
      urgency: staleNodes.length > 8 ? "high" : staleNodes.length ? "medium" : "low",
    },
    {
      action_id: "read-time-river",
      action_type: "review",
      confidence: clampActionScore(deltaStats.recentCount ? 0.74 : 0.5),
      effort_cost: "medium",
      evidence_count: riverEvidence.length,
      evidence_refs: riverEvidence,
      id: "read-time-river",
      linked_asset_ids: assetIdsForAction(protoStarNode ?? highLeverageNode),
      linked_topic_ids: topicIdsForAction(protoStarNode ?? highLeverageNode, topTopic.label),
      matched_reason: `近 30 天 ${deltaStats.recentCount.toLocaleString()} 条，较前 30 天 ${formatSigned(deltaStats.deltaCount)} 条，需要从时间河核对趋势形成过程。`,
      next_step: "进入记忆时间河，查看增强主题、决策节点和异常脉冲是否能解释本期变化。",
      node: protoStarNode ?? highLeverageNode,
      priority: deltaStats.deltaCount >= 0 ? "P2" : "P1",
      proposal_hint: "proposal_not_needed",
      proposal_only: true,
      reason: `近 30 天 ${deltaStats.recentCount.toLocaleString()} 条，较前 30 天 ${formatSigned(deltaStats.deltaCount)} 条。`,
      recommended_time_window: deltaStats.deltaCount < 0 ? "today" : "this_week",
      rollback_hint: "时间河只读复盘不产生写回；若发现排序问题，后续走 proposal-only 调整层。",
      roi_score: deltaStats.deltaCount < 0 ? 0.72 : 0.58,
      source: "home_overview.delta_stats",
      status: "review",
      targetView: "timeline",
      title: "按时间复盘增量",
      urgency: deltaStats.deltaCount < 0 ? "high" : "medium",
    },
    {
      action_id: "validate-proto-star",
      action_type: "explore",
      confidence: confidenceForAction(protoStarNode, protoStarNodes.length ? 0.7 : 0.46),
      effort_cost: "low",
      evidence_count: protoEvidence.length,
      evidence_refs: protoEvidence,
      id: "validate-proto-star",
      linked_asset_ids: assetIdsForAction(protoStarNode).concat(protoStarNodes.slice(0, 4).map((node) => node.id)),
      linked_topic_ids: topicIdsForAction(protoStarNode, topTopic.label),
      matched_reason: protoStarNodes.length
        ? `${protoStarNodes.length.toLocaleString()} 个近期机会信号可作为新项目、技能或行动候选。`
        : "近期机会信号不足，先从主导主题中寻找可执行切口。",
      next_step: protoStarNode
        ? "打开记忆星系，查看该 proto-star 周围的主题引力源和相邻证据。"
        : "保留机会观察项，下一轮先补充近期高置信证据。",
      node: protoStarNode,
      priority: protoStarNodes.length ? "P2" : "P3",
      proposal_hint: protoStarNodes.length ? "proposal_recommended" : "proposal_not_needed",
      proposal_only: true,
      reason: protoStarNode
        ? `${humanNodeDisplayTitle(protoStarNode)}：ROI ${formatScore(protoStarNode.metrics?.roi?.leverage_score)}`
        : "近期机会信号不足；先从主导主题中寻找可执行切口。",
      recommended_time_window: protoStarNodes.length ? "today" : "later",
      rollback_hint: "机会判断只影响本地展示和 proposal 草稿，不会在 Phase 1.2 写回数据库。",
      roi_score: protoStarNodes.length ? roiScoreForNode(protoStarNode, 0.66) : 0.34,
      source: "home_overview.proto_star_candidates",
      status: protoStarNodes.length ? "proposed" : "review",
      targetView: "galaxy",
      title: "验证新生机会",
      urgency: protoStarNodes.length > 4 ? "high" : protoStarNodes.length ? "medium" : "low",
    },
  ];

  return candidates
    .sort((left, right) => nextActionSortScore(right) - nextActionSortScore(left))
    .slice(0, NEXT_ACTION_TOP_LIMIT);
}

function nextActionSortScore(action: HomeActionDetail): number {
  return (
    action.roi_score * NEXT_ACTION_SORT_WEIGHTS.roi_weight +
    urgencyScore(action.urgency) * NEXT_ACTION_SORT_WEIGHTS.urgency_weight +
    action.confidence * NEXT_ACTION_SORT_WEIGHTS.confidence_weight -
    effortPenalty(action.effort_cost) * NEXT_ACTION_SORT_WEIGHTS.effort_penalty_weight
  );
}

function urgencyScore(urgency: HomeActionDetail["urgency"]): number {
  if (urgency === "high") return 1;
  if (urgency === "medium") return 0.66;
  return 0.33;
}

function effortPenalty(effortCost: HomeActionDetail["effort_cost"]): number {
  if (effortCost === "high") return 0.82;
  if (effortCost === "medium") return 0.45;
  return 0.15;
}

function roiScoreForNode(node: AtlasNode | null, fallback: number): number {
  return clampActionScore(node?.metrics?.roi?.leverage_score ?? node?.metrics?.weight_score ?? fallback);
}

function confidenceForAction(node: AtlasNode | null, fallback: number): number {
  const parsed = Number(node?.confidence);
  if (Number.isFinite(parsed)) return clampActionScore(parsed);
  return clampActionScore(fallback);
}

function clampActionScore(value: number): number {
  return Math.max(0, Math.min(1, value));
}

function evidenceRefsForNode(node: AtlasNode | null, graphEdges: AtlasEdge[], prefix: string): string[] {
  if (!node) return [`${prefix}:empty-node`];
  const refs = [
    `${prefix}:node:${node.id}`,
    `${prefix}:source:${node.source_label ?? node.data_source ?? "unknown"}`,
    `${prefix}:edge_count:${edgeCountFor(node.id, graphEdges)}`,
  ];
  if (node.memory_id) refs.push(`${prefix}:memory:${node.memory_id}`);
  return refs;
}

function topicIdsForAction(node: AtlasNode | null, fallbackLabel: string): string[] {
  const label = node ? compactThemeLabel(humanThemeLabel(node)) : fallbackLabel;
  return label ? [`topic:${label}`] : [];
}

function assetIdsForAction(node: AtlasNode | null): string[] {
  return node ? [node.id] : [];
}

function buildMiniStarfieldPreview(nodes: AtlasNode[], graphEdges: AtlasEdge[]): MiniStarfieldPoint[] {
  const degree = degreeMap(graphEdges);
  return [...nodes]
    .sort((a, b) => homePreviewScore(b, degree) - homePreviewScore(a, degree) || (b.date ?? "").localeCompare(a.date ?? ""))
    .slice(0, 28)
    .map((node, index) => {
      const orbit = index % 4;
      const angle = stableUnit(node.id, "home-mini-star-angle") * Math.PI * 2;
      const radius = 20 + orbit * 32 + stableUnit(node.id, "home-mini-star-radius") * 28;
      const centerX = 210 + Math.cos(angle) * radius;
      const centerY = 95 + Math.sin(angle) * radius * 0.46;
      const score = homePreviewScore(node, degree);
      return {
        id: node.id,
        label: humanNodeDisplayTitle(node),
        x: Math.min(384, Math.max(36, centerX)),
        y: Math.min(158, Math.max(30, centerY)),
        radius: Math.min(9, 3.2 + Math.sqrt(Math.max(0, score)) * 0.42),
        color: nodeColor(node),
        node,
      };
    });
}

function homePreviewScore(node: AtlasNode, degree: Map<string, number>): number {
  const tier = normalizeMemoryTier(node.memory_tier);
  const tierScore = tier === "核心画像" ? 14 : tier === "一般" ? 8 : 3;
  const categoryScore = ["decision", "project_context", "workflow", "preference", "answering_rule"].includes(node.category ?? "") ? 10 : 0;
  const roi = (node.metrics?.roi?.leverage_score ?? 0) * 16;
  const importance = node.importance === "高" ? 10 : node.importance === "中" ? 5 : 1;
  return tierScore + categoryScore + roi + importance + (degree.get(node.id) ?? 0) * 1.6;
}

function buildRiverPulsePreview(recentNodes: AtlasNode[], previousNodes: AtlasNode[]): RiverPulseSegment[] {
  const recentCounts = countBy(recentNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "近期主题");
  const previousCounts = countBy(previousNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "历史主题");
  const labels = Array.from(new Set([...Object.keys(recentCounts), ...Object.keys(previousCounts)]));
  const rows = labels
    .map((label) => {
      const candidates = recentNodes.filter((node) => compactThemeLabel(humanThemeLabel(node)) === label);
      const fallback = previousNodes.filter((node) => compactThemeLabel(humanThemeLabel(node)) === label);
      const recentCount = recentCounts[label] ?? 0;
      const previousCount = previousCounts[label] ?? 0;
      return {
        id: normalizeDisplayKey(label) || label,
        label,
        recentCount,
        previousCount,
        delta: recentCount - previousCount,
        intensity: 0,
        node: selectRepresentativeNode(candidates.length ? candidates : fallback),
      };
    })
    .filter((row) => row.recentCount > 0 || row.previousCount > 0)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta) || b.recentCount - a.recentCount || a.label.localeCompare(b.label, "zh-CN"))
    .slice(0, 6);
  const maxDelta = Math.max(1, ...rows.map((row) => Math.abs(row.delta)));
  const displayRows = rows.length
    ? rows
    : [{
        id: "no-river-pulse",
        label: "暂无近期主题变化",
        recentCount: 0,
        previousCount: 0,
        delta: 0,
        intensity: 18,
        node: null,
      }];
  return displayRows.map((row) => ({
    ...row,
    intensity: row.intensity || Math.max(12, Math.round((Math.abs(row.delta) / maxDelta) * 100)),
  }));
}

function buildHomeInspectorLinks(
  preferredNodes: Array<AtlasNode | null>,
  memoryNodes: AtlasNode[],
  graphEdges: AtlasEdge[],
): HomeInspectorLink[] {
  const degree = degreeMap(graphEdges);
  const rows = new Map<string, AtlasNode>();
  for (const node of preferredNodes) {
    if (node) rows.set(node.id, node);
  }
  for (const node of [...memoryNodes].sort((a, b) => homePreviewScore(b, degree) - homePreviewScore(a, degree))) {
    if (rows.size >= 4) break;
    rows.set(node.id, node);
  }
  if (!rows.size) {
    return [{
      id: "empty-inspector-link",
      title: "暂无可同步焦点",
      meta: "放宽筛选条件后可从首页直接打开详情。",
      node: null,
    }];
  }
  return Array.from(rows.values()).slice(0, 4).map((node) => ({
    id: node.id,
    title: humanNodeDisplayTitle(node),
    meta: `${normalizeMemoryTier(node.memory_tier)} / ${humanCategoryLabel(node.category)} / ${node.date || "未知日期"}`,
    node,
  }));
}

function isBlackHoleCandidate(node: AtlasNode): boolean {
  const stale = node.metrics?.roi?.staleness_status ?? "";
  return (
    stale.includes("stale") ||
    stale === "needs_review" ||
    node.category === "deprecated_info" ||
    node.category === "temporary_or_sensitive" ||
    normalizeMemoryTier(node.memory_tier) === "临时"
  );
}

function isProtoStarCandidate(node: AtlasNode, recentStart: Date, latest: Date): boolean {
  const leverage = node.metrics?.roi?.leverage_score ?? 0;
  const recent = isNodeBetween(node, recentStart, latest);
  return recent && (leverage >= 0.54 || node.category === "decision" || node.category === "project_context" || node.importance === "高");
}

function findDecliningTopicRows(
  recentNodes: AtlasNode[],
  olderComparableNodes: AtlasNode[],
): Array<{ label: string; count: number }> {
  const recentCounts = countBy(recentNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "未归类主题");
  const olderCounts = countBy(olderComparableNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "未归类主题");
  return Object.entries(olderCounts)
    .map(([label, count]) => ({ label, count: Math.max(0, count - (recentCounts[label] ?? 0)) }))
    .filter((row) => row.count > 0)
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "zh-CN"))
    .slice(0, 4);
}

function homeWeatherFor(
  deltaStats: DeltaStats,
  blackHoleCount: number,
  protoStarCount: number,
): { label: string; note: string; tone: HomeSignalCard["tone"] } {
  if (blackHoleCount > Math.max(12, protoStarCount * 2) && deltaStats.deltaCount < 0) {
    return {
      label: "风暴",
      note: "过时或临时信号偏多，且近期增量下降；先做压缩、降权和证据复核。",
      tone: "black-hole",
    };
  }
  if (protoStarCount >= 6 && deltaStats.deltaCount >= 0) {
    return {
      label: "新生云团",
      note: "近期机会和高杠杆记忆正在增加，适合转成项目、Skill 或下一步执行清单。",
      tone: "proto-star",
    };
  }
  if (deltaStats.deltaCount < 0) {
    return {
      label: "低温",
      note: "近期记忆增量低于上一周期，适合复盘停滞主题并清理不再有效的信息。",
      tone: "declining",
    };
  }
  return {
    label: "晴朗",
    note: "当前主题和增量相对稳定，可以从主导主题进入 ROI、时间线或 Summary 复核。",
    tone: "weather",
  };
}

function buildMemoryWeatherV2(
  memoryNodes: AtlasNode[],
  deltaStats: DeltaStats,
  staleNodes: AtlasNode[],
  protoStarNodes: AtlasNode[],
  topicRows: Array<{ label: string; count: number }>,
  decliningRows: Array<{ label: string; count: number }>,
): MemoryWeatherV2 {
  const total = Math.max(1, memoryNodes.length);
  const dominantShare = (topicRows[0]?.count ?? 0) / total;
  const rawMomentum = deltaStats.deltaRate === null
    ? deltaStats.deltaCount / Math.max(12, deltaStats.recentCount + deltaStats.previousCount)
    : deltaStats.deltaRate;
  const momentumScore = clamp(0.5 + rawMomentum * 0.42, 0, 1);
  const riskScore = clamp(staleNodes.length / Math.max(12, total * 0.08), 0, 1);
  const opportunityScore = clamp(protoStarNodes.length / Math.max(6, total * 0.035), 0, 1);
  const volatilityPenalty = clamp(Math.abs(deltaStats.deltaCount) / Math.max(18, deltaStats.recentCount + deltaStats.previousCount), 0, 0.65);
  const stabilityScore = clamp(0.72 + dominantShare * 0.16 - riskScore * 0.28 - volatilityPenalty, 0, 1);
  const confidenceScore = clamp(Math.log10(total + 10) / 3 + (deltaStats.latestDate ? 0.1 : 0), 0, 1);
  let label = "平稳晴朗";
  let tone: HomeSignalCard["tone"] = "weather";
  if (riskScore >= 0.72 && opportunityScore >= 0.72) {
    label = "高能高压";
    tone = "rising";
  } else if (riskScore >= 0.72 && momentumScore < 0.48) {
    label = "高压整理";
    tone = "black-hole";
  } else if (opportunityScore >= 0.72 && momentumScore >= 0.5) {
    label = "机会上升";
    tone = "proto-star";
  } else if (momentumScore < 0.38) {
    label = "低温收缩";
    tone = "declining";
  } else if (stabilityScore >= 0.68 && riskScore < 0.55) {
    label = "稳态上升";
    tone = "rising";
  }
  const dominant = topicRows[0]?.label ?? "暂无主导主题";
  const cooling = decliningRows[0]?.label ?? "无明显冷却主题";
  return {
    label,
    tone,
    stabilityScore,
    momentumScore,
    riskScore,
    opportunityScore,
    confidenceScore,
    summary: `${dominant} 是主导气候；风险 ${formatScore(riskScore)}，机会 ${formatScore(opportunityScore)}，稳定性 ${formatScore(stabilityScore)}。`,
    signals: [
      `delta ${formatSigned(deltaStats.deltaCount)} / latest ${deltaStats.latestDate || "unknown"}`,
      `${protoStarNodes.length.toLocaleString()} proto-star vs ${staleNodes.length.toLocaleString()} black-hole`,
      `cooling: ${cooling}`,
    ],
  };
}

function buildOpportunityItems(
  topicRows: Array<{ label: string; count: number }>,
  categoryRows: Array<{ label: string; count: number }>,
  deltaStats: DeltaStats,
): string[] {
  const items: string[] = [];
  const topicText = topicRows.map((row) => row.label).join(" / ");
  if (topicText.includes("记忆") || topicText.includes("RAG")) {
    items.push("把长期记忆库包装成所有 agent 的 RAG / personalization 入口，减少重复解释和上下文损耗。");
  }
  if (topicText.includes("Codex") || topicText.includes("agent") || topicText.includes("workflow")) {
    items.push("把高频 Codex 工作流产品化成可复用 Skill、Task Pack、验收脚本，提升每次开发 ROI。");
  }
  if (topicText.includes("金融") || topicText.includes("交易") || topicText.includes("概率")) {
    items.push("把金融、FIFA、概率决策沉淀为研究和风控仪表盘，优先服务 paper trading / 人审决策。");
  }
  if (topicText.includes("学习") || topicText.includes("Notion")) {
    items.push("把学习记录、Notion dashboard、周/月复盘打通，形成能力成长的可观察闭环。");
  }
  if (topicText.includes("工业") || topicText.includes("回转窑")) {
    items.push("工业服务方向可继续沉淀为测量、诊断、动态调整方案，适合形成行业化交付资产。");
  }
  if (categoryRows.some((row) => row.label.includes("项目上下文"))) {
    items.push("项目上下文占比较高，适合做项目索引和路线图，减少切换成本。");
  }
  if (deltaStats.recentDecisionCount > 0) {
    items.push("近期已有新决策，建议把对应行动项同步进下周执行清单。");
  }
  return items.slice(0, 4).length ? items.slice(0, 4) : ["先从最高密度主题做一次人工复盘，找出可产品化、可自动化、可投资研究的方向。"];
}

function buildSemanticInsights(nodes: AtlasNode[]): {
  topics: SemanticInsight[];
  tiers: string[];
  matrixRows: string[];
  matrix: Map<string, SemanticMatrixCell>;
  wordCloud: WordCloudItem[];
} {
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const topicMap = new Map<string, SemanticInsight>();
  const wordMap = new Map<string, WordCloudItem>();
  const latest = maxNodeDate(memoryNodes) ?? new Date();
  const recentStart = addDays(latest, -29);

  for (const node of memoryNodes) {
    const topic = compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category);
    const current = topicMap.get(topic) ?? { label: topic, count: 0, roiScore: 0, recentCount: 0, nodes: [] };
    current.count += 1;
    current.roiScore += node.metrics?.roi?.leverage_score ?? 0;
    if (isNodeBetween(node, recentStart, latest)) current.recentCount += 1;
    current.nodes.push(node);
    topicMap.set(topic, current);

    for (const token of semanticTokensForNode(node)) {
      const row = wordMap.get(token) ?? {
        label: token,
        count: 0,
        score: 0,
        x: 8 + stableUnit(token, "word-x") * 78,
        y: 8 + stableUnit(token, "word-y") * 76,
        rotate: stableUnit(token, "word-rotate") > 0.82 ? -8 + stableUnit(token, "word-tilt") * 16 : 0,
        nodes: [],
      };
      row.count += 1;
      row.score += 1 + (node.metrics?.roi?.leverage_score ?? 0);
      row.nodes.push(node);
      wordMap.set(token, row);
    }
  }

  const topics = Array.from(topicMap.values())
    .map((topic) => ({
      ...topic,
      roiScore: topic.count ? topic.roiScore / topic.count : 0,
    }))
    .sort((a, b) => b.count - a.count || b.roiScore - a.roiScore || a.label.localeCompare(b.label, "zh-CN"));
  const tiers = ["核心画像", "一般", "临时"].filter((tier) => memoryNodes.some((node) => normalizeMemoryTier(node.memory_tier) === tier));
  const safeTiers = tiers.length ? tiers : ["未分层"];
  const matrixRows = topics.slice(0, 8).map((topic) => topic.label);
  const matrix = new Map<string, SemanticMatrixCell>();
  for (const row of matrixRows) {
    for (const tier of safeTiers) {
      const cellNodes = (topicMap.get(row)?.nodes ?? []).filter((node) => normalizeMemoryTier(node.memory_tier) === tier);
      matrix.set(`${row}::${tier}`, { topic: row, tier, count: cellNodes.length, nodes: cellNodes });
    }
  }
  const wordCloud = Array.from(wordMap.values())
    .sort((a, b) => b.score - a.score || b.count - a.count || a.label.localeCompare(b.label, "zh-CN"))
    .slice(0, 42);

  return { topics, tiers: safeTiers, matrixRows, matrix, wordCloud };
}

function semanticTokensForNode(node: AtlasNode): string[] {
  const themeTokens = humanThemeLabel(node)
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean);
  const categoryTokens = [humanCategoryLabel(node.category), normalizeMemoryTier(node.memory_tier)].filter(Boolean);
  const textTokens = `${node.label} ${node.statement ?? ""}`
    .match(/[A-Za-z][A-Za-z0-9+_-]{2,}|[\u4e00-\u9fff]{2,8}/g)
    ?.map((token) => token.trim())
    .filter((token) => token.length >= 2 && !semanticStopwords.has(token.toLowerCase()))
    .slice(0, 8) ?? [];
  return Array.from(new Set([...themeTokens, ...categoryTokens, ...textTokens]))
    .map((token) => truncate(token.replace(/^(核心画像|一般|临时)\s*·\s*/, ""), 16))
    .filter((token) => token && !semanticStopwords.has(token.toLowerCase()));
}

const semanticStopwords = new Set([
  "静态图谱低敏摘要",
  "层级",
  "分类",
  "重要性",
  "有效期",
  "主题",
  "unknown",
  "memory",
  "一般短期",
  "重要中长期",
]);

function selectRepresentativeNode(nodes: AtlasNode[]): AtlasNode | null {
  return [...nodes].sort((a, b) => {
    const roi = (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0);
    if (roi !== 0) return roi;
    if ((b.importance === "高") !== (a.importance === "高")) return b.importance === "高" ? -1 : 1;
    return (b.date ?? "").localeCompare(a.date ?? "");
  })[0] ?? null;
}

function semanticHeatStyle(count: number, maxCount: number): CSSProperties {
  const level = count <= 0 ? 0 : Math.max(1, Math.min(5, Math.ceil((count / Math.max(1, maxCount)) * 5)));
  const color = heatColorForScore(count, maxCount, level);
  return {
    "--semantic-bg": count ? `linear-gradient(145deg, ${withAlpha(color, 0.72)}, ${color})` : "rgba(15, 17, 22, 0.9)",
    "--semantic-border": count ? withAlpha(color, 0.72) : "rgba(244, 241, 232, 0.08)",
  } as CSSProperties;
}

function semanticColor(index: number): string {
  const palette = ["#7ee8d4", "#8fd3ff", "#48c7e8", "#f48fb1", "#c7a7ff", "#6ea8ff", "#94a3b8"];
  return palette[index % palette.length];
}

function wordCloudStyle(item: WordCloudItem, maxScore: number): CSSProperties {
  const ratio = Math.min(1, Math.max(0.12, item.score / Math.max(1, maxScore)));
  const size = 11 + Math.sqrt(ratio) * 23;
  return {
    "--word-x": `${item.x}%`,
    "--word-y": `${item.y}%`,
    "--word-rotate": `${item.rotate}deg`,
    "--word-size": `${size}px`,
    "--word-color": heatColorForScore(item.score, maxScore, Math.ceil(ratio * 5)),
  } as CSSProperties;
}

function buildHumanNodeSummary(node: AtlasNode, edgeCount: number) {
  const theme = humanThemeLabel(node);
  const categoryLabel = humanCategoryLabel(node.category);
  const tier = normalizeMemoryTier(node.memory_tier);
  const continuityMemory = isMemoryContinuityNode(node, theme);
  const title = humanNodeTitle(node, theme, continuityMemory);
  const topics = splitHumanTopics(theme);
  const memoryType = tier !== "未分层" ? `${tier} / ${categoryLabel}` : categoryLabel;
  const status = humanMemoryStatus(node);
  return {
    title,
    subtitle: buildHumanNodeSubtitle(node, theme, continuityMemory),
    scope: `人类视图 · ${tier !== "未分层" ? tier : categoryLabel}`,
    meaning: buildMeaningBullets(node, theme, continuityMemory),
    impact: buildHumanImpact(node, edgeCount, continuityMemory),
    futureUse: buildFutureUseItems(node, continuityMemory),
    topics,
    statusRows: [
      { label: "记忆类型", value: memoryType },
      { label: "适用对象", value: continuityMemory ? "ChatGPT / Codex / 任意 Agent" : humanApplicableScope(node) },
      { label: "首次记录", value: node.date || "未知" },
      { label: "当前状态", value: status },
      { label: "关联数量", value: edgeCount.toLocaleString() },
      { label: "可信度", value: node.confidence || "未知" },
    ],
    agentMemory: buildAgentMemoryLine(node, title, continuityMemory),
    agentMeta: buildAgentMetaLine(node, theme, status),
  };
}

function recommendedActionForNode(node: AtlasNode): string {
  if (node.category === "answering_rule") return "作为未来回答和验收标准，执行前先检查。";
  if (node.category === "decision") return "作为已做出的选择，后续方案默认继承并记录影响。";
  if (node.category === "project_context") return "用于恢复项目背景，继续任务前先读关联项目和下一步。";
  if (node.category === "workflow") return "沉淀成可复用流程、Skill 或自动化检查。";
  if (node.category === "security_boundary") return "作为硬边界处理，涉及外部写入、交易、secret 时先确认。";
  if (node.category === "deprecated_info") return "保留历史轨迹，但回答时标明可能过时，避免当成当前事实。";
  if (node.category === "temporary_or_sensitive") return "低权重召回，只在当前任务相关时读取，不要污染长期画像。";
  const tier = normalizeMemoryTier(node.memory_tier);
  if (tier === "核心画像") return "优先进入 personalization，影响所有 agent 的默认行为。";
  if (tier === "一般") return "保留为一般上下文，用于项目连续性和决策复盘。";
  return "作为背景资料保留，必要时再展开。";
}

function isMemoryContinuityNode(node: AtlasNode, theme: string): boolean {
  const text = `${node.label} ${node.statement ?? ""} ${theme} ${node.visual?.cluster ?? ""}`.toLowerCase();
  return (
    text.includes("memory-rag-continuity") ||
    text.includes("长期记忆") ||
    text.includes("memory atlas") ||
    text.includes("openaidatabase") ||
    text.includes("rag") ||
    text.includes("personalization") ||
    text.includes("agent continuity")
  );
}

function humanNodeTitle(node: AtlasNode, theme?: string, continuityMemory = false): string {
  const compactTheme = compactThemeLabel(theme ?? humanThemeLabel(node));
  if (continuityMemory && node.category === "answering_rule") {
    return `回答规则：${compactTheme || "长期记忆库"}先于执行`;
  }
  if (node.category === "answering_rule") return `回答规则：${compactTheme || "交付标准"}`;
  if (node.category === "decision") return `决策：${compactTheme || "重要选择"}`;
  if (node.category === "project_context") return `项目背景：${compactTheme || "上下文"}`;
  if (node.category === "workflow") return `工作流：${compactTheme || "可复用流程"}`;
  if (node.category === "preference") return `偏好：${compactTheme || "判断标准"}`;
  if (node.category === "security_boundary") return `安全边界：${compactTheme || "高风险动作"}`;
  if (node.category === "deprecated_info") return `历史信息：${compactTheme || "默认低权重"}`;
  return node.label
    .replace(/^(核心画像|一般|临时|重要中长期|一般短期)\s*·\s*/, "")
    .replace(/\s*·\s*/g, " / ")
    .slice(0, 72);
}

function buildHumanNodeSubtitle(node: AtlasNode, theme: string, continuityMemory: boolean): string {
  if (continuityMemory) {
    return "这条记忆的重点不是数据库字段，而是让未来任何 agent 先理解你的画像、偏好、项目历史、决策标准和回答规则，再开始工作。";
  }
  if (node.kind !== "memory") {
    return "这是一个导航节点，用来把相关主题、项目、决策、时间线和记忆连接起来，帮助你从全局理解历史轨迹。";
  }
  if (node.category === "answering_rule") return "这是一条会影响未来回答方式和交付验收标准的长期规则。";
  if (node.category === "decision") return "这记录了一个已做出的选择，后续规划和 agent 执行应默认继承。";
  if (node.category === "project_context") return "这保存项目背景，目的是降低换线程、换 agent 或隔一段时间后继续工作的成本。";
  if (node.category === "preference") return "这记录你的偏好、taste 或判断标准，未来 personalization 应优先使用。";
  return `这条记忆和「${theme}」有关，适合用于复盘、搜索、上下文恢复和未来 agent 个性化。`;
}

function buildMeaningBullets(node: AtlasNode, theme: string, continuityMemory: boolean): string[] {
  if (continuityMemory) {
    return [
      "你不希望 AI 只记住设置页里很短的 personalization，而是要有完整、长期、可追溯的记忆数据库。",
      "ChatGPT、Codex 和未来任意 agent 都应能读取同一套画像、偏好、历史项目、决策标准和回答规则。",
      "前端默认展示人类能理解的结论、机会、建议和待办；完整原文和高敏内容只给授权 agent 读取。",
    ];
  }
  if (node.kind !== "memory") {
    return [
      `它把「${theme}」相关的记忆集中到同一个导航对象。`,
      "点击它的价值是快速找到相关历史、项目、决策和行为模式。",
    ];
  }
  if (node.category === "decision") {
    return [
      "这里记录的是已经做出的选择，不应在未来任务中反复重新讨论。",
      "后续 agent 应把它作为默认背景，并在新证据出现时再提出修改建议。",
    ];
  }
  if (node.category === "answering_rule") {
    return [
      "这里记录的是未来回答和交付方式需要遵守的规则。",
      "它的用途是提高回答稳定性，减少你重复纠正同类问题的次数。",
    ];
  }
  if (node.category === "project_context") {
    return [
      "这里保存的是项目背景、历史进展或上下文，不是一次性的聊天片段。",
      "它能帮助新线程、新 agent 或未来的你快速恢复任务状态。",
    ];
  }
  const cleanStatement = humanizeStatement(node.statement);
  return [
    cleanStatement || `这是一条关于「${theme}」的记忆，适合用于搜索、复盘和上下文恢复。`,
    recommendedActionForNode(node),
  ];
}

function buildHumanImpact(node: AtlasNode, edgeCount: number, continuityMemory: boolean): string {
  if (continuityMemory) {
    return "它直接影响所有未来 AI 协作质量：减少重复解释、降低上下文成本、提高项目接续能力，并让 agent 更接近长期了解你的工作伙伴。";
  }
  if (node.category === "answering_rule") return "它能减少重复纠错，让不同 agent 在回答风格、验收标准和执行边界上更一致。";
  if (node.category === "decision") return "它能避免重复决策，让后续计划沿着既定方向推进，同时保留未来修正的证据入口。";
  if (node.category === "project_context") return "它能降低项目切换成本，让历史背景、当前状态和下一步行动更容易被恢复。";
  if (node.category === "preference") return "它会影响未来 personalization，让回答更贴近你的 taste、偏好、风险边界和决策方式。";
  if (node.category === "security_boundary") return "它属于硬边界信息，能防止 agent 在外部写入、隐私、交易或 secret 场景里越权。";
  const connectionText = edgeCount ? `当前有 ${edgeCount.toLocaleString()} 个关联，` : "";
  return `${connectionText}它的价值在于帮助你看清反复出现的主题、行为习惯和潜在机会，而不是只作为后台索引。`;
}

function buildFutureUseItems(node: AtlasNode, continuityMemory: boolean): string[] {
  if (continuityMemory) {
    return [
      "新 agent 启动前先读取 Memory Atlas / OpenAIDatabase，再生成适配你的 profile、preference 和项目上下文。",
      "回答时优先遵守你的长期偏好、交付标准、历史决策和安全边界。",
      "发现新偏好、新规则或新项目决策时，先生成可审查、可回滚的 memory update candidate。",
    ];
  }
  if (node.category === "security_boundary") {
    return ["涉及外部写入、交易、secret、隐私或权限时先停下来确认。", "把它作为 agent 执行前的硬性检查项。"];
  }
  if (node.category === "workflow") {
    return ["把它沉淀成可复用 skill、Task Pack 或自动化检查。", "未来相似任务先套用这套流程，再根据新证据调整。"];
  }
  if (node.category === "deprecated_info") {
    return ["保留历史轨迹，但回答时明确它可能过时。", "如果新资料冲突，应以更新证据为准并生成修改提案。"];
  }
  return [recommendedActionForNode(node), "如果这条记忆影响未来回答，建议在下方写回提案里补充更清晰的人类结论。"];
}

function humanNodeDisplayTitle(node: AtlasNode): string {
  const theme = humanThemeLabel(node);
  return humanNodeTitle(node, theme, isMemoryContinuityNode(node, theme));
}

function buildSearchResultPreview(node: AtlasNode, duplicateCount: number): { title: string; summary: string; meta: string } {
  const theme = humanThemeLabel(node);
  const continuityMemory = isMemoryContinuityNode(node, theme);
  const title = humanNodeTitle(node, theme, continuityMemory);
  const summary = humanizeStatement(node.statement) || buildHumanNodeSubtitle(node, theme, continuityMemory);
  const meta = [
    normalizeMemoryTier(node.memory_tier),
    humanCategoryLabel(node.category),
    node.date || "未知日期",
    duplicateCount > 1 ? `已合并 ${duplicateCount.toLocaleString()} 条同类记录` : "",
  ].filter(Boolean).join(" / ");
  return { title, summary, meta };
}

function dedupeNodesForDisplay(nodes: AtlasNode[]): Array<{ node: AtlasNode; duplicateCount: number }> {
  const rows = new Map<string, { node: AtlasNode; duplicateCount: number }>();
  for (const node of nodes) {
    const title = humanNodeDisplayTitle(node);
    const theme = humanThemeLabel(node);
    const summary = humanizeStatement(node.statement);
    const keySource = node.category === "answering_rule"
      ? `${node.kind}|${node.category}|${normalizeMemoryTier(node.memory_tier)}|${theme}`
      : `${node.kind}|${node.category}|${title}|${summary || node.label}`;
    const key = normalizeDisplayKey(keySource);
    const current = rows.get(key);
    if (current) {
      current.duplicateCount += 1;
    } else {
      rows.set(key, { node, duplicateCount: 1 });
    }
  }
  return [...rows.values()];
}

function dedupeRecommendationItems(
  items: Array<{ id: string; title: string; statement: string; evidence_count?: number; reason?: string }>,
): Array<{ item: { id: string; title: string; statement: string; evidence_count?: number; reason?: string }; duplicateCount: number }> {
  const rows = new Map<string, { item: { id: string; title: string; statement: string; evidence_count?: number; reason?: string }; duplicateCount: number }>();
  for (const item of items) {
    const key = normalizeDisplayKey(`${humanizeRecommendationTitle(item.title)}|${humanizeStatement(item.statement)}`);
    const current = rows.get(key);
    if (current) {
      current.duplicateCount += 1;
      current.item.evidence_count = Math.max(current.item.evidence_count ?? 0, item.evidence_count ?? 0);
    } else {
      rows.set(key, { item, duplicateCount: 1 });
    }
  }
  return [...rows.values()];
}

function dedupeDisplayItems(items: string[], limit: number): string[] {
  const rows = new Map<string, { text: string; count: number }>();
  for (const item of items) {
    const key = normalizeDisplayKey(item);
    const current = rows.get(key);
    if (current) {
      current.count += 1;
    } else {
      rows.set(key, { text: item, count: 1 });
    }
  }
  return [...rows.values()].slice(0, limit).map((row) => (
    row.count > 1 ? `${row.text}（另有 ${row.count - 1} 条同类记录）` : row.text
  ));
}

function humanizeRecommendationTitle(value: string): string {
  return truncate(value
    .replace(/^(Memory|Meta Data)\s*·\s*/i, "")
    .replace(/answering_rule/g, "回答规则")
    .replace(/project_context/g, "项目上下文")
    .replace(/security_boundary/g, "安全边界")
    .replace(/temporary_or_sensitive/g, "短期/敏感背景")
    .replace(/\s*·\s*/g, " / "), 72);
}

function recommendationMeta(
  item: { evidence_count?: number },
  duplicateCount: number,
): string {
  const parts = [`证据 ${item.evidence_count ?? 0}`];
  if (duplicateCount > 1) parts.push(`合并 ${duplicateCount.toLocaleString()} 条同类`);
  return parts.join(" / ");
}

function splitHumanTopics(theme: string): string[] {
  return theme
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 8);
}

function humanMemoryStatus(node: AtlasNode): string {
  if (node.category === "deprecated_info") return "保留历史，默认不作为当前事实";
  if (node.validity === "临时") return "临时有效";
  if (node.validity === "项目结束前") return "项目期内有效";
  return "有效";
}

function humanApplicableScope(node: AtlasNode): string {
  if (node.category === "answering_rule") return "所有未来回答";
  if (node.category === "preference") return "Personalization / Profile";
  if (node.category === "project_context") return "相关项目和接续任务";
  if (node.category === "workflow") return "Codex / Agent 工作流";
  if (node.category === "security_boundary") return "所有高风险动作";
  return "搜索 / 复盘 / 相关 Agent";
}

function buildAgentMemoryLine(node: AtlasNode, title: string, continuityMemory: boolean): string {
  const prefix = continuityMemory ? "核心 personalization" : humanCategoryLabel(node.category);
  return `${prefix}：${title}。未来 agent 应把这条记忆用于画像、偏好、历史上下文或回答规则恢复；新增/修改/删除需走下方写回提案。`;
}

function buildAgentMetaLine(node: AtlasNode, theme: string, status: string): string {
  return [
    `层级=${normalizeMemoryTier(node.memory_tier)}`,
    `分类=${node.category || "未知"}`,
    `重要性=${node.importance || "未知"}`,
    `有效期=${node.validity || "未知"}`,
    `状态=${status}`,
    `主题=${theme}`,
  ].join("；");
}

function humanizeStatement(value: string | undefined): string {
  if (!value) return "";
  const withoutPrefix = value
    .replace(/^静态图谱低敏摘要[：:]\s*/, "")
    .replace(/层级=/g, "层级是")
    .replace(/分类=/g, "分类是")
    .replace(/重要性=/g, "重要性是")
    .replace(/有效期=/g, "有效期是")
    .replace(/主题=/g, "主题是");
  return truncate(withoutPrefix, 150);
}

function compactThemeLabel(value: string): string {
  return value
    .replace(/agent continuity/gi, "Agent 连续性")
    .replace(/agent/gi, "Agent")
    .replace(/workflow/gi, "工作流")
    .replace(/token/gi, "Token")
    .replace(/dashboard/gi, "仪表盘")
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 2)
    .join(" / ")
    .slice(0, 38);
}

function normalizeDisplayKey(value: string): string {
  return value
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[，。；：、/|·:;,.()[\]（）【】「」]/g, "")
    .trim();
}

function humanThemeLabel(node: AtlasNode): string {
  const cluster = node.visual?.cluster;
  if (cluster) return themeLabelFromCluster(cluster);
  const parts = node.label.split("·").map((part) => part.trim()).filter(Boolean);
  return parts[2] || node.category || normalizeMemoryTier(node.memory_tier) || translateKind(node.kind);
}

function themeLabelFromCluster(cluster: string): string {
  const labels: Record<string, string> = {
    "memory-rag-continuity": "长期记忆库 / RAG / Agent 连续性",
    "codex-agent-workflow": "Codex / Agent 工作流 / Token ROI",
    "learning-notion-nitrosend": "学习系统 / Notion / 仪表盘",
    "rotary-kiln-industrial": "回转窑 / 工业服务 / 动态测量调整",
    "finance-trading-probability": "金融 / 交易 / FIFA / 概率决策",
    "course-reporting": "课程 / 公司报告 / 可持续报告",
    "ai-era-growth": "AI 时代 / 社会影响 / 个人能力突破",
    "formal-engineering-delivery": "EVA OS / 系统开发 / Task Pack",
    uncategorized: "其他待人工归类主题",
  };
  return labels[cluster] ?? cluster;
}

function humanCategoryLabel(value: string | undefined): string {
  const labels: Record<string, string> = {
    answering_rule: "回答规则",
    codex_agent_metadata: "Codex agent 元数据",
    codex_development_record: "Codex 开发记录",
    codex_personalization: "Codex 个性化上下文",
    codex_usage_record: "Codex 使用记录",
    decision: "重要决策",
    deprecated_info: "历史/可能过时信息",
    fact: "事实资料",
    preference: "个人偏好",
    project_context: "项目上下文",
    security_boundary: "安全边界",
    temporary_or_sensitive: "短期/敏感背景",
    workflow: "工作流",
  };
  return labels[value ?? ""] ?? value ?? "未分类";
}

function countBy<T>(items: T[], getKey: (item: T) => string): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const key = getKey(item) || "未分类";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
}

function remapValues(values: Record<string, number>, mapKey: (key: string) => string): Record<string, number> {
  return Object.entries(values).reduce<Record<string, number>>((acc, [key, count]) => {
    const label = mapKey(key) || "未分类";
    acc[label] = (acc[label] ?? 0) + count;
    return acc;
  }, {});
}

function topRows(values: Record<string, number>, limit: number): Array<{ label: string; count: number }> {
  const rows = Object.entries(values)
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "zh-CN"))
    .slice(0, limit);
  return rows.length ? rows : [{ label: "暂无数据", count: 0 }];
}

function buildSearchVisualRows(nodes: AtlasNode[]): {
  topics: Array<{ label: string; count: number }>;
  tiers: Array<{ label: string; count: number }>;
  signals: Array<{ label: string; count: number }>;
} {
  const latest = maxNodeDate(nodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  return {
    topics: topRows(countBy(nodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)), 7),
    tiers: topRows(countBy(nodes, (node) => normalizeMemoryTier(node.memory_tier)), 4),
    signals: [
      { label: "近 30 天", count: nodes.filter((node) => isNodeBetween(node, recentStart, latest)).length },
      { label: "决策", count: nodes.filter((node) => node.category === "decision").length },
      { label: "核心画像", count: nodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length },
      { label: "待行动", count: nodes.filter((node) => /todo|action|执行|继续|需要|下一步/i.test(`${node.label} ${node.statement ?? ""}`)).length },
    ],
  };
}

function buildDataGuideLayout(nodes: AtlasNode[], edges: AtlasEdge[], limit: number): {
  frames: DataGuideFrame[];
  nodes: DataGuideNode[];
  edges: DataGuideEdge[];
  visibleNodeCount: number;
  edgeCount: number;
} {
  const degree = degreeMap(edges);
  const frameTemplates: Array<Omit<DataGuideFrame, "count">> = [
    buildDataGuideFrameTemplate("source", 36, 92, "#8fd3ff"),
    buildDataGuideFrameTemplate("profile", 276, 92, "#7ee8d4"),
    buildDataGuideFrameTemplate("project", 516, 92, "#f48fb1"),
    buildDataGuideFrameTemplate("action", 756, 92, "#94a3b8"),
  ];
  const framesById = new Map(frameTemplates.map((frame) => [frame.id, frame]));
  const frameBuckets = new Map<DataGuideFrameId, AtlasNode[]>();
  for (const frame of frameTemplates) frameBuckets.set(frame.id, []);

  const candidates = nodes
    .filter((node) => ["theme", "tier", "category", "project", "decision", "memory"].includes(node.kind))
    .sort((a, b) => dataGuideScore(b, degree) - dataGuideScore(a, degree) || (b.date ?? "").localeCompare(a.date ?? "") || a.label.localeCompare(b.label, "zh-CN"));
  for (const node of candidates) {
    frameBuckets.get(dataGuideFrameForNode(node))?.push(node);
  }

  const maxPerFrame = Math.max(8, Math.floor(limit / frameTemplates.length));
  const layoutNodes: DataGuideNode[] = [];
  for (const template of frameTemplates) {
    const bucket = frameBuckets.get(template.id) ?? [];
    const display = bucket.slice(0, maxPerFrame);
    const columns = 2;
    const gapX = 10;
    const gapY = 8;
    const cardW = (template.w - 34 - gapX) / columns;
    const cardH = 54;
    const startY = template.y + 78;
    display.forEach((node, index) => {
      const column = index % columns;
      const row = Math.floor(index / columns);
      const score = dataGuideScore(node, degree);
      layoutNodes.push({
        node,
        frameId: template.id,
        frameTitle: template.title,
        x: template.x + 14 + column * (cardW + gapX),
        y: startY + row * (cardH + gapY),
        w: cardW,
        h: cardH,
        color: dataGuideNodeColor(node, template.color),
        title: shortNodeLabel(node, 10),
        typeLabel: dataGuideTypeLabel(node),
        meta: dataGuideMetaLabel(node, degree.get(node.id) ?? 0),
        signalRadius: Math.min(8, 3 + Math.sqrt(Math.max(0, score)) * 0.48),
        score,
      });
    });
  }

  const byId = new Map(layoutNodes.map((node) => [node.node.id, node]));
  const layoutEdges = edges
    .map((edge): DataGuideEdge | null => {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target || source.frameId === target.frameId) return null;
      const left = source.x <= target.x ? source : target;
      const right = left === source ? target : source;
      return {
        id: edge.id,
        source,
        target,
        path: dataGuideEdgePath(left, right),
        color: right.color,
        strokeWidth: Math.max(0.9, Math.min(3.2, 0.8 + edge.weight * 1.4)),
        explanation: dataGuideRelationExplanation(edge, source, target),
      };
    })
    .filter((edge): edge is DataGuideEdge => Boolean(edge))
    .sort((a, b) => b.strokeWidth - a.strokeWidth)
    .slice(0, 130);

  const frames = frameTemplates.map((frame) => ({ ...frame, count: frameBuckets.get(frame.id)?.length ?? 0 }));
  return {
    frames,
    nodes: layoutNodes,
    edges: layoutEdges,
    visibleNodeCount: layoutNodes.length,
    edgeCount: layoutEdges.length,
  };
}

function buildDataGuideFrameTemplate(
  frameId: DataGuideFrameId,
  x: number,
  y: number,
  color: string,
): Omit<DataGuideFrame, "count"> {
  const layer = DATA_MAP_STRUCTURE_LAYERS.find((item) => item.frameId === frameId);
  if (!layer) throw new Error(`Unknown data guide frame: ${frameId}`);
  return {
    id: frameId,
    structureLayerId: layer.id,
    title: layer.title,
    subtitle: layer.subtitle,
    nodeTypes: layer.nodeTypes,
    fields: layer.fields,
    interaction: layer.interaction,
    detailEntry: layer.detailEntry,
    x,
    y,
    w: 214,
    h: 448,
    color,
  };
}

function dataGuideFrameForNode(node: AtlasNode): DataGuideFrameId {
  if (node.kind !== "memory") return "source";
  const tier = normalizeMemoryTier(node.memory_tier);
  if (tier === "核心画像" || node.category === "preference" || node.category === "answering_rule" || node.category === "security_boundary") {
    return "profile";
  }
  if (node.category === "decision" || node.category === "project_context" || node.category === "workflow") {
    return "project";
  }
  return "action";
}

function dataGuideScore(node: AtlasNode, degree: Map<string, number>): number {
  const tier = normalizeMemoryTier(node.memory_tier);
  const importance = node.importance === "高" ? 18 : node.importance === "中" ? 9 : 2;
  const tierScore = tier === "核心画像" ? 22 : tier === "一般" ? 11 : 4;
  const categoryScore = ["decision", "answering_rule", "project_context", "workflow", "preference"].includes(node.category ?? "") ? 18 : 0;
  const kindScore = node.kind === "theme" ? 24 : node.kind === "project" || node.kind === "decision" ? 18 : 0;
  const roi = (node.metrics?.roi?.leverage_score ?? 0) * 12;
  return (degree.get(node.id) ?? 0) * 2.2 + importance + tierScore + categoryScore + kindScore + roi;
}

function dataGuideNodeColor(node: AtlasNode, frameColor: string): string {
  if (node.kind !== "memory") return "#8fd3ff";
  if (node.category === "decision") return "#f48fb1";
  if (node.category === "security_boundary") return "#c7a7ff";
  if (normalizeMemoryTier(node.memory_tier) === "核心画像") return "#7ee8d4";
  return frameColor;
}

function dataGuideTypeLabel(node: AtlasNode): string {
  if (node.kind !== "memory") return translateKind(node.kind);
  const tier = normalizeMemoryTier(node.memory_tier);
  const category = humanCategoryLabel(node.category);
  return truncate(tier === "未分层" ? category : `${tier} · ${category}`, 13);
}

function dataGuideMetaLabel(node: AtlasNode, degree: number): string {
  const parts = [
    node.date ? node.date.slice(0, 10) : "",
    degree ? `${degree} 连` : "",
    node.importance ? `重要性${node.importance}` : "",
  ].filter(Boolean);
  return truncate(parts.join(" / ") || "结构节点", 16);
}

function dataGuideEdgePath(left: DataGuideNode, right: DataGuideNode): string {
  const x1 = left.x + left.w;
  const y1 = left.y + left.h / 2;
  const x2 = right.x;
  const y2 = right.y + right.h / 2;
  const dx = Math.max(54, (x2 - x1) * 0.45);
  return `M${x1} ${y1} C${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
}

function dataGuideRelationExplanation(edge: AtlasEdge, source: DataGuideNode, target: DataGuideNode): DataGuideRelationExplanation {
  const sourceNode = source.node;
  const targetNode = target.node;
  const strength = dataGuideRelationStrength(edge.weight);
  const time = dataGuideRelationTime(sourceNode, targetNode);
  const evidence = [
    `edge:${edge.id}`,
    `kind:${edge.kind || "related"}`,
    `weight:${edge.weight.toFixed(2)}`,
    `nodes:${sourceNode.id},${targetNode.id}`,
  ].join(" | ");
  const sourceLabel = shortNodeLabel(sourceNode, 18);
  const targetLabel = shortNodeLabel(targetNode, 18);
  const sourceDetail = [
    source.frameTitle,
    sourceNode.source_label || sourceNode.data_source || translateKind(sourceNode.kind),
    edge.kind || "related",
  ].filter(Boolean).join(" / ");

  return {
    source: sourceDetail,
    sourceLabel,
    targetLabel,
    strength,
    evidence,
    time,
    reason: `${source.frameTitle}「${sourceLabel}」连接到${target.frameTitle}「${targetLabel}」：${edge.kind || "related"} 关系，强度 ${strength}，证据来自当前 atlas edge 和两端节点。`,
  };
}

function dataGuideRelationStrength(weight: number): string {
  if (weight >= 0.78) return "高";
  if (weight >= 0.48) return "中";
  return "低";
}

function dataGuideRelationTime(source: AtlasNode, target: AtlasNode): string {
  const dates = [source.date, target.date].filter((date): date is string => Boolean(date)).sort();
  return dates.at(-1)?.slice(0, 10) || "time unavailable";
}

function buildDataMapNodeDetail(node: AtlasNode | null, edges: AtlasEdge[]): DataMapNodeDetail {
  if (!node) {
    return {
      asset: "未选择",
      theme: "未选择",
      suggestedAction: "未选择",
      importance: "未选择",
      priority: "未选择",
      status: "默认折叠",
      layerLabel: "默认折叠",
      summary: "点击节点后显示资产、主题、建议动作、重要性和优先级。",
      evidenceRefs: [],
    };
  }
  const asset = dataMapAssetLabelForNode(node);
  const theme = humanThemeLabel(node);
  const suggestedAction = translateAction(node.metrics?.roi?.recommended_action);
  const importance = node.importance || "未知";
  const priority = dataMapPriorityForNode(node);
  const status = [
    normalizeMemoryTier(node.memory_tier),
    humanCategoryLabel(node.category),
    node.metrics?.roi?.staleness_status ? translateStaleness(node.metrics.roi.staleness_status) : "",
  ].filter(Boolean).join(" / ") || translateKind(node.kind);
  const layerLabel = DATA_MAP_STRUCTURE_LAYERS.find((layer) => layer.frameId === dataGuideFrameForNode(node))?.label ?? "未归层";
  const evidenceRefs = dataMapEvidenceRefsForNode(node, edges);
  return {
    asset,
    theme,
    suggestedAction,
    importance,
    priority,
    status,
    layerLabel,
    summary: `${asset} 位于 ${theme}，建议动作是 ${suggestedAction}；重要性 ${importance}，优先级 ${priority}。`,
    evidenceRefs,
  };
}

function dataMapAssetLabelForNode(node: AtlasNode): string {
  if (node.kind === "theme") return "主题资产";
  if (node.kind === "project") return "项目资产";
  if (node.kind === "decision") return "决策资产";
  const tier = normalizeMemoryTier(node.memory_tier);
  const category = humanCategoryLabel(node.category);
  return [tier, category].filter(Boolean).join(" · ") || translateKind(node.kind);
}

function dataMapPriorityForNode(node: AtlasNode): "watch" | "p3" | "p2" | "p1" | "p0" {
  const leverage = node.metrics?.roi?.leverage_score ?? 0;
  if (node.importance === "高" && leverage >= 0.75) return "p0";
  if (node.importance === "高") return "p1";
  if (leverage >= 0.6) return "p2";
  if (node.metrics?.roi?.staleness_status === "stale" || node.validity === "stale" || node.category === "deprecated_info") return "watch";
  return "p3";
}

function dataMapEvidenceRefsForNode(node: AtlasNode, edges: AtlasEdge[]): string[] {
  const refs = edges
    .filter((edge) => edge.source === node.id || edge.target === node.id)
    .sort((a, b) => b.weight - a.weight || a.id.localeCompare(b.id))
    .slice(0, 6)
    .map((edge) => `${edge.kind || "related"}:${edge.id}:weight=${edge.weight.toFixed(2)}`);
  return refs.length ? refs : [`node:${node.id}:derived_snapshot`];
}

function buildMapLayout(nodes: AtlasNode[], edges: AtlasEdge[], limit: number): { nodes: LayoutNode[]; edges: LayoutEdge[]; groups: LayoutGroup[] } {
  const degree = degreeMap(edges);
  const themes = nodes.filter((node) => node.kind === "theme");
  const displayNodes = nodes
    .filter((node) => ["theme", "project", "decision", "memory"].includes(node.kind))
    .sort((a, b) => (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0))
    .slice(0, limit);
  const themeIds = new Map(themes.map((node, index) => [node.id.replace("theme:", ""), index]));
  const layoutNodes = displayNodes.map((node, index): LayoutNode => {
    const cluster = node.visual?.cluster ?? node.id.replace("theme:", "");
    const groupIndex = themeIds.get(cluster) ?? index % Math.max(themes.length, 1);
    const groupAngle = (groupIndex / Math.max(themes.length, 1)) * Math.PI * 2 - Math.PI / 2;
    const groupX = 500 + Math.cos(groupAngle) * 265;
    const groupY = 310 + Math.sin(groupAngle) * 205;
    const localAngle = stableUnit(node.id, "map-angle") * Math.PI * 2;
    const localRadius = node.kind === "theme" ? 0 : 28 + stableUnit(node.id, "map-radius") * 82;
    return {
      node,
      x: node.kind === "theme" ? groupX : groupX + Math.cos(localAngle) * localRadius,
      y: node.kind === "theme" ? groupY : groupY + Math.sin(localAngle) * localRadius,
      r: nodeRadius(node, degree.get(node.id) ?? 0),
      color: nodeColor(node),
      label: shortNodeLabel(node, node.kind === "theme" ? 20 : 12),
      degree: degree.get(node.id) ?? 0,
    };
  });
  const byId = new Map(layoutNodes.map((node) => [node.node.id, node]));
  const layoutEdges = edges
    .map((edge): LayoutEdge | null => {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target) return null;
      return { id: edge.id, source, target, weight: edge.weight, color: source.color };
    })
    .filter((edge): edge is LayoutEdge => Boolean(edge))
    .slice(0, 420);
  const groups = themes.map((theme, index): LayoutGroup => {
    const angle = (index / Math.max(themes.length, 1)) * Math.PI * 2 - Math.PI / 2;
    return {
      id: theme.id,
      label: shortNodeLabel(theme, 18),
      x: 500 + Math.cos(angle) * 265,
      y: 310 + Math.sin(angle) * 205,
      r: 112,
      color: nodeColor(theme),
    };
  });
  return { nodes: layoutNodes, edges: layoutEdges, groups };
}

function buildObsidianLayout(
  nodes: AtlasNode[],
  edges: AtlasEdge[],
  selectedNode: AtlasNode | null,
  localOnly: boolean,
  depth: number,
): { nodes: LayoutNode[]; edges: LayoutEdge[] } {
  const visibleIds = localOnly && selectedNode ? expandGraphIds(selectedNode.id, edges, depth) : new Set(nodes.map((node) => node.id));
  const filteredNodes = nodes
    .filter((node) => visibleIds.has(node.id))
    .sort((a, b) => kindRank(a.kind) - kindRank(b.kind))
    .slice(0, 220);
  const filteredNodeIds = new Set(filteredNodes.map((node) => node.id));
  const filteredEdges = edges.filter((edge) => filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)).slice(0, 650);
  const degree = degreeMap(filteredEdges);
  const count = filteredNodes.length || 1;
  const layoutNodes = filteredNodes.map((node, index): LayoutNode => {
    const clusterSeed = clusterIndex(node);
    const ring = node.kind === "theme" ? 120 : node.kind === "memory" ? 225 : 175;
    const angle = (index / count) * Math.PI * 2 + clusterSeed * 0.38;
    const jitter = (stableUnit(node.id, "obsidian-radius") - 0.5) * 72;
    return {
      node,
      x: 500 + Math.cos(angle) * (ring + jitter),
      y: 300 + Math.sin(angle) * (ring * 0.72 + jitter * 0.45),
      r: nodeRadius(node, degree.get(node.id) ?? 0),
      color: nodeColor(node),
      label: (degree.get(node.id) ?? 0) > 6 || node.kind !== "memory" ? shortNodeLabel(node, 14) : "",
      degree: degree.get(node.id) ?? 0,
    };
  });
  const byId = new Map(layoutNodes.map((node) => [node.node.id, node]));
  const layoutEdges = filteredEdges
    .map((edge): LayoutEdge | null => {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target) return null;
      return { id: edge.id, source, target, weight: edge.weight, color: edge.kind === "belongs_to_theme" ? target.color : "rgba(244,241,232,0.7)" };
    })
    .filter((edge): edge is LayoutEdge => Boolean(edge));
  return { nodes: layoutNodes, edges: layoutEdges };
}

function parseTimelineUtcDay(value: string | undefined): Date | null {
  return parseDay(value);
}

function timelineUtcMs(day: Date): number {
  return Date.UTC(day.getUTCFullYear(), day.getUTCMonth(), day.getUTCDate());
}

function buildTimelineLayout(timeline: TimelineEvent[], nodeMap: Map<string, AtlasNode>, controls: TimelineLayoutControls) {
  const allEvents = timeline
    .map((event) => ({ source: event, day: parseTimelineUtcDay(event.date), node: nodeMap.get(event.node_id) }))
    .filter((event): event is { source: TimelineEvent; day: Date; node: AtlasNode | undefined } => Boolean(event.day))
    .sort((a, b) => timelineUtcMs(a.day) - timelineUtcMs(b.day));
  const minAllDay = allEvents[0]?.day ?? new Date();
  const maxAllDay = allEvents[allEvents.length - 1]?.day ?? minAllDay;
  const minAllMs = timelineUtcMs(minAllDay);
  const maxAllMs = timelineUtcMs(maxAllDay);
  const totalSpan = Math.max(1, maxAllMs - minAllMs);
  const zoom = Math.min(8, Math.max(1, controls.zoom || 1));
  const visibleSpan = Math.max(1, totalSpan / zoom);
  const rawCenter = minAllMs + totalSpan * Math.min(1, Math.max(0, controls.center));
  const minWindow = minAllMs;
  const maxWindow = maxAllMs;
  const unclampedStart = rawCenter - visibleSpan / 2;
  const windowStartMs = Math.max(minWindow, Math.min(Math.max(minWindow, maxWindow - visibleSpan), unclampedStart));
  const windowEndMs = Math.min(maxWindow, windowStartMs + visibleSpan);
  const minDay = new Date(windowStartMs);
  const maxDay = new Date(windowEndMs);
  const span = Math.max(1, windowEndMs - windowStartMs);
  const cursor = Math.min(1, Math.max(0, controls.cursor));
  const cursorMs = windowStartMs + span * cursor;
  const visibleEvents = allEvents
    .filter((event) => timelineUtcMs(event.day) >= windowStartMs && timelineUtcMs(event.day) <= windowEndMs)
    .slice(-260);
  const laneKeys = uniqueSorted(visibleEvents.map((event) => normalizeMemoryTier(event.source.memory_tier) || event.source.category)).slice(0, 7);
  const lanes = laneKeys.map((key, index) => ({
    key,
    label: translateTierOrKind(key),
    y: 95 + index * (410 / Math.max(laneKeys.length - 1, 1)),
    color: laneColor(key, index),
  }));
  const laneMap = new Map(lanes.map((lane) => [lane.key, lane]));
  const ticks = buildMonthTicks(minDay, maxDay, MEMORY_RIVER_MIN_X, MEMORY_RIVER_MAX_X);
  const eventTicks = buildEventDateTicks(visibleEvents, minDay, maxDay, MEMORY_RIVER_MIN_X, MEMORY_RIVER_MAX_X);
  const densityBands = buildTimelineDensityBands(allEvents, minAllDay, maxAllDay, windowStartMs, windowEndMs);
  const densityBars = buildTimelineDensityBackdrops(visibleEvents, minDay, maxDay);
  const importantCount = visibleEvents.filter((event) => event.source.importance === "高" || event.source.category === "decision").length;
  const coreCount = visibleEvents.filter((event) => normalizeMemoryTier(event.source.memory_tier) === "核心画像").length;
  return {
    lanes,
    ticks,
    eventTicks,
    densityBands,
    densityBars,
    rangeLabel: `${formatAxisDate(minDay)} - ${formatAxisDate(maxDay)}`,
    cursorLabel: formatAxisDate(new Date(cursorMs)),
    cursorX: MEMORY_RIVER_MIN_X + cursor * MEMORY_RIVER_WIDTH,
    windowStartMs,
    windowEndMs,
    totalCount: allEvents.length,
    visibleCount: visibleEvents.length,
    importantCount,
    coreCount,
    peakDensity: Math.max(0, ...densityBands.map((band) => band.count)),
    events: visibleEvents.map((event, index) => {
      const lane = laneMap.get(normalizeMemoryTier(event.source.memory_tier) || event.source.category) ?? lanes[index % Math.max(lanes.length, 1)];
      const eventMs = timelineUtcMs(event.day);
      const x = MEMORY_RIVER_MIN_X + ((eventMs - timelineUtcMs(minDay)) / span) * MEMORY_RIVER_WIDTH;
      const major = event.source.importance === "高" || event.source.category === "decision" || index % 11 === 0;
      return {
        id: `${event.source.date}-${event.source.node_id}-${event.source.memory_id || index}`,
        source: event.source,
        node: event.node,
        day: event.day,
        utcDate: toDayKey(event.day),
        x,
        y: lane?.y ?? 300,
        radius: event.source.importance === "高" ? 9 : event.source.category === "decision" ? 8 : 5,
        color: event.node ? nodeColor(event.node) : lane?.color ?? "#94a3b8",
        major,
        future: eventMs > cursorMs,
        shortLabel: truncate(event.source.label, 18),
      };
    }),
  };
}

function getInitialTimelineFeedbackSettings(): TimelineFeedbackSettings {
  const reducedMotion = typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const defaults: TimelineFeedbackSettings = { reducedMotion: Boolean(reducedMotion), pseudoHaptic: false, audio: false };
  if (typeof window === "undefined") return defaults;
  try {
    const stored = window.localStorage.getItem(TIMELINE_FEEDBACK_SETTINGS_KEY);
    if (!stored) return defaults;
    const parsed = JSON.parse(stored) as Partial<TimelineFeedbackSettings>;
    return {
      reducedMotion: Boolean(parsed.reducedMotion ?? defaults.reducedMotion),
      pseudoHaptic: Boolean(parsed.pseudoHaptic),
      audio: Boolean(parsed.audio),
    };
  } catch {
    return defaults;
  }
}

function persistTimelineFeedbackSettings(settings: TimelineFeedbackSettings): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(TIMELINE_FEEDBACK_SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    // Preference persistence is best-effort for locked-down local previews.
  }
}

function timelineRangeSummary(range: TimelineTimeRangeSelection | null): string | null {
  if (!range) return null;
  return `时间河选择 ${range.label} · ${range.eventCount.toLocaleString()} 事件 · ${range.topTheme}`;
}

function memoryRiverPointerX(event: PointerEvent<SVGSVGElement>): number {
  const rect = event.currentTarget.getBoundingClientRect();
  const ratio = rect.width > 0 ? (event.clientX - rect.left) / rect.width : 0;
  return clampMemoryRiverX(ratio * 1000);
}

function clampMemoryRiverX(value: number): number {
  return Math.min(MEMORY_RIVER_MAX_X, Math.max(MEMORY_RIVER_MIN_X, value));
}

function memoryRiverXToRatio(x: number): number {
  return Math.min(1, Math.max(0, (clampMemoryRiverX(x) - MEMORY_RIVER_MIN_X) / MEMORY_RIVER_WIDTH));
}

function memoryRiverDateAtX(display: ReturnType<typeof buildTimelineLayout>, x: number): Date {
  const ratio = memoryRiverXToRatio(x);
  return new Date(display.windowStartMs + (display.windowEndMs - display.windowStartMs) * ratio);
}

function memoryRiverXForUtcMs(display: ReturnType<typeof buildTimelineLayout>, utcMs: number): number {
  const span = Math.max(1, display.windowEndMs - display.windowStartMs);
  return MEMORY_RIVER_MIN_X + ((utcMs - display.windowStartMs) / span) * MEMORY_RIVER_WIDTH;
}

function buildTimelineRangeSelection(
  display: ReturnType<typeof buildTimelineLayout>,
  startX: number,
  endX: number,
): TimelineTimeRangeSelection | null {
  const left = clampMemoryRiverX(Math.min(startX, endX));
  const right = clampMemoryRiverX(Math.max(startX, endX));
  if (right - left < 14) return null;
  const startDate = memoryRiverDateAtX(display, left);
  const endDate = memoryRiverDateAtX(display, right);
  const startKey = toDayKey(startDate);
  const endKey = toDayKey(endDate);
  const events = display.events.filter((event) => event.utcDate >= startKey && event.utcDate <= endKey);
  const topTheme = topRows(countBy(events, (event) => event.node ? compactThemeLabel(humanThemeLabel(event.node)) || "未归类主题" : "未归类主题"), 1)[0]?.label ?? "暂无主题";
  return {
    id: `memory-river-brush-${startKey}-${endKey}-${stableHash(`${startKey}:${endKey}:${events.length}`)}`,
    source: "memory-river-brush",
    startDate: startKey,
    endDate: endKey,
    label: `${formatAxisDate(startDate)} - ${formatAxisDate(endDate)}`,
    eventCount: events.length,
    decisionCount: events.filter((event) => event.source.category === "decision").length,
    coreMemoryCount: events.filter((event) => normalizeMemoryTier(event.source.memory_tier) === "核心画像").length,
    topTheme,
  };
}

function buildMemoryRiverRangeOverlay(range: TimelineTimeRangeSelection | null, display: ReturnType<typeof buildTimelineLayout>) {
  if (!range) return null;
  const startDay = parseTimelineUtcDay(range.startDate);
  const endDay = parseTimelineUtcDay(range.endDate);
  if (!startDay || !endDay) return null;
  const startX = memoryRiverXForUtcMs(display, timelineUtcMs(startDay));
  const endX = memoryRiverXForUtcMs(display, timelineUtcMs(endDay));
  if (endX < MEMORY_RIVER_MIN_X || startX > MEMORY_RIVER_MAX_X) return null;
  const x = clampMemoryRiverX(Math.min(startX, endX));
  const right = clampMemoryRiverX(Math.max(startX, endX));
  const width = Math.max(3, right - x);
  return { x, width, labelX: x + width / 2, label: `${range.label} · ${range.eventCount}` };
}

function buildMemoryRiverDraftOverlay(draft: TimelineBrushDraft) {
  const x = clampMemoryRiverX(Math.min(draft.startX, draft.endX));
  const right = clampMemoryRiverX(Math.max(draft.startX, draft.endX));
  return { x, width: Math.max(3, right - x) };
}

function emitTimelineFeedback(settings: TimelineFeedbackSettings, kind: "pan" | "brush" | "event"): void {
  if (settings.reducedMotion) return;
  if (settings.pseudoHaptic && typeof navigator !== "undefined" && navigator.vibrate) {
    navigator.vibrate(kind === "brush" ? [8, 24, 8] : 10);
  }
  if (!settings.audio || typeof window === "undefined" || typeof window.AudioContext === "undefined") return;
  try {
    const context = new window.AudioContext();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.frequency.value = kind === "event" ? 660 : kind === "brush" ? 520 : 390;
    gain.gain.value = 0.018;
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start();
    window.setTimeout(() => {
      oscillator.stop();
      void context.close();
    }, 55);
  } catch {
    // Optional audio feedback must never break the visualization.
  }
}

function buildMemoryRiverLayout(events: TimelineDisplayEvent[], cursorX: number): MemoryRiverLayout {
  const levelSpecs: Array<MemoryRiverLevelBand & { maxLanes: number }> = [
    { level: "Macro", note: "层级 / 长期记忆气候", y: 118, maxLanes: 3 },
    { level: "Meso", note: "主题 / 项目迁移", y: 294, maxLanes: 4 },
    { level: "Micro", note: "分类 / 事件波纹", y: 464, maxLanes: 4 },
  ];
  const levelCounts: Record<MemoryRiverLevel, number> = { Macro: 0, Meso: 0, Micro: 0 };
  const lanes: MemoryRiverLane[] = [];
  const laneLookup = new Map<string, MemoryRiverLane>();

  for (const spec of levelSpecs) {
    const buckets = new Map<string, { key: string; label: string; events: TimelineDisplayEvent[]; score: number }>();
    for (const event of events) {
      const group = memoryRiverGroup(event, spec.level);
      const bucket = buckets.get(group.key) ?? { key: group.key, label: group.label, events: [], score: 0 };
      bucket.events.push(event);
      bucket.score += memoryRiverEventScore(event);
      buckets.set(group.key, bucket);
    }
    levelCounts[spec.level] = buckets.size;
    const selected = Array.from(buckets.values())
      .sort((a, b) => b.events.length - a.events.length || b.score - a.score || a.label.localeCompare(b.label, "zh-CN"))
      .slice(0, spec.maxLanes);
    const spacing = selected.length > 1 ? Math.min(42, 98 / Math.max(1, selected.length - 1)) : 0;
    selected.forEach((bucket, index) => {
      const y = spec.y + (index - (selected.length - 1) / 2) * spacing;
      const color = memoryRiverLaneColor(bucket.key, spec.level, index);
      const strokeWidth = Math.max(8, Math.min(34, 7 + Math.log1p(bucket.events.length) * 9 + bucket.score * 0.03));
      const lane: MemoryRiverLane = {
        id: `river-${spec.level.toLowerCase()}-${stableHash(`${spec.level}:${bucket.key}`)}`,
        groupKey: bucket.key,
        level: spec.level,
        label: truncate(bucket.label, spec.level === "Macro" ? 16 : 18),
        count: bucket.events.length,
        path: buildMemoryRiverPath(bucket.events, y),
        color,
        gradientId: `memory-river-gradient-${spec.level.toLowerCase()}-${index}-${stableHash(bucket.key)}`,
        strokeWidth,
        labelX: Math.max(96, Math.min(820, bucket.events[0]?.x ?? 120)),
        labelY: y - Math.max(14, strokeWidth / 2 + 7),
        y,
      };
      lanes.push(lane);
      laneLookup.set(`${spec.level}:${bucket.key}`, lane);
    });
  }

  const markerEvents = events
    .filter((event) => event.major || event.source.importance === "高" || ["decision", "deprecated_info", "temporary_or_sensitive"].includes(event.source.category))
    .sort((a, b) => timelineUtcMs(a.day) - timelineUtcMs(b.day))
    .slice(-64);
  const markers = markerEvents.map((event): MemoryRiverMarker => {
    const level = memoryRiverMarkerLevel(event);
    const group = memoryRiverGroup(event, level);
    const lane = laneLookup.get(`${level}:${group.key}`) ?? lanes.find((candidate) => candidate.level === level) ?? lanes[0];
    const kind = memoryRiverMarkerKind(event);
    return {
      id: `river-marker-${event.id}`,
      kind,
      event,
      title: `${event.utcDate} UTC · ${kind === "black-hole" ? "Black Hole" : kind === "proto-star" ? "Proto-Star" : "Memory Event"} · ROI ${formatScore(event.node?.metrics?.roi?.leverage_score)} · ${event.source.label}`,
      x: Math.max(86, Math.min(954, event.x)),
      y: (lane?.y ?? 300) + (stableUnit(`${event.id}:${level}`, "memory-river-marker-y") - 0.5) * 26,
      radius: kind === "black-hole" ? Math.max(6, event.radius + 2) : kind === "proto-star" ? Math.max(5, event.radius + 1) : event.radius,
    };
  });
  const visibleLanes = lanes.length ? lanes : buildEmptyMemoryRiverLanes(levelSpecs, cursorX);
  const evidenceLayers = buildMemoryRiverEvidenceLayers(events, laneLookup, visibleLanes);
  const roiGradient = buildMemoryRiverRoiGradient(events);

  return {
    levels: levelSpecs.map(({ level, note, y }) => ({ level, note, y })),
    lanes: visibleLanes,
    evidenceLayers,
    roiGradient,
    markers,
    levelCounts,
  };
}

function buildMemoryRiverRoiGradient(events: TimelineDisplayEvent[]): MemoryRiverRoiGradient {
  const bandCount = 12;
  const bandWidth = MEMORY_RIVER_WIDTH / bandCount;
  const bands: MemoryRiverRoiGradientBand[] = [];
  const scoredEvents = events.map((event) => ({
    event,
    roi: event.node?.metrics?.roi?.leverage_score ?? 0,
    capability: isCapabilityGrowthEvent(event),
  }));
  for (let index = 0; index < bandCount; index += 1) {
    const x = MEMORY_RIVER_MIN_X + index * bandWidth;
    const right = x + bandWidth;
    const inBand = scoredEvents.filter(({ event }) => event.x >= x && event.x < right);
    const averageRoi = inBand.length ? inBand.reduce((sum, item) => sum + item.roi, 0) / inBand.length : 0;
    const capabilityCount = inBand.filter((item) => item.capability).length;
    const score = clamp(averageRoi * 0.74 + Math.min(1, capabilityCount / 4) * 0.26, 0, 1);
    bands.push({
      id: `roi-gradient-${index}`,
      x: x + 1,
      y: 112,
      width: Math.max(2, bandWidth - 2),
      height: 402,
      score,
      color: roiGradientColor(score),
      label: `${index + 1}/${bandCount} · ROI ${formatScore(averageRoi)} · capability ${capabilityCount.toLocaleString()}`,
    });
  }
  const averageRoiScore = scoredEvents.length ? scoredEvents.reduce((sum, item) => sum + item.roi, 0) / scoredEvents.length : 0;
  const highLeverageCount = scoredEvents.filter((item) => item.roi >= 0.54).length;
  const capabilityGrowthCount = scoredEvents.filter((item) => item.capability).length;
  return {
    label: `ROI gradient · avg ${formatScore(averageRoiScore)}`,
    signal: `${highLeverageCount.toLocaleString()} high leverage / ${capabilityGrowthCount.toLocaleString()} capability-growth events`,
    averageRoiScore,
    highLeverageCount,
    capabilityGrowthCount,
    bands,
  };
}

function isCapabilityGrowthEvent(event: TimelineDisplayEvent): boolean {
  const roi = event.node?.metrics?.roi?.leverage_score ?? 0;
  const text = `${event.source.label} ${event.node?.statement ?? ""}`;
  return roi >= 0.54 || event.source.category === "decision" || event.source.category === "project_context" || /机会|增长|下一步|能力|capability|workflow/i.test(text);
}

function roiGradientColor(score: number): string {
  if (score >= 0.72) return `rgba(126, 232, 212, ${0.11 + score * 0.12})`;
  if (score >= 0.48) return `rgba(143, 211, 255, ${0.09 + score * 0.1})`;
  if (score > 0) return `rgba(199, 167, 255, ${0.07 + score * 0.08})`;
  return "rgba(244, 241, 232, 0.025)";
}

function buildMemoryRiverEvidenceLayers(
  events: TimelineDisplayEvent[],
  laneLookup: Map<string, MemoryRiverLane>,
  lanes: MemoryRiverLane[],
): MemoryRiverEvidenceLayer[] {
  if (!events.length) return [];
  const latest = events.reduce((max, event) => Math.max(max, timelineUtcMs(event.day)), 0);
  const latestDay = latest > 0 ? new Date(latest) : new Date();
  const recentStart = addDays(latestDay, -29);
  const blackHoleEvents = events.filter(isMemoryRiverBlackHoleEvent);
  const protoStarEvents = events.filter((event) => isMemoryRiverProtoStarEvent(event, recentStart, latestDay));
  const staleEvents = events.filter(isMemoryRiverStaleDeprecatedEvent);
  return [
    buildBlackHoleLifecycleLayer(blackHoleEvents, laneLookup, lanes),
    buildProtoStarLifecycleLayer(protoStarEvents, laneLookup, lanes),
    buildStaleDeprecatedLayer(staleEvents),
  ].filter((layer): layer is MemoryRiverEvidenceLayer => Boolean(layer));
}

function buildBlackHoleLifecycleLayer(
  events: TimelineDisplayEvent[],
  laneLookup: Map<string, MemoryRiverLane>,
  lanes: MemoryRiverLane[],
): MemoryRiverEvidenceLayer | null {
  const sorted = [...events].sort((a, b) => a.x - b.x);
  if (!sorted.length) return null;
  const range = memoryRiverEvidenceRange(sorted, 46);
  const y = 500;
  const width = Math.max(44, range.endX - range.startX);
  const peak = sorted[Math.max(0, sorted.length - 1)];
  const microLane = laneForMemoryRiverEvent(peak, "Micro", laneLookup, lanes);
  return {
    id: "memory-river-black-hole-lifecycle",
    kind: "black-hole-lifecycle",
    label: `黑洞生命周期 · ${sorted.length}`,
    detail: "与首页风险循环一致：stale / needs_review / deprecated / 临时低权重信号",
    startX: range.startX,
    endX: range.endX,
    labelX: Math.min(900, range.startX + width / 2),
    labelY: y - 12,
    count: sorted.length,
    path: `M ${range.startX} ${y + 28} C ${range.startX + width * 0.28} ${y + 6}, ${range.endX - width * 0.24} ${y + 50}, ${range.endX} ${y + 22}`,
    points: sorted.slice(-6).map((event, index) => ({
      id: `black-hole-point-${event.id}`,
      x: Math.max(MEMORY_RIVER_MIN_X, Math.min(MEMORY_RIVER_MAX_X, event.x)),
      y: (microLane?.y ?? y) + (index % 2 ? 18 : -10),
      radius: Math.max(4.5, Math.min(9, event.radius + 1.5)),
      label: `${event.utcDate} UTC · 黑洞增强 · ${event.source.label}`,
    })),
    segments: [
      {
        id: "black-hole-band",
        x: range.startX,
        y,
        width,
        height: 42,
        label: `低价值循环从 ${sorted[0].utcDate} 到 ${sorted[sorted.length - 1].utcDate} 可见增强`,
        strength: Math.min(1, sorted.length / 8),
      },
    ],
  };
}

function buildProtoStarLifecycleLayer(
  events: TimelineDisplayEvent[],
  laneLookup: Map<string, MemoryRiverLane>,
  lanes: MemoryRiverLane[],
): MemoryRiverEvidenceLayer | null {
  const sorted = [...events].sort((a, b) => a.x - b.x).slice(-10);
  if (!sorted.length) return null;
  const points = sorted.map((event, index) => {
    const lane = laneForMemoryRiverEvent(event, "Meso", laneLookup, lanes);
    return {
      id: `proto-star-point-${event.id}`,
      x: Math.max(MEMORY_RIVER_MIN_X, Math.min(MEMORY_RIVER_MAX_X, event.x)),
      y: (lane?.y ?? 294) + (index % 2 ? -22 : 20),
      radius: Math.max(4.5, Math.min(8.5, event.radius + 1)),
      label: `${event.utcDate} UTC · 机会成长 · ${event.source.label}`,
    };
  });
  const range = memoryRiverEvidenceRange(sorted, 34);
  return {
    id: "memory-river-proto-star-lifecycle",
    kind: "proto-star-lifecycle",
    label: `机会生命周期 · ${sorted.length}`,
    detail: "decision / project_context / high-leverage / 高重要信号形成增长路径",
    startX: range.startX,
    endX: range.endX,
    labelX: Math.min(900, range.startX + Math.max(48, range.endX - range.startX) / 2),
    labelY: 224,
    count: sorted.length,
    path: memoryRiverEvidencePath(points),
    points,
    segments: [],
  };
}

function buildStaleDeprecatedLayer(events: TimelineDisplayEvent[]): MemoryRiverEvidenceLayer | null {
  const sorted = [...events].sort((a, b) => a.x - b.x).slice(-18);
  if (!sorted.length) return null;
  const range = memoryRiverEvidenceRange(sorted, 38);
  const segments = sorted.map((event, index) => ({
    id: `stale-fade-${event.id}`,
    x: Math.max(MEMORY_RIVER_MIN_X, Math.min(MEMORY_RIVER_MAX_X - 18, event.x - 9)),
    y: 405 + (index % 3) * 16,
    width: 24 + Math.min(34, event.radius * 3),
    height: 86 - (index % 3) * 10,
    label: `${event.utcDate} UTC · 冷却/废弃 · ${event.source.label}`,
    strength: Math.min(1, 0.35 + index / Math.max(1, sorted.length)),
  }));
  return {
    id: "memory-river-stale-deprecated-layer",
    kind: "stale-deprecated",
    label: `冷却/废弃层 · ${sorted.length}`,
    detail: "stale_short_term / deprecated_info / temporary_or_sensitive 仅作为可读冷却状态显示",
    startX: range.startX,
    endX: range.endX,
    labelX: Math.min(900, range.startX + Math.max(48, range.endX - range.startX) / 2),
    labelY: 392,
    count: sorted.length,
    points: [],
    segments,
  };
}

function laneForMemoryRiverEvent(
  event: TimelineDisplayEvent,
  level: MemoryRiverLevel,
  laneLookup: Map<string, MemoryRiverLane>,
  lanes: MemoryRiverLane[],
): MemoryRiverLane | undefined {
  const group = memoryRiverGroup(event, level);
  return laneLookup.get(`${level}:${group.key}`) ?? lanes.find((lane) => lane.level === level);
}

function memoryRiverEvidenceRange(events: TimelineDisplayEvent[], minWidth: number): { startX: number; endX: number } {
  const xs = events.map((event) => Math.max(MEMORY_RIVER_MIN_X, Math.min(MEMORY_RIVER_MAX_X, event.x))).sort((a, b) => a - b);
  const left = xs[0] ?? MEMORY_RIVER_MIN_X;
  const right = xs[xs.length - 1] ?? left;
  const midpoint = (left + right) / 2;
  const half = Math.max(minWidth / 2, (right - left) / 2);
  return {
    startX: Math.max(MEMORY_RIVER_MIN_X, midpoint - half),
    endX: Math.min(MEMORY_RIVER_MAX_X, midpoint + half),
  };
}

function memoryRiverEvidencePath(points: MemoryRiverEvidencePoint[]): string | undefined {
  if (!points.length) return undefined;
  if (points.length === 1) return `M ${points[0].x - 14} ${points[0].y} C ${points[0].x - 4} ${points[0].y - 18}, ${points[0].x + 10} ${points[0].y + 18}, ${points[0].x + 26} ${points[0].y}`;
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1];
    const current = points[index];
    const midX = previous.x + (current.x - previous.x) / 2;
    path += ` C ${midX} ${previous.y}, ${midX} ${current.y}, ${current.x} ${current.y}`;
  }
  return path;
}

function isMemoryRiverBlackHoleEvent(event: TimelineDisplayEvent): boolean {
  return memoryRiverMarkerKind(event) === "black-hole" || Boolean(event.node && isBlackHoleCandidate(event.node));
}

function isMemoryRiverProtoStarEvent(event: TimelineDisplayEvent, recentStart: Date, latest: Date): boolean {
  return memoryRiverMarkerKind(event) === "proto-star" || Boolean(event.node && isProtoStarCandidate(event.node, recentStart, latest));
}

function isMemoryRiverStaleDeprecatedEvent(event: TimelineDisplayEvent): boolean {
  const stale = event.node?.metrics?.roi?.staleness_status ?? "";
  return (
    stale.includes("stale") ||
    stale === "needs_review" ||
    event.source.category === "deprecated_info" ||
    event.source.category === "temporary_or_sensitive" ||
    normalizeMemoryTier(event.source.memory_tier) === "临时"
  );
}

function buildEmptyMemoryRiverLanes(levels: Array<MemoryRiverLevelBand & { maxLanes: number }>, cursorX: number): MemoryRiverLane[] {
  return levels.map((level, index) => ({
    id: `river-empty-${level.level.toLowerCase()}`,
    groupKey: "empty",
    level: level.level,
    label: "暂无可渲染事件",
    count: 0,
    path: `M 80 ${level.y} C ${Math.max(120, cursorX - 90)} ${level.y}, ${Math.min(920, cursorX + 90)} ${level.y}, 960 ${level.y}`,
    color: memoryRiverLaneColor("empty", level.level, index),
    gradientId: `memory-river-gradient-empty-${level.level.toLowerCase()}`,
    strokeWidth: 8,
    labelX: 110,
    labelY: level.y - 14,
    y: level.y,
  }));
}

function memoryRiverGroup(event: TimelineDisplayEvent, level: MemoryRiverLevel): { key: string; label: string } {
  if (level === "Macro") {
    const tier = normalizeMemoryTier(event.source.memory_tier) || "未分层";
    return { key: tier, label: translateTierOrKind(tier) };
  }
  if (level === "Meso") {
    const theme = event.node ? compactThemeLabel(humanThemeLabel(event.node)) || event.node.visual?.cluster || "未归类主题" : "未归类主题";
    return { key: event.node?.visual?.cluster ?? theme, label: theme };
  }
  const category = event.source.category || "unknown";
  return { key: category, label: humanCategoryLabel(category) };
}

function memoryRiverEventScore(event: TimelineDisplayEvent): number {
  const tier = normalizeMemoryTier(event.source.memory_tier);
  return (
    (event.source.importance === "高" ? 12 : event.source.importance === "中" ? 6 : 2) +
    (event.source.category === "decision" ? 8 : 0) +
    (tier === "核心画像" ? 8 : tier === "一般" ? 4 : 0)
  );
}

function memoryRiverLaneColor(key: string, level: MemoryRiverLevel, index: number): string {
  if (level === "Macro") return laneColor(key, index);
  const mesoColors = ["#8fd3ff", "#7ee8d4", "#f48fb1", "#6ea8ff", "#c7a7ff"];
  const microColors = ["#f48fb1", "#c7a7ff", "#94a3b8", "#48c7e8", "#7ee8d4"];
  return (level === "Meso" ? mesoColors : microColors)[(index + Math.floor(stableUnit(key, `river-${level}`) * 10)) % (level === "Meso" ? mesoColors.length : microColors.length)];
}

function buildMemoryRiverPath(events: TimelineDisplayEvent[], baseY: number): string {
  const sorted = [...events].sort((a, b) => a.x - b.x);
  const anchors = [
    { x: 80, y: baseY },
    ...sorted.map((event) => ({
      x: Math.max(80, Math.min(960, event.x)),
      y: baseY + (stableUnit(event.id, "memory-river-wave") - 0.5) * 38,
    })),
    { x: 960, y: baseY },
  ];
  let path = `M ${anchors[0].x} ${anchors[0].y}`;
  for (let index = 1; index < anchors.length; index += 1) {
    const previous = anchors[index - 1];
    const current = anchors[index];
    const midX = previous.x + (current.x - previous.x) / 2;
    path += ` C ${midX} ${previous.y}, ${midX} ${current.y}, ${current.x} ${current.y}`;
  }
  return path;
}

function memoryRiverMarkerLevel(event: TimelineDisplayEvent): MemoryRiverLevel {
  if (event.source.category === "deprecated_info" || event.source.category === "temporary_or_sensitive") return "Micro";
  if (event.source.category === "decision" || event.source.importance === "高") return "Meso";
  return "Macro";
}

function memoryRiverMarkerKind(event: TimelineDisplayEvent): MemoryRiverMarker["kind"] {
  const text = `${event.source.label} ${event.node?.statement ?? ""}`;
  if (event.source.category === "deprecated_info" || event.source.category === "temporary_or_sensitive") return "black-hole";
  if (event.source.category === "decision" || event.source.importance === "高" || /机会|增长|突破|下一步|opportunity|next/i.test(text)) return "proto-star";
  return "memory-event";
}

function buildTimelineDensityBands(
  events: Array<{ day: Date }>,
  minDay: Date,
  maxDay: Date,
  windowStartMs: number,
  windowEndMs: number,
) {
  const count = 48;
  const minMs = timelineUtcMs(minDay);
  const maxMs = timelineUtcMs(maxDay);
  const totalSpan = Math.max(1, maxMs - minMs);
  const bins = Array.from({ length: count }, (_unused, index) => ({
    key: `density-${index}`,
    count: 0,
    center: (index + 0.5) / count,
    label: "",
    intensity: 0,
    active: false,
  }));
  for (const event of events) {
    const ratio = Math.min(0.999, Math.max(0, (timelineUtcMs(event.day) - minMs) / totalSpan));
    bins[Math.floor(ratio * count)].count += 1;
  }
  const peak = Math.max(1, ...bins.map((bin) => bin.count));
  return bins.map((bin, index) => {
    const start = new Date(minDay.getTime() + totalSpan * (index / count));
    const end = new Date(minDay.getTime() + totalSpan * ((index + 1) / count));
    return {
      ...bin,
      label: `${formatAxisDate(start)}-${formatAxisDate(end)}`,
      intensity: bin.count > 0 ? Math.log1p(bin.count) / Math.log1p(peak) : 0,
      active: end.getTime() >= windowStartMs && start.getTime() <= windowEndMs,
    };
  });
}

function buildTimelineDensityBackdrops(
  events: Array<{ day: Date }>,
  minDay: Date,
  maxDay: Date,
) {
  const count = 36;
  const minMs = timelineUtcMs(minDay);
  const span = Math.max(1, timelineUtcMs(maxDay) - minMs);
  const bins = Array.from({ length: count }, (_unused, index) => ({ key: `timeline-band-${index}`, count: 0 }));
  for (const event of events) {
    const ratio = Math.min(0.999, Math.max(0, (timelineUtcMs(event.day) - minMs) / span));
    bins[Math.floor(ratio * count)].count += 1;
  }
  const peak = Math.max(1, ...bins.map((bin) => bin.count));
  return bins.map((bin, index) => {
    const width = 880 / count;
    const intensity = bin.count > 0 ? Math.log1p(bin.count) / Math.log1p(peak) : 0;
    return {
      key: bin.key,
      x: 80 + index * width,
      y: 540 - Math.max(12, intensity * 430),
      width: Math.max(8, width - 1),
      height: Math.max(12, intensity * 430),
    };
  });
}

function buildContributionPeriods(atlas: MemoryAtlas, nodes: AtlasNode[], filters: AtlasFilters, selectedYear: number) {
  const latest = parseDay(atlas.contribution.range_end) ?? new Date(Date.UTC(selectedYear, 11, 31));
  const year = selectedYear;
  const startYear = year - 1;
  const endYear = year;
  const globalDaily = new Map(atlas.contribution.daily.map((bucket) => [bucket.date, bucket]));
  const filteredDaily = aggregateFilteredNodes(nodes, "day");
  const yearStart = new Date(Date.UTC(year, 0, 1));
  const daysInYear = isLeapYear(year) ? 366 : 365;
  const startWeekday = mondayWeekdayIndex(yearStart);
  const weekColumns = Math.ceil((daysInYear + startWeekday) / 7);
  const periods = new Map<string, PeriodCounts & { delta: number; previousLabel: string }>();
  const filterActive =
    filters.query !== "" || filters.tier !== "all" || filters.category !== "all" || filters.theme !== "all";

  const dailyCells = Array.from({ length: daysInYear }, (_, index) => {
    const day = addDays(yearStart, index);
    const dateKey = toDayKey(day);
    const global = globalDaily.get(dateKey);
    const filtered = filteredDaily.get(dateKey);
    const weekColumn = Math.floor((index + startWeekday) / 7);
    const weekKey = calendarWeekKey(year, weekColumn);
    const count = mergePeriodCounts(dateKey, formatChineseDate(day), global, filtered, filterActive);
    periods.set(dateKey, withDelta(count, periods.get(toDayKey(addDays(day, -1)))));
    return {
      ...count,
      weekday: mondayWeekdayIndex(day),
      weekColumn,
      weekKey,
      activityLevel: count.activityLevel,
    };
  });

  const weeklyMap = aggregateCells(dailyCells, (cell) => cell.weekKey, (cell) => `第 ${cell.weekColumn + 1} 周`);
  const weekColumnByKey = new Map<string, number>();
  for (const cell of dailyCells) {
    if (!weekColumnByKey.has(cell.weekKey)) {
      weekColumnByKey.set(cell.weekKey, cell.weekColumn);
    }
  }
  const weekEntries = Array.from(weeklyMap.entries()).sort((a, b) => (weekColumnByKey.get(a[0]) ?? 0) - (weekColumnByKey.get(b[0]) ?? 0));
  weekEntries.forEach(([key, value], index) => {
    const previousValue = index > 0 ? weekEntries[index - 1][1] : undefined;
    periods.set(key, withDelta(value, previousValue));
  });
  const weekCells = weekEntries.map(([key, value]) => ({
    ...(periods.get(key) ?? withDelta(value, undefined)),
    weekKey: key,
    weekColumn: weekColumnByKey.get(key) ?? 0,
    daySlots: Array.from({ length: 7 }, (_, weekday) => dailyCells.find((cell) => cell.weekKey === key && cell.weekday === weekday) ?? null),
  }));

  const globalMonthly = new Map(atlas.contribution.monthly.map((bucket) => [bucket.date, bucket]));
  const filteredMonthly = aggregateFilteredNodes(nodes, "month");
  const monthCells = Array.from({ length: 24 }, (_, index) => {
    const cellYear = startYear + Math.floor(index / 12);
    const month = index % 12;
    const dateKey = `${cellYear}-${String(month + 1).padStart(2, "0")}`;
    const count = mergePeriodCounts(dateKey, `${cellYear} 年 ${month + 1} 月`, globalMonthly.get(dateKey), filteredMonthly.get(dateKey), filterActive);
    const previousKey = month === 0 ? `${cellYear - 1}-12` : `${cellYear}-${String(month).padStart(2, "0")}`;
    periods.set(dateKey, withDelta(count, periods.get(previousKey)));
    return {
      ...count,
      year: cellYear,
      month,
      monthLabel: `${month + 1}月`,
      daySlots: buildMonthDaySlots(cellYear, month, globalDaily, filteredDaily, filterActive),
    };
  });
  const yearlyMap = aggregateCells(monthCells, (cell) => String(cell.year), (cell) => `${cell.year} 年`);
  for (const [key, value] of yearlyMap) {
    periods.set(key, withDelta(value, periods.get(String(Number(key) - 1)) ?? yearlyMap.get(String(Number(key) - 1))));
  }
  const yearCells = [startYear, endYear].map((cellYear) => {
    const key = String(cellYear);
    const yearlyValue = periods.get(key) ?? withDelta(yearlyMap.get(key) ?? aggregateCells(monthCells.filter((cell) => cell.year === cellYear), () => key, () => `${cellYear} 年`).get(key)!, undefined);
    return {
      ...yearlyValue,
      year: cellYear,
      monthSlots: monthCells.filter((cell) => cell.year === cellYear),
    };
  });
  const latestWithinYear = latest.getUTCFullYear() === year ? latest : new Date(Date.UTC(year, 11, 31));
  const latestDayKey = toDayKey(latestWithinYear);
  const latestWeekKey = calendarWeekKey(year, Math.floor((dayOfYearIndex(latestWithinYear) + startWeekday) / 7));
  const latestMonthKey = `${year}-${String(latestWithinYear.getUTCMonth() + 1).padStart(2, "0")}`;
  const latestYearKey = String(year);
  const defaultPeriod =
    periods.get(latestDayKey) ??
    withDelta(mergePeriodCounts(latestDayKey, formatChineseDate(latestWithinYear), undefined, undefined, filterActive), undefined);
  const dayMaxActivityScore = maxActivityScore(dailyCells);
  const weekMaxActivityScore = maxActivityScore(weekCells);
  const monthMaxActivityScore = maxActivityScore(monthCells);
  const yearMaxActivityScore = maxActivityScore(yearCells);
  return {
    dailyCells,
    weekCells,
    monthCells,
    yearCells,
    periods,
    latestDayKey,
    latestWeekKey,
    latestMonthKey,
    latestYearKey,
    defaultPeriod,
    weekColumns,
    year,
    startYear,
    endYear,
    dayMaxActivityScore,
    weekMaxActivityScore,
    monthMaxActivityScore,
    yearMaxActivityScore,
  };
}

function buildMonthDaySlots(
  cellYear: number,
  month: number,
  globalDaily: Map<string, ActivityBucket>,
  filteredDaily: Map<string, ActivityBucket>,
  filterActive: boolean,
) {
  const firstDay = new Date(Date.UTC(cellYear, month, 1));
  const daysInMonth = new Date(Date.UTC(cellYear, month + 1, 0)).getUTCDate();
  return Array.from({ length: daysInMonth }, (_, index) => {
    const day = addDays(firstDay, index);
    const dateKey = toDayKey(day);
    return mergePeriodCounts(dateKey, formatChineseDate(day), globalDaily.get(dateKey), filteredDaily.get(dateKey), filterActive);
  });
}

function maxActivityScore(items: Array<{ activityScore?: number } | null>) {
  return Math.max(0, ...items.map((item) => Number(item?.activityScore ?? 0)));
}

function buildContributionPeriodDetail(
  scale: ContributionScale,
  bucket: PeriodCounts,
  nodes: AtlasNode[],
): ContributionPeriodDetail {
  const relatedNodes = nodes
    .filter((node) => nodeMatchesContributionPeriod(node, scale, bucket.date))
    .sort((a, b) => {
      const score = (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0);
      if (score !== 0) return score;
      return (b.date ?? "").localeCompare(a.date ?? "");
    });
  return { scale, bucket, relatedNodes };
}

function nodeMatchesContributionPeriod(node: AtlasNode, scale: ContributionScale, periodKey: string): boolean {
  const day = parseDay(node.date);
  if (!day) return false;
  if (scale === "day") return toDayKey(day) === periodKey;
  if (scale === "month") return `${day.getUTCFullYear()}-${String(day.getUTCMonth() + 1).padStart(2, "0")}` === periodKey;
  if (scale === "year") return String(day.getUTCFullYear()) === periodKey;
  const year = day.getUTCFullYear();
  const startWeekday = mondayWeekdayIndex(new Date(Date.UTC(year, 0, 1)));
  return calendarWeekKey(year, Math.floor((dayOfYearIndex(day) + startWeekday) / 7)) === periodKey;
}

function periodMeaningLine(bucket: PeriodCounts, scale: ContributionScale): string {
  const label = scale === "day" ? "这一天" : scale === "week" ? "这一周" : scale === "month" ? "这个月" : "这一年";
  if (bucket.activityScore <= 0) return `${label}没有明显活动，适合作为低使用或空窗期参考。`;
  if (bucket.filteredCoreCount > 0) return `${label}出现核心画像增量，说明有会影响长期 personalization 或 agent 默认行为的信息。`;
  if (bucket.filteredDecisionCount > 0) return `${label}出现新的决策记录，后续项目和 agent 执行应默认继承这些选择。`;
  if (bucket.filteredMemoryCount > 0) return `${label}沉淀了新的记忆内容，适合检查是否已经转成可执行待办或可复用上下文。`;
  return `${label}主要体现交互强度变化，具体记忆增量较少，适合用于使用行为复盘。`;
}

function periodImpactLine(bucket: PeriodCounts, relatedNodeCount: number): string {
  if (bucket.filteredCoreCount > 0) {
    return "它会影响未来 ChatGPT / Codex / 其他 agent 对你的默认理解，应该优先进入 personalization 和核心画像复盘。";
  }
  if (bucket.filteredDecisionCount > 0) {
    return "它包含决策密度，价值在于避免未来重复决策，并把当时的选择接入后续执行。";
  }
  if (relatedNodeCount > 0) {
    return `它关联 ${relatedNodeCount.toLocaleString()} 条具体记忆，可以直接回看这段时间你关注过什么、推进过什么、哪些事情值得继续。`;
  }
  if (bucket.messageCount > 0) {
    return "它说明这段时间有明显交互行为，但当前筛选下没有对应记忆，可能需要补做记忆抽取或复盘。";
  }
  return "它的价值主要是作为基线，帮助识别真正的使用高峰、低频空窗和后续增量变化。";
}

function defaultPeriodKeyForScale(
  scale: ContributionScale,
  periodData: ReturnType<typeof buildContributionPeriods>,
): string {
  if (scale === "day") return periodData.latestDayKey;
  if (scale === "week") return periodData.latestWeekKey;
  if (scale === "month") return periodData.latestMonthKey;
  return periodData.latestYearKey;
}

function aggregateFilteredNodes(nodes: AtlasNode[], period: "day" | "month") {
  const map = new Map<string, ActivityBucket>();
  for (const node of nodes) {
    const day = parseDay(node.date);
    if (!day) continue;
    const key = period === "day" ? toDayKey(day) : `${day.getUTCFullYear()}-${String(day.getUTCMonth() + 1).padStart(2, "0")}`;
    const bucket = map.get(key) ?? blankBucket(key);
    bucket.memory_count += 1;
    if (node.category === "decision") bucket.decision_count += 1;
    const tier = normalizeMemoryTier(node.memory_tier);
    if (tier === "核心画像") bucket.core_memory_count += 1;
    else if (tier === "一般") bucket.mid_long_memory_count += 1;
    else bucket.short_memory_count += 1;
    bucket.activity_score = bucket.memory_count * 3 + bucket.decision_count * 4;
    bucket.activity_level = Math.max(1, Math.min(5, Math.ceil(bucket.activity_score / 6)));
    map.set(key, bucket);
  }
  return map;
}

function mergePeriodCounts(
  dateKey: string,
  label: string,
  global: ActivityBucket | undefined,
  filtered: ActivityBucket | undefined,
  filterActive: boolean,
): PeriodCounts {
  const activityScore = filterActive ? filtered?.activity_score ?? 0 : global?.activity_score ?? filtered?.activity_score ?? 0;
  return {
    date: dateKey,
    label,
    activityScore,
    activityLevel: global?.activity_level ?? filtered?.activity_level ?? levelFromScore(activityScore),
    globalActivityScore: global?.activity_score ?? 0,
    conversationCount: global?.conversation_count ?? 0,
    messageCount: global?.message_count ?? 0,
    memoryCount: global?.memory_count ?? 0,
    decisionCount: global?.decision_count ?? 0,
    coreMemoryCount: global?.core_memory_count ?? 0,
    midLongMemoryCount: global?.mid_long_memory_count ?? 0,
    shortMemoryCount: global?.short_memory_count ?? 0,
    filteredMemoryCount: filtered?.memory_count ?? 0,
    filteredDecisionCount: filtered?.decision_count ?? 0,
    filteredCoreCount: filtered?.core_memory_count ?? 0,
    toolCallCount: global?.tool_call_count ?? 0,
    errorEventCount: global?.error_event_count ?? 0,
    abortCount: global?.abort_count ?? 0,
  };
}

function aggregateCells<T extends PeriodCounts>(cells: T[], getKey: (cell: T) => string, getLabel: (cell: T) => string) {
  const map = new Map<string, PeriodCounts>();
  for (const cell of cells) {
    const key = getKey(cell);
    const target = map.get(key) ?? {
      date: key,
      label: getLabel(cell),
      activityScore: 0,
      activityLevel: 0,
      globalActivityScore: 0,
      conversationCount: 0,
      messageCount: 0,
      memoryCount: 0,
      decisionCount: 0,
      coreMemoryCount: 0,
      midLongMemoryCount: 0,
      shortMemoryCount: 0,
      filteredMemoryCount: 0,
      filteredDecisionCount: 0,
      filteredCoreCount: 0,
      toolCallCount: 0,
      errorEventCount: 0,
      abortCount: 0,
    };
    for (const keyName of [
      "activityScore",
      "globalActivityScore",
      "conversationCount",
      "messageCount",
      "memoryCount",
      "decisionCount",
      "coreMemoryCount",
      "midLongMemoryCount",
      "shortMemoryCount",
      "filteredMemoryCount",
      "filteredDecisionCount",
      "filteredCoreCount",
      "toolCallCount",
      "errorEventCount",
      "abortCount",
    ] as const) {
      target[keyName] = (target[keyName] ?? 0) + (cell[keyName] ?? 0);
    }
    target.activityLevel = levelFromScore(target.activityScore);
    map.set(key, target);
  }
  return map;
}

function withDelta(current: PeriodCounts, previous?: PeriodCounts): PeriodCounts & { delta: number; previousLabel: string } {
  return {
    ...current,
    delta: current.activityScore - (previous?.activityScore ?? 0),
    previousLabel: previous?.label ?? "上一周期",
  };
}

function degreeMap(edges: AtlasEdge[]): Map<string, number> {
  const counts = new Map<string, number>();
  for (const edge of edges) {
    counts.set(edge.source, (counts.get(edge.source) ?? 0) + 1);
    counts.set(edge.target, (counts.get(edge.target) ?? 0) + 1);
  }
  return counts;
}

function expandGraphIds(rootId: string, edges: AtlasEdge[], depth: number): Set<string> {
  const ids = new Set([rootId]);
  let frontier = new Set([rootId]);
  for (let level = 0; level < depth; level += 1) {
    const next = new Set<string>();
    for (const edge of edges) {
      if (frontier.has(edge.source) && !ids.has(edge.target)) next.add(edge.target);
      if (frontier.has(edge.target) && !ids.has(edge.source)) next.add(edge.source);
    }
    for (const id of next) ids.add(id);
    frontier = next;
  }
  return ids;
}

function buildMonthTicks(minDay: Date, maxDay: Date, minX: number, maxX: number) {
  const ticks: Array<{ label: string; x: number }> = [];
  const start = new Date(Date.UTC(minDay.getUTCFullYear(), minDay.getUTCMonth(), 1));
  const end = new Date(Date.UTC(maxDay.getUTCFullYear(), maxDay.getUTCMonth(), 1));
  const minMs = timelineUtcMs(minDay);
  const span = Math.max(1, timelineUtcMs(maxDay) - minMs);
  let cursor = start;
  while (cursor <= end) {
    const x = minX + ((timelineUtcMs(cursor) - minMs) / span) * (maxX - minX);
    ticks.push({ label: `${cursor.getUTCFullYear()}.${cursor.getUTCMonth() + 1}`, x });
    cursor = new Date(Date.UTC(cursor.getUTCFullYear(), cursor.getUTCMonth() + 1, 1));
  }
  return ticks.filter((_, index) => index % Math.max(1, Math.ceil(ticks.length / 8)) === 0);
}

function buildEventDateTicks(
  events: Array<{ source: TimelineEvent; day: Date }>,
  minDay: Date,
  maxDay: Date,
  minX: number,
  maxX: number,
) {
  const grouped = new Map<string, { date: string; day: Date; count: number; score: number }>();
  for (const event of events) {
    const date = toDayKey(event.day);
    const current = grouped.get(date) ?? { date, day: event.day, count: 0, score: 0 };
    current.count += 1;
    current.score += event.source.importance === "高" ? 8 : event.source.category === "decision" ? 6 : 1;
    grouped.set(date, current);
  }
  const all = Array.from(grouped.values()).sort((a, b) => timelineUtcMs(a.day) - timelineUtcMs(b.day));
  if (all.length <= 12) return all.map((tick, index) => eventDateTick(tick, index, minDay, maxDay, minX, maxX));
  const selected = new Map<string, (typeof all)[number]>();
  selected.set(all[0].date, all[0]);
  selected.set(all[all.length - 1].date, all[all.length - 1]);
  const minMs = timelineUtcMs(minDay);
  const span = Math.max(1, timelineUtcMs(maxDay) - minMs);
  const xFor = (day: Date) => minX + ((timelineUtcMs(day) - minMs) / span) * (maxX - minX);
  const ranked = [...all].sort((a, b) => b.count * 3 + b.score - (a.count * 3 + a.score));
  for (const candidate of ranked) {
    if (selected.size >= 12) break;
    const candidateX = xFor(candidate.day);
    const hasSpace = Array.from(selected.values()).every((tick) => Math.abs(candidateX - xFor(tick.day)) >= 62);
    if (hasSpace) selected.set(candidate.date, candidate);
  }
  return Array.from(selected.values())
    .sort((a, b) => timelineUtcMs(a.day) - timelineUtcMs(b.day))
    .map((tick, index) => eventDateTick(tick, index, minDay, maxDay, minX, maxX));
}

function eventDateTick(
  tick: { date: string; day: Date; count: number },
  index: number,
  minDay: Date,
  maxDay: Date,
  minX: number,
  maxX: number,
) {
  const minMs = timelineUtcMs(minDay);
  const span = Math.max(1, timelineUtcMs(maxDay) - minMs);
  return {
    date: tick.date,
    label: formatAxisDate(tick.day),
    x: minX + ((timelineUtcMs(tick.day) - minMs) / span) * (maxX - minX),
    count: tick.count,
    stagger: index % 2,
  };
}

function formatAxisDate(day: Date) {
  return `${day.getUTCFullYear()}.${day.getUTCMonth() + 1}.${day.getUTCDate()}`;
}

function filteredMetricValues(nodes: AtlasNode[], key: "memory_tier" | "category"): Record<string, number> {
  return nodes.reduce<Record<string, number>>((acc, node) => {
    const value = key === "memory_tier" ? normalizeMemoryTier(node.memory_tier) : node[key] || "unknown";
    acc[value] = (acc[value] ?? 0) + 1;
    return acc;
  }, {});
}

function topEntry(values: Record<string, number>): [string, number] | undefined {
  return Object.entries(values).sort((a, b) => b[1] - a[1])[0];
}

function nodeRadius(node: AtlasNode, degree: number): number {
  const base = node.kind === "theme" ? 18 : node.kind === "project" ? 15 : node.kind === "decision" ? 13 : 8;
  return Math.min(28, base + Math.sqrt(Math.max(0, degree)) * 1.6 + (node.metrics?.roi?.leverage_score ?? 0) * 4);
}

function nodeColor(node: AtlasNode): string {
  if (node.kind === "decision") return "#f48fb1";
  if (node.kind === "project") return "#8fd3ff";
  const tier = normalizeMemoryTier(node.memory_tier);
  if (tier === "核心画像") return "#7ee8d4";
  if (tier === "一般") return node.visual?.color ?? "#8fd3ff";
  return node.visual?.color ?? "#94a3b8";
}

function isGraphParentNode(node: AtlasNode): boolean {
  return node.kind === "theme" || node.kind === "project" || node.kind === "category" || node.kind === "tier";
}

function clusterIndex(node: AtlasNode): number {
  return Math.floor(stableUnit(node.visual?.cluster ?? node.category ?? node.id, "cluster") * 12);
}

function kindRank(kind: AtlasNode["kind"]): number {
  return { theme: 0, project: 1, decision: 2, memory: 3, category: 4, tier: 5, timeline_event: 6 }[kind] ?? 9;
}

function kindLabelSign(kind: AtlasNode["kind"]): string {
  return { theme: "主题", project: "项目", decision: "决策", memory: "记忆", category: "分类", tier: "层级", timeline_event: "事件" }[kind] ?? "节点";
}

function shortNodeLabel(node: AtlasNode, length: number): string {
  return truncate(node.kind === "memory" ? node.label : `${kindLabelSign(node.kind)} · ${node.label}`, length);
}

function laneColor(key: string, index: number): string {
  const colors = ["#7ee8d4", "#8fd3ff", "#48c7e8", "#f48fb1", "#c7a7ff", "#6ea8ff", "#94a3b8"];
  if (key === "核心画像") return "#7ee8d4";
  if (key === "一般") return "#8fd3ff";
  if (key === "decision") return "#f48fb1";
  return colors[index % colors.length];
}

function blankBucket(dateKey: string): ActivityBucket {
  return {
    date: dateKey,
    conversation_count: 0,
    message_count: 0,
    user_message_count: 0,
    assistant_message_count: 0,
    memory_count: 0,
    candidate_count: 0,
    decision_count: 0,
    core_memory_count: 0,
    mid_long_memory_count: 0,
    short_memory_count: 0,
    tool_call_count: 0,
    error_event_count: 0,
    abort_count: 0,
    codex_session_count: 0,
    activity_score: 0,
    activity_level: 0,
  };
}

function levelFromScore(score: number): number {
  if (score <= 0) return 0;
  if (score < 8) return 1;
  if (score < 24) return 2;
  if (score < 64) return 3;
  if (score < 160) return 4;
  return 5;
}

function contributionTitle(bucket: PeriodCounts) {
  return `${bucket.label}: 活动分 ${bucket.activityScore}; 全局对话 ${bucket.conversationCount}; 全局消息 ${bucket.messageCount}; 工具调用 ${bucket.toolCallCount ?? 0}; 错误事件 ${bucket.errorEventCount ?? 0}; 中断 ${bucket.abortCount ?? 0}; 筛选记忆 ${bucket.filteredMemoryCount}; 筛选决策 ${bucket.filteredDecisionCount}`;
}

function scaleLabel(scale: ContributionScale): string {
  return { day: "日", week: "周", month: "月", year: "年" }[scale];
}

function buildInspectorExplanation(node: AtlasNode, edgeCount: number, sharedState: SharedAtlasState): InspectorExplanation {
  const tierScore = modelTierScore(node.memory_tier);
  const importanceScore = modelImportanceScore(node.importance);
  const confidenceScore = modelConfidenceScore(node.confidence);
  const derivedWeight = node.metrics?.weight_score;
  const calculatedWeight = tierScore * 0.5 + importanceScore * 0.3 + confidenceScore * 0.2;
  const displayedWeight = typeof derivedWeight === "number" ? derivedWeight : calculatedWeight;
  const decisionImpact = node.category === "decision" ? 1 : 0;
  const sensitivityPenalty = modelSensitivityPenalty(node);
  const displayedLeverage = node.metrics?.roi?.leverage_score;
  const calculatedLeverage = Math.max(0, displayedWeight + decisionImpact * 0.15 - sensitivityPenalty);
  const leverageValue = typeof displayedLeverage === "number" ? displayedLeverage : calculatedLeverage;
  const theme = humanThemeLabel(node);
  const focusNode = sharedState.focus.inspector.nodeId || sharedState.selection.nodeId || node.id;
  return {
    summary: `这条记忆当前作为「${humanCategoryLabel(node.category)}」解释：默认面板只使用派生层级、分类、日期、连接数、ROI 和共享焦点状态，不展示 raw transcript。`,
    formulas: [
      {
        label: "记忆权重",
        value: formatScore(displayedWeight),
        formula: "memory_weight = tier*0.5 + importance*0.3 + confidence*0.2",
        parameters: `tier=${tierScore.toFixed(2)}, importance=${importanceScore.toFixed(2)}, confidence=${confidenceScore.toFixed(2)}`,
      },
      {
        label: "ROI Leverage",
        value: `${formatScore(leverageValue)} · ${translateAction(node.metrics?.roi?.recommended_action)}`,
        formula: "leverage_score = max(0, memory_weight + decision_impact*0.15 - sensitivity_penalty)",
        parameters: `decision_impact=${decisionImpact}, sensitivity_penalty=${sensitivityPenalty.toFixed(2)}, stale=${translateStaleness(node.metrics?.roi?.staleness_status)}`,
      },
      {
        label: "共享焦点",
        value: `${sharedState.sync.updatedBy} · r${sharedState.sync.revision}`,
        formula: "sharedAtlasReducer -> focus(inspector/home/galaxy/timeline/roi)",
        parameters: `node=${focusNode}, cluster=${sharedState.focus.inspector.clusterId ?? "none"}`,
      },
    ],
    evidence: [
      { label: "主题", value: theme },
      { label: "层级 / 分类", value: `${normalizeMemoryTier(node.memory_tier) || "未知"} / ${humanCategoryLabel(node.category)}` },
      { label: "日期 / 时效", value: `${node.date || "未知"} / ${node.validity || translateStaleness(node.metrics?.roi?.staleness_status)}` },
      { label: "连接数", value: edgeCount.toLocaleString() },
      { label: "来源", value: node.source_label ?? node.data_source ?? "脱敏派生快照" },
    ],
    safetyNotes: [
      "默认解释只读 redacted derived snapshot。",
      "结构化字段和低敏摘要位于 Debug 面板，默认关闭。",
      "长期记忆写回只生成提案 JSON，不能直接修改主动记忆库。",
    ],
  };
}

function modelTierScore(value: string | undefined): number {
  const tier = normalizeMemoryTier(value);
  if (tier === "核心画像") return 1;
  if (tier === "一般") return 0.66;
  if (tier === "临时") return 0.28;
  return 0.5;
}

function modelImportanceScore(value: string | undefined): number {
  if (value === "高") return 1;
  if (value === "中") return 0.62;
  if (value === "低") return 0.32;
  return 0.5;
}

function modelConfidenceScore(value: string | undefined): number {
  if (value === "high" || value === "高") return 1;
  if (value === "medium" || value === "中") return 0.72;
  if (value === "low" || value === "低") return 0.45;
  return 0.72;
}

function modelSensitivityPenalty(node: AtlasNode): number {
  if (node.visual?.sensitive || node.category === "temporary_or_sensitive" || node.category === "security_boundary") return 0.35;
  return 0.1;
}

function buildWritebackProposalDraft(input: WritebackProposalDraftInput): WritebackProposal {
  const text = input.proposedText.trim();
  const reason = input.reason.trim();
  const idSeed = `${input.node.id}:${input.action}:${text}:${reason}:${input.proposalCount + 1}:${input.proposalIdPrefix}`;
  return {
    schema_version: input.policy.proposal_schema_version || "memory_change_proposal.v1",
    proposal_id: `${input.proposalIdPrefix}_${compactTimestamp(input.now)}_${stableHash(idSeed)}`,
    created_at: input.now,
    status: "draft_pending_agent_apply",
    target_ref: {
      node_id: input.node.id,
      memory_id: input.node.memory_id ?? input.node.id,
      label: input.node.label,
      source_file: input.node.source_label ?? input.node.data_source ?? "visual_snapshot",
      base_date: input.node.date ?? "",
    },
    action: input.action,
    payload: {
      proposed_text: text,
      reason,
      current_tier: normalizeMemoryTier(input.node.memory_tier),
      current_category: input.node.category ?? "",
    },
    diff: buildProposalDiff(input.baseText, text),
    version: {
      revision: (input.latest?.version.revision ?? 0) + 1,
      parent_proposal_id: input.latest?.proposal_id ?? null,
      rollback_unit: input.policy.rollback_unit || "per_memory_version",
      supersedes_proposal_id: null,
    },
    review: buildProposalReview(input.action, input.node, reason),
    safety: {
      direct_frontend_mutation_of_active_memory: false,
      requires_conflict_check: true,
      requires_agent_or_human_apply: true,
      forbidden_payload: input.policy.frontend_payload_contract?.forbidden_payload ?? [
        "plaintext secrets",
        "raw conversation text",
        "record hashes",
        "local absolute paths",
      ],
    },
  };
}

function buildProposalDiff(baseText: string, proposedText: string): NonNullable<WritebackProposal["diff"]> {
  const base = normalizeTextForDiff(baseText);
  const proposed = normalizeTextForDiff(proposedText);
  const baseSegments = splitReadableSegments(base);
  const proposedSegments = splitReadableSegments(proposed);
  const baseSet = new Set(baseSegments);
  const proposedSet = new Set(proposedSegments);
  const changedSegments =
    proposedSegments.filter((segment) => !baseSet.has(segment)).length +
    baseSegments.filter((segment) => !proposedSet.has(segment)).length;
  const lengthDelta = proposed.length - base.length;
  return {
    base_text: base,
    proposed_text: proposed,
    length_delta: lengthDelta,
    changed_segments: changedSegments,
    summary: `长度 ${lengthDelta > 0 ? "+" : ""}${lengthDelta}，片段变化 ${changedSegments}`,
  };
}

function buildProposalReview(action: WritebackAction, node: AtlasNode, reason: string): NonNullable<WritebackProposal["review"]> {
  const tier = normalizeMemoryTier(node.memory_tier);
  const actionLabel = writebackActionLabels[action];
  return {
    human_summary: `${actionLabel}：${humanNodeTitle(node)}。${reason || "需要补充证据和冲突检查后再写入。"} `,
    agent_next_step: "重新读取当前主动记忆库和历史提案，核对来源、冲突、敏感字段与版本号，然后写入提案历史并提交 git 回滚点。",
    conflict_policy: `目标层级 ${tier || "未知"}；如果现有库已出现更新版本或同主题相反结论，必须先生成冲突报告，不可静默覆盖。`,
    apply_status: "proposal_only_pending_agent_apply",
  };
}

function normalizeTextForDiff(value: string | undefined): string {
  return (value ?? "").replace(/\s+/g, " ").trim();
}

function splitReadableSegments(value: string): string[] {
  return value
    .split(/[。！？!?;；\n]+/)
    .map((segment) => segment.trim())
    .filter(Boolean);
}

function loadWritebackProposals(): WritebackProposal[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(WRITEBACK_QUEUE_KEY);
    if (!raw) return [];
    const payload: unknown = JSON.parse(raw);
    if (!Array.isArray(payload)) return [];
    return payload.filter(isWritebackProposal);
  } catch {
    return [];
  }
}

function saveWritebackProposals(proposals: WritebackProposal[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(WRITEBACK_QUEUE_KEY, JSON.stringify(proposals));
}

function isWritebackProposal(value: unknown): value is WritebackProposal {
  if (!value || typeof value !== "object") return false;
  const record = value as Partial<WritebackProposal>;
  return (
    typeof record.schema_version === "string" &&
    typeof record.proposal_id === "string" &&
    typeof record.created_at === "string" &&
    record.status === "draft_pending_agent_apply" &&
    Boolean(record.target_ref) &&
    Boolean(record.payload) &&
    Boolean(record.version)
  );
}

function downloadJson(filename: string, payload: unknown) {
  const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function compactTimestamp(value: string): string {
  return value.replace(/[-:.]/g, "").replace("T", "T").replace("Z", "Z");
}

function stableHash(value: string): string {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(36).padStart(7, "0").slice(0, 7);
}

function translateKind(kind: AtlasNode["kind"]): string {
  return {
    memory: "记忆",
    theme: "主题",
    tier: "层级",
    category: "分类",
    project: "项目",
    decision: "决策",
    timeline_event: "时间事件",
  }[kind];
}

function translateTierOrKind(value: string): string {
  if (value === "decision") return "决策";
  if (value === "project") return "项目";
  if (value === "timeline_event") return "时间事件";
  return value;
}

function translateAction(value: string | undefined): string {
  return {
    keep_high_weight: "高权重保留",
    review_for_project_linkage: "复查项目连接",
    keep_low_weight_or_refresh: "低权重保留或刷新",
    keep_as_context: "作为上下文保留",
  }[value ?? ""] ?? "作为上下文保留";
}

function translateStaleness(value: string | undefined): string {
  return {
    stale_short_term: "临时信息已旧",
    needs_review: "需要复查",
    current: "当前有效",
    unknown: "未知时效",
  }[value ?? ""] ?? "未知时效";
}

function formatScore(value: number | undefined | null): string {
  return typeof value === "number" ? value.toFixed(2) : "n/a";
}

function formatSigned(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toLocaleString()}`;
}

function sumValues(values: Record<string, number>, keys: string[]): number {
  return keys.reduce((sum, key) => sum + (values[key] ?? 0), 0);
}

function parseDay(value: string | undefined): Date | null {
  if (!value) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (!match) return null;
  return new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
}

function maxNodeDate(nodes: AtlasNode[]): Date | null {
  return nodes.reduce<Date | null>((latest, node) => {
    const day = parseDay(node.date);
    if (!day) return latest;
    if (!latest || day > latest) return day;
    return latest;
  }, null);
}

function isNodeBetween(node: AtlasNode, start: Date, end: Date): boolean {
  const day = parseDay(node.date);
  return Boolean(day && day >= start && day <= end);
}

function addDays(day: Date, count: number): Date {
  const next = new Date(day.getTime());
  next.setUTCDate(next.getUTCDate() + count);
  return next;
}

function contributionYears(atlas: MemoryAtlas, nodes: AtlasNode[]): number[] {
  const years = new Set<number>();
  for (const bucket of atlas.contribution.daily) {
    const day = parseDay(bucket.date);
    if (day) years.add(day.getUTCFullYear());
  }
  for (const node of nodes) {
    const day = parseDay(node.date);
    if (day) years.add(day.getUTCFullYear());
  }
  if (!years.size) years.add(new Date().getUTCFullYear());
  return Array.from(years).sort((a, b) => a - b);
}

function buildIterationHighlights(nodes: AtlasNode[], deltaStats: DeltaStats) {
  const coreCount = nodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length;
  const decisionCount = nodes.filter((node) => node.category === "decision").length;
  const actionCount = nodes.filter((node) => /todo|action|执行|继续|需要|下一步/i.test(`${node.label} ${node.statement ?? ""}`)).length;
  return [
    {
      label: "核心画像",
      value: coreCount,
      note: "优先进入 ChatGPT / Codex Personalization，影响默认理解。",
    },
    {
      label: "决策",
      value: decisionCount,
      note: "后续 agent 执行时应继承，除非新证据明确推翻。",
    },
    {
      label: "近期增量",
      value: formatSigned(deltaStats.deltaCount),
      note: deltaStats.deltaRate === null ? "没有上一周期基准。" : `较上一周期 ${(deltaStats.deltaRate * 100).toFixed(2)}%。`,
    },
    {
      label: "可行动线索",
      value: actionCount,
      note: "适合进入下一轮任务、周复盘或项目待办。",
    },
  ];
}

function formatUpdatedAt(value: string | undefined): string {
  if (!value) return "待同步";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
}

function toDayKey(day: Date): string {
  return `${day.getUTCFullYear()}-${String(day.getUTCMonth() + 1).padStart(2, "0")}-${String(day.getUTCDate()).padStart(2, "0")}`;
}

function formatChineseDate(day: Date): string {
  return `${day.getUTCFullYear()} 年 ${day.getUTCMonth() + 1} 月 ${day.getUTCDate()} 日`;
}

function mondayWeekdayIndex(day: Date): number {
  return (day.getUTCDay() + 6) % 7;
}

function dayOfYearIndex(day: Date): number {
  const start = new Date(Date.UTC(day.getUTCFullYear(), 0, 1));
  return Math.floor((day.getTime() - start.getTime()) / 86400000);
}

function calendarWeekKey(year: number, weekColumn: number): string {
  return `${year}-CW${String(weekColumn + 1).padStart(2, "0")}`;
}

function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}

function stableUnit(value: string, salt: string): number {
  let hash = 2166136261;
  const input = `${salt}:${value}`;
  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return (hash % 1000000) / 1000000;
}

function truncate(value: string, length: number): string {
  const text = value.replace(/\s+/g, " ").trim();
  return text.length > length ? `${text.slice(0, Math.max(0, length - 1))}…` : text;
}

function isActivationKey(event: KeyboardEvent): boolean {
  return event.key === "Enter" || event.key === " ";
}

function edgeCountFor(nodeId: string | undefined, edges: AtlasEdge[]): number {
  if (!nodeId) return 0;
  return edges.reduce((count, edge) => count + (edge.source === nodeId || edge.target === nodeId ? 1 : 0), 0);
}
