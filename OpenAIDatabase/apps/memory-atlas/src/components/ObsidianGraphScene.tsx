import { Eye, EyeOff, Minus, Pause, Play, Plus, RotateCcw, Settings } from "lucide-react";
import type { KeyboardEvent as ReactKeyboardEvent, PointerEvent as ReactPointerEvent, WheelEvent as ReactWheelEvent } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { normalizeMemoryTier } from "../data/atlas";
import type { AtlasEdge, AtlasNode } from "../types";

interface ObsidianDeltaStats {
  recentCount: number;
  previousCount: number;
  deltaCount: number;
  deltaRate: number | null;
  topCategory: string;
}

interface ObsidianGraphSceneProps {
  nodes: AtlasNode[];
  edges: AtlasEdge[];
  selectedNode: AtlasNode | null;
  deltaStats: ObsidianDeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}

interface ObsidianSettings {
  showTags: boolean;
  showAttachments: boolean;
  existingFilesOnly: boolean;
  showOrphans: boolean;
  showArrows: boolean;
  textFadeThreshold: number;
  nodeSize: number;
  linkThickness: number;
  animate: boolean;
  centerForce: number;
  repelForce: number;
  linkForce: number;
  linkDistance: number;
}

interface ObsidianNodeDatum {
  node: AtlasNode;
  r: number;
  color: string;
  label: string;
  degree: number;
  depth: number;
  visibleAt: number;
  groupLabel: string;
}

interface ObsidianEdgeDatum {
  id: string;
  sourceId: string;
  targetId: string;
  weight: number;
  color: string;
  kind: string;
}

interface ObsidianSimNode extends ObsidianNodeDatum {
  x: number;
  y: number;
  vx: number;
  vy: number;
  pinned: boolean;
}

interface ObsidianSimEdge {
  id: string;
  source: ObsidianSimNode;
  target: ObsidianSimNode;
  weight: number;
  color: string;
  kind: string;
}

interface ObsidianDataset {
  nodes: ObsidianNodeDatum[];
  edges: ObsidianEdgeDatum[];
  groups: Array<{ label: string; color: string; count: number; query: string }>;
  totalBeforeLimit: number;
  hiddenByLimit: number;
  orphanCount: number;
}

interface ViewTransform {
  x: number;
  y: number;
  k: number;
}

const DEFAULT_OBSIDIAN_SETTINGS: ObsidianSettings = {
  showTags: true,
  showAttachments: true,
  existingFilesOnly: true,
  showOrphans: true,
  showArrows: false,
  textFadeThreshold: 1.18,
  nodeSize: 1,
  linkThickness: 1,
  animate: true,
  centerForce: 0.52,
  repelForce: 0.64,
  linkForce: 0.52,
  linkDistance: 118,
};

const VIEWBOX_WIDTH = 1000;
const VIEWBOX_HEIGHT = 600;
const MAX_OBSIDIAN_NODES = 260;
const MAX_OBSIDIAN_EDGES = 780;

export function ObsidianGraphScene({ nodes, edges, selectedNode, deltaStats, onSelectNode }: ObsidianGraphSceneProps) {
  const [localOnly, setLocalOnly] = useState(false);
  const [depth, setDepth] = useState(1);
  const [query, setQuery] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(true);
  const [settings, setSettings] = useState<ObsidianSettings>(DEFAULT_OBSIDIAN_SETTINGS);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [view, setView] = useState<ViewTransform>({ x: 0, y: 0, k: 1 });
  const [revealProgress, setRevealProgress] = useState(1);
  const [contextNode, setContextNode] = useState<{ node: AtlasNode; x: number; y: number } | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const panStartRef = useRef<{ pointerId: number; clientX: number; clientY: number; x: number; y: number } | null>(null);

  const dataset = useMemo(
    () => buildObsidianDataset(nodes, edges, selectedNode, localOnly, depth, query, settings),
    [nodes, edges, selectedNode, localOnly, depth, query, settings],
  );
  const graph = useObsidianForceGraph(dataset.nodes, dataset.edges, settings);

  const activeFocusId = hoveredNodeId ?? selectedNode?.id ?? null;
  const activeNeighborhood = useMemo(() => buildNeighborhood(activeFocusId, graph.edges), [activeFocusId, graph.edges]);
  const visibleNodeIds = useMemo(
    () => new Set(graph.nodes.filter((node) => node.visibleAt <= revealProgress).map((node) => node.node.id)),
    [graph.nodes, revealProgress],
  );
  const visibleEdges = useMemo(
    () => graph.edges.filter((edge) => visibleNodeIds.has(edge.source.node.id) && visibleNodeIds.has(edge.target.node.id)),
    [graph.edges, visibleNodeIds],
  );

  useEffect(() => {
    if (!settings.animate) {
      setRevealProgress(1);
      return;
    }
    let frame = 0;
    let raf = 0;
    const startedAt = performance.now();
    const run = (now: number) => {
      frame += 1;
      const elapsed = now - startedAt;
      const progress = Math.min(1, elapsed / 4200);
      setRevealProgress(smoothStep(progress));
      if (progress < 1 || frame < 32) {
        raf = window.requestAnimationFrame(run);
      }
    };
    setRevealProgress(0.04);
    raf = window.requestAnimationFrame(run);
    return () => window.cancelAnimationFrame(raf);
  }, [settings.animate, dataset.nodes.length]);

  const toGraphPoint = useCallback(
    (clientX: number, clientY: number) => {
      const rect = svgRef.current?.getBoundingClientRect();
      if (!rect) return { x: VIEWBOX_WIDTH / 2, y: VIEWBOX_HEIGHT / 2 };
      const viewX = ((clientX - rect.left) / Math.max(1, rect.width)) * VIEWBOX_WIDTH;
      const viewY = ((clientY - rect.top) / Math.max(1, rect.height)) * VIEWBOX_HEIGHT;
      return {
        x: (viewX - view.x) / view.k,
        y: (viewY - view.y) / view.k,
      };
    },
    [view],
  );

  const handleWheel = useCallback(
    (event: ReactWheelEvent<SVGSVGElement>) => {
      event.preventDefault();
      const rect = event.currentTarget.getBoundingClientRect();
      const viewX = ((event.clientX - rect.left) / Math.max(1, rect.width)) * VIEWBOX_WIDTH;
      const viewY = ((event.clientY - rect.top) / Math.max(1, rect.height)) * VIEWBOX_HEIGHT;
      const nextK = clamp(view.k * (event.deltaY > 0 ? 0.9 : 1.12), 0.42, 3.4);
      const graphX = (viewX - view.x) / view.k;
      const graphY = (viewY - view.y) / view.k;
      setView({ k: nextK, x: viewX - graphX * nextK, y: viewY - graphY * nextK });
    },
    [view],
  );

  const handleCanvasPointerDown = useCallback((event: ReactPointerEvent<SVGSVGElement>) => {
    if (event.button !== 0) return;
    setContextNode(null);
    panStartRef.current = { pointerId: event.pointerId, clientX: event.clientX, clientY: event.clientY, x: view.x, y: view.y };
    event.currentTarget.setPointerCapture(event.pointerId);
  }, [view.x, view.y]);

  const handleCanvasPointerMove = useCallback(
    (event: ReactPointerEvent<SVGSVGElement>) => {
      if (draggingNodeId) {
        graph.dragNode(draggingNodeId, toGraphPoint(event.clientX, event.clientY));
        return;
      }
      const pan = panStartRef.current;
      if (!pan || pan.pointerId !== event.pointerId) return;
      const rect = event.currentTarget.getBoundingClientRect();
      const dx = ((event.clientX - pan.clientX) / Math.max(1, rect.width)) * VIEWBOX_WIDTH;
      const dy = ((event.clientY - pan.clientY) / Math.max(1, rect.height)) * VIEWBOX_HEIGHT;
      setView((current) => ({ ...current, x: pan.x + dx, y: pan.y + dy }));
    },
    [draggingNodeId, graph, toGraphPoint],
  );

  const stopPointerAction = useCallback((event: ReactPointerEvent<SVGSVGElement>) => {
    panStartRef.current = null;
    if (draggingNodeId) {
      graph.releaseNode(draggingNodeId);
      setDraggingNodeId(null);
    }
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }, [draggingNodeId, graph]);

  const zoomBy = useCallback((delta: number) => {
    setView((current) => {
      const nextK = clamp(current.k * (delta > 0 ? 1.14 : 0.88), 0.42, 3.4);
      return {
        k: nextK,
        x: VIEWBOX_WIDTH / 2 - ((VIEWBOX_WIDTH / 2 - current.x) / current.k) * nextK,
        y: VIEWBOX_HEIGHT / 2 - ((VIEWBOX_HEIGHT / 2 - current.y) / current.k) * nextK,
      };
    });
  }, []);

  function resetView() {
    setView({ x: 0, y: 0, k: 1 });
    graph.reset();
  }

  function updateSetting<K extends keyof ObsidianSettings>(key: K, value: ObsidianSettings[K]) {
    setSettings((current) => ({ ...current, [key]: value }));
  }

  function handleGraphKeyDown(event: ReactKeyboardEvent<SVGSVGElement>) {
    if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      zoomBy(1);
    } else if (event.key === "-") {
      event.preventDefault();
      zoomBy(-1);
    } else if (event.key === "ArrowLeft" || event.key === "ArrowRight" || event.key === "ArrowUp" || event.key === "ArrowDown") {
      event.preventDefault();
      const step = event.shiftKey ? 58 : 24;
      setView((current) => ({
        ...current,
        x: current.x + (event.key === "ArrowLeft" ? step : event.key === "ArrowRight" ? -step : 0),
        y: current.y + (event.key === "ArrowUp" ? step : event.key === "ArrowDown" ? -step : 0),
      }));
    }
  }

  return (
    <div className="visual-workspace obsidian-map obsidian-graph-view" ref={containerRef}>
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">Obsidian Graph View / 力导向 / 可拖拽缩放</p>
          <h2>像 Obsidian 内置图谱一样探索记忆节点、关系、过滤器、分组和力参数</h2>
        </div>
        <span>{dataset.nodes.length} 个节点 / {dataset.edges.length} 条连接</span>
      </div>

      <div className="obsidian-topbar" aria-label="Obsidian 图谱工具栏">
        <div className="obsidian-mode-tabs">
          <button className={!localOnly ? "segmented active" : "segmented"} onClick={() => setLocalOnly(false)} type="button">全局图</button>
          <button className={localOnly ? "segmented active" : "segmented"} onClick={() => setLocalOnly(true)} type="button">局部图</button>
          <label className="obsidian-depth-control">
            深度
            <input min={1} max={4} step={1} type="range" value={depth} onChange={(event) => setDepth(Number(event.target.value))} />
            <strong>{depth}</strong>
          </label>
        </div>
        <div className="obsidian-action-buttons">
          <button aria-label="缩小图谱" title="缩小" type="button" onClick={() => zoomBy(-1)}><Minus size={15} /></button>
          <button aria-label="放大图谱" title="放大" type="button" onClick={() => zoomBy(1)}><Plus size={15} /></button>
          <button aria-label="重置图谱视角" title="重置视角" type="button" onClick={resetView}><RotateCcw size={15} /></button>
          <button aria-label="打开或关闭图谱设置" title="图谱设置" type="button" onClick={() => setSettingsOpen((value) => !value)}><Settings size={15} /></button>
        </div>
      </div>

      <div className="obsidian-status-strip" aria-label="图谱状态">
        <span><b>{localOnly ? "局部图" : "全局图"}</b><em>{localOnly && selectedNode ? `${selectedNode.label} · ${depth} 层` : "全部可见关系"}</em></span>
        <span><b>筛选</b><em>{query.trim() || "无搜索词"}</em></span>
        <span><b>增量</b><em>{formatDelta(deltaStats.deltaCount, deltaStats.deltaRate)}</em></span>
        <span><b>隐藏</b><em>{dataset.hiddenByLimit} 个超限节点 / {dataset.orphanCount} 个孤立节点</em></span>
      </div>

      <div className="obsidian-scene-shell">
        <svg
          className="obsidian-graph-canvas"
          viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
          role="application"
          aria-label="Obsidian 风格动态记忆图谱"
          tabIndex={0}
          ref={svgRef}
          onWheel={handleWheel}
          onPointerDown={handleCanvasPointerDown}
          onPointerMove={handleCanvasPointerMove}
          onPointerUp={stopPointerAction}
          onPointerCancel={stopPointerAction}
          onKeyDown={handleGraphKeyDown}
        >
          <defs>
            <radialGradient id="obsidian-node-glow">
              <stop offset="0%" stopColor="rgba(255,255,255,0.95)" />
              <stop offset="100%" stopColor="rgba(255,255,255,0)" />
            </radialGradient>
            <marker id="obsidian-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
              <path d="M0,0 L7,3.5 L0,7 Z" fill="rgba(214, 219, 224, 0.62)" />
            </marker>
          </defs>
          <rect className="obsidian-graph-background" x="0" y="0" width={VIEWBOX_WIDTH} height={VIEWBOX_HEIGHT} />
          <g transform={`translate(${view.x} ${view.y}) scale(${view.k})`}>
            <g className="obsidian-links">
              {visibleEdges.map((edge) => {
                const related = !activeFocusId || activeNeighborhood.has(edge.source.node.id) || activeNeighborhood.has(edge.target.node.id);
                const directlyRelated = Boolean(activeFocusId && (edge.source.node.id === activeFocusId || edge.target.node.id === activeFocusId));
                return (
                  <line
                    key={edge.id}
                    className={directlyRelated ? "obsidian-link focused" : "obsidian-link"}
                    x1={edge.source.x}
                    y1={edge.source.y}
                    x2={edge.target.x}
                    y2={edge.target.y}
                    stroke={edge.color}
                    strokeWidth={Math.max(0.45, edge.weight * 1.7 * settings.linkThickness)}
                    opacity={related ? (directlyRelated ? 0.82 : 0.3) : 0.055}
                    markerEnd={settings.showArrows ? "url(#obsidian-arrow)" : undefined}
                  />
                );
              })}
            </g>
            <g className="obsidian-nodes">
              {graph.nodes.map((item) => {
                if (!visibleNodeIds.has(item.node.id)) return null;
                const selected = item.node.id === selectedNode?.id;
                const hovered = item.node.id === hoveredNodeId;
                const related = !activeFocusId || activeNeighborhood.has(item.node.id);
                const labelVisible = selected || hovered || view.k >= settings.textFadeThreshold || item.degree >= 10;
                return (
                  <g
                    key={item.node.id}
                    className={`obsidian-node${selected ? " selected" : ""}${hovered ? " hovered" : ""}${related ? "" : " dimmed"}`}
                    role="button"
                    tabIndex={0}
                    aria-label={`${kindLabel(item.node.kind)} · ${item.node.label}`}
                    transform={`translate(${item.x} ${item.y})`}
                    onPointerDown={(event) => {
                      event.stopPropagation();
                      setContextNode(null);
                      setDraggingNodeId(item.node.id);
                      graph.pinNode(item.node.id);
                      onSelectNode(item.node);
                    }}
                    onMouseEnter={() => setHoveredNodeId(item.node.id)}
                    onMouseLeave={() => setHoveredNodeId(null)}
                    onClick={(event) => {
                      event.stopPropagation();
                      onSelectNode(item.node);
                    }}
                    onContextMenu={(event) => {
                      event.preventDefault();
                      event.stopPropagation();
                      const rect = containerRef.current?.getBoundingClientRect();
                      setContextNode({
                        node: item.node,
                        x: event.clientX - (rect?.left ?? 0),
                        y: event.clientY - (rect?.top ?? 0),
                      });
                    }}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        onSelectNode(item.node);
                      }
                    }}
                  >
                    <title>{`${kindLabel(item.node.kind)} · ${item.node.label} · ${item.degree} 条连接`}</title>
                    <circle className="obsidian-node-aura" r={item.r * 2.25} fill={item.color} opacity={selected || hovered ? 0.2 : 0.08} />
                    <circle className="obsidian-node-core" r={item.r} fill={item.color} />
                    {labelVisible && (
                      <text className="obsidian-node-label" x={item.r + 7} y="4">
                        {item.label}
                      </text>
                    )}
                  </g>
                );
              })}
            </g>
          </g>
        </svg>

        {settingsOpen && (
          <ObsidianSettingsPanel
            query={query}
            setQuery={setQuery}
            settings={settings}
            setSetting={updateSetting}
            groups={dataset.groups}
            onReset={() => {
              setSettings(DEFAULT_OBSIDIAN_SETTINGS);
              setQuery("");
              setDepth(1);
              setLocalOnly(false);
              resetView();
            }}
          />
        )}

        {contextNode && (
          <div className="obsidian-context-menu" style={{ left: contextNode.x, top: contextNode.y }} role="menu">
            <strong>{contextNode.node.label}</strong>
            <button type="button" onClick={() => onSelectNode(contextNode.node)}>查看详情</button>
            <button
              type="button"
              onClick={() => {
                onSelectNode(contextNode.node);
                setLocalOnly(true);
                setContextNode(null);
              }}
            >
              只看局部图
            </button>
            <button
              type="button"
              onClick={() => {
                graph.pinNode(contextNode.node.id);
                setContextNode(null);
              }}
            >
              固定节点位置
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function ObsidianSettingsPanel({
  query,
  setQuery,
  settings,
  setSetting,
  groups,
  onReset,
}: {
  query: string;
  setQuery: (value: string) => void;
  settings: ObsidianSettings;
  setSetting: <K extends keyof ObsidianSettings>(key: K, value: ObsidianSettings[K]) => void;
  groups: Array<{ label: string; color: string; count: number; query: string }>;
  onReset: () => void;
}) {
  return (
    <aside className="obsidian-settings-panel" aria-label="Obsidian 图谱设置">
      <div className="obsidian-settings-head">
        <strong>图谱设置</strong>
        <button type="button" onClick={onReset}>恢复默认</button>
      </div>
      <section>
        <h3>过滤器</h3>
        <label className="obsidian-search-field">
          搜索文件
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="输入主题、项目、记忆关键词" />
        </label>
        <ToggleRow label="标签" checked={settings.showTags} onChange={(value) => setSetting("showTags", value)} />
        <ToggleRow label="附件" checked={settings.showAttachments} onChange={(value) => setSetting("showAttachments", value)} />
        <ToggleRow label="仅现有文件" checked={settings.existingFilesOnly} onChange={(value) => setSetting("existingFilesOnly", value)} />
        <ToggleRow label="孤立节点" checked={settings.showOrphans} onChange={(value) => setSetting("showOrphans", value)} />
      </section>
      <section>
        <h3>分组</h3>
        <div className="obsidian-group-list">
          {groups.slice(0, 6).map((group) => (
            <span key={group.label}>
              <i style={{ background: group.color }} />
              <b>{group.label}</b>
              <em>{group.query}</em>
              <small>{group.count}</small>
            </span>
          ))}
        </div>
      </section>
      <section>
        <h3>显示</h3>
        <ToggleRow label="箭头" checked={settings.showArrows} onChange={(value) => setSetting("showArrows", value)} />
        <SliderRow label="文字淡出阈值" min={0.42} max={1.8} step={0.02} value={settings.textFadeThreshold} onChange={(value) => setSetting("textFadeThreshold", value)} />
        <SliderRow label="节点大小" min={0.65} max={1.7} step={0.05} value={settings.nodeSize} onChange={(value) => setSetting("nodeSize", value)} />
        <SliderRow label="连线粗细" min={0.5} max={1.8} step={0.05} value={settings.linkThickness} onChange={(value) => setSetting("linkThickness", value)} />
        <button className="obsidian-animate-button" type="button" onClick={() => setSetting("animate", !settings.animate)}>
          {settings.animate ? <Pause size={14} /> : <Play size={14} />}
          {settings.animate ? "暂停动画" : "播放动画"}
        </button>
      </section>
      <section>
        <h3>力</h3>
        <SliderRow label="中心力" min={0.1} max={1.3} step={0.03} value={settings.centerForce} onChange={(value) => setSetting("centerForce", value)} />
        <SliderRow label="排斥力" min={0.1} max={1.3} step={0.03} value={settings.repelForce} onChange={(value) => setSetting("repelForce", value)} />
        <SliderRow label="链接力" min={0.1} max={1.3} step={0.03} value={settings.linkForce} onChange={(value) => setSetting("linkForce", value)} />
        <SliderRow label="链接距离" min={52} max={220} step={4} value={settings.linkDistance} onChange={(value) => setSetting("linkDistance", value)} />
      </section>
    </aside>
  );
}

function ToggleRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <button className="obsidian-toggle-row" type="button" onClick={() => onChange(!checked)} aria-pressed={checked}>
      <span>{label}</span>
      {checked ? <Eye size={14} /> : <EyeOff size={14} />}
    </button>
  );
}

function SliderRow({
  label,
  min,
  max,
  step,
  value,
  onChange,
}: {
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="obsidian-slider-row">
      <span>{label}</span>
      <input min={min} max={max} step={step} type="range" value={value} onChange={(event) => onChange(Number(event.target.value))} />
      <b>{value >= 10 ? Math.round(value) : value.toFixed(2)}</b>
    </label>
  );
}

function useObsidianForceGraph(inputNodes: ObsidianNodeDatum[], inputEdges: ObsidianEdgeDatum[], settings: ObsidianSettings) {
  const positionsRef = useRef(new Map<string, ObsidianSimNode>());
  const edgesRef = useRef<ObsidianEdgeDatum[]>([]);
  const settleFramesRef = useRef(160);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const nextIds = new Set(inputNodes.map((node) => node.node.id));
    const positions = positionsRef.current;
    for (const id of Array.from(positions.keys())) {
      if (!nextIds.has(id)) positions.delete(id);
    }
    inputNodes.forEach((node, index) => {
      const existing = positions.get(node.node.id);
      if (existing) {
        Object.assign(existing, node, { r: node.r * settings.nodeSize });
        return;
      }
      positions.set(node.node.id, createInitialSimNode(node, index, settings.nodeSize));
    });
    edgesRef.current = inputEdges;
    settleFramesRef.current = 180;
    setTick((value) => value + 1);
  }, [inputNodes, inputEdges, settings.nodeSize]);

  useEffect(() => {
    settleFramesRef.current = 160;
  }, [settings.centerForce, settings.repelForce, settings.linkForce, settings.linkDistance, settings.animate]);

  useEffect(() => {
    let raf = 0;
    const run = () => {
      const shouldContinue = settings.animate || settleFramesRef.current > 0;
      if (!shouldContinue) return;
      stepObsidianForceSimulation(positionsRef.current, edgesRef.current, settings);
      settleFramesRef.current = Math.max(0, settleFramesRef.current - 1);
      setTick((value) => (value + 1) % 100000);
      raf = window.requestAnimationFrame(run);
    };
    raf = window.requestAnimationFrame(run);
    return () => window.cancelAnimationFrame(raf);
  }, [settings]);

  const nodes = useMemo(
    () =>
      Array.from(positionsRef.current.values()).sort((a, b) => {
        const kindDiff = kindRank(a.node.kind) - kindRank(b.node.kind);
        if (kindDiff !== 0) return kindDiff;
        return b.degree - a.degree;
      }),
    [tick],
  );

  const graphEdges = useMemo(() => {
    const byId = new Map(nodes.map((node) => [node.node.id, node]));
    return edgesRef.current
      .map((edge): ObsidianSimEdge | null => {
        const source = byId.get(edge.sourceId);
        const target = byId.get(edge.targetId);
        if (!source || !target) return null;
        return { ...edge, source, target };
      })
      .filter((edge): edge is ObsidianSimEdge => Boolean(edge));
  }, [nodes]);

  const dragNode = useCallback((id: string, point: { x: number; y: number }) => {
    const node = positionsRef.current.get(id);
    if (!node) return;
    node.x = clamp(point.x, 18, VIEWBOX_WIDTH - 18);
    node.y = clamp(point.y, 18, VIEWBOX_HEIGHT - 18);
    node.vx = 0;
    node.vy = 0;
    node.pinned = true;
    settleFramesRef.current = 80;
    setTick((value) => value + 1);
  }, []);

  const pinNode = useCallback((id: string) => {
    const node = positionsRef.current.get(id);
    if (!node) return;
    node.pinned = true;
    node.vx = 0;
    node.vy = 0;
    settleFramesRef.current = 80;
    setTick((value) => value + 1);
  }, []);

  const releaseNode = useCallback((id: string) => {
    const node = positionsRef.current.get(id);
    if (!node) return;
    node.pinned = false;
    settleFramesRef.current = 90;
  }, []);

  const reset = useCallback(() => {
    const positions = positionsRef.current;
    positions.clear();
    inputNodes.forEach((node, index) => {
      positions.set(node.node.id, createInitialSimNode(node, index, settings.nodeSize));
    });
    settleFramesRef.current = 180;
    setTick((value) => value + 1);
  }, [inputNodes, settings.nodeSize]);

  return { nodes, edges: graphEdges, dragNode, pinNode, releaseNode, reset };
}

function createInitialSimNode(node: ObsidianNodeDatum, index: number, nodeSize: number): ObsidianSimNode {
  const angle = stableUnit(node.node.id, "obsidian-angle") * Math.PI * 2;
  const radius = 70 + stableUnit(node.node.id, "obsidian-radius") * 220 + index * 0.16;
  return {
    ...node,
    r: node.r * nodeSize,
    x: VIEWBOX_WIDTH / 2 + Math.cos(angle) * radius,
    y: VIEWBOX_HEIGHT / 2 + Math.sin(angle) * radius * 0.72,
    vx: 0,
    vy: 0,
    pinned: false,
  };
}

function buildObsidianDataset(
  nodes: AtlasNode[],
  edges: AtlasEdge[],
  selectedNode: AtlasNode | null,
  localOnly: boolean,
  depth: number,
  query: string,
  settings: ObsidianSettings,
): ObsidianDataset {
  const localIds = localOnly && selectedNode ? expandGraphIds(selectedNode.id, edges, depth) : new Set(nodes.map((node) => node.id));
  const normalizedQuery = query.trim().toLowerCase();
  let candidates = nodes.filter((node) => localIds.has(node.id));

  if (normalizedQuery) {
    candidates = candidates.filter((node) =>
      [node.label, node.statement, node.category, node.memory_tier, node.source_kind, node.source_label, node.data_source, node.visual?.cluster]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(normalizedQuery)),
    );
  }
  if (!settings.showTags) {
    candidates = candidates.filter((node) => node.kind !== "theme" && node.kind !== "category" && node.kind !== "tier");
  }
  if (!settings.showAttachments) {
    candidates = candidates.filter((node) => node.kind !== "project" && node.kind !== "decision" && node.kind !== "timeline_event");
  }
  if (settings.existingFilesOnly) {
    candidates = candidates.filter((node) => node.kind !== "timeline_event");
  }

  const candidateIds = new Set(candidates.map((node) => node.id));
  let filteredEdges = edges.filter((edge) => candidateIds.has(edge.source) && candidateIds.has(edge.target));
  let degree = degreeMap(filteredEdges);
  const orphanCount = candidates.filter((node) => (degree.get(node.id) ?? 0) === 0).length;
  if (!settings.showOrphans) {
    candidates = candidates.filter((node) => (degree.get(node.id) ?? 0) > 0 || node.id === selectedNode?.id);
  }

  const totalBeforeLimit = candidates.length;
  degree = degreeMap(filteredEdges);
  candidates = candidates
    .sort((a, b) => {
      if (a.id === selectedNode?.id) return -1;
      if (b.id === selectedNode?.id) return 1;
      const degreeDiff = (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0);
      if (degreeDiff !== 0) return degreeDiff;
      const kindDiff = kindRank(a.kind) - kindRank(b.kind);
      if (kindDiff !== 0) return kindDiff;
      return (b.date ?? "").localeCompare(a.date ?? "");
    })
    .slice(0, MAX_OBSIDIAN_NODES);

  const visibleIds = new Set(candidates.map((node) => node.id));
  filteredEdges = filteredEdges
    .filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target))
    .sort((a, b) => b.weight - a.weight)
    .slice(0, MAX_OBSIDIAN_EDGES);
  degree = degreeMap(filteredEdges);
  const depthByNode = localOnly && selectedNode ? graphDepthMap(selectedNode.id, filteredEdges, depth) : new Map<string, number>();
  const visibleAt = creationOrderMap(candidates);

  const graphNodes = candidates.map((node): ObsidianNodeDatum => {
    const nodeDegree = degree.get(node.id) ?? 0;
    return {
      node,
      r: nodeRadius(node, nodeDegree),
      color: nodeColor(node),
      label: shortNodeLabel(node, node.kind === "memory" ? 26 : 22),
      degree: nodeDegree,
      depth: depthByNode.get(node.id) ?? 0,
      visibleAt: visibleAt.get(node.id) ?? 1,
      groupLabel: groupLabelFor(node),
    };
  });

  return {
    nodes: graphNodes,
    edges: filteredEdges.map((edge) => ({
      id: edge.id,
      sourceId: edge.source,
      targetId: edge.target,
      weight: edge.weight,
      color: edgeColor(edge, nodes),
      kind: edge.kind,
    })),
    groups: buildGroups(graphNodes),
    totalBeforeLimit,
    hiddenByLimit: Math.max(0, totalBeforeLimit - graphNodes.length),
    orphanCount,
  };
}

function stepObsidianForceSimulation(nodesMap: Map<string, ObsidianSimNode>, edges: ObsidianEdgeDatum[], settings: ObsidianSettings) {
  const nodes = Array.from(nodesMap.values());
  const centerX = VIEWBOX_WIDTH / 2;
  const centerY = VIEWBOX_HEIGHT / 2;
  const centerStrength = settings.centerForce * 0.0018;
  const repelStrength = settings.repelForce * 18;
  const linkStrength = settings.linkForce * 0.012;

  for (const node of nodes) {
    if (node.pinned) continue;
    node.vx += (centerX - node.x) * centerStrength;
    node.vy += (centerY - node.y) * centerStrength;
  }

  for (let i = 0; i < nodes.length; i += 1) {
    const a = nodes[i];
    for (let j = i + 1; j < nodes.length; j += 1) {
      const b = nodes[j];
      let dx = b.x - a.x;
      let dy = b.y - a.y;
      let distanceSq = dx * dx + dy * dy;
      if (distanceSq < 0.01) {
        dx = stableUnit(`${a.node.id}:${b.node.id}`, "dx") - 0.5;
        dy = stableUnit(`${b.node.id}:${a.node.id}`, "dy") - 0.5;
        distanceSq = dx * dx + dy * dy + 0.01;
      }
      const distance = Math.sqrt(distanceSq);
      const minimum = a.r + b.r + 9;
      const strength = (repelStrength / Math.max(80, distanceSq)) + (distance < minimum ? (minimum - distance) * 0.02 : 0);
      const fx = (dx / distance) * strength;
      const fy = (dy / distance) * strength;
      if (!a.pinned) {
        a.vx -= fx;
        a.vy -= fy;
      }
      if (!b.pinned) {
        b.vx += fx;
        b.vy += fy;
      }
    }
  }

  for (const edge of edges) {
    const source = nodesMap.get(edge.sourceId);
    const target = nodesMap.get(edge.targetId);
    if (!source || !target) continue;
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const distance = Math.max(0.1, Math.sqrt(dx * dx + dy * dy));
    const targetDistance = settings.linkDistance * (edge.kind === "belongs_to_theme" ? 0.76 : 1) * (1 - Math.min(0.32, edge.weight * 0.12));
    const force = (distance - targetDistance) * linkStrength;
    const fx = (dx / distance) * force;
    const fy = (dy / distance) * force;
    if (!source.pinned) {
      source.vx += fx;
      source.vy += fy;
    }
    if (!target.pinned) {
      target.vx -= fx;
      target.vy -= fy;
    }
  }

  for (const node of nodes) {
    if (node.pinned) continue;
    node.vx *= 0.86;
    node.vy *= 0.86;
    node.x = clamp(node.x + node.vx, 16, VIEWBOX_WIDTH - 16);
    node.y = clamp(node.y + node.vy, 16, VIEWBOX_HEIGHT - 16);
  }
}

function buildNeighborhood(focusId: string | null, edges: ObsidianSimEdge[]): Set<string> {
  const ids = new Set<string>();
  if (!focusId) return ids;
  ids.add(focusId);
  for (const edge of edges) {
    if (edge.source.node.id === focusId) ids.add(edge.target.node.id);
    if (edge.target.node.id === focusId) ids.add(edge.source.node.id);
  }
  return ids;
}

function degreeMap(edges: Array<AtlasEdge | ObsidianEdgeDatum>): Map<string, number> {
  const counts = new Map<string, number>();
  for (const edge of edges) {
    const source = "source" in edge ? edge.source : edge.sourceId;
    const target = "target" in edge ? edge.target : edge.targetId;
    counts.set(source, (counts.get(source) ?? 0) + 1);
    counts.set(target, (counts.get(target) ?? 0) + 1);
  }
  return counts;
}

function expandGraphIds(rootId: string, edges: AtlasEdge[], depth: number): Set<string> {
  const ids = new Set([rootId]);
  let frontier = new Set([rootId]);
  for (let level = 0; level < depth; level += 1) {
    const next = new Set<string>();
    for (const edge of edges) {
      if (frontier.has(edge.source) && !ids.has(edge.target)) next.add(edge.target);
      if (frontier.has(edge.target) && !ids.has(edge.source)) next.add(edge.source);
    }
    for (const id of next) ids.add(id);
    frontier = next;
  }
  return ids;
}

function graphDepthMap(rootId: string, edges: AtlasEdge[], maxDepth: number): Map<string, number> {
  const depths = new Map([[rootId, 0]]);
  let frontier = new Set([rootId]);
  for (let depth = 1; depth <= maxDepth; depth += 1) {
    const next = new Set<string>();
    for (const edge of edges) {
      if (frontier.has(edge.source) && !depths.has(edge.target)) next.add(edge.target);
      if (frontier.has(edge.target) && !depths.has(edge.source)) next.add(edge.source);
    }
    for (const id of next) depths.set(id, depth);
    frontier = next;
  }
  return depths;
}

function creationOrderMap(nodes: AtlasNode[]): Map<string, number> {
  const sorted = [...nodes].sort((a, b) => (a.date ?? "9999").localeCompare(b.date ?? "9999"));
  const denominator = Math.max(1, sorted.length - 1);
  return new Map(sorted.map((node, index) => [node.id, index / denominator]));
}

function buildGroups(nodes: ObsidianNodeDatum[]) {
  const groups = new Map<string, { label: string; color: string; count: number; query: string }>();
  for (const item of nodes) {
    const label = item.groupLabel;
    const current = groups.get(label) ?? { label, color: item.color, count: 0, query: `group:${label}` };
    current.count += 1;
    if (item.node.kind === "memory") current.color = item.color;
    groups.set(label, current);
  }
  return Array.from(groups.values()).sort((a, b) => b.count - a.count);
}

function edgeColor(edge: AtlasEdge, nodes: AtlasNode[]): string {
  if (edge.kind === "belongs_to_theme") {
    const target = nodes.find((node) => node.id === edge.target);
    return target ? nodeColor(target) : "rgba(214, 219, 224, 0.58)";
  }
  if (edge.kind === "source") return "rgba(164, 180, 196, 0.42)";
  return "rgba(214, 219, 224, 0.62)";
}

function nodeRadius(node: AtlasNode, degree: number): number {
  const base = node.kind === "theme" ? 6.2 : node.kind === "project" ? 5.8 : node.kind === "decision" ? 5.4 : 4.2;
  return Math.min(16, base + Math.sqrt(Math.max(0, degree)) * 1.25 + (node.metrics?.roi?.leverage_score ?? 0) * 2.4);
}

function nodeColor(node: AtlasNode): string {
  if (node.kind === "decision") return "#ff7eb6";
  if (node.kind === "project") return "#8fd3ff";
  if (node.kind === "theme") return node.visual?.color ?? "#c7a7ff";
  if (node.kind === "category" || node.kind === "tier") return "#d6dbe0";
  const tier = normalizeMemoryTier(node.memory_tier);
  if (tier === "核心画像") return "#7ee8d4";
  if (tier === "一般") return node.visual?.color ?? "#8fd3ff";
  return node.visual?.color ?? "#9aa5b1";
}

function groupLabelFor(node: AtlasNode): string {
  if (node.kind !== "memory") return kindLabel(node.kind);
  return normalizeMemoryTier(node.memory_tier) || node.category || "记忆";
}

function kindRank(kind: AtlasNode["kind"]): number {
  return { theme: 0, project: 1, decision: 2, memory: 3, category: 4, tier: 5, timeline_event: 6 }[kind] ?? 9;
}

function kindLabel(kind: AtlasNode["kind"]): string {
  return { theme: "标签", project: "项目", decision: "决策", memory: "记忆", category: "分类", tier: "层级", timeline_event: "事件" }[kind] ?? "节点";
}

function shortNodeLabel(node: AtlasNode, length: number): string {
  const prefix = node.kind === "memory" ? "" : `${kindLabel(node.kind)} · `;
  return truncate(`${prefix}${node.label}`, length);
}

function formatDelta(deltaCount: number, deltaRate: number | null): string {
  const sign = deltaCount > 0 ? "+" : "";
  if (deltaRate === null) return `${sign}${deltaCount} / 无基准`;
  return `${sign}${deltaCount} / ${(deltaRate * 100).toFixed(2)}%`;
}

function stableUnit(value: string, salt: string): number {
  let hash = 2166136261;
  const input = `${salt}:${value}`;
  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return (hash % 1000000) / 1000000;
}

function smoothStep(value: number): number {
  const x = clamp(value, 0, 1);
  return x * x * (3 - 2 * x);
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function truncate(value: string, length: number): string {
  const text = value.replace(/\s+/g, " ").trim();
  return text.length > length ? `${text.slice(0, Math.max(0, length - 1))}…` : text;
}
