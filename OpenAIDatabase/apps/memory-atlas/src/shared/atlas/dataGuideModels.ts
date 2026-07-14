import { normalizeMemoryTier } from "../../data/atlas";
import type { AtlasEdge, AtlasNode } from "../../types";
import { degreeMap, shortNodeLabel } from "./contributionModels";
import { DATA_MAP_STRUCTURE_LAYERS, DataGuideEdge, DataGuideFrame, DataGuideFrameId, DataGuideNode, DataGuideRelationExplanation, DataMapNodeDetail } from "./layoutContracts";
import { humanCategoryLabel, humanThemeLabel } from "./semanticHuman";
import { translateAction, translateKind, translateStaleness, truncate } from "./utils";



export function buildDataGuideLayout(nodes: AtlasNode[], edges: AtlasEdge[], limit: number): {
  frames: DataGuideFrame[];
  nodes: DataGuideNode[];
  edges: DataGuideEdge[];
  visibleNodeCount: number;
  edgeCount: number;
} {
  const degree = degreeMap(edges);
  const frameTemplates: Array<Omit<DataGuideFrame, "count">> = [
    buildDataGuideFrameTemplate("source", 36, 92, "#8fd3ff"),
    buildDataGuideFrameTemplate("profile", 276, 92, "#7ee8d4"),
    buildDataGuideFrameTemplate("project", 516, 92, "#f48fb1"),
    buildDataGuideFrameTemplate("action", 756, 92, "#94a3b8"),
  ];
  const framesById = new Map(frameTemplates.map((frame) => [frame.id, frame]));
  const frameBuckets = new Map<DataGuideFrameId, AtlasNode[]>();
  for (const frame of frameTemplates) frameBuckets.set(frame.id, []);

  const candidates = nodes
    .filter((node) => ["theme", "tier", "category", "project", "decision", "memory"].includes(node.kind))
    .sort((a, b) => dataGuideScore(b, degree) - dataGuideScore(a, degree) || (b.date ?? "").localeCompare(a.date ?? "") || a.label.localeCompare(b.label, "zh-CN"));
  for (const node of candidates) {
    frameBuckets.get(dataGuideFrameForNode(node))?.push(node);
  }

  const maxPerFrame = Math.max(8, Math.floor(limit / frameTemplates.length));
  const layoutNodes: DataGuideNode[] = [];
  for (const template of frameTemplates) {
    const bucket = frameBuckets.get(template.id) ?? [];
    const display = bucket.slice(0, maxPerFrame);
    const columns = 2;
    const gapX = 10;
    const gapY = 8;
    const cardW = (template.w - 34 - gapX) / columns;
    const cardH = 54;
    const startY = template.y + 78;
    display.forEach((node, index) => {
      const column = index % columns;
      const row = Math.floor(index / columns);
      const score = dataGuideScore(node, degree);
      layoutNodes.push({
        node,
        frameId: template.id,
        frameTitle: template.title,
        x: template.x + 14 + column * (cardW + gapX),
        y: startY + row * (cardH + gapY),
        w: cardW,
        h: cardH,
        color: dataGuideNodeColor(node, template.color),
        title: shortNodeLabel(node, 10),
        typeLabel: dataGuideTypeLabel(node),
        meta: dataGuideMetaLabel(node, degree.get(node.id) ?? 0),
        signalRadius: Math.min(8, 3 + Math.sqrt(Math.max(0, score)) * 0.48),
        score,
      });
    });
  }

  const byId = new Map(layoutNodes.map((node) => [node.node.id, node]));
  const layoutEdges = edges
    .map((edge): DataGuideEdge | null => {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target || source.frameId === target.frameId) return null;
      const left = source.x <= target.x ? source : target;
      const right = left === source ? target : source;
      return {
        id: edge.id,
        source,
        target,
        path: dataGuideEdgePath(left, right),
        color: right.color,
        strokeWidth: Math.max(0.9, Math.min(3.2, 0.8 + edge.weight * 1.4)),
        explanation: dataGuideRelationExplanation(edge, source, target),
      };
    })
    .filter((edge): edge is DataGuideEdge => Boolean(edge))
    .sort((a, b) => b.strokeWidth - a.strokeWidth)
    .slice(0, 130);

  const frames = frameTemplates.map((frame) => ({ ...frame, count: frameBuckets.get(frame.id)?.length ?? 0 }));
  return {
    frames,
    nodes: layoutNodes,
    edges: layoutEdges,
    visibleNodeCount: layoutNodes.length,
    edgeCount: layoutEdges.length,
  };
}



export function buildDataGuideFrameTemplate(
  frameId: DataGuideFrameId,
  x: number,
  y: number,
  color: string,
): Omit<DataGuideFrame, "count"> {
  const layer = DATA_MAP_STRUCTURE_LAYERS.find((item) => item.frameId === frameId);
  if (!layer) throw new Error(`Unknown data guide frame: ${frameId}`);
  return {
    id: frameId,
    structureLayerId: layer.id,
    title: layer.title,
    subtitle: layer.subtitle,
    nodeTypes: layer.nodeTypes,
    fields: layer.fields,
    interaction: layer.interaction,
    detailEntry: layer.detailEntry,
    x,
    y,
    w: 214,
    h: 448,
    color,
  };
}



export function dataGuideFrameForNode(node: AtlasNode): DataGuideFrameId {
  if (node.kind !== "memory") return "source";
  const tier = normalizeMemoryTier(node.memory_tier);
  if (tier === "核心画像" || node.category === "preference" || node.category === "answering_rule" || node.category === "security_boundary") {
    return "profile";
  }
  if (node.category === "decision" || node.category === "project_context" || node.category === "workflow") {
    return "project";
  }
  return "action";
}



export function dataGuideScore(node: AtlasNode, degree: Map<string, number>): number {
  const tier = normalizeMemoryTier(node.memory_tier);
  const importance = node.importance === "高" ? 18 : node.importance === "中" ? 9 : 2;
  const tierScore = tier === "核心画像" ? 22 : tier === "一般" ? 11 : 4;
  const categoryScore = ["decision", "answering_rule", "project_context", "workflow", "preference"].includes(node.category ?? "") ? 18 : 0;
  const kindScore = node.kind === "theme" ? 24 : node.kind === "project" || node.kind === "decision" ? 18 : 0;
  const roi = (node.metrics?.roi?.leverage_score ?? 0) * 12;
  return (degree.get(node.id) ?? 0) * 2.2 + importance + tierScore + categoryScore + kindScore + roi;
}



export function dataGuideNodeColor(node: AtlasNode, frameColor: string): string {
  if (node.kind !== "memory") return "#8fd3ff";
  if (node.category === "decision") return "#f48fb1";
  if (node.category === "security_boundary") return "#c7a7ff";
  if (normalizeMemoryTier(node.memory_tier) === "核心画像") return "#7ee8d4";
  return frameColor;
}



export function dataGuideTypeLabel(node: AtlasNode): string {
  if (node.kind !== "memory") return translateKind(node.kind);
  const tier = normalizeMemoryTier(node.memory_tier);
  const category = humanCategoryLabel(node.category);
  return truncate(tier === "未分层" ? category : `${tier} · ${category}`, 13);
}



export function dataGuideMetaLabel(node: AtlasNode, degree: number): string {
  const parts = [
    node.date ? node.date.slice(0, 10) : "",
    degree ? `${degree} 连` : "",
    node.importance ? `重要性${node.importance}` : "",
  ].filter(Boolean);
  return truncate(parts.join(" / ") || "结构节点", 16);
}



export function dataGuideEdgePath(left: DataGuideNode, right: DataGuideNode): string {
  const x1 = left.x + left.w;
  const y1 = left.y + left.h / 2;
  const x2 = right.x;
  const y2 = right.y + right.h / 2;
  const dx = Math.max(54, (x2 - x1) * 0.45);
  return `M${x1} ${y1} C${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
}



export function dataGuideRelationExplanation(edge: AtlasEdge, source: DataGuideNode, target: DataGuideNode): DataGuideRelationExplanation {
  const sourceNode = source.node;
  const targetNode = target.node;
  const strength = dataGuideRelationStrength(edge.weight);
  const time = dataGuideRelationTime(sourceNode, targetNode);
  const evidence = [
    `edge:${edge.id}`,
    `kind:${edge.kind || "related"}`,
    `weight:${edge.weight.toFixed(2)}`,
    `nodes:${sourceNode.id},${targetNode.id}`,
  ].join(" | ");
  const sourceLabel = shortNodeLabel(sourceNode, 18);
  const targetLabel = shortNodeLabel(targetNode, 18);
  const sourceDetail = [
    source.frameTitle,
    sourceNode.source_label || sourceNode.data_source || translateKind(sourceNode.kind),
    edge.kind || "related",
  ].filter(Boolean).join(" / ");

  return {
    source: sourceDetail,
    sourceLabel,
    targetLabel,
    strength,
    evidence,
    time,
    reason: `${source.frameTitle}「${sourceLabel}」连接到${target.frameTitle}「${targetLabel}」：${edge.kind || "related"} 关系，强度 ${strength}，证据来自当前 atlas edge 和两端节点。`,
  };
}



export function dataGuideRelationStrength(weight: number): string {
  if (weight >= 0.78) return "高";
  if (weight >= 0.48) return "中";
  return "低";
}



export function dataGuideRelationTime(source: AtlasNode, target: AtlasNode): string {
  const dates = [source.date, target.date].filter((date): date is string => Boolean(date)).sort();
  return dates.at(-1)?.slice(0, 10) || "time unavailable";
}



export function buildDataMapNodeDetail(node: AtlasNode | null, edges: AtlasEdge[]): DataMapNodeDetail {
  if (!node) {
    return {
      asset: "未选择",
      theme: "未选择",
      suggestedAction: "未选择",
      importance: "未选择",
      priority: "未选择",
      status: "默认折叠",
      layerLabel: "默认折叠",
      summary: "点击节点后显示资产、主题、建议动作、重要性和优先级。",
      evidenceRefs: [],
    };
  }
  const asset = dataMapAssetLabelForNode(node);
  const theme = humanThemeLabel(node);
  const suggestedAction = translateAction(node.metrics?.roi?.recommended_action);
  const importance = node.importance || "未知";
  const priority = dataMapPriorityForNode(node);
  const status = [
    normalizeMemoryTier(node.memory_tier),
    humanCategoryLabel(node.category),
    node.metrics?.roi?.staleness_status ? translateStaleness(node.metrics.roi.staleness_status) : "",
  ].filter(Boolean).join(" / ") || translateKind(node.kind);
  const layerLabel = DATA_MAP_STRUCTURE_LAYERS.find((layer) => layer.frameId === dataGuideFrameForNode(node))?.label ?? "未归层";
  const evidenceRefs = dataMapEvidenceRefsForNode(node, edges);
  return {
    asset,
    theme,
    suggestedAction,
    importance,
    priority,
    status,
    layerLabel,
    summary: `${asset} 位于 ${theme}，建议动作是 ${suggestedAction}；重要性 ${importance}，优先级 ${priority}。`,
    evidenceRefs,
  };
}



export function dataMapAssetLabelForNode(node: AtlasNode): string {
  if (node.kind === "theme") return "主题资产";
  if (node.kind === "project") return "项目资产";
  if (node.kind === "decision") return "决策资产";
  const tier = normalizeMemoryTier(node.memory_tier);
  const category = humanCategoryLabel(node.category);
  return [tier, category].filter(Boolean).join(" · ") || translateKind(node.kind);
}



export function dataMapPriorityForNode(node: AtlasNode): "watch" | "p3" | "p2" | "p1" | "p0" {
  const leverage = node.metrics?.roi?.leverage_score ?? 0;
  if (node.importance === "高" && leverage >= 0.75) return "p0";
  if (node.importance === "高") return "p1";
  if (leverage >= 0.6) return "p2";
  if (node.metrics?.roi?.staleness_status === "stale" || node.validity === "stale" || node.category === "deprecated_info") return "watch";
  return "p3";
}



export function dataMapEvidenceRefsForNode(node: AtlasNode, edges: AtlasEdge[]): string[] {
  const refs = edges
    .filter((edge) => edge.source === node.id || edge.target === node.id)
    .sort((a, b) => b.weight - a.weight || a.id.localeCompare(b.id))
    .slice(0, 6)
    .map((edge) => `${edge.kind || "related"}:${edge.id}:weight=${edge.weight.toFixed(2)}`);
  return refs.length ? refs : [`node:${node.id}:derived_snapshot`];
}
