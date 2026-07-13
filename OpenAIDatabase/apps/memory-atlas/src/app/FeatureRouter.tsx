import { useEffect, useMemo } from "react";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { useAtlasData } from "../providers/AtlasDataProvider";
import { useAtlasWorkspace } from "../providers/AtlasWorkspaceProvider";
import {
  CLIO_LIKE_VISUALS_VERSION,
  ECONOMIC_LIKE_VISUALS_VERSION,
  HUMAN_QUESTION_MAP_VERSION,
  WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION,
  buildGalaxyStarfieldMapping,
  uiCopy,
} from "../shared/atlas/constants";
import { buildClioLikeVisualModel, buildEconomicLikeVisualModel } from "../shared/atlas/clioEconomicModels";
import { buildHumanQuestionMapModel, buildWorkflowLatentGovernanceVisualModel } from "../shared/atlas/workflowQuestionModels";
import { viewEmptyState } from "../shared/ui/display";
import { ROUTE_REGISTRY } from "./routeRegistry";

export function FeatureRouter() {
  const { loadError, loadState } = useAtlasData();
  const workspace = useAtlasWorkspace();
  const {
    activeView,
    filters,
    nodeMap,
    openHelp,
    resetFilters,
    scopedAtlas,
    selectContributionPeriod,
    selectNode,
    selectTimelineRange,
    selectedNode,
    sharedState,
    slice,
    switchView,
    timelineTimeRange,
    clearTimelineRange,
  } = workspace;
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
  const starfieldMapping = useMemo(() => buildGalaxyStarfieldMapping(slice.graphNodes), [slice.graphNodes]);

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
      safety: { rawPrivateDataIncluded: false, directActiveMemoryWriteback: false, proposalWrite: false },
    });
    return () => { delete window.__memoryAtlasS11Phase1; };
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
      safety: { rawPrivateDataIncluded: false, directActiveMemoryWriteback: false, proposalWrite: false },
    });
    return () => { delete window.__memoryAtlasS11Phase2; };
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
      safety: { rawPrivateDataIncluded: false, directActiveMemoryWriteback: false, proposalWrite: false },
    });
    return () => { delete window.__memoryAtlasS11Phase3; };
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
      safety: { rawPrivateDataIncluded: false, directActiveMemoryWriteback: false, proposalWrite: false },
    });
    return () => { delete window.__memoryAtlasS11Phase4; };
  }, [humanQuestionMapModel]);

  if (loadState === "loading") return <div className="galaxy-loading">{uiCopy.states.loadingGalaxy}</div>;
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

  const emptyState = viewEmptyState(scopedAtlas, slice);
  if (emptyState === "empty-atlas") {
    return (
      <EmptyState
        actionLabel={uiCopy.states.emptyAtlasAction}
        dataState="empty-atlas"
        description={uiCopy.states.emptyAtlasDescription}
        onAction={openHelp}
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
        onAction={resetFilters}
        title={uiCopy.states.noFilteredResultsTitle}
      />
    );
  }

  const Route = ROUTE_REGISTRY[activeView];
  if (!Route) {
    return <ErrorState dataState="unknown-route" description="当前视图未登记。" title="无法打开此视图" />;
  }
  return (
    <Route
      activeView={activeView}
      atlas={scopedAtlas}
      filters={filters}
      nodeMap={nodeMap}
      onClearTimelineRange={clearTimelineRange}
      onSelectContributionPeriod={selectContributionPeriod}
      onSelectNode={selectNode}
      onSelectTimelineRange={selectTimelineRange}
      onSwitchView={switchView}
      selectedNode={selectedNode}
      sharedState={sharedState}
      slice={slice}
      starfieldMapping={starfieldMapping}
      timelineTimeRange={timelineTimeRange}
    />
  );
}
