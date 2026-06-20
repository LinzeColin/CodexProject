"use client";

export const SAVED_VIEW_API_BASE_STORAGE_KEY = "eei.apiBaseUrl.v1";
export const SAVED_VIEW_WORKSPACE_KEY = "mvp";

export type SavedViewServerRecord = {
  id: string;
  name: string;
  workspace_key: string;
  state: Record<string, unknown>;
  schema_version: "saved-view-v1";
  current_version: number;
  version_count?: number;
  updated_at?: string;
  metadata?: Record<string, unknown>;
};

export type SavedViewSyncResult =
  | {
      mode: "server";
      status: "saved" | "restored";
      endpoint: string;
      record: SavedViewServerRecord;
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
      status: "saved" | "restored";
      reason: "api_base_missing" | "server_id_missing";
    };

export type SavedViewSavePayload = {
  name: string;
  description?: string;
  state: Record<string, unknown>;
  metadata: Record<string, unknown>;
  serverId?: string;
  expectedVersion?: number;
};

export function readSavedViewApiBaseUrl() {
  const override = window.localStorage.getItem(SAVED_VIEW_API_BASE_STORAGE_KEY)?.trim();
  const configured = process.env.NEXT_PUBLIC_EEI_API_BASE_URL?.trim();
  return stripTrailingSlash(override || configured || "");
}

export async function saveViewToServer(
  payload: SavedViewSavePayload
): Promise<SavedViewSyncResult> {
  const apiBaseUrl = readSavedViewApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "saved", reason: "api_base_missing" };
  }

  const isUpdate = Boolean(payload.serverId && payload.expectedVersion);
  const endpoint = isUpdate
    ? `${apiBaseUrl}/v1/saved-views/${payload.serverId}`
    : `${apiBaseUrl}/v1/saved-views`;
  const body = isUpdate
    ? {
        expected_version: payload.expectedVersion,
        state: payload.state,
        description: payload.description,
        schema_version: "saved-view-v1",
        change_note: "EEI frontend update",
        metadata: payload.metadata
      }
    : {
        name: payload.name,
        description: payload.description,
        workspace_key: SAVED_VIEW_WORKSPACE_KEY,
        state: payload.state,
        schema_version: "saved-view-v1",
        change_note: "EEI frontend create",
        metadata: payload.metadata
      };

  return requestSavedView(endpoint, isUpdate ? "PUT" : "POST", body, "saved");
}

export async function restoreViewFromServer(
  serverId: string | undefined
): Promise<SavedViewSyncResult> {
  if (!serverId) {
    return { mode: "local_fallback", status: "restored", reason: "server_id_missing" };
  }
  const apiBaseUrl = readSavedViewApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "local_fallback", status: "restored", reason: "api_base_missing" };
  }
  const endpoint = `${apiBaseUrl}/v1/saved-views/${serverId}`;
  return requestSavedView(endpoint, "GET", undefined, "restored");
}

async function requestSavedView(
  endpoint: string,
  method: "GET" | "POST" | "PUT",
  body: Record<string, unknown> | undefined,
  successStatus: "saved" | "restored"
): Promise<SavedViewSyncResult> {
  try {
    const response = await window.fetch(endpoint, {
      method,
      headers: body ? { "content-type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined
    });
    const payload = (await response.json().catch(() => null)) as unknown;
    if (response.status === 409) {
      return {
        mode: "server",
        status: "conflict",
        endpoint,
        reason: conflictReason(payload),
        detail: payload
      };
    }
    if (!response.ok || !isSavedViewServerRecord(payload)) {
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
      status: successStatus,
      endpoint,
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
  return "saved_view_conflict";
}

function isSavedViewServerRecord(value: unknown): value is SavedViewServerRecord {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    typeof value.id === "string" &&
    "state" in value &&
    typeof value.state === "object" &&
    "schema_version" in value &&
    value.schema_version === "saved-view-v1" &&
    "current_version" in value &&
    typeof value.current_version === "number"
  );
}

function stripTrailingSlash(value: string) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}
