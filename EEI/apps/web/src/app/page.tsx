"use client";

import { useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import {
  ArrowDown,
  ArrowUp,
  Boxes,
  ChevronLeft,
  Crosshair,
  FileSearch,
  GitBranch,
  Network,
  Route,
  Search,
  RotateCcw,
  Save,
  Star
} from "lucide-react";
import {
  ACTIVE_ANALYSIS_CONTEXT,
  ANALYSIS_PREVIEW_STORAGE_KEY,
  type AnalysisContext
} from "./analysis-contract";
import {
  EXPLORE_API_BASE_STORAGE_KEY,
  loadExploreGraph,
  type ExploreGraphRecord,
  type ExploreGraphRequest
} from "./explore-api-client";
import {
  MODEL_CONTEXT_API_BASE_STORAGE_KEY,
  activateModelProfile,
  listModelProfiles,
  loadActiveModelContext,
  type ActiveModelContextRecord,
  type ModelActivationResult,
  type ScoringProfileRecord
} from "./model-activation-client";
import { useAnalysisContext } from "./use-analysis-context";
import {
  SAVED_VIEW_API_BASE_STORAGE_KEY,
  SAVED_VIEW_WORKSPACE_KEY,
  restoreViewFromServer,
  saveViewToServer,
  type SavedViewServerRecord,
  type SavedViewSyncResult
} from "./saved-view-client";
import {
  createWorkspaceContextValue,
  SAVED_VIEW_STORAGE_KEY,
  WORKSPACE_STATE_STORAGE_KEY,
  WorkspaceContextContractMarker,
  WorkspaceContextProvider,
  type WorkspaceModuleId
} from "./workspace-context";
import { WorkspaceNavigationRail } from "./workspace-navigation";

type FocusKey =
  | "materials"
  | "equipment"
  | "foundry"
  | "nvidia"
  | "business"
  | "capital"
  | "policy"
  | "systems"
  | "cloud"
  | "datacenter"
  | "energy";

type NodeKey = FocusKey | "systemMakersGroup";

type LensKey =
  | "all"
  | "supply_chain"
  | "business_segments"
  | "capital_transactions"
  | "policy_risk";

type RelationshipLens = Exclude<LensKey, "all">;

type SemanticZoom = "L0" | "L1" | "L2" | "L3";

type TransitionState = "ready" | "loading" | "fallback";

type TimelineKey = "2026-06-01" | "2026-06-12" | "2026-06-19";

type WorkspaceLayerKey =
  | "group_structure"
  | "business_segments"
  | "supply_chain"
  | "capital_network"
  | "ma_transactions"
  | "control_relationships"
  | "policy_environment"
  | "strategic_signals";

type StructureKind = "legal_group" | "business_segment" | "brand" | "product" | "facility";

type WorkspaceState = {
  focusKey: FocusKey;
  selectedKey: NodeKey;
  path: FocusKey[];
  activeLens: LensKey;
  semanticZoom: SemanticZoom;
  asOf: TimelineKey;
};

type SavedViewRecord = WorkspaceState & {
  id: string;
  version: "saved-view-v1";
  workspaceKey: string;
  filters: string;
  layout: string;
  modelVersion: string;
  profileVersion: string;
  dataSnapshot: string;
  scoreSnapshot: string;
  notes: string;
  updatedAt: string;
  serverId?: string;
  serverVersion?: number;
  syncMode: "server" | "local_fallback";
  syncReason: string;
  serverEndpoint?: string;
};

type ModelContextStatus =
  | "local-active"
  | "loading-server-context"
  | "server-current"
  | "server-stale"
  | "activating"
  | "server-activated"
  | "server-refreshed"
  | "server-conflict"
  | "server-error"
  | "server-no-target";

type ProductionGraphStatus =
  | "local-fixture"
  | "loading-production-graph"
  | "server-hydrated"
  | "server-error";

type WorkspaceStateInput = {
  focusKey?: unknown;
  selectedKey?: unknown;
  path?: unknown;
  activeLens?: unknown;
  semanticZoom?: unknown;
  asOf?: unknown;
};

type Zone =
  | "upstream"
  | "focus"
  | "downstream"
  | "infrastructure"
  | "business"
  | "capital"
  | "policy";

type MapNode = {
  key: NodeKey;
  label: string;
  shortLabel: string;
  stage: string;
  role: string;
  x: number;
  y: number;
  zone: Zone;
  centerable: boolean;
  aggregateCount?: number;
  groupMembers?: string[];
};

type MapEdge = {
  from: NodeKey;
  to: NodeKey;
  label: string;
  stage: string;
  lens: RelationshipLens;
  fixtureNotice: string;
};

type GraphRenderNode = {
  key: string;
  label: string;
  shortLabel: string;
  stage: string;
  role: string;
  x: number;
  y: number;
  zone: Zone;
  centerable: boolean;
  source: "fixture" | "server";
  localKey?: NodeKey;
  entityType?: string;
  fixtureNotice?: string | null;
  aggregateCount?: number;
  groupMembers?: string[];
};

type GraphRenderEdge = {
  id: string;
  from: string;
  to: string;
  label: string;
  stage: string;
  lens: RelationshipLens;
  fixtureNotice: string;
  evidenceCount: number;
  observedAt: string;
  source: "fixture" | "server";
};

type FocusScenario = {
  focus: FocusKey;
  heading: string;
  subtitle: string;
  nodes: MapNode[];
  edges: MapEdge[];
  nextCenters: FocusKey[];
};

type HomeSearchResult = {
  key: string;
  label: string;
  description: string;
  aliases: string[];
  target: FocusKey;
  objectType: "entity" | "industry" | "theme" | "facility";
};

type HomeIndustryEntry = {
  key: string;
  name: string;
  taxonomy: string;
  entityCount: number;
  recentChangeCount: number;
  target: FocusKey;
};

type HomeWatchItem = {
  key: FocusKey;
  label: string;
  unread: number;
  state: string;
  savedLens: LensKey;
  savedZoom: SemanticZoom;
  profile: string;
};

type HomeRecentEntry = {
  key: FocusKey;
  label: string;
  path: string;
};

type HomeChangeEntry = {
  key: string;
  label: string;
  severity: string;
  target: FocusKey;
};

const entityLabels: Record<NodeKey, string> = {
  materials: "Synthetic Specialty Materials Co.",
  equipment: "Synthetic Lithography Equipment Co.",
  foundry: "Synthetic Advanced Foundry",
  nvidia: "NVIDIA Corporation",
  business: "Synthetic Accelerated Computing Segment",
  capital: "Synthetic Capital Commitment",
  policy: "Synthetic Export Control Context",
  systems: "Synthetic Systems Integrator",
  cloud: "Synthetic Cloud Customer",
  datacenter: "Synthetic AI Data Center Campus",
  energy: "Synthetic Grid Utility",
  systemMakersGroup: "Synthetic System Makers Group"
};

const shortLabels: Record<NodeKey, string> = {
  materials: "Materials",
  equipment: "Equipment",
  foundry: "Foundry",
  nvidia: "NVIDIA",
  business: "Accel Compute",
  capital: "Capital",
  policy: "Policy Risk",
  systems: "Systems",
  cloud: "Cloud",
  datacenter: "Data Center",
  energy: "Energy",
  systemMakersGroup: "System Makers"
};

const lensItems: { key: LensKey; label: string }[] = [
  { key: "all", label: "综合" },
  { key: "supply_chain", label: "供应链" },
  { key: "business_segments", label: "业务" },
  { key: "capital_transactions", label: "资本" },
  { key: "policy_risk", label: "政策" }
];

const workspaceLayerItems: {
  key: WorkspaceLayerKey;
  label: string;
  state: "active" | "available" | "stub";
}[] = [
  { key: "group_structure", label: "集团结构", state: "active" },
  { key: "business_segments", label: "业务板块", state: "active" },
  { key: "supply_chain", label: "供应链", state: "available" },
  { key: "capital_network", label: "资本网络", state: "available" },
  { key: "ma_transactions", label: "并购交易", state: "stub" },
  { key: "control_relationships", label: "控制关系", state: "stub" },
  { key: "policy_environment", label: "政策环境", state: "available" },
  { key: "strategic_signals", label: "战略信号", state: "stub" }
];

const structureRows: {
  kind: StructureKind;
  label: string;
  typeLabel: string;
  relationship: string;
  scope: "focus" | "direct" | "adjacent" | "missing";
  control: string;
}[] = [
  {
    kind: "legal_group",
    label: "NVIDIA Corporation",
    typeLabel: "legal_entity",
    relationship: "focus_entity",
    scope: "focus",
    control: "当前主体；不是母子控制声明"
  },
  {
    kind: "business_segment",
    label: "Accelerated Computing Segment (Synthetic)",
    typeLabel: "business_segment",
    relationship: "segment_of",
    scope: "direct",
    control: "业务映射；不是法律控制声明"
  },
  {
    kind: "brand",
    label: "No brand fixture loaded",
    typeLabel: "brand",
    relationship: "unknown",
    scope: "missing",
    control: "未知保留；不补零"
  },
  {
    kind: "product",
    label: "AI Accelerator Platform (Synthetic)",
    typeLabel: "product",
    relationship: "product_of",
    scope: "direct",
    control: "产品映射；不是法律控制声明"
  },
  {
    kind: "facility",
    label: "Synthetic AI Data Center Campus",
    typeLabel: "facility",
    relationship: "operates_facility via CoreWeave",
    scope: "adjacent",
    control: "相邻生态设施；不表示 NVIDIA 拥有或运营"
  }
];

const semanticZoomItems: { key: SemanticZoom; label: string; title: string }[] = [
  { key: "L0", label: "L0", title: "Overview with grouped dense nodes" },
  { key: "L1", label: "L1", title: "Relationship labels" },
  { key: "L2", label: "L2", title: "Evidence and fixture state" },
  { key: "L3", label: "L3", title: "Detailed node role labels" }
];

const timelineItems: {
  key: TimelineKey;
  label: string;
  change: string;
  overlay: string;
}[] = [
  {
    key: "2026-06-01",
    label: "Baseline",
    change: "Baseline supplier and customer graph",
    overlay: "No material-change overlay in this fixture snapshot"
  },
  {
    key: "2026-06-12",
    label: "Comparison",
    change: "Packaging queue and customer-demand path changed",
    overlay: "Change overlay highlights packaging and demand pressure"
  },
  {
    key: "2026-06-19",
    label: "Active",
    change: "Current fixture snapshot for MVP validation",
    overlay: "Active snapshot, not real-time market data"
  }
];

const SAVED_VIEW_VERSION = "saved-view-v1";
const WORKSPACE_LAYOUT_GRAMMAR =
  "upstream-left focus-center downstream-right capital-top policy-bottom";
const DEFAULT_GRAPH_BUDGET = { max_nodes: 42, max_edges: 64, expand_nodes: 12 } as const;

const focusEntityIds: Record<FocusKey, string> = {
  materials: "00000000-0000-4000-8000-000000000023",
  equipment: "00000000-0000-4000-8000-000000000022",
  foundry: "00000000-0000-4000-8000-000000000021",
  nvidia: "00000000-0000-4000-8000-000000000006",
  business: "00000000-0000-4000-8000-000000000026",
  capital: "00000000-0000-4000-8000-000000000006",
  policy: "00000000-0000-4000-8000-000000000019",
  systems: "00000000-0000-4000-8000-000000000029",
  cloud: "00000000-0000-4000-8000-000000000030",
  datacenter: "00000000-0000-4000-8000-000000000024",
  energy: "00000000-0000-4000-8000-000000000025"
};

const systemMakersGroupMembers = [
  "Synthetic Systems Integrator",
  "Synthetic Rack Manufacturer",
  "Synthetic ODM Partner",
  "Synthetic Thermal Platform Co.",
  "Synthetic Network Appliance Co.",
  "Synthetic Storage Platform Co.",
  "Synthetic Regional Integrator",
  "Synthetic AI Factory Builder"
];

const stageRows = [
  { id: "SC-02", name: "Materials", side: "upstream" },
  { id: "SC-04", name: "Equipment", side: "upstream" },
  { id: "SC-05", name: "Design / IP", side: "focus" },
  { id: "SC-06", name: "Manufacturing", side: "upstream" },
  { id: "SC-08", name: "Advanced packaging", side: "focus" },
  { id: "SC-09", name: "System", side: "downstream" },
  { id: "SC-10", name: "Data center / Energy", side: "downstream" },
  { id: "SC-12", name: "Customer", side: "downstream" }
] as const;

const focusIndustryByKey: Record<FocusKey, { key: string; label: string }> = {
  materials: { key: "semiconductors", label: "Semiconductors" },
  equipment: { key: "semiconductors", label: "Semiconductors" },
  foundry: { key: "semiconductors", label: "Semiconductors" },
  nvidia: { key: "semiconductors", label: "Semiconductors" },
  business: { key: "semiconductors", label: "Semiconductors" },
  capital: { key: "semiconductors", label: "Semiconductors" },
  policy: { key: "semiconductors", label: "Semiconductors" },
  systems: { key: "ai-cloud", label: "AI cloud infrastructure" },
  cloud: { key: "ai-cloud", label: "AI cloud infrastructure" },
  datacenter: { key: "energy", label: "Power and data-center energy" },
  energy: { key: "energy", label: "Power and data-center energy" }
};

const homeSearchResults: HomeSearchResult[] = [
  {
    key: "nvidia",
    label: "NVIDIA Corporation",
    description: "legal_entity / AI infrastructure focus",
    aliases: ["nvda", "nvidia", "gpu", "accelerated computing"],
    target: "nvidia",
    objectType: "entity"
  },
  {
    key: "tsmc",
    label: "TSMC representative foundry",
    description: "entity / semiconductor manufacturing",
    aliases: ["tsmc", "taiwan semiconductor", "foundry", "晶圆制造"],
    target: "foundry",
    objectType: "entity"
  },
  {
    key: "semiconductors",
    label: "Semiconductors",
    description: "industry / taxonomy v4.2",
    aliases: ["semiconductor", "semiconductors", "半导体", "industry"],
    target: "nvidia",
    objectType: "industry"
  },
  {
    key: "ai-cloud",
    label: "AI cloud demand",
    description: "theme / customer and infrastructure demand",
    aliases: ["ai cloud", "cloud", "demand", "customer"],
    target: "cloud",
    objectType: "theme"
  }
];

const homeIndustries: HomeIndustryEntry[] = [
  {
    key: "semiconductors",
    name: "Semiconductors",
    taxonomy: "taxonomy-v4.2",
    entityCount: 8,
    recentChangeCount: 2,
    target: "nvidia"
  },
  {
    key: "ai-cloud",
    name: "AI cloud infrastructure",
    taxonomy: "taxonomy-v4.2",
    entityCount: 6,
    recentChangeCount: 1,
    target: "cloud"
  },
  {
    key: "energy",
    name: "Power and data-center energy",
    taxonomy: "taxonomy-v4.2",
    entityCount: 3,
    recentChangeCount: 1,
    target: "energy"
  }
];

const homeWatchItems: HomeWatchItem[] = [
  {
    key: "nvidia",
    label: "NVIDIA",
    unread: 3,
    state: "last viewed",
    savedLens: "supply_chain",
    savedZoom: "L2",
    profile: "Balanced v2"
  },
  {
    key: "foundry",
    label: "Advanced Foundry",
    unread: 2,
    state: "upstream",
    savedLens: "supply_chain",
    savedZoom: "L2",
    profile: "Balanced v2"
  },
  {
    key: "equipment",
    label: "Lithography Equipment",
    unread: 1,
    state: "supplier",
    savedLens: "supply_chain",
    savedZoom: "L1",
    profile: "Balanced v2"
  },
  {
    key: "materials",
    label: "Specialty Materials",
    unread: 1,
    state: "materials",
    savedLens: "supply_chain",
    savedZoom: "L1",
    profile: "Balanced v2"
  },
  {
    key: "cloud",
    label: "Cloud Customer",
    unread: 2,
    state: "downstream",
    savedLens: "supply_chain",
    savedZoom: "L2",
    profile: "Balanced v2"
  }
];

const homeRecentExplorations: HomeRecentEntry[] = [
  { key: "nvidia", label: "NVIDIA", path: "NVIDIA" },
  { key: "foundry", label: "Advanced Foundry", path: "NVIDIA -> Foundry" },
  { key: "equipment", label: "Lithography Equipment", path: "NVIDIA -> Foundry -> Equipment" }
];

const homeChanges: HomeChangeEntry[] = [
  { key: "capital", label: "Capital/control signal refreshed", severity: "material", target: "capital" },
  { key: "policy", label: "Policy-risk context updated", severity: "watch", target: "policy" },
  { key: "cloud", label: "Customer-demand path changed", severity: "watch", target: "cloud" }
];

const homeFreshness = {
  status: "synthetic_fixture",
  latestRelationshipObservedAt: ACTIVE_ANALYSIS_CONTEXT.defaultAsOf,
  sourceDocumentCount: 3,
  coverage: ACTIVE_ANALYSIS_CONTEXT.dataSnapshot
};

const homeModelStatus = {
  profile: ACTIVE_ANALYSIS_CONTEXT.profileLabel,
  latestCalibration: "scheduled",
  cadenceDays: 14,
  nextScheduledFor: "2026-07-03"
};

const baseEdges: MapEdge[] = [
  {
    from: "materials",
    to: "foundry",
    label: "material provider to",
    stage: "SC-02 -> SC-06",
    lens: "supply_chain",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "equipment",
    to: "foundry",
    label: "equipment provider to",
    stage: "SC-04 -> SC-06",
    lens: "supply_chain",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "foundry",
    to: "nvidia",
    label: "wafer foundry for",
    stage: "SC-06 -> SC-08",
    lens: "supply_chain",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "nvidia",
    to: "systems",
    label: "licenses IP to",
    stage: "SC-05 -> SC-09",
    lens: "supply_chain",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "systems",
    to: "cloud",
    label: "system integrator for",
    stage: "SC-09 -> SC-12",
    lens: "supply_chain",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "cloud",
    to: "nvidia",
    label: "customer of",
    stage: "SC-12 -> SC-08",
    lens: "supply_chain",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "energy",
    to: "datacenter",
    label: "energy provider to",
    stage: "SC-10 -> SC-10",
    lens: "supply_chain",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "datacenter",
    to: "cloud",
    label: "infrastructure supports",
    stage: "SC-10 -> SC-12",
    lens: "supply_chain",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  }
];

const nvidiaContextEdges: MapEdge[] = [
  {
    from: "nvidia",
    to: "business",
    label: "operates business segment",
    stage: "Business -> Focus",
    lens: "business_segments",
    fixtureNotice: "Synthetic fixture for business-segment visual coverage."
  },
  {
    from: "capital",
    to: "nvidia",
    label: "capital and control signal for",
    stage: "Capital/control -> Focus",
    lens: "capital_transactions",
    fixtureNotice: "Synthetic fixture for capital/control visual coverage."
  },
  {
    from: "policy",
    to: "nvidia",
    label: "policy risk constrains",
    stage: "Policy/risk -> Focus",
    lens: "policy_risk",
    fixtureNotice: "Synthetic fixture for policy/risk visual coverage."
  }
];

const overviewAggregateEdges: MapEdge[] = [
  {
    from: "nvidia",
    to: "systemMakersGroup",
    label: "aggregates system makers",
    stage: "SC-05 -> SC-09",
    lens: "supply_chain",
    fixtureNotice: "Synthetic grouped node for anti-hairball semantic zoom."
  },
  {
    from: "systemMakersGroup",
    to: "cloud",
    label: "group supplies systems to",
    stage: "SC-09 -> SC-12",
    lens: "supply_chain",
    fixtureNotice: "Synthetic grouped node for anti-hairball semantic zoom."
  }
];

const scenarios: Record<FocusKey, FocusScenario> = {
  nvidia: {
    focus: "nvidia",
    heading: "NVIDIA",
    subtitle: "Semiconductor and AI infrastructure ecosystem",
    nodes: [
      node("materials", 82, 336, "upstream", "SC-02 Materials", "specialty materials"),
      node("equipment", 92, 122, "upstream", "SC-04 Equipment", "lithography equipment"),
      node("foundry", 252, 224, "upstream", "SC-06 Manufacturing", "advanced foundry"),
      node("nvidia", 394, 246, "focus", "SC-05 Design / IP", "current focus"),
      node("business", 610, 76, "business", "Business segment", "accelerated computing segment"),
      node("capital", 390, 72, "capital", "Capital / control", "capital and control signal"),
      node("policy", 396, 418, "policy", "Policy / risk", "export-control context"),
      node("systems", 536, 176, "downstream", "SC-09 System", "system integration"),
      node("systemMakersGroup", 548, 180, "downstream", "SC-09 System", "aggregated system makers", {
        aggregateCount: systemMakersGroupMembers.length,
        centerable: false,
        groupMembers: systemMakersGroupMembers
      }),
      node("cloud", 650, 244, "downstream", "SC-12 Customer", "cloud customer"),
      node("datacenter", 562, 358, "infrastructure", "SC-10 Data center", "AI data center"),
      node("energy", 666, 390, "infrastructure", "SC-10 Energy", "grid utility")
    ],
    edges: [...baseEdges, ...nvidiaContextEdges],
    nextCenters: ["foundry", "systems", "cloud"]
  },
  business: {
    focus: "business",
    heading: "Synthetic Accelerated Computing Segment",
    subtitle: "Centered business-segment view with company and customer demand retained",
    nodes: [
      node("nvidia", 150, 246, "upstream", "SC-05 Design / IP", "parent platform"),
      node("business", 360, 238, "focus", "Business segment", "current focus"),
      node("systems", 540, 180, "downstream", "SC-09 System", "system route to market"),
      node("cloud", 650, 250, "downstream", "SC-12 Customer", "cloud demand")
    ],
    edges: [nvidiaContextEdges[0], baseEdges[3], baseEdges[4]],
    nextCenters: ["nvidia", "systems", "cloud"]
  },
  capital: {
    focus: "capital",
    heading: "Synthetic Capital Commitment",
    subtitle: "Centered capital/control view with company exposure retained",
    nodes: [
      node("capital", 350, 210, "focus", "Capital / control", "current focus"),
      node("nvidia", 560, 244, "downstream", "SC-05 Design / IP", "company exposure"),
      node("business", 660, 154, "downstream", "Business segment", "capital allocation target")
    ],
    edges: [nvidiaContextEdges[1], nvidiaContextEdges[0]],
    nextCenters: ["nvidia", "business"]
  },
  policy: {
    focus: "policy",
    heading: "Synthetic Export Control Context",
    subtitle: "Centered policy/risk view with constrained company and downstream demand retained",
    nodes: [
      node("policy", 340, 252, "focus", "Policy / risk", "current focus"),
      node("nvidia", 540, 238, "downstream", "SC-05 Design / IP", "constrained company"),
      node("cloud", 660, 300, "downstream", "SC-12 Customer", "demand exposure")
    ],
    edges: [nvidiaContextEdges[2], baseEdges[5]],
    nextCenters: ["nvidia", "cloud"]
  },
  foundry: {
    focus: "foundry",
    heading: "Synthetic Advanced Foundry",
    subtitle: "Centered manufacturing view with inherited supply-chain lens",
    nodes: [
      node("materials", 92, 318, "upstream", "SC-02 Materials", "specialty materials"),
      node("equipment", 104, 142, "upstream", "SC-04 Equipment", "lithography equipment"),
      node("foundry", 360, 238, "focus", "SC-06 Manufacturing", "current focus"),
      node("nvidia", 560, 238, "downstream", "SC-05 / SC-08", "design and packaging"),
      node("systems", 660, 158, "downstream", "SC-09 System", "system integration")
    ],
    edges: baseEdges.slice(0, 4),
    nextCenters: ["equipment", "materials", "nvidia"]
  },
  equipment: {
    focus: "equipment",
    heading: "Synthetic Lithography Equipment Co.",
    subtitle: "Centered equipment view with manufacturing dependency retained",
    nodes: [
      node("materials", 118, 314, "upstream", "SC-02 Materials", "material dependency"),
      node("equipment", 332, 210, "focus", "SC-04 Equipment", "current focus"),
      node("foundry", 522, 238, "downstream", "SC-06 Manufacturing", "advanced foundry"),
      node("nvidia", 650, 266, "downstream", "SC-08 Packaging", "downstream customer")
    ],
    edges: baseEdges.slice(0, 3),
    nextCenters: ["materials", "foundry", "nvidia"]
  },
  materials: {
    focus: "materials",
    heading: "Synthetic Specialty Materials Co.",
    subtitle: "Centered materials view with downstream manufacturing chain",
    nodes: [
      node("materials", 328, 240, "focus", "SC-02 Materials", "current focus"),
      node("equipment", 158, 150, "upstream", "SC-04 Equipment", "adjacent equipment"),
      node("foundry", 510, 236, "downstream", "SC-06 Manufacturing", "advanced foundry"),
      node("nvidia", 650, 284, "downstream", "SC-08 Packaging", "downstream customer")
    ],
    edges: baseEdges.slice(0, 3),
    nextCenters: ["foundry", "nvidia"]
  },
  systems: {
    focus: "systems",
    heading: "Synthetic Systems Integrator",
    subtitle: "Centered system view across customer and infrastructure stages",
    nodes: [
      node("nvidia", 138, 240, "upstream", "SC-05 Design / IP", "upstream IP"),
      node("systems", 356, 236, "focus", "SC-09 System", "current focus"),
      node("cloud", 552, 236, "downstream", "SC-12 Customer", "cloud customer"),
      node("datacenter", 566, 358, "infrastructure", "SC-10 Data center", "AI data center"),
      node("energy", 672, 392, "infrastructure", "SC-10 Energy", "grid utility")
    ],
    edges: baseEdges.slice(3),
    nextCenters: ["cloud", "nvidia"]
  },
  cloud: {
    focus: "cloud",
    heading: "Synthetic Cloud Customer",
    subtitle: "Centered customer view with system and data-center dependencies",
    nodes: [
      node("nvidia", 112, 236, "upstream", "SC-08 Packaging", "upstream platform"),
      node("systems", 260, 204, "upstream", "SC-09 System", "system integrator"),
      node("cloud", 448, 238, "focus", "SC-12 Customer", "current focus"),
      node("datacenter", 560, 350, "infrastructure", "SC-10 Data center", "AI data center"),
      node("energy", 664, 390, "infrastructure", "SC-10 Energy", "grid utility")
    ],
    edges: baseEdges.slice(3),
    nextCenters: ["systems", "datacenter", "nvidia"]
  },
  datacenter: {
    focus: "datacenter",
    heading: "Synthetic AI Data Center Campus",
    subtitle: "Centered infrastructure view",
    nodes: [
      node("energy", 132, 310, "upstream", "SC-10 Energy", "grid utility"),
      node("datacenter", 360, 240, "focus", "SC-10 Data center", "current focus"),
      node("cloud", 560, 220, "downstream", "SC-12 Customer", "cloud customer")
    ],
    edges: baseEdges.slice(6),
    nextCenters: ["energy", "cloud"]
  },
  energy: {
    focus: "energy",
    heading: "Synthetic Grid Utility",
    subtitle: "Centered energy view",
    nodes: [
      node("energy", 340, 244, "focus", "SC-10 Energy", "current focus"),
      node("datacenter", 548, 244, "downstream", "SC-10 Data center", "AI data center"),
      node("cloud", 666, 190, "downstream", "SC-12 Customer", "cloud customer")
    ],
    edges: baseEdges.slice(6),
    nextCenters: ["datacenter", "cloud"]
  }
};

function node(
  key: NodeKey,
  x: number,
  y: number,
  zone: Zone,
  stage: string,
  role: string,
  options: Partial<Pick<MapNode, "aggregateCount" | "centerable" | "groupMembers">> = {}
): MapNode {
  return {
    key,
    label: entityLabels[key],
    shortLabel: shortLabels[key],
    stage,
    role,
    x,
    y,
    zone,
    centerable: options.centerable ?? key !== "systemMakersGroup",
    aggregateCount: options.aggregateCount,
    groupMembers: options.groupMembers
  };
}

function fixtureRenderNode(mapNode: MapNode): GraphRenderNode {
  return {
    ...mapNode,
    key: mapNode.key,
    source: "fixture",
    localKey: mapNode.key,
    fixtureNotice: "Synthetic fixture visual projection."
  };
}

function fixtureRenderEdge(edge: MapEdge, observedAt: string): GraphRenderEdge {
  return {
    id: `${edge.from}-${edge.to}`,
    from: edge.from,
    to: edge.to,
    label: edge.label,
    stage: edge.stage,
    lens: edge.lens,
    fixtureNotice: edge.fixtureNotice,
    evidenceCount: 1,
    observedAt,
    source: "fixture"
  };
}

function serverGraphRenderNodes(
  graph: ExploreGraphRecord | null,
  focusEntityId: string
): GraphRenderNode[] | null {
  if (!graph || graph.nodes.length === 0) return null;
  const familyByNode = new Map<string, string>();
  for (const edge of graph.edges) {
    if (!familyByNode.has(edge.subject_id)) familyByNode.set(edge.subject_id, edge.relationship_family);
    if (!familyByNode.has(edge.object_id)) familyByNode.set(edge.object_id, edge.relationship_family);
  }
  const nodesByLane = new Map<Zone, ExploreGraphRecord["nodes"]>();
  for (const item of graph.nodes) {
    const zone = serverNodeZone(item.id, focusEntityId, item.entity_type, familyByNode.get(item.id));
    const next = nodesByLane.get(zone) ?? [];
    next.push(item);
    nodesByLane.set(zone, next);
  }
  return graph.nodes.map((item) => {
    const zone = serverNodeZone(item.id, focusEntityId, item.entity_type, familyByNode.get(item.id));
    const lane = nodesByLane.get(zone) ?? [item];
    const laneIndex = lane.findIndex((candidate) => candidate.id === item.id);
    const laneCount = lane.length;
    const position = serverNodePosition(zone, Math.max(laneIndex, 0), Math.max(laneCount, 1));
    const localKey = serverLocalKeyForEntityId(item.id);
    return {
      key: item.id,
      label: item.canonical_name,
      shortLabel: shortServerLabel(item.canonical_name),
      stage: serverNodeStage(item.entity_type, familyByNode.get(item.id)),
      role: item.id === focusEntityId ? "server focus entity" : "server returned entity",
      x: position.x,
      y: position.y,
      zone,
      centerable: Boolean(localKey),
      source: "server",
      localKey,
      entityType: item.entity_type,
      fixtureNotice: item.fixture_notice
    };
  });
}

function serverGraphRenderEdges(
  graph: ExploreGraphRecord | null,
  renderedNodes: GraphRenderNode[],
  observedAt: string
): GraphRenderEdge[] | null {
  if (!graph) return null;
  const nodeKeys = new Set(renderedNodes.map((item) => item.key));
  const edges = graph.edges
    .filter((edge) => nodeKeys.has(edge.subject_id) && nodeKeys.has(edge.object_id))
    .map((edge) => ({
      id: edge.id,
      from: edge.subject_id,
      to: edge.object_id,
      label: relationshipLabel(edge.relationship_type),
      stage: edge.relationship_family.replaceAll("_", " "),
      lens: lensForRelationshipFamily(edge.relationship_family),
      fixtureNotice: edge.fixture_notice ?? `${edge.status ?? "relationship"}; evidence=${edge.evidence_count ?? 0}`,
      evidenceCount: edge.evidence_count ?? 0,
      observedAt,
      source: "server" as const
    }));
  return edges.length > 0 ? edges : null;
}

function serverNodeZone(
  id: string,
  focusEntityId: string,
  entityType: string | undefined,
  family: string | undefined
): Zone {
  if (id === focusEntityId) return "focus";
  if (entityType === "facility" || entityType === "asset") return "infrastructure";
  if (family === "capital_financing" || family === "ownership_control" || family === "mergers_acquisitions") {
    return "capital";
  }
  if (family === "government_policy") return "policy";
  if (family === "corporate_structure" || family === "commercial_dependency") return "business";
  return "upstream";
}

function serverNodePosition(zone: Zone, index: number, count: number) {
  const clampedCount = Math.max(count, 1);
  const y = 126 + ((index + 1) * 228) / (clampedCount + 1);
  const positions: Record<Zone, { x: number; y?: number }> = {
    upstream: { x: 132 },
    focus: { x: 380, y: 240 },
    downstream: { x: 628 },
    infrastructure: { x: 628 },
    business: { x: 380, y: 92 + index * 56 },
    capital: { x: 258, y: 78 + index * 54 },
    policy: { x: 500, y: 382 - index * 52 }
  };
  const base = positions[zone];
  return { x: base.x, y: base.y ?? y };
}

function serverNodeStage(entityType: string | undefined, family: string | undefined) {
  const entity = entityType ? entityType.replaceAll("_", " ") : "entity";
  const relationship = family ? family.replaceAll("_", " ") : "relationship";
  return `${entity} / ${relationship}`;
}

function relationshipLabel(value: string) {
  return value.replaceAll("_", " ");
}

function shortServerLabel(value: string) {
  const words = value.split(/\s+/).filter(Boolean);
  const compact = words.slice(0, 3).join(" ");
  return compact.length > 22 ? `${compact.slice(0, 19)}...` : compact;
}

function lensForRelationshipFamily(family: string): RelationshipLens {
  if (["capital_financing", "ownership_control", "mergers_acquisitions"].includes(family)) {
    return "capital_transactions";
  }
  if (family === "government_policy") return "policy_risk";
  if (["corporate_structure", "commercial_dependency"].includes(family)) {
    return "business_segments";
  }
  return "supply_chain";
}

function serverLocalKeyForEntityId(entityId: string): FocusKey | undefined {
  return (Object.entries(focusEntityIds) as [FocusKey, string][]).find(([, id]) => id === entityId)?.[0];
}

const focusKeySet = new Set<FocusKey>(Object.keys(scenarios) as FocusKey[]);
const nodeKeySet = new Set<NodeKey>(Object.keys(entityLabels) as NodeKey[]);
const lensKeySet = new Set<LensKey>(lensItems.map((item) => item.key));
const semanticZoomSet = new Set<SemanticZoom>(semanticZoomItems.map((item) => item.key));
const timelineKeySet = new Set<TimelineKey>(timelineItems.map((item) => item.key));

const defaultWorkspaceState: WorkspaceState = {
  focusKey: "nvidia",
  selectedKey: "nvidia",
  path: ["nvidia"],
  activeLens: "all",
  semanticZoom: "L1",
  asOf: ACTIVE_ANALYSIS_CONTEXT.defaultAsOf
};

function isFocusKey(value: string | null | undefined): value is FocusKey {
  return Boolean(value && focusKeySet.has(value as FocusKey));
}

function isNodeKey(value: string | null | undefined): value is NodeKey {
  return Boolean(value && nodeKeySet.has(value as NodeKey));
}

function isLensKey(value: string | null | undefined): value is LensKey {
  return Boolean(value && lensKeySet.has(value as LensKey));
}

function isSemanticZoom(value: string | null | undefined): value is SemanticZoom {
  return Boolean(value && semanticZoomSet.has(value as SemanticZoom));
}

function isTimelineKey(value: string | null | undefined): value is TimelineKey {
  return Boolean(value && timelineKeySet.has(value as TimelineKey));
}

function stringField(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function normalizeWorkspaceState(input: WorkspaceStateInput): WorkspaceState {
  const focusKeyValue = stringField(input.focusKey);
  const selectedKeyValue = stringField(input.selectedKey);
  const activeLensValue = stringField(input.activeLens);
  const semanticZoomValue = stringField(input.semanticZoom);
  const asOfValue = stringField(input.asOf);
  const parsedPath = Array.isArray(input.path)
    ? input.path.filter((item): item is string => typeof item === "string").filter(isFocusKey)
    : [];
  const focusKey = isFocusKey(focusKeyValue) ? focusKeyValue : defaultWorkspaceState.focusKey;
  const selectedCandidate = isNodeKey(selectedKeyValue) ? selectedKeyValue : focusKey;
  const selectedKey = scenarios[focusKey].nodes.some((item) => item.key === selectedCandidate)
    ? selectedCandidate
    : focusKey;
  const path = parsedPath.length ? parsedPath : defaultWorkspaceState.path;
  const normalizedPath = path[path.length - 1] === focusKey ? path : [...path, focusKey];

  return {
    focusKey,
    selectedKey,
    path: normalizedPath,
    activeLens: isLensKey(activeLensValue) ? activeLensValue : defaultWorkspaceState.activeLens,
    semanticZoom: isSemanticZoom(semanticZoomValue)
      ? semanticZoomValue
      : defaultWorkspaceState.semanticZoom,
    asOf: isTimelineKey(asOfValue) ? asOfValue : defaultWorkspaceState.asOf
  };
}

function readWorkspaceStateFromParams(params: URLSearchParams): WorkspaceState | null {
  const hasState = ["subject", "selected", "lens", "zoom", "asOf", "path"].some((key) =>
    params.has(key)
  );
  if (!hasState) return null;

  return normalizeWorkspaceState({
    focusKey: params.get("subject") ?? undefined,
    selectedKey: params.get("selected") ?? undefined,
    path: (params.get("path") ?? "").split("."),
    activeLens: params.get("lens") ?? undefined,
    semanticZoom: params.get("zoom") ?? undefined,
    asOf: params.get("asOf") ?? undefined
  });
}

function readWorkspaceStatePayload(rawValue: string | null): WorkspaceState | null {
  if (!rawValue) return null;
  try {
    const parsed = JSON.parse(rawValue) as Partial<WorkspaceState>;
    return normalizeWorkspaceState(parsed);
  } catch {
    return null;
  }
}

function writeWorkspaceStateParams(params: URLSearchParams, state: WorkspaceState) {
  params.set("subject", state.focusKey);
  params.set("selected", state.selectedKey);
  params.set("lens", state.activeLens);
  params.set("zoom", state.semanticZoom);
  params.set("asOf", state.asOf);
  params.set("filters", state.activeLens);
  params.set("path", state.path.join("."));
}

function createExploreGraphRequest(
  state: WorkspaceState,
  scoringProfileVersionId?: string | null
): ExploreGraphRequest {
  return {
    focus: {
      object_type: "entity",
      object_id: focusEntityIds[state.focusKey]
    },
    active_layers: activeLayersForLens(state.activeLens),
    direction: directionForLens(state.activeLens),
    hops: hopsForSemanticZoom(state.semanticZoom),
    as_of: `${state.asOf}T00:00:00Z`,
    scoring_profile_version_id: scoringProfileVersionId ?? null,
    filters: {
      visual_lens: state.activeLens,
      semantic_zoom: state.semanticZoom,
      ui_path: state.path,
      selected_key: state.selectedKey
    },
    budget: { ...DEFAULT_GRAPH_BUDGET }
  };
}

function activeLayersForLens(lens: LensKey) {
  switch (lens) {
    case "supply_chain":
      return ["supply_chain_operations", "technology_data_ip"];
    case "business_segments":
      return ["business_segments", "commercial_dependency", "technology_data_ip"];
    case "capital_transactions":
      return ["capital_control"];
    case "policy_risk":
      return ["policy_regulatory"];
    case "all":
    default:
      return ["all"];
  }
}

function directionForLens(lens: LensKey): ExploreGraphRequest["direction"] {
  if (lens === "capital_transactions" || lens === "policy_risk") return "upstream";
  return "both";
}

function hopsForSemanticZoom(zoom: SemanticZoom) {
  return zoom === "L2" || zoom === "L3" ? 2 : 1;
}

function createSavedView(
  state: WorkspaceState,
  analysisContext: AnalysisContext = ACTIVE_ANALYSIS_CONTEXT
): SavedViewRecord {
  const normalized = normalizeWorkspaceState(state);
  return {
    ...normalized,
    id: `sv-${normalized.focusKey}-${normalized.activeLens}-${normalized.semanticZoom}-${normalized.asOf}`,
    version: SAVED_VIEW_VERSION,
    workspaceKey: SAVED_VIEW_WORKSPACE_KEY,
    filters: normalized.activeLens,
    layout: WORKSPACE_LAYOUT_GRAMMAR,
    modelVersion: analysisContext.modelVersion,
    profileVersion: analysisContext.profileVersion,
    dataSnapshot: analysisContext.dataSnapshot,
    scoreSnapshot: analysisContext.scoreSnapshot,
    notes: `${entityLabels[normalized.focusKey]} / ${normalized.activeLens} / ${normalized.asOf}`,
    updatedAt: ACTIVE_ANALYSIS_CONTEXT.defaultAsOf,
    syncMode: "local_fallback",
    syncReason: "not_synced"
  };
}

function readSavedViewPayload(rawValue: string | null): SavedViewRecord | null {
  if (!rawValue) return null;
  try {
    const parsed = JSON.parse(rawValue) as Partial<SavedViewRecord>;
    if (parsed.version !== SAVED_VIEW_VERSION) return null;
    const base = createSavedView(normalizeWorkspaceState(parsed));
    return {
      ...base,
      id: parsed.id ?? base.id,
      workspaceKey: parsed.workspaceKey ?? SAVED_VIEW_WORKSPACE_KEY,
      filters: parsed.filters ?? base.filters,
      layout: parsed.layout ?? base.layout,
      modelVersion: parsed.modelVersion ?? base.modelVersion,
      profileVersion: parsed.profileVersion ?? base.profileVersion,
      dataSnapshot: parsed.dataSnapshot ?? base.dataSnapshot,
      scoreSnapshot: parsed.scoreSnapshot ?? base.scoreSnapshot,
      notes: parsed.notes ?? base.notes,
      updatedAt: parsed.updatedAt ?? ACTIVE_ANALYSIS_CONTEXT.defaultAsOf,
      serverId: stringField(parsed.serverId),
      serverVersion:
        typeof parsed.serverVersion === "number" && Number.isFinite(parsed.serverVersion)
          ? parsed.serverVersion
          : undefined,
      syncMode: parsed.syncMode === "server" ? "server" : "local_fallback",
      syncReason: parsed.syncReason ?? "local_record",
      serverEndpoint: stringField(parsed.serverEndpoint)
    };
  } catch {
    return null;
  }
}

function createSavedViewServerState(savedViewRecord: SavedViewRecord): Record<string, unknown> {
  return {
    local_id: savedViewRecord.id,
    focus_key: savedViewRecord.focusKey,
    selected_key: savedViewRecord.selectedKey,
    path: savedViewRecord.path,
    visual_lens: savedViewRecord.activeLens,
    semantic_zoom: savedViewRecord.semanticZoom,
    as_of: savedViewRecord.asOf,
    filters: savedViewRecord.filters,
    layout: savedViewRecord.layout,
    model_version: savedViewRecord.modelVersion,
    profile_version: savedViewRecord.profileVersion,
    data_snapshot: savedViewRecord.dataSnapshot,
    score_snapshot: savedViewRecord.scoreSnapshot,
    notes: savedViewRecord.notes
  };
}

function createSavedViewMetadata(savedViewRecord: SavedViewRecord): Record<string, unknown> {
  return {
    source: "eei-web",
    workspace_key: savedViewRecord.workspaceKey,
    local_id: savedViewRecord.id,
    model_version: savedViewRecord.modelVersion,
    profile_version: savedViewRecord.profileVersion,
    data_snapshot: savedViewRecord.dataSnapshot,
    score_snapshot: savedViewRecord.scoreSnapshot
  };
}

function workspaceStateFromServerState(state: Record<string, unknown>): WorkspaceState {
  const rawPath = state.path;
  const path =
    Array.isArray(rawPath) || typeof rawPath === "string"
      ? Array.isArray(rawPath)
        ? rawPath
        : rawPath.split(".")
      : undefined;
  return normalizeWorkspaceState({
    focusKey: state.focus_key ?? state.focusKey,
    selectedKey: state.selected_key ?? state.selectedKey,
    path,
    activeLens: state.visual_lens ?? state.activeLens,
    semanticZoom: state.semantic_zoom ?? state.semanticZoom,
    asOf: state.as_of ?? state.asOf
  });
}

function savedViewFromServerRecord(
  record: SavedViewServerRecord,
  endpoint: string,
  analysisContext: AnalysisContext
): SavedViewRecord {
  const serverState = record.state;
  const base = createSavedView(workspaceStateFromServerState(serverState), analysisContext);
  return {
    ...base,
    id: stringField(serverState.local_id) ?? base.id,
    workspaceKey: record.workspace_key,
    filters: stringField(serverState.filters) ?? base.filters,
    layout: stringField(serverState.layout) ?? base.layout,
    modelVersion: stringField(serverState.model_version) ?? base.modelVersion,
    profileVersion: stringField(serverState.profile_version) ?? base.profileVersion,
    dataSnapshot: stringField(serverState.data_snapshot) ?? base.dataSnapshot,
    scoreSnapshot: stringField(serverState.score_snapshot) ?? base.scoreSnapshot,
    notes: stringField(serverState.notes) ?? record.name ?? base.notes,
    updatedAt: record.updated_at ?? base.updatedAt,
    serverId: record.id,
    serverVersion: record.current_version,
    syncMode: "server",
    syncReason: "ok",
    serverEndpoint: endpoint
  };
}

function analysisContextFromActiveModelContext(
  record: ActiveModelContextRecord,
  fallback: AnalysisContext
): AnalysisContext {
  return {
    ...fallback,
    modelVersion: record.model_version,
    profileVersion: record.profile_version,
    profileLabel: record.profile_version,
    dataSnapshot: record.active_data_snapshot_key ?? fallback.dataSnapshot,
    scoreSnapshot: record.active_scoring_run_id ?? fallback.scoreSnapshot
  };
}

function isFailedServerSyncResult(
  result: SavedViewSyncResult
): result is Extract<SavedViewSyncResult, { mode: "server"; status: "conflict" | "error" }> {
  return result.mode === "server" && (result.status === "conflict" || result.status === "error");
}

function isFailedModelActivationResult(
  result: ModelActivationResult
): result is Extract<ModelActivationResult, { mode: "server"; status: "conflict" | "error" }> {
  return result.mode === "server" && (result.status === "conflict" || result.status === "error");
}

export default function Home() {
  const { analysisContext, applyPreview, applyServerContext, clearPreview, isPreviewActive } =
    useAnalysisContext();
  const [focusKey, setFocusKey] = useState<FocusKey>("nvidia");
  const [selectedKey, setSelectedKey] = useState<NodeKey>("nvidia");
  const [path, setPath] = useState<FocusKey[]>(["nvidia"]);
  const [activeLens, setActiveLens] = useState<LensKey>("all");
  const [semanticZoom, setSemanticZoom] = useState<SemanticZoom>("L1");
  const [asOf, setAsOf] = useState<TimelineKey>(ACTIVE_ANALYSIS_CONTEXT.defaultAsOf);
  const [transitionState, setTransitionState] = useState<TransitionState>("ready");
  const [groupListOpen, setGroupListOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [savedView, setSavedView] = useState<SavedViewRecord>(() =>
    createSavedView(defaultWorkspaceState)
  );
  const [savedViewStatus, setSavedViewStatus] = useState("ready");
  const [modelContextStatus, setModelContextStatus] =
    useState<ModelContextStatus>("local-active");
  const [productionGraphStatus, setProductionGraphStatus] =
    useState<ProductionGraphStatus>("local-fixture");
  const [productionGraphSyncMode, setProductionGraphSyncMode] = useState<
    "server" | "local_fallback"
  >("local_fallback");
  const [productionGraphSyncReason, setProductionGraphSyncReason] = useState("not_synced");
  const [productionGraphEndpoint, setProductionGraphEndpoint] = useState("");
  const [productionGraph, setProductionGraph] = useState<ExploreGraphRecord | null>(null);
  const [selectedProductionNodeKey, setSelectedProductionNodeKey] = useState("");
  const [modelContextSyncMode, setModelContextSyncMode] = useState<"server" | "local_fallback">(
    "local_fallback"
  );
  const [modelContextSyncReason, setModelContextSyncReason] = useState("not_synced");
  const [serverModelContext, setServerModelContext] = useState<ActiveModelContextRecord | null>(
    null
  );
  const [modelContextEndpoint, setModelContextEndpoint] = useState("");
  const [candidateProfile, setCandidateProfile] = useState<ScoringProfileRecord | null>(null);
  const [rollbackProfile, setRollbackProfile] = useState<ScoringProfileRecord | null>(null);
  const [previousModelRefreshToken, setPreviousModelRefreshToken] = useState("");
  const [pinnedNodeKeys, setPinnedNodeKeys] = useState<NodeKey[]>([]);
  const [comparisonNodeKeys, setComparisonNodeKeys] = useState<NodeKey[]>([]);
  const [watchlistNodeKeys, setWatchlistNodeKeys] = useState<NodeKey[]>([]);
  const [tableLensFilter, setTableLensFilter] = useState<LensKey>("all");
  const [nodeActionStatus, setNodeActionStatus] = useState("ready");
  const [navActionStatus, setNavActionStatus] = useState("ready");
  const [stateReady, setStateReady] = useState(false);
  const restoringHistoryState = useRef(false);
  const hasWrittenHistoryState = useRef(false);
  const scenario = scenarios[focusKey];
  const workspaceState = useMemo<WorkspaceState>(
    () => ({ focusKey, selectedKey, path, activeLens, semanticZoom, asOf }),
    [activeLens, asOf, focusKey, path, selectedKey, semanticZoom]
  );
  const productionGraphRequest = useMemo(
    () =>
      createExploreGraphRequest(
        workspaceState,
        serverModelContext?.active_scoring_profile_version_id
      ),
    [serverModelContext?.active_scoring_profile_version_id, workspaceState]
  );
  const workspaceContextValue = useMemo(
    () =>
      createWorkspaceContextValue({
        ...workspaceState,
        analysisContext
      }),
    [analysisContext, workspaceState]
  );
  const currentTimeline = timelineItems.find((item) => item.key === asOf) ?? timelineItems[2];
  const nodeByKey = useMemo(
    () => new Map(scenario.nodes.map((item) => [item.key, item])),
    [scenario.nodes]
  );
  const displayNodes = useMemo(() => {
    if (focusKey !== "nvidia" || semanticZoom !== "L0") {
      return scenario.nodes.filter((item) => item.key !== "systemMakersGroup");
    }
    return scenario.nodes.filter(
      (item) => !["systems", "datacenter", "energy"].includes(item.key)
    );
  }, [focusKey, scenario.nodes, semanticZoom]);
  const displayNodeByKey = useMemo(
    () => new Map(displayNodes.map((item) => [item.key, item])),
    [displayNodes]
  );
  const displayEdges = useMemo(() => {
    if (focusKey !== "nvidia" || semanticZoom !== "L0") {
      return scenario.edges;
    }
    const groupedKeys = new Set<NodeKey>(["systems", "datacenter", "energy"]);
    return [
      ...scenario.edges.filter((edge) => !groupedKeys.has(edge.from) && !groupedKeys.has(edge.to)),
      ...overviewAggregateEdges
    ];
  }, [focusKey, scenario.edges, semanticZoom]);
  const fixtureGraphNodes = useMemo(() => displayNodes.map(fixtureRenderNode), [displayNodes]);
  const fixtureGraphEdges = useMemo(
    () => displayEdges.map((edge) => fixtureRenderEdge(edge, asOf)),
    [asOf, displayEdges]
  );
  const serverGraphNodes = useMemo(
    () => serverGraphRenderNodes(productionGraph, productionGraphRequest.focus.object_id),
    [productionGraph, productionGraphRequest.focus.object_id]
  );
  const serverGraphEdges = useMemo(
    () => serverGraphRenderEdges(productionGraph, serverGraphNodes ?? [], asOf),
    [asOf, productionGraph, serverGraphNodes]
  );
  const isServerGraphRendered =
    productionGraphStatus === "server-hydrated" &&
    Boolean(serverGraphNodes?.length) &&
    Boolean(serverGraphEdges?.length);
  const graphViewNodes = isServerGraphRendered ? serverGraphNodes! : fixtureGraphNodes;
  const graphViewEdges = isServerGraphRendered ? serverGraphEdges! : fixtureGraphEdges;
  const graphViewNodeByKey = useMemo(
    () => new Map(graphViewNodes.map((item) => [item.key, item])),
    [graphViewNodes]
  );
  const graphViewMode = isServerGraphRendered ? "server" : "fixture";
  const productionContext = productionGraph?.production_context;
  const productionCoverage = productionGraph?.coverage;
  const productionCandidateCoverage = productionCoverage?.relationship_fact_candidates;
  const productionCandidateSummary = productionContext?.candidate_fact_summary;
  const productionPublishedRelationships =
    productionContext?.record_modes?.published_relationships;
  const productionGraphBudget = productionGraph?.query.budget ?? productionGraphRequest.budget;
  const tableEdges = useMemo(
    () =>
      tableLensFilter === "all"
        ? graphViewEdges
        : graphViewEdges.filter((edge) => edge.lens === tableLensFilter),
    [graphViewEdges, tableLensFilter]
  );
  const activeEdgeKeys = useMemo(() => {
    const keys = new Set<string>([isServerGraphRendered ? productionGraphRequest.focus.object_id : focusKey]);
    for (const edge of graphViewEdges) {
      if (activeLens === "all" || edge.lens === activeLens) {
        keys.add(edge.from);
        keys.add(edge.to);
      }
    }
    return keys;
  }, [activeLens, focusKey, graphViewEdges, isServerGraphRendered, productionGraphRequest.focus.object_id]);
  const selectedNode =
    nodeByKey.get(selectedKey) ?? nodeByKey.get(scenario.focus) ?? scenario.nodes[0];
  const selectedGraphNode =
    graphViewMode === "server"
      ? graphViewNodeByKey.get(selectedProductionNodeKey) ??
        graphViewNodeByKey.get(productionGraphRequest.focus.object_id) ??
        graphViewNodes[0]
      : graphViewNodeByKey.get(selectedNode.key) ?? fixtureRenderNode(selectedNode);
  const industryPath = useMemo(() => {
    const ordered: { key: string; label: string }[] = [];
    for (const key of path) {
      const industry = focusIndustryByKey[key];
      if (ordered[ordered.length - 1]?.key !== industry.key) {
        ordered.push(industry);
      }
    }
    return ordered;
  }, [path]);
  const industryPathLabel = industryPath.map((item) => item.label).join(" -> ");
  const isCrossIndustryPath = industryPath.length > 1;
  const upstreamCandidate = useMemo(
    () => scenario.edges.find((edge) => edge.to === selectedNode.key && nodeByKey.has(edge.from))?.from,
    [nodeByKey, scenario.edges, selectedNode.key]
  );
  const downstreamCandidate = useMemo(
    () =>
      scenario.edges.find((edge) => edge.from === selectedNode.key && nodeByKey.has(edge.to))?.to,
    [nodeByKey, scenario.edges, selectedNode.key]
  );

  function applyWorkspaceState(nextState: WorkspaceStateInput) {
    const normalized = normalizeWorkspaceState(nextState);
    setFocusKey(normalized.focusKey);
    setSelectedKey(normalized.selectedKey);
    setPath(normalized.path);
    setActiveLens(normalized.activeLens);
    setSemanticZoom(normalized.semanticZoom);
    setAsOf(normalized.asOf);
    setGroupListOpen(false);
    setTransitionState("ready");
  }

  function applyPathSubject(pathIndex: number) {
    const nextFocus = path[pathIndex];
    if (!nextFocus) return;
    applyWorkspaceState({
      ...workspaceState,
      focusKey: nextFocus,
      selectedKey: nextFocus,
      path: path.slice(0, pathIndex + 1)
    });
  }

  function browserBack() {
    window.history.back();
  }

  async function saveCurrentView() {
    setSavedViewStatus("saving");
    const nextSavedView = createSavedView(workspaceState, analysisContext);
    const syncResult = await saveViewToServer({
      name: nextSavedView.notes,
      description: "EEI workspace saved view",
      state: createSavedViewServerState(nextSavedView),
      metadata: createSavedViewMetadata(nextSavedView),
      serverId: savedView.serverId,
      expectedVersion: savedView.serverVersion
    });
    let syncedSavedView: SavedViewRecord;
    if (syncResult.mode === "server" && syncResult.status === "saved") {
      syncedSavedView = savedViewFromServerRecord(
        syncResult.record,
        syncResult.endpoint,
        analysisContext
      );
    } else if (isFailedServerSyncResult(syncResult)) {
      syncedSavedView = {
        ...nextSavedView,
        serverId: savedView.serverId,
        serverVersion: savedView.serverVersion,
        syncMode: "server",
        syncReason: syncResult.reason,
        serverEndpoint: syncResult.endpoint
      };
    } else if (syncResult.mode === "local_fallback") {
      syncedSavedView = {
        ...nextSavedView,
        serverId: savedView.serverId,
        serverVersion: savedView.serverVersion,
        syncMode: "local_fallback",
        syncReason: syncResult.reason
      };
    } else {
      syncedSavedView = {
        ...nextSavedView,
        serverId: savedView.serverId,
        serverVersion: savedView.serverVersion,
        syncMode: "server",
        syncReason: "unexpected_saved_view_sync_status",
        serverEndpoint: syncResult.endpoint
      };
    }

    window.localStorage.setItem(SAVED_VIEW_STORAGE_KEY, JSON.stringify(syncedSavedView));
    setSavedView(syncedSavedView);
    setSavedViewStatus(
      syncResult.mode === "server"
        ? syncResult.status === "saved"
          ? "server-saved"
          : syncResult.status === "conflict"
            ? "server-conflict"
            : "server-error"
        : "local-saved"
    );
  }

  async function restoreSavedView() {
    setSavedViewStatus("restoring");
    const storedSavedView = readSavedViewPayload(window.localStorage.getItem(SAVED_VIEW_STORAGE_KEY));
    const nextSavedView = storedSavedView ?? savedView;
    const syncResult = await restoreViewFromServer(nextSavedView.serverId);
    if (syncResult.mode === "server" && syncResult.status === "restored") {
      const serverSavedView = savedViewFromServerRecord(
        syncResult.record,
        syncResult.endpoint,
        analysisContext
      );
      window.localStorage.setItem(SAVED_VIEW_STORAGE_KEY, JSON.stringify(serverSavedView));
      setSavedView(serverSavedView);
      restoringHistoryState.current = true;
      applyWorkspaceState(serverSavedView);
      setSavedViewStatus("server-restored");
      return;
    }

    if (syncResult.mode === "local_fallback") {
      const localSavedView: SavedViewRecord = {
        ...nextSavedView,
        syncMode: "local_fallback",
        syncReason: syncResult.reason
      };
      window.localStorage.setItem(SAVED_VIEW_STORAGE_KEY, JSON.stringify(localSavedView));
      setSavedView(localSavedView);
      restoringHistoryState.current = true;
      applyWorkspaceState(localSavedView);
      setSavedViewStatus("local-restored");
      return;
    }

    if (!isFailedServerSyncResult(syncResult)) return;

    const failedSavedView: SavedViewRecord = {
      ...nextSavedView,
      syncMode: "server",
      syncReason: syncResult.reason,
      serverEndpoint: syncResult.endpoint
    };
    window.localStorage.setItem(SAVED_VIEW_STORAGE_KEY, JSON.stringify(failedSavedView));
    setSavedView(failedSavedView);
    setSavedViewStatus(syncResult.status === "conflict" ? "server-conflict" : "server-error");
  }

  async function resolveSavedViewConflict() {
    setSavedViewStatus("resolving-conflict");
    const syncResult = await restoreViewFromServer(savedView.serverId);
    if (syncResult.mode === "server" && syncResult.status === "restored") {
      const serverSavedView = {
        ...savedViewFromServerRecord(syncResult.record, syncResult.endpoint, analysisContext),
        syncReason: "resolved_latest"
      };
      window.localStorage.setItem(SAVED_VIEW_STORAGE_KEY, JSON.stringify(serverSavedView));
      setSavedView(serverSavedView);
      restoringHistoryState.current = true;
      applyWorkspaceState(serverSavedView);
      setSavedViewStatus("server-conflict-resolved");
      return;
    }
    if (syncResult.mode === "local_fallback") {
      setSavedViewStatus("local-restored");
      return;
    }
    if (!isFailedServerSyncResult(syncResult)) return;
    setSavedView({
      ...savedView,
      syncMode: "server",
      syncReason: syncResult.reason,
      serverEndpoint: syncResult.endpoint
    });
    setSavedViewStatus(syncResult.status === "conflict" ? "server-conflict" : "server-error");
  }

  async function hydrateProductionGraph(reason = "manual_refresh") {
    setProductionGraphStatus("loading-production-graph");
    const graphResult = await loadExploreGraph(productionGraphRequest);
    if (graphResult.mode === "local_fallback") {
      setProductionGraphSyncMode("local_fallback");
      setProductionGraphSyncReason(graphResult.reason);
      setProductionGraphEndpoint("");
      setProductionGraphStatus("local-fixture");
      return;
    }
    if (graphResult.status === "error") {
      setProductionGraphSyncMode("server");
      setProductionGraphSyncReason(graphResult.reason);
      setProductionGraphEndpoint(graphResult.endpoint);
      setProductionGraphStatus("server-error");
      return;
    }
    setProductionGraph(graphResult.record);
    setSelectedProductionNodeKey(graphResult.record.query.focus.object_id);
    setProductionGraphSyncMode("server");
    setProductionGraphSyncReason(reason);
    setProductionGraphEndpoint(graphResult.endpoint);
    setProductionGraphStatus("server-hydrated");
  }

  async function hydrateModelContext(clientRefreshToken?: string, reason = "manual_refresh") {
    setModelContextStatus("loading-server-context");
    const contextResult = await loadActiveModelContext(clientRefreshToken);
    if (contextResult.mode === "local_fallback") {
      setModelContextSyncMode("local_fallback");
      setModelContextSyncReason(contextResult.reason);
      setModelContextStatus("local-active");
      return;
    }
    if (contextResult.status === "error") {
      setModelContextSyncMode("server");
      setModelContextSyncReason(contextResult.reason);
      setModelContextEndpoint(contextResult.endpoint);
      setModelContextStatus("server-error");
      return;
    }

    applyServerContext(
      analysisContextFromActiveModelContext(contextResult.record, ACTIVE_ANALYSIS_CONTEXT)
    );
    setServerModelContext(contextResult.record);
    setModelContextSyncMode("server");
    setModelContextSyncReason(
      contextResult.status === "stale" ? "stale_client_refetched" : reason
    );
    setModelContextEndpoint(contextResult.endpoint);
    setModelContextStatus(
      contextResult.status === "stale" && clientRefreshToken
        ? "server-refreshed"
        : contextResult.status === "stale"
          ? "server-stale"
          : "server-current"
    );

    const profileResult = await listModelProfiles();
    if (profileResult.mode === "server" && profileResult.status === "listed") {
      const nextCandidate =
        profileResult.profiles.find((profile) => !profile.active) ??
        profileResult.profiles.find(
          (profile) => profile.id !== contextResult.record.active_scoring_profile_version_id
        ) ??
        null;
      setCandidateProfile(nextCandidate);
    }
  }

  async function activateCandidateModelProfile() {
    await activateModelProfileTransaction(candidateProfile, "EEI model-center transaction activation");
  }

  async function rollbackLatestModelActivation() {
    await activateModelProfileTransaction(rollbackProfile, "EEI model-center rollback activation");
  }

  async function activateModelProfileTransaction(
    targetProfile: ScoringProfileRecord | null,
    reason: string
  ) {
    if (!targetProfile) {
      setModelContextSyncReason("target_profile_missing");
      setModelContextStatus("server-no-target");
      return;
    }
    setModelContextStatus("activating");
    const activationResult = await activateModelProfile({
      targetProfileVersionId: targetProfile.id,
      expectedActiveProfileVersionId: serverModelContext?.active_scoring_profile_version_id,
      clientRefreshToken: serverModelContext?.refresh_token,
      reason
    });
    if (activationResult.mode === "local_fallback") {
      setModelContextSyncMode("local_fallback");
      setModelContextSyncReason(activationResult.reason);
      setModelContextStatus("server-error");
      return;
    }
    if (isFailedModelActivationResult(activationResult)) {
      setModelContextSyncMode("server");
      setModelContextSyncReason(activationResult.reason);
      setModelContextEndpoint(activationResult.endpoint);
      setModelContextStatus(
        activationResult.status === "conflict" ? "server-conflict" : "server-error"
      );
      return;
    }

    const nextContext = activationResult.response.active_context;
    applyServerContext(analysisContextFromActiveModelContext(nextContext, ACTIVE_ANALYSIS_CONTEXT));
    setPreviousModelRefreshToken(
      activationResult.response.cache_invalidation.previous_refresh_token ?? ""
    );
    setServerModelContext(nextContext);
    setCandidateProfile(activationResult.response.previous_profile);
    setRollbackProfile(activationResult.response.previous_profile);
    setModelContextSyncMode("server");
    setModelContextSyncReason("activation_transaction_committed");
    setModelContextEndpoint(activationResult.endpoint);
    setModelContextStatus("server-activated");
  }

  const viewportAnchor = `${focusKey}:${selectedNode.key}:${semanticZoom}`;
  const visibleSearchResults = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return homeSearchResults.slice(0, 3);
    }
    return homeSearchResults.filter((result) =>
      [result.label, result.description, ...result.aliases].some((value) =>
        value.toLowerCase().includes(normalizedQuery)
      )
    );
  }, [searchQuery]);

  function requestCenter(nextFocus: string) {
    setTransitionState("loading");
    window.setTimeout(() => {
      if (!(nextFocus in scenarios)) {
        setTransitionState("fallback");
        return;
      }
      const validFocus = nextFocus as FocusKey;
      setFocusKey(validFocus);
      setSelectedKey(validFocus);
      setPath((current) =>
        current[current.length - 1] === validFocus ? current : [...current, validFocus]
      );
      setGroupListOpen(false);
      setTransitionState("ready");
    }, 360);
  }

  function setCenter(nextFocus: FocusKey) {
    requestCenter(nextFocus);
  }

  function inspectNode(nextSelected: NodeKey) {
    setSelectedKey(nextSelected);
    setGroupListOpen(false);
  }

  function inspectGraphNode(nextSelected: GraphRenderNode) {
    if (nextSelected.source === "server") {
      setSelectedProductionNodeKey(nextSelected.key);
    }
    if (nextSelected.localKey) {
      inspectNode(nextSelected.localKey);
      return;
    }
    setSelectedProductionNodeKey(nextSelected.key);
    setNodeActionStatus(`server-inspect:${nextSelected.key}`);
    setGroupListOpen(false);
  }

  function addUniqueNode(current: NodeKey[], key: NodeKey) {
    return current.includes(key) ? current : [...current, key];
  }

  function pinSelectedNode() {
    setPinnedNodeKeys((current) => addUniqueNode(current, selectedNode.key));
    setNodeActionStatus(`pinned:${selectedNode.key}`);
  }

  function compareSelectedNode() {
    setComparisonNodeKeys((current) => addUniqueNode(current, selectedNode.key).slice(-4));
    setNodeActionStatus(`compare:${selectedNode.key}`);
  }

  function addSelectedNodeToWatchlist() {
    setWatchlistNodeKeys((current) => addUniqueNode(current, selectedNode.key));
    setNodeActionStatus(`watchlist:${selectedNode.key}`);
  }

  function applyWorkspaceNavigationLens(lens: string, moduleId: WorkspaceModuleId) {
    if (!isLensKey(lens)) return;
    setActiveLens(lens);
    setNavActionStatus(`lens:${moduleId}:${lens}`);
  }

  function applyWorkspaceNavigationSection(sectionTestId: string, moduleId: WorkspaceModuleId) {
    const section = document.querySelector<HTMLElement>(`[data-testid="${sectionTestId}"]`);
    section?.scrollIntoView({ block: "nearest", inline: "nearest" });
    section?.focus?.({ preventScroll: true });
    setNavActionStatus(`section:${moduleId}:${sectionTestId}`);
  }

  function openSelectedPath() {
    setNodeActionStatus(`path:${selectedNode.key}`);
  }

  function openSelectedEvidence() {
    setNodeActionStatus(`evidence:${selectedNode.key}`);
  }

  function handleNodeKeyDown(event: KeyboardEvent<SVGGElement>, nextSelected: GraphRenderNode) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      inspectGraphNode(nextSelected);
    }
  }

  function resetToNvidia() {
    setFocusKey("nvidia");
    setSelectedKey("nvidia");
    setPath(["nvidia"]);
    setGroupListOpen(false);
    setTransitionState("ready");
  }

  function restoreWatchItem(item: HomeWatchItem) {
    setActiveLens(item.savedLens);
    setSemanticZoom(item.savedZoom);
    setCenter(item.key);
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const firstResult = visibleSearchResults[0] ?? homeSearchResults[0];
    setCenter(firstResult.target);
  }

  useEffect(() => {
    const urlState = readWorkspaceStateFromParams(new URLSearchParams(window.location.search));
    const sessionState = readWorkspaceStatePayload(
      window.sessionStorage.getItem(WORKSPACE_STATE_STORAGE_KEY)
    );
    const storedSavedView = readSavedViewPayload(window.localStorage.getItem(SAVED_VIEW_STORAGE_KEY));

    if (storedSavedView) {
      setSavedView(storedSavedView);
    }
    if (urlState ?? sessionState) {
      restoringHistoryState.current = true;
      applyWorkspaceState((urlState ?? sessionState)!);
    }

    function handlePopState(event: PopStateEvent) {
      const eventState = event.state as { eeiWorkspaceState?: WorkspaceStateInput } | null;
      const nextState =
        readWorkspaceStateFromParams(new URLSearchParams(window.location.search)) ??
        (eventState?.eeiWorkspaceState
          ? normalizeWorkspaceState(eventState.eeiWorkspaceState)
          : null);
      if (!nextState) return;
      restoringHistoryState.current = true;
      applyWorkspaceState(nextState);
    }

    window.addEventListener("popstate", handlePopState);
    setStateReady(true);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    void hydrateModelContext(undefined, "initial_hydration");
  }, []);

  useEffect(() => {
    void hydrateProductionGraph("initial_hydration");
  }, []);

  useEffect(() => {
    if (!stateReady) return;
    const normalized = normalizeWorkspaceState(workspaceState);
    const payload = JSON.stringify(normalized);
    window.sessionStorage.setItem(WORKSPACE_STATE_STORAGE_KEY, payload);
    window.localStorage.setItem(WORKSPACE_STATE_STORAGE_KEY, payload);

    const nextUrl = new URL(window.location.href);
    writeWorkspaceStateParams(nextUrl.searchParams, normalized);
    const historyState = { eeiWorkspaceState: normalized };
    const shouldReplace = restoringHistoryState.current || !hasWrittenHistoryState.current;
    if (shouldReplace) {
      window.history.replaceState(historyState, "", nextUrl);
      restoringHistoryState.current = false;
      hasWrittenHistoryState.current = true;
      return;
    }
    window.history.pushState(historyState, "", nextUrl);
  }, [stateReady, workspaceState]);

  useEffect(() => {
    function handleExternalCenterRequest(event: Event) {
      const detail = (event as CustomEvent<string | { focus?: string }>).detail;
      const nextFocus = typeof detail === "string" ? detail : detail?.focus;
      if (nextFocus) {
        requestCenter(nextFocus);
      }
    }

    window.addEventListener("eei:request-center", handleExternalCenterRequest);
    return () => window.removeEventListener("eei:request-center", handleExternalCenterRequest);
  });

  return (
    <WorkspaceContextProvider value={workspaceContextValue}>
    <main
      className="workspace"
      data-active-data-snapshot={analysisContext.dataSnapshot}
      data-active-lens={activeLens}
      data-active-model-version={analysisContext.modelVersion}
      data-active-profile-version={analysisContext.profileVersion}
      data-active-score-snapshot={analysisContext.scoreSnapshot}
      data-active-time={asOf}
      data-analysis-contract={analysisContext.contractVersion}
      data-focus-key={focusKey}
      data-layout-grammar={WORKSPACE_LAYOUT_GRAMMAR}
      data-last-nav-action={navActionStatus}
      data-path={path.join(".")}
      data-path-length={path.length}
      data-reroot-state={transitionState}
      data-selected-node={selectedNode.key}
      data-semantic-zoom={semanticZoom}
      data-testid="workspace-shell"
      data-viewport-anchor={viewportAnchor}
      data-workspace-model="recursive-enterprise-map"
    >
      <WorkspaceContextContractMarker />
      <WorkspaceNavigationRail
        activeLens={activeLens}
        activeModuleId="business_map"
        onLensTarget={applyWorkspaceNavigationLens}
        onSectionTarget={applyWorkspaceNavigationSection}
      />

      <section className="focusPanel" aria-label="当前主体">
        <div className="subjectHeader">
          <div>
            <p className="eyebrow">Watchlist current focus</p>
            <h1 data-testid="current-focus-title">{scenario.heading}</h1>
            <p className="subjectSubtitle">{scenario.subtitle}</p>
          </div>
          <span className="snapshotTag">Synthetic fixture</span>
        </div>
        <dl className="subjectStats" data-testid="home-model-status">
          <div>
            <dt>Snapshot</dt>
            <dd>{analysisContext.dataSnapshot}</dd>
          </div>
          <div>
            <dt>Model</dt>
            <dd>{analysisContext.profileLabel}</dd>
          </div>
          <div>
            <dt>Budget</dt>
            <dd data-testid="graph-budget">
              {graphViewNodes.length} / {graphViewEdges.length}
            </dd>
          </div>
          <div>
            <dt>Model review</dt>
            <dd>
              {homeModelStatus.latestCalibration} / {homeModelStatus.cadenceDays}d /{" "}
              {homeModelStatus.nextScheduledFor}
            </dd>
          </div>
        </dl>
        <section
          className="modelPreviewPanel"
          data-active-profile-id={serverModelContext?.active_scoring_profile_version_id ?? "local"}
          data-api-base-storage-key={MODEL_CONTEXT_API_BASE_STORAGE_KEY}
          data-client-state={serverModelContext?.client_state ?? "local"}
          data-model-endpoint={modelContextEndpoint || "local"}
          data-model-refresh-generation={serverModelContext?.refresh_generation ?? 0}
          data-model-refresh-token={serverModelContext?.refresh_token ?? "local"}
          data-model-sync-mode={modelContextSyncMode}
          data-model-sync-reason={modelContextSyncReason}
          data-preview-scope="workspace,graph-table,saved-view,industry-landscape"
          data-preview-state={isPreviewActive ? "preview" : "active"}
          data-preview-storage={ANALYSIS_PREVIEW_STORAGE_KEY}
          data-rollback-profile-id={rollbackProfile?.id ?? "none"}
          data-target-profile-id={candidateProfile?.id ?? "none"}
          data-testid="model-preview-panel"
        >
          <div>
            <strong>Model preview</strong>
            <span data-testid="model-preview-status">
              {analysisContext.profileLabel} / {analysisContext.scoreSnapshot}
            </span>
          </div>
          <div>
            <strong>Model activation</strong>
            <span data-testid="model-activation-status">{modelContextStatus}</span>
          </div>
          <div>
            <strong>Refresh context</strong>
            <span data-testid="model-server-context-state">
              {modelContextSyncMode} / {serverModelContext?.refresh_generation ?? 0} /{" "}
              {serverModelContext?.client_state ?? "local"} / {modelContextSyncReason}
            </span>
          </div>
          <div className="modelPreviewActions">
            <button data-testid="preview-model-edit" onClick={applyPreview} type="button">
              Preview supply-chain emphasis
            </button>
            <button data-testid="clear-model-preview" onClick={clearPreview} type="button">
              Clear preview
            </button>
            <button
              data-testid="hydrate-model-context"
              onClick={() => void hydrateModelContext(undefined, "manual_refresh")}
              type="button"
            >
              Load server context
            </button>
            <button
              data-testid="activate-model-profile"
              disabled={!candidateProfile || modelContextStatus === "activating"}
              onClick={() => void activateCandidateModelProfile()}
              type="button"
            >
              Activate profile
            </button>
            <button
              data-testid="check-model-refresh"
              disabled={!previousModelRefreshToken && !serverModelContext}
              onClick={() =>
                void hydrateModelContext(
                  previousModelRefreshToken || serverModelContext?.refresh_token,
                  "manual_refresh"
                )
              }
              type="button"
            >
              Check refresh
            </button>
            <button
              data-testid="rollback-model-activation"
              disabled={!rollbackProfile || modelContextStatus === "activating"}
              onClick={() => void rollbackLatestModelActivation()}
              type="button"
            >
              Rollback
            </button>
          </div>
        </section>
        <section
          className="modelPreviewPanel productionGraphPanel"
          data-api-base-storage-key={EXPLORE_API_BASE_STORAGE_KEY}
          data-candidate-total-count={
            productionCandidateSummary?.total ?? productionCandidateCoverage?.total ?? 0
          }
          data-graph-endpoint={productionGraphEndpoint || "local"}
          data-graph-query-version={productionContext?.graph_query_version ?? "local"}
          data-graph-sync-mode={productionGraphSyncMode}
          data-graph-sync-reason={productionGraphSyncReason}
          data-min-independent-sources={
            productionContext?.publication_policy?.minimum_independent_sources ?? 0
          }
          data-published-relationship-count={productionPublishedRelationships?.total ?? 0}
          data-query-as-of={productionGraphRequest.as_of ?? "none"}
          data-query-budget={`${productionGraphBudget.max_nodes}/${productionGraphBudget.max_edges}/${productionGraphBudget.expand_nodes}`}
          data-query-direction={productionGraphRequest.direction}
          data-query-focus-id={productionGraphRequest.focus.object_id}
          data-query-hops={productionGraphRequest.hops}
          data-query-layers={productionGraphRequest.active_layers.join(",")}
          data-relationship-candidate-excluded-count={
            productionCandidateCoverage?.excluded_from_graph_edges ?? 0
          }
          data-relationship-candidates-in-graph={String(
            productionContext?.publication_policy?.relationship_fact_candidates_in_graph_edges ??
              false
          )}
          data-render-source={graphViewMode}
          data-scoring-service-version={productionContext?.scoring_service_version ?? "local"}
          data-server-edge-count={productionGraph?.edges.length ?? 0}
          data-server-node-count={productionGraph?.nodes.length ?? 0}
          data-server-session-id={productionGraph?.session_id ?? "none"}
          data-synthetic-fixture-edge-count={
            productionCoverage?.synthetic_fixture_edges ?? displayEdges.length
          }
          data-testid="production-graph-context"
          data-visible-edge-count={productionCoverage?.visible_edges ?? displayEdges.length}
          data-visible-node-count={productionCoverage?.visible_nodes ?? displayNodes.length}
          data-visual-edge-count={graphViewEdges.length}
          data-visual-node-count={graphViewNodes.length}
        >
          <div>
            <strong>Production graph</strong>
            <span data-testid="production-graph-status">{productionGraphStatus}</span>
          </div>
          <div>
            <strong>Query contract</strong>
            <span data-testid="production-graph-query">
              {productionGraphRequest.focus.object_id} /{" "}
              {productionGraphRequest.active_layers.join(",")} /{" "}
              {productionGraphRequest.direction} / {productionGraphRequest.hops} hop
            </span>
          </div>
          <div>
            <strong>Server coverage</strong>
            <span data-testid="production-graph-coverage">
              {productionCoverage?.visible_nodes ?? displayNodes.length} nodes /{" "}
              {productionCoverage?.visible_edges ?? displayEdges.length} edges /{" "}
              {productionCoverage?.source_count ?? 0} sources
            </span>
          </div>
          <dl data-testid="production-graph-contract">
            <div>
              <dt>Budget</dt>
              <dd data-testid="production-graph-budget">
                {productionGraphBudget.max_nodes} / {productionGraphBudget.max_edges} /{" "}
                {productionGraphBudget.expand_nodes}
              </dd>
            </div>
            <div>
              <dt>Context</dt>
              <dd>
                {productionContext?.graph_query_version ?? "local-fixture"} /{" "}
                {productionContext?.scoring_service_version ?? "local-score"}
              </dd>
            </div>
            <div>
              <dt>Publication state</dt>
              <dd data-testid="production-graph-publication-gate">
                candidates-in-graph=
                {String(
                  productionContext?.publication_policy
                    ?.relationship_fact_candidates_in_graph_edges ?? false
                )}{" "}
                / min-sources=
                {productionContext?.publication_policy?.minimum_independent_sources ?? 0}
              </dd>
            </div>
            <div>
              <dt>Candidate facts</dt>
              <dd data-testid="production-graph-candidates">
                excluded={productionCandidateCoverage?.excluded_from_graph_edges ?? 0} / total=
                {productionCandidateSummary?.total ?? productionCandidateCoverage?.total ?? 0}
              </dd>
            </div>
          </dl>
          <div className="modelPreviewActions">
            <button
              data-testid="hydrate-production-graph"
              onClick={() => void hydrateProductionGraph("manual_refresh")}
              type="button"
            >
              Load production graph
            </button>
          </div>
        </section>
        <div
          className="fixtureDisclosure"
          data-testid="fixture-disclosure"
          data-freshness-status={homeFreshness.status}
        >
          <strong>Fixture-only data</strong>
          <span>Visible synthetic notices are required; no live fact claim is shown.</span>
        </div>

        <section
          aria-label="公司八层视图"
          className="workspaceLayerStrip"
          data-layer-count={workspaceLayerItems.length}
          data-required-layers={workspaceLayerItems.map((item) => item.key).join(",")}
          data-testid="workspace-layer-strip"
        >
          <header>
            <span>八层视图</span>
            <small>{workspaceLayerItems.length}/8</small>
          </header>
          <div>
            {workspaceLayerItems.map((item) => (
              <button
                data-layer-key={item.key}
                data-layer-state={item.state}
                data-testid={`workspace-layer-${item.key}`}
                key={item.key}
                onClick={() => {
                  if (item.key === "business_segments" || item.key === "group_structure") {
                    setActiveLens("business_segments");
                  } else if (item.key === "supply_chain") {
                    setActiveLens("supply_chain");
                  } else if (item.key === "capital_network") {
                    setActiveLens("capital_transactions");
                  } else if (item.key === "policy_environment") {
                    setActiveLens("policy_risk");
                  }
                }}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>
        </section>

        <section
          aria-label="集团结构与业务板块"
          className="structureMatrix"
          data-api-contract="/v1/entities/{entityId}/empire"
          data-commercial-empire-control-claim="false"
          data-separates="legal_group,business_segment,brand,product,facility"
          data-testid="company-structure-matrix"
        >
          <header>
            <span>集团结构</span>
            <small>商业版图不是法律控制声明</small>
          </header>
          <table>
            <thead>
              <tr>
                <th scope="col">对象</th>
                <th scope="col">类型</th>
                <th scope="col">关系</th>
                <th scope="col">控制语义</th>
              </tr>
            </thead>
            <tbody>
              {structureRows.map((row) => (
                <tr
                  data-control-claim="false"
                  data-relationship={row.relationship}
                  data-scope={row.scope}
                  data-structure-kind={row.kind}
                  data-testid={`structure-row-${row.kind}`}
                  key={row.kind}
                >
                  <td>{row.label}</td>
                  <td>{row.typeLabel}</td>
                  <td>{row.relationship}</td>
                  <td>{row.control}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <form
          aria-label="全局搜索"
          className="homeSearch"
          data-endpoint="/v1/entities"
          data-primary-actions-to-focus="2"
          data-supported-types="legal_entity,industry,theme,facility"
          data-testid="home-global-search"
          onSubmit={submitSearch}
          role="search"
        >
          <label htmlFor="global-search-input">全局搜索</label>
          <div className="searchInputRow">
            <Search size={16} aria-hidden="true" />
            <input
              autoComplete="off"
              data-testid="global-search-input"
              id="global-search-input"
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="NVIDIA, TSMC, 半导体"
              type="search"
              value={searchQuery}
            />
            <button data-testid="global-search-submit" type="submit">
              打开
            </button>
          </div>
          <div className="searchResults" data-testid="global-search-results">
            {visibleSearchResults.map((result) => (
              <button
                data-object-type={result.objectType}
                data-testid={`search-result-${result.key}`}
                key={result.key}
                onClick={() => setCenter(result.target)}
                type="button"
              >
                <span>{result.label}</span>
                <small>{result.description}</small>
              </button>
            ))}
          </div>
        </form>

        <section className="homeSection" aria-label="行业入口" data-testid="home-industries">
          <header>
            <span>行业</span>
            <a data-testid="home-industry-map-link" href="/industries">
              地图
            </a>
          </header>
          <div className="compactList">
            {homeIndustries.map((industry) => (
              <button
                data-testid={`home-industry-${industry.key}`}
                key={industry.key}
                onClick={() => setCenter(industry.target)}
                type="button"
              >
                <span>{industry.name}</span>
                <small>
                  {industry.entityCount} entities / {industry.recentChangeCount} changes
                </small>
              </button>
            ))}
          </div>
        </section>

        <section className="homeSection" aria-label="关注主体" data-testid="home-watchlist">
          <header>
            <span>我的关注</span>
            <small>{homeWatchItems.reduce((total, item) => total + item.unread, 0)} unread</small>
          </header>
          <div className="watchlistStack">
            {homeWatchItems.map((item) => (
            <button
              className={item.key === focusKey ? "watchItem current" : "watchItem"}
              data-testid={`home-watchlist-${item.key}`}
              key={item.key}
              onClick={() => restoreWatchItem(item)}
              type="button"
            >
              <span>{item.label}</span>
              <small data-testid={`watchlist-saved-state-${item.key}`}>
                {item.unread} unread / {item.state} / {item.savedLens} / {item.savedZoom} /{" "}
                {item.profile}
              </small>
              <Route size={16} aria-hidden="true" />
            </button>
          ))}
          </div>
        </section>

        <section className="homeSection" aria-label="最近探索" data-testid="home-recent-explorations">
          <header>
            <span>探索记录</span>
            <small>{homeRecentExplorations.length}</small>
          </header>
          <div className="compactList">
            {homeRecentExplorations.map((entry) => (
              <button
                data-testid={`home-recent-${entry.key}`}
                key={entry.key}
                onClick={() => setCenter(entry.key)}
                type="button"
              >
                <span>{entry.label}</span>
                <small>{entry.path}</small>
              </button>
            ))}
          </div>
        </section>

        <section className="homeSection" aria-label="重要变化" data-testid="home-changes">
          <header>
            <span>重要变化</span>
            <small>{homeChanges.length}</small>
          </header>
          <div className="compactList">
            {homeChanges.map((change) => (
              <button
                data-testid={`home-change-${change.key}`}
                key={change.key}
                onClick={() => setCenter(change.target)}
                type="button"
              >
                <span>{change.label}</span>
                <small>{change.severity}</small>
              </button>
            ))}
          </div>
        </section>

        <div className="freshnessGrid" data-testid="home-freshness">
          <span>{homeFreshness.status}</span>
          <span>{homeFreshness.latestRelationshipObservedAt}</span>
          <span>{homeFreshness.sourceDocumentCount} sources</span>
          <span>{analysisContext.dataSnapshot}</span>
        </div>
      </section>

      <section className="canvas" aria-label="商业版图" data-testid="visual-canvas">
        <div className="canvasTopbar">
          <div>
            <p className="eyebrow">Golden Vertical</p>
            <h2>Semiconductor and AI infrastructure ecosystem</h2>
          </div>
          <div className="lensBar" aria-label="分析视角">
            {lensItems.map((lens) => (
              <button
                aria-pressed={activeLens === lens.key}
                className={activeLens === lens.key ? "lens active" : "lens"}
                data-testid={`lens-${lens.key}`}
                key={lens.key}
                onClick={() => setActiveLens(lens.key)}
                type="button"
              >
                {lens.label}
              </button>
            ))}
          </div>
        </div>
        <div
          className="zoomBar"
          aria-label="语义缩放"
          data-testid="semantic-zoom-controls"
          data-zoom-contract="L0,L1,L2,L3"
        >
          {semanticZoomItems.map((item) => (
            <button
              aria-pressed={semanticZoom === item.key}
              className={semanticZoom === item.key ? "zoomControl active" : "zoomControl"}
              data-testid={`zoom-${item.key}`}
              key={item.key}
              onClick={() => setSemanticZoom(item.key)}
              title={item.title}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>

        <div
          className="timelineBar"
          aria-label="时间演变"
          data-active-as-of={asOf}
          data-testid="timeline-controls"
        >
          {timelineItems.map((item) => (
            <button
              aria-pressed={asOf === item.key}
              className={asOf === item.key ? "timelineControl active" : "timelineControl"}
              data-testid={`timeline-${item.key}`}
              key={item.key}
              onClick={() => setAsOf(item.key)}
              type="button"
            >
              <span>{item.label}</span>
              <small>{item.key}</small>
            </button>
          ))}
        </div>

        <div className="stageRail" aria-label="供应链阶段覆盖">
          {stageRows.map((stage) => (
            <span className={`stagePill ${stage.side}`} key={stage.id}>
              {stage.id} {stage.name}
            </span>
          ))}
        </div>

        <div className="mapSurface" data-testid="ecosystem-map-surface">
          {transitionState === "loading" ? (
            <div className="canvasOverlay" data-testid="transition-loading">
              Loading relationship map
            </div>
          ) : null}
          {transitionState === "fallback" ? (
            <div className="canvasOverlay warning" data-testid="transition-fallback">
              Canvas preserved
            </div>
          ) : null}
          <div
            className="changeOverlay"
            data-as-of={asOf}
            data-testid="change-overlay"
            data-timeline-mode="as-of-snapshot"
          >
            <strong>As of {asOf}</strong>
            <span>{currentTimeline.change}</span>
            <small>{currentTimeline.overlay}; not real-time.</small>
          </div>
          <svg
            className={`ecosystemMap zoom-${semanticZoom}`}
            data-render-source={graphViewMode}
            data-semantic-zoom={semanticZoom}
            data-server-rendered-edge-count={graphViewMode === "server" ? graphViewEdges.length : 0}
            data-server-rendered-node-count={graphViewMode === "server" ? graphViewNodes.length : 0}
            data-testid="ecosystem-map-svg"
            viewBox="0 0 760 480"
            role="img"
            aria-label={
              graphViewMode === "server"
                ? "EEI server recursive relationship map"
                : "NVIDIA synthetic recursive supply-chain graph"
            }
          >
            <defs>
              <marker
                id="arrow"
                markerHeight="8"
                markerWidth="8"
                orient="auto"
                refX="7"
                refY="4"
                viewBox="0 0 8 8"
              >
                <path d="M0,0 L8,4 L0,8 z" />
              </marker>
            </defs>
            {graphViewEdges.map((edge) => {
              const source = graphViewNodeByKey.get(edge.from);
              const target = graphViewNodeByKey.get(edge.to);
              if (!source || !target) return null;
              const midX = (source.x + target.x) / 2;
              const midY = (source.y + target.y) / 2 - 10;
              const lensState = activeLens === "all" || edge.lens === activeLens ? "active" : "faded";
              return (
                <g
                  className={`edgeGroup ${lensState}`}
                  data-lens-state={lensState}
                  data-render-source={edge.source}
                  data-testid={`edge-group-${edge.from}-${edge.to}`}
                  key={edge.id}
                >
                  <line
                    className="edge"
                    data-testid={`edge-${edge.from}-${edge.to}`}
                    markerEnd="url(#arrow)"
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                  />
                  <text
                    className="edgeLabel"
                    data-testid={`edge-label-${edge.from}-${edge.to}`}
                    textAnchor="middle"
                    x={midX}
                    y={midY}
                  >
                    {edge.label}
                  </text>
                  {semanticZoom === "L2" || semanticZoom === "L3" ? (
                    <text className="edgeEvidence" textAnchor="middle" x={midX} y={midY + 16}>
                      {edge.source === "server" ? `${edge.evidenceCount} sources` : "fixture evidence"}
                    </text>
                  ) : null}
                </g>
              );
            })}
            {graphViewNodes.map((mapNode) => {
              const lensState =
                activeLens === "all" || activeEdgeKeys.has(mapNode.key) ? "active" : "faded";
              const isSelected = mapNode.key === selectedGraphNode.key;
              const isFocus =
                mapNode.key ===
                (graphViewMode === "server" ? productionGraphRequest.focus.object_id : focusKey);
              return (
              <g
                aria-label={`Inspect ${mapNode.label}`}
                aria-pressed={isSelected}
                className={`node ${mapNode.zone} ${lensState}${isSelected ? " selected" : ""}`}
                data-aggregate-count={mapNode.aggregateCount}
                data-lens-state={lensState}
                data-node-kind={mapNode.aggregateCount ? "aggregate" : "entity"}
                data-render-source={mapNode.source}
                data-testid={`graph-node-${mapNode.key}`}
                key={mapNode.key}
                onClick={() => inspectGraphNode(mapNode)}
                onKeyDown={(event) => handleNodeKeyDown(event, mapNode)}
                role="button"
                tabIndex={0}
                transform={`translate(${mapNode.x} ${mapNode.y})`}
              >
                <circle r={isFocus ? 40 : 31} />
                <text textAnchor="middle" dominantBaseline="middle">
                  {mapNode.aggregateCount ? `${mapNode.shortLabel} ${mapNode.aggregateCount}` : mapNode.shortLabel}
                </text>
                <text className="nodeStage" textAnchor="middle" y={52}>
                  {mapNode.stage}
                </text>
                {semanticZoom === "L3" ? (
                  <text className="nodeRole" textAnchor="middle" y={68}>
                    {mapNode.role}
                  </text>
                ) : null}
              </g>
              );
            })}
          </svg>
        </div>

        <div className="historyControls" aria-label="历史恢复">
          <button data-testid="app-back" onClick={browserBack} type="button">
            <ChevronLeft size={16} aria-hidden="true" />
            <span>返回</span>
          </button>
        </div>

        <ol className="breadcrumb" aria-label="探索路径" data-testid="reroot-breadcrumb">
          {path.map((key, index) => (
            <li key={`${key}-${index}`}>
              <button
                aria-current={index === path.length - 1 ? "page" : undefined}
                data-testid={`breadcrumb-subject-${key}-${index}`}
                onClick={() => applyPathSubject(index)}
                type="button"
              >
                {key === "nvidia" ? "NVIDIA" : entityLabels[key]}
              </button>
            </li>
          ))}
        </ol>

        <section
          className="crossIndustryReroot"
          data-cross-industry={isCrossIndustryPath}
          data-industry-path={industryPath.map((item) => item.key).join(">")}
          data-testid="cross-industry-reroot-notice"
        >
          <strong>Cross-industry path</strong>
          <span>{industryPathLabel}</span>
          <small>
            {isCrossIndustryPath
              ? `已从 ${industryPath[0]?.label} 进入 ${industryPath[industryPath.length - 1]?.label}`
              : "当前路径仍在单一行业内"}
          </small>
        </section>
      </section>

      <aside className="inspector" aria-label="证据与状态" data-testid="evidence-center">
        <div className="inspectorHeader">
          <p className="eyebrow">Evidence Center</p>
          <h2>Relationship path</h2>
        </div>

        <section
          className="selectedNodeCard"
          aria-label="当前选择节点"
          data-render-source={selectedGraphNode.source}
          data-selected-graph-node={selectedGraphNode.key}
          data-testid="selected-node-card"
        >
          <span className={`nodeToken ${selectedGraphNode.zone}`}>{selectedGraphNode.zone}</span>
          <h3 data-testid="selected-node-title">{selectedGraphNode.label}</h3>
          <dl>
            <div>
              <dt>Stage</dt>
              <dd>{selectedGraphNode.stage}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{selectedGraphNode.role}</dd>
            </div>
            <div>
              <dt>Current subject</dt>
              <dd>{scenario.heading}</dd>
            </div>
          </dl>
        </section>

        <section
          className="savedViewPanel"
          data-api-base-storage-key={SAVED_VIEW_API_BASE_STORAGE_KEY}
          data-data-snapshot={savedView.dataSnapshot}
          data-model-version={savedView.modelVersion}
          data-profile-version={savedView.profileVersion}
          data-saved-view-id={savedView.id}
          data-server-endpoint={savedView.serverEndpoint ?? ""}
          data-server-id={savedView.serverId ?? ""}
          data-server-version={savedView.serverVersion ?? ""}
          data-saved-view-version={savedView.version}
          data-score-snapshot={savedView.scoreSnapshot}
          data-sync-mode={savedView.syncMode}
          data-sync-reason={savedView.syncReason}
          data-testid="saved-view-panel"
          data-workspace-key={savedView.workspaceKey}
        >
          <header>
            <p className="eyebrow">Saved View</p>
            <strong data-testid="saved-view-status">{savedViewStatus}</strong>
          </header>
          <dl data-testid="saved-view-contract">
            <div>
              <dt>Subject</dt>
              <dd>{entityLabels[savedView.focusKey]}</dd>
            </div>
            <div>
              <dt>Lens / Time</dt>
              <dd>
                {savedView.activeLens} / {savedView.asOf}
              </dd>
            </div>
            <div>
              <dt>Filters</dt>
              <dd>{savedView.filters}</dd>
            </div>
            <div>
              <dt>Layout</dt>
              <dd>{savedView.layout}</dd>
            </div>
            <div>
              <dt>Notes</dt>
              <dd>{savedView.notes}</dd>
            </div>
          </dl>
          <div className="savedViewActions">
            <button data-testid="save-current-view" onClick={saveCurrentView} type="button">
              <Save size={16} aria-hidden="true" />
              <span>保存</span>
            </button>
            <button data-testid="restore-saved-view" onClick={restoreSavedView} type="button">
              <RotateCcw size={16} aria-hidden="true" />
              <span>恢复</span>
            </button>
            {savedViewStatus === "server-conflict" && savedView.serverId ? (
              <button
                data-testid="resolve-saved-view-conflict"
                onClick={resolveSavedViewConflict}
                type="button"
              >
                <RotateCcw size={16} aria-hidden="true" />
                <span>获取最新</span>
              </button>
            ) : null}
          </div>
        </section>

        <ol className="pathList">
          {scenario.edges.slice(0, 4).map((edge) => (
            <li key={`${edge.from}-${edge.to}`}>
              <strong>{`${nodeByKey.get(edge.from)?.shortLabel ?? edge.from} -> ${
                nodeByKey.get(edge.to)?.shortLabel ?? edge.to
              }`}</strong>
              <span>{edge.stage}</span>
              <em>Synthetic fixture</em>
              <small>{edge.fixtureNotice}</small>
            </li>
          ))}
        </ol>

        <section
          className="graphPolicyPanel"
          data-continuation-endpoint="/v1/explore/expand"
          data-sort-keys="active-lens,evidence,confidence,observed_at,id"
          data-testid="inclusion-truncation-explanation"
          data-truncation-contract="edge_budget,node_budget,returned_counts,continuation"
        >
          <header>
            <p className="eyebrow">Inclusion policy</p>
            <strong>Bounded relationship set</strong>
          </header>
          <dl>
            <div>
              <dt>Included first</dt>
              <dd>Active lens, evidence-bearing edges, confidence, observed time, stable id</dd>
            </div>
            <div>
              <dt>Truncation</dt>
              <dd>edge_budget and node_budget return reasons, counts and continuation metadata</dd>
            </div>
            <div>
              <dt>Continuation</dt>
              <dd>/v1/explore/expand preserves the current focus and loads a bounded increment</dd>
            </div>
          </dl>
        </section>

        <section
          className="graphTablePanel"
          data-accessibility-equivalent="graph-relationships"
          data-color-independent-encoding="labels,arrows,stages,roles,evidence"
          data-equivalent-fields="direction,type,evidence_status,observed_at"
          data-testid="graph-table-alternative"
        >
          <header>
            <p className="eyebrow">Graph Table</p>
            <label htmlFor="graph-table-lens-filter">Lens</label>
            <select
              data-testid="graph-table-filter"
              id="graph-table-lens-filter"
              onChange={(event) => setTableLensFilter(event.target.value as LensKey)}
              value={tableLensFilter}
            >
              {lensItems.map((lens) => (
                <option key={lens.key} value={lens.key}>
                  {lens.label}
                </option>
              ))}
            </select>
          </header>
          <p
            className="visualSemanticsNotice"
            data-color-independent-encoding="labels,arrows,stages,roles,evidence"
            data-control-semantics="layout-position-not-control"
            data-testid="visual-semantics-notice"
          >
            Layout position is visual focus only; relationship labels, arrows, stages, roles and
            evidence carry semantics.
          </p>
          <table>
            <thead>
              <tr>
                <th scope="col">From</th>
                <th scope="col">To</th>
                <th scope="col">Direction</th>
                <th scope="col">Type</th>
                <th scope="col">Relationship</th>
                <th scope="col">Stage</th>
                <th scope="col">Evidence</th>
                <th scope="col">Time</th>
              </tr>
            </thead>
            <tbody>
              {tableEdges.map((edge) => (
                <tr
                  data-direction={`${edge.from}->${edge.to}`}
                  data-evidence-status={edge.source === "server" ? "server-evidence" : "fixture-evidence"}
                  data-lens={edge.lens}
                  data-observed-at={edge.observedAt}
                  data-render-source={edge.source}
                  data-relationship-type={edge.lens}
                  data-testid={`graph-table-row-${edge.from}-${edge.to}`}
                  key={edge.id}
                >
                  <td>{graphViewNodeByKey.get(edge.from)?.shortLabel ?? edge.from}</td>
                  <td>{graphViewNodeByKey.get(edge.to)?.shortLabel ?? edge.to}</td>
                  <td>{`${graphViewNodeByKey.get(edge.from)?.shortLabel ?? edge.from} -> ${
                    graphViewNodeByKey.get(edge.to)?.shortLabel ?? edge.to
                  }`}</td>
                  <td>{edge.lens.replaceAll("_", " ")}</td>
                  <td>
                    <span>{edge.label}</span>
                    <small>{edge.fixtureNotice}</small>
                  </td>
                  <td>{edge.stage}</td>
                  <td>
                    <span className="evidencePill">
                      {edge.source === "server" ? `${edge.evidenceCount} sources` : "fixture evidence"}
                    </span>
                  </td>
                  <td>{edge.observedAt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <div className="actionStack" aria-label="主体操作">
          <button
            className="primaryAction"
            data-testid="primary-set-center"
            disabled={!selectedGraphNode.localKey || !selectedGraphNode.centerable || selectedGraphNode.localKey === focusKey}
            onClick={() =>
              selectedGraphNode.localKey &&
              selectedGraphNode.centerable &&
              setCenter(selectedGraphNode.localKey as FocusKey)
            }
            type="button"
          >
            <Crosshair size={16} aria-hidden="true" />
            <span>以 {selectedGraphNode.label} 为中心</span>
          </button>
          <button
            data-testid="node-action-upstream"
            disabled={graphViewMode === "server" || !upstreamCandidate}
            onClick={() => upstreamCandidate && inspectNode(upstreamCandidate)}
            type="button"
          >
            <ArrowUp size={16} aria-hidden="true" />
            <span>展开上游</span>
          </button>
          <button
            data-testid="node-action-downstream"
            disabled={graphViewMode === "server" || !downstreamCandidate}
            onClick={() => downstreamCandidate && inspectNode(downstreamCandidate)}
            type="button"
          >
            <ArrowDown size={16} aria-hidden="true" />
            <span>展开下游</span>
          </button>
          <button
            data-testid="node-action-pin"
            disabled={!selectedGraphNode.localKey}
            onClick={pinSelectedNode}
            type="button"
          >
            <Star size={16} aria-hidden="true" />
            <span>固定节点</span>
          </button>
          <button
            data-testid="node-action-compare"
            disabled={!selectedGraphNode.localKey}
            onClick={compareSelectedNode}
            type="button"
          >
            <GitBranch size={16} aria-hidden="true" />
            <span>加入比较</span>
          </button>
          <button
            data-testid="node-action-watchlist"
            disabled={!selectedGraphNode.localKey}
            onClick={addSelectedNodeToWatchlist}
            type="button"
          >
            <Star size={16} aria-hidden="true" />
            <span>加入关注</span>
          </button>
          <button data-testid="node-action-path" onClick={openSelectedPath} type="button">
            <Route size={16} aria-hidden="true" />
            <span>查看路径</span>
          </button>
          <button data-testid="node-action-evidence" onClick={openSelectedEvidence} type="button">
            <FileSearch size={16} aria-hidden="true" />
            <span>打开证据</span>
          </button>
          {selectedNode.groupMembers ? (
            <button data-testid="open-group-list" onClick={() => setGroupListOpen((open) => !open)} type="button">
              <Boxes size={16} aria-hidden="true" />
              <span>查看组列表</span>
            </button>
          ) : null}
          {scenario.nextCenters.map((key) => (
            <button key={key} onClick={() => setCenter(key)} type="button">
              <Network size={16} aria-hidden="true" />
              <span>以 {entityLabels[key]} 为中心</span>
            </button>
          ))}
          <button onClick={resetToNvidia} type="button">
            <Route size={16} aria-hidden="true" />
            <span>回到 NVIDIA</span>
          </button>
        </div>

        <section
          className="nodeActionState"
          data-compare-count={comparisonNodeKeys.length}
          data-pinned-count={pinnedNodeKeys.length}
          data-testid="node-action-state"
          data-watchlist-count={watchlistNodeKeys.length}
        >
          <div>
            <strong>Pinned</strong>
            <span data-testid="pinned-node-list">
              {pinnedNodeKeys.map((key) => entityLabels[key]).join(" / ") || "none"}
            </span>
          </div>
          <div>
            <strong>Compare</strong>
            <span data-testid="comparison-node-list">
              {comparisonNodeKeys.map((key) => entityLabels[key]).join(" / ") || "none"}
            </span>
          </div>
          <div>
            <strong>Watchlist</strong>
            <span data-testid="watchlist-node-list">
              {watchlistNodeKeys.map((key) => entityLabels[key]).join(" / ") || "none"}
            </span>
          </div>
          <small data-testid="node-action-status">{nodeActionStatus}</small>
        </section>

        {selectedNode.groupMembers && groupListOpen ? (
          <ol className="groupList" data-testid="group-list">
            {selectedNode.groupMembers.map((member) => (
              <li key={member}>{member}</li>
            ))}
          </ol>
        ) : null}

        <div className="statusStrip">
          <span>Data: synthetic fixture</span>
          <span>Live facts: disabled</span>
          <span>DB fixture notice: visible</span>
          <span data-testid="model-contract-state">
            Model: {analysisContext.modelVersion} / Preference: {analysisContext.profileVersion} /
            Formula: {analysisContext.formulaRegistryVersion} / Parameters:{" "}
            {analysisContext.parameterCatalogVersion} / Thresholds:{" "}
            {analysisContext.thresholdRegistryVersion}
          </span>
          <span data-testid="active-context-state">
            Data: {analysisContext.dataSnapshot} / Score: {analysisContext.scoreSnapshot} / As of:{" "}
            {asOf}
          </span>
          <span data-testid="lens-state">Lens: {activeLens}</span>
          <span data-testid="zoom-state">Zoom: {semanticZoom}</span>
          <span data-testid="reroot-state">Canvas state: {transitionState}</span>
          <span data-testid="budget-state">
            Budget: {graphViewNodes.length} nodes / {graphViewEdges.length} edges / max 40 first-screen edges
          </span>
        </div>
      </aside>
    </main>
    </WorkspaceContextProvider>
  );
}
