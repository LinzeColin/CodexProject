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
  object_type: "event" | "relationship_fact_candidate" | "relationship";
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

export type SourceFreshnessItem = {
  source_id: string;
  source_code: string;
  source_name: string;
  source_tier: number;
  expected_cadence: string | null;
  typical_disclosure_lag: string | null;
  last_verified_at: string | null;
  record_modes: string[];
  data_mode: "fixture" | "live" | "mixed" | "missing";
  freshness_status:
    | "available"
    | "failed"
    | "running"
    | "never_attempted"
    | "missing_documents"
    | "fixture";
  attempt_count: number;
  success_count: number;
  failure_count: number;
  last_attempt_at: string | null;
  last_attempt_finished_at: string | null;
  last_attempt_status: string | null;
  last_success_at: string | null;
  last_failure_at: string | null;
  last_error_class: string | null;
  last_error_message: string | null;
  document_count: number;
  latest_document_date: string | null;
  latest_report_period_start: string | null;
  latest_report_period_end: string | null;
  latest_observed_at: string | null;
  latest_retrieved_at: string | null;
};

export type SourceFreshnessRecord = {
  schema_version: "source-freshness-v1";
  as_of: string;
  summary: {
    status: "available" | "degraded" | "running" | "never_attempted" | "missing";
    source_count: number;
    available_source_count: number;
    failed_source_count: number;
    running_source_count: number;
    attempt_count: number;
    success_count: number;
    failure_count: number;
    document_count: number;
    last_attempt_at: string | null;
    last_success_at: string | null;
    last_failure_at: string | null;
    latest_document_date: string | null;
    latest_report_period_end: string | null;
  };
  sources: SourceFreshnessItem[];
  semantics: {
    attempt_time_is_document_time: false;
    attempt_time_is_report_period: false;
    document_date_source: string;
    report_period_source: string;
  };
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

export type SourceFreshnessSyncResult =
  | {
      mode: "server";
      status: "hydrated";
      endpoint: string;
      record: SourceFreshnessRecord;
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

export async function loadSourceFreshness(): Promise<SourceFreshnessSyncResult> {
  const apiBaseUrl = readProductionDataApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "fixture", reason: "api_base_missing" };
  }

  const endpoint = `${apiBaseUrl}/v1/sources/freshness`;
  try {
    const response = await window.fetch(endpoint);
    const payload = (await response.json().catch(() => null)) as unknown;
    if (!response.ok || !isSourceFreshnessRecord(payload)) {
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
    return fetchSourceFreshnessErrorResult(endpoint, error);
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
  objectType: "event" | "relationship_fact_candidate" | "relationship";
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
    (value.object_type === "event" ||
      value.object_type === "relationship_fact_candidate" ||
      value.object_type === "relationship") &&
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

function isSourceFreshnessRecord(value: unknown): value is SourceFreshnessRecord {
  if (!isRecord(value) || !isRecord(value.summary) || !isRecord(value.semantics)) {
    return false;
  }
  return (
    value.schema_version === "source-freshness-v1" &&
    typeof value.as_of === "string" &&
    typeof value.summary.status === "string" &&
    typeof value.summary.source_count === "number" &&
    typeof value.summary.attempt_count === "number" &&
    typeof value.summary.success_count === "number" &&
    typeof value.summary.failure_count === "number" &&
    typeof value.summary.document_count === "number" &&
    Array.isArray(value.sources) &&
    value.sources.every(isSourceFreshnessItem) &&
    value.semantics.attempt_time_is_document_time === false &&
    value.semantics.attempt_time_is_report_period === false
  );
}

function isSourceFreshnessItem(value: unknown): value is SourceFreshnessItem {
  if (!isRecord(value)) return false;
  return (
    typeof value.source_id === "string" &&
    typeof value.source_code === "string" &&
    typeof value.source_name === "string" &&
    typeof value.source_tier === "number" &&
    typeof value.freshness_status === "string" &&
    typeof value.data_mode === "string" &&
    Array.isArray(value.record_modes) &&
    typeof value.attempt_count === "number" &&
    typeof value.success_count === "number" &&
    typeof value.failure_count === "number" &&
    typeof value.document_count === "number" &&
    isNullableString(value.last_attempt_at) &&
    isNullableString(value.last_success_at) &&
    isNullableString(value.last_failure_at) &&
    isNullableString(value.latest_document_date) &&
    isNullableString(value.latest_report_period_start) &&
    isNullableString(value.latest_report_period_end)
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

function fetchSourceFreshnessErrorResult(
  endpoint: string,
  error: unknown
): SourceFreshnessSyncResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function isNullableString(value: unknown): value is string | null {
  return typeof value === "string" || value === null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function stripTrailingSlash(value: string) {
  return value.replace(/\/+$/, "");
}
