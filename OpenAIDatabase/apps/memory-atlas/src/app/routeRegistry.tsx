import type { ComponentType } from "react";
import type { SharedAtlasState } from "../state/sharedAtlasState";
import type { AtlasFilters, AtlasNode, MemoryAtlas, ViewKey } from "../types";
import type { StarfieldMappingResult } from "../models/starfieldMapping";
import { ContributionGrid, HomeOverviewView, RoiDashboard, WordCloudView } from "../features/overview";
import { GalaxyView, ObsidianGraph, TimelineView } from "../features/assets";
import { DataGuideMap } from "../features/topics";
import { SearchReview } from "../features/search-review";
import { SummaryIterationView } from "../features/summary-iteration";
import type {
  ContributionPeriodDetail,
  FilteredAtlasSlice,
  TimelineTimeRangeSelection,
} from "../shared/atlas/contracts";

export interface FeatureRouteProps {
  activeView: ViewKey;
  atlas: MemoryAtlas;
  filters: AtlasFilters;
  nodeMap: Map<string, AtlasNode>;
  onClearTimelineRange: () => void;
  onSelectContributionPeriod: (detail: ContributionPeriodDetail) => void;
  onSelectNode: (node: AtlasNode) => void;
  onSelectTimelineRange: (range: TimelineTimeRangeSelection) => void;
  onSwitchView: (view: ViewKey) => void;
  selectedNode: AtlasNode | null;
  sharedState: SharedAtlasState;
  slice: FilteredAtlasSlice;
  starfieldMapping: StarfieldMappingResult;
  timelineTimeRange: TimelineTimeRangeSelection | null;
}

export type RouteComponent = ComponentType<FeatureRouteProps>;

export const ROUTE_REGISTRY = {
  home: (props) => (
    <HomeOverviewView
      atlas={props.atlas}
      nodes={props.slice.memoryNodes}
      graphEdges={props.slice.graphEdges}
      deltaStats={props.slice.deltaStats}
      selectedNode={props.selectedNode}
      sharedState={props.sharedState}
      timelineTimeRange={props.timelineTimeRange}
      onSelectNode={props.onSelectNode}
      onSwitchView={props.onSwitchView}
    />
  ),
  galaxy: (props) => (
    <GalaxyView
      graphNodes={props.slice.graphNodes}
      graphEdges={props.slice.graphEdges}
      memoryCount={props.slice.memoryNodes.length}
      selectedNode={props.selectedNode}
      sharedState={props.sharedState}
      deltaStats={props.slice.deltaStats}
      timelineTimeRange={props.timelineTimeRange}
      starfieldMapping={props.starfieldMapping}
      onSelectNode={props.onSelectNode}
    />
  ),
  notion: (props) => (
    <DataGuideMap
      nodes={props.slice.graphNodes}
      edges={props.slice.graphEdges}
      selectedNode={props.selectedNode}
      deltaStats={props.slice.deltaStats}
      parentSnapshotId={props.atlas.overview.generated_at || props.atlas.schema_version}
      onSelectNode={props.onSelectNode}
    />
  ),
  roi: (props) => (
    <RoiDashboard
      atlas={props.atlas}
      nodes={props.slice.memoryNodes}
      deltaStats={props.slice.deltaStats}
      onSelectNode={props.onSelectNode}
    />
  ),
  obsidian: (props) => (
    <ObsidianGraph
      nodes={props.slice.graphNodes}
      edges={props.slice.graphEdges}
      selectedNode={props.selectedNode}
      sharedState={props.sharedState}
      deltaStats={props.slice.deltaStats}
      onSelectNode={props.onSelectNode}
    />
  ),
  timeline: (props) => (
    <TimelineView
      timeline={props.slice.timeline}
      nodeMap={props.nodeMap}
      selectedNode={props.selectedNode}
      sharedState={props.sharedState}
      selectedTimelineRange={props.timelineTimeRange}
      deltaStats={props.slice.deltaStats}
      onSelectNode={props.onSelectNode}
      onSelectTimelineRange={props.onSelectTimelineRange}
      onClearTimelineRange={props.onClearTimelineRange}
    />
  ),
  contribution: (props) => (
    <ContributionGrid
      atlas={props.atlas}
      nodes={props.slice.memoryNodes}
      filters={props.filters}
      deltaStats={props.slice.deltaStats}
      onSelectPeriod={props.onSelectContributionPeriod}
    />
  ),
  wordcloud: (props) => (
    <WordCloudView nodes={props.slice.memoryNodes} deltaStats={props.slice.deltaStats} onSelectNode={props.onSelectNode} />
  ),
  search: (props) => (
    <SearchReview
      atlas={props.atlas}
      filters={props.filters}
      nodes={props.slice.memoryNodes}
      deltaStats={props.slice.deltaStats}
      onSelectNode={props.onSelectNode}
      onSwitchView={props.onSwitchView}
    />
  ),
  summary: (props) => (
    <SummaryIterationView atlas={props.atlas} nodes={props.slice.memoryNodes} deltaStats={props.slice.deltaStats} />
  ),
} satisfies Record<ViewKey, RouteComponent>;
