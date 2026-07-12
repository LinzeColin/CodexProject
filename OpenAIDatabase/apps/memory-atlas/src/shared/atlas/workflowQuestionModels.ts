import type { AtlasEdge, AtlasFilters, AtlasNode, ViewKey } from "../../types";
import { type SharedAtlasState } from "../../state/sharedAtlasState";
import { average, edgeCountHintForNode, normalizedNodeRoi } from "./clioEconomicModels";
import { HUMAN_QUESTION_MAP_VERSION, WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION } from "./constants";
import { ClioLikeVisualCopy, ClioLikeVisualId, ClioLikeVisualModel, DeltaStats, EconomicLikeVisualCopy, EconomicLikeVisualId, EconomicLikeVisualModel, EvidenceTimelineDatum, FormulaInspectorDatum, HumanQuestionMapEntry, HumanQuestionMapExcludedCandidate, HumanQuestionMapFamilyId, HumanQuestionMapModel, HumanQuestionMapVisualId, LatentRadarDatum, WorkflowLatentGovernanceVisualCopy, WorkflowLatentGovernanceVisualId, WorkflowLatentGovernanceVisualModel, WorkflowSankeyLinkDatum } from "./contracts";
import { compactThemeLabel, countBy, humanCategoryLabel, humanNodeDisplayTitle, selectRepresentativeNode, topRows } from "./semanticHuman";
import { sourceDisplayLabel } from "./sourceSlice";
import { addDays, formatChineseDate, isNodeBetween, maxNodeDate, parseDay } from "./utils";
import { clamp } from "../ui/visualStyles";



export function buildWorkflowLatentGovernanceVisualModel(
  nodes: AtlasNode[],
  graphEdges: AtlasEdge[],
  filters: AtlasFilters,
  sharedState: SharedAtlasState,
  deltaStats: DeltaStats,
): WorkflowLatentGovernanceVisualModel {
  const visualCopy: WorkflowLatentGovernanceVisualCopy[] = [
    {
      id: "agent_decision_sankey",
      title: "执行决策流",
      insightHeader: "Agent 路径要看入口、验收和回滚是否连起来",
      humanQuestion: "Codex/Agent 执行路径哪里失真？",
      actionValue: "把断点转成下一轮 run contract、validator 或人工授权判断。",
    },
    {
      id: "friction_heatmap",
      title: "返工摩擦热区",
      insightHeader: "返工热区优先处理证据缺口和 scope creep",
      humanQuestion: "我在哪些地方反复浪费时间？",
      actionValue: "把高热区转成停止条件、验收门禁或降噪规则。",
    },
    {
      id: "latent_radar",
      title: "潜在信号雷达",
      insightHeader: "潜在信号必须能被证据验证或降权",
      humanQuestion: "哪些潜在信号正在增强？",
      actionValue: "只继续验证可反驳、有证据 badge、有下一步的问题。",
    },
    {
      id: "evidence_timeline",
      title: "证据时间线",
      insightHeader: "结论要能沿时间线追到证据来源",
      humanQuestion: "这个结论从哪些记录来？",
      actionValue: "打开时间线复核证据新鲜度，避免旧结论继续驱动行动。",
    },
    {
      id: "formula_explorer",
      title: "公式解释",
      insightHeader: "公式权重只解释 proxy，不直接代表真实收益",
      humanQuestion: "这个分数为什么这样算？",
      actionValue: "检查参数、边界和仅提案规则，再决定是否继续进入授权流程。",
    },
  ];
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const latest = parseDay(deltaStats.latestDate) ?? maxNodeDate(memoryNodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const edgeCountByNode = graphEdges.reduce<Map<string, number>>((acc, edge) => {
    acc.set(edge.source, (acc.get(edge.source) ?? 0) + 1);
    acc.set(edge.target, (acc.get(edge.target) ?? 0) + 1);
    return acc;
  }, new Map<string, number>());

  const sankeyDefinitions = [
    {
      id: "human_to_codex",
      sourceLabel: "人类目标",
      targetLabel: "Codex 执行",
      patterns: ["goal", "task", "stage", "phase", "roadmap", "目标", "任务", "计划"],
      color: "#72d9d0",
    },
    {
      id: "codex_to_review",
      sourceLabel: "Codex 执行",
      targetLabel: "验证复审",
      patterns: ["validator", "validate", "test", "build", "audit", "验收", "测试", "复审"],
      color: "#8fd3ff",
    },
    {
      id: "review_to_rework",
      sourceLabel: "验证复审",
      targetLabel: "返工降噪",
      patterns: ["rework", "loop", "scope", "debt", "返工", "循环", "范围", "债"],
      color: "#f08fa3",
    },
    {
      id: "review_to_governance",
      sourceLabel: "验证复审",
      targetLabel: "治理记录",
      patterns: ["governance", "handoff", "record", "evidence", "机器治理", "记录", "证据"],
      color: "#f6c56f",
    },
    {
      id: "governance_to_authorization",
      sourceLabel: "治理记录",
      targetLabel: "授权下一步",
      patterns: ["proposal", "apply", "authorization", "next", "授权", "下一步", "门禁"],
      color: "#b6a2ff",
    },
  ];
  const sankeyLinks = sankeyDefinitions.map((definition, index): WorkflowSankeyLinkDatum => {
    const matching = memoryNodes.filter((node) => nodeTextMatches(node, definition.patterns));
    const value = Math.max(1, matching.length || Math.round(memoryNodes.length / Math.max(5, sankeyDefinitions.length + index)));
    return {
      id: definition.id,
      sourceLabel: definition.sourceLabel,
      targetLabel: definition.targetLabel,
      value,
      width: clamp(6 + Math.sqrt(value) * 4, 8, 30),
      y: 72 + index * 34,
      color: definition.color,
      node: selectRepresentativeNode(matching.length ? matching : memoryNodes),
    };
  });

  const frictionRows = [
    { id: "scope", label: "范围漂移", patterns: ["scope", "范围", "越界", "drift"], action: "先收口 run contract" },
    { id: "evidence", label: "证据缺口", patterns: ["evidence", "missing", "gap", "证据", "核验"], action: "补证据或降权" },
    { id: "rework", label: "返工循环", patterns: ["rework", "loop", "debt", "返工", "循环", "债"], action: "建立停止条件" },
    { id: "auth", label: "授权边界", patterns: ["auth", "apply", "raw", "credential", "授权", "凭证"], action: "保持 proposal-only" },
    { id: "formula", label: "公式维护", patterns: ["formula", "parameter", "weight", "公式", "参数", "权重"], action: "检查参数解释" },
  ];
  const frictionColumns = [
    { id: "planning", label: "规划", patterns: ["plan", "roadmap", "goal", "stage", "phase", "计划", "目标"] },
    { id: "execution", label: "执行", patterns: ["run", "build", "implement", "script", "执行", "开发"] },
    { id: "review", label: "复审", patterns: ["review", "audit", "validate", "test", "复审", "测试", "验收"] },
    { id: "governance", label: "治理", patterns: ["governance", "record", "handoff", "policy", "机器治理", "记录"] },
  ];
  const rawFrictionCells = frictionRows.flatMap((row) =>
    frictionColumns.map((column) => {
      const matching = memoryNodes.filter((node) => nodeTextMatches(node, row.patterns) && nodeTextMatches(node, column.patterns));
      const fallback = matching.length ? matching : memoryNodes.filter((node) => nodeTextMatches(node, row.patterns));
      return {
        id: `${row.id}_${column.id}`,
        rowLabel: row.label,
        columnLabel: column.label,
        count: matching.length,
        intensity: 0,
        action: row.action,
        node: selectRepresentativeNode(fallback.length ? fallback : memoryNodes),
      };
    }),
  );
  const maxFriction = Math.max(1, ...rawFrictionCells.map((cell) => cell.count));
  const frictionCells = rawFrictionCells.map((cell) => ({
    ...cell,
    intensity: clamp(cell.count / maxFriction, 0, 1),
  }));

  const latentAxisDefinitions = [
    { id: "asset_compounding", label: "资产复利", patterns: ["asset", "reuse", "handoff", "github", "恢复", "资产", "复用"] },
    { id: "automation_potential", label: "自动化势能", patterns: ["automation", "script", "validator", "sync", "自动化", "脚本"] },
    { id: "evidence_strength", label: "证据强度", patterns: ["evidence", "manifest", "audit", "证据", "核验"] },
    { id: "collaboration_clarity", label: "协作清晰", patterns: ["codex", "agent", "run contract", "协作", "任务包"] },
    { id: "governance_safety", label: "治理安全", patterns: ["governance", "raw", "credential", "proposal", "治理", "凭证", "授权"] },
  ];
  const latentAxes = latentAxisDefinitions.map((axis): LatentRadarDatum => {
    const matching = memoryNodes.filter((node) => nodeTextMatches(node, axis.patterns));
    const recentShare = matching.length
      ? matching.filter((node) => isNodeBetween(node, recentStart, latest)).length / Math.max(1, matching.length)
      : 0;
    const roi = matching.length ? average(matching.map((node) => normalizedNodeRoi(node))) : average(memoryNodes.map((node) => normalizedNodeRoi(node))) * 0.55;
    const density = matching.length / Math.max(1, Math.min(memoryNodes.length, 24));
    const value = clamp(density * 0.52 + roi * 0.3 + recentShare * 0.18, 0.12, 1);
    return {
      id: axis.id,
      label: axis.label,
      value,
      confidenceLabel: value >= 0.66 ? "高置信" : value >= 0.42 ? "中置信" : "待验证",
      evidenceBadge: value >= 0.66 ? "A" : value >= 0.34 ? "B" : "C",
      node: selectRepresentativeNode(matching.length ? matching : memoryNodes),
    };
  });

  const datedNodes = memoryNodes
    .filter((node) => parseDay(node.date))
    .sort((a, b) => (a.date ?? "").localeCompare(b.date ?? ""))
    .slice(-6);
  const firstDate = parseDay(datedNodes[0]?.date) ?? recentStart;
  const lastDate = parseDay(datedNodes[datedNodes.length - 1]?.date) ?? latest;
  const dateSpan = Math.max(1, lastDate.getTime() - firstDate.getTime());
  const evidenceEvents = (datedNodes.length ? datedNodes : memoryNodes.slice(0, 6)).map((node, index): EvidenceTimelineDatum => {
    const day = parseDay(node.date);
    const x = day ? 8 + ((day.getTime() - firstDate.getTime()) / dateSpan) * 84 : 10 + index * 15;
    const evidenceCount = Math.max(1, edgeCountByNode.get(node.id) ?? edgeCountHintForNode(node));
    return {
      id: node.id,
      label: compactThemeLabel(humanNodeDisplayTitle(node)).slice(0, 28),
      dateLabel: day ? formatChineseDate(day) : "无日期",
      x: clamp(x, 6, 92),
      evidenceCount,
      sourceLabel: sourceDisplayLabel(node.data_source ?? "memory_atlas", node.source_label ?? "memory_atlas"),
      node,
    };
  });

  const formulaNode = selectRepresentativeNode(memoryNodes.filter((node) => nodeTextMatches(node, ["formula", "parameter", "roi", "公式", "参数", "权重"]))) ?? selectRepresentativeNode(memoryNodes);
  const formulaRows: FormulaInspectorDatum[] = [
    {
      id: "time_saved_weight",
      label: "time_saved_weight",
      value: `${Math.round(average(memoryNodes.map((node) => normalizedNodeRoi(node))) * 100)}% proxy`,
      description: "时间节省权重来自内部信息 ROI proxy，不是精确收入预测。",
      sourcePath: "机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json",
      node: formulaNode,
    },
    {
      id: "reuse_value_weight",
      label: "reuse_value_weight",
      value: `${latentAxes.find((axis) => axis.id === "asset_compounding")?.evidenceBadge ?? "B"} badge`,
      description: "复用价值要能被 GitHub 可恢复资产或 handoff 证据支撑。",
      sourcePath: "data/derived/economic_proxy/formula_what_if_preview.json",
      node: formulaNode,
    },
    {
      id: "rework_cost_weight",
      label: "rework_cost_weight",
      value: `${frictionCells.filter((cell) => cell.rowLabel === "返工循环").reduce((sum, cell) => sum + cell.count, 0)} hits`,
      description: "返工成本用于扣减 proxy 分，帮助识别需要降噪的工作流。",
      sourcePath: "data/derived/behavior_intelligence/decision_debt_ledger.json",
      node: formulaNode,
    },
    {
      id: "proposal_required_before_apply",
      label: "proposal_required_before_apply",
      value: "true",
      description: "参数变化只进入 proposal，不直接写 active config 或 raw。",
      sourcePath: "data/derived/agent_collaboration/agent_authorization_boundary_report.json",
      node: formulaNode,
    },
  ];

  const activeFilters = {
    source: filters.source === "all" ? "全部来源" : sourceDisplayLabel(filters.source, filters.source),
    time: sharedState.filters.timeRange?.label ?? "全部时间",
    project: filters.theme === "all" ? "全部项目/主题" : filters.theme,
    task: filters.category === "all" ? "全部任务类别" : humanCategoryLabel(filters.category),
  };
  const hottestCell = [...frictionCells].sort((a, b) => b.count - a.count)[0];
  const strongestAxis = [...latentAxes].sort((a, b) => b.value - a.value)[0];
  const summary = memoryNodes.length
    ? `当前筛选下，${hottestCell?.rowLabel ?? "摩擦"} 在${hottestCell?.columnLabel ?? "流程"}最需要降噪，${strongestAxis?.label ?? "潜在信号"}是最强潜性轴；图谱已按来源、时间、项目和任务过滤。`
    : "当前筛选下没有可计算的工作流/潜性/治理信号；请放宽过滤条件后再查看。";

  return {
    schemaVersion: WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION,
    activeFilters,
    visualCopy,
    sankeyLinks,
    frictionCells,
    latentAxes,
    evidenceEvents,
    formulaRows,
    summary,
  };
}



export function buildHumanQuestionMapModel(
  clioModel: ClioLikeVisualModel,
  economicModel: EconomicLikeVisualModel,
  workflowModel: WorkflowLatentGovernanceVisualModel,
): HumanQuestionMapModel {
  const clioTargets: Record<ClioLikeVisualId, ViewKey> = {
    cluster_tree: "galaxy",
    bubble_map: "galaxy",
    topic_cluster_explorer: "search",
  };
  const economicTargets: Record<EconomicLikeVisualId, ViewKey> = {
    task_treemap: "roi",
    automation_vs_augmentation: "search",
    roi_scatter: "roi",
    opportunity_radar: "summary",
  };
  const workflowTargets: Record<WorkflowLatentGovernanceVisualId, ViewKey> = {
    agent_decision_sankey: "summary",
    friction_heatmap: "search",
    latent_radar: "summary",
    evidence_timeline: "timeline",
    formula_explorer: "roi",
  };
  const gateReasons: Record<HumanQuestionMapVisualId, string> = {
    cluster_tree: "问题能定位主题层级，行动能进入 galaxy/search 复核。",
    bubble_map: "问题能比较高频、机会和风险，行动能优先打开高 ROI 簇。",
    topic_cluster_explorer: "问题能决定继续追问哪个簇，行动能进入搜索复核证据。",
    task_treemap: "问题能识别 AI 使用集中任务，行动能与 ROI 对齐。",
    automation_vs_augmentation: "问题能区分自动化和增强，行动能选择固化流程或保留人工判断。",
    roi_scatter: "问题能识别值得继续加码的任务，行动能处理低 ROI 高频任务。",
    opportunity_radar: "问题能识别机会缺口，行动能选择下一步验证问题。",
    agent_decision_sankey: "问题能发现 Agent 执行路径失真，行动能转成 run contract 或授权判断。",
    friction_heatmap: "问题能定位反复浪费时间的位置，行动能转成停止条件或降噪规则。",
    latent_radar: "问题能追踪增强的潜在信号，行动能验证或降权。",
    evidence_timeline: "问题能追溯结论来源，行动能复核证据新鲜度。",
    formula_explorer: "问题能解释 proxy 分数，行动能检查参数和 proposal-only 边界。",
  };

  const entries: HumanQuestionMapEntry[] = [
    ...clioModel.visualCopy.map((copy) =>
      buildHumanQuestionMapEntry(copy, "clio_like", "主题/簇图谱", clioTargets[copy.id], gateReasons[copy.id]),
    ),
    ...economicModel.visualCopy.map((copy) =>
      buildHumanQuestionMapEntry(copy, "economic_like", "ROI/任务图谱", economicTargets[copy.id], gateReasons[copy.id]),
    ),
    ...workflowModel.visualCopy.map((copy) =>
      buildHumanQuestionMapEntry(copy, "workflow_governance", "工作流/治理图谱", workflowTargets[copy.id], gateReasons[copy.id]),
    ),
  ];
  const excludedCandidates: HumanQuestionMapExcludedCandidate[] = [
    {
      id: "decorative_density_cloud",
      title: "装饰性密度云",
      reason: "只有视觉密度，没有可回答的人类问题和行动入口，因此不纳入默认决策图谱。",
      visualRoiGatePass: false,
      p0Included: false,
    },
    {
      id: "raw_conversation_heat_glow",
      title: "Raw conversation heat glow",
      reason: "依赖原始私有语料且不能提升验收决策，因此保留为排除候选。",
      visualRoiGatePass: false,
      p0Included: false,
    },
  ];
  const p0VisualCount = entries.filter((entry) => entry.p0Included && entry.visualRoiGatePass).length;
  const failedP0Count = entries.filter((entry) => !entry.p0Included || !entry.visualRoiGatePass).length;
  const familyCounts = countBy(entries, (entry) => entry.familyLabel);
  const strongestGateLabel = topRows(familyCounts, 1)[0]?.label ?? "问题行动图谱";
  return {
    schemaVersion: HUMAN_QUESTION_MAP_VERSION,
    activeFilters: workflowModel.activeFilters,
    entries,
    excludedCandidates,
    p0VisualCount,
    failedP0Count,
    strongestGateLabel,
    summary: `${entries.length.toLocaleString()} 张图谱已统一到人类问题、行动价值和可验收判断；当前筛选沿用来源、时间、项目和任务，${failedP0Count.toLocaleString()} 张图谱未通过纳入标准。`,
  };
}



export function buildHumanQuestionMapEntry(
  copy: ClioLikeVisualCopy | EconomicLikeVisualCopy | WorkflowLatentGovernanceVisualCopy,
  familyId: HumanQuestionMapFamilyId,
  familyLabel: string,
  targetView: ViewKey,
  gateReason: string,
): HumanQuestionMapEntry {
  return {
    id: copy.id,
    familyId,
    familyLabel,
    title: copy.title,
    insightHeader: copy.insightHeader,
    humanQuestion: copy.humanQuestion,
    actionValue: copy.actionValue,
    targetView,
    gateReason,
    visualRoiGatePass: true,
    p0Included: true,
  };
}



export function nodeTextMatches(node: AtlasNode, patterns: string[]): boolean {
  const haystack = `${node.label} ${node.statement ?? ""} ${node.category ?? ""} ${node.memory_tier ?? ""} ${node.metrics?.roi?.recommended_action ?? ""}`.toLowerCase();
  return patterns.some((pattern) => haystack.includes(pattern.toLowerCase()));
}



export function workflowHeatColor(intensity: number): string {
  if (intensity >= 0.72) return "#f08fa3";
  if (intensity >= 0.42) return "#f6c56f";
  if (intensity > 0) return "#8fd3ff";
  return "#2c3440";
}
