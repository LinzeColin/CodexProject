import type { AtlasFilters, AtlasNode, ViewKey } from "../types";

export const SHARED_ATLAS_STATE_SCHEMA_VERSION = "memory_atlas_shared_state.v1" as const;

export type SharedAtlasUpdateSource = ViewKey | "startup" | "system";
export type SharedAtlasFilterKey = keyof AtlasFilters | "timeRange" | "roi";
export type SharedAtlasRoiFilter = "all" | "high_leverage" | "needs_review" | "stale_orbit";
export type SharedAtlasSignal =
  | "none"
  | "record"
  | "cluster"
  | "time_range"
  | "timeline_event"
  | "contribution_period"
  | "filter";

export interface SharedTimelineTimeRangeSelection {
  id: string;
  source: "memory-river-brush";
  startDate: string;
  endDate: string;
  label: string;
  eventCount: number;
  decisionCount: number;
  coreMemoryCount: number;
  topTheme: string;
}

export interface SharedContributionSelection {
  id: string;
  scale: string;
  label: string;
  activityScore: number;
  filteredMemoryCount: number;
}

export interface SharedAtlasSelectionState {
  nodeId: string | null;
  nodeKind: AtlasNode["kind"] | null;
  clusterId: string | null;
  recordId: string | null;
  timeRangeId: string | null;
  contributionPeriodId: string | null;
  signal: SharedAtlasSignal;
}

export interface SharedAtlasFilterState {
  query: string;
  source: string;
  tier: string;
  category: string;
  theme: string;
  timeRange: SharedTimelineTimeRangeSelection | null;
  roi: SharedAtlasRoiFilter;
}

export interface SharedAtlasFocusTarget {
  nodeId: string | null;
  clusterId: string | null;
  recordId: string | null;
  timeRangeId: string | null;
}

export interface SharedAtlasFocusState extends SharedAtlasFocusTarget {
  sourceView: SharedAtlasUpdateSource;
  home: SharedAtlasFocusTarget;
  galaxy: SharedAtlasFocusTarget;
  timeline: SharedAtlasFocusTarget;
  inspector: SharedAtlasFocusTarget;
  roiDashboard: SharedAtlasFocusTarget;
}

export interface SharedAtlasSyncState {
  revision: number;
  updatedBy: SharedAtlasUpdateSource;
  lastAction: SharedAtlasAction["type"];
  loopGuard: {
    mode: "single-dispatch-reducer";
    derivedViews: "read-only";
  };
}

export interface SharedAtlasState {
  schema_version: typeof SHARED_ATLAS_STATE_SCHEMA_VERSION;
  mode: {
    activeView: ViewKey;
  };
  selection: SharedAtlasSelectionState;
  filters: SharedAtlasFilterState;
  focus: SharedAtlasFocusState;
  sync: SharedAtlasSyncState;
}

export type SharedAtlasAction =
  | { type: "switch_view"; view: ViewKey; source: SharedAtlasUpdateSource }
  | { type: "select_node"; node: AtlasNode; source: SharedAtlasUpdateSource; signal?: SharedAtlasSignal }
  | { type: "select_time_range"; range: SharedTimelineTimeRangeSelection; source: SharedAtlasUpdateSource }
  | { type: "clear_time_range"; source: SharedAtlasUpdateSource }
  | { type: "select_contribution_period"; period: SharedContributionSelection; source: SharedAtlasUpdateSource }
  | { type: "set_filters"; filters: AtlasFilters; source: SharedAtlasUpdateSource }
  | { type: "set_filter"; key: keyof AtlasFilters; value: string; source: SharedAtlasUpdateSource }
  | { type: "set_roi_filter"; value: SharedAtlasRoiFilter; source: SharedAtlasUpdateSource }
  | { type: "clear_filter"; key: SharedAtlasFilterKey; source: SharedAtlasUpdateSource }
  | { type: "reset_filters"; source: SharedAtlasUpdateSource }
  | { type: "clear_focus"; source: SharedAtlasUpdateSource };

const DEFAULT_ATLAS_FILTERS: AtlasFilters = {
  query: "",
  source: "all",
  tier: "all",
  category: "all",
  theme: "all",
};

export function createSharedAtlasState(input: {
  activeView?: ViewKey;
  filters?: AtlasFilters;
  selectedNode?: AtlasNode | null;
  timeRange?: SharedTimelineTimeRangeSelection | null;
} = {}): SharedAtlasState {
  const filters = sharedFiltersFromAtlasFilters(input.filters ?? DEFAULT_ATLAS_FILTERS, input.timeRange ?? null);
  const selection = input.selectedNode
    ? selectionFromNode(input.selectedNode, filters.timeRange, "record")
    : emptySelection(filters.timeRange);
  const sourceView = input.activeView ?? "home";
  return {
    schema_version: SHARED_ATLAS_STATE_SCHEMA_VERSION,
    mode: { activeView: sourceView },
    selection,
    filters,
    focus: focusFromSelection(selection, sourceView),
    sync: {
      revision: 0,
      updatedBy: "startup",
      lastAction: "switch_view",
      loopGuard: {
        mode: "single-dispatch-reducer",
        derivedViews: "read-only",
      },
    },
  };
}

export function sharedAtlasReducer(state: SharedAtlasState, action: SharedAtlasAction): SharedAtlasState {
  if (action.type === "switch_view") {
    return commitState({ ...state, mode: { activeView: action.view } }, action);
  }
  if (action.type === "select_node") {
    const selection = selectionFromNode(action.node, state.filters.timeRange, action.signal ?? nodeSignal(action.node));
    return commitState({ ...state, selection, focus: focusFromSelection(selection, action.source) }, action);
  }
  if (action.type === "select_time_range") {
    const filters = { ...state.filters, timeRange: action.range };
    const selection = { ...state.selection, timeRangeId: action.range.id, signal: "time_range" as const };
    return commitState({ ...state, filters, selection, focus: focusFromSelection(selection, action.source) }, action);
  }
  if (action.type === "clear_time_range") {
    const filters = { ...state.filters, timeRange: null };
    const selection = { ...state.selection, timeRangeId: null, signal: state.selection.nodeId ? state.selection.signal : "none" };
    return commitState({ ...state, filters, selection, focus: focusFromSelection(selection, action.source) }, action);
  }
  if (action.type === "select_contribution_period") {
    const selection = {
      ...state.selection,
      contributionPeriodId: action.period.id,
      signal: "contribution_period" as const,
    };
    return commitState({ ...state, selection, focus: focusFromSelection(selection, action.source) }, action);
  }
  if (action.type === "set_filters") {
    const filters = sharedFiltersFromAtlasFilters(action.filters, state.filters.timeRange, state.filters.roi);
    const selection = { ...state.selection, signal: "filter" as const };
    return commitState({ ...state, filters, selection, focus: focusFromSelection(selection, action.source) }, action);
  }
  if (action.type === "set_filter") {
    const filters = { ...state.filters, [action.key]: action.value };
    const selection = { ...state.selection, signal: "filter" as const };
    return commitState({ ...state, filters, selection, focus: focusFromSelection(selection, action.source) }, action);
  }
  if (action.type === "set_roi_filter") {
    const filters = { ...state.filters, roi: action.value };
    const selection = { ...state.selection, signal: "filter" as const };
    return commitState({ ...state, filters, selection, focus: focusFromSelection(selection, action.source) }, action);
  }
  if (action.type === "clear_filter") {
    const filters = clearSharedAtlasFilter(state.filters, action.key);
    const selection = {
      ...state.selection,
      timeRangeId: action.key === "timeRange" ? null : state.selection.timeRangeId,
      signal: "filter" as const,
    };
    return commitState({ ...state, filters, selection, focus: focusFromSelection(selection, action.source) }, action);
  }
  if (action.type === "reset_filters") {
    const filters = sharedFiltersFromAtlasFilters(DEFAULT_ATLAS_FILTERS, state.filters.timeRange, "all");
    const selection = { ...state.selection, signal: "filter" as const };
    return commitState({ ...state, filters, selection, focus: focusFromSelection(selection, action.source) }, action);
  }
  if (action.type === "clear_focus") {
    const selection = emptySelection(state.filters.timeRange);
    return commitState({ ...state, selection, focus: focusFromSelection(selection, action.source) }, action);
  }
  return state;
}

export function atlasFiltersFromSharedState(state: SharedAtlasState): AtlasFilters {
  return atlasFiltersFromSharedFilters(state.filters);
}

export function atlasFiltersFromSharedFilters(filters: SharedAtlasFilterState): AtlasFilters {
  return {
    query: filters.query,
    source: filters.source,
    tier: filters.tier,
    category: filters.category,
    theme: filters.theme,
  };
}

export function sharedFiltersFromAtlasFilters(
  filters: AtlasFilters,
  timeRange: SharedTimelineTimeRangeSelection | null = null,
  roi: SharedAtlasRoiFilter = "all",
): SharedAtlasFilterState {
  return {
    query: filters.query,
    source: filters.source,
    tier: filters.tier,
    category: filters.category,
    theme: filters.theme,
    timeRange,
    roi,
  };
}

export function clearSharedAtlasFilter(filters: SharedAtlasFilterState, key: SharedAtlasFilterKey): SharedAtlasFilterState {
  if (key === "query") return { ...filters, query: "" };
  if (key === "source") return { ...filters, source: "all" };
  if (key === "tier") return { ...filters, tier: "all" };
  if (key === "category") return { ...filters, category: "all" };
  if (key === "theme") return { ...filters, theme: "all" };
  if (key === "timeRange") return { ...filters, timeRange: null };
  return { ...filters, roi: "all" };
}

export function sharedContributionSelection(input: {
  id: string;
  scale: string;
  label: string;
  activityScore: number;
  filteredMemoryCount: number;
}): SharedContributionSelection {
  return input;
}

function commitState(state: SharedAtlasState, action: SharedAtlasAction): SharedAtlasState {
  return {
    ...state,
    sync: {
      ...state.sync,
      revision: state.sync.revision + 1,
      updatedBy: action.source,
      lastAction: action.type,
    },
  };
}

function emptySelection(timeRange: SharedTimelineTimeRangeSelection | null): SharedAtlasSelectionState {
  return {
    nodeId: null,
    nodeKind: null,
    clusterId: null,
    recordId: null,
    timeRangeId: timeRange?.id ?? null,
    contributionPeriodId: null,
    signal: timeRange ? "time_range" : "none",
  };
}

function selectionFromNode(
  node: AtlasNode,
  timeRange: SharedTimelineTimeRangeSelection | null,
  signal: SharedAtlasSignal,
): SharedAtlasSelectionState {
  return {
    nodeId: node.id,
    nodeKind: node.kind,
    clusterId: clusterIdForNode(node),
    recordId: node.memory_id ?? node.id,
    timeRangeId: timeRange?.id ?? null,
    contributionPeriodId: null,
    signal,
  };
}

function focusFromSelection(selection: SharedAtlasSelectionState, sourceView: SharedAtlasUpdateSource): SharedAtlasFocusState {
  const target: SharedAtlasFocusTarget = {
    nodeId: selection.nodeId,
    clusterId: selection.clusterId,
    recordId: selection.recordId,
    timeRangeId: selection.timeRangeId,
  };
  return {
    ...target,
    sourceView,
    home: target,
    galaxy: target,
    timeline: target,
    inspector: target,
    roiDashboard: target,
  };
}

function nodeSignal(node: AtlasNode): SharedAtlasSignal {
  return node.kind === "theme" ? "cluster" : "record";
}

function clusterIdForNode(node: AtlasNode): string | null {
  if (node.visual?.cluster) return node.visual.cluster;
  if (node.kind === "theme") return node.id.replace(/^theme:/, "");
  return null;
}
