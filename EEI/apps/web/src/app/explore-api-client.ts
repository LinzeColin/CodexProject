"use client";

export const EXPLORE_API_BASE_STORAGE_KEY = "eei.exploreApiBaseUrl.v1";
const SHARED_API_BASE_STORAGE_KEY = "eei.apiBaseUrl.v1";

export type ExploreGraphBudget = {
  max_nodes: number;
  max_edges: number;
  expand_nodes: number;
};

export type ExploreGraphRequest = {
  session_id?: string;
  focus: {
    object_type: "entity";
    object_id: string;
  };
  active_layers: string[];
  direction: "both" | "upstream" | "downstream" | "in" | "out";
  hops: number;
  as_of?: string | null;
  scoring_profile_version_id?: string | null;
  filters: Record<string, unknown>;
  budget: ExploreGraphBudget;
};

export type ExploreGraphRecord = {
  session_id: string;
  focus: {
    id?: string;
    canonical_name?: string;
    entity_type?: string;
  };
  query: {
    focus: {
      object_type: string;
      object_id: string;
    };
    direction: string;
    hops: number;
    as_of?: string | null;
    scoring_profile_version_id?: string | null;
    active_layers: string[];
    filters: Record<string, unknown>;
    budget: ExploreGraphBudget;
    hard_limits?: Record<string, number>;
  };
  nodes: ExploreGraphNodeRecord[];
  edges: ExploreGraphEdgeRecord[];
  truncated: boolean;
  truncation: {
    applied: boolean;
    reasons: string[];
    message: string;
    fetched_edge_count: number;
    returned_edge_count: number;
    returned_node_count: number;
  };
  continuation?: {
    available: boolean;
    expand_endpoint?: string | null;
    anchor_entity_id?: string | null;
    direction?: string | null;
    expand_nodes?: number | null;
  };
  warnings: string[];
  coverage: {
    visible_nodes: number;
    visible_edges: number;
    source_count: number;
    relationship_family_count: number;
    synthetic_fixture_edges: number;
    relationship_fact_candidates?: {
      total: number;
      published: number;
      excluded_unpublished: number;
      source_threshold_open: number;
      review_open: number;
      excluded_from_graph_edges: number;
      reason: string;
    };
  };
  production_context: {
    schema_version: "production-context-v1";
    request_as_of?: string | null;
    graph_query_version: string;
    scoring_service_version: string;
    active_scoring_profile_version_id?: string | null;
    active_scoring_profile?: {
      profile_key: string;
      version: number;
      model_key: string;
    } | null;
    active_analysis_context?: Record<string, unknown> | null;
    record_modes?: {
      published_relationships?: {
        database: number;
        fixture: number;
        total: number;
      };
      relationship_fact_candidates?: Record<string, number>;
    };
    candidate_fact_summary?: {
      total: number;
      published: number;
      unpublished: number;
      source_threshold_open: number;
      review_open: number;
    };
    publication_policy?: {
      relationship_fact_candidates_in_graph_edges: boolean;
      minimum_independent_sources: number;
      publish_requires_source_threshold: boolean;
      publish_requires_human_review: boolean;
    };
  };
};

export type ExploreGraphNodeRecord = {
  id: string;
  canonical_name: string;
  entity_type?: string;
  fixture_notice?: string | null;
  synthetic?: boolean | null;
};

export type ExploreGraphEdgeRecord = {
  id: string;
  subject_id: string;
  object_id: string;
  relationship_type: string;
  relationship_family: string;
  status?: string;
  confidence?: number | null;
  valid_from?: string | null;
  valid_to?: string | null;
  evidence_count?: number;
  synthetic?: boolean | null;
  fixture_notice?: string | null;
};

export type ExploreGraphSyncResult =
  | {
      mode: "server";
      status: "hydrated";
      endpoint: string;
      request: ExploreGraphRequest;
      record: ExploreGraphRecord;
    }
  | {
      mode: "server";
      status: "error";
      endpoint: string;
      reason: string;
      detail?: unknown;
    }
  | {
      mode: "local_fallback";
      status: "fixture";
      reason: "api_base_missing";
    };

export function readExploreApiBaseUrl() {
  const override = window.localStorage.getItem(EXPLORE_API_BASE_STORAGE_KEY)?.trim();
  const sharedOverride = window.localStorage.getItem(SHARED_API_BASE_STORAGE_KEY)?.trim();
  const configured = process.env.NEXT_PUBLIC_EEI_API_BASE_URL?.trim();
  return stripTrailingSlash(override || sharedOverride || configured || "");
}

export async function loadExploreGraph(
  request: ExploreGraphRequest
): Promise<ExploreGraphSyncResult> {
  const apiBaseUrl = readExploreApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "fixture", reason: "api_base_missing" };
  }

  const endpoint = `${apiBaseUrl}/v1/explore`;
  try {
    const response = await window.fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(request)
    });
    const payload = (await response.json().catch(() => null)) as unknown;
    if (!response.ok || !isExploreGraphRecord(payload)) {
      return {
        mode: "server",
        status: "error",
        endpoint,
        reason: `http_${response.status}`,
        detail: payload
      };
    }
    return {
      mode: "server",
      status: "hydrated",
      endpoint,
      request,
      record: payload
    };
  } catch (error) {
    return {
      mode: "server",
      status: "error",
      endpoint,
      reason: error instanceof Error ? error.name : "fetch_failed",
      detail: error instanceof Error ? error.message : String(error)
    };
  }
}

function isExploreGraphRecord(value: unknown): value is ExploreGraphRecord {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Partial<ExploreGraphRecord>;
  return (
    typeof record.session_id === "string" &&
    typeof record.query === "object" &&
    record.query !== null &&
    Array.isArray(record.nodes) &&
    record.nodes.every(isExploreGraphNodeRecord) &&
    Array.isArray(record.edges) &&
    record.edges.every(isExploreGraphEdgeRecord) &&
    typeof record.coverage === "object" &&
    record.coverage !== null &&
    typeof record.production_context === "object" &&
    record.production_context !== null &&
    record.production_context.schema_version === "production-context-v1"
  );
}

function isExploreGraphNodeRecord(value: unknown): value is ExploreGraphNodeRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "string" &&
    "canonical_name" in value &&
    typeof value.canonical_name === "string"
  );
}

function isExploreGraphEdgeRecord(value: unknown): value is ExploreGraphEdgeRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "string" &&
    "subject_id" in value &&
    typeof value.subject_id === "string" &&
    "object_id" in value &&
    typeof value.object_id === "string" &&
    "relationship_type" in value &&
    typeof value.relationship_type === "string" &&
    "relationship_family" in value &&
    typeof value.relationship_family === "string"
  );
}

function stripTrailingSlash(value: string) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}
