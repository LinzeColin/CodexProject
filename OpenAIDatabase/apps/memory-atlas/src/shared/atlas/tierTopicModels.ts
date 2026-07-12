import { normalizeMemoryTier } from "../../data/atlas";
import type { AtlasEdge, AtlasNode } from "../../types";
import { HomeAction, HomeTierAsset, HomeTopicDetail, TierAssetDetail } from "./contracts";
import { evidenceRefsForNode } from "./previewWeatherModels";
import { TIER_ASSET_SORT_WEIGHTS, TIER_ASSET_TOP_LIMIT, TOPIC_CLASSIFICATION_TOP_LIMIT } from "./runtimeConfig";
import { compactThemeLabel, humanCategoryLabel, humanNodeDisplayTitle, humanThemeLabel, selectRepresentativeNode } from "./semanticHuman";
import { averageNodeScore, clampActionScore, confidenceForAction, parentTopicForTopic, roiScoreForNode, topCategoryForNodes, topicClassificationSortScore, topicStateForTopic, trendForTopic } from "./topicActionModels";
import { formatScore, parseDay } from "./utils";



export function buildTierAssetDetails({
  actions,
  graphEdges,
  latest,
  memoryNodes,
  protoStarNodes,
  staleNodes,
  topTopic,
}: {
  actions: HomeAction[];
  graphEdges: AtlasEdge[];
  latest: Date;
  memoryNodes: AtlasNode[];
  protoStarNodes: AtlasNode[];
  staleNodes: AtlasNode[];
  topTopic: { label: string; count: number };
}): HomeTierAsset[] {
  const assetTiers: HomeTierAsset["asset_tier"][] = [
    "core_profile",
    "project",
    "decision",
    "workflow",
    "knowledge",
    "opportunity",
    "stale",
  ];
  const assets = assetTiers
    .map((asset_tier) => {
      const candidates = tierAssetCandidatesFor(asset_tier, memoryNodes, protoStarNodes, staleNodes);
      const node = selectRepresentativeNode(candidates);
      return node ? createTierAssetDetail(asset_tier, node, actions, graphEdges, latest, topTopic.label) : null;
    })
    .filter((asset): asset is HomeTierAsset => Boolean(asset));

  return assets
    .sort((left, right) => tierAssetSortScore(right) - tierAssetSortScore(left))
    .slice(0, TIER_ASSET_TOP_LIMIT);
}



export function tierAssetCandidatesFor(
  assetTier: HomeTierAsset["asset_tier"],
  memoryNodes: AtlasNode[],
  protoStarNodes: AtlasNode[],
  staleNodes: AtlasNode[],
): AtlasNode[] {
  if (assetTier === "core_profile") {
    return memoryNodes.filter((node) => {
      const category = normalizedNodeCategory(node);
      return (
        normalizeMemoryTier(node.memory_tier) === "核心画像" ||
        category.includes("preference") ||
        category.includes("answering_rule") ||
        category.includes("security_boundary")
      );
    });
  }
  if (assetTier === "project") {
    return memoryNodes.filter((node) => textSignalsForNode(node).some((value) => value.includes("project") || value.includes("项目")));
  }
  if (assetTier === "decision") {
    return memoryNodes.filter((node) => node.category === "decision" || textSignalsForNode(node).some((value) => value.includes("决策")));
  }
  if (assetTier === "workflow") {
    return memoryNodes.filter((node) =>
      textSignalsForNode(node).some((value) =>
        ["workflow", "process", "automation", "run_contract", "流程", "工作流", "规则"].some((token) => value.includes(token)),
      ),
    );
  }
  if (assetTier === "opportunity") return protoStarNodes;
  if (assetTier === "stale") return staleNodes;

  const reserved = new Set([
    ...tierAssetCandidatesFor("core_profile", memoryNodes, protoStarNodes, staleNodes).map((node) => node.id),
    ...tierAssetCandidatesFor("project", memoryNodes, protoStarNodes, staleNodes).map((node) => node.id),
    ...tierAssetCandidatesFor("decision", memoryNodes, protoStarNodes, staleNodes).map((node) => node.id),
    ...tierAssetCandidatesFor("workflow", memoryNodes, protoStarNodes, staleNodes).map((node) => node.id),
    ...protoStarNodes.map((node) => node.id),
    ...staleNodes.map((node) => node.id),
  ]);
  return memoryNodes.filter((node) => !reserved.has(node.id));
}



export function createTierAssetDetail(
  asset_tier: HomeTierAsset["asset_tier"],
  node: AtlasNode,
  actions: HomeAction[],
  graphEdges: AtlasEdge[],
  latest: Date,
  fallbackTopic: string,
): HomeTierAsset {
  const value_score = roiScoreForNode(node, 0.48);
  const confidence = confidenceForAction(node, 0.62);
  const theme = compactThemeLabel(humanThemeLabel(node)) || fallbackTopic || "未归类主题";
  const updated_at = node.date || latest.toISOString().slice(0, 10);
  const staleness_status = stalenessStatusForAsset(asset_tier, node, latest);
  const evidence_refs = evidenceRefsForNode(node, graphEdges, `level-asset:${asset_tier}`);
  const linked_action_ids = actions
    .filter((action) => action.linked_asset_ids.includes(node.id) || action.linked_topic_ids.includes(`topic:${theme}`))
    .map((action) => action.action_id);
  const recommended_asset_action = recommendedAssetActionFor(asset_tier, staleness_status, value_score, confidence);
  const title = humanNodeDisplayTitle(node);

  return {
    asset_id: `${asset_tier}:${node.id}`,
    asset_tier,
    confidence,
    evidence_count: evidence_refs.length,
    evidence_refs,
    id: `${asset_tier}:${node.id}`,
    importance: importanceForAsset(value_score),
    last_seen_range: lastSeenRangeForAsset(node, latest),
    linked_action_ids,
    linked_topic_ids: [`topic:${theme}`],
    node,
    priority: priorityForAsset(asset_tier, staleness_status, value_score),
    proposal_hint: recommended_asset_action === "keep" && confidence >= 0.7 ? "proposal_not_needed" : "proposal_recommended",
    proposal_only: true,
    recommended_asset_action,
    rollback_hint: "若资产判断不成立，只关闭面板或撤销后续 proposal 草稿；Phase 1.3 不写长期记忆。",
    source_scope: "redacted_atlas_snapshot",
    staleness_status,
    summary: `${title} 属于 ${asset_tier} 层级资产；主题 ${theme}，当前仅使用 redacted label、层级、分类、日期、ROI 与连接数生成说明。`,
    targetView: "search",
    theme,
    title,
    updated_at,
    value_score,
  };
}



export function tierAssetSortScore(asset: TierAssetDetail): number {
  return (
    asset.value_score * TIER_ASSET_SORT_WEIGHTS.value_weight +
    importanceScore(asset.importance) * TIER_ASSET_SORT_WEIGHTS.importance_weight +
    asset.confidence * TIER_ASSET_SORT_WEIGHTS.confidence_weight -
    stalenessPenalty(asset.staleness_status) * TIER_ASSET_SORT_WEIGHTS.staleness_penalty_weight
  );
}



export function textSignalsForNode(node: AtlasNode): string[] {
  return [node.kind, node.category, node.label, node.source_label, humanCategoryLabel(node.category), normalizeMemoryTier(node.memory_tier)]
    .filter((value): value is string => Boolean(value))
    .map((value) => value.toLowerCase());
}



export function normalizedNodeCategory(node: AtlasNode): string {
  return (node.category || "").toLowerCase();
}



export function stalenessStatusForAsset(
  assetTier: HomeTierAsset["asset_tier"],
  node: AtlasNode,
  latest: Date,
): HomeTierAsset["staleness_status"] {
  if (assetTier === "stale" || node.metrics?.roi?.staleness_status?.includes("stale")) return "stale";
  const day = parseDay(node.date);
  if (!day) return "unknown";
  const ageDays = Math.max(0, Math.round((latest.getTime() - day.getTime()) / 86_400_000));
  return ageDays > 120 ? "needs_review" : "current";
}



export function lastSeenRangeForAsset(node: AtlasNode, latest: Date): string {
  const seen = node.date || "unknown";
  return `${seen}..${latest.toISOString().slice(0, 10)}`;
}



export function importanceForAsset(valueScore: number): HomeTierAsset["importance"] {
  if (valueScore >= 0.72) return "high";
  if (valueScore >= 0.45) return "medium";
  return "low";
}



export function importanceScore(importance: TierAssetDetail["importance"]): number {
  if (importance === "high") return 1;
  if (importance === "medium") return 0.62;
  return 0.32;
}



export function priorityForAsset(
  assetTier: HomeTierAsset["asset_tier"],
  stalenessStatus: HomeTierAsset["staleness_status"],
  valueScore: number,
): HomeTierAsset["priority"] {
  if (stalenessStatus === "stale") return "p1";
  if (assetTier === "core_profile" || valueScore >= 0.78) return "p0";
  if (assetTier === "decision" || assetTier === "project" || valueScore >= 0.58) return "p1";
  if (stalenessStatus === "needs_review") return "p2";
  return "watch";
}



export function stalenessPenalty(stalenessStatus: TierAssetDetail["staleness_status"]): number {
  if (stalenessStatus === "stale") return 0.85;
  if (stalenessStatus === "needs_review") return 0.45;
  if (stalenessStatus === "unknown") return 0.25;
  return 0.05;
}



export function recommendedAssetActionFor(
  assetTier: HomeTierAsset["asset_tier"],
  stalenessStatus: HomeTierAsset["staleness_status"],
  valueScore: number,
  confidence: number,
): HomeTierAsset["recommended_asset_action"] {
  if (stalenessStatus === "stale") return "lower_priority";
  if (stalenessStatus === "needs_review") return "review";
  if (assetTier === "opportunity") return "validate";
  if (assetTier === "workflow") return "consolidate";
  if (confidence < 0.5) return "review";
  if (valueScore < 0.35) return "defer";
  return "keep";
}



export function buildTopicClassificationDetails({
  actions,
  graphEdges,
  memoryNodes,
  protoStarNodes,
  recentNodes,
  olderComparableNodes,
  staleNodes,
  tierAssets,
}: {
  actions: HomeAction[];
  graphEdges: AtlasEdge[];
  memoryNodes: AtlasNode[];
  protoStarNodes: AtlasNode[];
  recentNodes: AtlasNode[];
  olderComparableNodes: AtlasNode[];
  staleNodes: AtlasNode[];
  tierAssets: HomeTierAsset[];
}): HomeTopicDetail[] {
  const groups = new Map<string, AtlasNode[]>();
  memoryNodes.forEach((node) => {
    const topic_label = compactThemeLabel(humanThemeLabel(node)) || "未归类主题";
    groups.set(topic_label, [...(groups.get(topic_label) ?? []), node]);
  });
  const topCount = Math.max(1, ...Array.from(groups.values()).map((nodes) => nodes.length));

  return Array.from(groups.entries())
    .map(([topic_label, nodes]) =>
      createTopicClassificationDetail(
        topic_label,
        nodes,
        topCount,
        actions,
        graphEdges,
        protoStarNodes,
        recentNodes,
        olderComparableNodes,
        staleNodes,
        tierAssets,
      ),
    )
    .sort((left, right) => topicClassificationSortScore(right) - topicClassificationSortScore(left))
    .slice(0, TOPIC_CLASSIFICATION_TOP_LIMIT);
}



export function createTopicClassificationDetail(
  topic_label: string,
  nodes: AtlasNode[],
  topCount: number,
  actions: HomeAction[],
  graphEdges: AtlasEdge[],
  protoStarNodes: AtlasNode[],
  recentNodes: AtlasNode[],
  olderComparableNodes: AtlasNode[],
  staleNodes: AtlasNode[],
  tierAssets: HomeTierAsset[],
): HomeTopicDetail {
  const topic_id = `topic:${topic_label}`;
  const representative = selectRepresentativeNode(nodes);
  const recent_count = nodes.filter((node) => recentNodes.some((recent) => recent.id === node.id)).length;
  const previous_count = nodes.filter((node) => olderComparableNodes.some((older) => older.id === node.id)).length;
  const stale_count = nodes.filter((node) => staleNodes.some((stale) => stale.id === node.id)).length;
  const proto_count = nodes.filter((node) => protoStarNodes.some((proto) => proto.id === node.id)).length;
  const topic_state = topicStateForTopic(topic_label, nodes.length, topCount, recent_count, previous_count, stale_count, proto_count);
  const trend = trendForTopic(recent_count, previous_count, proto_count, stale_count);
  const roi_score = averageNodeScore(nodes, (node) => roiScoreForNode(node, 0.45));
  const confidence = averageNodeScore(nodes, (node) => confidenceForAction(node, 0.58));
  const conflict_score = topic_state === "conflict" ? 0.72 : clampActionScore(stale_count / Math.max(1, nodes.length));
  const topic_strength = clampActionScore((nodes.length / topCount) * 0.5 + roi_score * 0.3 + recent_count / Math.max(1, nodes.length) * 0.2);
  const linked_action_ids = actions
    .filter((action) => action.linked_topic_ids.includes(topic_id) || action.reason.includes(topic_label))
    .map((action) => action.action_id);
  const linked_asset_ids = tierAssets
    .filter((asset) => asset.linked_topic_ids.includes(topic_id) || asset.theme === topic_label)
    .map((asset) => asset.asset_id);
  const evidence_refs = evidenceRefsForNode(representative, graphEdges, `topic-classification:${topic_label}`).concat(
    `record_count:${nodes.length}`,
    `recent_count:${recent_count}`,
  );

  return {
    category: topCategoryForNodes(nodes),
    confidence,
    conflict_score,
    evidence_refs,
    id: topic_id,
    linked_action_ids,
    linked_asset_ids,
    matched_reason: `${topic_label} has ${nodes.length.toLocaleString()} redacted records, ${recent_count.toLocaleString()} recent records, ROI ${formatScore(roi_score)} and state ${topic_state}.`,
    node: representative,
    nodes,
    parent_topic: parentTopicForTopic(topic_label),
    proposal_hint: topic_state === "dominant" && confidence >= 0.7 ? "proposal_not_needed" : "proposal_recommended",
    proposal_only: true,
    recent_count,
    record_count: nodes.length,
    representative_record_ids: nodes.slice(0, 5).map((node) => node.id),
    river_handoff: `memory_river:theme_lane:${topic_label}:recent_count:${recent_count}`,
    rollback_hint: "若主题判断不成立，只关闭面板或撤销后续 proposal 草稿；Phase 1.4 不写长期记忆。",
    roi_score,
    starfield_handoff: `memory_starfield:focus_topic:${topic_label}`,
    targetView: topic_state === "declining" || topic_state === "stale" || topic_state === "black_hole" ? "timeline" : "galaxy",
    topic_id,
    topic_label,
    topic_state,
    topic_strength,
    trend,
  };
}
