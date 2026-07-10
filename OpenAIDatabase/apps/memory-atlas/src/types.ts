export type ViewKey =
  | "home"
  | "galaxy"
  | "notion"
  | "roi"
  | "obsidian"
  | "timeline"
  | "contribution"
  | "wordcloud"
  | "search"
  | "summary";

export interface AtlasNode {
  id: string;
  kind: "memory" | "theme" | "tier" | "category" | "project" | "decision" | "timeline_event";
  label: string;
  memory_id?: string;
  statement?: string;
  date?: string;
  data_source?: string;
  source_label?: string;
  memory_tier?: string;
  category?: string;
  importance?: string;
  validity?: string;
  confidence?: string;
  visual?: {
    cluster?: string;
    color?: string;
    position?: { x: number; y: number; z: number };
    size?: number;
    brightness?: number;
    orbit_radius?: number;
    sensitive?: boolean;
    ring?: string;
  };
  metrics?: {
    weight_score?: number;
    roi?: {
      staleness_status?: string;
      leverage_score?: number;
      recommended_action?: string;
    };
  };
}

export interface AtlasEdge {
  id: string;
  source: string;
  target: string;
  kind: string;
  weight: number;
}

export interface ActivityBucket {
  date: string;
  conversation_count: number;
  message_count: number;
  user_message_count: number;
  assistant_message_count: number;
  memory_count: number;
  candidate_count: number;
  decision_count: number;
  core_memory_count: number;
  mid_long_memory_count: number;
  short_memory_count: number;
  tool_call_count?: number;
  error_event_count?: number;
  abort_count?: number;
  codex_session_count?: number;
  activity_score: number;
  activity_level: number;
}

export interface AtlasMetric {
  kind: string;
  values: Record<string, number>;
}

export interface BehaviorEvidenceRef {
  ref_id: string;
  ref_type?: string;
  source_id?: string;
  evidence_level?: string;
  path?: string;
  reason?: string;
}

export interface VisualFacetEvent {
  readonly event_id: string;
  readonly occurred_at: string;
  readonly source_id: string;
  readonly project: string;
  readonly task_type: string;
  readonly topic: string;
  readonly intent: string;
  readonly friction: readonly string[];
  readonly value_signal: readonly string[];
  readonly evidence_refs: readonly BehaviorEvidenceRef[];
}

export interface VisualFacetFilterOptions {
  readonly source: readonly string[];
  readonly project: readonly string[];
  readonly task: readonly string[];
}

export interface VisualWorkflow {
  readonly id: string;
  readonly family: string;
  readonly title_zh: string;
  readonly insight_header_zh: string;
  readonly human_question_zh: string;
  readonly action_value_zh: string;
  readonly visual_roi_gate_pass: boolean;
  readonly p0_included: boolean;
}

export interface VisualWorkflowRegistry {
  readonly schema_version: string;
  readonly p0_visual_count: number;
  readonly filter_dimensions: readonly string[];
  readonly visuals: readonly VisualWorkflow[];
  readonly excluded_candidates: readonly {
    id: string;
    title_zh: string;
    reason_zh: string;
    visual_roi_gate_pass: boolean;
    p0_included: boolean;
  }[];
}

export interface FormulaWhatIfPreview {
  readonly schema_version: string;
  readonly simulator_mode: string;
  readonly base_score: number;
  readonly summary_zh: string;
  readonly default_weights: Readonly<Record<string, number>>;
  readonly adjustable_weight_bounds: Readonly<Record<string, { min: number; max: number; step: number }>>;
  readonly baseline_signals: Readonly<Record<string, number>>;
  readonly rework_score: number;
  readonly formula_source: string;
  readonly scenarios: readonly {
    scenario_id: string;
    name_zh: string;
    description_zh: string;
    weighted_proxy_score: number;
    score_delta_vs_baseline: number;
    adjustable_weights: Readonly<Record<string, number>>;
    formula_source: string;
  }[];
  readonly safety: {
    active_config_write: false;
    proposal_required_before_apply: true;
    raw_mutation: false;
    financial_advice: false;
    precise_income_prediction: false;
  };
}

export interface BehaviorClusterSummary {
  cluster_id: string;
  cluster_type: string;
  label_zh: string;
  summary_zh: string;
  event_count: number;
  evidence_refs: BehaviorEvidenceRef[];
  representative_event_ids?: string[];
  filter_dimensions?: Record<string, unknown>;
}

export interface LowValueLoopSummary {
  loop_id: string;
  loop_type: string;
  label_zh: string;
  summary_zh: string;
  score: number;
  event_count: number;
  evidence_refs: BehaviorEvidenceRef[];
  decision_debt?: {
    debt_id?: string;
    decision_area?: string;
    suggested_closure_question?: string;
    status?: string;
  };
  action_half_life_days?: number;
  action_half_life_note?: string;
}

export interface OpportunitySummary {
  opportunity_id: string;
  opportunity_type: string;
  label_zh: string;
  summary_zh: string;
  score: number;
  confidence?: string;
  next_step_zh: string;
  opportunity_half_life_days?: number;
  defer_reason_zh?: string;
  evidence_refs: BehaviorEvidenceRef[];
  why_not_now_card?: {
    card_id?: string;
    reason_zh?: string;
    defer_until_signal_zh?: string;
    not_pressure_list?: boolean;
  };
}

export interface BehaviorIntelligenceSummary {
  schema_version: string;
  stage: "S06" | string;
  status: string;
  task_ids: string[];
  acceptance_ids: string[];
  source_files?: Record<string, string>;
  counts: {
    topic_clusters: number;
    hierarchy_clusters: number;
    clusters: number;
    low_value_loops: number;
    decision_debt: number;
    action_half_life: number;
    opportunities: number;
    defer_cards: number;
  };
  clusters: BehaviorClusterSummary[];
  facet_event_count?: number;
  facet_events?: VisualFacetEvent[];
  facet_filter_options?: VisualFacetFilterOptions;
  low_value_loops: LowValueLoopSummary[];
  opportunities: OpportunitySummary[];
  phase_boundary?: Record<string, unknown>;
}

export interface MemoryAtlas {
  schema_version: string;
  overview: {
    active_memory_count: number;
    candidate_count_latest_snapshot: number;
    conversation_count: number;
    node_count: number;
    edge_count: number;
    memory_node_count: number;
    theme_node_count: number;
    codex_session_count?: number;
    generated_at: string;
  };
  source_contract: {
    mode: string;
    export_profile: string;
    source_files: Record<string, string>;
    data_source_registry?: {
      schema_version: string;
      contract_version: string;
      registered_source_count: number;
      active_source_ids: string[];
      planned_source_ids: string[];
      canonical_required_fields: string[];
      mock_policy: string;
    };
    writeback_policy: {
      frontend_can_request_writeback: boolean;
      writeback_must_use_proposals: boolean;
      proposal_dir: string;
      history_dir: string;
      rollback_unit: string;
      proposal_schema_version: string;
      editable_fields: string[];
      frontend_payload_contract?: {
        target_ref: string;
        allowed_payload: string[];
        forbidden_payload: string[];
      };
      conflict_detection?: string[];
      direct_frontend_mutation_of_active_memory: boolean;
    };
  };
  visual_layers: {
    primary: string;
    secondary: string[];
    navigation: string;
  };
  nodes: AtlasNode[];
  edges: AtlasEdge[];
  timeline: Array<{
    date: string;
    node_id: string;
    memory_id: string;
    label: string;
    memory_tier: string;
    category: string;
    importance: string;
  }>;
  contribution: {
    metric_note: string;
    score_version: string;
    range_start: string;
    range_end: string;
    max_activity_score: number;
    quantiles: Record<string, number>;
    daily: ActivityBucket[];
    weekly: ActivityBucket[];
    monthly: ActivityBucket[];
    yearly: ActivityBucket[];
  };
  metrics: AtlasMetric[];
  data_sources?: DataSourceSummary[];
  behavior_intelligence?: BehaviorIntelligenceSummary;
  visual_workflows?: VisualWorkflowRegistry;
  formula_what_if?: FormulaWhatIfPreview;
  agent_recommendations?: AgentRecommendations;
}

export interface AtlasFilters {
  query: string;
  source: string;
  tier: string;
  category: string;
  theme: string;
}

export interface DataSourceSummary {
  id: string;
  label: string;
  description: string;
  platform?: string;
  status?: "active" | "planned" | string;
  ingestion_status?: string;
  record_types?: string[];
  node_count: number;
  activity_count: number;
  latest_date: string;
}

export interface AgentRecommendationItem {
  id: string;
  title: string;
  statement: string;
  source?: string;
  evidence_count?: number;
  confidence?: string;
  importance?: string;
  scope?: string;
  reason?: string;
}

export interface AgentRecommendationDiff {
  current: AgentRecommendationItem[];
  added: AgentRecommendationItem[];
  modified: Array<{
    before: AgentRecommendationItem;
    after: AgentRecommendationItem;
  }>;
  deleted: AgentRecommendationItem[];
}

export interface AgentRecommendations {
  schema_version: string;
  generated_at?: string;
  source?: string;
  session_count?: number;
  top_topics?: Array<{ label: string; count: number }>;
  memory: AgentRecommendationDiff;
  meta_data: AgentRecommendationDiff;
}
