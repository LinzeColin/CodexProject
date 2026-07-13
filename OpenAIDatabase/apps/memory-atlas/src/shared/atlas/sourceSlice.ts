import { normalizeMemoryTier, visibleGraphFor } from "../../data/atlas";
import type { ActivityBucket, AtlasFilters, AtlasMetric, AtlasNode, MemoryAtlas } from "../../types";
import { DeltaStats, FilteredAtlasSlice, HumanOverview, SourceOption } from "./contracts";
import { aggregateFilteredNodes, blankBucket, filteredMetricValues, levelFromScore, topEntry } from "./contributionModels";
import { buildOpportunityItems } from "./previewWeatherModels";
import { countBy, dedupeDisplayItems, humanCategoryLabel, humanNodeDisplayTitle, humanThemeLabel, recommendedActionForNode, topRows } from "./semanticHuman";
import { addDays, calendarWeekKey, dayOfYearIndex, formatSigned, isNodeBetween, maxNodeDate, mondayWeekdayIndex, parseDay, toDayKey } from "./utils";

export function selectableLensNodes(slice: FilteredAtlasSlice, selectedNode: AtlasNode | null): AtlasNode[] {
  if (selectedNode && slice.memoryNodes.some((node) => node.id === selectedNode.id)) return slice.memoryNodes;
  if (slice.memoryNodes.length && !selectedNode) return slice.memoryNodes;
  return slice.graphNodes;
}



export function buildFilteredSlice(atlas: MemoryAtlas, filteredMemoryNodes: AtlasNode[], filters: AtlasFilters): FilteredAtlasSlice {
  const visibleGraph = visibleGraphFor(atlas, filteredMemoryNodes);
  const visibleNodeIds = new Set(visibleGraph.nodes.map((node) => node.id));
  const memoryIds = new Set(filteredMemoryNodes.map((node) => node.memory_id).filter(Boolean));
  const timeline = atlas.timeline.filter((event) => visibleNodeIds.has(event.node_id) || memoryIds.has(event.memory_id));
  return {
    memoryNodes: filteredMemoryNodes,
    graphNodes: visibleGraph.nodes,
    graphEdges: visibleGraph.edges,
    timeline,
    visibleNodeIds,
    deltaStats: buildDeltaStats(atlas, filteredMemoryNodes),
    filterActive:
      filters.query !== "" || filters.source !== "all" || filters.tier !== "all" || filters.category !== "all" || filters.theme !== "all",
  };
}



export function selectionStillVisible(node: AtlasNode, slice: FilteredAtlasSlice): boolean {
  if (!slice.visibleNodeIds.has(node.id)) return false;
  if (!slice.filterActive) return true;
  if (node.kind === "memory") {
    return slice.memoryNodes.some((memoryNode) => memoryNode.id === node.id);
  }
  return true;
}



export function buildSourceOptions(atlas: MemoryAtlas, memoryNodes: AtlasNode[]): SourceOption[] {
  if (atlas.data_sources?.length) {
    return atlas.data_sources
      .filter((source) => ["all", "memory_atlas", "codex"].includes(source.id))
      .map((source) => ({
        id: source.id,
        label: sourceDisplayLabel(source.id, source.label),
        description: source.description,
        node_count: source.node_count,
      }));
  }
  const counts = memoryNodes.reduce<Record<string, number>>((acc, node) => {
    const id = node.data_source ?? "memory_atlas";
    acc[id] = (acc[id] ?? 0) + 1;
    return acc;
  }, {});
  return [
    { id: "all", label: "总数据源", description: "所有数据来源放在一起", node_count: memoryNodes.length },
    ...Object.entries(counts)
      .filter(([id]) => ["memory_atlas", "codex"].includes(id))
      .map(([id, count]) => ({
        id,
        label: sourceDisplayLabel(id, id),
        description: "自动识别的数据源",
        node_count: count,
      })),
  ];
}



export function sourceDisplayLabel(sourceId: string, fallback: string): string {
  if (sourceId === "all") return "总数据源";
  if (sourceId === "memory_atlas") return "ChatGPT";
  if (sourceId === "codex") return "Codex";
  return fallback;
}



export function sourceMatchesNode(node: AtlasNode, sourceId: string): boolean {
  return sourceId === "all" || (node.data_source ?? "memory_atlas") === sourceId;
}



export function buildSourceScopedAtlas(atlas: MemoryAtlas, sourceMemoryNodes: AtlasNode[], sourceId: string): MemoryAtlas {
  if (sourceId === "all") return atlas;
  const graph = visibleGraphFor(atlas, sourceMemoryNodes);
  const visibleNodeIds = new Set(graph.nodes.map((node) => node.id));
  const memoryIds = new Set(sourceMemoryNodes.map((node) => node.memory_id).filter(Boolean));
  const timeline = atlas.timeline.filter((event) => visibleNodeIds.has(event.node_id) || memoryIds.has(event.memory_id));
  const sourceSummary = atlas.data_sources?.find((source) => source.id === sourceId);
  const contribution = buildSourceScopedContribution(atlas, sourceMemoryNodes, sourceId);
  return {
    ...atlas,
    overview: {
      ...atlas.overview,
      active_memory_count: sourceMemoryNodes.length,
      memory_node_count: sourceMemoryNodes.length,
      node_count: graph.nodes.length,
      edge_count: graph.edges.length,
      conversation_count: sourceSummary?.activity_count ?? contribution.daily.length,
    },
    nodes: graph.nodes,
    edges: graph.edges,
    timeline,
    contribution,
    metrics: buildSourceScopedMetrics(sourceMemoryNodes),
    agent_recommendations: sourceId === "codex" ? atlas.agent_recommendations : undefined,
  };
}



export function buildSourceScopedContribution(atlas: MemoryAtlas, sourceMemoryNodes: AtlasNode[], sourceId: string): MemoryAtlas["contribution"] {
  const nodeDaily = aggregateFilteredNodes(sourceMemoryNodes, "day");
  const dailyByDate = new Map<string, ActivityBucket>();

  if (sourceId === "codex") {
    for (const row of atlas.contribution.daily) {
      if ((row.codex_session_count ?? 0) <= 0 && (row.tool_call_count ?? 0) <= 0) continue;
      dailyByDate.set(row.date, normalizeActivityBucket(row));
    }
  }

  for (const [dateKey, nodeBucket] of nodeDaily) {
    const target = dailyByDate.get(dateKey) ?? blankBucket(dateKey);
    target.memory_count = nodeBucket.memory_count;
    target.decision_count = nodeBucket.decision_count;
    target.core_memory_count = nodeBucket.core_memory_count;
    target.mid_long_memory_count = nodeBucket.mid_long_memory_count;
    target.short_memory_count = nodeBucket.short_memory_count;
    target.activity_score = Math.max(target.activity_score, nodeBucket.activity_score);
    target.activity_level = levelFromScore(target.activity_score);
    dailyByDate.set(dateKey, target);
  }

  const daily = Array.from(dailyByDate.values()).sort((a, b) => a.date.localeCompare(b.date));
  const maxActivity = Math.max(0, ...daily.map((row) => row.activity_score));
  return {
    ...atlas.contribution,
    range_start: daily[0]?.date ?? "",
    range_end: daily[daily.length - 1]?.date ?? "",
    max_activity_score: maxActivity,
    quantiles: {},
    daily,
    weekly: aggregateActivityBuckets(daily, "week"),
    monthly: aggregateActivityBuckets(daily, "month"),
    yearly: aggregateActivityBuckets(daily, "year"),
  };
}



export function normalizeActivityBucket(row: ActivityBucket): ActivityBucket {
  return {
    ...blankBucket(row.date),
    ...row,
    tool_call_count: row.tool_call_count ?? 0,
    error_event_count: row.error_event_count ?? 0,
    abort_count: row.abort_count ?? 0,
    codex_session_count: row.codex_session_count ?? 0,
  };
}



export function aggregateActivityBuckets(rows: ActivityBucket[], period: "week" | "month" | "year"): ActivityBucket[] {
  const buckets = new Map<string, ActivityBucket>();
  for (const row of rows) {
    const periodKey = activityPeriodKey(row.date, period);
    if (!periodKey) continue;
    const target = buckets.get(periodKey) ?? blankBucket(periodKey);
    for (const key of activityBucketNumericKeys) {
      target[key] = (target[key] ?? 0) + (row[key] ?? 0);
    }
    target.activity_level = levelFromScore(target.activity_score);
    buckets.set(periodKey, target);
  }
  return Array.from(buckets.values()).sort((a, b) => a.date.localeCompare(b.date));
}



export function activityPeriodKey(dateKey: string, period: "week" | "month" | "year"): string {
  const day = parseDay(dateKey);
  if (!day) return "";
  if (period === "month") return `${day.getUTCFullYear()}-${String(day.getUTCMonth() + 1).padStart(2, "0")}`;
  if (period === "year") return String(day.getUTCFullYear());
  const startWeekday = mondayWeekdayIndex(new Date(Date.UTC(day.getUTCFullYear(), 0, 1)));
  return calendarWeekKey(day.getUTCFullYear(), Math.floor((dayOfYearIndex(day) + startWeekday) / 7));
}



export const activityBucketNumericKeys = [
  "conversation_count",
  "message_count",
  "user_message_count",
  "assistant_message_count",
  "memory_count",
  "candidate_count",
  "decision_count",
  "core_memory_count",
  "mid_long_memory_count",
  "short_memory_count",
  "tool_call_count",
  "error_event_count",
  "abort_count",
  "codex_session_count",
  "activity_score",
] as const;



export function buildSourceScopedMetrics(nodes: AtlasNode[]): AtlasMetric[] {
  return [
    { kind: "tier", values: filteredMetricValues(nodes, "memory_tier") },
    { kind: "category", values: filteredMetricValues(nodes, "category") },
  ];
}



export function buildDeltaStats(atlas: MemoryAtlas, nodes: AtlasNode[]): DeltaStats {
  const latest = parseDay(atlas.contribution.range_end) ?? maxNodeDate(nodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const previousStart = addDays(latest, -59);
  const previousEnd = addDays(latest, -30);
  const recentNodes = nodes.filter((node) => isNodeBetween(node, recentStart, latest));
  const previousNodes = nodes.filter((node) => isNodeBetween(node, previousStart, previousEnd));
  const categoryCounts = filteredMetricValues(nodes, "category");
  const topCategory = topEntry(categoryCounts)?.[0] ?? "暂无";
  const deltaCount = recentNodes.length - previousNodes.length;
  return {
    totalFiltered: nodes.length,
    totalMemory: atlas.overview.active_memory_count,
    recentCount: recentNodes.length,
    previousCount: previousNodes.length,
    deltaCount,
    deltaRate: previousNodes.length ? deltaCount / previousNodes.length : null,
    recentDecisionCount: recentNodes.filter((node) => node.category === "decision").length,
    recentCoreCount: recentNodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length,
    topCategory,
    latestDate: toDayKey(latest),
  };
}



export function buildHumanOverview(nodes: AtlasNode[], deltaStats: DeltaStats): HumanOverview {
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const topicRows = topRows(countBy(memoryNodes, (node) => humanThemeLabel(node)), 6);
  const tierRows = topRows(countBy(memoryNodes, (node) => normalizeMemoryTier(node.memory_tier)), 4);
  const categoryRows = topRows(countBy(memoryNodes, (node) => humanCategoryLabel(node.category)), 6);
  const topTopic = topicRows[0]?.label ?? "当前筛选主题";
  const highLeverage = [...memoryNodes]
    .sort((a, b) => (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0))
    .slice(0, 4);
  const staleShortCount = memoryNodes.filter(
    (node) => normalizeMemoryTier(node.memory_tier) === "临时" || node.metrics?.roi?.staleness_status === "stale_short_term",
  ).length;
  const coreCount = memoryNodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length;
  const decisionCount = memoryNodes.filter((node) => node.category === "decision").length;
  const securityCount = memoryNodes.filter((node) => node.category === "security_boundary").length;

  const rememberItems = highLeverage.length
    ? dedupeDisplayItems(highLeverage.map((node) => `${humanNodeDisplayTitle(node)}：${recommendedActionForNode(node)}`), 4)
    : ["暂无高杠杆记忆；先选择主题或层级后查看更具体的事项。"];

  return {
    topicRows,
    tierRows,
    categoryRows,
    actionItems: [
      `优先复核「${topTopic}」：这是当前记忆密度最高的主题，适合先转成下一步任务清单。`,
      `把 ${coreCount.toLocaleString()} 条核心画像沉淀成可复制的 personalization / agent 启动上下文。`,
      staleShortCount
        ? `清理但不删除 ${staleShortCount.toLocaleString()} 条临时信息：压缩成低权重背景，避免干扰长期判断。`
        : "当前短期噪音较低，下一步可以集中补齐项目索引和决策日志。",
    ],
    rememberItems,
    opportunityItems: buildOpportunityItems(topicRows, categoryRows, deltaStats),
    riskItems: [
      securityCount
        ? `${securityCount.toLocaleString()} 条安全边界需要持续遵守；涉及交易、secret、外部部署时不能跳过确认。`
        : "当前筛选没有明显安全边界，但外部写入和账户操作仍需人工确认。",
      decisionCount
        ? `${decisionCount.toLocaleString()} 条决策应进入后续默认上下文，避免重复讨论。`
        : "当前筛选决策较少，后续应把重要选择明确写入决策日志。",
      `近 30 天较前 30 天 ${formatSigned(deltaStats.deltaCount)} 条，增量变化需要和实际任务成果一起复盘。`,
    ],
  };
}
