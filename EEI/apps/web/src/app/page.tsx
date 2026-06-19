"use client";

import { useMemo, useState } from "react";
import {
  Activity,
  Bell,
  Boxes,
  Building2,
  CircleDollarSign,
  Clock3,
  Database,
  FileSearch,
  GitBranch,
  Landmark,
  Network,
  PackageSearch,
  Route,
  Scale,
  Settings2,
  ShieldCheck
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

type NavItem = {
  name: string;
  icon: LucideIcon;
  active?: boolean;
};

type NodeKey =
  | "materials"
  | "equipment"
  | "foundry"
  | "nvidia"
  | "systems"
  | "cloud"
  | "datacenter"
  | "energy";

type Zone = "upstream" | "focus" | "downstream" | "infrastructure";

type MapNode = {
  key: NodeKey;
  label: string;
  shortLabel: string;
  stage: string;
  role: string;
  x: number;
  y: number;
  zone: Zone;
};

type MapEdge = {
  from: NodeKey;
  to: NodeKey;
  label: string;
  stage: string;
  fixtureNotice: string;
};

type FocusScenario = {
  focus: NodeKey;
  heading: string;
  subtitle: string;
  nodes: MapNode[];
  edges: MapEdge[];
  nextCenters: NodeKey[];
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
  systems: "Synthetic Systems Integrator",
  cloud: "Synthetic Cloud Customer",
  datacenter: "Synthetic AI Data Center Campus",
  energy: "Synthetic Grid Utility"
};

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
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "equipment",
    to: "foundry",
    label: "equipment provider to",
    stage: "SC-04 -> SC-06",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "foundry",
    to: "nvidia",
    label: "wafer foundry for",
    stage: "SC-06 -> SC-08",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "nvidia",
    to: "systems",
    label: "licenses IP to",
    stage: "SC-05 -> SC-09",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "systems",
    to: "cloud",
    label: "system integrator for",
    stage: "SC-09 -> SC-12",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "cloud",
    to: "nvidia",
    label: "customer of",
    stage: "SC-12 -> SC-08",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "energy",
    to: "datacenter",
    label: "energy provider to",
    stage: "SC-10 -> SC-10",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  },
  {
    from: "datacenter",
    to: "cloud",
    label: "infrastructure supports",
    stage: "SC-10 -> SC-12",
    fixtureNotice: "Synthetic fixture for interaction and data-model tests."
  }
];

const scenarios: Record<NodeKey, FocusScenario> = {
  nvidia: {
    focus: "nvidia",
    heading: "NVIDIA",
    subtitle: "Semiconductor and AI infrastructure ecosystem",
    nodes: [
      node("materials", 82, 336, "upstream", "SC-02 Materials", "specialty materials"),
      node("equipment", 92, 122, "upstream", "SC-04 Equipment", "lithography equipment"),
      node("foundry", 252, 224, "upstream", "SC-06 Manufacturing", "advanced foundry"),
      node("nvidia", 394, 246, "focus", "SC-05 Design / IP", "current focus"),
      node("systems", 536, 164, "downstream", "SC-09 System", "system integration"),
      node("cloud", 650, 244, "downstream", "SC-12 Customer", "cloud customer"),
      node("datacenter", 562, 358, "infrastructure", "SC-10 Data center", "AI data center"),
      node("energy", 666, 390, "infrastructure", "SC-10 Energy", "grid utility")
    ],
    edges: baseEdges,
    nextCenters: ["foundry", "systems", "cloud"]
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
  role: string
): MapNode {
  return {
    key,
    label: entityLabels[key],
    shortLabel:
      key === "nvidia"
        ? "NVIDIA"
        : entityLabels[key].replace("Synthetic ", "").replace(" Co.", ""),
    stage,
    role,
    x,
    y,
    zone
  };
}

export default function Home() {
  const [focusKey, setFocusKey] = useState<NodeKey>("nvidia");
  const [path, setPath] = useState<NodeKey[]>(["nvidia"]);
  const scenario = scenarios[focusKey];
  const nodeByKey = useMemo(
    () => new Map(scenario.nodes.map((item) => [item.key, item])),
    [scenario.nodes]
  );

  function setCenter(nextFocus: NodeKey) {
    setFocusKey(nextFocus);
    setPath((current) => [...current, nextFocus]);
  }

  function resetToNvidia() {
    setFocusKey("nvidia");
    setPath(["nvidia"]);
  }

  return (
    <main className="workspace">
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
      </aside>

      <section className="focusPanel" aria-label="当前主体">
        <div className="subjectHeader">
          <div>
            <p className="eyebrow">Watchlist current focus</p>
            <h1>{scenario.heading}</h1>
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
            <dd>{scenario.nodes.length} / {scenario.edges.length}</dd>
          </div>
        </dl>
        <div className="fixtureDisclosure" data-testid="fixture-disclosure">
          <strong>Fixture-only data</strong>
          <span>Visible synthetic notices are required; no live fact claim is shown.</span>
        </div>
        <div className="watchlistStack" aria-label="关注主体">
          {(["nvidia", "foundry", "equipment", "materials", "cloud"] as NodeKey[]).map((key) => (
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

      <section className="canvas" aria-label="商业版图">
        <div className="canvasTopbar">
          <div>
            <p className="eyebrow">Golden Vertical</p>
            <h2>Semiconductor and AI infrastructure ecosystem</h2>
          </div>
          <div className="lensBar" aria-label="分析视角">
            {["商业", "供应链", "资本", "政策"].map((lens, index) => (
              <button className={index === 1 ? "lens active" : "lens"} key={lens} type="button">
                {lens}
              </button>
            ))}
          </div>
        </div>

        <div className="stageRail" aria-label="供应链阶段覆盖">
          {stageRows.map((stage) => (
            <span className={`stagePill ${stage.side}`} key={stage.id}>
              {stage.id} {stage.name}
            </span>
          ))}
        </div>

        <div className="mapSurface" data-testid="ecosystem-map-surface">
          <svg
            className="ecosystemMap"
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
            {scenario.edges.map((edge) => {
              const source = nodeByKey.get(edge.from);
              const target = nodeByKey.get(edge.to);
              if (!source || !target) return null;
              const midX = (source.x + target.x) / 2;
              const midY = (source.y + target.y) / 2 - 10;
              return (
                <g key={`${edge.from}-${edge.to}`}>
                  <line
                    className="edge"
                    markerEnd="url(#arrow)"
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                  />
                  <text className="edgeLabel" textAnchor="middle" x={midX} y={midY}>
                    {edge.label}
                  </text>
                </g>
              );
            })}
            {scenario.nodes.map((mapNode) => (
              <g
                className={`node ${mapNode.zone}`}
                data-testid={`graph-node-${mapNode.key}`}
                key={mapNode.key}
                transform={`translate(${mapNode.x} ${mapNode.y})`}
              >
                <circle r={mapNode.key === focusKey ? 40 : 31} />
                <text textAnchor="middle" dominantBaseline="middle">
                  {mapNode.shortLabel}
                </text>
                <text className="nodeStage" textAnchor="middle" y={52}>
                  {mapNode.stage}
                </text>
              </g>
            ))}
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
          {scenario.nextCenters.map((key) => (
            <button key={key} onClick={() => setCenter(key)} type="button">
              以 {entityLabels[key]} 为中心
            </button>
          ))}
          <button onClick={resetToNvidia} type="button">
            回到 NVIDIA
          </button>
        </div>

        <div className="statusStrip">
          <span>Data: synthetic fixture</span>
          <span>Live facts: disabled</span>
          <span>DB fixture notice: visible</span>
        </div>
      </aside>
    </main>
  );
}
