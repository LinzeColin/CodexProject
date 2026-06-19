"use client";

import { useEffect, useMemo, useState, type KeyboardEvent } from "react";
import {
  Activity,
  ArrowDown,
  ArrowUp,
  Bell,
  Boxes,
  Building2,
  CircleDollarSign,
  Clock3,
  Crosshair,
  Database,
  FileSearch,
  GitBranch,
  Landmark,
  Network,
  PackageSearch,
  Route,
  Scale,
  Settings2,
  ShieldCheck,
  Star
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

type NavItem = {
  name: string;
  icon: LucideIcon;
  active?: boolean;
};

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

type FocusScenario = {
  focus: FocusKey;
  heading: string;
  subtitle: string;
  nodes: MapNode[];
  edges: MapEdge[];
  nextCenters: FocusKey[];
};

const navItems: NavItem[] = [
  { name: "商业版图", icon: Network, active: true },
  { name: "集团结构", icon: Building2 },
  { name: "业务板块", icon: Boxes },
  { name: "供应链", icon: PackageSearch },
  { name: "资本网络", icon: CircleDollarSign },
  { name: "并购交易", icon: GitBranch },
  { name: "控制关系", icon: ShieldCheck },
  { name: "政策环境", icon: Landmark },
  { name: "战略信号", icon: Activity },
  { name: "时间演变", icon: Clock3 },
  { name: "证据中心", icon: FileSearch },
  { name: "模型中心", icon: Settings2 },
  { name: "数据中心", icon: Database },
  { name: "我的关注", icon: Bell },
  { name: "探索记录", icon: Route },
  { name: "系统状态", icon: Scale }
];

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

const semanticZoomItems: { key: SemanticZoom; label: string; title: string }[] = [
  { key: "L0", label: "L0", title: "Overview with grouped dense nodes" },
  { key: "L1", label: "L1", title: "Relationship labels" },
  { key: "L2", label: "L2", title: "Evidence and fixture state" },
  { key: "L3", label: "L3", title: "Detailed node role labels" }
];

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
    subtitle: "Rerooted business-segment view with focus company and customer demand retained",
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
    subtitle: "Rerooted capital/control view with focus-company exposure retained",
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
    subtitle: "Rerooted policy/risk view with constrained company and downstream demand retained",
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
    subtitle: "Rerooted manufacturing view with inherited supply-chain lens",
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
    subtitle: "Rerooted equipment view with manufacturing dependency retained",
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
    subtitle: "Rerooted materials view with downstream manufacturing chain",
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
    subtitle: "Rerooted system view across customer and infrastructure stages",
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
    subtitle: "Rerooted customer view with system and data-center dependencies",
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
    subtitle: "Rerooted infrastructure view",
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
    subtitle: "Rerooted energy view",
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

export default function Home() {
  const [focusKey, setFocusKey] = useState<FocusKey>("nvidia");
  const [selectedKey, setSelectedKey] = useState<NodeKey>("nvidia");
  const [path, setPath] = useState<FocusKey[]>(["nvidia"]);
  const [activeLens, setActiveLens] = useState<LensKey>("all");
  const [semanticZoom, setSemanticZoom] = useState<SemanticZoom>("L1");
  const [transitionState, setTransitionState] = useState<TransitionState>("ready");
  const [groupListOpen, setGroupListOpen] = useState(false);
  const scenario = scenarios[focusKey];
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
  const activeEdgeKeys = useMemo(() => {
    const keys = new Set<NodeKey>([focusKey]);
    for (const edge of displayEdges) {
      if (activeLens === "all" || edge.lens === activeLens) {
        keys.add(edge.from);
        keys.add(edge.to);
      }
    }
    return keys;
  }, [activeLens, displayEdges, focusKey]);
  const selectedNode =
    nodeByKey.get(selectedKey) ?? nodeByKey.get(scenario.focus) ?? scenario.nodes[0];
  const upstreamCandidate = useMemo(
    () => scenario.edges.find((edge) => edge.to === selectedNode.key && nodeByKey.has(edge.from))?.from,
    [nodeByKey, scenario.edges, selectedNode.key]
  );
  const downstreamCandidate = useMemo(
    () =>
      scenario.edges.find((edge) => edge.from === selectedNode.key && nodeByKey.has(edge.to))?.to,
    [nodeByKey, scenario.edges, selectedNode.key]
  );

  const viewportAnchor = `${focusKey}:${selectedNode.key}:${semanticZoom}`;

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
    }, 160);
  }

  function setCenter(nextFocus: FocusKey) {
    requestCenter(nextFocus);
  }

  function inspectNode(nextSelected: NodeKey) {
    setSelectedKey(nextSelected);
    setGroupListOpen(false);
  }

  function handleNodeKeyDown(event: KeyboardEvent<SVGGElement>, nextSelected: NodeKey) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      inspectNode(nextSelected);
    }
  }

  function resetToNvidia() {
    setFocusKey("nvidia");
    setSelectedKey("nvidia");
    setPath(["nvidia"]);
    setGroupListOpen(false);
    setTransitionState("ready");
  }

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
    <main
      className="workspace"
      data-active-lens={activeLens}
      data-layout-grammar="upstream-left focus-center downstream-right capital-top policy-bottom"
      data-path-length={path.length}
      data-reroot-state={transitionState}
      data-selected-node={selectedNode.key}
      data-semantic-zoom={semanticZoom}
      data-testid="workspace-shell"
      data-viewport-anchor={viewportAnchor}
      data-workspace-model="recursive-enterprise-map"
    >
      <aside className="navRail" aria-label="主导航">
        <div className="brandMark" aria-label="商域图谱">
          <span className="brandGlyph">E</span>
          <span>
            <strong>商域图谱</strong>
            <small>EEI</small>
          </span>
        </div>
        <nav aria-label="主导航">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                className={item.active ? "navItem active" : "navItem"}
                key={item.name}
                type="button"
                aria-current={item.active ? "page" : undefined}
                title={item.name}
              >
                <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
                <span>{item.name}</span>
              </button>
            );
          })}
        </nav>
        <div className="systemNav" aria-label="系统模块">
          <span className="navGroupLabel">系统模块</span>
          <a
            className="navItem"
            data-testid="objects-scope-nav-link"
            href="/objects-scope"
            title="对象与范围"
          >
            <Database size={18} strokeWidth={1.8} aria-hidden="true" />
            <span>对象与范围</span>
          </a>
        </div>
      </aside>

      <section className="focusPanel" aria-label="当前主体">
        <div className="subjectHeader">
          <div>
            <p className="eyebrow">Watchlist current focus</p>
            <h1 data-testid="current-focus-title">{scenario.heading}</h1>
            <p className="subjectSubtitle">{scenario.subtitle}</p>
          </div>
          <span className="snapshotTag">Synthetic fixture</span>
        </div>
        <dl className="subjectStats">
          <div>
            <dt>Snapshot</dt>
            <dd>fixture-v1</dd>
          </div>
          <div>
            <dt>Model</dt>
            <dd>Balanced v2</dd>
          </div>
          <div>
            <dt>Budget</dt>
            <dd data-testid="graph-budget">
              {displayNodes.length} / {displayEdges.length}
            </dd>
          </div>
        </dl>
        <div className="fixtureDisclosure" data-testid="fixture-disclosure">
          <strong>Fixture-only data</strong>
          <span>Visible synthetic notices are required; no live fact claim is shown.</span>
        </div>
        <div className="watchlistStack" aria-label="关注主体">
          {(["nvidia", "foundry", "equipment", "materials", "cloud"] as FocusKey[]).map((key) => (
            <button
              className={key === focusKey ? "watchItem current" : "watchItem"}
              key={key}
              onClick={() => setCenter(key)}
              type="button"
            >
              <span>{key === "nvidia" ? "NVIDIA" : entityLabels[key].replace("Synthetic ", "")}</span>
              <Route size={16} aria-hidden="true" />
            </button>
          ))}
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
          <svg
            className={`ecosystemMap zoom-${semanticZoom}`}
            data-semantic-zoom={semanticZoom}
            data-testid="ecosystem-map-svg"
            viewBox="0 0 760 480"
            role="img"
            aria-label="NVIDIA synthetic recursive supply-chain graph"
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
            {displayEdges.map((edge) => {
              const source = displayNodeByKey.get(edge.from);
              const target = displayNodeByKey.get(edge.to);
              if (!source || !target) return null;
              const midX = (source.x + target.x) / 2;
              const midY = (source.y + target.y) / 2 - 10;
              const lensState = activeLens === "all" || edge.lens === activeLens ? "active" : "faded";
              return (
                <g
                  className={`edgeGroup ${lensState}`}
                  data-lens-state={lensState}
                  data-testid={`edge-group-${edge.from}-${edge.to}`}
                  key={`${edge.from}-${edge.to}`}
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
                      fixture evidence
                    </text>
                  ) : null}
                </g>
              );
            })}
            {displayNodes.map((mapNode) => {
              const lensState =
                activeLens === "all" || activeEdgeKeys.has(mapNode.key) ? "active" : "faded";
              return (
              <g
                aria-label={`Inspect ${mapNode.label}`}
                aria-pressed={mapNode.key === selectedNode.key}
                className={`node ${mapNode.zone} ${lensState}${mapNode.key === selectedNode.key ? " selected" : ""}`}
                data-aggregate-count={mapNode.aggregateCount}
                data-lens-state={lensState}
                data-node-kind={mapNode.aggregateCount ? "aggregate" : "entity"}
                data-testid={`graph-node-${mapNode.key}`}
                key={mapNode.key}
                onClick={() => inspectNode(mapNode.key)}
                onKeyDown={(event) => handleNodeKeyDown(event, mapNode.key)}
                role="button"
                tabIndex={0}
                transform={`translate(${mapNode.x} ${mapNode.y})`}
              >
                <circle r={mapNode.key === focusKey ? 40 : 31} />
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

        <ol className="breadcrumb" aria-label="探索路径" data-testid="reroot-breadcrumb">
          {path.map((key, index) => (
            <li key={`${key}-${index}`}>{key === "nvidia" ? "NVIDIA" : entityLabels[key]}</li>
          ))}
        </ol>
      </section>

      <aside className="inspector" aria-label="证据与状态">
        <div className="inspectorHeader">
          <p className="eyebrow">Evidence Center</p>
          <h2>Relationship path</h2>
        </div>

        <section className="selectedNodeCard" aria-label="当前选择节点" data-testid="selected-node-card">
          <span className={`nodeToken ${selectedNode.zone}`}>{selectedNode.zone}</span>
          <h3 data-testid="selected-node-title">{selectedNode.label}</h3>
          <dl>
            <div>
              <dt>Stage</dt>
              <dd>{selectedNode.stage}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{selectedNode.role}</dd>
            </div>
            <div>
              <dt>Current subject</dt>
              <dd>{scenario.heading}</dd>
            </div>
          </dl>
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

        <div className="actionStack" aria-label="主体操作">
          <button
            className="primaryAction"
            data-testid="primary-set-center"
            disabled={!selectedNode.centerable || selectedNode.key === focusKey}
            onClick={() => selectedNode.centerable && setCenter(selectedNode.key as FocusKey)}
            type="button"
          >
            <Crosshair size={16} aria-hidden="true" />
            <span>以 {selectedNode.label} 为中心</span>
          </button>
          <button
            disabled={!upstreamCandidate}
            onClick={() => upstreamCandidate && inspectNode(upstreamCandidate)}
            type="button"
          >
            <ArrowUp size={16} aria-hidden="true" />
            <span>展开上游</span>
          </button>
          <button
            disabled={!downstreamCandidate}
            onClick={() => downstreamCandidate && inspectNode(downstreamCandidate)}
            type="button"
          >
            <ArrowDown size={16} aria-hidden="true" />
            <span>展开下游</span>
          </button>
          <button onClick={() => inspectNode(selectedNode.key)} type="button">
            <Star size={16} aria-hidden="true" />
            <span>加入关注</span>
          </button>
          <button onClick={() => inspectNode(focusKey)} type="button">
            <Route size={16} aria-hidden="true" />
            <span>查看路径</span>
          </button>
          <button onClick={() => inspectNode(selectedNode.key)} type="button">
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
          <span data-testid="lens-state">Lens: {activeLens}</span>
          <span data-testid="zoom-state">Zoom: {semanticZoom}</span>
          <span data-testid="reroot-state">Canvas state: {transitionState}</span>
          <span data-testid="budget-state">
            Budget: {displayNodes.length} nodes / {displayEdges.length} edges / max 40 first-screen edges
          </span>
        </div>
      </aside>
    </main>
  );
}
