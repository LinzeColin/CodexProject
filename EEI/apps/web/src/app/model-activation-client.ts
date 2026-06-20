"use client";

export const MODEL_CONTEXT_API_BASE_STORAGE_KEY = "eei.modelApiBaseUrl.v1";

export type ActiveModelContextRecord = {
  schema_version: "active-analysis-context-v1";
  context_key: "global";
  active_scoring_profile_version_id: string;
  active_data_snapshot_id?: string | null;
  active_data_snapshot_key?: string | null;
  active_scoring_run_id?: string | null;
  refresh_token: string;
  refresh_generation: number;
  status: "active" | "refreshing" | "failed";
  activated_at?: string;
  activated_by?: string;
  affected_modules: string[];
  model_version: string;
  profile_version: string;
  client_state: "current" | "stale";
  stale_client_semantics?: string;
  metadata?: Record<string, unknown>;
};

export type ScoringProfileRecord = {
  id: string;
  profile_key: string;
  name: string;
  version: number;
  model_key: string;
  active: boolean;
  reason?: string;
};

export type ScoringProfileDraftResponse = {
  schema_version: "scoring-profile-draft-v1";
  status: "created";
  profile: ScoringProfileRecord;
  base_profile: ScoringProfileRecord;
  active_context: ActiveModelContextRecord;
  validation: {
    weight_sum: number;
    changed_weights: string[];
    active_context_unchanged: boolean;
    activation_required: boolean;
  };
};

export type ModelActivationServerResponse = {
  schema_version: "model-activation-v1";
  status: "activated";
  previous_profile: ScoringProfileRecord | null;
  activated_profile: ScoringProfileRecord;
  active_context: ActiveModelContextRecord;
  cache_invalidation: {
    previous_refresh_token?: string | null;
    refresh_token: string;
    refresh_generation: number;
    stale_client_semantics?: string;
  };
};

export type ScoreRecomputeJobRecord = {
  id: string;
  job_type: "score_recompute";
  idempotency_key: string;
  status: "queued" | "running" | "succeeded" | "dead_letter" | "cancelled";
  payload?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
};

export type ScoreRecomputeServerResponse = {
  schema_version: "score-recompute-request-v1";
  status: ScoreRecomputeJobRecord["status"];
  job: ScoreRecomputeJobRecord;
  idempotency_key: string;
  active_context: ActiveModelContextRecord;
  cache_policy: {
    refresh_token: string;
    refresh_generation: number;
    stale_client_semantics?: string;
  };
};

export type ModelContextSyncResult =
  | {
      mode: "server";
      status: "current" | "stale";
      endpoint: string;
      record: ActiveModelContextRecord;
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
      status: "current";
      reason: "api_base_missing";
    };

export type ModelProfileListResult =
  | {
      mode: "server";
      status: "listed";
      endpoint: string;
      profiles: ScoringProfileRecord[];
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
      status: "listed";
      reason: "api_base_missing";
    };

export type ModelProfileDraftResult =
  | {
      mode: "server";
      status: "created";
      endpoint: string;
      response: ScoringProfileDraftResponse;
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
      status: "error";
      reason: "api_base_missing";
    };

export type ModelActivationResult =
  | {
      mode: "server";
      status: "activated";
      endpoint: string;
      response: ModelActivationServerResponse;
    }
  | {
      mode: "server";
      status: "conflict" | "error";
      endpoint: string;
      reason: string;
      detail?: unknown;
    }
  | {
      mode: "local_fallback";
      status: "error";
      reason: "api_base_missing" | "target_profile_missing";
    };

export type ScoreRecomputeResult =
  | {
      mode: "server";
      status: ScoreRecomputeJobRecord["status"];
      endpoint: string;
      response: ScoreRecomputeServerResponse;
    }
  | {
      mode: "server";
      status: "conflict" | "error";
      endpoint: string;
      reason: string;
      detail?: unknown;
    }
  | {
      mode: "local_fallback";
      status: "error";
      reason: "api_base_missing";
    };

type ModelProfileTransitionPayload = {
  targetProfileVersionId?: string;
  expectedActiveProfileVersionId?: string;
  clientRefreshToken?: string;
  reason: string;
};

export function readModelContextApiBaseUrl() {
  const override = window.localStorage.getItem(MODEL_CONTEXT_API_BASE_STORAGE_KEY)?.trim();
  const configured = process.env.NEXT_PUBLIC_EEI_API_BASE_URL?.trim();
  return stripTrailingSlash(override || configured || "");
}

export async function loadActiveModelContext(
  clientRefreshToken?: string
): Promise<ModelContextSyncResult> {
  const apiBaseUrl = readModelContextApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "current", reason: "api_base_missing" };
  }
  const endpoint = `${apiBaseUrl}/v1/scoring/active-context${clientRefreshToken ? `?client_refresh_token=${encodeURIComponent(clientRefreshToken)}` : ""}`;
  try {
    const response = await window.fetch(endpoint);
    const payload = (await response.json().catch(() => null)) as unknown;
    if (!response.ok || !isActiveModelContextRecord(payload)) {
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
      status: payload.client_state,
      endpoint,
      record: payload
    };
  } catch (error) {
    return fetchErrorResult(endpoint, error);
  }
}

export async function listModelProfiles(): Promise<ModelProfileListResult> {
  const apiBaseUrl = readModelContextApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "listed", reason: "api_base_missing" };
  }
  const endpoint = `${apiBaseUrl}/v1/scoring/profiles`;
  try {
    const response = await window.fetch(endpoint);
    const payload = (await response.json().catch(() => null)) as unknown;
    if (!response.ok || !Array.isArray(payload) || !payload.every(isScoringProfileRecord)) {
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
      status: "listed",
      endpoint,
      profiles: payload
    };
  } catch (error) {
    return fetchProfileErrorResult(endpoint, error);
  }
}

export async function createModelProfileDraft(payload: {
  baseProfileVersionId?: string;
  profileKey: string;
  name: string;
  weights: Record<string, number>;
  missingValuePolicy?: "renormalize_available" | "mark_unscored" | "conservative_penalty";
  reason: string;
}): Promise<ModelProfileDraftResult> {
  const apiBaseUrl = readModelContextApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "error", reason: "api_base_missing" };
  }
  const endpoint = `${apiBaseUrl}/v1/scoring/profiles`;
  try {
    const response = await window.fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        base_profile_version_id: payload.baseProfileVersionId ?? null,
        profile_key: payload.profileKey,
        name: payload.name,
        weights: payload.weights,
        missing_value_policy: payload.missingValuePolicy ?? "renormalize_available",
        reason: payload.reason
      })
    });
    const responsePayload = (await response.json().catch(() => null)) as unknown;
    if (!response.ok || !isScoringProfileDraftResponse(responsePayload)) {
      return {
        mode: "server",
        status: "error",
        endpoint,
        reason: `http_${response.status}`,
        detail: responsePayload
      };
    }
    return {
      mode: "server",
      status: "created",
      endpoint,
      response: responsePayload
    };
  } catch (error) {
    return fetchDraftErrorResult(endpoint, error);
  }
}

export async function activateModelProfile(payload: {
  targetProfileVersionId?: string;
  expectedActiveProfileVersionId?: string;
  clientRefreshToken?: string;
  reason: string;
}): Promise<ModelActivationResult> {
  return postModelProfileTransition(payload, "activate");
}

export async function rollbackModelProfile(
  payload: ModelProfileTransitionPayload
): Promise<ModelActivationResult> {
  return postModelProfileTransition(payload, "rollback");
}

export async function requestScoreRecompute(payload: {
  expectedActiveProfileVersionId?: string;
  clientRefreshToken?: string;
  scope?: "global" | "active_workspace";
  reason: string;
}): Promise<ScoreRecomputeResult> {
  const apiBaseUrl = readModelContextApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "error", reason: "api_base_missing" };
  }
  const endpoint = `${apiBaseUrl}/v1/scoring/recompute`;
  try {
    const response = await window.fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        expected_active_profile_version_id: payload.expectedActiveProfileVersionId ?? null,
        client_refresh_token: payload.clientRefreshToken ?? null,
        scope: payload.scope ?? "global",
        reason: payload.reason
      })
    });
    const responsePayload = (await response.json().catch(() => null)) as unknown;
    if (response.status === 409) {
      return {
        mode: "server",
        status: "conflict",
        endpoint,
        reason: conflictReason(responsePayload),
        detail: responsePayload
      };
    }
    if (!response.ok || !isScoreRecomputeServerResponse(responsePayload)) {
      return {
        mode: "server",
        status: "error",
        endpoint,
        reason: `http_${response.status}`,
        detail: responsePayload
      };
    }
    return {
      mode: "server",
      status: responsePayload.status,
      endpoint,
      response: responsePayload
    };
  } catch (error) {
    return fetchRecomputeErrorResult(endpoint, error);
  }
}

async function postModelProfileTransition(
  payload: ModelProfileTransitionPayload,
  action: "activate" | "rollback"
): Promise<ModelActivationResult> {
  const apiBaseUrl = readModelContextApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "error", reason: "api_base_missing" };
  }
  if (!payload.targetProfileVersionId) {
    return { mode: "local_fallback", status: "error", reason: "target_profile_missing" };
  }
  const endpoint = `${apiBaseUrl}/v1/scoring/profiles/${payload.targetProfileVersionId}/${action}`;
  try {
    const response = await window.fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        expected_active_profile_version_id: payload.expectedActiveProfileVersionId ?? null,
        client_refresh_token: payload.clientRefreshToken ?? null,
        reason: payload.reason
      })
    });
    const responsePayload = (await response.json().catch(() => null)) as unknown;
    if (response.status === 409) {
      return {
        mode: "server",
        status: "conflict",
        endpoint,
        reason: conflictReason(responsePayload),
        detail: responsePayload
      };
    }
    if (!response.ok || !isModelActivationServerResponse(responsePayload)) {
      return {
        mode: "server",
        status: "error",
        endpoint,
        reason: `http_${response.status}`,
        detail: responsePayload
      };
    }
    return {
      mode: "server",
      status: "activated",
      endpoint,
      response: responsePayload
    };
  } catch (error) {
    return fetchActivationErrorResult(endpoint, error);
  }
}

function isActiveModelContextRecord(value: unknown): value is ActiveModelContextRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    "schema_version" in value &&
    value.schema_version === "active-analysis-context-v1" &&
    "context_key" in value &&
    value.context_key === "global" &&
    "active_scoring_profile_version_id" in value &&
    typeof value.active_scoring_profile_version_id === "string" &&
    "refresh_token" in value &&
    typeof value.refresh_token === "string" &&
    "refresh_generation" in value &&
    typeof value.refresh_generation === "number" &&
    "affected_modules" in value &&
    Array.isArray(value.affected_modules) &&
    "model_version" in value &&
    typeof value.model_version === "string" &&
    "profile_version" in value &&
    typeof value.profile_version === "string" &&
    "client_state" in value &&
    (value.client_state === "current" || value.client_state === "stale")
  );
}

function isScoringProfileRecord(value: unknown): value is ScoringProfileRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "string" &&
    "profile_key" in value &&
    typeof value.profile_key === "string" &&
    "name" in value &&
    typeof value.name === "string" &&
    "version" in value &&
    typeof value.version === "number" &&
    "model_key" in value &&
    typeof value.model_key === "string" &&
    "active" in value &&
    typeof value.active === "boolean"
  );
}

function isModelActivationServerResponse(value: unknown): value is ModelActivationServerResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "schema_version" in value &&
    value.schema_version === "model-activation-v1" &&
    "status" in value &&
    value.status === "activated" &&
    "activated_profile" in value &&
    isScoringProfileRecord(value.activated_profile) &&
    "active_context" in value &&
    isActiveModelContextRecord(value.active_context) &&
    "cache_invalidation" in value &&
    typeof value.cache_invalidation === "object" &&
    value.cache_invalidation !== null
  );
}

function isScoringProfileDraftResponse(value: unknown): value is ScoringProfileDraftResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "schema_version" in value &&
    value.schema_version === "scoring-profile-draft-v1" &&
    "status" in value &&
    value.status === "created" &&
    "profile" in value &&
    isScoringProfileRecord(value.profile) &&
    "base_profile" in value &&
    isScoringProfileRecord(value.base_profile) &&
    "active_context" in value &&
    isActiveModelContextRecord(value.active_context) &&
    "validation" in value &&
    typeof value.validation === "object" &&
    value.validation !== null
  );
}

function isScoreRecomputeJobRecord(value: unknown): value is ScoreRecomputeJobRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "string" &&
    "job_type" in value &&
    value.job_type === "score_recompute" &&
    "idempotency_key" in value &&
    typeof value.idempotency_key === "string" &&
    "status" in value &&
    typeof value.status === "string"
  );
}

function isScoreRecomputeServerResponse(
  value: unknown
): value is ScoreRecomputeServerResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "schema_version" in value &&
    value.schema_version === "score-recompute-request-v1" &&
    "status" in value &&
    typeof value.status === "string" &&
    "job" in value &&
    isScoreRecomputeJobRecord(value.job) &&
    "idempotency_key" in value &&
    typeof value.idempotency_key === "string" &&
    "active_context" in value &&
    isActiveModelContextRecord(value.active_context)
  );
}

function conflictReason(payload: unknown) {
  if (
    typeof payload === "object" &&
    payload &&
    "detail" in payload &&
    typeof payload.detail === "object" &&
    payload.detail &&
    "reason" in payload.detail &&
    typeof payload.detail.reason === "string"
  ) {
    return payload.detail.reason;
  }
  return "model_activation_conflict";
}

function fetchErrorResult(endpoint: string, error: unknown): ModelContextSyncResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function fetchProfileErrorResult(endpoint: string, error: unknown): ModelProfileListResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function fetchDraftErrorResult(endpoint: string, error: unknown): ModelProfileDraftResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function fetchActivationErrorResult(endpoint: string, error: unknown): ModelActivationResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function fetchRecomputeErrorResult(endpoint: string, error: unknown): ScoreRecomputeResult {
  return {
    mode: "server",
    status: "error",
    endpoint,
    reason: error instanceof Error ? error.name : "fetch_failed",
    detail: error instanceof Error ? error.message : String(error)
  };
}

function stripTrailingSlash(value: string) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}
