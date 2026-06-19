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

const nodes = [
  { id: "NVIDIA", x: 390, y: 240, size: 74, tone: "focus" },
  { id: "TSMC", x: 205, y: 170, size: 56, tone: "supply" },
  { id: "ASML", x: 80, y: 115, size: 46, tone: "supply" },
  { id: "HBM", x: 180, y: 320, size: 42, tone: "supply" },
  { id: "Cloud", x: 600, y: 170, size: 54, tone: "market" },
  { id: "Energy", x: 635, y: 320, size: 48, tone: "policy" },
  { id: "Policy", x: 405, y: 410, size: 44, tone: "policy" }
];

const edges = [
  ["ASML", "TSMC"],
  ["TSMC", "NVIDIA"],
  ["HBM", "NVIDIA"],
  ["NVIDIA", "Cloud"],
  ["Energy", "Cloud"],
  ["Policy", "NVIDIA"]
] as const;

const nodeById = new Map(nodes.map((node) => [node.id, node]));

export default function Home() {
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
            <h1>NVIDIA</h1>
          </div>
          <span className="snapshotTag">fixture shell</span>
        </div>
        <dl className="subjectStats">
          <div>
            <dt>Snapshot</dt>
            <dd>G1-shell</dd>
          </div>
          <div>
            <dt>Model</dt>
            <dd>Balanced v2</dd>
          </div>
          <div>
            <dt>Budget</dt>
            <dd>42 / 64</dd>
          </div>
        </dl>
        <div className="watchlistStack" aria-label="关注主体">
          {["NVIDIA", "TSMC", "ASML", "Microsoft", "CoreWeave"].map((name) => (
            <button className={name === "NVIDIA" ? "watchItem current" : "watchItem"} key={name} type="button">
              <span>{name}</span>
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
              <button className={index === 0 ? "lens active" : "lens"} key={lens} type="button">
                {lens}
              </button>
            ))}
          </div>
        </div>

        <div className="mapSurface">
          <svg className="ecosystemMap" viewBox="0 0 720 480" role="img" aria-label="NVIDIA to TSMC to ASML ecosystem path">
            {edges.map(([from, to]) => {
              const source = nodeById.get(from);
              const target = nodeById.get(to);
              if (!source || !target) return null;
              return (
                <line
                  className="edge"
                  key={`${from}-${to}`}
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                />
              );
            })}
            {nodes.map((node) => (
              <g className={`node ${node.tone}`} key={node.id} transform={`translate(${node.x} ${node.y})`}>
                <circle r={node.size / 2} />
                <text textAnchor="middle" dominantBaseline="middle">
                  {node.id}
                </text>
              </g>
            ))}
          </svg>
        </div>
      </section>

      <aside className="inspector" aria-label="证据与状态">
        <div className="inspectorHeader">
          <p className="eyebrow">Evidence Center</p>
          <h2>Relationship path</h2>
        </div>
        <ol className="pathList">
          <li>{"NVIDIA -> TSMC"}</li>
          <li>{"TSMC -> ASML"}</li>
          <li>{"NVIDIA -> Cloud"}</li>
        </ol>
        <div className="statusStrip">
          <span>Data: fixture</span>
          <span>API: shell</span>
          <span>DB: pending</span>
        </div>
      </aside>
    </main>
  );
}
