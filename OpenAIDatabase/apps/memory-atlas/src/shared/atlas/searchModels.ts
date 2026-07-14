import { getMemoryNodes, normalizeMemoryTier } from "../../data/atlas";
import type { AtlasNode, MemoryAtlas } from "../../types";
import { Search2Filters, Search2Result, Search2SessionSummary } from "./contracts";
import { buildSearchResultPreview, countBy, humanNodeDisplayTitle, humanThemeLabel, humanizeStatement, normalizeDisplayKey, topRows } from "./semanticHuman";
import { addDays, isNodeBetween, maxNodeDate, truncate } from "./utils";



export function buildSearch2Results(atlas: MemoryAtlas, nodes: AtlasNode[], filters: Search2Filters): Search2Result[] {
  const latest = maxNodeDate(nodes) ?? new Date();
  const query = normalizeSearch2Text(filters.query);
  return nodes
    .map((node) => buildSearch2Result(atlas, node, latest, query))
    .filter((result) => {
      if (filters.tier !== "all" && result.tier !== filters.tier) return false;
      if (filters.topic !== "all" && result.topic !== filters.topic) return false;
      if (filters.recency !== "all" && result.recency !== filters.recency) return false;
      if (filters.importance !== "all" && result.importance !== filters.importance) return false;
      if (filters.evidenceOnly && result.evidence_refs.length === 0) return false;
      if (!query) return true;
      return search2CandidateFields(result, result.node).some((value) => normalizeSearch2Text(value).includes(query));
    })
    .map((result) => ({
      ...result,
      matched_reason: buildSearch2MatchedReason(result, query),
      score: search2Score(result, query),
    }))
    .sort((a, b) => b.score - a.score || (b.node.date ?? "").localeCompare(a.node.date ?? "") || a.title.localeCompare(b.title, "zh-CN"));
}



export function buildSearch2Result(atlas: MemoryAtlas, node: AtlasNode, latest: Date, query: string): Search2Result {
  const duplicateCount = duplicateCountForNode(nodesForDuplicateCount(atlas), node);
  const preview = buildSearchResultPreview(node, duplicateCount);
  const topic = humanThemeLabel(node);
  const evidenceRefs = buildSearch2EvidenceRefs(atlas, node);
  const recency = search2RecencyForNode(node, latest);
  const importance = search2ImportanceForNode(node);
  const tier = search2TierForNode(node, recency);
  return {
    result_id: node.id,
    title: preview.title,
    summary: preview.summary,
    source: node.source_label || node.data_source || atlas.source_contract.export_profile || "redacted snapshot",
    tier,
    topic,
    recency,
    importance,
    matched_reason: query ? "matched_reason pending query scoring" : "matched_reason default ranking by importance, recency and evidence",
    evidence_refs: evidenceRefs,
    jump_to_starfield: node.visual?.cluster ? `cluster:${node.visual.cluster}` : node.id,
    jump_to_river: node.date ? `date:${node.date}` : "no_river_event_ref",
    open_inspector: node.id,
    proposal_candidate: search2ProposalCandidate(node, importance, recency),
    score: 0,
    node,
  };
}



export function nodesForDuplicateCount(atlas: MemoryAtlas): AtlasNode[] {
  return getMemoryNodes(atlas);
}



export function duplicateCountForNode(nodes: AtlasNode[], node: AtlasNode): number {
  const title = humanNodeDisplayTitle(node);
  const summary = humanizeStatement(node.statement);
  const key = normalizeDisplayKey(`${node.kind}|${node.category}|${title}|${summary || node.label}`);
  return nodes.filter((candidate) => {
    const candidateKey = normalizeDisplayKey(`${candidate.kind}|${candidate.category}|${humanNodeDisplayTitle(candidate)}|${humanizeStatement(candidate.statement) || candidate.label}`);
    return candidateKey === key;
  }).length || 1;
}



export function buildSearch2EvidenceRefs(atlas: MemoryAtlas, node: AtlasNode): string[] {
  const refs = atlas.edges
    .filter((edge) => edge.source === node.id || edge.target === node.id)
    .slice(0, 4)
    .map((edge) => edge.id);
  if (node.memory_id) refs.unshift(`memory:${node.memory_id}`);
  return Array.from(new Set(refs.length ? refs : [`node:${node.id}`])).slice(0, 4);
}



export function buildSearch2MatchedReason(result: Search2Result, query: string): string {
  const matchedFields = search2CandidateFields(result, result.node)
    .filter((value) => query && normalizeSearch2Text(value).includes(query))
    .slice(0, 3);
  if (matchedFields.length) {
    return `query matched ${matchedFields.map((value) => truncate(value, 36)).join(" / ")}; ranked by ${result.importance} importance, ${result.recency} recency and ${result.evidence_refs.length} evidence_refs.`;
  }
  return `default workflow match: ${result.topic}; ranked by ${result.importance} importance, ${result.recency} recency and ${result.evidence_refs.length} evidence_refs.`;
}



export function search2CandidateFields(result: Search2Result, node: AtlasNode): string[] {
  return [
    result.title,
    result.summary,
    result.source,
    result.tier,
    result.topic,
    result.recency,
    result.importance,
    result.matched_reason,
    node.label,
    node.statement,
    node.category,
    node.memory_tier,
    node.source_label,
    node.data_source,
    node.metrics?.roi?.recommended_action,
  ].filter((value): value is string => Boolean(value));
}



export function search2Score(result: Search2Result, query: string): number {
  const queryScore = query
    ? search2CandidateFields(result, result.node).some((value) => normalizeSearch2Text(value).includes(query)) ? 80 : 0
    : 20;
  const importanceWeight: Record<Search2Result["importance"], number> = {
    critical: 50,
    high: 40,
    medium: 24,
    low: 8,
  };
  const recencyWeight: Record<Search2Result["recency"], number> = {
    recent: 28,
    active: 20,
    stale: 14,
    archival: 8,
  };
  const evidenceScore = Math.min(18, result.evidence_refs.length * 6);
  const proposalScore = result.proposal_candidate ? 10 : 0;
  return queryScore + importanceWeight[result.importance] + recencyWeight[result.recency] + evidenceScore + proposalScore;
}



export function buildSearch2SessionSummary(results: Search2Result[], query: string): Search2SessionSummary {
  const dominantTopics = topRows(countBy(results, (result) => result.topic), 3).map((row) => row.label).filter((label) => label !== "暂无数据");
  const highImportanceHits = results
    .filter((result) => result.importance === "high" || result.importance === "critical")
    .slice(0, 3)
    .map((result) => result.title);
  const staleHits = results
    .filter((result) => result.recency === "stale" || result.tier === "stale")
    .slice(0, 3)
    .map((result) => result.title);
  const missingEvidence = results
    .filter((result) => result.evidence_refs.length === 0)
    .slice(0, 3)
    .map((result) => result.title);
  return {
    query,
    result_count: results.length,
    dominant_topics: dominantTopics,
    high_importance_hits: highImportanceHits,
    stale_or_black_hole_hits: staleHits,
    missing_evidence: missingEvidence,
    next_step: results.length
      ? "Open Inspector for the strongest matched_reason, then use proposal-only handoff if a change is needed."
      : "Use zero_result_recovery before opening a later review workflow hint.",
    proposal_candidate: results.some((result) => result.proposal_candidate),
  };
}



export function search2FilterStateLabel(filters: Search2Filters): string {
  return [
    `query=${filters.query || "all"}`,
    `tier=${filters.tier}`,
    `topic=${filters.topic}`,
    `recency=${filters.recency}`,
    `importance=${filters.importance}`,
    `evidence=${filters.evidenceOnly ? "required" : "optional"}`,
  ].join(" / ");
}



export function search2TierForNode(node: AtlasNode, recency: Search2Result["recency"]): Search2Result["tier"] {
  const tier = normalizeMemoryTier(node.memory_tier);
  if (node.category === "deprecated_info" || recency === "stale") return "stale";
  if (tier.includes("核心") || node.category === "preference") return "core_profile";
  if (node.category === "decision" || node.kind === "decision") return "decision";
  if (node.category === "workflow") return "workflow";
  if (node.category === "project_context" || node.kind === "project") return "project";
  if (node.metrics?.roi?.recommended_action || /机会|opportunity/i.test(`${node.label} ${node.statement ?? ""}`)) return "opportunity";
  return "knowledge";
}



export function search2RecencyForNode(node: AtlasNode, latest: Date): Search2Result["recency"] {
  if (node.category === "deprecated_info" || /过期|deprecated|stale/i.test(`${node.validity ?? ""} ${node.metrics?.roi?.staleness_status ?? ""}`)) {
    return "stale";
  }
  const day = node.date ? new Date(node.date) : null;
  if (!day || Number.isNaN(day.getTime())) return "archival";
  if (isNodeBetween(node, addDays(latest, -30), latest)) return "recent";
  if (isNodeBetween(node, addDays(latest, -180), latest)) return "active";
  return "archival";
}



export function search2ImportanceForNode(node: AtlasNode): Search2Result["importance"] {
  const value = `${node.importance ?? ""} ${node.metrics?.weight_score ?? ""}`.toLowerCase();
  if (/critical|最高|关键|紧急/.test(value)) return "critical";
  if (/high|高/.test(value)) return "high";
  if (/low|低/.test(value)) return "low";
  return "medium";
}



export function search2ProposalCandidate(
  node: AtlasNode,
  importance: Search2Result["importance"],
  recency: Search2Result["recency"],
): boolean {
  const text = `${node.label} ${node.statement ?? ""} ${node.metrics?.roi?.recommended_action ?? ""}`;
  return (
    importance === "critical" ||
    (importance === "high" && recency !== "archival") ||
    /下一步|继续|需要|建议|todo|action|优化|修正|降权|隐藏|补充/i.test(text)
  );
}



export function normalizeSearch2Text(value: string): string {
  return value.toLowerCase().replace(/\s+/g, " ").trim();
}
