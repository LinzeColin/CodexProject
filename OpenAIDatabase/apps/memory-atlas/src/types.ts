export type ViewKey =
  | "galaxy"
  | "notion"
  | "roi"
  | "obsidian"
  | "timeline"
  | "contribution"
  | "wordcloud"
  | "search";

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
  sensitivity?: string;
  retrieval_weight?: string;
  evidence_count?: number;
  source_kind?: string;
  source_file?: string;
  proposal_ref?: {
    schema_version: string;
    allowed_actions: string[];
    requires_conflict_check: boolean;
    client_payload?: string;
    conflict_tokens?: string;
  };
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
      retrieval_weight_score?: number;
      evidence_count?: number;
      recency_days?: number | null;
      decision_impact?: number;
      sensitivity_penalty?: number;
      staleness_status?: string;
      leverage_score?: number;
      recommended_action?: string;
    };
    usage?: Record<string, number>;
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
