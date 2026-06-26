"use client";

export const PRODUCTION_DATA_API_BASE_STORAGE_KEY = "eei.productionDataApiBaseUrl.v1";
const SHARED_API_BASE_STORAGE_KEY = "eei.apiBaseUrl.v1";

export type CatalogSummaryRecord = {
  catalog_id: string;
  catalog_key: string;
  name_zh: string;
  path: string;
  primary_key: string;
  row_count: number;
  owner: string;
  ui_surfaces: string;
  scope: string;
  status: string;
  source_of_truth: boolean;
  export_links: Record<string, string>;
};

export type SupplyChainStageRecord = {
  stage_id: string;
  stage_order: number;
  slug: string;
  name_zh: string;
  name_en: string;
  default_direction: string;
  relationship_count: number;
  upstream_edge_count: number;
  downstream_edge_count: number;
  unknown_count: number;
};

export type SupplyChainEdgeRecord = {
  id: string;
  subject: { id: string; canonical_name: string; entity_type: string };
  object: { id: string; canonical_name: string; entity_type: string };
  relationship_type: string;
  relationship_family: string;
  status: string;
  stage_from: string | null;
  stage_from_name: string;
  stage_to: string | null;
  stage_to_name: string;
  chain_side: "upstream" | "downstream" | "midstream" | "unknown";
  tier: string;
  materiality: string;
  substitutability: string | number;
  geography: string | unknown[];
  capacity: "unknown" | { value: number; unit: string | null };
  amount: "unknown" | { value: number; currency: string | null; kind: string | null };
  time: Record<string, unknown>;
  evidence_count: number;
  unknown_fields: string[];
  synthetic: boolean;
  fixture_notice: string | null;
};

export type SupplyChainRecord = {
  schema_version: "entity-supply-chain-v1";
  as_of: string;
  focus: { id: string; canonical_name: string; entity_type: string };
  directional_summary: {
    upstream_edge_count: number;
    downstream_edge_count: number;
    supports_upstream_downstream: boolean;
  };
  chain_stages: SupplyChainStageRecord[];
  edges: SupplyChainEdgeRecord[];
  unknowns: {
    relationship_id: string;
    field: string;
    status: "unknown";
    message: string;
  }[];
  coverage: {
    ordered_stage_count: number;
    covered_stage_count: number;
    edge_count: number;
    evidence_source_count: number;
    all_edges_have_evidence: boolean;
    edge_metadata_fields: string[];
    unknowns_explicit: boolean;
  };
  content_rules: Record<string, unknown>;
  data_mode: string;
  fixture_notice: string | null;
};

export type SemanticBucketRecord = {
  key: string;
  label: string;
  dimension: string;
  description: string;
  record_count: number;
  amount_record_count: number;
  unknown_count: number;
  required: boolean;
};

export type CapitalPolicyRelationshipRecord = {
  id: string;
  relationship_type: string;
  relationship_family: string;
  status: string;
  confidence: number | null;
  semantic_class: string;
  semantic_tags: string[];
  direction: "in" | "out" | "neutral";
  subject: { id: string; canonical_name: string; entity_type: string };
  object: { id: string; canonical_name: string; entity_type: string };
  amount_semantics: {
    amount: number | null;
    currency: string | null;
    amount_kind: string | null;
    unknown_not_zero: boolean;
    aggregation_rule: string;
    aggregation_key: string;
    summable: boolean;
  };
  time: Record<string, unknown>;
  qualifiers?: Record<string, unknown>;
  evidence_count: number;
  unknown_fields: string[];
  synthetic: boolean;
  fixture_notice: string | null;
};

export type CapitalPolicyEventRecord = {
  id: string;
  event_type: string;
  title: string;
  status: string;
  semantic_class: string;
  semantic_tags: string[];
  amount_semantics: CapitalPolicyRelationshipRecord["amount_semantics"];
  time: Record<string, unknown>;
  evidence_count: number;
  unknown_fields: string[];
  participants: unknown[];
};

export type EntityCapitalMapRecord = {
  schema_version: "entity-capital-map-v1";
  as_of: string;
  focus: { id: string; canonical_name: string; entity_type: string };
  relationships: CapitalPolicyRelationshipRecord[];
  events: CapitalPolicyEventRecord[];
  semantic_buckets: SemanticBucketRecord[];
  coverage: {
    relationship_count: number;
    event_count: number;
    semantic_class_count: number;
    required_semantic_classes: string[];
    no_silent_summing: boolean;
    unknown_amount_not_zero: boolean;
  };
  content_rules: Record<string, unknown>;
  data_mode: string;
  fixture_notice: string | null;
};

export type EntityPolicyMapRecord = {
  schema_version: "entity-policy-map-v1";
  as_of: string;
  focus: { id: string; canonical_name: string; entity_type: string };
  policy_records: CapitalPolicyRelationshipRecord[];
  technology_records: CapitalPolicyRelationshipRecord[];
  events: CapitalPolicyEventRecord[];
  semantic_buckets: SemanticBucketRecord[];
  coverage: {
    policy_record_count: number;
    technology_record_count: number;
    event_count: number;
    policy_semantic_classes: string[];
    technology_semantic_classes: string[];
    unknowns_explicit: boolean;
  };
  content_rules: Record<string, unknown>;
  data_mode: string;
  fixture_notice: string | null;
};

export type CatalogInventoryRecord = {
  as_of: string;
  catalog_version: string;
  catalog_count: number;
  source_of_truth_count: number;
  total_declared_rows: number;
  catalogs: CatalogSummaryRecord[];
};

export type ScoreExplanationRecord = {
  object_type: "relationship_fact_candidate";
  object_id: string;
  candidate_key: string;
  relationship_type: string;
  relationship_family: string;
  record_mode: string;
  fact_status: string;
  publication_status: string;
  source_threshold: {
    minimum_independent_sources: number;
    independent_source_count: number;
    met: boolean;
  };
  review_status: string;
  parser_version: string;
  raw_score: number;
  evidence_quality: number;
  adjusted_score: number;
  coverage: number;
  contributions: Record<string, unknown>[];
  missing_inputs: string[];
  model_version: string;
  profile_version: string;
  profile_version_id: string;
  structured_fact: Record<string, unknown>;
  counter_evidence: unknown[];
  subject: Record<string, unknown>;
  object: Record<string, unknown>;
  evidence: Record<string, unknown>[];
  review_queue: Record<string, unknown>[];
  production_context: Record<string, unknown>;
  scoring_service_version: string;
};

export type EvidenceDetailItem = {
  evidence_id: string;
  source_document_id: string;
  ingestion_evidence_chain_id: string | null;
  role: string;
  source_tier: number;
  publisher: string | null;
  title: string | null;
  url: string | null;
  locator: string | null;
  support_excerpt: string | null;
  snippet: {
    text: string | null;
    locator: string | null;
    redaction_status: string;
  };
  structured_fact: Record<string, unknown>;
  counter_evidence: unknown[];
  parser_version: string | null;
  confidence: number | null;
  review_status: string | null;
  source_document: Record<string, unknown>;
};

export type EvidenceDetailRecord = {
  schema_version: "evidence-detail-v1";
  object_type: "relationship_fact_candidate" | "relationship";
  object_id: string;
  object_summary: Record<string, unknown>;
  evidence_count: number;
  returned_evidence_count: number;
  source_document_count: number;
  limit: number;
  truncated: boolean;
  source_documents: Record<string, unknown>[];
  evidence: EvidenceDetailItem[];
  production_context: Record<string, unknown>;
};

export type CatalogInventorySyncResult =
  | {
      mode: "server";
      status: "hydrated";
      endpoint: string;
      record: CatalogInventoryRecord;
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

export type ScoreExplanationSyncResult =
  | {
      mode: "server";
      status: "hydrated";
      endpoint: string;
      record: ScoreExplanationRecord;
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
      reason: "api_base_missing" | "candidate_id_missing";
    };

export type EvidenceDetailSyncResult =
  | {
      mode: "server";
      status: "hydrated";
      endpoint: string;
      record: EvidenceDetailRecord;
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
      reason: "api_base_missing" | "object_id_missing";
    };

export type SupplyChainSyncResult =
  | {
      mode: "server";
      status: "hydrated";
      endpoint: string;
      record: SupplyChainRecord;
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
      reason: "api_base_missing" | "entity_id_missing";
    };

export type CapitalMapSyncResult =
  | {
      mode: "server";
      status: "hydrated";
      endpoint: string;
      record: EntityCapitalMapRecord;
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
      reason: "api_base_missing" | "entity_id_missing";
    };

export type PolicyMapSyncResult =
  | {
      mode: "server";
      status: "hydrated";
      endpoint: string;
      record: EntityPolicyMapRecord;
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
      reason: "api_base_missing" | "entity_id_missing";
    };

export function readProductionDataApiBaseUrl() {
  const override = window.localStorage.getItem(PRODUCTION_DATA_API_BASE_STORAGE_KEY)?.trim();
  const sharedOverride = window.localStorage.getItem(SHARED_API_BASE_STORAGE_KEY)?.trim();
  const configured = process.env.NEXT_PUBLIC_EEI_API_BASE_URL?.trim();
  return stripTrailingSlash(override || sharedOverride || configured || "");
}

export async function loadCatalogInventory(): Promise<CatalogInventorySyncResult> {
  const apiBaseUrl = readProductionDataApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "fixture", reason: "api_base_missing" };
  }

  const endpoint = `${apiBaseUrl}/v1/catalogs`;
  try {
    const response = await window.fetch(endpoint);
    const payload = (await response.json().catch(() => null)) as unknown;
    if (!response.ok || !isCatalogInventoryRecord(payload)) {
      return {
        mode: "server",
        status: "error",
        endpoint,
        reason: `http_${response.status}`,
        detail: payload
      };
    }
    return { mode: "server", status: "hydrated", endpoint, record: payload };
  } catch (error) {
    return fetchCatalogErrorResult(endpoint, error);
  }
}

export async function loadSupplyChain(input: {
  entityId?: string | null;
  profileId?: string | null;
}): Promise<SupplyChainSyncResult> {
  if (!input.entityId) {
    return { mode: "local_fallback", status: "fixture", reason: "entity_id_missing" };
  }
  const apiBaseUrl = readProductionDataApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "fixture", reason: "api_base_missing" };
  }

  const query = input.profileId ? `?profile=${encodeURIComponent(input.profileId)}` : "";
  const endpoint = `${apiBaseUrl}/v1/entities/${encodeURIComponent(input.entityId)}/supply-chain${query}`;
  try {
    const response = await window.fetch(endpoint);
    const payload = (await response.json().catch(() => null)) as unknown;
    if (!response.ok || !isSupplyChainRecord(payload)) {
      return {
        mode: "server",
        status: "error",
        endpoint,
        reason: `http_${response.status}`,
        detail: payload
      };
    }
    return { mode: "server", status: "hydrated", endpoint, record: payload };
  } catch (error) {
    return fetchSupplyChainErrorResult(endpoint, error);
  }
}

export async function loadCapitalMap(input: {
  entityId?: string | null;
  profileId?: string | null;
}): Promise<CapitalMapSyncResult> {
  if (!input.entityId) {
    return { mode: "local_fallback", status: "fixture", reason: "entity_id_missing" };
  }
  const apiBaseUrl = readProductionDataApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "fixture", reason: "api_base_missing" };
  }

  const query = input.profileId ? `?profile=${encodeURIComponent(input.profileId)}` : "";
  const endpoint = `${apiBaseUrl}/v1/entities/${encodeURIComponent(input.entityId)}/capital${query}`;
  try {
    const response = await window.fetch(endpoint);
    const payload = (await response.json().catch(() => null)) as unknown;
    if (!response.ok || !isEntityCapitalMapRecord(payload)) {
      return {
        mode: "server",
        status: "error",
        endpoint,
        reason: `http_${response.status}`,
        detail: payload
      };
    }
    return { mode: "server", status: "hydrated", endpoint, record: payload };
  } catch (error) {
    return fetchCapitalMapErrorResult(endpoint, error);
  }
}

export async function loadPolicyMap(input: {
  entityId?: string | null;
  profileId?: string | null;
}): Promise<PolicyMapSyncResult> {
  if (!input.entityId) {
    return { mode: "local_fallback", status: "fixture", reason: "entity_id_missing" };
  }
  const apiBaseUrl = readProductionDataApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "fixture", reason: "api_base_missing" };
  }

  const query = input.profileId ? `?profile=${encodeURIComponent(input.profileId)}` : "";
  const endpoint = `${apiBaseUrl}/v1/entities/${encodeURIComponent(input.entityId)}/policy${query}`;
  try {
    const response = await window.fetch(endpoint);
    const payload = (await response.json().catch(() => null)) as unknown;
    if (!response.ok || !isEntityPolicyMapRecord(payload)) {
      return {
        mode: "server",
        status: "error",
        endpoint,
        reason: `http_${response.status}`,
        detail: payload
      };
    }
    return { mode: "server", status: "hydrated", endpoint, record: payload };
  } catch (error) {
    return fetchPolicyMapErrorResult(endpoint, error);
  }
}

export async function loadScoreExplanation(input: {
  objectType: "relationship_fact_candidate";
  objectId?: string | null;
  profileId?: string | null;
}): Promise<ScoreExplanationSyncResult> {
  if (!input.objectId) {
    return { mode: "local_fallback", status: "fixture", reason: "candidate_id_missing" };
  }
  const apiBaseUrl = readProductionDataApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "fixture", reason: "api_base_missing" };
  }

  const query = input.profileId ? `?profile=${encodeURIComponent(input.profileId)}` : "";
  const endpoint = `${apiBaseUrl}/v1/scoring/explain/${input.objectType}/${input.objectId}${query}`;
  try {
    const response = await window.fetch(endpoint);
    const payload = (await response.json().catch(() => null)) as unknown;
    if (!response.ok || !isScoreExplanationRecord(payload)) {
      return {
        mode: "server",
        status: "error",
        endpoint,
        reason: `http_${response.status}`,
        detail: payload
      };
    }
    return { mode: "server", status: "hydrated", endpoint, record: payload };
  } catch (error) {
    return fetchScoreErrorResult(endpoint, error);
  }
}

export async function loadEvidenceDetail(input: {
  objectType: "relationship_fact_candidate" | "relationship";
  objectId?: string | null;
  limit?: number;
}): Promise<EvidenceDetailSyncResult> {
  if (!input.objectId) {
    return { mode: "local_fallback", status: "fixture", reason: "object_id_missing" };
  }
  const apiBaseUrl = readProductionDataApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "fixture", reason: "api_base_missing" };
  }

  const limit = input.limit ?? 20;
  const endpoint = `${apiBaseUrl}/v1/evidence/${input.objectType}/${input.objectId}?limit=${encodeURIComponent(
    String(limit)
  )}`;
  try {
    const response = await window.fetch(endpoint);
    const payload = (await response.json().catch(() => null)) as unknown;
    if (!response.ok || !isEvidenceDetailRecord(payload)) {
      return {
        mode: "server",
        status: "error",
        endpoint,
        reason: `http_${response.status}`,
        detail: payload
      };
    }
    return { mode: "server", status: "hydrated", endpoint, record: payload };
  } catch (error) {
    return fetchEvidenceErrorResult(endpoint, error);
  }
}

function isCatalogInventoryRecord(value: unknown): value is CatalogInventoryRecord {
  if (!isRecord(value)) return false;
  return (
    typeof value.as_of === "string" &&
    typeof value.catalog_version === "string" &&
    typeof value.catalog_count === "number" &&
    typeof value.source_of_truth_count === "number" &&
    typeof value.total_declared_rows === "number" &&
    Array.isArray(value.catalogs) &&
    value.catalogs.every(isCatalogSummaryRecord)
  );
}

function isCatalogSummaryRecord(value: unknown): value is CatalogSummaryRecord {
  if (!isRecord(value)) return false;
  return (
    typeof value.catalog_id === "string" &&
    typeof value.catalog_key === "string" &&
    typeof value.name_zh === "string" &&
    typeof value.path === "string" &&
    typeof value.primary_key === "string" &&
    typeof value.row_count === "number" &&
    typeof value.owner === "string" &&
    typeof value.ui_surfaces === "string" &&
    typeof value.scope === "string" &&
    typeof value.status === "string" &&
    typeof value.source_of_truth === "boolean" &&
    isRecord(value.export_links)
  );
}

function isSupplyChainRecord(value: unknown): value is SupplyChainRecord {
  if (!isRecord(value) || !isRecord(value.directional_summary) || !isRecord(value.coverage)) {
    return false;
  }
  return (
    value.schema_version === "entity-supply-chain-v1" &&
    typeof value.as_of === "string" &&
    isRecord(value.focus) &&
    typeof value.focus.id === "string" &&
    typeof value.focus.canonical_name === "string" &&
    typeof value.directional_summary.upstream_edge_count === "number" &&
    typeof value.directional_summary.downstream_edge_count === "number" &&
    typeof value.directional_summary.supports_upstream_downstream === "boolean" &&
    Array.isArray(value.chain_stages) &&
    value.chain_stages.every(isSupplyChainStageRecord) &&
    Array.isArray(value.edges) &&
    value.edges.every(isSupplyChainEdgeRecord) &&
    Array.isArray(value.unknowns) &&
    typeof value.coverage.ordered_stage_count === "number" &&
    typeof value.coverage.covered_stage_count === "number" &&
    typeof value.coverage.edge_count === "number" &&
    typeof value.coverage.evidence_source_count === "number" &&
    typeof value.coverage.all_edges_have_evidence === "boolean" &&
    Array.isArray(value.coverage.edge_metadata_fields) &&
    typeof value.coverage.unknowns_explicit === "boolean" &&
    typeof value.data_mode === "string"
  );
}

function isSupplyChainStageRecord(value: unknown): value is SupplyChainStageRecord {
  if (!isRecord(value)) return false;
  return (
    typeof value.stage_id === "string" &&
    typeof value.stage_order === "number" &&
    typeof value.slug === "string" &&
    typeof value.name_zh === "string" &&
    typeof value.name_en === "string" &&
    typeof value.default_direction === "string" &&
    typeof value.relationship_count === "number" &&
    typeof value.upstream_edge_count === "number" &&
    typeof value.downstream_edge_count === "number" &&
    typeof value.unknown_count === "number"
  );
}

function isSupplyChainEdgeRecord(value: unknown): value is SupplyChainEdgeRecord {
  if (!isRecord(value) || !isRecord(value.subject) || !isRecord(value.object)) return false;
  return (
    typeof value.id === "string" &&
    typeof value.subject.id === "string" &&
    typeof value.subject.canonical_name === "string" &&
    typeof value.object.id === "string" &&
    typeof value.object.canonical_name === "string" &&
    typeof value.relationship_type === "string" &&
    typeof value.relationship_family === "string" &&
    typeof value.status === "string" &&
    ["upstream", "downstream", "midstream", "unknown"].includes(String(value.chain_side)) &&
    typeof value.tier === "string" &&
    typeof value.materiality === "string" &&
    typeof value.evidence_count === "number" &&
    Array.isArray(value.unknown_fields) &&
    typeof value.synthetic === "boolean"
  );
}

function isEntityCapitalMapRecord(value: unknown): value is EntityCapitalMapRecord {
  if (!isRecord(value) || !isRecord(value.coverage)) return false;
  return (
    value.schema_version === "entity-capital-map-v1" &&
    typeof value.as_of === "string" &&
    isRecord(value.focus) &&
    typeof value.focus.id === "string" &&
    Array.isArray(value.relationships) &&
    value.relationships.every(isCapitalPolicyRelationshipRecord) &&
    Array.isArray(value.events) &&
    value.events.every(isCapitalPolicyEventRecord) &&
    Array.isArray(value.semantic_buckets) &&
    value.semantic_buckets.every(isSemanticBucketRecord) &&
    typeof value.coverage.relationship_count === "number" &&
    typeof value.coverage.event_count === "number" &&
    Array.isArray(value.coverage.required_semantic_classes) &&
    typeof value.coverage.no_silent_summing === "boolean" &&
    typeof value.coverage.unknown_amount_not_zero === "boolean"
  );
}

function isEntityPolicyMapRecord(value: unknown): value is EntityPolicyMapRecord {
  if (!isRecord(value) || !isRecord(value.coverage)) return false;
  return (
    value.schema_version === "entity-policy-map-v1" &&
    typeof value.as_of === "string" &&
    isRecord(value.focus) &&
    typeof value.focus.id === "string" &&
    Array.isArray(value.policy_records) &&
    value.policy_records.every(isCapitalPolicyRelationshipRecord) &&
    Array.isArray(value.technology_records) &&
    value.technology_records.every(isCapitalPolicyRelationshipRecord) &&
    Array.isArray(value.events) &&
    value.events.every(isCapitalPolicyEventRecord) &&
    Array.isArray(value.semantic_buckets) &&
    value.semantic_buckets.every(isSemanticBucketRecord) &&
    typeof value.coverage.policy_record_count === "number" &&
    typeof value.coverage.technology_record_count === "number" &&
    Array.isArray(value.coverage.policy_semantic_classes) &&
    Array.isArray(value.coverage.technology_semantic_classes) &&
    typeof value.coverage.unknowns_explicit === "boolean"
  );
}

function isSemanticBucketRecord(value: unknown): value is SemanticBucketRecord {
  if (!isRecord(value)) return false;
  return (
    typeof value.key === "string" &&
    typeof value.label === "string" &&
    typeof value.dimension === "string" &&
    typeof value.record_count === "number" &&
    typeof value.amount_record_count === "number" &&
    typeof value.unknown_count === "number" &&
    typeof value.required === "boolean"
  );
}

function isCapitalPolicyRelationshipRecord(
  value: unknown
): value is CapitalPolicyRelationshipRecord {
  if (!isRecord(value) || !isRecord(value.subject) || !isRecord(value.object)) return false;
  return (
    typeof value.id === "string" &&
    typeof value.relationship_type === "string" &&
    typeof value.relationship_family === "string" &&
    typeof value.semantic_class === "string" &&
    Array.isArray(value.semantic_tags) &&
    ["in", "out", "neutral"].includes(String(value.direction)) &&
    isRecord(value.amount_semantics) &&
    typeof value.amount_semantics.unknown_not_zero === "boolean" &&
    typeof value.evidence_count === "number" &&
    Array.isArray(value.unknown_fields) &&
    typeof value.synthetic === "boolean"
  );
}

function isCapitalPolicyEventRecord(value: unknown): value is CapitalPolicyEventRecord {
  if (!isRecord(value)) return false;
  return (
    typeof value.id === "string" &&
    typeof value.event_type === "string" &&
    typeof value.title === "string" &&
    typeof value.semantic_class === "string" &&
    Array.isArray(value.semantic_tags) &&
    isRecord(value.amount_semantics) &&
    typeof value.amount_semantics.unknown_not_zero === "boolean" &&
    typeof value.evidence_count === "number" &&
    Array.isArray(value.unknown_fields) &&
    Array.isArray(value.participants)
  );
}

function isScoreExplanationRecord(value: unknown): value is ScoreExplanationRecord {
  if (!isRecord(value)) return false;
  return (
    value.object_type === "relationship_fact_candidate" &&
    typeof value.object_id === "string" &&
    typeof value.candidate_key === "string" &&
    typeof value.relationship_type === "string" &&
    typeof value.relationship_family === "string" &&
    typeof value.publication_status === "string" &&
    isRecord(value.source_threshold) &&
    typeof value.source_threshold.minimum_independent_sources === "number" &&
    typeof value.source_threshold.independent_source_count === "number" &&
    typeof value.source_threshold.met === "boolean" &&
    typeof value.raw_score === "number" &&
    typeof value.evidence_quality === "number" &&
    typeof value.adjusted_score === "number" &&
    typeof value.coverage === "number" &&
    Array.isArray(value.contributions) &&
    Array.isArray(value.missing_inputs) &&
    typeof value.model_version === "string" &&
    typeof value.profile_version === "string" &&
    typeof value.profile_version_id === "string" &&
    Array.isArray(value.evidence) &&
    typeof value.scoring_service_version === "string"
  );
}

function isEvidenceDetailRecord(value: unknown): value is EvidenceDetailRecord {
  if (!isRecord(value)) return false;
  return (
    value.schema_version === "evidence-detail-v1" &&
    (value.object_type === "relationship_fact_candidate" || value.object_type === "relationship") &&
    typeof value.object_id === "string" &&
    isRecord(value.object_summary) &&
    typeof value.evidence_count === "number" &&
    typeof value.returned_evidence_count === "number" &&
    typeof value.source_document_count === "number" &&
    typeof value.limit === "number" &&
    typeof value.truncated === "boolean" &&
    Array.isArray(value.source_documents) &&
    Array.isArray(value.evidence) &&
    value.evidence.every(isEvidenceDetailItem) &&
    isRecord(value.production_context)
  );
}

function isEvidenceDetailItem(value: unknown): value is EvidenceDetailItem {
  if (!isRecord(value) || !isRecord(value.snippet)) return false;
  return (
    typeof value.evidence_id === "string" &&
    typeof value.source_document_id === "string" &&
    typeof value.role === "string" &&
    typeof value.source_tier === "number" &&
    (typeof value.snippet.text === "string" || value.snippet.text === null) &&
    (typeof value.snippet.locator === "string" || value.snippet.locator === null) &&
    typeof value.snippet.redaction_status === "string" &&
    isRecord(value.structured_fact) &&
    Array.isArray(value.counter_evidence) &&
    isRecord(value.source_document)
  );
}

function fetchCatalogErrorResult(endpoint: string, error: unknown): CatalogInventorySyncResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function fetchSupplyChainErrorResult(endpoint: string, error: unknown): SupplyChainSyncResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function fetchCapitalMapErrorResult(endpoint: string, error: unknown): CapitalMapSyncResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function fetchPolicyMapErrorResult(endpoint: string, error: unknown): PolicyMapSyncResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function fetchScoreErrorResult(endpoint: string, error: unknown): ScoreExplanationSyncResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function fetchEvidenceErrorResult(endpoint: string, error: unknown): EvidenceDetailSyncResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function stripTrailingSlash(value: string) {
  return value.replace(/\/+$/, "");
}
