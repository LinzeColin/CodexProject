export const PROPOSAL_DRAFT_SCHEMA_VERSION = "memory_atlas_proposal_draft.v1" as const;
export const PROPOSAL_DRAFT_STORE_SCHEMA_VERSION = "memory_atlas_proposal_draft_store.v1" as const;
export const PROPOSAL_DRAFT_STORE_KEY = "memory-atlas.proposal-drafts.v1" as const;

export const PROPOSAL_EDITABLE_FIELDS = [
  "importance",
  "priority",
  "status",
  "theme_override",
  "action_state",
  "note",
] as const;

export const PROPOSAL_DRAFT_TARGET_TYPES = [
  "memory_node",
  "suggested_action",
  "tier_asset",
  "topic_classification",
] as const;

export const PROPOSAL_DRAFT_STATUSES = [
  "draft_local",
  "needs_review",
  "ready_for_agent_apply",
  "reverted",
] as const;

export const PROPOSAL_DRAFT_REFRESH_WARNING =
  "当前有未提交的 proposal draft。刷新或关闭页面前请确认已保存、导出或撤销本地调整。";

export type ProposalEditableField = (typeof PROPOSAL_EDITABLE_FIELDS)[number];
export type ProposalDraftTargetType = (typeof PROPOSAL_DRAFT_TARGET_TYPES)[number];
export type ProposalDraftStatus = (typeof PROPOSAL_DRAFT_STATUSES)[number];
export type ProposalDraftValue = string | number | boolean | null;

export interface ProposalDraftChange {
  field: ProposalEditableField;
  old_value: ProposalDraftValue;
  proposed_value: ProposalDraftValue;
  reason: string;
  evidence_refs: string[];
  confidence: number;
  status: ProposalDraftStatus;
  created_at: string;
  updated_at: string;
  proposal_only: true;
  requires_conflict_check: true;
  requires_agent_or_human_apply: true;
  rollback_hint: string;
}

export interface ProposalDraft {
  draft_id: string;
  schema_version: typeof PROPOSAL_DRAFT_SCHEMA_VERSION;
  parent_snapshot_id: string;
  source_surface: string;
  target_type: ProposalDraftTargetType;
  target_id: string;
  changes: ProposalDraftChange[];
  status: ProposalDraftStatus;
  created_at: string;
  updated_at: string;
  proposal_only: true;
  requires_conflict_check: true;
  requires_agent_or_human_apply: true;
  rollback_hint: string;
}

export interface ProposalDraftStoreSnapshot {
  schema_version: typeof PROPOSAL_DRAFT_STORE_SCHEMA_VERSION;
  store_key: typeof PROPOSAL_DRAFT_STORE_KEY;
  saved_at: string;
  drafts: ProposalDraft[];
}

export interface ProposalDraftCreateInput {
  draft_id: string;
  parent_snapshot_id: string;
  source_surface: string;
  target_type: ProposalDraftTargetType;
  target_id: string;
  now: string;
  rollback_hint?: string;
}

export interface ProposalDraftChangeInput {
  field: ProposalEditableField;
  old_value: ProposalDraftValue;
  proposed_value: ProposalDraftValue;
  reason: string;
  evidence_refs?: string[];
  confidence?: number;
  now: string;
  rollback_hint?: string;
}

const DEFAULT_ROLLBACK_HINT = "撤销本地 draft change；如已导出 proposal，则生成新的 superseding proposal，不覆盖历史记录。";

export function createProposalDraft(input: ProposalDraftCreateInput): ProposalDraft {
  return {
    draft_id: input.draft_id,
    schema_version: PROPOSAL_DRAFT_SCHEMA_VERSION,
    parent_snapshot_id: input.parent_snapshot_id,
    source_surface: input.source_surface,
    target_type: input.target_type,
    target_id: input.target_id,
    changes: [],
    status: "draft_local",
    created_at: input.now,
    updated_at: input.now,
    proposal_only: true,
    requires_conflict_check: true,
    requires_agent_or_human_apply: true,
    rollback_hint: input.rollback_hint ?? DEFAULT_ROLLBACK_HINT,
  };
}

export function upsertProposalDraftChange(draft: ProposalDraft, input: ProposalDraftChangeInput): ProposalDraft {
  assertEditableField(input.field);
  const change: ProposalDraftChange = {
    field: input.field,
    old_value: input.old_value,
    proposed_value: input.proposed_value,
    reason: input.reason.trim(),
    evidence_refs: normalizeEvidenceRefs(input.evidence_refs ?? []),
    confidence: clampConfidence(input.confidence ?? 0.72),
    status: "draft_local",
    created_at: draft.changes.find((item) => item.field === input.field)?.created_at ?? input.now,
    updated_at: input.now,
    proposal_only: true,
    requires_conflict_check: true,
    requires_agent_or_human_apply: true,
    rollback_hint: input.rollback_hint ?? DEFAULT_ROLLBACK_HINT,
  };
  const changes = draft.changes.filter((item) => item.field !== input.field).concat(change);
  return { ...draft, changes, status: "draft_local", updated_at: input.now };
}

export function removeProposalDraftChange(draft: ProposalDraft, field: ProposalEditableField, now: string): ProposalDraft {
  assertEditableField(field);
  const changes = draft.changes.filter((item) => item.field !== field);
  return { ...draft, changes, status: changes.length ? draft.status : "reverted", updated_at: now };
}

export function hasUnsavedProposalDrafts(drafts: ProposalDraft[]): boolean {
  return drafts.some((draft) => draft.changes.length > 0 && draft.status !== "reverted");
}

export function proposalDraftRefreshWarning(drafts: ProposalDraft[]): string | null {
  return hasUnsavedProposalDrafts(drafts) ? PROPOSAL_DRAFT_REFRESH_WARNING : null;
}

export function serializeProposalDraftStore(drafts: ProposalDraft[], savedAt: string): string {
  const snapshot: ProposalDraftStoreSnapshot = {
    schema_version: PROPOSAL_DRAFT_STORE_SCHEMA_VERSION,
    store_key: PROPOSAL_DRAFT_STORE_KEY,
    saved_at: savedAt,
    drafts,
  };
  return `${JSON.stringify(snapshot, null, 2)}\n`;
}

export function parseProposalDraftStore(raw: string | null): ProposalDraft[] {
  if (!raw) return [];
  try {
    const payload: unknown = JSON.parse(raw);
    if (!isProposalDraftStoreSnapshot(payload)) return [];
    return payload.drafts.filter(isProposalDraft);
  } catch {
    return [];
  }
}

export function loadProposalDraftStore(storage: Pick<Storage, "getItem"> | null = defaultStorage()): ProposalDraft[] {
  if (!storage) return [];
  return parseProposalDraftStore(storage.getItem(PROPOSAL_DRAFT_STORE_KEY));
}

export function saveProposalDraftStore(
  drafts: ProposalDraft[],
  savedAt: string,
  storage: Pick<Storage, "setItem"> | null = defaultStorage(),
) {
  if (!storage) return;
  storage.setItem(PROPOSAL_DRAFT_STORE_KEY, serializeProposalDraftStore(drafts, savedAt));
}

export function clearProposalDraftStore(storage: Pick<Storage, "removeItem"> | null = defaultStorage()) {
  if (!storage) return;
  storage.removeItem(PROPOSAL_DRAFT_STORE_KEY);
}

export function isProposalEditableField(value: string): value is ProposalEditableField {
  return (PROPOSAL_EDITABLE_FIELDS as readonly string[]).includes(value);
}

function assertEditableField(value: string): asserts value is ProposalEditableField {
  if (!isProposalEditableField(value)) {
    throw new Error(`Unsupported proposal draft field: ${value}`);
  }
}

function normalizeEvidenceRefs(values: string[]): string[] {
  return values.map((value) => value.trim()).filter(Boolean).slice(0, 12);
}

function clampConfidence(value: number): number {
  if (!Number.isFinite(value)) return 0.72;
  return Math.max(0, Math.min(1, value));
}

function defaultStorage(): Storage | null {
  return typeof window === "undefined" ? null : window.localStorage;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object";
}

function isProposalDraftStoreSnapshot(value: unknown): value is ProposalDraftStoreSnapshot {
  return (
    isRecord(value) &&
    value.schema_version === PROPOSAL_DRAFT_STORE_SCHEMA_VERSION &&
    value.store_key === PROPOSAL_DRAFT_STORE_KEY &&
    typeof value.saved_at === "string" &&
    Array.isArray(value.drafts)
  );
}

function isProposalDraft(value: unknown): value is ProposalDraft {
  if (!isRecord(value)) return false;
  return (
    typeof value.draft_id === "string" &&
    value.schema_version === PROPOSAL_DRAFT_SCHEMA_VERSION &&
    typeof value.parent_snapshot_id === "string" &&
    typeof value.source_surface === "string" &&
    typeof value.target_id === "string" &&
    typeof value.target_type === "string" &&
    PROPOSAL_DRAFT_TARGET_TYPES.includes(value.target_type as ProposalDraftTargetType) &&
    Array.isArray(value.changes) &&
    value.changes.every(isProposalDraftChange) &&
    typeof value.status === "string" &&
    PROPOSAL_DRAFT_STATUSES.includes(value.status as ProposalDraftStatus) &&
    value.proposal_only === true &&
    value.requires_conflict_check === true &&
    value.requires_agent_or_human_apply === true
  );
}

function isProposalDraftChange(value: unknown): value is ProposalDraftChange {
  if (!isRecord(value)) return false;
  return (
    typeof value.field === "string" &&
    isProposalEditableField(value.field) &&
    typeof value.reason === "string" &&
    Array.isArray(value.evidence_refs) &&
    value.evidence_refs.every((item) => typeof item === "string") &&
    typeof value.confidence === "number" &&
    typeof value.status === "string" &&
    PROPOSAL_DRAFT_STATUSES.includes(value.status as ProposalDraftStatus) &&
    typeof value.created_at === "string" &&
    typeof value.updated_at === "string" &&
    value.proposal_only === true &&
    value.requires_conflict_check === true &&
    value.requires_agent_or_human_apply === true &&
    typeof value.rollback_hint === "string"
  );
}
