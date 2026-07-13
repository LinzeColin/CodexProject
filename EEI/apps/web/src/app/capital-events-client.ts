"use client";

import { readProductionDataApiBaseUrl } from "./production-data-client";

export type CapitalEventFilters = {
  entity: string;
  from: string;
  to: string;
  eventType: string;
  currency: string;
  amountKind: string;
};

export type EventParticipant = {
  entity_id: string;
  role: string;
  direction: string | null;
};

export type AmountAggregationKey = {
  currency: string;
  amount_kind: string;
  period_start: string | null;
  period_end: string | null;
};

export type EventAmountSemantics = {
  schema_version: "event-amount-semantics-v1";
  state: "unreported" | "reported" | "reported_unclassified";
  amount: number | null;
  display_amount: number | null;
  currency: string | null;
  amount_kind: string | null;
  period_start: string | null;
  period_end: string | null;
  visual_weight: number | null;
  width_eligible: boolean;
  aggregate_eligible: boolean;
  aggregation_key: AmountAggregationKey | null;
  non_aggregation_reason: string | null;
};

export type CapitalEventRecord = {
  id: string;
  event_type: string;
  title: string;
  status: string;
  announced_at: string | null;
  effective_at: string | null;
  period_start: string | null;
  period_end: string | null;
  observed_at: string;
  amount: number | null;
  currency: string | null;
  amount_kind: string | null;
  description: string | null;
  qualifiers: Record<string, unknown>;
  evidence_count: number;
  participants: EventParticipant[];
  amount_semantics: EventAmountSemantics;
};

export type EventAmountBucket = AmountAggregationKey & {
  total_amount: number;
  visual_weight_total: number;
  event_count: number;
  event_ids: string[];
};

export type EventAmountSummary = {
  schema_version: "event-amount-semantics-v1";
  event_count: number;
  reported_event_count: number;
  unreported_event_count: number;
  unclassified_event_count: number;
  bucket_count: number;
  buckets: EventAmountBucket[];
  unreported_event_ids: string[];
  unclassified_event_ids: string[];
  incomparable_dimensions: string[];
  cross_bucket_summation_performed: false;
  comparable_reported_total_available: boolean;
  comparable_reported_total: number | null;
  comparable_reported_total_complete: boolean;
  semantics: {
    unknown_amount_is_zero: false;
    unknown_amount_has_visual_weight: false;
    aggregation_key: string[];
    incomparable_buckets_are_summed: false;
  };
  filters: Record<string, unknown>;
};

export type CapitalRiverSyncResult =
  | {
      mode: "server";
      status: "hydrated";
      eventsEndpoint: string;
      summaryEndpoint: string;
      events: CapitalEventRecord[];
      summary: EventAmountSummary;
    }
  | {
      mode: "server";
      status: "error";
      eventsEndpoint: string;
      summaryEndpoint: string;
      reason: string;
      detail?: unknown;
    }
  | {
      mode: "unavailable";
      status: "api_required";
      reason: "api_base_missing";
    };

export async function loadCapitalRiver(
  filters: CapitalEventFilters
): Promise<CapitalRiverSyncResult> {
  const apiBaseUrl = readProductionDataApiBaseUrl();
  if (!apiBaseUrl) {
    return { mode: "unavailable", status: "api_required", reason: "api_base_missing" };
  }
  const query = buildCapitalEventQuery(filters);
  const eventsEndpoint = `${apiBaseUrl}/v1/events?${query}`;
  const summaryEndpoint = `${apiBaseUrl}/v1/events/amount-summary?${query}`;

  try {
    const [eventsResponse, summaryResponse] = await Promise.all([
      window.fetch(eventsEndpoint),
      window.fetch(summaryEndpoint)
    ]);
    const [eventsPayload, summaryPayload] = await Promise.all([
      eventsResponse.json().catch(() => null),
      summaryResponse.json().catch(() => null)
    ]);
    if (
      !eventsResponse.ok ||
      !summaryResponse.ok ||
      !isCapitalEventList(eventsPayload) ||
      !isEventAmountSummary(summaryPayload)
    ) {
      return {
        mode: "server",
        status: "error",
        eventsEndpoint,
        summaryEndpoint,
        reason: `http_${eventsResponse.status}_${summaryResponse.status}`,
        detail: { events: eventsPayload, summary: summaryPayload }
      };
    }
    return {
      mode: "server",
      status: "hydrated",
      eventsEndpoint,
      summaryEndpoint,
      events: eventsPayload,
      summary: summaryPayload
    };
  } catch (error) {
    return {
      mode: "server",
      status: "error",
      eventsEndpoint,
      summaryEndpoint,
      reason: error instanceof Error ? error.name : "fetch_failed",
      detail: error instanceof Error ? error.message : String(error)
    };
  }
}

export function buildCapitalEventQuery(filters: CapitalEventFilters) {
  const query = new URLSearchParams({ limit: "100" });
  setQueryValue(query, "entity", filters.entity);
  setQueryValue(query, "from", dateBoundary(filters.from, "start"));
  setQueryValue(query, "to", dateBoundary(filters.to, "end"));
  setQueryValue(query, "event_type", filters.eventType);
  setQueryValue(query, "currency", filters.currency.toUpperCase());
  setQueryValue(query, "amount_kind", filters.amountKind);
  return query.toString();
}

export function amountBucketKey(key: AmountAggregationKey) {
  return [key.currency, key.amount_kind, key.period_start ?? "open", key.period_end ?? "open"].join(
    "|"
  );
}

function dateBoundary(value: string, boundary: "start" | "end") {
  const normalized = value.trim();
  if (!normalized) return "";
  return `${normalized}T${boundary === "start" ? "00:00:00.000" : "23:59:59.999"}Z`;
}

function setQueryValue(query: URLSearchParams, key: string, value: string) {
  const normalized = value.trim();
  if (normalized) query.set(key, normalized);
}

function isCapitalEventList(value: unknown): value is CapitalEventRecord[] {
  return Array.isArray(value) && value.every(isCapitalEventRecord);
}

function isCapitalEventRecord(value: unknown): value is CapitalEventRecord {
  if (!isRecord(value) || !isRecord(value.amount_semantics)) return false;
  return (
    typeof value.id === "string" &&
    typeof value.event_type === "string" &&
    typeof value.title === "string" &&
    typeof value.status === "string" &&
    isNullableString(value.announced_at) &&
    isNullableString(value.effective_at) &&
    isNullableString(value.period_start) &&
    isNullableString(value.period_end) &&
    typeof value.observed_at === "string" &&
    isNullableNumber(value.amount) &&
    isNullableString(value.currency) &&
    isNullableString(value.amount_kind) &&
    isNullableString(value.description) &&
    isRecord(value.qualifiers) &&
    typeof value.evidence_count === "number" &&
    Array.isArray(value.participants) &&
    value.participants.every(isEventParticipant) &&
    isEventAmountSemantics(value.amount_semantics)
  );
}

function isEventParticipant(value: unknown): value is EventParticipant {
  return (
    isRecord(value) &&
    typeof value.entity_id === "string" &&
    typeof value.role === "string" &&
    (typeof value.direction === "string" || value.direction === null)
  );
}

function isEventAmountSemantics(value: unknown): value is EventAmountSemantics {
  if (!isRecord(value)) return false;
  return (
    value.schema_version === "event-amount-semantics-v1" &&
    ["unreported", "reported", "reported_unclassified"].includes(String(value.state)) &&
    isNullableNumber(value.amount) &&
    isNullableNumber(value.display_amount) &&
    isNullableString(value.currency) &&
    isNullableString(value.amount_kind) &&
    isNullableString(value.period_start) &&
    isNullableString(value.period_end) &&
    isNullableNumber(value.visual_weight) &&
    typeof value.width_eligible === "boolean" &&
    typeof value.aggregate_eligible === "boolean" &&
    (value.aggregation_key === null || isAmountAggregationKey(value.aggregation_key)) &&
    isNullableString(value.non_aggregation_reason)
  );
}

function isEventAmountSummary(value: unknown): value is EventAmountSummary {
  if (!isRecord(value) || !isRecord(value.semantics)) return false;
  return (
    value.schema_version === "event-amount-semantics-v1" &&
    typeof value.event_count === "number" &&
    typeof value.reported_event_count === "number" &&
    typeof value.unreported_event_count === "number" &&
    typeof value.unclassified_event_count === "number" &&
    typeof value.bucket_count === "number" &&
    Array.isArray(value.buckets) &&
    value.buckets.every(isEventAmountBucket) &&
    isStringArray(value.unreported_event_ids) &&
    isStringArray(value.unclassified_event_ids) &&
    isStringArray(value.incomparable_dimensions) &&
    value.cross_bucket_summation_performed === false &&
    typeof value.comparable_reported_total_available === "boolean" &&
    isNullableNumber(value.comparable_reported_total) &&
    typeof value.comparable_reported_total_complete === "boolean" &&
    value.semantics.unknown_amount_is_zero === false &&
    value.semantics.unknown_amount_has_visual_weight === false &&
    isStringArray(value.semantics.aggregation_key) &&
    value.semantics.incomparable_buckets_are_summed === false &&
    isRecord(value.filters)
  );
}

function isEventAmountBucket(value: unknown): value is EventAmountBucket {
  if (!isRecord(value) || !isAmountAggregationKey(value)) return false;
  const bucket = value as Record<string, unknown>;
  return (
    typeof bucket.total_amount === "number" &&
    typeof bucket.visual_weight_total === "number" &&
    typeof bucket.event_count === "number" &&
    isStringArray(bucket.event_ids)
  );
}

function isAmountAggregationKey(value: unknown): value is AmountAggregationKey {
  return (
    isRecord(value) &&
    typeof value.currency === "string" &&
    typeof value.amount_kind === "string" &&
    isNullableString(value.period_start) &&
    isNullableString(value.period_end)
  );
}

function isNullableNumber(value: unknown): value is number | null {
  return (typeof value === "number" && Number.isFinite(value)) || value === null;
}

function isNullableString(value: unknown): value is string | null {
  return typeof value === "string" || value === null;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
