import { Download, RotateCcw, Save } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { AtlasNode } from "../types";
import {
  PROPOSAL_DRAFT_SCHEMA_VERSION,
  PROPOSAL_DRAFT_STORE_KEY,
  PROPOSAL_EDITABLE_FIELDS,
  createProposalDraft,
  loadProposalDraftStore,
  proposalDraftRefreshWarning,
  removeProposalDraftChange,
  saveProposalDraftStore,
  serializeProposalDraftStore,
  upsertProposalDraftChange,
  type ProposalDraft,
  type ProposalDraftChange,
} from "../state/proposalDraftStore";
import { ProposalDiffPreview, type ProposalDiffPreviewChange } from "./ProposalDiffPreview";

const EXPORT_SCHEMA_VERSION = "memory_atlas_proposal_export.v1" as const;
const IMPORTANCE_VALUES = ["低", "中", "高"] as const;
const PRIORITY_VALUES = ["watch", "p3", "p2", "p1", "p0"] as const;

interface ProposalEditorProps {
  node: AtlasNode;
  parentSnapshotId: string;
  sourceSurface: string;
}

export function ProposalEditor({ node, parentSnapshotId, sourceSurface }: ProposalEditorProps) {
  const baseImportance = normalizeImportance(node.importance);
  const basePriority = inferPriority(node);
  const [importanceIndex, setImportanceIndex] = useState(() => IMPORTANCE_VALUES.indexOf(baseImportance));
  const [priorityIndex, setPriorityIndex] = useState(() => PRIORITY_VALUES.indexOf(basePriority));
  const [note, setNote] = useState("");
  const [drafts, setDrafts] = useState<ProposalDraft[]>(() => loadProposalDraftStore());
  const [savedAt, setSavedAt] = useState<string | null>(null);

  useEffect(() => {
    setImportanceIndex(IMPORTANCE_VALUES.indexOf(baseImportance));
    setPriorityIndex(PRIORITY_VALUES.indexOf(basePriority));
    setNote("");
  }, [baseImportance, basePriority, node.id]);

  const draftId = `draft_${stableId(`${parentSnapshotId}:${sourceSurface}:${node.id}`)}`;
  const proposedImportance = IMPORTANCE_VALUES[importanceIndex] ?? baseImportance;
  const proposedPriority = PRIORITY_VALUES[priorityIndex] ?? basePriority;
  const unsavedChanges = useMemo(
    () => buildDraftChanges({
      baseImportance,
      proposedImportance,
      basePriority,
      proposedPriority,
      note,
    }),
    [baseImportance, basePriority, note, proposedImportance, proposedPriority],
  );
  const warning = proposalDraftRefreshWarning(
    unsavedChanges.length
      ? [
          createProposalDraft({
            draft_id: draftId,
            parent_snapshot_id: parentSnapshotId,
            source_surface: sourceSurface,
            target_type: "memory_node",
            target_id: node.id,
            now: new Date().toISOString(),
          }),
        ]
      : drafts,
  );
  const diffChanges = useMemo(() => buildDiffPreviewChanges(unsavedChanges), [unsavedChanges]);
  const exportPayload = useMemo(
    () => buildProposalExport({
      node,
      parentSnapshotId,
      sourceSurface,
      draftId,
      baseImportance,
      proposedImportance,
      basePriority,
      proposedPriority,
      note,
      unsavedChanges,
      drafts,
    }),
    [
      baseImportance,
      basePriority,
      draftId,
      drafts,
      node,
      note,
      parentSnapshotId,
      proposedImportance,
      proposedPriority,
      sourceSurface,
      unsavedChanges,
    ],
  );

  function persistDraft() {
    const now = new Date().toISOString();
    let draft = drafts.find((item) => item.draft_id === draftId) ?? createProposalDraft({
      draft_id: draftId,
      parent_snapshot_id: parentSnapshotId,
      source_surface: sourceSurface,
      target_type: "memory_node",
      target_id: node.id,
      now,
    });
    unsavedChanges.forEach((change) => {
      draft = upsertProposalDraftChange(draft, {
        field: change.field,
        old_value: change.old_value,
        proposed_value: change.proposed_value,
        reason: change.reason,
        evidence_refs: change.evidence_refs,
        confidence: change.confidence,
        now,
        rollback_hint: change.rollback_hint,
      });
    });
    const next = drafts.filter((item) => item.draft_id !== draftId).concat(draft);
    setDrafts(next);
    saveProposalDraftStore(next, now);
    setSavedAt(now);
  }

  function resetLocalChanges() {
    const now = new Date().toISOString();
    const existing = drafts.find((item) => item.draft_id === draftId);
    const clearedDraft = existing
      ? PROPOSAL_EDITABLE_FIELDS.reduce((draft, field) => removeProposalDraftChange(draft, field, now), existing)
      : null;
    const next = drafts.filter((item) => item.draft_id !== draftId);
    if (clearedDraft) next.push(clearedDraft);
    setDrafts(next);
    saveProposalDraftStore(next, now);
    setImportanceIndex(IMPORTANCE_VALUES.indexOf(baseImportance));
    setPriorityIndex(PRIORITY_VALUES.indexOf(basePriority));
    setNote("");
    setSavedAt(now);
  }

  function downloadProposalJson() {
    const filename = `${draftId}_proposal.json`;
    const blob = new Blob([`${JSON.stringify(exportPayload, null, 2)}\n`], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  return (
    <section
      aria-label="Proposal UI"
      className="proposal-editor"
      data-active-memory-mutation="false"
      data-proposal-editor={draftId}
      data-proposal-only="true"
      data-proposal-store-key={PROPOSAL_DRAFT_STORE_KEY}
    >
      <div className="panel-title-row">
        <h4>Proposal UI</h4>
        <span>{PROPOSAL_DRAFT_SCHEMA_VERSION}</span>
      </div>

      {warning ? <p className="proposal-editor-warning">{warning}</p> : null}

      <div className="proposal-editor-grid">
        <FieldRange
          ariaLabel="调整 importance"
          field="importance"
          originalValue={baseImportance}
          proposedValue={proposedImportance}
          value={importanceIndex}
          max={IMPORTANCE_VALUES.length - 1}
          onChange={setImportanceIndex}
        />
        <FieldRange
          ariaLabel="调整 priority"
          field="priority"
          originalValue={basePriority}
          proposedValue={proposedPriority}
          value={priorityIndex}
          max={PRIORITY_VALUES.length - 1}
          onChange={setPriorityIndex}
        />
      </div>

      <label className="proposal-field-control">
        <span>note</span>
        <textarea
          aria-label="proposal note"
          onChange={(event) => setNote(event.target.value)}
          placeholder="说明为什么要调整；不要粘贴 raw/private 内容。"
          rows={3}
          value={note}
        />
      </label>

      <ProposalDiffPreview changes={diffChanges} exportSchemaVersion={EXPORT_SCHEMA_VERSION} />

      <div className="proposal-editor-actions">
        <button disabled={!unsavedChanges.length} onClick={persistDraft} type="button">
          <Save size={15} />
          保存本地 draft
        </button>
        <button disabled={!unsavedChanges.length} onClick={downloadProposalJson} type="button">
          <Download size={15} />
          导出 proposal JSON
        </button>
        <button disabled={!unsavedChanges.length && !drafts.some((item) => item.draft_id === draftId)} onClick={resetLocalChanges} type="button">
          <RotateCcw size={15} />
          撤销本地调整
        </button>
      </div>

      <small>
        {savedAt ? `saved_at ${new Date(savedAt).toLocaleString("zh-CN")}` : "仅保存到本地 draft store；不会直接写长期记忆。"}
      </small>
    </section>
  );
}

function FieldRange({
  ariaLabel,
  field,
  originalValue,
  proposedValue,
  value,
  max,
  onChange,
}: {
  ariaLabel: string;
  field: "importance" | "priority";
  originalValue: string;
  proposedValue: string;
  value: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="proposal-field-control">
      <span>{field}</span>
      <div className="proposal-range-row">
        <strong>original_value: {originalValue}</strong>
        <strong>proposed_value: {proposedValue}</strong>
      </div>
      <input
        aria-label={ariaLabel}
        max={max}
        min={0}
        onChange={(event) => onChange(Number(event.target.value))}
        type="range"
        value={value}
      />
    </label>
  );
}

function buildDraftChanges(input: {
  baseImportance: string;
  proposedImportance: string;
  basePriority: string;
  proposedPriority: string;
  note: string;
}): ProposalDraftChange[] {
  const now = new Date().toISOString();
  const changes: ProposalDraftChange[] = [];
  if (input.baseImportance !== input.proposedImportance) {
    changes.push(buildChange("importance", input.baseImportance, input.proposedImportance, "调整重要性会影响首页排序、星系视觉强调和后续复盘优先级。", now));
  }
  if (input.basePriority !== input.proposedPriority) {
    changes.push(buildChange("priority", input.basePriority, input.proposedPriority, "调整优先级会影响建议动作排队和本轮复盘顺序。", now));
  }
  if (input.note.trim()) {
    changes.push(buildChange("note", "", input.note.trim(), "note 只保存人类解释，不改变 active memory。", now));
  }
  return changes;
}

function buildChange(
  field: ProposalDraftChange["field"],
  oldValue: string,
  proposedValue: string,
  reason: string,
  now: string,
): ProposalDraftChange {
  return {
    field,
    old_value: oldValue,
    proposed_value: proposedValue,
    reason,
    evidence_refs: ["derived_memory_atlas_snapshot", "human_frontend_review"],
    confidence: 0.72,
    status: "draft_local",
    created_at: now,
    updated_at: now,
    proposal_only: true,
    requires_conflict_check: true,
    requires_agent_or_human_apply: true,
    rollback_hint: `撤销 ${field} 本地调整，恢复 original_value=${oldValue || "empty"}。`,
  };
}

function buildDiffPreviewChanges(changes: ProposalDraftChange[]): ProposalDiffPreviewChange[] {
  return changes.map((change) => ({
    field: change.field,
    original_value: String(change.old_value ?? ""),
    proposed_value: String(change.proposed_value ?? ""),
    impact_summary: change.reason,
    rollback_metadata: {
      rollback_field: change.field,
      rollback_value: String(change.old_value ?? ""),
      rollback_hint: change.rollback_hint,
    },
  }));
}

function buildProposalExport(input: {
  node: AtlasNode;
  parentSnapshotId: string;
  sourceSurface: string;
  draftId: string;
  baseImportance: string;
  proposedImportance: string;
  basePriority: string;
  proposedPriority: string;
  note: string;
  unsavedChanges: ProposalDraftChange[];
  drafts: ProposalDraft[];
}) {
  return {
    schema_version: EXPORT_SCHEMA_VERSION,
    exported_at: new Date().toISOString(),
    draft_id: input.draftId,
    parent_snapshot_id: input.parentSnapshotId,
    source_surface: input.sourceSurface,
    target_ref: {
      target_type: "memory_node",
      target_id: input.node.id,
      memory_id: input.node.memory_id ?? input.node.id,
      label: input.node.label,
    },
    original_value: {
      importance: input.baseImportance,
      priority: input.basePriority,
    },
    proposed_value: {
      importance: input.proposedImportance,
      priority: input.proposedPriority,
      note: input.note.trim(),
    },
    changes: input.unsavedChanges,
    stored_drafts: input.drafts.length,
    rollback_metadata: input.unsavedChanges.map((change) => ({
      rollback_field: change.field,
      rollback_value: change.old_value,
      rollback_hint: change.rollback_hint,
    })),
    safety: {
      proposal_only: true,
      direct_frontend_mutation_of_active_memory: false,
      requires_conflict_check: true,
      requires_agent_or_human_apply: true,
      forbidden_payload: ["raw/private transcript", "plaintext secret", "cookie", "session", "local absolute path"],
    },
    serialized_store_preview: serializeProposalDraftStore(input.drafts, new Date().toISOString()),
  };
}

function normalizeImportance(value: string | undefined): (typeof IMPORTANCE_VALUES)[number] {
  if (value === "高" || value === "high") return "高";
  if (value === "低" || value === "low") return "低";
  return "中";
}

function inferPriority(node: AtlasNode): (typeof PRIORITY_VALUES)[number] {
  const leverage = node.metrics?.roi?.leverage_score ?? 0;
  const importance = normalizeImportance(node.importance);
  if (importance === "高" && leverage >= 0.75) return "p0";
  if (importance === "高") return "p1";
  if (leverage >= 0.6) return "p2";
  if (node.validity === "stale") return "watch";
  return "p3";
}

function stableId(value: string): string {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(36);
}
