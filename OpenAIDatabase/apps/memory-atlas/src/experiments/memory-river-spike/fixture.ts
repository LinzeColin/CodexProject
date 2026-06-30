export type RiverLaneLevel = "macro" | "meso" | "micro";

export type RiverLaneFixture = {
  id: string;
  label: string;
  level: RiverLaneLevel;
  summary: string;
  color: string;
  evidenceCount: number;
};

export type RiverEventKind = "decision" | "build" | "review" | "migration" | "signal";

export type RiverEventFixture = {
  id: string;
  laneId: string;
  occurredAt: string;
  kind: RiverEventKind;
  label: string;
  summary: string;
  intensity: number;
  confidence: number;
  evidenceCount: number;
  sourceScope: "redacted_summary" | "derived_snapshot";
};

export type RiverBandFixture = {
  id: string;
  startAt: string;
  endAt: string;
  label: string;
  summary: string;
  intensity: number;
  suggestedAction: string;
  evidenceCount: number;
};

export type RiverMarkerFixture = {
  id: string;
  laneId: string;
  occurredAt: string;
  label: string;
  summary: string;
  confidence: number;
  evidenceCount: number;
};

export const memoryRiverFixture = {
  schemaVersion: "memory_river_spike_fixture.v1",
  source: "redacted derived temporal sample",
  rawPrivateDataIncluded: false,
  plaintextSecretsIncluded: false,
  localAbsolutePathsIncluded: false,
  writebackAllowed: false,
  window: {
    startAt: "2026-01-01T00:00:00Z",
    endAt: "2026-06-30T00:00:00Z",
  },
  lanes: [
    {
      id: "lane-memory-atlas",
      label: "Memory Atlas",
      level: "macro",
      summary: "长期记忆、可视化、RAG 和 personalization 的主河道。",
      color: "#8fd3ff",
      evidenceCount: 142,
    },
    {
      id: "lane-codex-workflow",
      label: "Codex 工作流",
      level: "macro",
      summary: "路径约束、Task Pack、验收证据、GitHub 同步持续增强。",
      color: "#7ee8d4",
      evidenceCount: 119,
    },
    {
      id: "lane-visual-system",
      label: "视觉系统",
      level: "meso",
      summary: "星系、时间河、Universe State 的视觉语言逐步成形。",
      color: "#f7cf6b",
      evidenceCount: 68,
    },
    {
      id: "lane-governance",
      label: "治理与复审",
      level: "meso",
      summary: "单 phase、复审、回滚和证据登记成为稳定交付约束。",
      color: "#b9a8ff",
      evidenceCount: 51,
    },
    {
      id: "lane-import-hygiene",
      label: "导入边界",
      level: "micro",
      summary: "旧电脑路径、standalone repo 和 raw session 数据被明确隔离。",
      color: "#8aa0b8",
      evidenceCount: 34,
    },
  ] satisfies RiverLaneFixture[],
  events: [
    {
      id: "evt-scope-freeze",
      laneId: "lane-memory-atlas",
      occurredAt: "2026-01-12T00:00:00Z",
      kind: "decision",
      label: "范围冻结",
      summary: "Memory Atlas v1.1.5 首批模块被限定为总览、星系、时间河、共享状态层。",
      intensity: 0.62,
      confidence: 0.86,
      evidenceCount: 18,
      sourceScope: "derived_snapshot",
    },
    {
      id: "evt-codex-rules",
      laneId: "lane-codex-workflow",
      occurredAt: "2026-02-02T00:00:00Z",
      kind: "decision",
      label: "Codex 路径规则",
      summary: "canonical repo、项目级 worktree 和低上下文读取边界被稳定采用。",
      intensity: 0.7,
      confidence: 0.9,
      evidenceCount: 29,
      sourceScope: "redacted_summary",
    },
    {
      id: "evt-river-contract",
      laneId: "lane-visual-system",
      occurredAt: "2026-02-21T00:00:00Z",
      kind: "build",
      label: "时间河合同",
      summary: "Timeline 被重新定义为 dynamic time river，而不是列表或静态散点。",
      intensity: 0.56,
      confidence: 0.78,
      evidenceCount: 16,
      sourceScope: "derived_snapshot",
    },
    {
      id: "evt-review-rhythm",
      laneId: "lane-governance",
      occurredAt: "2026-03-08T00:00:00Z",
      kind: "review",
      label: "复审节奏",
      summary: "每个 stage 完成后复审，复审暴露问题先修再上传 main。",
      intensity: 0.64,
      confidence: 0.84,
      evidenceCount: 21,
      sourceScope: "redacted_summary",
    },
    {
      id: "evt-shadow-risk",
      laneId: "lane-import-hygiene",
      occurredAt: "2026-03-26T00:00:00Z",
      kind: "signal",
      label: "旧路径风险",
      summary: "旧电脑路径和 shadow checkout 只能作为历史参考，不能作为事实源。",
      intensity: 0.52,
      confidence: 0.82,
      evidenceCount: 14,
      sourceScope: "redacted_summary",
    },
    {
      id: "evt-starfield-spike",
      laneId: "lane-visual-system",
      occurredAt: "2026-04-17T00:00:00Z",
      kind: "build",
      label: "星系 Spike",
      summary: "WebGL starfield 验证了星云、流场、引力盘、黑洞和新星视觉方向。",
      intensity: 0.88,
      confidence: 0.88,
      evidenceCount: 32,
      sourceScope: "derived_snapshot",
    },
    {
      id: "evt-history-import",
      laneId: "lane-import-hygiene",
      occurredAt: "2026-05-09T00:00:00Z",
      kind: "migration",
      label: "历史导入边界",
      summary: "旧电脑 session history 被放入历史导入区，避免覆盖新电脑 live session。",
      intensity: 0.68,
      confidence: 0.8,
      evidenceCount: 19,
      sourceScope: "redacted_summary",
    },
    {
      id: "evt-governance-spike",
      laneId: "lane-governance",
      occurredAt: "2026-05-28T00:00:00Z",
      kind: "review",
      label: "证据驱动验收",
      summary: "验收从口头确认转为 build、浏览器、端口和 Git 证据组合。",
      intensity: 0.76,
      confidence: 0.86,
      evidenceCount: 27,
      sourceScope: "derived_snapshot",
    },
    {
      id: "evt-river-spike",
      laneId: "lane-memory-atlas",
      occurredAt: "2026-06-30T00:00:00Z",
      kind: "build",
      label: "时间河 Spike",
      summary: "Stage 1 验证 zoom、brush、theme lanes、黑洞带和机会 marker。",
      intensity: 0.92,
      confidence: 0.74,
      evidenceCount: 12,
      sourceScope: "derived_snapshot",
    },
  ] satisfies RiverEventFixture[],
  blackHoleBands: [
    {
      id: "band-scope-drift",
      startAt: "2026-03-18T00:00:00Z",
      endAt: "2026-04-08T00:00:00Z",
      label: "范围漂移黑洞带",
      summary: "多项目上下文、旧路径和过早集成风险在这一窗口变强。",
      intensity: 0.84,
      suggestedAction: "继续执行 single phase run contract，并把生产集成留到后续 stage。",
      evidenceCount: 17,
    },
  ] satisfies RiverBandFixture[],
  protoStars: [
    {
      id: "proto-universe-state",
      laneId: "lane-memory-atlas",
      occurredAt: "2026-05-21T00:00:00Z",
      label: "Universe State 原型机会",
      summary: "共享状态层可成为总览、星系、时间河、Inspector 和 ROI 的共同语义层。",
      confidence: 0.72,
      evidenceCount: 23,
    },
    {
      id: "proto-river-pulse",
      laneId: "lane-visual-system",
      occurredAt: "2026-06-12T00:00:00Z",
      label: "River Pulse 机会",
      summary: "首页近期脉冲可以从时间河选择窗口中派生，减少重复状态计算。",
      confidence: 0.66,
      evidenceCount: 11,
    },
  ] satisfies RiverMarkerFixture[],
};
