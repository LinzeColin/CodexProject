import { CommandExecutionState, uiCopy } from "./constants";
import { HeatStop, TopicClassificationDetail, WritebackAction } from "./contracts";



export const WRITEBACK_QUEUE_KEY = "memory-atlas.writeback.proposals.v1";


export const TIMELINE_FEEDBACK_SETTINGS_KEY = "memory-atlas.timeline.feedback";


export const TRANSIENT_STORAGE_PREFIXES = ["memory-atlas.runtime.", "memory-atlas.cache.", "memory-atlas.temp.", "memory-atlas.view."];


export const TRANSIENT_CACHE_PREFIXES = ["memory-atlas", "memory_atlas", "vite-memory-atlas"];


export const LOCAL_RUNTIME_HEARTBEAT_MS = 10_000;


export const INITIAL_COMMAND_EXECUTION_STATE: CommandExecutionState = {
  commandId: null,
  status: "idle",
  title: "",
  message: "",
  outputs: [],
  inputHint: "",
  fallbackUrl: "",
  navigationView: null,
};


export const NEXT_ACTION_TOP_LIMIT = 5;


export const NEXT_ACTION_SORT_WEIGHTS = {
  roi_weight: 0.4,
  urgency_weight: 0.25,
  confidence_weight: 0.25,
  effort_penalty_weight: 0.1,
};


export const TIER_ASSET_TOP_LIMIT = 7;


export const TIER_ASSET_SORT_WEIGHTS = {
  value_weight: 0.35,
  importance_weight: 0.25,
  confidence_weight: 0.25,
  staleness_penalty_weight: 0.15,
};


export const TOPIC_CLASSIFICATION_TOP_LIMIT = 10;


export const TOPIC_CLASSIFICATION_STATES: TopicClassificationDetail["topic_state"][] = [
  "dominant",
  "rising",
  "declining",
  "emerging",
  "conflict",
  "black_hole",
  "stale",
];


export const TOPIC_CLASSIFICATION_SORT_WEIGHTS = {
  strength_weight: 0.38,
  trend_weight: 0.24,
  confidence_weight: 0.22,
  conflict_penalty_weight: 0.16,
};


export const MEMORY_RIVER_MIN_X = 80;


export const MEMORY_RIVER_MAX_X = 960;


export const MEMORY_RIVER_WIDTH = MEMORY_RIVER_MAX_X - MEMORY_RIVER_MIN_X;


export const weekdayLabels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];


export const heatStops: HeatStop[] = [
  { stop: 0, rgb: [15, 17, 22] },
  { stop: 0.1, rgb: [23, 34, 58] },
  { stop: 0.24, rgb: [29, 63, 119] },
  { stop: 0.4, rgb: [31, 109, 178] },
  { stop: 0.58, rgb: [31, 155, 209] },
  { stop: 0.76, rgb: [72, 199, 232] },
  { stop: 0.9, rgb: [126, 224, 248] },
  { stop: 1, rgb: [167, 236, 255] },
];


export const heatLevelAnchors = [0, 0.16, 0.34, 0.54, 0.74, 0.93] as const;


export const emptyHeatColor = "#0f1116";



export const writebackActionLabels: Record<WritebackAction, string> = {
  update_statement: uiCopy.proposal.actions.update_statement,
  add_context: uiCopy.proposal.actions.add_context,
  change_tier: uiCopy.proposal.actions.change_tier,
  flag_conflict: uiCopy.proposal.actions.flag_conflict,
  rollback_to_version: uiCopy.proposal.actions.rollback_to_version,
};
