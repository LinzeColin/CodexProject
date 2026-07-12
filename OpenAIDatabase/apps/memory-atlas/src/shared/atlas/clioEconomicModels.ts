import type { AtlasFilters, AtlasNode } from "../../types";
import { type SharedAtlasState } from "../../state/sharedAtlasState";
import { CLIO_LIKE_VISUALS_VERSION, ECONOMIC_LIKE_VISUALS_VERSION } from "./constants";
import { ClioClusterDatum, ClioLikeVisualCopy, ClioLikeVisualModel, DeltaStats, EconomicLikeVisualCopy, EconomicLikeVisualModel, EconomicRadarAxis, EconomicTaskDatum } from "./contracts";
import { topEntry } from "./contributionModels";
import { isBlackHoleCandidate } from "./previewWeatherModels";
import { compactThemeLabel, countBy, humanCategoryLabel, humanThemeLabel, selectRepresentativeNode } from "./semanticHuman";
import { sourceDisplayLabel } from "./sourceSlice";
import { addDays, formatScore, isNodeBetween, maxNodeDate, parseDay } from "./utils";
import { clamp } from "../ui/visualStyles";



export function buildClioLikeVisualModel(
  nodes: AtlasNode[],
  filters: AtlasFilters,
  sharedState: SharedAtlasState,
  deltaStats: DeltaStats,
): ClioLikeVisualModel {
  const visualCopy: ClioLikeVisualCopy[] = [
    {
      id: "cluster_tree",
      title: "层级簇树",
      insightHeader: "主导主题先看树干，不从散点开始",
      humanQuestion: "我最近主要在关注哪些主题层级？",
      actionValue: "先定位主题重心，再决定进入搜索、星图还是后续 ROI 图谱。",
    },
    {
      id: "bubble_map",
      title: "气泡分布",
      insightHeader: "大气泡显示高频和高 ROI 的交汇点",
      humanQuestion: "高频、机会、风险如何分布？",
      actionValue: "优先打开高 ROI 且近期活跃的簇，低 ROI 高频簇进入降噪复盘。",
    },
    {
      id: "topic_cluster_explorer",
      title: "主题簇探索",
      insightHeader: "先打开证据最多的簇再行动",
      humanQuestion: "哪个主题簇最值得继续追问？",
      actionValue: "用代表记录进入搜索视图，复核证据后再生成下一步 proposal。",
    },
  ];
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const latest = parseDay(deltaStats.latestDate) ?? maxNodeDate(memoryNodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const clusterMap = new Map<string, AtlasNode[]>();

  for (const node of memoryNodes) {
    const key = node.visual?.cluster || node.category || "unclustered";
    const bucket = clusterMap.get(key) ?? [];
    bucket.push(node);
    clusterMap.set(key, bucket);
  }

  const palette = ["#7ee8d4", "#8fd3ff", "#f6c56f", "#f08fa3", "#b6a2ff", "#93df8f"];
  const clusters = Array.from(clusterMap.entries())
    .map(([id, clusterNodes], index): ClioClusterDatum => {
      const representative = selectRepresentativeNode(clusterNodes);
      const roiScore = average(clusterNodes.map((node) => normalizedNodeRoi(node)));
      const recentCount = clusterNodes.filter((node) => isNodeBetween(node, recentStart, latest)).length;
      const riskCount = clusterNodes.filter((node) => isBlackHoleCandidate(node)).length;
      const dominantCategory = topEntry(countBy(clusterNodes, (node) => humanCategoryLabel(node.category)))?.[0] ?? "未归类任务";
      const sourceCount = new Set(clusterNodes.map((node) => node.data_source ?? "memory_atlas")).size;
      const gridColumn = index % 3;
      const gridRow = Math.floor(index / 3);
      return {
        id,
        label: compactClioClusterLabel(id, representative),
        count: clusterNodes.length,
        recentCount,
        riskCount,
        roiScore,
        evidenceCount: Math.max(1, Math.round(clusterNodes.length + clusterNodes.reduce((total, node) => total + edgeCountHintForNode(node), 0))),
        dominantCategory,
        sourceCount,
        color: palette[index % palette.length],
        x: 94 + gridColumn * 146,
        y: 72 + gridRow * 82,
        radius: clamp(18 + clusterNodes.length * 1.8 + roiScore * 18, 22, 54),
        node: representative,
        nodes: clusterNodes,
      };
    })
    .sort((a, b) => b.count + b.roiScore * 4 - (a.count + a.roiScore * 4))
    .slice(0, 6)
    .map((cluster, index) => ({
      ...cluster,
      x: 94 + (index % 3) * 146,
      y: 72 + Math.floor(index / 3) * 82,
    }));

  const fallbackCluster: ClioClusterDatum = {
    id: "empty",
    label: "暂无筛选簇",
    count: 0,
    recentCount: 0,
    riskCount: 0,
    roiScore: 0,
    evidenceCount: 0,
    dominantCategory: "无",
    sourceCount: 0,
    color: "#8fd3ff",
    x: 220,
    y: 130,
    radius: 24,
    node: null,
    nodes: [],
  };
  const visibleClusters = clusters.length ? clusters : [fallbackCluster];
  const treeBranches = visibleClusters.slice(0, 5).map((cluster, index) => {
    const y = 48 + index * 42;
    return {
      id: cluster.id,
      label: cluster.label,
      count: cluster.count,
      x1: 174,
      y1: 130,
      x2: 228 + (index % 2) * 40,
      y2: y,
      node: cluster.node,
    };
  });

  const activeFilters = {
    source: filters.source === "all" ? "全部来源" : sourceDisplayLabel(filters.source, filters.source),
    time: sharedState.filters.timeRange?.label ?? "全部时间",
    project: filters.theme === "all" ? "全部项目/主题" : filters.theme,
    task: filters.category === "all" ? "全部任务类别" : humanCategoryLabel(filters.category),
  };
  const topCluster = visibleClusters[0];
  const summary = topCluster.count
    ? `当前筛选下，${topCluster.label} 是最大簇，包含 ${topCluster.count.toLocaleString()} 条记忆；图谱已按来源、时间、项目和任务过滤。`
    : "当前筛选下没有可视化簇；请放宽过滤条件后再查看。";

  return {
    schemaVersion: CLIO_LIKE_VISUALS_VERSION,
    activeFilters,
    visualCopy,
    clusters: visibleClusters,
    treeBranches,
    explorerRows: visibleClusters,
    summary,
  };
}



export function buildEconomicLikeVisualModel(
  nodes: AtlasNode[],
  filters: AtlasFilters,
  sharedState: SharedAtlasState,
  deltaStats: DeltaStats,
): EconomicLikeVisualModel {
  const visualCopy: EconomicLikeVisualCopy[] = [
    {
      id: "task_treemap",
      title: "任务占比分布",
      insightHeader: "任务面积显示 AI 使用最集中的地方",
      humanQuestion: "我的 AI 使用集中在哪些任务？",
      actionValue: "把最大面积任务先和 ROI 对齐，避免把时间继续投给低回报任务。",
    },
    {
      id: "automation_vs_augmentation",
      title: "自动化与辅助判断",
      insightHeader: "自动化和增强必须分开决策",
      humanQuestion: "哪些任务是 AI 自动化，哪些只是增强？",
      actionValue: "自动化高的任务优先固化流程；增强高的任务保留人工判断和复盘入口。",
    },
    {
      id: "roi_scatter",
      title: "投入回报分布",
      insightHeader: "右上角任务才值得继续加码",
      humanQuestion: "哪些任务最值得继续？",
      actionValue: "优先打开高 ROI 且近期活跃的任务；低 ROI 高频任务进入停止或降噪判断。",
    },
    {
      id: "opportunity_radar",
      title: "机会雷达",
      insightHeader: "机会不只看数量，还要看新鲜度和复用价值",
      humanQuestion: "哪些方向有机会但还需要证据？",
      actionValue: "用雷达缺口选择下一步验证问题，不把机会清单变成压力清单。",
    },
  ];
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const latest = parseDay(deltaStats.latestDate) ?? maxNodeDate(memoryNodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const taskMap = new Map<string, AtlasNode[]>();

  for (const node of memoryNodes) {
    const taskKey = economicTaskKey(node);
    const bucket = taskMap.get(taskKey) ?? [];
    bucket.push(node);
    taskMap.set(taskKey, bucket);
  }

  const palette = ["#7ee8d4", "#f6c56f", "#8fd3ff", "#f08fa3", "#93df8f", "#b6a2ff"];
  const rawRows = Array.from(taskMap.entries())
    .map(([id, taskNodes], index): EconomicTaskDatum => {
      const representative = selectRepresentativeNode(taskNodes);
      const roiScore = average(taskNodes.map((node) => normalizedNodeRoi(node)));
      const automationShare = average(taskNodes.map((node) => nodeAutomationLikelihood(node)));
      const augmentationShare = clamp(1 - automationShare * 0.72, 0.12, 1);
      const recentCount = taskNodes.filter((node) => isNodeBetween(node, recentStart, latest)).length;
      const opportunityScore = average(taskNodes.map((node) => economicOpportunityScore(node, recentStart, latest)));
      const riskScore = average(taskNodes.map((node) => (isBlackHoleCandidate(node) ? 1 : node.metrics?.roi?.staleness_status ? 0.62 : 0.22)));
      const sourceCount = new Set(taskNodes.map((node) => node.data_source ?? "memory_atlas")).size;
      return {
        id,
        label: economicTaskLabel(id, representative),
        count: taskNodes.length,
        roiScore,
        automationShare,
        augmentationShare,
        opportunityScore,
        riskScore,
        recentCount,
        sourceCount,
        color: palette[index % palette.length],
        x: 72 + clamp(recentCount / Math.max(1, taskNodes.length), 0, 1) * 315,
        y: 214 - roiScore * 160,
        radius: clamp(13 + Math.sqrt(taskNodes.length) * 4 + opportunityScore * 10, 18, 46),
        width: 1,
        height: 1,
        node: representative,
        nodes: taskNodes,
      };
    })
    .sort((a, b) => b.count + b.roiScore * 5 + b.opportunityScore * 4 - (a.count + a.roiScore * 5 + a.opportunityScore * 4))
    .slice(0, 6);

  const fallbackRow: EconomicTaskDatum = {
    id: "empty",
    label: "暂无筛选任务",
    count: 0,
    roiScore: 0,
    automationShare: 0,
    augmentationShare: 0,
    opportunityScore: 0,
    riskScore: 0,
    recentCount: 0,
    sourceCount: 0,
    color: "#8fd3ff",
    x: 220,
    y: 132,
    radius: 20,
    width: 1,
    height: 1,
    node: null,
    nodes: [],
  };
  const taskRows = (rawRows.length ? rawRows : [fallbackRow]).map((row, index, rows) => {
    const total = rows.reduce((sum, item) => sum + Math.max(1, item.count), 0);
    const share = Math.max(0.12, Math.max(1, row.count) / Math.max(1, total));
    const column = index % 3;
    const rowIndex = Math.floor(index / 3);
    return {
      ...row,
      width: clamp(118 + share * 250, 118, 250),
      height: clamp(54 + row.roiScore * 44 + share * 68, 64, 136),
      x: 72 + clamp(row.recentCount / Math.max(1, row.count), 0, 1) * 315,
      y: 214 - row.roiScore * 160,
      radius: clamp(row.radius, 18, 46),
      color: row.color || palette[(column + rowIndex) % palette.length],
    };
  });

  const automationAverage = average(taskRows.map((row) => row.automationShare));
  const augmentationAverage = average(taskRows.map((row) => row.augmentationShare));
  const radarAxes: EconomicRadarAxis[] = [
    { id: "roi", label: "ROI", value: average(taskRows.map((row) => row.roiScore)) },
    { id: "automation", label: "自动化", value: automationAverage },
    { id: "augmentation", label: "增强", value: augmentationAverage },
    { id: "opportunity", label: "机会", value: average(taskRows.map((row) => row.opportunityScore)) },
    { id: "freshness", label: "新鲜度", value: average(taskRows.map((row) => clamp(row.recentCount / Math.max(1, row.count), 0, 1))) },
    { id: "risk", label: "风险", value: average(taskRows.map((row) => row.riskScore)) },
  ];

  const activeFilters = {
    source: filters.source === "all" ? "全部来源" : sourceDisplayLabel(filters.source, filters.source),
    time: sharedState.filters.timeRange?.label ?? "全部时间",
    project: filters.theme === "all" ? "全部项目/主题" : filters.theme,
    task: filters.category === "all" ? "全部任务类别" : humanCategoryLabel(filters.category),
  };
  const topTask = taskRows[0];
  const summary = topTask.count
    ? `当前筛选下，${topTask.label} 是最大的投入任务面，平均 ROI ${formatScore(topTask.roiScore)}；图谱已按来源、时间、项目和任务过滤。`
    : "当前筛选下没有可计算的经济任务；请放宽过滤条件后再查看。";

  return {
    schemaVersion: ECONOMIC_LIKE_VISUALS_VERSION,
    activeFilters,
    visualCopy,
    taskRows,
    scatterPoints: taskRows,
    radarAxes,
    automationAverage,
    augmentationAverage,
    summary,
  };
}



export function average(values: number[]): number {
  const valid = values.filter((value) => Number.isFinite(value));
  if (!valid.length) return 0;
  return valid.reduce((total, value) => total + value, 0) / valid.length;
}



export function normalizedNodeRoi(node: AtlasNode): number {
  const leverage = node.metrics?.roi?.leverage_score;
  if (typeof leverage === "number") return clamp(leverage > 1 ? leverage / 100 : leverage, 0, 1);
  const weight = node.metrics?.weight_score;
  if (typeof weight === "number") return clamp(weight > 1 ? weight / 100 : weight, 0, 1);
  return 0.35;
}



export function edgeCountHintForNode(node: AtlasNode): number {
  const visualSize = node.visual?.size;
  if (typeof visualSize === "number") return Math.max(1, Math.round(visualSize));
  return node.memory_id ? 1 : 0;
}



export function compactClioClusterLabel(clusterId: string, representative: AtlasNode | null): string {
  const themeLabel = representative ? compactThemeLabel(humanThemeLabel(representative)) : "";
  if (themeLabel && themeLabel !== "未归类主题") return themeLabel;
  return clusterId
    .replace(/^cluster[-_:]/, "")
    .replace(/^theme[-_:]/, "")
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .slice(0, 22) || "未归类主题";
}



export function economicTaskKey(node: AtlasNode): string {
  if (node.category) return node.category;
  const label = `${node.label} ${node.statement ?? ""}`.toLowerCase();
  if (/sync|同步|archive|归档|backup|备份|automation|自动化|script|脚本/.test(label)) return "workflow_automation";
  if (/review|复盘|审核|验证|validator|gate|门禁/.test(label)) return "review_validation";
  if (/proposal|决策|decision|roadmap|计划|stage|phase/.test(label)) return "decision_planning";
  if (/visual|ui|图谱|可视化|dashboard/.test(label)) return "visualization";
  return "knowledge_work";
}



export function economicTaskLabel(taskId: string, representative: AtlasNode | null): string {
  const categoryLabel = humanCategoryLabel(taskId);
  if (categoryLabel && categoryLabel !== taskId) return categoryLabel;
  if (representative) return compactThemeLabel(humanThemeLabel(representative));
  return taskId.replace(/[-_]+/g, " ").replace(/\b\w/g, (char) => char.toUpperCase()).slice(0, 24) || "未归类任务";
}



export function nodeAutomationLikelihood(node: AtlasNode): number {
  const text = `${node.label} ${node.statement ?? ""} ${node.category ?? ""} ${node.metrics?.roi?.recommended_action ?? ""}`.toLowerCase();
  if (/自动化|automation|script|cron|scheduled|cli|validator|sync|同步|backup|备份|archive|归档|apply|pipeline/.test(text)) return 0.82;
  if (/codex|agent|tool|run|build|test|audit|门禁|验收/.test(text)) return 0.62;
  if (/review|复盘|判断|decision|决策|proposal|研究|写作|planning|计划/.test(text)) return 0.34;
  return 0.48;
}



export function economicOpportunityScore(node: AtlasNode, recentStart: Date, latest: Date): number {
  const roi = normalizedNodeRoi(node);
  const recentBoost = isNodeBetween(node, recentStart, latest) ? 0.18 : 0;
  const opportunityText = /机会|opportunity|继续|next|下一步|增长|复用|capability|能力/i.test(`${node.label} ${node.statement ?? ""} ${node.metrics?.roi?.recommended_action ?? ""}`)
    ? 0.18
    : 0;
  return clamp(roi * 0.64 + recentBoost + opportunityText, 0, 1);
}
