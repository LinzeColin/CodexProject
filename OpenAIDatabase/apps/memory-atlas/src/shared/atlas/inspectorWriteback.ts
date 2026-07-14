import { normalizeMemoryTier } from "../../data/atlas";
import type { AtlasNode } from "../../types";
import { type SharedAtlasState } from "../../state/sharedAtlasState";
import { InspectorExplanation, WritebackAction, WritebackProposal, WritebackProposalDraftInput } from "./contracts";
import { WRITEBACK_QUEUE_KEY, writebackActionLabels } from "./runtimeConfig";
import { humanCategoryLabel, humanNodeTitle, humanThemeLabel } from "./semanticHuman";
import { importanceScore } from "./tierTopicModels";
import { formatScore, translateAction, translateStaleness } from "./utils";



export function buildInspectorExplanation(node: AtlasNode, edgeCount: number, sharedState: SharedAtlasState): InspectorExplanation {
  const tierScore = modelTierScore(node.memory_tier);
  const importanceScore = modelImportanceScore(node.importance);
  const confidenceScore = modelConfidenceScore(node.confidence);
  const derivedWeight = node.metrics?.weight_score;
  const calculatedWeight = tierScore * 0.5 + importanceScore * 0.3 + confidenceScore * 0.2;
  const displayedWeight = typeof derivedWeight === "number" ? derivedWeight : calculatedWeight;
  const decisionImpact = node.category === "decision" ? 1 : 0;
  const sensitivityPenalty = modelSensitivityPenalty(node);
  const displayedLeverage = node.metrics?.roi?.leverage_score;
  const calculatedLeverage = Math.max(0, displayedWeight + decisionImpact * 0.15 - sensitivityPenalty);
  const leverageValue = typeof displayedLeverage === "number" ? displayedLeverage : calculatedLeverage;
  const theme = humanThemeLabel(node);
  const focusNode = sharedState.focus.inspector.nodeId || sharedState.selection.nodeId || node.id;
  return {
    summary: `这条记忆当前作为「${humanCategoryLabel(node.category)}」解释：默认面板只使用派生层级、分类、日期、连接数、ROI 和共享焦点状态，不展示 raw transcript。`,
    formulas: [
      {
        label: "记忆权重",
        value: formatScore(displayedWeight),
        formula: "memory_weight = tier*0.5 + importance*0.3 + confidence*0.2",
        parameters: `tier=${tierScore.toFixed(2)}, importance=${importanceScore.toFixed(2)}, confidence=${confidenceScore.toFixed(2)}`,
      },
      {
        label: "ROI Leverage",
        value: `${formatScore(leverageValue)} · ${translateAction(node.metrics?.roi?.recommended_action)}`,
        formula: "leverage_score = max(0, memory_weight + decision_impact*0.15 - sensitivity_penalty)",
        parameters: `decision_impact=${decisionImpact}, sensitivity_penalty=${sensitivityPenalty.toFixed(2)}, stale=${translateStaleness(node.metrics?.roi?.staleness_status)}`,
      },
      {
        label: "共享焦点",
        value: `${sharedState.sync.updatedBy} · r${sharedState.sync.revision}`,
        formula: "sharedAtlasReducer -> focus(inspector/home/galaxy/timeline/roi)",
        parameters: `node=${focusNode}, cluster=${sharedState.focus.inspector.clusterId ?? "none"}`,
      },
    ],
    evidence: [
      { label: "主题", value: theme },
      { label: "层级 / 分类", value: `${normalizeMemoryTier(node.memory_tier) || "未知"} / ${humanCategoryLabel(node.category)}` },
      { label: "日期 / 时效", value: `${node.date || "未知"} / ${node.validity || translateStaleness(node.metrics?.roi?.staleness_status)}` },
      { label: "连接数", value: edgeCount.toLocaleString() },
      { label: "来源", value: node.source_label ?? node.data_source ?? "脱敏派生快照" },
    ],
    safetyNotes: [
      "默认解释只读 redacted derived snapshot。",
      "结构化字段和低敏摘要位于 Debug 面板，默认关闭。",
      "长期记忆写回只生成提案 JSON，不能直接修改主动记忆库。",
    ],
  };
}



export function modelTierScore(value: string | undefined): number {
  const tier = normalizeMemoryTier(value);
  if (tier === "核心画像") return 1;
  if (tier === "一般") return 0.66;
  if (tier === "临时") return 0.28;
  return 0.5;
}



export function modelImportanceScore(value: string | undefined): number {
  if (value === "高") return 1;
  if (value === "中") return 0.62;
  if (value === "低") return 0.32;
  return 0.5;
}



export function modelConfidenceScore(value: string | undefined): number {
  if (value === "high" || value === "高") return 1;
  if (value === "medium" || value === "中") return 0.72;
  if (value === "low" || value === "低") return 0.45;
  return 0.72;
}



export function modelSensitivityPenalty(node: AtlasNode): number {
  if (node.visual?.sensitive || node.category === "temporary_or_sensitive" || node.category === "security_boundary") return 0.35;
  return 0.1;
}



export function buildWritebackProposalDraft(input: WritebackProposalDraftInput): WritebackProposal {
  const text = input.proposedText.trim();
  const reason = input.reason.trim();
  const idSeed = `${input.node.id}:${input.action}:${text}:${reason}:${input.proposalCount + 1}:${input.proposalIdPrefix}`;
  return {
    schema_version: input.policy.proposal_schema_version || "memory_change_proposal.v1",
    proposal_id: `${input.proposalIdPrefix}_${compactTimestamp(input.now)}_${stableHash(idSeed)}`,
    created_at: input.now,
    status: "draft_pending_agent_apply",
    target_ref: {
      node_id: input.node.id,
      memory_id: input.node.memory_id ?? input.node.id,
      label: input.node.label,
      source_file: input.node.source_label ?? input.node.data_source ?? "visual_snapshot",
      base_date: input.node.date ?? "",
    },
    action: input.action,
    payload: {
      proposed_text: text,
      reason,
      current_tier: normalizeMemoryTier(input.node.memory_tier),
      current_category: input.node.category ?? "",
    },
    diff: buildProposalDiff(input.baseText, text),
    version: {
      revision: (input.latest?.version.revision ?? 0) + 1,
      parent_proposal_id: input.latest?.proposal_id ?? null,
      rollback_unit: input.policy.rollback_unit || "per_memory_version",
      supersedes_proposal_id: null,
    },
    review: buildProposalReview(input.action, input.node, reason),
    safety: {
      direct_frontend_mutation_of_active_memory: false,
      requires_conflict_check: true,
      requires_agent_or_human_apply: true,
      forbidden_payload: input.policy.frontend_payload_contract?.forbidden_payload ?? [
        "plaintext secrets",
        "raw conversation text",
        "record hashes",
        "local absolute paths",
      ],
    },
  };
}



export function buildProposalDiff(baseText: string, proposedText: string): NonNullable<WritebackProposal["diff"]> {
  const base = normalizeTextForDiff(baseText);
  const proposed = normalizeTextForDiff(proposedText);
  const baseSegments = splitReadableSegments(base);
  const proposedSegments = splitReadableSegments(proposed);
  const baseSet = new Set(baseSegments);
  const proposedSet = new Set(proposedSegments);
  const changedSegments =
    proposedSegments.filter((segment) => !baseSet.has(segment)).length +
    baseSegments.filter((segment) => !proposedSet.has(segment)).length;
  const lengthDelta = proposed.length - base.length;
  return {
    base_text: base,
    proposed_text: proposed,
    length_delta: lengthDelta,
    changed_segments: changedSegments,
    summary: `长度 ${lengthDelta > 0 ? "+" : ""}${lengthDelta}，片段变化 ${changedSegments}`,
  };
}



export function buildProposalReview(action: WritebackAction, node: AtlasNode, reason: string): NonNullable<WritebackProposal["review"]> {
  const tier = normalizeMemoryTier(node.memory_tier);
  const actionLabel = writebackActionLabels[action];
  return {
    human_summary: `${actionLabel}：${humanNodeTitle(node)}。${reason || "需要补充证据和冲突检查后再写入。"} `,
    agent_next_step: "重新读取当前主动记忆库和历史提案，核对来源、冲突、敏感字段与版本号，然后写入提案历史并提交 git 回滚点。",
    conflict_policy: `目标层级 ${tier || "未知"}；如果现有库已出现更新版本或同主题相反结论，必须先生成冲突报告，不可静默覆盖。`,
    apply_status: "proposal_only_pending_agent_apply",
  };
}



export function normalizeTextForDiff(value: string | undefined): string {
  return (value ?? "").replace(/\s+/g, " ").trim();
}



export function splitReadableSegments(value: string): string[] {
  return value
    .split(/[。！？!?;；\n]+/)
    .map((segment) => segment.trim())
    .filter(Boolean);
}



export function loadWritebackProposals(): WritebackProposal[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(WRITEBACK_QUEUE_KEY);
    if (!raw) return [];
    const payload: unknown = JSON.parse(raw);
    if (!Array.isArray(payload)) return [];
    return payload.filter(isWritebackProposal);
  } catch {
    return [];
  }
}



export function saveWritebackProposals(proposals: WritebackProposal[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(WRITEBACK_QUEUE_KEY, JSON.stringify(proposals));
}



export function isWritebackProposal(value: unknown): value is WritebackProposal {
  if (!value || typeof value !== "object") return false;
  const record = value as Partial<WritebackProposal>;
  return (
    typeof record.schema_version === "string" &&
    typeof record.proposal_id === "string" &&
    typeof record.created_at === "string" &&
    record.status === "draft_pending_agent_apply" &&
    Boolean(record.target_ref) &&
    Boolean(record.payload) &&
    Boolean(record.version)
  );
}



export function downloadJson(filename: string, payload: unknown) {
  const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}



export function compactTimestamp(value: string): string {
  return value.replace(/[-:.]/g, "").replace("T", "T").replace("Z", "Z");
}



export function stableHash(value: string): string {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(36).padStart(7, "0").slice(0, 7);
}
