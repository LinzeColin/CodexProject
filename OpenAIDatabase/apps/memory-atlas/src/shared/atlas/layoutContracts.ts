import type { AtlasNode } from "../../types";



export type DataGuideFrameId = "source" | "profile" | "project" | "action";


export type DataMapStructureLayerId = "source_layer" | "profile_layer" | "project_decision_layer" | "action_opportunity_layer";



export const DATA_MAP_STRUCTURE_LAYERS: Array<{
  id: DataMapStructureLayerId;
  frameId: DataGuideFrameId;
  label: string;
  title: string;
  subtitle: string;
  nodeTypes: string[];
  fields: string[];
  interaction: string;
  detailEntry: string;
  defaultCollapsed: true;
}> = [
  {
    id: "source_layer",
    frameId: "source",
    label: "来源层",
    title: "来源层",
    subtitle: "来源 / 主题簇 / 分类索引",
    nodeTypes: ["theme", "tier", "category"],
    fields: ["data_source", "source_label", "category", "date"],
    interaction: "select_source_or_topic_node",
    detailEntry: "open_source_or_topic_detail",
    defaultCollapsed: true,
  },
  {
    id: "profile_layer",
    frameId: "profile",
    label: "画像层",
    title: "画像层",
    subtitle: "核心画像 / taste / 规则",
    nodeTypes: ["memory:preference", "memory:answering_rule", "memory:security_boundary"],
    fields: ["memory_tier", "category", "importance", "confidence"],
    interaction: "select_profile_node",
    detailEntry: "open_profile_detail",
    defaultCollapsed: true,
  },
  {
    id: "project_decision_layer",
    frameId: "project",
    label: "项目决策层",
    title: "项目决策层",
    subtitle: "项目背景 / 决策 / 工作流",
    nodeTypes: ["project", "decision", "memory:project_context", "memory:workflow"],
    fields: ["project", "decision", "validity", "importance"],
    interaction: "select_project_decision_node",
    detailEntry: "open_project_decision_detail",
    defaultCollapsed: true,
  },
  {
    id: "action_opportunity_layer",
    frameId: "action",
    label: "行动机会层",
    title: "行动机会层",
    subtitle: "行动 / 机会 / 待整理",
    nodeTypes: ["memory:temporary", "memory:recommended_action", "memory:roi_opportunity"],
    fields: ["recommended_action", "leverage_score", "staleness_status", "date"],
    interaction: "select_action_opportunity_node",
    detailEntry: "open_action_opportunity_detail",
    defaultCollapsed: true,
  },
];



export interface DataGuideFrame {
  id: DataGuideFrameId;
  structureLayerId: DataMapStructureLayerId;
  title: string;
  subtitle: string;
  nodeTypes: string[];
  fields: string[];
  interaction: string;
  detailEntry: string;
  x: number;
  y: number;
  w: number;
  h: number;
  color: string;
  count: number;
}



export interface DataGuideNode {
  node: AtlasNode;
  frameId: DataGuideFrameId;
  frameTitle: string;
  x: number;
  y: number;
  w: number;
  h: number;
  color: string;
  title: string;
  typeLabel: string;
  meta: string;
  signalRadius: number;
  score: number;
}



export interface DataGuideEdge {
  id: string;
  source: DataGuideNode;
  target: DataGuideNode;
  path: string;
  color: string;
  strokeWidth: number;
  explanation: DataGuideRelationExplanation;
}



export interface DataGuideRelationExplanation {
  source: string;
  sourceLabel: string;
  targetLabel: string;
  strength: string;
  evidence: string;
  time: string;
  reason: string;
}



export interface DataMapNodeDetail {
  asset: string;
  theme: string;
  suggestedAction: string;
  importance: string;
  priority: string;
  status: string;
  layerLabel: string;
  summary: string;
  evidenceRefs: string[];
}
