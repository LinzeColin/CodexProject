import { normalizeMemoryTier } from "../../data/atlas";
import type { AtlasEdge, AtlasNode } from "../../types";
import { DeltaStats, HomeInspectorLink, HomeSignalCard, MemoryWeatherV2, MiniStarfieldPoint, RiverPulseSegment } from "./contracts";
import { degreeMap, nodeColor } from "./contributionModels";
import { compactThemeLabel, countBy, humanCategoryLabel, humanNodeDisplayTitle, humanThemeLabel, normalizeDisplayKey, selectRepresentativeNode } from "./semanticHuman";
import { edgeCountFor, formatScore, formatSigned, isNodeBetween, stableUnit } from "./utils";
import { clamp } from "../ui/visualStyles";



export function evidenceRefsForNode(node: AtlasNode | null, graphEdges: AtlasEdge[], prefix: string): string[] {
  if (!node) return [`${prefix}:empty-node`];
  const refs = [
    `${prefix}:node:${node.id}`,
    `${prefix}:source:${node.source_label ?? node.data_source ?? "unknown"}`,
    `${prefix}:edge_count:${edgeCountFor(node.id, graphEdges)}`,
  ];
  if (node.memory_id) refs.push(`${prefix}:memory:${node.memory_id}`);
  return refs;
}



export function topicIdsForAction(node: AtlasNode | null, fallbackLabel: string): string[] {
  const label = node ? compactThemeLabel(humanThemeLabel(node)) : fallbackLabel;
  return label ? [`topic:${label}`] : [];
}



export function assetIdsForAction(node: AtlasNode | null): string[] {
  return node ? [node.id] : [];
}



export function buildMiniStarfieldPreview(nodes: AtlasNode[], graphEdges: AtlasEdge[]): MiniStarfieldPoint[] {
  const degree = degreeMap(graphEdges);
  return [...nodes]
    .sort((a, b) => homePreviewScore(b, degree) - homePreviewScore(a, degree) || (b.date ?? "").localeCompare(a.date ?? ""))
    .slice(0, 28)
    .map((node, index) => {
      const orbit = index % 4;
      const angle = stableUnit(node.id, "home-mini-star-angle") * Math.PI * 2;
      const radius = 20 + orbit * 32 + stableUnit(node.id, "home-mini-star-radius") * 28;
      const centerX = 210 + Math.cos(angle) * radius;
      const centerY = 95 + Math.sin(angle) * radius * 0.46;
      const score = homePreviewScore(node, degree);
      return {
        id: node.id,
        label: humanNodeDisplayTitle(node),
        x: Math.min(384, Math.max(36, centerX)),
        y: Math.min(158, Math.max(30, centerY)),
        radius: Math.min(9, 3.2 + Math.sqrt(Math.max(0, score)) * 0.42),
        color: nodeColor(node),
        node,
      };
    });
}



export function homePreviewScore(node: AtlasNode, degree: Map<string, number>): number {
  const tier = normalizeMemoryTier(node.memory_tier);
  const tierScore = tier === "核心画像" ? 14 : tier === "一般" ? 8 : 3;
  const categoryScore = ["decision", "project_context", "workflow", "preference", "answering_rule"].includes(node.category ?? "") ? 10 : 0;
  const roi = (node.metrics?.roi?.leverage_score ?? 0) * 16;
  const importance = node.importance === "高" ? 10 : node.importance === "中" ? 5 : 1;
  return tierScore + categoryScore + roi + importance + (degree.get(node.id) ?? 0) * 1.6;
}



export function buildRiverPulsePreview(recentNodes: AtlasNode[], previousNodes: AtlasNode[]): RiverPulseSegment[] {
  const recentCounts = countBy(recentNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "近期主题");
  const previousCounts = countBy(previousNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "历史主题");
  const labels = Array.from(new Set([...Object.keys(recentCounts), ...Object.keys(previousCounts)]));
  const rows = labels
    .map((label) => {
      const candidates = recentNodes.filter((node) => compactThemeLabel(humanThemeLabel(node)) === label);
      const fallback = previousNodes.filter((node) => compactThemeLabel(humanThemeLabel(node)) === label);
      const recentCount = recentCounts[label] ?? 0;
      const previousCount = previousCounts[label] ?? 0;
      return {
        id: normalizeDisplayKey(label) || label,
        label,
        recentCount,
        previousCount,
        delta: recentCount - previousCount,
        intensity: 0,
        node: selectRepresentativeNode(candidates.length ? candidates : fallback),
      };
    })
    .filter((row) => row.recentCount > 0 || row.previousCount > 0)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta) || b.recentCount - a.recentCount || a.label.localeCompare(b.label, "zh-CN"))
    .slice(0, 6);
  const maxDelta = Math.max(1, ...rows.map((row) => Math.abs(row.delta)));
  const displayRows = rows.length
    ? rows
    : [{
        id: "no-river-pulse",
        label: "暂无近期主题变化",
        recentCount: 0,
        previousCount: 0,
        delta: 0,
        intensity: 18,
        node: null,
      }];
  return displayRows.map((row) => ({
    ...row,
    intensity: row.intensity || Math.max(12, Math.round((Math.abs(row.delta) / maxDelta) * 100)),
  }));
}



export function buildHomeInspectorLinks(
  preferredNodes: Array<AtlasNode | null>,
  memoryNodes: AtlasNode[],
  graphEdges: AtlasEdge[],
): HomeInspectorLink[] {
  const degree = degreeMap(graphEdges);
  const rows = new Map<string, AtlasNode>();
  for (const node of preferredNodes) {
    if (node) rows.set(node.id, node);
  }
  for (const node of [...memoryNodes].sort((a, b) => homePreviewScore(b, degree) - homePreviewScore(a, degree))) {
    if (rows.size >= 4) break;
    rows.set(node.id, node);
  }
  if (!rows.size) {
    return [{
      id: "empty-inspector-link",
      title: "暂无可同步焦点",
      meta: "放宽筛选条件后可从首页直接打开详情。",
      node: null,
    }];
  }
  return Array.from(rows.values()).slice(0, 4).map((node) => ({
    id: node.id,
    title: humanNodeDisplayTitle(node),
    meta: `${normalizeMemoryTier(node.memory_tier)} / ${humanCategoryLabel(node.category)} / ${node.date || "未知日期"}`,
    node,
  }));
}



export function isBlackHoleCandidate(node: AtlasNode): boolean {
  const stale = node.metrics?.roi?.staleness_status ?? "";
  return (
    stale.includes("stale") ||
    stale === "needs_review" ||
    node.category === "deprecated_info" ||
    node.category === "temporary_or_sensitive" ||
    normalizeMemoryTier(node.memory_tier) === "临时"
  );
}



export function isProtoStarCandidate(node: AtlasNode, recentStart: Date, latest: Date): boolean {
  const leverage = node.metrics?.roi?.leverage_score ?? 0;
  const recent = isNodeBetween(node, recentStart, latest);
  return recent && (leverage >= 0.54 || node.category === "decision" || node.category === "project_context" || node.importance === "高");
}



export function findDecliningTopicRows(
  recentNodes: AtlasNode[],
  olderComparableNodes: AtlasNode[],
): Array<{ label: string; count: number }> {
  const recentCounts = countBy(recentNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "未归类主题");
  const olderCounts = countBy(olderComparableNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "未归类主题");
  return Object.entries(olderCounts)
    .map(([label, count]) => ({ label, count: Math.max(0, count - (recentCounts[label] ?? 0)) }))
    .filter((row) => row.count > 0)
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "zh-CN"))
    .slice(0, 4);
}



export function homeWeatherFor(
  deltaStats: DeltaStats,
  blackHoleCount: number,
  protoStarCount: number,
): { label: string; note: string; tone: HomeSignalCard["tone"] } {
  if (blackHoleCount > Math.max(12, protoStarCount * 2) && deltaStats.deltaCount < 0) {
    return {
      label: "风暴",
      note: "过时或临时信号偏多，且近期增量下降；先做压缩、降权和证据复核。",
      tone: "black-hole",
    };
  }
  if (protoStarCount >= 6 && deltaStats.deltaCount >= 0) {
    return {
      label: "新生云团",
      note: "近期机会和高杠杆记忆正在增加，适合转成项目、Skill 或下一步执行清单。",
      tone: "proto-star",
    };
  }
  if (deltaStats.deltaCount < 0) {
    return {
      label: "低温",
      note: "近期记忆增量低于上一周期，适合复盘停滞主题并清理不再有效的信息。",
      tone: "declining",
    };
  }
  return {
    label: "晴朗",
    note: "当前主题和增量相对稳定，可以从主导主题进入 ROI、时间线或 Summary 复核。",
    tone: "weather",
  };
}



export function buildMemoryWeatherV2(
  memoryNodes: AtlasNode[],
  deltaStats: DeltaStats,
  staleNodes: AtlasNode[],
  protoStarNodes: AtlasNode[],
  topicRows: Array<{ label: string; count: number }>,
  decliningRows: Array<{ label: string; count: number }>,
): MemoryWeatherV2 {
  const total = Math.max(1, memoryNodes.length);
  const dominantShare = (topicRows[0]?.count ?? 0) / total;
  const rawMomentum = deltaStats.deltaRate === null
    ? deltaStats.deltaCount / Math.max(12, deltaStats.recentCount + deltaStats.previousCount)
    : deltaStats.deltaRate;
  const momentumScore = clamp(0.5 + rawMomentum * 0.42, 0, 1);
  const riskScore = clamp(staleNodes.length / Math.max(12, total * 0.08), 0, 1);
  const opportunityScore = clamp(protoStarNodes.length / Math.max(6, total * 0.035), 0, 1);
  const volatilityPenalty = clamp(Math.abs(deltaStats.deltaCount) / Math.max(18, deltaStats.recentCount + deltaStats.previousCount), 0, 0.65);
  const stabilityScore = clamp(0.72 + dominantShare * 0.16 - riskScore * 0.28 - volatilityPenalty, 0, 1);
  const confidenceScore = clamp(Math.log10(total + 10) / 3 + (deltaStats.latestDate ? 0.1 : 0), 0, 1);
  let label = "平稳晴朗";
  let tone: HomeSignalCard["tone"] = "weather";
  if (riskScore >= 0.72 && opportunityScore >= 0.72) {
    label = "高能高压";
    tone = "rising";
  } else if (riskScore >= 0.72 && momentumScore < 0.48) {
    label = "高压整理";
    tone = "black-hole";
  } else if (opportunityScore >= 0.72 && momentumScore >= 0.5) {
    label = "机会上升";
    tone = "proto-star";
  } else if (momentumScore < 0.38) {
    label = "低温收缩";
    tone = "declining";
  } else if (stabilityScore >= 0.68 && riskScore < 0.55) {
    label = "稳态上升";
    tone = "rising";
  }
  const dominant = topicRows[0]?.label ?? "暂无主导主题";
  const cooling = decliningRows[0]?.label ?? "无明显冷却主题";
  return {
    label,
    tone,
    stabilityScore,
    momentumScore,
    riskScore,
    opportunityScore,
    confidenceScore,
    summary: `${dominant} 是主导气候；风险 ${formatScore(riskScore)}，机会 ${formatScore(opportunityScore)}，稳定性 ${formatScore(stabilityScore)}。`,
    signals: [
      `delta ${formatSigned(deltaStats.deltaCount)} / latest ${deltaStats.latestDate || "unknown"}`,
      `${protoStarNodes.length.toLocaleString()} proto-star vs ${staleNodes.length.toLocaleString()} black-hole`,
      `cooling: ${cooling}`,
    ],
  };
}



export function buildOpportunityItems(
  topicRows: Array<{ label: string; count: number }>,
  categoryRows: Array<{ label: string; count: number }>,
  deltaStats: DeltaStats,
): string[] {
  const items: string[] = [];
  const topicText = topicRows.map((row) => row.label).join(" / ");
  if (topicText.includes("记忆") || topicText.includes("RAG")) {
    items.push("把长期记忆库包装成所有 agent 的 RAG / personalization 入口，减少重复解释和上下文损耗。");
  }
  if (topicText.includes("Codex") || topicText.includes("agent") || topicText.includes("workflow")) {
    items.push("把高频 Codex 工作流产品化成可复用 Skill、Task Pack、验收脚本，提升每次开发 ROI。");
  }
  if (topicText.includes("金融") || topicText.includes("交易") || topicText.includes("概率")) {
    items.push("把金融、FIFA、概率决策沉淀为研究和风控仪表盘，优先服务 paper trading / 人审决策。");
  }
  if (topicText.includes("学习") || topicText.includes("Notion")) {
    items.push("把学习记录、Notion dashboard、周/月复盘打通，形成能力成长的可观察闭环。");
  }
  if (topicText.includes("工业") || topicText.includes("回转窑")) {
    items.push("工业服务方向可继续沉淀为测量、诊断、动态调整方案，适合形成行业化交付资产。");
  }
  if (categoryRows.some((row) => row.label.includes("项目上下文"))) {
    items.push("项目上下文占比较高，适合做项目索引和路线图，减少切换成本。");
  }
  if (deltaStats.recentDecisionCount > 0) {
    items.push("近期已有新决策，建议把对应行动项同步进下周执行清单。");
  }
  return items.slice(0, 4).length ? items.slice(0, 4) : ["先从最高密度主题做一次人工复盘，找出可产品化、可自动化、可投资研究的方向。"];
}
