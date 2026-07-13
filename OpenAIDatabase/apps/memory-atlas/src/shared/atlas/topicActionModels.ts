import { normalizeMemoryTier } from "../../data/atlas";
import type { AtlasEdge, AtlasNode } from "../../types";
import { DeltaStats, HomeAction, HomeActionDetail, TopicClassificationDetail } from "./contracts";
import { assetIdsForAction, evidenceRefsForNode, topicIdsForAction } from "./previewWeatherModels";
import { NEXT_ACTION_SORT_WEIGHTS, NEXT_ACTION_TOP_LIMIT, TOPIC_CLASSIFICATION_SORT_WEIGHTS, TOPIC_CLASSIFICATION_STATES } from "./runtimeConfig";
import { countBy, humanCategoryLabel, humanNodeDisplayTitle, topRows } from "./semanticHuman";
import { edgeCountFor, formatScore, formatSigned } from "./utils";



export function topicClassificationSortScore(topic: TopicClassificationDetail): number {
  return (
    topic.topic_strength * TOPIC_CLASSIFICATION_SORT_WEIGHTS.strength_weight +
    trendScore(topic.trend) * TOPIC_CLASSIFICATION_SORT_WEIGHTS.trend_weight +
    topic.confidence * TOPIC_CLASSIFICATION_SORT_WEIGHTS.confidence_weight -
    topic.conflict_score * TOPIC_CLASSIFICATION_SORT_WEIGHTS.conflict_penalty_weight
  );
}



export function topicStateForTopic(
  topicLabel: string,
  recordCount: number,
  topCount: number,
  recentCount: number,
  previousCount: number,
  staleCount: number,
  protoCount: number,
): TopicClassificationDetail["topic_state"] {
  const lower = topicLabel.toLowerCase();
  if (lower.includes("conflict") || lower.includes("冲突")) return "conflict";
  if (staleCount >= Math.max(2, recordCount * 0.5)) return "black_hole";
  if (recordCount === topCount) return "dominant";
  if (recentCount > previousCount + 1) return "rising";
  if (protoCount > 0 || (recordCount <= 2 && recentCount > 0)) return "emerging";
  if (previousCount > recentCount + 1) return "declining";
  if (staleCount > 0) return "stale";
  return TOPIC_CLASSIFICATION_STATES.includes("dominant") ? "dominant" : "emerging";
}



export function trendForTopic(
  recentCount: number,
  previousCount: number,
  protoCount: number,
  staleCount: number,
): TopicClassificationDetail["trend"] {
  if (recentCount > previousCount + 1 || protoCount > 0) return "up";
  if (previousCount > recentCount + 1 || staleCount > recentCount) return "down";
  return "stable";
}



export function trendScore(trend: TopicClassificationDetail["trend"]): number {
  if (trend === "up") return 1;
  if (trend === "stable") return 0.62;
  return 0.35;
}



export function topCategoryForNodes(nodes: AtlasNode[]): string {
  return topRows(countBy(nodes, (node) => humanCategoryLabel(node.category)), 1)[0]?.label ?? "未分类";
}



export function parentTopicForTopic(topicLabel: string): string {
  const lower = topicLabel.toLowerCase();
  if (lower.includes("memory") || topicLabel.includes("记忆")) return "Memory Atlas";
  if (lower.includes("codex") || lower.includes("workflow") || topicLabel.includes("工作流")) return "Delivery System";
  if (lower.includes("visual") || topicLabel.includes("可视化")) return "Visual System";
  return "General";
}



export function averageNodeScore(nodes: AtlasNode[], score: (node: AtlasNode) => number): number {
  if (!nodes.length) return 0;
  return clampActionScore(nodes.reduce((sum, node) => sum + score(node), 0) / nodes.length);
}



export function buildNextActionDetails({
  blackHoleNode,
  coreCount,
  decisionCount,
  deltaStats,
  graphEdges,
  highLeverageNode,
  memoryNodes,
  protoStarNode,
  protoStarNodes,
  recentNodes,
  staleNodes,
  topTopic,
}: {
  blackHoleNode: AtlasNode | null;
  coreCount: number;
  decisionCount: number;
  deltaStats: DeltaStats;
  graphEdges: AtlasEdge[];
  highLeverageNode: AtlasNode | null;
  memoryNodes: AtlasNode[];
  protoStarNode: AtlasNode | null;
  protoStarNodes: AtlasNode[];
  recentNodes: AtlasNode[];
  staleNodes: AtlasNode[];
  topTopic: { label: string; count: number };
}): HomeAction[] {
  const topNodeEvidence = evidenceRefsForNode(highLeverageNode, graphEdges, "highest-leverage");
  const coreDecisionEvidence = [
    `core_memory_count:${coreCount}`,
    `decision_count:${decisionCount}`,
    `dominant_topic:${topTopic.label}`,
  ];
  const staleEvidence = evidenceRefsForNode(blackHoleNode, graphEdges, "black-hole").concat(
    `stale_candidate_count:${staleNodes.length}`,
  );
  const riverEvidence = evidenceRefsForNode(protoStarNode ?? highLeverageNode, graphEdges, "time-river").concat(
    `recent_count:${deltaStats.recentCount}`,
    `delta_count:${deltaStats.deltaCount}`,
  );
  const protoEvidence = evidenceRefsForNode(protoStarNode, graphEdges, "proto-star").concat(
    `proto_star_count:${protoStarNodes.length}`,
    `recent_memory_count:${recentNodes.length}`,
  );

  const candidates: HomeAction[] = [
    {
      action_id: "inspect-roi",
      action_type: "continue",
      confidence: confidenceForAction(highLeverageNode, 0.78),
      effort_cost: "low",
      evidence_count: topNodeEvidence.length,
      evidence_refs: topNodeEvidence,
      id: "inspect-roi",
      linked_asset_ids: assetIdsForAction(highLeverageNode),
      linked_topic_ids: topicIdsForAction(highLeverageNode, topTopic.label),
      matched_reason: highLeverageNode
        ? `${humanNodeDisplayTitle(highLeverageNode)} 同时具备较高 ROI 与 ${edgeCountFor(highLeverageNode.id, graphEdges).toLocaleString()} 个连接。`
        : "当前筛选下缺少可直接执行的高杠杆记忆，需要先放宽筛选条件。",
      next_step: "打开 ROI Dashboard，核对该记忆是否应进入本轮复盘或 proposal 调整。",
      node: highLeverageNode,
      priority: "P1",
      proposal_hint: "proposal_recommended",
      proposal_only: true,
      reason: highLeverageNode
        ? `${humanNodeDisplayTitle(highLeverageNode)} · ${edgeCountFor(highLeverageNode.id, graphEdges).toLocaleString()} 个连接`
        : "当前筛选下暂无可选记忆，先放宽筛选条件。",
      recommended_time_window: highLeverageNode ? "now" : "later",
      rollback_hint: "若判断不成立，仅关闭 Drawer 或撤销 proposal 草稿；本阶段不会写入长期记忆。",
      roi_score: roiScoreForNode(highLeverageNode, 0.62),
      source: "home_overview.high_leverage",
      status: highLeverageNode ? "proposed" : "review",
      targetView: "roi",
      title: "查看最高杠杆记忆",
      urgency: highLeverageNode ? "high" : "low",
    },
    {
      action_id: "review-core",
      action_type: "review",
      confidence: clampActionScore(coreCount || decisionCount ? 0.82 : 0.54),
      effort_cost: "medium",
      evidence_count: coreDecisionEvidence.length,
      evidence_refs: coreDecisionEvidence,
      id: "review-core",
      linked_asset_ids: memoryNodes
        .filter((node) => node.category === "decision" || normalizeMemoryTier(node.memory_tier) === "核心画像")
        .slice(0, 5)
        .map((node) => node.id),
      linked_topic_ids: [`topic:${topTopic.label}`],
      matched_reason: `${coreCount.toLocaleString()} 条核心画像与 ${decisionCount.toLocaleString()} 条决策是 Summary & Iteration 的主要复核输入。`,
      next_step: "进入 Summary & Iteration，检查核心画像、规则与决策是否仍然支持当前目标。",
      node: null,
      priority: coreCount + decisionCount ? "P1" : "P2",
      proposal_hint: "proposal_recommended",
      proposal_only: true,
      reason: `${coreCount.toLocaleString()} 条核心画像、${decisionCount.toLocaleString()} 条决策适合进入 Summary & Iteration 复核。`,
      recommended_time_window: "today",
      rollback_hint: "如果复核没有发现变更，保留只读结论，不生成 proposal。",
      roi_score: clampActionScore(0.58 + Math.min(0.28, (coreCount + decisionCount) / 80)),
      source: "home_overview.core_decision_counts",
      status: "review",
      targetView: "summary",
      title: "同步核心画像与规则",
      urgency: coreCount + decisionCount ? "medium" : "low",
    },
    {
      action_id: "compress-black-hole",
      action_type: staleNodes.length ? "consolidate" : "defer",
      confidence: confidenceForAction(blackHoleNode, staleNodes.length ? 0.76 : 0.5),
      effort_cost: staleNodes.length > 12 ? "high" : "medium",
      evidence_count: staleEvidence.length,
      evidence_refs: staleEvidence,
      id: "compress-black-hole",
      linked_asset_ids: assetIdsForAction(blackHoleNode).concat(staleNodes.slice(0, 4).map((node) => node.id)),
      linked_topic_ids: topicIdsForAction(blackHoleNode, "Black Hole"),
      matched_reason: staleNodes.length
        ? `${staleNodes.length.toLocaleString()} 条历史、临时或过时信号被标记为 Black Hole 候选。`
        : "当前没有明显 Black Hole 候选，保留为定期低价值循环检查。",
      next_step: staleNodes.length
        ? "打开 Search Review，检查是否需要降权、隐藏到期窗口或补充新证据。"
        : "本轮跳过压缩动作，只在复盘中保留低价值循环观察项。",
      node: blackHoleNode,
      priority: staleNodes.length ? "P2" : "P3",
      proposal_hint: staleNodes.length ? "proposal_recommended" : "proposal_not_needed",
      proposal_only: true,
      reason: staleNodes.length
        ? `${staleNodes.length.toLocaleString()} 条历史、临时或过时信号需要降权或补证。`
        : "当前没有明显 Black Hole；保留这一步作为定期检查。",
      recommended_time_window: staleNodes.length ? "this_week" : "later",
      rollback_hint: "任何降权、隐藏或 stale override 都只能生成 proposal JSON，不直接修改长期记忆。",
      roi_score: staleNodes.length ? clampActionScore(0.52 + Math.min(0.3, staleNodes.length / 60)) : 0.28,
      source: "home_overview.black_hole_candidates",
      status: staleNodes.length ? "proposed" : "review",
      targetView: "search",
      title: "压缩低价值循环",
      urgency: staleNodes.length > 8 ? "high" : staleNodes.length ? "medium" : "low",
    },
    {
      action_id: "read-time-river",
      action_type: "review",
      confidence: clampActionScore(deltaStats.recentCount ? 0.74 : 0.5),
      effort_cost: "medium",
      evidence_count: riverEvidence.length,
      evidence_refs: riverEvidence,
      id: "read-time-river",
      linked_asset_ids: assetIdsForAction(protoStarNode ?? highLeverageNode),
      linked_topic_ids: topicIdsForAction(protoStarNode ?? highLeverageNode, topTopic.label),
      matched_reason: `近 30 天 ${deltaStats.recentCount.toLocaleString()} 条，较前 30 天 ${formatSigned(deltaStats.deltaCount)} 条，需要从时间河核对趋势形成过程。`,
      next_step: "进入记忆时间河，查看增强主题、决策节点和异常脉冲是否能解释本期变化。",
      node: protoStarNode ?? highLeverageNode,
      priority: deltaStats.deltaCount >= 0 ? "P2" : "P1",
      proposal_hint: "proposal_not_needed",
      proposal_only: true,
      reason: `近 30 天 ${deltaStats.recentCount.toLocaleString()} 条，较前 30 天 ${formatSigned(deltaStats.deltaCount)} 条。`,
      recommended_time_window: deltaStats.deltaCount < 0 ? "today" : "this_week",
      rollback_hint: "时间河只读复盘不产生写回；若发现排序问题，后续走 proposal-only 调整层。",
      roi_score: deltaStats.deltaCount < 0 ? 0.72 : 0.58,
      source: "home_overview.delta_stats",
      status: "review",
      targetView: "timeline",
      title: "按时间复盘增量",
      urgency: deltaStats.deltaCount < 0 ? "high" : "medium",
    },
    {
      action_id: "validate-proto-star",
      action_type: "explore",
      confidence: confidenceForAction(protoStarNode, protoStarNodes.length ? 0.7 : 0.46),
      effort_cost: "low",
      evidence_count: protoEvidence.length,
      evidence_refs: protoEvidence,
      id: "validate-proto-star",
      linked_asset_ids: assetIdsForAction(protoStarNode).concat(protoStarNodes.slice(0, 4).map((node) => node.id)),
      linked_topic_ids: topicIdsForAction(protoStarNode, topTopic.label),
      matched_reason: protoStarNodes.length
        ? `${protoStarNodes.length.toLocaleString()} 个近期机会信号可作为新项目、技能或行动候选。`
        : "近期机会信号不足，先从主导主题中寻找可执行切口。",
      next_step: protoStarNode
        ? "打开记忆星系，查看该 proto-star 周围的主题引力源和相邻证据。"
        : "保留机会观察项，下一轮先补充近期高置信证据。",
      node: protoStarNode,
      priority: protoStarNodes.length ? "P2" : "P3",
      proposal_hint: protoStarNodes.length ? "proposal_recommended" : "proposal_not_needed",
      proposal_only: true,
      reason: protoStarNode
        ? `${humanNodeDisplayTitle(protoStarNode)}：ROI ${formatScore(protoStarNode.metrics?.roi?.leverage_score)}`
        : "近期机会信号不足；先从主导主题中寻找可执行切口。",
      recommended_time_window: protoStarNodes.length ? "today" : "later",
      rollback_hint: "机会判断只影响本地展示和 proposal 草稿，不会在 Phase 1.2 写回数据库。",
      roi_score: protoStarNodes.length ? roiScoreForNode(protoStarNode, 0.66) : 0.34,
      source: "home_overview.proto_star_candidates",
      status: protoStarNodes.length ? "proposed" : "review",
      targetView: "galaxy",
      title: "验证新生机会",
      urgency: protoStarNodes.length > 4 ? "high" : protoStarNodes.length ? "medium" : "low",
    },
  ];

  return candidates
    .sort((left, right) => nextActionSortScore(right) - nextActionSortScore(left))
    .slice(0, NEXT_ACTION_TOP_LIMIT);
}



export function nextActionSortScore(action: HomeActionDetail): number {
  return (
    action.roi_score * NEXT_ACTION_SORT_WEIGHTS.roi_weight +
    urgencyScore(action.urgency) * NEXT_ACTION_SORT_WEIGHTS.urgency_weight +
    action.confidence * NEXT_ACTION_SORT_WEIGHTS.confidence_weight -
    effortPenalty(action.effort_cost) * NEXT_ACTION_SORT_WEIGHTS.effort_penalty_weight
  );
}



export function urgencyScore(urgency: HomeActionDetail["urgency"]): number {
  if (urgency === "high") return 1;
  if (urgency === "medium") return 0.66;
  return 0.33;
}



export function effortPenalty(effortCost: HomeActionDetail["effort_cost"]): number {
  if (effortCost === "high") return 0.82;
  if (effortCost === "medium") return 0.45;
  return 0.15;
}



export function roiScoreForNode(node: AtlasNode | null, fallback: number): number {
  return clampActionScore(node?.metrics?.roi?.leverage_score ?? node?.metrics?.weight_score ?? fallback);
}



export function confidenceForAction(node: AtlasNode | null, fallback: number): number {
  const parsed = Number(node?.confidence);
  if (Number.isFinite(parsed)) return clampActionScore(parsed);
  return clampActionScore(fallback);
}



export function clampActionScore(value: number): number {
  return Math.max(0, Math.min(1, value));
}
