export type MemoryClusterKind = "dominant" | "rising" | "declining" | "black_hole" | "proto_star" | "terrain";

export type MemoryClusterFixture = {
  id: string;
  label: string;
  kind: MemoryClusterKind;
  summary: string;
  mass: number;
  confidence: number;
  evidenceCount: number;
  color: string;
  position: [number, number, number];
};

export const memoryStarfieldFixture = {
  schemaVersion: "memory_starfield_spike_fixture.v1",
  source: "redacted derived sample",
  rawPrivateDataIncluded: false,
  plaintextSecretsIncluded: false,
  localAbsolutePathsIncluded: false,
  clusters: [
    {
      id: "cluster-memory-continuity",
      label: "长期记忆连续性",
      kind: "dominant",
      summary: "核心主题稳定，持续连接 Memory Atlas、RAG 和 agent personalization。",
      mass: 1.0,
      confidence: 0.92,
      evidenceCount: 128,
      color: "#8fd3ff",
      position: [-1.35, 0.18, -0.25],
    },
    {
      id: "cluster-codex-workflow",
      label: "Codex 工作流",
      kind: "dominant",
      summary: "开发节奏、验证习惯、路径约束和 GitHub 交付规则高度集中。",
      mass: 0.92,
      confidence: 0.9,
      evidenceCount: 112,
      color: "#7ee8d4",
      position: [1.08, -0.12, 0.18],
    },
    {
      id: "cluster-visual-ux",
      label: "可视化体验升级",
      kind: "rising",
      summary: "记忆星系、时间河、Universe State 的可视化需求正在升温。",
      mass: 0.74,
      confidence: 0.82,
      evidenceCount: 54,
      color: "#f7cf6b",
      position: [0.32, 0.88, -0.52],
    },
    {
      id: "cluster-agent-governance",
      label: "Agent 治理",
      kind: "rising",
      summary: "任务边界、验收证据、参数登记和复审流程成为稳定治理层。",
      mass: 0.68,
      confidence: 0.78,
      evidenceCount: 46,
      color: "#b9a8ff",
      position: [-0.12, -0.92, 0.46],
    },
    {
      id: "cluster-stale-imports",
      label: "旧导入路径降温",
      kind: "declining",
      summary: "旧电脑路径、standalone repo、shadow checkout 已被明确降权。",
      mass: 0.46,
      confidence: 0.76,
      evidenceCount: 33,
      color: "#8aa0b8",
      position: [-1.95, -0.62, 0.34],
    },
    {
      id: "black-hole-scope-drift",
      label: "范围漂移黑洞",
      kind: "black_hole",
      summary: "若跳过 phase 边界，容易把合同、spike 与生产集成混在一起。",
      mass: 0.82,
      confidence: 0.86,
      evidenceCount: 39,
      color: "#1d2433",
      position: [1.78, 0.72, -0.08],
    },
    {
      id: "proto-star-universe-state",
      label: "Universe State 原型机会",
      kind: "proto_star",
      summary: "共享状态层可成为记忆总览、星系、时间河联动的第一颗新星。",
      mass: 0.58,
      confidence: 0.7,
      evidenceCount: 24,
      color: "#ffef9a",
      position: [0.82, 1.42, 0.38],
    },
    {
      id: "terrain-review-ridge",
      label: "复审山脊",
      kind: "terrain",
      summary: "复审、证据和回滚形成稳定高地，适合在 Analysis Mode 解释。",
      mass: 0.52,
      confidence: 0.74,
      evidenceCount: 29,
      color: "#74c0fc",
      position: [-0.78, 1.22, 0.66],
    },
  ] satisfies MemoryClusterFixture[],
};
