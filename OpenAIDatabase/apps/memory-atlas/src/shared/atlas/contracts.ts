import type { ComponentType } from "react";
import type { AtlasEdge, AtlasFilters, AtlasNode, MemoryAtlas, ViewKey } from "../../types";
import { type SharedTimelineTimeRangeSelection } from "../../state/sharedAtlasState";
import { CLIO_LIKE_VISUALS_VERSION, ECONOMIC_LIKE_VISUALS_VERSION, HOME_ARRIVAL_CATEGORY_LABELS, HUMAN_QUESTION_MAP_VERSION, REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION, SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION, WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION } from "./constants";



export type ContributionScale = "day" | "week" | "month" | "year";


export type WritebackAction = "update_statement" | "add_context" | "change_tier" | "flag_conflict" | "rollback_to_version";


export type FilterKey = keyof AtlasFilters;


export type TimelineInteractionMode = "pan" | "brush";



export interface TimelineEvent {
  date: string;
  node_id: string;
  memory_id: string;
  label: string;
  memory_tier: string;
  category: string;
  importance: string;
}



export interface TimelineLayoutControls {
  zoom: number;
  center: number;
  cursor: number;
}



export type MemoryRiverLevel = "Macro" | "Meso" | "Micro";



export interface TimelineDisplayEvent {
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



export type TimelineTimeRangeSelection = SharedTimelineTimeRangeSelection;



export interface TimelineBrushDraft {
  pointerId: number;
  startX: number;
  endX: number;
}



export interface TimelinePanDraft {
  pointerId: number;
  startX: number;
  startCenter: number;
}



export interface TimelineFeedbackSettings {
  reducedMotion: boolean;
  pseudoHaptic: boolean;
  audio: boolean;
}



export interface MemoryRiverLevelBand {
  level: MemoryRiverLevel;
  note: string;
  y: number;
}



export interface MemoryRiverLane {
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



export interface MemoryRiverMarker {
  id: string;
  kind: "black-hole" | "proto-star" | "memory-event";
  event: TimelineDisplayEvent;
  title: string;
  x: number;
  y: number;
  radius: number;
}



export type MemoryRiverEvidenceKind = "black-hole-lifecycle" | "proto-star-lifecycle" | "stale-deprecated";



export interface MemoryRiverEvidencePoint {
  id: string;
  x: number;
  y: number;
  radius: number;
  label: string;
}



export interface MemoryRiverEvidenceSegment {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  strength: number;
}



export interface MemoryRiverEvidenceLayer {
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



export interface MemoryRiverRoiGradientBand {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  score: number;
  color: string;
  label: string;
}



export interface MemoryRiverRoiGradient {
  label: string;
  signal: string;
  averageRoiScore: number;
  highLeverageCount: number;
  capabilityGrowthCount: number;
  bands: MemoryRiverRoiGradientBand[];
}



export interface MemoryRiverLayout {
  levels: MemoryRiverLevelBand[];
  lanes: MemoryRiverLane[];
  evidenceLayers: MemoryRiverEvidenceLayer[];
  roiGradient: MemoryRiverRoiGradient;
  markers: MemoryRiverMarker[];
  levelCounts: Record<MemoryRiverLevel, number>;
}



export interface DeltaStats {
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



export interface FilteredAtlasSlice {
  memoryNodes: AtlasNode[];
  graphNodes: AtlasNode[];
  graphEdges: AtlasEdge[];
  timeline: TimelineEvent[];
  visibleNodeIds: Set<string>;
  deltaStats: DeltaStats;
  filterActive: boolean;
}



export type ReviewPeriodId = "last_30_days" | "last_90_days" | "all";



export type ReviewPanelId =
  | "review_period_selector"
  | "theme_change_panel"
  | "opportunity_panel"
  | "low_value_loop_panel"
  | "decision_change_panel"
  | "next_action_panel"
  | "proposal_decision_panel"
  | "iteration_backlog";



export type ReviewQuestionId =
  | "dominant_topics"
  | "strengthening_topics"
  | "declining_topics"
  | "new_opportunities"
  | "low_value_loops"
  | "decision_changes"
  | "next_actions"
  | "proposal_decision";



export interface ReviewSignalRow {
  title: string;
  summary: string;
  count: number;
  evidence_refs: string[];
}



export interface ReviewNextAction {
  action_id: string;
  title: string;
  reason: string;
  priority: "high" | "medium" | "low";
  source_scope: "redacted_atlas_snapshot" | "agent_recommendations_redacted";
  evidence_refs: string[];
  acceptance_hint: string;
}



export interface ReviewIterationItem {
  item_id: string;
  title: string;
  why_it_matters: string;
  next_step: string;
  acceptance_hint: string;
  priority: "high" | "medium" | "low";
}



export interface ReviewQuestionAnswer {
  question_id: ReviewQuestionId;
  panel_id: ReviewPanelId;
  question: string;
  answer: string;
  evidence_refs: string[];
}



export interface ReviewSummaryIterationOutput {
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



export type SummaryClosurePanelId = "change_comparison" | "stale_conflict_signals" | "proposal_candidates";



export interface SummaryClosureChangeRow {
  signal_id: string;
  title: string;
  summary: string;
  current_count: number;
  previous_count: number;
  delta: number;
  evidence_refs: string[];
}



export interface SummaryClosureSignal {
  signal_id: string;
  signal_type: "stale" | "conflict";
  severity: "high" | "medium" | "low";
  title: string;
  summary: string;
  evidence_refs: string[];
  proposal_hint: string;
  rollback_hint: string;
}



export interface SummaryClosureProposalCandidate {
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



export interface SummaryIterationClosureOutput {
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



export interface SourceOption {
  id: string;
  label: string;
  description: string;
  node_count: number;
}



export interface PeriodCounts {
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



export type TrendSlot = Pick<PeriodCounts, "activityLevel" | "activityScore"> | null;



export interface ContributionPeriodDetail {
  scale: ContributionScale;
  bucket: PeriodCounts;
  relatedNodes: AtlasNode[];
}



export interface HumanOverview {
  topicRows: Array<{ label: string; count: number }>;
  tierRows: Array<{ label: string; count: number }>;
  categoryRows: Array<{ label: string; count: number }>;
  rememberItems: string[];
  actionItems: string[];
  opportunityItems: string[];
  riskItems: string[];
}



export interface HomeSignalCard {
  id: string;
  title: string;
  value: string;
  note: string;
  tone: "weather" | "dominant" | "rising" | "declining" | "black-hole" | "proto-star";
}



export type HomeArrivalBriefingCardId = keyof typeof HOME_ARRIVAL_CATEGORY_LABELS;



export interface HomeArrivalBriefingCard {
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

export interface HomeActionDetail {
  action_id: string;
  title: string;
  action_type: "continue" | "review" | "consolidate" | "explore" | "defer";
  priority: string;
  reason: string;
  roi_score: number;
  effort_cost: "low" | "medium" | "high";
  urgency: "low" | "medium" | "high";
  confidence: number;
  source: string;
  status: "proposed" | "review" | "blocked" | "done_safe";
  evidence_count: number;
  evidence_refs: string[];
  matched_reason: string;
  linked_topic_ids: string[];
  linked_asset_ids: string[];
  next_step: string;
  recommended_time_window: "now" | "today" | "this_week" | "later";
  proposal_hint: "proposal_recommended" | "proposal_not_needed";
  rollback_hint: string;
  proposal_only: true;
}

export interface TierAssetDetail {
  asset_id: string;
  asset_tier: "core_profile" | "project" | "decision" | "workflow" | "knowledge" | "opportunity" | "stale";
  title: string;
  summary: string;
  theme: string;
  value_score: number;
  updated_at: string;
  importance: "high" | "medium" | "low";
  priority: "p0" | "p1" | "p2" | "p3" | "watch";
  confidence: number;
  staleness_status: "current" | "needs_review" | "stale" | "unknown";
  last_seen_range: string;
  evidence_count: number;
  evidence_refs: string[];
  source_scope: string;
  linked_action_ids: string[];
  linked_topic_ids: string[];
  recommended_asset_action: "keep" | "review" | "consolidate" | "lower_priority" | "validate" | "defer";
  proposal_hint: "proposal_recommended" | "proposal_not_needed";
  rollback_hint: string;
  proposal_only: true;
}

export interface TopicClassificationDetail {
  topic_id: string;
  topic_label: string;
  parent_topic: string;
  category: string;
  topic_state: "dominant" | "rising" | "declining" | "emerging" | "conflict" | "black_hole" | "stale";
  topic_strength: number;
  trend: "up" | "stable" | "down";
  roi_score: number;
  conflict_score: number;
  confidence: number;
  record_count: number;
  recent_count: number;
  representative_record_ids: string[];
  evidence_refs: string[];
  matched_reason: string;
  linked_asset_ids: string[];
  linked_action_ids: string[];
  starfield_handoff: string;
  river_handoff: string;
  proposal_hint: "proposal_recommended" | "proposal_not_needed";
  rollback_hint: string;
  proposal_only: true;
}



export interface HomeAction extends HomeActionDetail {
  id: string;
  targetView: ViewKey;
  node: AtlasNode | null;
}



export interface HomeTierAsset extends TierAssetDetail {
  id: string;
  targetView: ViewKey;
  node: AtlasNode | null;
}



export interface HomeTopicDetail extends TopicClassificationDetail {
  id: string;
  targetView: ViewKey;
  node: AtlasNode | null;
  nodes: AtlasNode[];
}



export type ClioLikeVisualId = "cluster_tree" | "bubble_map" | "topic_cluster_explorer";



export interface ClioClusterDatum {
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



export interface ClioTreeBranch {
  id: string;
  label: string;
  count: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  node: AtlasNode | null;
}



export interface ClioLikeVisualCopy {
  id: ClioLikeVisualId;
  title: string;
  insightHeader: string;
  humanQuestion: string;
  actionValue: string;
}



export interface ClioLikeVisualModel {
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



export type EconomicLikeVisualId = "task_treemap" | "automation_vs_augmentation" | "roi_scatter" | "opportunity_radar";



export interface EconomicLikeVisualCopy {
  id: EconomicLikeVisualId;
  title: string;
  insightHeader: string;
  humanQuestion: string;
  actionValue: string;
}



export interface EconomicTaskDatum {
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



export interface EconomicRadarAxis {
  id: string;
  label: string;
  value: number;
}



export interface EconomicLikeVisualModel {
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



export type WorkflowLatentGovernanceVisualId =
  | "agent_decision_sankey"
  | "friction_heatmap"
  | "latent_radar"
  | "evidence_timeline"
  | "formula_explorer";



export interface WorkflowLatentGovernanceVisualCopy {
  id: WorkflowLatentGovernanceVisualId;
  title: string;
  insightHeader: string;
  humanQuestion: string;
  actionValue: string;
}



export interface WorkflowSankeyLinkDatum {
  id: string;
  sourceLabel: string;
  targetLabel: string;
  value: number;
  width: number;
  y: number;
  color: string;
  node: AtlasNode | null;
}



export interface FrictionHeatmapCellDatum {
  id: string;
  rowLabel: string;
  columnLabel: string;
  count: number;
  intensity: number;
  action: string;
  node: AtlasNode | null;
}



export interface LatentRadarDatum {
  id: string;
  label: string;
  value: number;
  confidenceLabel: string;
  evidenceBadge: string;
  node: AtlasNode | null;
}



export interface EvidenceTimelineDatum {
  id: string;
  label: string;
  dateLabel: string;
  x: number;
  evidenceCount: number;
  sourceLabel: string;
  node: AtlasNode | null;
}



export interface FormulaInspectorDatum {
  id: string;
  label: string;
  value: string;
  description: string;
  sourcePath: string;
  node: AtlasNode | null;
}



export interface WorkflowLatentGovernanceVisualModel {
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



export type HumanQuestionMapVisualId = ClioLikeVisualId | EconomicLikeVisualId | WorkflowLatentGovernanceVisualId;


export type HumanQuestionMapFamilyId = "clio_like" | "economic_like" | "workflow_governance";



export interface HumanQuestionMapEntry {
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



export interface HumanQuestionMapExcludedCandidate {
  id: string;
  title: string;
  reason: string;
  visualRoiGatePass: false;
  p0Included: false;
}



export interface HumanQuestionMapModel {
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



export interface MemoryWeatherV2 {
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



export interface MiniStarfieldPoint {
  id: string;
  label: string;
  x: number;
  y: number;
  radius: number;
  color: string;
  node: AtlasNode;
}



export interface RiverPulseSegment {
  id: string;
  label: string;
  recentCount: number;
  previousCount: number;
  delta: number;
  intensity: number;
  node: AtlasNode | null;
}



export interface HomeInspectorLink {
  id: string;
  title: string;
  meta: string;
  node: AtlasNode | null;
}



export type Search2TierFilter = "all" | "core_profile" | "project" | "decision" | "workflow" | "knowledge" | "opportunity" | "stale";


export type Search2RecencyFilter = "all" | "recent" | "active" | "stale" | "archival";


export type Search2ImportanceFilter = "all" | "low" | "medium" | "high" | "critical";



export interface Search2Filters {
  query: string;
  tier: Search2TierFilter;
  topic: string;
  recency: Search2RecencyFilter;
  importance: Search2ImportanceFilter;
  evidenceOnly: boolean;
}



export interface Search2Result {
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



export interface Search2SessionSummary {
  query: string;
  result_count: number;
  dominant_topics: string[];
  high_importance_hits: string[];
  stale_or_black_hole_hits: string[];
  missing_evidence: string[];
  next_step: string;
  proposal_candidate: boolean;
}



export interface SemanticInsight {
  label: string;
  count: number;
  roiScore: number;
  recentCount: number;
  nodes: AtlasNode[];
}



export interface SemanticMatrixCell {
  topic: string;
  tier: string;
  count: number;
  nodes: AtlasNode[];
}



export interface WordCloudItem {
  label: string;
  count: number;
  score: number;
  x: number;
  y: number;
  rotate: number;
  nodes: AtlasNode[];
}



export interface WritebackProposal {
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



export interface InspectorFormulaRow {
  label: string;
  value: string;
  formula: string;
  parameters: string;
}



export interface InspectorEvidenceRow {
  label: string;
  value: string;
}



export interface InspectorExplanation {
  summary: string;
  formulas: InspectorFormulaRow[];
  evidence: InspectorEvidenceRow[];
  safetyNotes: string[];
}



export interface WritebackProposalDraftInput {
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



export interface HeatStop {
  stop: number;
  rgb: readonly [number, number, number];
}



export interface RuntimeState {
  runStartedAt: Date;
  snapshotLoadedAt: Date | null;
  lifecycle: "载入中" | "已同步" | "读取失败";
  serverMode: "检测中" | "本地自释放" | "静态托管";
  commandApiAvailable: boolean;
  proposalApiAvailable: boolean;
  ownerDailyApiAvailable: boolean;
}
