import type { Dispatch, PropsWithChildren } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { filterMemoryNodes, getMemoryNodes, getNodeMap, getThemeNodes, normalizeMemoryTier, uniqueSorted } from "../data/atlas";
import {
  atlasFiltersFromSharedState,
  createSharedAtlasState,
  sharedAtlasReducer,
  sharedContributionSelection,
  type SharedAtlasAction,
  type SharedAtlasState,
} from "../state/sharedAtlasState";
import type { AtlasFilters, AtlasNode, MemoryAtlas, ViewKey } from "../types";
import { DEFAULT_MEMORY_ATLAS_VIEW, defaultFilters } from "../shared/atlas/constants";
import type { ContributionPeriodDetail, FilterKey, FilteredAtlasSlice, SourceOption, TimelineTimeRangeSelection } from "../shared/atlas/contracts";
import {
  buildFilteredSlice,
  buildSourceOptions,
  buildSourceScopedAtlas,
  selectionStillVisible,
  selectableLensNodes,
  sourceMatchesNode,
} from "../shared/atlas/sourceSlice";
import { useAtlasData } from "./AtlasDataProvider";

export interface AtlasWorkspaceContextValue {
  activeView: ViewKey;
  categories: string[];
  clearFilter: (key: FilterKey) => void;
  clearTimelineRange: () => void;
  dispatchSharedState: Dispatch<SharedAtlasAction>;
  filters: AtlasFilters;
  focusSelectedTheme: () => void;
  closeHelp: () => void;
  helpOpen: boolean;
  nodeMap: Map<string, AtlasNode>;
  resetFilters: () => void;
  openHelp: () => void;
  openHelpView: (view: ViewKey) => void;
  scopedAtlas: MemoryAtlas;
  selectAdjacentNode: (direction: -1 | 1) => void;
  selectContributionPeriod: (detail: ContributionPeriodDetail) => void;
  selectNode: (node: AtlasNode) => void;
  selectTimelineRange: (range: TimelineTimeRangeSelection) => void;
  selectedContributionPeriod: ContributionPeriodDetail | null;
  selectedNode: AtlasNode | null;
  sharedState: SharedAtlasState;
  slice: FilteredAtlasSlice;
  sourceOptions: SourceOption[];
  switchView: (view: ViewKey) => void;
  themeOptions: Array<{ id: string; label: string }>;
  tiers: string[];
  timelineTimeRange: TimelineTimeRangeSelection | null;
  updateFilters: (updater: (current: AtlasFilters) => AtlasFilters) => void;
}

const AtlasWorkspaceContext = createContext<AtlasWorkspaceContextValue | null>(null);

export function AtlasWorkspaceProvider({ children }: PropsWithChildren) {
  const { atlas, loadState, revision } = useAtlasData();
  const [sharedState, dispatchSharedState] = useReducer(
    sharedAtlasReducer,
    undefined,
    () => createSharedAtlasState({ activeView: DEFAULT_MEMORY_ATLAS_VIEW, filters: defaultFilters }),
  );
  const [selectedContributionPeriod, setSelectedContributionPeriod] = useState<ContributionPeriodDetail | null>(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const handledRevisionRef = useRef(0);
  const activeView = sharedState.mode.activeView;
  const filters = useMemo(() => atlasFiltersFromSharedState(sharedState), [sharedState]);
  const timelineTimeRange = sharedState.filters.timeRange;
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
    () => themeNodes
      .map((node) => ({ id: node.visual?.cluster ?? node.id.replace("theme:", ""), label: node.label }))
      .sort((left, right) => left.label.localeCompare(right.label, "zh-CN")),
    [themeNodes],
  );
  const filteredMemoryNodes = useMemo(() => filterMemoryNodes(sourceMemoryNodes, filters), [sourceMemoryNodes, filters]);
  const slice = useMemo(
    () => buildFilteredSlice(scopedAtlas, filteredMemoryNodes, filters),
    [filteredMemoryNodes, filters, scopedAtlas],
  );

  const selectNode = useCallback((node: AtlasNode) => {
    setSelectedContributionPeriod(null);
    dispatchSharedState({ type: "select_node", node, source: activeView });
  }, [activeView]);
  const selectContributionPeriod = useCallback((detail: ContributionPeriodDetail) => {
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
  const selectTimelineRange = useCallback((range: TimelineTimeRangeSelection) => {
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
    if (view !== "contribution") setSelectedContributionPeriod(null);
    dispatchSharedState({ type: "switch_view", view, source: activeView });
  }, [activeView]);
  const openHelpView = useCallback((view: ViewKey) => {
    switchView(view);
    setHelpOpen(false);
  }, [switchView]);
  const focusSelectedTheme = useCallback(() => {
    const theme = selectedNode?.visual?.cluster;
    if (!theme) return;
    setSelectedContributionPeriod(null);
    dispatchSharedState({ type: "set_filter", key: "theme", value: theme, source: activeView });
  }, [activeView, selectedNode?.visual?.cluster]);
  const clearFilter = useCallback((key: FilterKey) => {
    setSelectedContributionPeriod(null);
    dispatchSharedState({ type: "clear_filter", key, source: activeView });
  }, [activeView]);
  const resetFilters = useCallback(() => {
    setSelectedContributionPeriod(null);
    dispatchSharedState({ type: "reset_filters", source: activeView });
  }, [activeView]);
  const selectAdjacentNode = useCallback((direction: -1 | 1) => {
    const candidates = selectableLensNodes(slice, selectedNode);
    if (candidates.length < 2) return;
    const currentIndex = candidates.findIndex((node) => node.id === selectedNode?.id);
    if (currentIndex < 0) return;
    selectNode(candidates[(currentIndex + direction + candidates.length) % candidates.length]);
  }, [selectNode, selectedNode, slice]);

  useEffect(() => {
    if (loadState !== "ready") return;
    if (revision && handledRevisionRef.current !== revision) {
      handledRevisionRef.current = revision;
      const firstNode = getMemoryNodes(atlas)[0] ?? atlas.nodes[0] ?? null;
      if (firstNode) dispatchSharedState({ type: "select_node", node: firstNode, source: "startup" });
      return;
    }
    if (selectedNode && selectionStillVisible(selectedNode, slice)) return;
    const fallbackNode = slice.memoryNodes[0] ?? slice.graphNodes[0] ?? scopedAtlas.nodes[0] ?? null;
    if (fallbackNode) dispatchSharedState({ type: "select_node", node: fallbackNode, source: "system" });
    else if (sharedState.selection.nodeId) dispatchSharedState({ type: "clear_focus", source: "system" });
  }, [atlas, loadState, revision, scopedAtlas.nodes, selectedNode, sharedState.selection.nodeId, slice]);

  const value = useMemo<AtlasWorkspaceContextValue>(() => ({
    activeView,
    categories,
    closeHelp: () => setHelpOpen(false),
    clearFilter,
    clearTimelineRange,
    dispatchSharedState,
    filters,
    focusSelectedTheme,
    helpOpen,
    nodeMap,
    openHelp: () => setHelpOpen(true),
    openHelpView,
    resetFilters,
    scopedAtlas,
    selectAdjacentNode,
    selectContributionPeriod,
    selectNode,
    selectTimelineRange,
    selectedContributionPeriod,
    selectedNode,
    sharedState,
    slice,
    sourceOptions,
    switchView,
    themeOptions,
    tiers,
    timelineTimeRange,
    updateFilters,
  }), [
    activeView, categories, clearFilter, clearTimelineRange, filters, focusSelectedTheme, helpOpen, nodeMap, openHelpView, resetFilters,
    scopedAtlas, selectAdjacentNode, selectContributionPeriod, selectNode, selectTimelineRange,
    selectedContributionPeriod, selectedNode, sharedState, slice, sourceOptions, switchView, themeOptions, tiers,
    timelineTimeRange, updateFilters,
  ]);

  return <AtlasWorkspaceContext.Provider value={value}>{children}</AtlasWorkspaceContext.Provider>;
}

export function useAtlasWorkspace(): AtlasWorkspaceContextValue {
  const context = useContext(AtlasWorkspaceContext);
  if (!context) throw new Error("useAtlasWorkspace must be used within AtlasWorkspaceProvider");
  return context;
}
