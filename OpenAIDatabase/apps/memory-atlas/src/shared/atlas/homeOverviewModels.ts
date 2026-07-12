import { Activity, Cloud, Download, FilterX, Save } from "lucide-react";
import { normalizeMemoryTier } from "../../data/atlas";
import type { AtlasEdge, AtlasNode, DataSourceSummary, MemoryAtlas } from "../../types";
import { HOME_ARRIVAL_CATEGORY_LABELS } from "./constants";
import { DeltaStats, HomeAction, HomeArrivalBriefingCard, HomeInspectorLink, HomeSignalCard, HomeTierAsset, HomeTopicDetail, MemoryWeatherV2, MiniStarfieldPoint, RiverPulseSegment } from "./contracts";
import { buildHomeInspectorLinks, buildMemoryWeatherV2, buildMiniStarfieldPreview, buildRiverPulsePreview, findDecliningTopicRows, homeWeatherFor, isBlackHoleCandidate, isProtoStarCandidate } from "./previewWeatherModels";
import { compactThemeLabel, countBy, humanCategoryLabel, humanNodeDisplayTitle, humanThemeLabel, recommendedActionForNode, selectRepresentativeNode, topRows } from "./semanticHuman";
import { buildTierAssetDetails, buildTopicClassificationDetails } from "./tierTopicModels";
import { buildNextActionDetails } from "./topicActionModels";
import { addDays, formatScore, formatSigned, isNodeBetween, maxNodeDate, parseDay } from "./utils";



export function buildHomeOverviewModel(
  nodes: AtlasNode[],
  graphEdges: AtlasEdge[],
  deltaStats: DeltaStats,
): {
  weatherLabel: string;
  weatherNote: string;
  weatherTone: HomeSignalCard["tone"];
  weatherV2: MemoryWeatherV2;
  topicRows: Array<{ label: string; count: number }>;
  tierRows: Array<{ label: string; count: number }>;
  categoryRows: Array<{ label: string; count: number }>;
  protoStarCount: number;
  blackHoleCount: number;
  signals: HomeSignalCard[];
  actions: HomeAction[];
  tierAssets: HomeTierAsset[];
  topicDetails: HomeTopicDetail[];
  miniStarfieldPoints: MiniStarfieldPoint[];
  miniStarfieldFocus: AtlasNode | null;
  miniStarfieldSummary: string;
  riverPulseSegments: RiverPulseSegment[];
  riverPulseFocus: AtlasNode | null;
  inspectorLinks: HomeInspectorLink[];
} {
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const topicRows = topRows(countBy(memoryNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "未归类主题"), 6);
  const tierRows = topRows(countBy(memoryNodes, (node) => normalizeMemoryTier(node.memory_tier)), 4);
  const categoryRows = topRows(countBy(memoryNodes, (node) => humanCategoryLabel(node.category)), 6);
  const latest = parseDay(deltaStats.latestDate) ?? maxNodeDate(memoryNodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const previousStart = addDays(latest, -89);
  const recentNodes = memoryNodes.filter((node) => isNodeBetween(node, recentStart, latest));
  const olderComparableNodes = memoryNodes.filter((node) => isNodeBetween(node, previousStart, addDays(recentStart, -1)));
  const staleNodes = memoryNodes.filter((node) => isBlackHoleCandidate(node));
  const protoStarNodes = memoryNodes.filter((node) => isProtoStarCandidate(node, recentStart, latest));
  const decliningRows = findDecliningTopicRows(recentNodes, olderComparableNodes);
  const weather = homeWeatherFor(deltaStats, staleNodes.length, protoStarNodes.length);
  const weatherV2 = buildMemoryWeatherV2(memoryNodes, deltaStats, staleNodes, protoStarNodes, topicRows, decliningRows);
  const topTopic = topicRows[0] ?? { label: "暂无主题", count: 0 };
  const risingTopic = topRows(countBy(recentNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || "近期主题"), 1)[0] ?? {
    label: "暂无近期增量",
    count: 0,
  };
  const decliningTopic = decliningRows[0] ?? { label: "暂无明显冷却", count: 0 };
  const blackHoleNode = selectRepresentativeNode(staleNodes);
  const protoStarNode = selectRepresentativeNode(protoStarNodes);
  const highLeverageNode = selectRepresentativeNode(memoryNodes);
  const decisionCount = memoryNodes.filter((node) => node.category === "decision").length;
  const coreCount = memoryNodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length;
  const miniStarfieldPoints = buildMiniStarfieldPreview(memoryNodes, graphEdges);
  const riverPulseSegments = buildRiverPulsePreview(recentNodes, olderComparableNodes);
  const riverPulseFocus = riverPulseSegments.find((segment) => segment.node)?.node ?? protoStarNode ?? highLeverageNode;
  const actions = buildNextActionDetails({
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
  });
  const tierAssets = buildTierAssetDetails({
    actions,
    graphEdges,
    latest,
    memoryNodes,
    protoStarNodes,
    staleNodes,
    topTopic,
  });

  return {
    weatherLabel: weather.label,
    weatherNote: weather.note,
    weatherTone: weather.tone,
    weatherV2,
    topicRows,
    tierRows,
    categoryRows,
    protoStarCount: protoStarNodes.length,
    blackHoleCount: staleNodes.length,
    signals: [
      {
        id: "weather",
        title: "认知天气",
        value: weather.label,
        note: weather.note,
        tone: weather.tone,
      },
      {
        id: "dominant",
        title: "主导主题",
        value: topTopic.label,
        note: `${topTopic.count.toLocaleString()} 条记忆集中在这个主题，可作为本轮复盘入口。`,
        tone: "dominant",
      },
      {
        id: "rising",
        title: "上升机会",
        value: risingTopic.label,
        note: `${risingTopic.count.toLocaleString()} 条近期记录；优先检查是否可以转成项目、技能或行动。`,
        tone: "rising",
      },
      {
        id: "declining",
        title: "冷却轨道",
        value: decliningTopic.label,
        note: decliningTopic.count
          ? `近 30 天降温 ${decliningTopic.count.toLocaleString()} 条；适合压缩、降权或补充新证据。`
          : "当前没有明显降温主题；继续观察低频但重要的长期资产。",
        tone: "declining",
      },
      {
        id: "black-hole",
        title: "Black Hole 风险",
        value: staleNodes.length.toLocaleString(),
        note: blackHoleNode
          ? `${humanNodeDisplayTitle(blackHoleNode)}：${recommendedActionForNode(blackHoleNode)}`
          : "未发现明显低价值循环；仍需保持 proposal-only 写回边界。",
        tone: "black-hole",
      },
      {
        id: "proto-star",
        title: "Proto-Star 机会",
        value: protoStarNodes.length.toLocaleString(),
        note: protoStarNode
          ? `${humanNodeDisplayTitle(protoStarNode)}：ROI ${formatScore(protoStarNode.metrics?.roi?.leverage_score)}`
          : "近期机会信号不足；先从主导主题中寻找可执行切口。",
        tone: "proto-star",
      },
    ],
    actions,
    tierAssets,
    topicDetails: buildTopicClassificationDetails({
      actions,
      graphEdges,
      memoryNodes,
      protoStarNodes,
      recentNodes,
      olderComparableNodes,
      staleNodes,
      tierAssets,
    }),
    miniStarfieldPoints,
    miniStarfieldFocus: miniStarfieldPoints[0]?.node ?? highLeverageNode,
    miniStarfieldSummary: `${miniStarfieldPoints.length.toLocaleString()} 个轻量静态星点，按 ROI、连接和层级压缩显示，不加载 WebGL。`,
    riverPulseSegments,
    riverPulseFocus,
    inspectorLinks: buildHomeInspectorLinks([protoStarNode, blackHoleNode, highLeverageNode], memoryNodes, graphEdges),
  };
}



export function buildHomeArrivalBriefing(
  atlas: MemoryAtlas,
  nodes: AtlasNode[],
  model: ReturnType<typeof buildHomeOverviewModel>,
  deltaStats: DeltaStats,
): HomeArrivalBriefingCard[] {
  const latest = parseDay(deltaStats.latestDate) ?? maxNodeDate(nodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const recentNodes = nodes
    .filter((node) => node.kind === "memory" && isNodeBetween(node, recentStart, latest))
    .sort((a, b) => (Date.parse(b.date ?? "") || 0) - (Date.parse(a.date ?? "") || 0));
  const newestImportantNode = recentNodes
    .slice()
    .sort((a, b) => (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0))
    .at(0) ?? recentNodes.at(0) ?? model.miniStarfieldFocus;
  const strengtheningSegment = model.riverPulseSegments.find((segment) => segment.delta > 0) ?? model.riverPulseSegments[0];
  const weakeningSegment = model.riverPulseSegments.find((segment) => segment.delta < 0);
  const recommendationCount = pendingProposalCandidateCount(atlas.agent_recommendations);
  const proposedActionCount = model.actions.filter((action) => action.status === "proposed" || action.status === "review").length;
  const pendingProposalCount = Math.max(recommendationCount, proposedActionCount);
  const failedSources = syncFailureSources(atlas);
  const latestSource = latestDataSource(atlas);
  const topAction = model.actions[0];

  return [
    {
      id: "new_material",
      label: HOME_ARRIVAL_CATEGORY_LABELS.new_material,
      value: `${deltaStats.recentCount.toLocaleString()} 条`,
      summary: newestImportantNode
        ? `最近新增或活跃的高价值线索是「${humanNodeDisplayTitle(newestImportantNode)}」。`
        : "当前筛选下没有新的高价值资料；先保持观察，不生成伪增量。",
      evidence: `近 30 天 ${deltaStats.recentCount.toLocaleString()} 条，上一窗口 ${deltaStats.previousCount.toLocaleString()} 条。`,
      nextStep: newestImportantNode ? "打开星图核对证据和关联主题" : "放宽筛选或等待下一次同步",
      targetView: "galaxy",
      node: newestImportantNode,
      icon: Download,
      tone: "new-material",
      machineSignal: `delta=${deltaStats.deltaCount}`,
    },
    {
      id: "strengthened",
      label: HOME_ARRIVAL_CATEGORY_LABELS.strengthened,
      value: strengtheningSegment ? strengtheningSegment.label : model.topicRows[0]?.label ?? "暂无",
      summary: strengtheningSegment
        ? `这个结论在近期窗口增强 ${formatSigned(strengtheningSegment.delta)} 条。`
        : "没有稳定增强信号；先看主导主题是否仍有决策价值。",
      evidence: strengtheningSegment
        ? `近期 ${strengtheningSegment.recentCount.toLocaleString()} 条，对比窗口 ${strengtheningSegment.previousCount.toLocaleString()} 条。`
        : `主导主题 ${model.topicRows[0]?.count ?? 0} 条。`,
      nextStep: "进入时间轴查看增强发生在哪些记录上",
      targetView: "timeline",
      node: strengtheningSegment?.node ?? model.riverPulseFocus,
      icon: Activity,
      tone: "strengthened",
      machineSignal: `strengthened_delta=${strengtheningSegment?.delta ?? 0}`,
    },
    {
      id: "weakened",
      label: HOME_ARRIVAL_CATEGORY_LABELS.weakened,
      value: model.blackHoleCount.toLocaleString(),
      summary: weakeningSegment
        ? `「${weakeningSegment.label}」近期减弱 ${formatSigned(weakeningSegment.delta)} 条，需要确认是过期还是沉淀完成。`
        : `${model.blackHoleCount.toLocaleString()} 条风险循环或过期候选需要保留在复盘视野里。`,
      evidence: weakeningSegment
        ? `近期 ${weakeningSegment.recentCount.toLocaleString()} 条，对比窗口 ${weakeningSegment.previousCount.toLocaleString()} 条。`
        : "根据时效和低价值循环信号综合判断。",
      nextStep: "先复核，不直接降权或删除",
      targetView: "summary",
      node: weakeningSegment?.node ?? topAction?.node ?? null,
      icon: FilterX,
      tone: "weakened",
      machineSignal: `black_holes=${model.blackHoleCount}`,
    },
    {
      id: "pending_proposal",
      label: HOME_ARRIVAL_CATEGORY_LABELS.pending_proposal,
      value: `${pendingProposalCount.toLocaleString()} 项`,
      summary: pendingProposalCount
        ? "有代理建议或下一步行动可转成提案候选，仍需人工授权。"
        : "当前没有待授权提案；系统继续保持仅生成提案，不直接应用。",
      evidence: `代理建议 ${recommendationCount.toLocaleString()} 项，行动建议 ${proposedActionCount.toLocaleString()} 项。`,
      nextStep: pendingProposalCount ? "进入决定下一步，逐项人工判断" : "保留仅生成提案的边界",
      targetView: "summary",
      node: topAction?.node ?? null,
      icon: Save,
      tone: "proposal",
      machineSignal: `pending_proposals=${pendingProposalCount}`,
    },
    {
      id: "sync_failure",
      label: HOME_ARRIVAL_CATEGORY_LABELS.sync_failure,
      value: `${failedSources.length.toLocaleString()} 个`,
      summary: failedSources.length
        ? `需要处理的数据源：${failedSources.map((source) => source.label).join("、")}。`
        : `当前未看到同步失败；最新活跃数据源是 ${latestSource?.label ?? "未知数据源"}。`,
      evidence: latestSource ? `最新数据源「${latestSource.label}」已纳入本次快照。` : "当前没有可用的数据源状态。",
      nextStep: failedSources.length ? "先修同步，再相信新增结论" : "继续用当前快照判断",
      targetView: "search",
      node: null,
      icon: Cloud,
      tone: "sync",
      machineSignal: `sync_failures=${failedSources.length}`,
    },
  ];
}



export function pendingProposalCandidateCount(recommendations: MemoryAtlas["agent_recommendations"]): number {
  if (!recommendations) return 0;
  return (
    recommendations.memory.added.length +
    recommendations.memory.modified.length +
    recommendations.meta_data.added.length +
    recommendations.meta_data.modified.length
  );
}



export function syncFailureSources(atlas: MemoryAtlas): DataSourceSummary[] {
  return (atlas.data_sources ?? []).filter((source) => {
    if (source.id === "all") return false;
    const status = `${source.status ?? ""} ${source.ingestion_status ?? ""}`.toLowerCase();
    return /fail|error|stale|blocked|missing|denied|timeout|失败|过期|阻塞/.test(status) || !/active|merged/.test(status);
  });
}



export function latestDataSource(atlas: MemoryAtlas): DataSourceSummary | null {
  return (atlas.data_sources ?? [])
    .filter((source) => source.id !== "all")
    .slice()
    .sort((a, b) => (b.latest_date || "").localeCompare(a.latest_date || ""))
    .at(0) ?? null;
}
