import {
  Activity,
  Blocks,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Cloud,
  Crosshair,
  Download,
  FilterX,
  GitBranch,
  LayoutDashboard,
  Network,
  Orbit,
  Pause,
  Play,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import type { ComponentType, CSSProperties, KeyboardEvent, WheelEvent } from "react";
import { Suspense, lazy, useCallback, useEffect, useMemo, useState } from "react";
import {
  emptyAtlas,
  filterMemoryNodes,
  getMemoryNodes,
  getNodeMap,
  getThemeNodes,
  loadMemoryAtlas,
  metricValues,
  normalizeMemoryTier,
  uniqueSorted,
  visibleGraphFor,
} from "./data/atlas";
import type { ActivityBucket, AtlasEdge, AtlasFilters, AtlasMetric, AtlasNode, MemoryAtlas, ViewKey } from "./types";

const GalaxyScene = lazy(() => import("./components/GalaxyScene").then((module) => ({ default: module.GalaxyScene })));
const ObsidianGraphScene = lazy(() => import("./components/ObsidianGraphScene").then((module) => ({ default: module.ObsidianGraphScene })));

const views: Array<{ key: ViewKey; label: string; icon: ComponentType<{ size?: number }> }> = [
  { key: "galaxy", label: "银河星云", icon: Orbit },
  { key: "notion", label: "Notion 关系地图", icon: Blocks },
  { key: "roi", label: "ROI 仪表盘", icon: LayoutDashboard },
  { key: "obsidian", label: "Obsidian 图谱", icon: Network },
  { key: "timeline", label: "时间轴", icon: CalendarDays },
  { key: "contribution", label: "贡献网格", icon: Activity },
  { key: "wordcloud", label: "词云洞察", icon: Cloud },
  { key: "search", label: "搜索与复盘", icon: Search },
  { key: "summary", label: "总结与迭代", icon: RefreshCw },
];

const defaultFilters: AtlasFilters = {
  query: "",
  source: "all",
  tier: "all",
  category: "all",
  theme: "all",
};

type ContributionScale = "day" | "week" | "month" | "year";
type WritebackAction = "update_statement" | "add_context" | "change_tier" | "flag_conflict" | "rollback_to_version";
type FilterKey = keyof AtlasFilters;

interface TimelineEvent {
  date: string;
  node_id: string;
  memory_id: string;
  label: string;
  memory_tier: string;
  category: string;
  importance: string;
}

interface TimelineLayoutControls {
  zoom: number;
  center: number;
  cursor: number;
}

interface DeltaStats {
  totalFiltered: number;
  totalMemory: number;
  recentCount: number;
  previousCount: number;
  deltaCount: number;
  deltaRate: number | null;
  recentDecisionCount: number;
  recentCoreCount: number;
  topCategory: string;
  latestDate: string;
}

interface FilteredAtlasSlice {
  memoryNodes: AtlasNode[];
  graphNodes: AtlasNode[];
  graphEdges: AtlasEdge[];
  timeline: TimelineEvent[];
  visibleNodeIds: Set<string>;
  deltaStats: DeltaStats;
  filterActive: boolean;
}

interface SourceOption {
  id: string;
  label: string;
  description: string;
  node_count: number;
}

interface PeriodCounts {
  date: string;
  label: string;
  activityScore: number;
  activityLevel: number;
  globalActivityScore: number;
  conversationCount: number;
  messageCount: number;
  memoryCount: number;
  decisionCount: number;
  coreMemoryCount: number;
  midLongMemoryCount: number;
  shortMemoryCount: number;
  filteredMemoryCount: number;
  filteredDecisionCount: number;
  filteredCoreCount: number;
  toolCallCount?: number;
  errorEventCount?: number;
  abortCount?: number;
  delta?: number;
  previousLabel?: string;
}

type TrendSlot = Pick<PeriodCounts, "activityLevel" | "activityScore"> | null;

interface ContributionPeriodDetail {
  scale: ContributionScale;
  bucket: PeriodCounts;
  relatedNodes: AtlasNode[];
}

interface HumanOverview {
  topicRows: Array<{ label: string; count: number }>;
  tierRows: Array<{ label: string; count: number }>;
  categoryRows: Array<{ label: string; count: number }>;
  rememberItems: string[];
  actionItems: string[];
  opportunityItems: string[];
  riskItems: string[];
}

interface SemanticInsight {
  label: string;
  count: number;
  roiScore: number;
  recentCount: number;
  nodes: AtlasNode[];
}

interface SemanticMatrixCell {
  topic: string;
  tier: string;
  count: number;
  nodes: AtlasNode[];
}

interface WordCloudItem {
  label: string;
  count: number;
  score: number;
  x: number;
  y: number;
  rotate: number;
  nodes: AtlasNode[];
}

interface WritebackProposal {
  schema_version: string;
  proposal_id: string;
  created_at: string;
  status: "draft_pending_agent_apply";
  target_ref: {
    node_id: string;
    memory_id: string;
    label: string;
    source_file: string;
    base_date: string;
  };
  action: WritebackAction;
  payload: {
    proposed_text: string;
    reason: string;
    current_tier: string;
    current_category: string;
  };
  version: {
    revision: number;
    parent_proposal_id: string | null;
    rollback_unit: string;
    supersedes_proposal_id?: string | null;
  };
  diff?: {
    base_text: string;
    proposed_text: string;
    length_delta: number;
    changed_segments: number;
    summary: string;
  };
  rollback?: {
    rollback_to_proposal_id: string;
    rollback_to_revision: number;
    rollback_text: string;
    rollback_reason: string;
  };
  review?: {
    human_summary: string;
    agent_next_step: string;
    conflict_policy: string;
    apply_status: "proposal_only_pending_agent_apply";
  };
  safety: {
    direct_frontend_mutation_of_active_memory: false;
    requires_conflict_check: true;
    requires_agent_or_human_apply: true;
    forbidden_payload: string[];
  };
}

interface HeatStop {
  stop: number;
  rgb: readonly [number, number, number];
}

interface RuntimeState {
  runStartedAt: Date;
  snapshotLoadedAt: Date | null;
  lifecycle: "载入中" | "已同步" | "读取失败";
  serverMode: "检测中" | "本地自释放" | "静态托管";
}

const WRITEBACK_QUEUE_KEY = "memory-atlas.writeback.proposals.v1";
const TRANSIENT_STORAGE_PREFIXES = ["memory-atlas.runtime.", "memory-atlas.cache.", "memory-atlas.temp.", "memory-atlas.view."];
const TRANSIENT_CACHE_PREFIXES = ["memory-atlas", "memory_atlas", "vite-memory-atlas"];
const LOCAL_RUNTIME_HEARTBEAT_MS = 10_000;
const weekdayLabels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
const heatStops: HeatStop[] = [
  { stop: 0, rgb: [15, 17, 22] },
  { stop: 0.1, rgb: [23, 34, 58] },
  { stop: 0.24, rgb: [29, 63, 119] },
  { stop: 0.4, rgb: [31, 109, 178] },
  { stop: 0.58, rgb: [31, 155, 209] },
  { stop: 0.76, rgb: [72, 199, 232] },
  { stop: 0.9, rgb: [126, 224, 248] },
  { stop: 1, rgb: [167, 236, 255] },
];
const heatLevelAnchors = [0, 0.16, 0.34, 0.54, 0.74, 0.93] as const;
const emptyHeatColor = "#0f1116";

const writebackActionLabels: Record<WritebackAction, string> = {
  update_statement: "更新记忆表述",
  add_context: "补充长期上下文",
  change_tier: "调整层级/分类",
  flag_conflict: "标记冲突或过时",
  rollback_to_version: "生成回滚提案",
};

async function clearTransientBrowserState(): Promise<void> {
  try {
    window.sessionStorage.clear();
  } catch {
    // Browser privacy settings may block storage access during page release.
  }
  try {
    for (let index = window.localStorage.length - 1; index >= 0; index -= 1) {
      const key = window.localStorage.key(index);
      if (!key || key === WRITEBACK_QUEUE_KEY) continue;
      if (TRANSIENT_STORAGE_PREFIXES.some((prefix) => key.startsWith(prefix))) {
        window.localStorage.removeItem(key);
      }
    }
  } catch {
    // Keep release best-effort; the server shutdown signal is still sent.
  }
  try {
    if ("caches" in window) {
      const cacheKeys = await caches.keys();
      await Promise.all(
        cacheKeys
          .filter((key) => TRANSIENT_CACHE_PREFIXES.some((prefix) => key.startsWith(prefix)))
          .map((key) => caches.delete(key)),
      );
    }
  } catch {
    // Cache Storage may be unavailable for static previews or blocked profiles.
  }
  try {
    if ("serviceWorker" in navigator) {
      const registrations = await navigator.serviceWorker.getRegistrations();
      await Promise.all(
        registrations
          .filter((registration) => registration.scope.includes("memory-atlas") || registration.scope.includes("127.0.0.1"))
          .map((registration) => registration.unregister()),
      );
    }
  } catch {
    // Memory Atlas does not depend on a service worker; unregister is best-effort cleanup.
  }
}

export function App() {
  const [activeView, setActiveView] = useState<ViewKey>("galaxy");
  const [filters, setFilters] = useState<AtlasFilters>(defaultFilters);
  const [atlas, setAtlas] = useState<MemoryAtlas>(emptyAtlas);
  const [selectedNode, setSelectedNode] = useState<AtlasNode | null>(null);
  const [selectedContributionPeriod, setSelectedContributionPeriod] = useState<ContributionPeriodDetail | null>(null);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [loadError, setLoadError] = useState("");
  const [runtimeState, setRuntimeState] = useState<RuntimeState>(() => ({
    runStartedAt: new Date(),
    snapshotLoadedAt: null,
    lifecycle: "载入中",
    serverMode: "检测中",
  }));

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    const runStartedAt = new Date();
    setRuntimeState((current) => ({ ...current, runStartedAt, snapshotLoadedAt: null, lifecycle: "载入中" }));
    loadMemoryAtlas(controller.signal)
      .then((loadedAtlas) => {
        if (cancelled) return;
        setAtlas(loadedAtlas);
        setSelectedNode(getMemoryNodes(loadedAtlas)[0] ?? loadedAtlas.nodes[0] ?? null);
        setLoadState("ready");
        setRuntimeState((current) => ({ ...current, snapshotLoadedAt: new Date(), lifecycle: "已同步" }));
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        if (cancelled) return;
        setLoadError(error instanceof Error ? error.message : "未知 Memory Atlas 读取错误");
        setLoadState("error");
        setRuntimeState((current) => ({ ...current, snapshotLoadedAt: null, lifecycle: "读取失败" }));
      });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    let heartbeatTimer = 0;
    let heartbeatEnabled = false;
    let released = false;

    const release = (reason: "page_release" | "react_unmount" = "page_release") => {
      if (!heartbeatEnabled || released) return;
      released = true;
      window.clearInterval(heartbeatTimer);
      void clearTransientBrowserState();
      const payload = new Blob([JSON.stringify({ reason, at: new Date().toISOString() })], {
        type: "application/json",
      });
      if (navigator.sendBeacon) {
        navigator.sendBeacon("/__memory_atlas_release", payload);
        return;
      }
      void fetch("/__memory_atlas_release", { method: "POST", body: payload, keepalive: true }).catch(() => undefined);
    };

    const handlePageRelease = () => release("page_release");

    const heartbeat = () => {
      if (!heartbeatEnabled) return;
      void fetch("/__memory_atlas_heartbeat", {
        method: "POST",
        cache: "no-store",
        keepalive: true,
      }).catch(() => undefined);
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") heartbeat();
    };

    fetch("/__memory_atlas_runtime_state", { cache: "no-store" })
      .then((response) => {
        if (cancelled || !response.ok) return;
        heartbeatEnabled = true;
        setRuntimeState((current) => ({ ...current, serverMode: "本地自释放" }));
        heartbeat();
        heartbeatTimer = window.setInterval(heartbeat, LOCAL_RUNTIME_HEARTBEAT_MS);
        window.addEventListener("pagehide", handlePageRelease);
        window.addEventListener("beforeunload", handlePageRelease);
        document.addEventListener("visibilitychange", handleVisibilityChange);
      })
      .catch(() => {
        if (!cancelled) {
          setRuntimeState((current) => ({ ...current, serverMode: "静态托管" }));
        }
      });

    const fallbackTimer = window.setTimeout(() => {
      if (!heartbeatEnabled && !cancelled) {
        setRuntimeState((current) => ({ ...current, serverMode: "静态托管" }));
      }
    }, 1200);

    return () => {
      cancelled = true;
      window.clearInterval(heartbeatTimer);
      window.clearTimeout(fallbackTimer);
      window.removeEventListener("pagehide", handlePageRelease);
      window.removeEventListener("beforeunload", handlePageRelease);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      release("react_unmount");
    };
  }, []);

  const memoryNodes = useMemo(() => getMemoryNodes(atlas), [atlas]);
  const sourceMemoryNodes = useMemo(
    () => memoryNodes.filter((node) => sourceMatchesNode(node, filters.source)),
    [filters.source, memoryNodes],
  );
  const scopedAtlas = useMemo(
    () => buildSourceScopedAtlas(atlas, sourceMemoryNodes, filters.source),
    [atlas, filters.source, sourceMemoryNodes],
  );
  const themeNodes = useMemo(() => getThemeNodes(scopedAtlas), [scopedAtlas]);
  const nodeMap = useMemo(() => getNodeMap(scopedAtlas), [scopedAtlas]);
  const sourceOptions = useMemo(() => buildSourceOptions(atlas, memoryNodes), [atlas, memoryNodes]);
  const categories = useMemo(() => uniqueSorted(sourceMemoryNodes.map((node) => node.category)), [sourceMemoryNodes]);
  const tiers = useMemo(() => uniqueSorted(sourceMemoryNodes.map((node) => normalizeMemoryTier(node.memory_tier))), [sourceMemoryNodes]);
  const themeOptions = useMemo(
    () =>
      themeNodes
        .map((node) => ({ id: node.visual?.cluster ?? node.id.replace("theme:", ""), label: node.label }))
        .sort((a, b) => a.label.localeCompare(b.label, "zh-CN")),
    [themeNodes],
  );
  const filteredMemoryNodes = useMemo(() => filterMemoryNodes(sourceMemoryNodes, filters), [sourceMemoryNodes, filters]);
  const slice = useMemo(
    () => buildFilteredSlice(scopedAtlas, filteredMemoryNodes, filters),
    [scopedAtlas, filteredMemoryNodes, filters],
  );

  const handleSelectNode = useCallback((node: AtlasNode) => {
    setSelectedContributionPeriod(null);
    setSelectedNode(node);
  }, []);
  const handleSelectContributionPeriod = useCallback((detail: ContributionPeriodDetail) => {
    setSelectedContributionPeriod(detail);
  }, []);
  const updateFilters = useCallback((updater: (current: AtlasFilters) => AtlasFilters) => {
    setSelectedContributionPeriod(null);
    setSelectedNode(null);
    setFilters(updater);
  }, []);
  const switchView = useCallback((view: ViewKey) => {
    if (view !== "contribution") {
      setSelectedContributionPeriod(null);
    }
    setActiveView(view);
  }, []);
  const selectAdjacentNode = useCallback(
    (direction: -1 | 1) => {
      const candidates = selectableLensNodes(slice, selectedNode);
      if (candidates.length < 2) return;
      const currentIndex = candidates.findIndex((node) => node.id === selectedNode?.id);
      if (currentIndex < 0) return;
      const nextIndex = (currentIndex + direction + candidates.length) % candidates.length;
      handleSelectNode(candidates[nextIndex]);
    },
    [handleSelectNode, selectedNode, slice],
  );
  const focusSelectedTheme = useCallback(() => {
    const theme = selectedNode?.visual?.cluster;
    if (!theme) return;
    updateFilters((current) => ({ ...current, theme }));
  }, [selectedNode?.visual?.cluster, updateFilters]);
  const clearFilter = useCallback(
    (key: FilterKey) => {
      updateFilters((current) => {
        if (key === "query") return { ...current, query: "" };
        if (key === "source") return { ...current, source: "all", tier: "all", category: "all", theme: "all" };
        return { ...current, [key]: "all" };
      });
    },
    [updateFilters],
  );
  const resetFilters = useCallback(() => updateFilters(() => defaultFilters), [updateFilters]);

  useEffect(() => {
    if (loadState !== "ready") return;
    if (selectedNode && selectionStillVisible(selectedNode, slice)) return;
    setSelectedNode(slice.memoryNodes[0] ?? slice.graphNodes[0] ?? scopedAtlas.nodes[0] ?? null);
  }, [loadState, scopedAtlas.nodes, selectedNode, slice.filterActive, slice.graphNodes, slice.memoryNodes, slice.visibleNodeIds]);

  const generatedAt = atlas.overview.generated_at
    ? new Date(atlas.overview.generated_at).toLocaleString("zh-CN")
    : "尚未载入";
  const loadedAt = runtimeState.snapshotLoadedAt ? runtimeState.snapshotLoadedAt.toLocaleString("zh-CN") : "读取中";
  const runtimeStatus = `${runtimeState.lifecycle} / ${runtimeState.serverMode}`;
  const selectedTitle = views.find((view) => view.key === activeView)?.label ?? "记忆星图";
  const wideView = activeView === "contribution";

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="记忆星图导航">
        <div className="brand">
          <GitBranch size={22} />
          <div>
            <strong>记忆星图</strong>
            <span>OpenAIDatabase</span>
          </div>
        </div>
        <nav className="nav-list">
          {views.map((view) => {
            const Icon = view.icon;
            return (
              <button
                className={activeView === view.key ? "nav-item active" : "nav-item"}
                key={view.key}
                onClick={() => switchView(view.key)}
                title={view.label}
                type="button"
              >
                <Icon size={18} />
                <span>{view.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <span>快照生成时间</span>
          <strong>{generatedAt}</strong>
          <span>本次读取时间</span>
          <strong>{loadedAt}</strong>
          <span>运行状态</span>
          <strong>{runtimeStatus}</strong>
        </div>
      </aside>

      <main className={wideView ? "workspace contribution-workspace" : "workspace"}>
        <header className="topbar">
          <div>
            <p className="eyebrow">本地记忆 / 使用行为 / 后续动作</p>
            <h1>{selectedTitle}</h1>
          </div>
          <div className="stat-strip" aria-label="星图总览">
            <Metric label="记忆" value={scopedAtlas.overview.active_memory_count} />
            <Metric label="节点" value={scopedAtlas.overview.node_count} />
            <Metric label="连接" value={scopedAtlas.overview.edge_count} />
            <Metric label="活动" value={scopedAtlas.overview.conversation_count} />
          </div>
        </header>

        {loadState === "error" ? (
          <div className="load-banner" role="alert">
            <strong>星图读取失败</strong>
            <span>{loadError}</span>
          </div>
        ) : null}

        <section className="controls" aria-label="星图筛选器">
          <label className="search-box">
            <Search size={18} />
            <input
              value={filters.query}
              onChange={(event) => updateFilters((current) => ({ ...current, query: event.target.value }))}
            placeholder="搜索主题、项目、记忆、规则"
            />
          </label>
          <label className="select-filter source-filter">
            <span>分析对象</span>
            <select
              value={filters.source}
              onChange={(event) =>
                updateFilters((current) => ({
                  ...current,
                  source: event.target.value,
                  tier: "all",
                  category: "all",
                  theme: "all",
                }))
              }
            >
              {sourceOptions.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.label}
                </option>
              ))}
            </select>
          </label>
          <SelectFilter
            label="层级"
            value={filters.tier}
            options={tiers}
            onChange={(value) => updateFilters((current) => ({ ...current, tier: value }))}
          />
          <SelectFilter
            label="分类"
            value={filters.category}
            options={categories}
            onChange={(value) => updateFilters((current) => ({ ...current, category: value }))}
          />
          <label className="select-filter">
            <span>主题</span>
            <select value={filters.theme} onChange={(event) => updateFilters((current) => ({ ...current, theme: event.target.value }))}>
              <option value="all">全部</option>
              {themeOptions.map((theme) => (
                <option key={theme.id} value={theme.id}>
                  {theme.label}
                </option>
              ))}
            </select>
          </label>
        </section>

        <InteractionLens
          activeView={activeView}
          filters={filters}
          selectedContributionPeriod={activeView === "contribution" ? selectedContributionPeriod : null}
          selectedNode={selectedNode}
          slice={slice}
          sourceOptions={sourceOptions}
          onClearFilter={clearFilter}
          onFocusTheme={focusSelectedTheme}
          onResetFilters={resetFilters}
          onSelectAdjacent={selectAdjacentNode}
        />

        <div className={wideView ? "content-grid wide-view" : "content-grid"}>
          <section className="view-surface">
            <ViewRouter
              activeView={activeView}
              atlas={scopedAtlas}
              filters={filters}
              slice={slice}
              nodeMap={nodeMap}
              selectedNode={selectedNode}
              loadState={loadState}
              onSelectNode={handleSelectNode}
              onSelectContributionPeriod={handleSelectContributionPeriod}
            />
          </section>
          {activeView === "contribution" && selectedContributionPeriod ? (
            <ContributionPeriodInspector detail={selectedContributionPeriod} onSelectNode={handleSelectNode} />
          ) : (
            <NodeInspector atlas={scopedAtlas} node={selectedNode} edgeCount={edgeCountFor(selectedNode?.id, scopedAtlas.edges)} />
          )}
        </div>
      </main>
    </div>
  );
}

function ViewRouter({
  activeView,
  atlas,
  filters,
  slice,
  nodeMap,
  selectedNode,
  loadState,
  onSelectNode,
  onSelectContributionPeriod,
}: {
  activeView: ViewKey;
  atlas: MemoryAtlas;
  filters: AtlasFilters;
  slice: FilteredAtlasSlice;
  nodeMap: Map<string, AtlasNode>;
  selectedNode: AtlasNode | null;
  loadState: "loading" | "ready" | "error";
  onSelectNode: (node: AtlasNode) => void;
  onSelectContributionPeriod: (detail: ContributionPeriodDetail) => void;
}) {
  if (loadState === "loading") {
    return <div className="galaxy-loading">正在载入记忆星图...</div>;
  }
  if (activeView === "galaxy") {
    return (
      <GalaxyView
        graphNodes={slice.graphNodes}
        graphEdges={slice.graphEdges}
        memoryCount={slice.memoryNodes.length}
        selectedNode={selectedNode}
        deltaStats={slice.deltaStats}
        onSelectNode={onSelectNode}
      />
    );
  }
  if (activeView === "notion") {
    return <NotionMap nodes={slice.graphNodes} edges={slice.graphEdges} selectedNode={selectedNode} deltaStats={slice.deltaStats} onSelectNode={onSelectNode} />;
  }
  if (activeView === "roi") {
    return <RoiDashboard atlas={atlas} nodes={slice.memoryNodes} deltaStats={slice.deltaStats} onSelectNode={onSelectNode} />;
  }
  if (activeView === "obsidian") {
    return <ObsidianGraph nodes={slice.graphNodes} edges={slice.graphEdges} selectedNode={selectedNode} deltaStats={slice.deltaStats} onSelectNode={onSelectNode} />;
  }
  if (activeView === "timeline") {
    return <TimelineView timeline={slice.timeline} nodeMap={nodeMap} selectedNode={selectedNode} deltaStats={slice.deltaStats} onSelectNode={onSelectNode} />;
  }
  if (activeView === "contribution") {
    return (
      <ContributionGrid
        atlas={atlas}
        nodes={slice.memoryNodes}
        filters={filters}
        deltaStats={slice.deltaStats}
        onSelectPeriod={onSelectContributionPeriod}
      />
    );
  }
  if (activeView === "wordcloud") {
    return <WordCloudView nodes={slice.memoryNodes} deltaStats={slice.deltaStats} onSelectNode={onSelectNode} />;
  }
  if (activeView === "summary") {
    return <SummaryIterationView atlas={atlas} nodes={slice.memoryNodes} deltaStats={slice.deltaStats} />;
  }
  return <SearchReview atlas={atlas} nodes={slice.memoryNodes} deltaStats={slice.deltaStats} onSelectNode={onSelectNode} />;
}

function GalaxyView({
  graphNodes,
  graphEdges,
  memoryCount,
  selectedNode,
  deltaStats,
  onSelectNode,
}: {
  graphNodes: AtlasNode[];
  graphEdges: AtlasEdge[];
  memoryCount: number;
  selectedNode: AtlasNode | null;
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  return (
    <div className="galaxy-view">
      <div className="surface-heading">
        <div>
          <p className="eyebrow">语义银河 / 记忆关系 / 增量观察</p>
          <h2>按主题关系探索记忆密度、局部邻域和近期增量</h2>
        </div>
        <span>{memoryCount} 条记忆 / {graphNodes.length} 个节点 / {graphEdges.length} 条连接</span>
      </div>
      <DeltaStrip stats={deltaStats} />
      <Suspense fallback={<div className="galaxy-loading">正在载入 Three.js 银河...</div>}>
        <GalaxyScene nodes={graphNodes} edges={graphEdges} selectedNode={selectedNode} onSelectNode={onSelectNode} />
      </Suspense>
    </div>
  );
}

function NotionMap({
  nodes,
  edges,
  selectedNode,
  deltaStats,
  onSelectNode,
}: {
  nodes: AtlasNode[];
  edges: AtlasEdge[];
  selectedNode: AtlasNode | null;
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const display = useMemo(() => buildMapLayout(nodes, edges, 170), [nodes, edges]);
  return (
    <div className="visual-workspace notion-map">
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">数据库关系地图</p>
          <h2>把 Notion 式数据库关系转成主题、项目、决策、记忆的可探索地图</h2>
        </div>
        <span>{display.nodes.length} 个节点 / {display.edges.length} 条连接</span>
      </div>
      <GraphUsageStrip
        items={[
          { label: "主题簇", value: "外圈分组" },
          { label: "点击节点", value: "右侧详情" },
          { label: "适合查看", value: "项目和决策关系" },
        ]}
      />
      <DeltaStrip stats={deltaStats} compact />
      <svg className="relation-canvas" viewBox="0 0 1000 620" role="img" aria-label="Notion 关系地图">
        <defs>
          <filter id="softGlow">
            <feGaussianBlur stdDeviation="1.25" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <g opacity="0.13">
          {display.edges.map((edge) => (
            <line
              key={edge.id}
              x1={edge.source.x}
              y1={edge.source.y}
              x2={edge.target.x}
              y2={edge.target.y}
              stroke={edge.color}
              strokeWidth={Math.max(0.45, edge.weight * 1.65)}
            />
          ))}
        </g>
        {display.groups.map((group) => (
          <g key={group.id}>
            <circle cx={group.x} cy={group.y} r={group.r} fill={group.color} opacity="0.026" />
            <circle cx={group.x} cy={group.y} r={group.r} fill="none" stroke={group.color} strokeDasharray="8 12" opacity="0.16" />
          </g>
        ))}
        {display.nodes.map((item) => (
          <GraphSvgNode
            key={item.node.id}
            item={item}
            selected={item.node.id === selectedNode?.id}
            onSelectNode={onSelectNode}
          />
        ))}
      </svg>
      <div className="map-legend">
        <LegendItem color="#8fd3ff" label="主题/数据库中心" />
        <LegendItem color="#f48fb1" label="决策信标" />
        <LegendItem color="#7ee8d4" label="核心画像/高权重" />
        <LegendItem color="#94a3b8" label="临时/外层信息" />
      </div>
    </div>
  );
}

function RoiDashboard({
  atlas,
  nodes,
  deltaStats,
  onSelectNode,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const tierValues = filteredMetricValues(nodes, "memory_tier");
  const categoryValues = filteredMetricValues(nodes, "category");
  const globalTierValues = metricValues(atlas, "tier");
  const tierRows = topRows(tierValues, 4);
  const categoryRows = topRows(remapValues(categoryValues, humanCategoryLabel), 8);
  const actionRows = topRows(countBy(nodes, (node) => translateAction(node.metrics?.roi?.recommended_action)), 5);
  const highLeverage = [...nodes]
    .sort((a, b) => (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0))
    .slice(0, 12);
  return (
    <div className="dashboard-grid">
      <InsightCard title="当前切片密度" value={nodes.length} note={`全库 ${atlas.overview.active_memory_count.toLocaleString()} 条中的筛选结果`} />
      <InsightCard title="长期资产密度" value={sumValues(tierValues, ["核心画像", "一般"])} note="当前筛选中的核心画像 + 一般" />
      <InsightCard title="临时信息池" value={tierValues["临时"] ?? 0} note={`全局临时 ${globalTierValues["临时"] ?? 0} 条；保留但低权重召回`} />
      <InsightCard title="近期增量" value={deltaStats.recentCount} note={`近 30 天较前 30 天 ${formatSigned(deltaStats.deltaCount)} 条`} />
      <section className="wide-panel roi-visual-strip" aria-label="ROI 视觉密度分布">
        <div className="panel-title-row">
          <h2>ROI 视觉分布</h2>
          <span>层级、分类和建议动作同步当前筛选</span>
        </div>
        <div className="roi-mini-bars">
          <MiniBarList title="层级资产" rows={tierRows} />
          <MiniBarList title="主题分类" rows={categoryRows} />
          <MiniBarList title="建议动作" rows={actionRows} />
        </div>
      </section>
      <section className="wide-panel">
        <div className="panel-title-row">
          <h2>优先观察的高杠杆记忆</h2>
          <span>当前分类热点：{topEntry(categoryValues)?.[0] ?? "暂无"}</span>
        </div>
        <ol>
          {highLeverage.map((node) => (
            <li key={node.id}>
              <button onClick={() => onSelectNode(node)} type="button">
                <strong>{formatScore(node.metrics?.roi?.leverage_score)}</strong>
                <span>{node.label}</span>
                <small>{translateAction(node.metrics?.roi?.recommended_action)} / {translateStaleness(node.metrics?.roi?.staleness_status)}</small>
              </button>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function ObsidianGraph({
  nodes,
  edges,
  selectedNode,
  deltaStats,
  onSelectNode,
}: {
  nodes: AtlasNode[];
  edges: AtlasEdge[];
  selectedNode: AtlasNode | null;
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  return (
    <Suspense fallback={<div className="galaxy-loading">正在载入 Obsidian 动态图谱...</div>}>
      <ObsidianGraphScene nodes={nodes} edges={edges} selectedNode={selectedNode} deltaStats={deltaStats} onSelectNode={onSelectNode} />
    </Suspense>
  );
}

function TimelineView({
  timeline,
  nodeMap,
  selectedNode,
  deltaStats,
  onSelectNode,
}: {
  timeline: TimelineEvent[];
  nodeMap: Map<string, AtlasNode>;
  selectedNode: AtlasNode | null;
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const [timelineZoom, setTimelineZoom] = useState(1);
  const [timelineCenter, setTimelineCenter] = useState(0.5);
  const [timelineCursor, setTimelineCursor] = useState(1);
  const [timelinePlaying, setTimelinePlaying] = useState(false);
  const [hoveredEventId, setHoveredEventId] = useState<string | null>(null);
  const display = useMemo(
    () => buildTimelineLayout(timeline, nodeMap, { zoom: timelineZoom, center: timelineCenter, cursor: timelineCursor }),
    [timeline, nodeMap, timelineCenter, timelineCursor, timelineZoom],
  );
  const hoveredEvent = useMemo(
    () => display.events.find((event) => event.id === hoveredEventId) ?? display.events.find((event) => event.source.node_id === selectedNode?.id) ?? display.events[display.events.length - 1] ?? null,
    [display.events, hoveredEventId, selectedNode?.id],
  );

  useEffect(() => {
    setTimelinePlaying(false);
    setTimelineCursor(1);
  }, [timeline.length]);

  useEffect(() => {
    if (!timelinePlaying) return undefined;
    const timer = window.setInterval(() => {
      setTimelineCursor((current) => {
        if (current >= 0.995) {
          setTimelinePlaying(false);
          return 1;
        }
        return Math.min(1, current + 0.012);
      });
    }, 180);
    return () => window.clearInterval(timer);
  }, [timelinePlaying]);

  const clampTimelineCenter = useCallback((value: number) => {
    setTimelineCenter(Math.min(1, Math.max(0, value)));
  }, []);
  const clampTimelineZoom = useCallback((value: number) => {
    setTimelineZoom(Math.min(8, Math.max(1, Number(value.toFixed(2)))));
  }, []);
  const handleTimelineWheel = useCallback((event: WheelEvent<SVGSVGElement>) => {
    event.preventDefault();
    clampTimelineZoom(timelineZoom + (event.deltaY < 0 ? 0.45 : -0.45));
  }, [clampTimelineZoom, timelineZoom]);

  function resetTimelineView() {
    setTimelineZoom(1);
    setTimelineCenter(0.5);
    setTimelineCursor(1);
    setTimelinePlaying(false);
  }

  return (
    <div className="visual-workspace timeline-map">
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">时间轴 / 动态窗口 / 事件密度</p>
          <h2>按真实日期播放、缩放和定位记忆、决策、项目事件</h2>
        </div>
        <span>{display.visibleCount} / {display.totalCount} 个事件 · {display.rangeLabel}</span>
      </div>
      <DeltaStrip stats={deltaStats} compact />
      <div className="timeline-control-bar" aria-label="时间轴控制">
        <button aria-label={timelinePlaying ? "暂停时间轴播放" : "播放时间轴"} className="icon-control" onClick={() => setTimelinePlaying((value) => !value)} type="button">
          {timelinePlaying ? <Pause size={15} /> : <Play size={15} />}
        </button>
        <button aria-label="缩小时间窗口" className="icon-control" onClick={() => clampTimelineZoom(timelineZoom - 0.5)} disabled={timelineZoom <= 1} type="button">
          <ZoomOut size={15} />
        </button>
        <button aria-label="放大时间窗口" className="icon-control" onClick={() => clampTimelineZoom(timelineZoom + 0.5)} disabled={timelineZoom >= 8} type="button">
          <ZoomIn size={15} />
        </button>
        <label className="timeline-range-control">
          <span>窗口</span>
          <input aria-label="时间窗口中心" max="1" min="0" onChange={(event) => clampTimelineCenter(Number(event.target.value))} step="0.01" type="range" value={timelineCenter} />
        </label>
        <label className="timeline-range-control">
          <span>游标</span>
          <input aria-label="时间播放游标" max="1" min="0" onChange={(event) => setTimelineCursor(Number(event.target.value))} step="0.01" type="range" value={timelineCursor} />
        </label>
        <button className="segmented" onClick={resetTimelineView} type="button">
          <RotateCcw size={14} />
          重置
        </button>
        <span className="timeline-zoom-readout">{timelineZoom.toFixed(1)}x · {display.cursorLabel}</span>
      </div>
      <div className="timeline-summary-grid" aria-label="时间轴摘要">
        <div><span>窗口事件</span><strong>{display.visibleCount.toLocaleString()}</strong></div>
        <div><span>高重要/决策</span><strong>{display.importantCount.toLocaleString()}</strong></div>
        <div><span>核心画像</span><strong>{display.coreCount.toLocaleString()}</strong></div>
        <div><span>密度峰值</span><strong>{display.peakDensity.toLocaleString()}</strong></div>
      </div>
      <div className="timeline-density-track" aria-label="时间密度轨">
        {display.densityBands.map((band) => (
          <button
            aria-label={`${band.label} · ${band.count} 个事件`}
            className={band.active ? "timeline-density-band active" : "timeline-density-band"}
            key={band.key}
            onClick={() => clampTimelineCenter(band.center)}
            style={{ "--band-height": `${Math.max(8, band.intensity * 100)}%` } as CSSProperties}
            title={`${band.label} · ${band.count} 个事件`}
            type="button"
          />
        ))}
      </div>
      <svg className="timeline-canvas" viewBox="0 0 1000 640" role="img" aria-label="动态记忆时间轴" onWheel={handleTimelineWheel}>
        <defs>
          <filter id="softGlow">
            <feGaussianBlur stdDeviation="3.2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {display.densityBars.map((band) => (
          <rect className="timeline-density-backdrop" height={band.height} key={band.key} width={band.width} x={band.x} y={band.y} />
        ))}
        <line x1="80" x2="960" y1="540" y2="540" stroke="rgba(244,241,232,0.28)" strokeWidth="2" />
        {display.ticks.map((tick) => (
          <g key={tick.label}>
            <line x1={tick.x} x2={tick.x} y1="70" y2="548" stroke="rgba(244,241,232,0.08)" />
            <text x={tick.x} y="570" textAnchor="middle" className="axis-label">{tick.label}</text>
          </g>
        ))}
        {display.eventTicks.map((tick) => (
          <g className="event-date-tick" key={tick.date}>
            <title>{`${tick.date} · ${tick.count} 个真实事件`}</title>
            <line x1={tick.x} x2={tick.x} y1="528" y2="552" />
            <text x={tick.x} y={tick.stagger ? 612 : 594} textAnchor="middle" className="event-axis-label">{tick.label}</text>
          </g>
        ))}
        {display.lanes.map((lane) => (
          <g key={lane.key}>
            <line x1="80" x2="960" y1={lane.y} y2={lane.y} stroke={lane.color} opacity="0.2" />
            <text x="28" y={lane.y + 4} className="lane-label">{lane.label}</text>
          </g>
        ))}
        <g className="timeline-cursor">
          <line x1={display.cursorX} x2={display.cursorX} y1="58" y2="552" />
          <text x={display.cursorX} y="50" textAnchor="middle">{display.cursorLabel}</text>
        </g>
        {display.events.map((event) => {
          const node = event.node;
          const selected = event.source.node_id === selectedNode?.id;
          const hovered = event.id === hoveredEventId;
          const statusClass = event.future ? "future" : "past";
          return (
            <g
              className={`timeline-event ${statusClass}${selected ? " selected" : ""}${hovered ? " hovered" : ""}`}
              aria-label={`${event.source.date} · ${normalizeMemoryTier(event.source.memory_tier)} · ${event.source.label}`}
              key={event.id}
              role="button"
              tabIndex={node ? 0 : -1}
              onClick={() => {
                if (node) onSelectNode(node);
              }}
              onMouseEnter={() => setHoveredEventId(event.id)}
              onMouseLeave={() => setHoveredEventId(null)}
              onKeyDown={(keyboardEvent) => {
                if (node && isActivationKey(keyboardEvent)) onSelectNode(node);
              }}
            >
              <line x1={event.x} x2={event.x} y1={event.y} y2="540" stroke={event.color} opacity="0.28" />
              <circle cx={event.x} cy={event.y} r={event.radius} fill={event.color} filter="url(#softGlow)" />
              {(event.major || selected || hovered) ? (
                <text x={Math.min(930, event.x + 10)} y={event.y - 10} className="timeline-point-label">{event.shortLabel}</text>
              ) : null}
            </g>
          );
        })}
      </svg>
      <div className="timeline-event-detail-strip" aria-label="时间轴事件详情">
        {hoveredEvent ? (
          <>
            <div>
              <span>{hoveredEvent.source.date} · {normalizeMemoryTier(hoveredEvent.source.memory_tier)} · {humanCategoryLabel(hoveredEvent.source.category)}</span>
              <strong>{humanizeStatement(hoveredEvent.node?.statement) || hoveredEvent.source.label}</strong>
            </div>
            <button disabled={!hoveredEvent.node} onClick={() => hoveredEvent.node && onSelectNode(hoveredEvent.node)} type="button">
              同步详情
            </button>
          </>
        ) : (
          <p>移动到事件点查看内容；点击事件同步右侧详情。滚轮缩放，窗口滑块定位年份内局部阶段。</p>
        )}
      </div>
    </div>
  );
}

function ContributionGrid({
  atlas,
  nodes,
  filters,
  deltaStats,
  onSelectPeriod,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  filters: AtlasFilters;
  deltaStats: DeltaStats;
  onSelectPeriod: (detail: ContributionPeriodDetail) => void;
}) {
  const [scale, setScale] = useState<ContributionScale>("day");
  const availableYears = useMemo(() => contributionYears(atlas, nodes), [atlas, nodes]);
  const [selectedYear, setSelectedYear] = useState(() => availableYears[availableYears.length - 1] ?? new Date().getUTCFullYear());
  useEffect(() => {
    if (!availableYears.length) return;
    if (!availableYears.includes(selectedYear)) {
      setSelectedYear(availableYears[availableYears.length - 1]);
    }
  }, [availableYears, selectedYear]);
  const periodData = useMemo(() => buildContributionPeriods(atlas, nodes, filters, selectedYear), [atlas, nodes, filters, selectedYear]);
  const [selectedPeriod, setSelectedPeriod] = useState("");
  const selected = periodData.periods.get(selectedPeriod) ?? periodData.defaultPeriod;
  const selectedDetail = useMemo(
    () => buildContributionPeriodDetail(scale, selected, nodes),
    [nodes, scale, selected],
  );
  const isDayOrWeek = scale === "day" || scale === "week";
  const dayWeekModeClass = scale === "week" ? "week-mode" : "day-mode";

  useEffect(() => {
    setSelectedPeriod(defaultPeriodKeyForScale(scale, periodData));
  }, [periodData, scale]);

  useEffect(() => {
    onSelectPeriod(selectedDetail);
  }, [onSelectPeriod, selectedDetail]);

  return (
    <div className="contribution-view visual-workspace">
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">使用强度 / 记忆增量 / 时间尺度对比</p>
          <h2>按日、周、月、年观察交互强度和记忆增量</h2>
        </div>
        <span>{periodData.year} 年 / 数据 {atlas.contribution.range_start || "暂无"}-{atlas.contribution.range_end || "暂无"}</span>
      </div>
      <div className="contribution-toolbar">
        <DeltaStrip stats={deltaStats} compact />
        <div className="scale-tabs" role="group" aria-label="贡献网格尺度">
          {(["day", "week", "month", "year"] as ContributionScale[]).map((item) => (
            <button className={scale === item ? "segmented active" : "segmented"} key={item} onClick={() => setScale(item)} type="button">
              {scaleLabel(item)}
            </button>
          ))}
        </div>
        <label className="year-picker">
          <span>年份</span>
          <select value={selectedYear} onChange={(event) => setSelectedYear(Number(event.target.value))}>
            {availableYears.map((yearOption) => (
              <option key={yearOption} value={yearOption}>
                {yearOption}
              </option>
            ))}
          </select>
        </label>
      </div>
      <HeatLegend />
      {isDayOrWeek ? (
        <div className={`year-heatmap-wrap ${scale === "week" ? "week-scale" : "day-scale"}`}>
          <div className="year-heatmap-body">
            <div className="weekday-label-column" aria-hidden="true">
              {weekdayLabels.map((label) => (
                <span key={label}>{label}</span>
              ))}
            </div>
            <div
              className={`year-heatmap ${dayWeekModeClass}`}
              style={{
                "--week-columns": periodData.weekColumns,
              } as CSSProperties}
            >
              {scale === "week"
                ? periodData.weekCells.map((cell) => {
                    const active = selectedPeriod === cell.weekKey;
                    return (
                      <button
                        className={`week-cell level-${cell.activityLevel}${active ? " selected" : ""}`}
                        key={cell.weekKey}
                        onClick={() => setSelectedPeriod(cell.weekKey)}
                        style={
                          {
                            ...heatCellStyle(cell, periodData.weekMaxActivityScore),
                            gridColumn: cell.weekColumn + 1,
                            gridRow: "1 / span 7",
                            "--trend-gradient": trendGradient(cell.daySlots, "180deg", periodData.dayMaxActivityScore),
                          } as CSSProperties
                        }
                        title={contributionTitle(cell)}
                        type="button"
                      >
                        <div className="cell-trend week-trend smooth-trend" aria-hidden="true">
                          {cell.daySlots.map((slot, index) => (
                            <i
                              className={`trend-segment level-${slot?.activityLevel ?? 0}${slot ? "" : " empty"}`}
                              key={slot?.date ?? index}
                              style={trendSegmentStyle(slot, periodData.dayMaxActivityScore)}
                            />
                          ))}
                        </div>
                        <span>{cell.label}</span>
                      </button>
                    );
                  })
                : periodData.dailyCells.map((cell) => {
                    const active = selectedPeriod === cell.date;
                    return (
                      <button
                        className={`heat-cell level-${cell.activityLevel}${active ? " selected" : ""}`}
                        key={cell.date}
                        onClick={() => setSelectedPeriod(cell.date)}
                        style={{ ...heatCellStyle(cell, periodData.dayMaxActivityScore), gridColumn: cell.weekColumn + 1, gridRow: cell.weekday + 1 }}
                        title={contributionTitle(cell)}
                        type="button"
                      >
                        <span>{cell.date}</span>
                      </button>
                    );
                  })}
            </div>
          </div>
          <div className="week-label-shell">
            <span aria-hidden="true" />
            <div className="week-label-row" style={{ "--week-columns": periodData.weekColumns } as CSSProperties}>
              {Array.from({ length: periodData.weekColumns }, (_, index) => (
                <span key={index}>{index % 2 === 0 ? `W${index + 1}` : ""}</span>
              ))}
            </div>
          </div>
        </div>
      ) : scale === "year" ? (
        <div className="year-trend-grid vertical-year-trend">
          {periodData.yearCells.map((cell) => {
            const periodKey = String(cell.year);
            const active = selectedPeriod === periodKey;
            return (
              <button
                aria-label={`${cell.year} 年，活动得分 ${cell.activityScore}，环比 ${formatSigned(cell.delta ?? 0)}`}
                className={`year-cell year-summary-card level-${cell.activityLevel}${active ? " selected" : ""}`}
                key={periodKey}
                onClick={() => setSelectedPeriod(periodKey)}
                style={yearCellStyle(cell, periodData.yearMaxActivityScore)}
                title={contributionTitle(cell)}
                type="button"
              >
                <div className="year-card-header">
                  <strong>{cell.year}</strong>
                  <span>{cell.activityScore.toLocaleString()} 分</span>
                </div>
                <div className="year-month-track" aria-hidden="true">
                  {cell.monthSlots.map((slot) => (
                    <i className={`year-month-bar level-${slot.activityLevel}`} key={slot.date} style={monthBarStyle(slot, cell.monthSlots)} />
                  ))}
                </div>
                <div className="year-month-axis" aria-hidden="true">
                  <span>Q1</span>
                  <span>Q2</span>
                  <span>Q3</span>
                  <span>Q4</span>
                </div>
                <div className="year-card-footer">
                  <span>消息 {cell.messageCount.toLocaleString()}</span>
                  <span>记忆 {cell.filteredMemoryCount.toLocaleString()}</span>
                  <span className={(cell.delta ?? 0) >= 0 ? "positive" : "negative"}>{formatSigned(cell.delta ?? 0)}</span>
                </div>
                <span>{cell.label}</span>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="month-heatmap">
          {periodData.monthCells.map((cell) => {
            const periodKey = cell.date;
            const active = selectedPeriod === periodKey;
            const monthTrendMax = maxActivityScore(cell.daySlots);
            return (
              <button
                className={`month-cell level-${cell.activityLevel}${active ? " selected" : ""}`}
                key={cell.date}
                onClick={() => setSelectedPeriod(periodKey)}
                style={
                  {
                    ...heatCellStyle(cell, periodData.monthMaxActivityScore),
                    "--trend-gradient": trendGradient(cell.daySlots, "180deg", monthTrendMax),
                    "--month-days": cell.daySlots.length,
                  } as CSSProperties
                }
                title={contributionTitle(cell)}
                type="button"
              >
                <div className="cell-trend month-trend smooth-trend" aria-hidden="true">
                  {cell.daySlots.map((slot) => (
                    <i className={`trend-segment level-${slot.activityLevel}`} key={slot.date} style={trendSegmentStyle(slot, monthTrendMax)} />
                  ))}
                </div>
                <strong>{cell.monthLabel}</strong>
                <span>{cell.year}</span>
              </button>
            );
          })}
        </div>
      )}
      <div className="contribution-analysis">
        <InsightCard title="当前对象" value={selected.activityScore} note={`${selected.label}；活动得分`} />
        <InsightCard title="筛选记忆增量" value={selected.filteredMemoryCount} note={`当前筛选命中；决策 ${selected.filteredDecisionCount} 条`} />
        <InsightCard title="全局交互量" value={selected.messageCount} note={`对话 ${selected.conversationCount} 个；消息 ${selected.messageCount} 条`} />
        <InsightCard title="环比变化" value={selected.delta} note={`${selected.previousLabel} 对比 ${formatSigned(selected.delta)} 分`} />
      </div>
      <p className="note">
        说明：当前分析对象的真实数据范围显示在标题右侧；全年空格代表该对象当天为 0，不代表存在使用记录。层级/分类/主题筛选后的贡献增量来自当前筛选记忆节点日期聚合，避免伪造主题级消息数。
      </p>
    </div>
  );
}

function HeatLegend() {
  return (
    <div className="heat-legend" aria-label="贡献网格热度标尺">
      <span>热度趋势</span>
      <div className="heat-legend-gradient" role="img" aria-label="热度从 0、低频、中频到高频逐步增强">
        <b>0</b>
        <i aria-hidden="true" />
        <b>高</b>
      </div>
    </div>
  );
}

function WordCloudView({
  nodes,
  deltaStats,
  onSelectNode,
}: {
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const semantic = useMemo(() => buildSemanticInsights(nodes), [nodes]);
  const maxTopicCount = Math.max(1, ...semantic.topics.map((topic) => topic.count));
  const maxWordScore = Math.max(1, ...semantic.wordCloud.map((item) => item.score));

  function jumpToBestNode(candidates: AtlasNode[]) {
    const target = selectRepresentativeNode(candidates);
    if (target) onSelectNode(target);
  }

  return (
    <div className="visual-workspace semantic-workspace">
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">词云 / 语义热力 / 主题气泡</p>
          <h2>把当前筛选切片转成可点击的主题密度、关键词和机会信号</h2>
        </div>
        <span>{nodes.length.toLocaleString()} 条记忆 / {semantic.topics.length.toLocaleString()} 个主题</span>
      </div>
      <DeltaStrip stats={deltaStats} compact />
      <div className="semantic-dashboard" aria-label="词云洞察">
        <section className="semantic-panel semantic-heatmap" aria-label="主题层级热力图">
          <div className="panel-title-row">
            <h3>主题 x 层级 Heatmap</h3>
            <span>{semantic.tiers.join(" / ")}</span>
          </div>
          <div
            className="semantic-matrix"
            style={{ gridTemplateColumns: `minmax(76px, 1.1fr) repeat(${semantic.tiers.length}, minmax(42px, 0.7fr))` }}
          >
            <span className="semantic-axis-corner" aria-hidden="true" />
            {semantic.tiers.map((tier) => (
              <strong className="semantic-axis-label" key={tier}>{tier}</strong>
            ))}
            {semantic.matrixRows.map((topic) => (
              <div className="semantic-row" key={topic}>
                <b title={topic}>{topic}</b>
                {semantic.tiers.map((tier) => {
                  const cell = semantic.matrix.get(`${topic}::${tier}`) ?? { topic, tier, count: 0, nodes: [] };
                  return (
                    <button
                      aria-label={`${topic} / ${tier} / ${cell.count} 条`}
                      className="semantic-heat-cell"
                      disabled={!cell.nodes.length}
                      key={`${topic}-${tier}`}
                      onClick={() => jumpToBestNode(cell.nodes)}
                      style={semanticHeatStyle(cell.count, maxTopicCount)}
                      title={`${topic} · ${tier} · ${cell.count} 条`}
                      type="button"
                    >
                      <span>{cell.count}</span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </section>

        <section className="semantic-panel semantic-bubbles" aria-label="主题气泡图">
          <div className="panel-title-row">
            <h3>Bubble Chart</h3>
            <span>横轴 ROI / 纵轴近期增量</span>
          </div>
          <svg className="semantic-bubble-canvas" viewBox="0 0 520 330" role="img" aria-label="主题 ROI 与近期增量气泡图">
            <line x1="48" x2="494" y1="286" y2="286" />
            <line x1="48" x2="48" y1="28" y2="286" />
            <text x="494" y="312" textAnchor="end">ROI</text>
            <text x="12" y="38" transform="rotate(-90 12 38)">近期</text>
            {semantic.topics.slice(0, 18).map((topic, index) => {
              const radius = 10 + Math.sqrt(topic.count / maxTopicCount) * 28;
              const x = 62 + Math.min(1, Math.max(0, topic.roiScore)) * 406;
              const y = 270 - Math.min(1, topic.recentCount / Math.max(1, deltaStats.recentCount || topic.count)) * 218 - stableUnit(topic.label, "bubble-y") * 18;
              const color = semanticColor(index);
              return (
                <g
                  className="semantic-bubble"
                  key={topic.label}
                  role="button"
                  tabIndex={0}
                  onClick={() => jumpToBestNode(topic.nodes)}
                  onKeyDown={(event) => {
                    if (isActivationKey(event)) jumpToBestNode(topic.nodes);
                  }}
                >
                  <title>{`${topic.label} · ${topic.count} 条 · ROI ${topic.roiScore.toFixed(2)} · 近期 ${topic.recentCount}`}</title>
                  <circle cx={x} cy={y} r={radius} fill={color} />
                  <text x={x} y={y + 3} textAnchor="middle">{truncate(topic.label, radius > 28 ? 8 : 5)}</text>
                </g>
              );
            })}
          </svg>
        </section>

        <section className="semantic-panel semantic-cloud" aria-label="词云">
          <div className="panel-title-row">
            <h3>Word Cloud</h3>
            <span>点击词条跳转代表记忆</span>
          </div>
          <div className="word-cloud-field">
            {semantic.wordCloud.map((item) => (
              <button
                className="word-cloud-token"
                key={item.label}
                onClick={() => jumpToBestNode(item.nodes)}
                style={wordCloudStyle(item, maxWordScore)}
                title={`${item.label} · ${item.count} 条`}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function InteractionLens({
  activeView,
  filters,
  selectedContributionPeriod,
  selectedNode,
  slice,
  sourceOptions,
  onClearFilter,
  onFocusTheme,
  onResetFilters,
  onSelectAdjacent,
}: {
  activeView: ViewKey;
  filters: AtlasFilters;
  selectedContributionPeriod: ContributionPeriodDetail | null;
  selectedNode: AtlasNode | null;
  slice: FilteredAtlasSlice;
  sourceOptions: SourceOption[];
  onClearFilter: (key: FilterKey) => void;
  onFocusTheme: () => void;
  onResetFilters: () => void;
  onSelectAdjacent: (direction: -1 | 1) => void;
}) {
  const candidates = useMemo(() => selectableLensNodes(slice, selectedNode), [selectedNode, slice]);
  const selectedIndex = selectedNode ? candidates.findIndex((node) => node.id === selectedNode.id) : -1;
  const canStep = selectedIndex >= 0 && candidates.length > 1;
  const chips = useMemo(() => activeFilterChips(filters, sourceOptions), [filters, sourceOptions]);
  const focusTheme = selectedNode?.visual?.cluster;
  const viewLabel = views.find((view) => view.key === activeView)?.label ?? "当前视图";
  const focusTitle = selectedContributionPeriod
    ? `${scaleLabel(selectedContributionPeriod.scale)} · ${selectedContributionPeriod.bucket.label}`
    : selectedNode
      ? humanNodeDisplayTitle(selectedNode)
      : "暂无焦点";
  const focusMeta = selectedContributionPeriod
    ? `活动 ${selectedContributionPeriod.bucket.activityScore.toLocaleString()} / 筛选记忆 ${selectedContributionPeriod.bucket.filteredMemoryCount.toLocaleString()} / 环比 ${formatSigned(selectedContributionPeriod.bucket.delta ?? 0)}`
    : selectedNode
      ? `${normalizeMemoryTier(selectedNode.memory_tier)} / ${humanCategoryLabel(selectedNode.category)} / ${selectedNode.date || "未知日期"}`
      : "选择节点、事件或时间格后同步更新";

  return (
    <section className="interaction-lens" aria-label="当前交互焦点">
      <div className="lens-focus">
        <span className="lens-badge">{viewLabel}</span>
        <div>
          <strong>{focusTitle}</strong>
          <span>{focusMeta}</span>
        </div>
      </div>
      <div className="lens-stepper" aria-label="焦点切换">
        <button aria-label="上一个焦点" disabled={!canStep} onClick={() => onSelectAdjacent(-1)} title="上一个焦点" type="button">
          <ChevronLeft size={16} />
        </button>
        <span>{selectedIndex >= 0 ? `${selectedIndex + 1}/${candidates.length}` : `0/${candidates.length}`}</span>
        <button aria-label="下一个焦点" disabled={!canStep} onClick={() => onSelectAdjacent(1)} title="下一个焦点" type="button">
          <ChevronRight size={16} />
        </button>
      </div>
      <div className="lens-actions">
        <button disabled={!focusTheme || filters.theme === focusTheme} onClick={onFocusTheme} type="button">
          <Crosshair size={15} />
          <span>聚焦主题</span>
        </button>
        <button disabled={!chips.length} onClick={onResetFilters} type="button">
          <FilterX size={15} />
          <span>重置筛选</span>
        </button>
      </div>
      <div className="filter-chip-row" aria-label="活跃筛选">
        {chips.length ? (
          chips.map((chip) => (
            <button key={chip.key} onClick={() => onClearFilter(chip.key)} title={`清除${chip.label}`} type="button">
              <span>{chip.label}</span>
              <strong>{chip.value}</strong>
              <em aria-hidden="true">×</em>
            </button>
          ))
        ) : (
          <span className="filter-empty">全部数据</span>
        )}
      </div>
    </section>
  );
}

function selectableLensNodes(slice: FilteredAtlasSlice, selectedNode: AtlasNode | null): AtlasNode[] {
  if (selectedNode && slice.memoryNodes.some((node) => node.id === selectedNode.id)) return slice.memoryNodes;
  if (slice.memoryNodes.length && !selectedNode) return slice.memoryNodes;
  return slice.graphNodes;
}

function activeFilterChips(filters: AtlasFilters, sourceOptions: SourceOption[]): Array<{ key: FilterKey; label: string; value: string }> {
  const chips: Array<{ key: FilterKey; label: string; value: string }> = [];
  if (filters.source !== "all") chips.push({ key: "source", label: "对象", value: sourceOptions.find((source) => source.id === filters.source)?.label ?? filters.source });
  if (filters.query.trim()) chips.push({ key: "query", label: "搜索", value: filters.query.trim() });
  if (filters.tier !== "all") chips.push({ key: "tier", label: "层级", value: filters.tier });
  if (filters.category !== "all") chips.push({ key: "category", label: "分类", value: humanCategoryLabel(filters.category) });
  if (filters.theme !== "all") chips.push({ key: "theme", label: "主题", value: themeLabelFromCluster(filters.theme) });
  return chips;
}

function trendGradient(slots: TrendSlot[], direction: "90deg" | "180deg", maxScore = maxActivityScore(slots)) {
  const colors = fluidTrendIntensities(slots.map((slot) => trendIntensity(slot, maxScore)))
    .map(trendColorFromIntensity);
  if (!colors.length) return `linear-gradient(${direction}, ${trendColor(0)}, ${trendColor(0)})`;
  if (colors.length === 1) return `linear-gradient(${direction}, ${colors[0]}, ${colors[0]})`;
  const lastIndex = colors.length - 1;
  const stops = colors.map((color, index) => {
    const position = Number(((index / lastIndex) * 100).toFixed(2));
    return `${color} ${position}%`;
  });
  return `linear-gradient(${direction}, ${stops.join(", ")})`;
}

function trendIntensity(slot: TrendSlot, maxScore: number) {
  if (!slot) return 0;
  const score = Number(slot.activityScore ?? 0);
  if (score <= 0 && slot.activityLevel <= 0) return 0;
  return heatIntensityForScore(score, maxScore, slot.activityLevel);
}

function smoothTrendIntensities(values: number[]) {
  if (!values.some((value) => value > 0)) return values;
  return values.map((value, index) => {
    const previous = values[index - 1] ?? value;
    const next = values[index + 1] ?? value;
    const interpolated = previous * 0.2 + value * 0.6 + next * 0.2;
    return Math.min(1, Math.max(interpolated, value * 0.72));
  });
}

function fluidTrendIntensities(values: number[]) {
  if (values.length <= 1 || !values.some((value) => value > 0)) return values;
  const anchors = smoothTrendIntensities(values);
  const sampleCount = Math.max(anchors.length * 7, 18);
  const lastIndex = anchors.length - 1;
  return Array.from({ length: sampleCount }, (_, sampleIndex) => {
    const scaled = (sampleIndex / (sampleCount - 1)) * lastIndex;
    const index = Math.min(lastIndex - 1, Math.max(0, Math.floor(scaled)));
    const t = smoothStep(scaled - index);
    const p0 = anchors[Math.max(0, index - 1)];
    const p1 = anchors[index];
    const p2 = anchors[Math.min(lastIndex, index + 1)];
    const p3 = anchors[Math.min(lastIndex, index + 2)];
    return clamp(catmullRom(p0, p1, p2, p3, t), 0, 1);
  });
}

function smoothStep(value: number) {
  const t = clamp(value, 0, 1);
  return t * t * (3 - 2 * t);
}

function catmullRom(p0: number, p1: number, p2: number, p3: number, t: number) {
  const t2 = t * t;
  const t3 = t2 * t;
  return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3);
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function trendColorFromIntensity(value: number) {
  return value <= 0 ? emptyHeatColor : interpolateHeatColor(value);
}

function trendColor(slotOrLevel: TrendSlot | number, maxScore = 0) {
  if (slotOrLevel === null) return "rgba(9, 10, 13, 0.44)";
  const score = typeof slotOrLevel === "number" ? 0 : Number(slotOrLevel.activityScore ?? 0);
  const level = typeof slotOrLevel === "number" ? slotOrLevel : slotOrLevel.activityLevel;
  if (score <= 0 && level <= 0) return emptyHeatColor;
  return heatColorForScore(score, maxScore, level);
}

function trendSegmentStyle(slot: TrendSlot, maxScore: number): CSSProperties {
  const base = !slot
    ? heatCellStyle({ activityScore: 0, activityLevel: 0 }, maxScore)
    : heatCellStyle({ activityScore: Number(slot.activityScore ?? 0), activityLevel: slot.activityLevel }, maxScore);
  return {
    ...base,
    "--segment-color": trendColor(slot, maxScore),
  } as CSSProperties;
}

function heatCellStyle(bucket: Pick<PeriodCounts, "activityScore" | "activityLevel">, maxScore: number): CSSProperties {
  const color = heatColorForScore(bucket.activityScore, maxScore, bucket.activityLevel);
  const strong = bucket.activityScore > 0 || bucket.activityLevel > 0;
  return {
    "--heat-bg": strong
      ? `linear-gradient(145deg, ${withAlpha(color, 0.82)} 0%, ${color} 100%)`
      : "rgba(15, 17, 22, 0.96)",
    "--heat-border": strong ? withAlpha(color, 0.72) : "rgba(244, 241, 232, 0.08)",
    "--heat-shadow": strong ? `0 0 16px ${withAlpha(color, 0.24)}, inset 0 0 0 1px rgba(255, 255, 255, 0.05)` : "inset 0 0 0 1px rgba(244, 241, 232, 0.04)",
  } as CSSProperties;
}

function yearCellStyle(bucket: Pick<PeriodCounts, "activityScore" | "activityLevel">, maxScore: number): CSSProperties {
  return {
    ...heatCellStyle(bucket, maxScore),
    "--year-accent": heatColorForScore(bucket.activityScore, maxScore, bucket.activityLevel),
  } as CSSProperties;
}

function monthBarStyle(slot: Pick<PeriodCounts, "activityScore" | "activityLevel">, slots: Array<Pick<PeriodCounts, "activityScore">>): CSSProperties {
  const maxScore = maxActivityScore(slots);
  const score = Math.max(0, slot.activityScore);
  const ratio = maxScore > 0 ? score / maxScore : 0;
  const height = score > 0 ? Math.round(24 + Math.sqrt(ratio) * 76) : 9;
  return {
    "--month-color": trendColor(slot, maxScore),
    "--month-height": `${height}%`,
  } as CSSProperties;
}

function heatColorForScore(score: number, maxScore: number, fallbackLevel: number) {
  if (score <= 0 && fallbackLevel <= 0) return emptyHeatColor;
  return interpolateHeatColor(heatIntensityForScore(score, maxScore, fallbackLevel));
}

function heatIntensityForScore(score: number, maxScore: number, fallbackLevel: number) {
  const level = Math.max(0, Math.min(5, Math.round(fallbackLevel)));
  const levelAnchor = heatLevelAnchors[level] ?? heatLevelAnchors[1];
  const rawRatio = maxScore > 0 ? Math.min(1, Math.max(0.001, score / maxScore)) : 0;
  const logRatio = maxScore > 0 ? Math.log1p(Math.max(0, score)) / Math.log1p(maxScore) : levelAnchor;
  const ratio = Math.max(levelAnchor, logRatio * 0.82 + rawRatio * 0.18);
  return Math.min(1, Math.max(0.08, 0.04 + ratio * 0.96));
}

function interpolateHeatColor(value: number) {
  const bounded = Math.min(1, Math.max(0, value));
  let left = heatStops[0];
  let right = heatStops[heatStops.length - 1];
  for (let index = 1; index < heatStops.length; index += 1) {
    if (bounded <= heatStops[index].stop) {
      right = heatStops[index];
      left = heatStops[index - 1];
      break;
    }
  }
  const span = Math.max(0.001, right.stop - left.stop);
  const local = (bounded - left.stop) / span;
  const rgb = left.rgb.map((part, index) => Math.round(part + (right.rgb[index] - part) * local));
  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

function withAlpha(color: string, alpha: number) {
  const match = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
  if (!match) return color;
  return `rgba(${match[1]}, ${match[2]}, ${match[3]}, ${alpha})`;
}

function SearchReview({
  atlas,
  nodes,
  deltaStats,
  onSelectNode,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const displayNodes = useMemo(() => dedupeNodesForDisplay(nodes).slice(0, 150), [nodes]);
  const searchVisualRows = useMemo(() => buildSearchVisualRows(nodes), [nodes]);
  return (
    <div className="search-review">
      <DeltaStrip stats={deltaStats} compact />
      <HumanOverviewPanel nodes={nodes} deltaStats={deltaStats} />
      <section className="search-visual-summary" aria-label="搜索结果视觉摘要">
        <div className="panel-title-row">
          <h3>当前结果分布</h3>
          <span>{nodes.length.toLocaleString()} 条</span>
        </div>
        <div className="search-topic-bars">
          <MiniBarList title="高频主题" rows={searchVisualRows.topics} />
          <MiniBarList title="记忆层级" rows={searchVisualRows.tiers} />
          <MiniBarList title="近期/决策" rows={searchVisualRows.signals} />
        </div>
      </section>
      <div className="writeback-banner">
        <strong>写回策略</strong>
        <span>前端以后可以提交修改建议，但只能进入变更提案；受控写入层重新计算冲突、生成版本历史并支持回滚。</span>
      </div>
      {displayNodes.map(({ node, duplicateCount }) => {
        const preview = buildSearchResultPreview(node, duplicateCount);
        return (
          <button key={node.id} onClick={() => onSelectNode(node)} type="button">
            <strong>{preview.title}</strong>
            <span>{preview.summary}</span>
            <small>{preview.meta}</small>
          </button>
        );
      })}
    </div>
  );
}

function MiniBarList({ title, rows }: { title: string; rows: Array<{ label: string; count: number }> }) {
  const max = Math.max(1, ...rows.map((row) => row.count));
  return (
    <div className="mini-bar-list">
      <strong>{title}</strong>
      {rows.length ? (
        rows.map((row) => (
          <div className="mini-bar-row" key={`${title}-${row.label}`}>
            <span>{row.label}</span>
            <i style={{ "--bar-width": `${Math.max(4, Math.round((row.count / max) * 100))}%` } as CSSProperties} aria-hidden="true" />
            <b>{row.count.toLocaleString()}</b>
          </div>
        ))
      ) : (
        <p>暂无</p>
      )}
    </div>
  );
}

function SummaryIterationView({
  atlas,
  nodes,
  deltaStats,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
}) {
  const recommendations = atlas.agent_recommendations;
  const updatedAt = formatUpdatedAt(recommendations?.generated_at || atlas.overview.generated_at);
  const highlights = useMemo(() => buildIterationHighlights(nodes, deltaStats), [nodes, deltaStats]);
  return (
    <div className="summary-iteration-view visual-workspace">
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">总结与迭代</p>
          <h2>把当前记忆切片转成可更新的 Personalization、Agents.md 和 Memory 建议</h2>
        </div>
        <span>更新时间：{updatedAt}</span>
      </div>
      <DeltaStrip stats={deltaStats} compact />
      <div className="summary-signal-grid" aria-label="总结与迭代关键结论">
        {highlights.map((item) => (
          <SummarySignalCard key={item.label} label={item.label} value={item.value} note={item.note} />
        ))}
      </div>
      <HumanOverviewPanel nodes={nodes} deltaStats={deltaStats} />
      <section className="iteration-panels" aria-label="给 ChatGPT 和 Codex 使用的更新建议">
        <AgentRecommendationsPanel atlas={atlas} />
        <ConfigMemoryPanel atlas={atlas} updatedAt={updatedAt} />
      </section>
    </div>
  );
}

function SummarySignalCard({ label, value, note }: { label: string; value: string | number; note: string }) {
  return (
    <article className="summary-signal-card">
      <span>{label}</span>
      <strong>{typeof value === "number" ? value.toLocaleString() : value}</strong>
      <p>{note}</p>
    </article>
  );
}

function AgentRecommendationsPanel({ atlas }: { atlas: MemoryAtlas }) {
  const recommendations = atlas.agent_recommendations;
  if (!recommendations) {
    return null;
  }
  return (
    <section className="agent-recommendations" aria-label="建议写入 ChatGPT 与 Codex 的内容">
      <div className="panel-title-row">
        <h3>Personalization / Agents.md 建议</h3>
        <span>{formatUpdatedAt(recommendations.generated_at)}</span>
      </div>
      <div className="recommendation-columns">
        <RecommendationBucket title="Memory / Personalization" section={recommendations.memory} />
        <RecommendationBucket title="Agents.md / 执行规则" section={recommendations.meta_data} />
      </div>
    </section>
  );
}

function ConfigMemoryPanel({ atlas, updatedAt }: { atlas: MemoryAtlas; updatedAt: string }) {
  const recommendations = atlas.agent_recommendations;
  const memoryCurrent = recommendations?.memory.current ?? [];
  const metaCurrent = recommendations?.meta_data.current ?? [];
  const configItems = [
    {
      title: "config.toml",
      statement: "保留中文优先、真实验证、低上下文成本、每轮输出进度/风险/下一步；写库必须走提案与版本回滚。",
      count: metaCurrent.length,
    },
    {
      title: "Memory",
      statement: "优先装载核心画像、长期偏好、项目历史、决策日志和回答规则；短期信息保留但低权重召回。",
      count: memoryCurrent.length,
    },
    {
      title: "新增/删除/修改",
      statement: `新增 ${recommendations?.memory.added.length ?? 0} / 修改 ${recommendations?.memory.modified.length ?? 0} / 降权 ${recommendations?.memory.deleted.length ?? 0}；Meta 同步显示在上方。`,
      count: (recommendations?.memory.added.length ?? 0) + (recommendations?.memory.modified.length ?? 0) + (recommendations?.memory.deleted.length ?? 0),
    },
  ];
  return (
    <section className="config-memory-panel" aria-label="config.toml 和 Memory 建议">
      <div className="panel-title-row">
        <h3>config.toml / Memory</h3>
        <span>更新时间：{updatedAt}</span>
      </div>
      <div className="config-memory-grid">
        {configItems.map((item) => (
          <article key={item.title}>
            <strong>{item.title}</strong>
            <p>{item.statement}</p>
            <small>{item.count.toLocaleString()} 条相关建议</small>
          </article>
        ))}
      </div>
    </section>
  );
}

function RecommendationBucket({
  title,
  section,
}: {
  title: string;
  section: NonNullable<MemoryAtlas["agent_recommendations"]>["memory"];
}) {
  return (
    <article className="recommendation-bucket">
      <strong>{title}</strong>
      <RecommendationList label="新增" items={section.added} />
      <RecommendationList label="修改" items={section.modified.map((item) => item.after)} />
      <RecommendationList label="降权/不再默认使用" items={section.deleted} />
      <RecommendationList label="当前有效" items={section.current} limit={6} />
    </article>
  );
}

function RecommendationList({
  label,
  items,
  limit = 4,
}: {
  label: string;
  items: Array<{ id: string; title: string; statement: string; evidence_count?: number; reason?: string }>;
  limit?: number;
}) {
  const displayItems = useMemo(() => dedupeRecommendationItems(items).slice(0, limit), [items, limit]);
  return (
    <div className="recommendation-list">
      <span>{label}</span>
      {displayItems.length ? (
        <ul>
          {displayItems.map(({ item, duplicateCount }) => (
            <li key={`${label}-${item.id}`}>
              <b>{humanizeRecommendationTitle(item.title)}</b>
              <small>{humanizeStatement(item.statement)}</small>
              <em>{recommendationMeta(item, duplicateCount)}</em>
            </li>
          ))}
        </ul>
      ) : (
        <p>暂无</p>
      )}
    </div>
  );
}

function NodeInspector({ atlas, node, edgeCount }: { atlas: MemoryAtlas; node: AtlasNode | null; edgeCount: number }) {
  const memoryNodes = useMemo(() => getMemoryNodes(atlas), [atlas]);
  const overviewNodes = memoryNodes.length ? memoryNodes : atlas.nodes;
  if (!node) {
    return (
      <aside className="inspector">
        <h2>选择一个节点</h2>
        <p>点击星体、关系图、时间轴事件或搜索结果查看记忆详情。</p>
        <HumanOverviewPanel nodes={overviewNodes} deltaStats={buildDeltaStats(atlas, memoryNodes)} compact />
      </aside>
    );
  }
  const humanNode = buildHumanNodeSummary(node, edgeCount);
  return (
    <aside className="inspector">
      <HumanOverviewPanel nodes={overviewNodes} deltaStats={buildDeltaStats(atlas, memoryNodes)} compact />
      <p className="eyebrow">{humanNode.scope}</p>
      <h2>{humanNode.title}</h2>
      <p className="human-node-subtitle">{humanNode.subtitle}</p>
      <section className="human-node-card">
        <div className="human-node-section">
          <strong>这条记忆说明了什么</strong>
          <ul>
            {humanNode.meaning.map((item, index) => (
              <li key={`meaning-${index}-${item}`}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="human-node-section">
          <strong>为什么重要</strong>
          <p>{humanNode.impact}</p>
        </div>
        <div className="human-node-section">
          <strong>未来应该怎么用</strong>
          <ul>
            {humanNode.futureUse.map((item, index) => (
              <li key={`future-${index}-${item}`}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="human-node-section">
          <strong>相关主题</strong>
          <div className="human-node-topics">
            {humanNode.topics.map((topic, index) => (
              <span key={`topic-${index}-${topic}`}>{topic}</span>
            ))}
          </div>
        </div>
      </section>
      <dl className="human-node-status">
        {humanNode.statusRows.map((row, index) => (
          <div key={`status-${index}-${row.label}`}><dt>{row.label}</dt><dd>{row.value}</dd></div>
        ))}
      </dl>
      <details className="agent-structured-fields">
        <summary>Agent 结构化字段 / 原始摘要</summary>
        <div className="agent-field-grid">
          <section>
            <strong>Memory（给 ChatGPT / Codex Personalization）</strong>
            <p>{humanNode.agentMemory}</p>
          </section>
          <section>
            <strong>Meta Data（给 ChatGPT / Codex Agents.md）</strong>
            <p>{humanNode.agentMeta}</p>
          </section>
        </div>
        {node.statement ? (
          <div className="raw-summary-inline">
            <strong>低敏数据库摘要</strong>
            <p>{node.statement}</p>
          </div>
        ) : null}
        <dl>
          <div><dt>类型</dt><dd>{translateKind(node.kind)}</dd></div>
          <div><dt>连接数</dt><dd>{edgeCount.toLocaleString()}</dd></div>
          <div><dt>日期</dt><dd>{node.date || "未知"}</dd></div>
          <div><dt>分类</dt><dd>{node.category || "未知"}</dd></div>
          <div><dt>重要性</dt><dd>{node.importance || "未知"}</dd></div>
          <div><dt>有效期</dt><dd>{node.validity || "未知"}</dd></div>
          <div><dt>置信度</dt><dd>{node.confidence || "未知"}</dd></div>
          <div><dt>ROI</dt><dd>{formatScore(node.metrics?.roi?.leverage_score)}</dd></div>
        </dl>
      </details>
      <WritebackProposalPanel atlas={atlas} node={node} />
    </aside>
  );
}

function ContributionPeriodInspector({
  detail,
  onSelectNode,
}: {
  detail: ContributionPeriodDetail;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const bucket = detail.bucket;
  const relatedNodes = detail.relatedNodes.slice(0, 18);
  const periodLabel = scaleLabel(detail.scale);
  return (
    <aside className="inspector contribution-period-inspector">
      <p className="eyebrow">时间段详情 · {periodLabel}</p>
      <h2>{bucket.label}</h2>
      <p>
        这个对象来自贡献网格，重点是看某个时间单位里的交互强度、记忆增量、决策密度和环比变化。
      </p>
      <section className="human-node-card">
        <div className="human-node-section">
          <strong>这段时间说明了什么</strong>
          <ul>
            <li>{periodMeaningLine(bucket, detail.scale)}</li>
            <li>当前筛选命中 {bucket.filteredMemoryCount.toLocaleString()} 条记忆，其中决策 {bucket.filteredDecisionCount.toLocaleString()} 条，核心画像 {bucket.filteredCoreCount.toLocaleString()} 条。</li>
            <li>全局交互包含 {bucket.conversationCount.toLocaleString()} 个对话、{bucket.messageCount.toLocaleString()} 条消息。</li>
          </ul>
        </div>
        <div className="human-node-section">
          <strong>为什么重要</strong>
          <p>{periodImpactLine(bucket, detail.relatedNodes.length)}</p>
        </div>
        <div className="human-node-section">
          <strong>建议怎么用</strong>
          <ul>
            <li>把这个时间段和相邻周期对比，判断是一次性高峰、持续投入，还是记忆整理遗漏。</li>
            <li>优先点开下方相关记忆，查看具体话题、决策和需要继续做的事情。</li>
          </ul>
        </div>
      </section>
      <dl className="human-node-status">
        <div><dt>活动得分</dt><dd>{bucket.activityScore.toLocaleString()}</dd></div>
        <div><dt>环比变化</dt><dd>{formatSigned(bucket.delta ?? 0)} / {bucket.previousLabel ?? "上一周期"}</dd></div>
        <div><dt>全局消息</dt><dd>{bucket.messageCount.toLocaleString()}</dd></div>
        <div><dt>工具调用</dt><dd>{(bucket.toolCallCount ?? 0).toLocaleString()}</dd></div>
        <div><dt>筛选记忆</dt><dd>{bucket.filteredMemoryCount.toLocaleString()}</dd></div>
        <div><dt>核心画像</dt><dd>{bucket.filteredCoreCount.toLocaleString()}</dd></div>
        <div><dt>决策</dt><dd>{bucket.filteredDecisionCount.toLocaleString()}</dd></div>
        <div><dt>错误/中断</dt><dd>{(bucket.errorEventCount ?? 0).toLocaleString()} / {(bucket.abortCount ?? 0).toLocaleString()}</dd></div>
      </dl>
      <section className="period-related-list" aria-label="这个时间段对应的记忆">
        <div className="panel-title-row">
          <h3>对应记忆</h3>
          <span>{detail.relatedNodes.length.toLocaleString()} 条</span>
        </div>
        {relatedNodes.length ? (
          relatedNodes.map((node) => (
            <button key={node.id} onClick={() => onSelectNode(node)} type="button">
              <strong>{humanNodeTitle(node)}</strong>
              <span>{humanizeStatement(node.statement) || node.label}</span>
              <small>{normalizeMemoryTier(node.memory_tier)} / {humanCategoryLabel(node.category)} / {node.date || "未知日期"}</small>
            </button>
          ))
        ) : (
          <p>当前筛选下没有具体记忆节点；这个格子主要来自全局交互统计。切换筛选条件或年份后可继续查看。</p>
        )}
      </section>
    </aside>
  );
}

function WritebackProposalPanel({ atlas, node }: { atlas: MemoryAtlas; node: AtlasNode }) {
  const [action, setAction] = useState<WritebackAction>("update_statement");
  const [draftText, setDraftText] = useState(node.statement ?? node.label);
  const [reason, setReason] = useState("");
  const [proposals, setProposals] = useState<WritebackProposal[]>(() => loadWritebackProposals());

  const policy = atlas.source_contract.writeback_policy;
  const editable = policy.frontend_can_request_writeback && policy.writeback_must_use_proposals && !policy.direct_frontend_mutation_of_active_memory;
  const nodeProposals = useMemo(
    () => proposals.filter((proposal) => proposal.target_ref.node_id === node.id),
    [node.id, proposals],
  );
  const latest = nodeProposals[nodeProposals.length - 1] ?? null;
  const previous = nodeProposals[nodeProposals.length - 2] ?? null;
  const baseText = node.statement ?? node.label;
  const draftDiff = useMemo(() => buildProposalDiff(baseText, draftText), [baseText, draftText]);
  const versionChain = useMemo(() => [...nodeProposals].reverse().slice(0, 6), [nodeProposals]);

  useEffect(() => {
    setDraftText(node.statement ?? node.label);
    setReason("");
    setAction("update_statement");
  }, [node.id, node.label, node.statement]);

  function persist(next: WritebackProposal[]) {
    setProposals(next);
    saveWritebackProposals(next);
  }

  function saveProposal() {
    const text = draftText.trim();
    if (!editable || !text) return;
    const now = new Date().toISOString();
    const proposal: WritebackProposal = {
      schema_version: policy.proposal_schema_version || "memory_change_proposal.v1",
      proposal_id: `atlas_${compactTimestamp(now)}_${stableHash(`${node.id}:${text}:${nodeProposals.length + 1}`)}`,
      created_at: now,
      status: "draft_pending_agent_apply",
      target_ref: {
        node_id: node.id,
        memory_id: node.memory_id ?? node.id,
        label: node.label,
        source_file: node.source_label ?? node.data_source ?? "visual_snapshot",
        base_date: node.date ?? "",
      },
      action,
      payload: {
        proposed_text: text,
        reason: reason.trim(),
        current_tier: normalizeMemoryTier(node.memory_tier),
        current_category: node.category ?? "",
      },
      diff: buildProposalDiff(baseText, text),
      version: {
        revision: (latest?.version.revision ?? 0) + 1,
        parent_proposal_id: latest?.proposal_id ?? null,
        rollback_unit: policy.rollback_unit || "per_memory_version",
        supersedes_proposal_id: null,
      },
      review: buildProposalReview(action, node, reason.trim()),
      safety: {
        direct_frontend_mutation_of_active_memory: false,
        requires_conflict_check: true,
        requires_agent_or_human_apply: true,
        forbidden_payload: policy.frontend_payload_contract?.forbidden_payload ?? [
          "plaintext secrets",
          "raw conversation text",
          "record hashes",
          "local absolute paths",
        ],
      },
    };
    persist([...proposals, proposal]);
  }

  function createRollbackProposal() {
    if (!editable || !latest) return;
    const target = previous ?? latest;
    const now = new Date().toISOString();
    const rollbackText = target.payload.proposed_text || baseText;
    const rollbackReason = `回滚到版本 ${target.version.revision}：${target.proposal_id}`;
    const proposal: WritebackProposal = {
      schema_version: policy.proposal_schema_version || "memory_change_proposal.v1",
      proposal_id: `atlas_${compactTimestamp(now)}_${stableHash(`${node.id}:rollback:${latest.proposal_id}:${nodeProposals.length + 1}`)}`,
      created_at: now,
      status: "draft_pending_agent_apply",
      target_ref: {
        node_id: node.id,
        memory_id: node.memory_id ?? node.id,
        label: node.label,
        source_file: node.source_label ?? node.data_source ?? "visual_snapshot",
        base_date: node.date ?? "",
      },
      action: "rollback_to_version",
      payload: {
        proposed_text: rollbackText,
        reason: rollbackReason,
        current_tier: normalizeMemoryTier(node.memory_tier),
        current_category: node.category ?? "",
      },
      diff: buildProposalDiff(latest.payload.proposed_text || baseText, rollbackText),
      version: {
        revision: (latest.version.revision ?? 0) + 1,
        parent_proposal_id: latest.proposal_id,
        rollback_unit: policy.rollback_unit || "per_memory_version",
        supersedes_proposal_id: latest.proposal_id,
      },
      rollback: {
        rollback_to_proposal_id: target.proposal_id,
        rollback_to_revision: target.version.revision,
        rollback_text: rollbackText,
        rollback_reason: rollbackReason,
      },
      review: {
        human_summary: `建议把当前写回提案回滚到版本 ${target.version.revision}。`,
        agent_next_step: "重新读取当前主动记忆库，核对冲突与敏感字段后，写入提案历史，并用 git commit 建立回滚点。",
        conflict_policy: "若当前库已存在更新版本，先生成冲突报告，不可直接覆盖。",
        apply_status: "proposal_only_pending_agent_apply",
      },
      safety: {
        direct_frontend_mutation_of_active_memory: false,
        requires_conflict_check: true,
        requires_agent_or_human_apply: true,
        forbidden_payload: policy.frontend_payload_contract?.forbidden_payload ?? [
          "plaintext secrets",
          "raw conversation text",
          "record hashes",
          "local absolute paths",
        ],
      },
    };
    persist([...proposals, proposal]);
  }

  function rollbackDraft() {
    if (!previous) return;
    setAction(previous.action);
    setDraftText(previous.payload.proposed_text);
    setReason(`回滚到 ${previous.proposal_id}`);
  }

  function exportLatest() {
    if (!latest) return;
    downloadJson(`${latest.proposal_id}.json`, latest);
  }

  function exportProposalHistory() {
    if (!nodeProposals.length) return;
    downloadJson(`memory_atlas_writeback_history_${node.id}.json`, {
      schema_version: "memory_atlas_writeback_history.v1",
      exported_at: new Date().toISOString(),
      target_ref: {
        node_id: node.id,
        memory_id: node.memory_id ?? node.id,
        label: node.label,
      },
      proposals: nodeProposals,
    });
  }

  return (
    <section className="writeback-panel" aria-label="长期记忆写回提案">
      <div className="panel-title-row">
        <h3>写回提案</h3>
        <span>{nodeProposals.length} 版</span>
      </div>
      <p>
        前端只生成版本化提案；不直接修改主动记忆库。后续受控代理写库前必须重新读库、做冲突检查并生成可回滚历史。
      </p>
      <div className="writeback-diff-grid" aria-label="当前草稿差异">
        <div><span>长度变化</span><strong>{draftDiff.length_delta > 0 ? "+" : ""}{draftDiff.length_delta}</strong></div>
        <div><span>变更片段</span><strong>{draftDiff.changed_segments}</strong></div>
        <div><span>回滚单位</span><strong>{policy.rollback_unit || "per_memory_version"}</strong></div>
      </div>
      <label>
        动作
        <select value={action} onChange={(event) => setAction(event.target.value as WritebackAction)} disabled={!editable}>
          {(Object.keys(writebackActionLabels) as WritebackAction[]).map((key) => (
            <option key={key} value={key}>{writebackActionLabels[key]}</option>
          ))}
        </select>
      </label>
      <label>
        建议写回内容
        <textarea
          value={draftText}
          onChange={(event) => setDraftText(event.target.value)}
          disabled={!editable}
          rows={5}
        />
      </label>
      <label>
        原因 / 证据 / 回滚说明
        <textarea
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          disabled={!editable}
          rows={3}
          placeholder="说明为什么要更新、依据是什么、是否会覆盖旧结论。"
        />
      </label>
      <div className="writeback-actions">
        <button type="button" onClick={saveProposal} disabled={!editable || !draftText.trim()}>
          <Save size={15} />
          保存新版
        </button>
        <button type="button" onClick={exportLatest} disabled={!latest}>
          <Download size={15} />
          导出最新
        </button>
        <button type="button" onClick={exportProposalHistory} disabled={!nodeProposals.length}>
          <GitBranch size={15} />
          导出版本链
        </button>
        <button type="button" onClick={rollbackDraft} disabled={!previous}>
          <RotateCcw size={15} />
          载入上一版
        </button>
        <button type="button" onClick={createRollbackProposal} disabled={!latest}>
          <RotateCcw size={15} />
          生成回滚提案
        </button>
      </div>
      {versionChain.length ? (
        <div className="writeback-version-chain" aria-label="写回提案版本链">
          {versionChain.map((proposal) => (
            <button key={proposal.proposal_id} onClick={() => {
              setAction(proposal.action);
              setDraftText(proposal.payload.proposed_text);
              setReason(proposal.payload.reason);
            }} type="button">
              <strong>v{proposal.version.revision} · {writebackActionLabels[proposal.action]}</strong>
              <span>{proposal.diff?.summary ?? "旧版本无差异摘要"} · {new Date(proposal.created_at).toLocaleString("zh-CN")}</span>
              <small>{proposal.version.parent_proposal_id ? `parent ${proposal.version.parent_proposal_id}` : "root proposal"}</small>
            </button>
          ))}
        </div>
      ) : null}
      <small>
        {latest
          ? `最新版本 ${latest.version.revision} · ${new Date(latest.created_at).toLocaleString("zh-CN")} · 待受控代理应用`
          : "尚无本地提案版本"}
      </small>
    </section>
  );
}

function DeltaStrip({ stats, compact = false }: { stats: DeltaStats; compact?: boolean }) {
  return (
    <div className={compact ? "delta-strip compact" : "delta-strip"}>
      <div>
        <span>当前切片</span>
        <strong>{stats.totalFiltered.toLocaleString()}</strong>
      </div>
      <div>
        <span>近 30 天</span>
        <strong>{stats.recentCount.toLocaleString()}</strong>
      </div>
      <div>
        <span>较前 30 天</span>
        <strong className={stats.deltaCount >= 0 ? "positive" : "negative"}>{formatSigned(stats.deltaCount)}</strong>
      </div>
      <div>
        <span>新增决策/核心</span>
        <strong>{stats.recentDecisionCount}/{stats.recentCoreCount}</strong>
      </div>
      <div>
        <span>热点分类</span>
        <strong>{stats.topCategory}</strong>
      </div>
    </div>
  );
}

function HumanOverviewPanel({
  nodes,
  deltaStats,
  compact = false,
}: {
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  compact?: boolean;
}) {
  const overview = useMemo(() => buildHumanOverview(nodes, deltaStats), [nodes, deltaStats]);
  return (
    <section className={compact ? "human-overview compact" : "human-overview"} aria-label="人类可读记忆摘要">
      <div className="panel-title-row">
        <h3>目前记录了什么</h3>
        <span>{nodes.length.toLocaleString()} 条</span>
      </div>
      <div className="human-overview-grid">
        <div>
          <strong>主要话题</strong>
          <HumanPillList rows={overview.topicRows} />
        </div>
        <div>
          <strong>记忆层级</strong>
          <HumanPillList rows={overview.tierRows} />
        </div>
      </div>
      <div className="human-lists">
        <HumanBulletList title="需要做什么" items={overview.actionItems} />
        <HumanBulletList title="记得做什么" items={overview.rememberItems} />
        <HumanBulletList title="机会/增长方向" items={overview.opportunityItems} />
        <HumanBulletList title="需要留意" items={overview.riskItems} />
      </div>
    </section>
  );
}

function HumanPillList({ rows }: { rows: Array<{ label: string; count: number }> }) {
  return (
    <div className="human-pill-list">
      {rows.slice(0, 5).map((row) => (
        <span key={row.label}>
          {row.label}
          <b>{row.count}</b>
        </span>
      ))}
    </div>
  );
}

function HumanBulletList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="human-bullet-list">
      <strong>{title}</strong>
      <ul>
        {items.map((item, index) => (
          <li key={`${title}-${index}-${item}`}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function GraphSvgNode({
  item,
  selected,
  onSelectNode,
}: {
  item: LayoutNode;
  selected: boolean;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const radius = selected ? item.r + 5 : item.r;
  const isParent = isGraphParentNode(item.node);
  return (
    <g
      className={`${selected ? "graph-node selected" : "graph-node"}${isParent ? " parent-node" : ""}`}
      aria-label={`${translateKind(item.node.kind)} · ${item.node.label}`}
      role="button"
      tabIndex={0}
      onClick={() => onSelectNode(item.node)}
      onKeyDown={(event) => {
        if (isActivationKey(event)) onSelectNode(item.node);
      }}
    >
      <title>{`${translateKind(item.node.kind)} · ${item.node.label}`}</title>
      <circle className="graph-node-halo" cx={item.x} cy={item.y} r={radius + (isParent ? 8 : 5)} fill={item.color} opacity={isParent ? 0.1 : 0.045} />
      <circle className="graph-node-core" cx={item.x} cy={item.y} r={radius} fill={item.color} filter="url(#softGlow)" />
    </g>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value.toLocaleString()}</strong>
    </div>
  );
}

function SelectFilter({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="select-filter">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="all">全部</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function InsightCard({ title, value, note }: { title: string; value: number; note: string }) {
  return (
    <article className="insight-card">
      <span>{title}</span>
      <strong>{value.toLocaleString()}</strong>
      <p>{note}</p>
    </article>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span>
      <i style={{ background: color }} />
      {label}
    </span>
  );
}

function GraphUsageStrip({ items }: { items: Array<{ label: string; value: string }> }) {
  return (
    <div className="graph-usage-strip" aria-label="图谱读法">
      {items.map((item) => (
        <span key={`${item.label}-${item.value}`}>
          <b>{item.label}</b>
          <em>{item.value}</em>
        </span>
      ))}
    </div>
  );
}

interface LayoutNode {
  node: AtlasNode;
  x: number;
  y: number;
  r: number;
  color: string;
  label: string;
  degree: number;
}

interface LayoutEdge {
  id: string;
  source: LayoutNode;
  target: LayoutNode;
  weight: number;
  color: string;
}

interface LayoutGroup {
  id: string;
  label: string;
  x: number;
  y: number;
  r: number;
  color: string;
}

function buildFilteredSlice(atlas: MemoryAtlas, filteredMemoryNodes: AtlasNode[], filters: AtlasFilters): FilteredAtlasSlice {
  const visibleGraph = visibleGraphFor(atlas, filteredMemoryNodes);
  const visibleNodeIds = new Set(visibleGraph.nodes.map((node) => node.id));
  const memoryIds = new Set(filteredMemoryNodes.map((node) => node.memory_id).filter(Boolean));
  const timeline = atlas.timeline.filter((event) => visibleNodeIds.has(event.node_id) || memoryIds.has(event.memory_id));
  return {
    memoryNodes: filteredMemoryNodes,
    graphNodes: visibleGraph.nodes,
    graphEdges: visibleGraph.edges,
    timeline,
    visibleNodeIds,
    deltaStats: buildDeltaStats(atlas, filteredMemoryNodes),
    filterActive:
      filters.query !== "" || filters.source !== "all" || filters.tier !== "all" || filters.category !== "all" || filters.theme !== "all",
  };
}

function selectionStillVisible(node: AtlasNode, slice: FilteredAtlasSlice): boolean {
  if (!slice.visibleNodeIds.has(node.id)) return false;
  if (!slice.filterActive) return true;
  if (node.kind === "memory") {
    return slice.memoryNodes.some((memoryNode) => memoryNode.id === node.id);
  }
  return true;
}

function buildSourceOptions(atlas: MemoryAtlas, memoryNodes: AtlasNode[]): SourceOption[] {
  if (atlas.data_sources?.length) {
    return atlas.data_sources
      .filter((source) => ["all", "memory_atlas", "codex"].includes(source.id))
      .map((source) => ({
        id: source.id,
        label: sourceDisplayLabel(source.id, source.label),
        description: source.description,
        node_count: source.node_count,
      }));
  }
  const counts = memoryNodes.reduce<Record<string, number>>((acc, node) => {
    const id = node.data_source ?? "memory_atlas";
    acc[id] = (acc[id] ?? 0) + 1;
    return acc;
  }, {});
  return [
    { id: "all", label: "总数据源", description: "所有数据来源放在一起", node_count: memoryNodes.length },
    ...Object.entries(counts)
      .filter(([id]) => ["memory_atlas", "codex"].includes(id))
      .map(([id, count]) => ({
        id,
        label: sourceDisplayLabel(id, id),
        description: "自动识别的数据源",
        node_count: count,
      })),
  ];
}

function sourceDisplayLabel(sourceId: string, fallback: string): string {
  if (sourceId === "all") return "总数据源";
  if (sourceId === "memory_atlas") return "ChatGPT";
  if (sourceId === "codex") return "Codex";
  return fallback;
}

function sourceMatchesNode(node: AtlasNode, sourceId: string): boolean {
  return sourceId === "all" || (node.data_source ?? "memory_atlas") === sourceId;
}

function buildSourceScopedAtlas(atlas: MemoryAtlas, sourceMemoryNodes: AtlasNode[], sourceId: string): MemoryAtlas {
  if (sourceId === "all") return atlas;
  const graph = visibleGraphFor(atlas, sourceMemoryNodes);
  const visibleNodeIds = new Set(graph.nodes.map((node) => node.id));
  const memoryIds = new Set(sourceMemoryNodes.map((node) => node.memory_id).filter(Boolean));
  const timeline = atlas.timeline.filter((event) => visibleNodeIds.has(event.node_id) || memoryIds.has(event.memory_id));
  const sourceSummary = atlas.data_sources?.find((source) => source.id === sourceId);
  const contribution = buildSourceScopedContribution(atlas, sourceMemoryNodes, sourceId);
  return {
    ...atlas,
    overview: {
      ...atlas.overview,
      active_memory_count: sourceMemoryNodes.length,
      memory_node_count: sourceMemoryNodes.length,
      node_count: graph.nodes.length,
      edge_count: graph.edges.length,
      conversation_count: sourceSummary?.activity_count ?? contribution.daily.length,
    },
    nodes: graph.nodes,
    edges: graph.edges,
    timeline,
    contribution,
    metrics: buildSourceScopedMetrics(sourceMemoryNodes),
    agent_recommendations: sourceId === "codex" ? atlas.agent_recommendations : undefined,
  };
}

function buildSourceScopedContribution(atlas: MemoryAtlas, sourceMemoryNodes: AtlasNode[], sourceId: string): MemoryAtlas["contribution"] {
  const nodeDaily = aggregateFilteredNodes(sourceMemoryNodes, "day");
  const dailyByDate = new Map<string, ActivityBucket>();

  if (sourceId === "codex") {
    for (const row of atlas.contribution.daily) {
      if ((row.codex_session_count ?? 0) <= 0 && (row.tool_call_count ?? 0) <= 0) continue;
      dailyByDate.set(row.date, normalizeActivityBucket(row));
    }
  }

  for (const [dateKey, nodeBucket] of nodeDaily) {
    const target = dailyByDate.get(dateKey) ?? blankBucket(dateKey);
    target.memory_count = nodeBucket.memory_count;
    target.decision_count = nodeBucket.decision_count;
    target.core_memory_count = nodeBucket.core_memory_count;
    target.mid_long_memory_count = nodeBucket.mid_long_memory_count;
    target.short_memory_count = nodeBucket.short_memory_count;
    target.activity_score = Math.max(target.activity_score, nodeBucket.activity_score);
    target.activity_level = levelFromScore(target.activity_score);
    dailyByDate.set(dateKey, target);
  }

  const daily = Array.from(dailyByDate.values()).sort((a, b) => a.date.localeCompare(b.date));
  const maxActivity = Math.max(0, ...daily.map((row) => row.activity_score));
  return {
    ...atlas.contribution,
    range_start: daily[0]?.date ?? "",
    range_end: daily[daily.length - 1]?.date ?? "",
    max_activity_score: maxActivity,
    quantiles: {},
    daily,
    weekly: aggregateActivityBuckets(daily, "week"),
    monthly: aggregateActivityBuckets(daily, "month"),
    yearly: aggregateActivityBuckets(daily, "year"),
  };
}

function normalizeActivityBucket(row: ActivityBucket): ActivityBucket {
  return {
    ...blankBucket(row.date),
    ...row,
    tool_call_count: row.tool_call_count ?? 0,
    error_event_count: row.error_event_count ?? 0,
    abort_count: row.abort_count ?? 0,
    codex_session_count: row.codex_session_count ?? 0,
  };
}

function aggregateActivityBuckets(rows: ActivityBucket[], period: "week" | "month" | "year"): ActivityBucket[] {
  const buckets = new Map<string, ActivityBucket>();
  for (const row of rows) {
    const periodKey = activityPeriodKey(row.date, period);
    if (!periodKey) continue;
    const target = buckets.get(periodKey) ?? blankBucket(periodKey);
    for (const key of activityBucketNumericKeys) {
      target[key] = (target[key] ?? 0) + (row[key] ?? 0);
    }
    target.activity_level = levelFromScore(target.activity_score);
    buckets.set(periodKey, target);
  }
  return Array.from(buckets.values()).sort((a, b) => a.date.localeCompare(b.date));
}

function activityPeriodKey(dateKey: string, period: "week" | "month" | "year"): string {
  const day = parseDay(dateKey);
  if (!day) return "";
  if (period === "month") return `${day.getUTCFullYear()}-${String(day.getUTCMonth() + 1).padStart(2, "0")}`;
  if (period === "year") return String(day.getUTCFullYear());
  const startWeekday = mondayWeekdayIndex(new Date(Date.UTC(day.getUTCFullYear(), 0, 1)));
  return calendarWeekKey(day.getUTCFullYear(), Math.floor((dayOfYearIndex(day) + startWeekday) / 7));
}

const activityBucketNumericKeys = [
  "conversation_count",
  "message_count",
  "user_message_count",
  "assistant_message_count",
  "memory_count",
  "candidate_count",
  "decision_count",
  "core_memory_count",
  "mid_long_memory_count",
  "short_memory_count",
  "tool_call_count",
  "error_event_count",
  "abort_count",
  "codex_session_count",
  "activity_score",
] as const;

function buildSourceScopedMetrics(nodes: AtlasNode[]): AtlasMetric[] {
  return [
    { kind: "tier", values: filteredMetricValues(nodes, "memory_tier") },
    { kind: "category", values: filteredMetricValues(nodes, "category") },
  ];
}

function buildDeltaStats(atlas: MemoryAtlas, nodes: AtlasNode[]): DeltaStats {
  const latest = parseDay(atlas.contribution.range_end) ?? maxNodeDate(nodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  const previousStart = addDays(latest, -59);
  const previousEnd = addDays(latest, -30);
  const recentNodes = nodes.filter((node) => isNodeBetween(node, recentStart, latest));
  const previousNodes = nodes.filter((node) => isNodeBetween(node, previousStart, previousEnd));
  const categoryCounts = filteredMetricValues(nodes, "category");
  const topCategory = topEntry(categoryCounts)?.[0] ?? "暂无";
  const deltaCount = recentNodes.length - previousNodes.length;
  return {
    totalFiltered: nodes.length,
    totalMemory: atlas.overview.active_memory_count,
    recentCount: recentNodes.length,
    previousCount: previousNodes.length,
    deltaCount,
    deltaRate: previousNodes.length ? deltaCount / previousNodes.length : null,
    recentDecisionCount: recentNodes.filter((node) => node.category === "decision").length,
    recentCoreCount: recentNodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length,
    topCategory,
    latestDate: toDayKey(latest),
  };
}

function buildHumanOverview(nodes: AtlasNode[], deltaStats: DeltaStats): HumanOverview {
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const topicRows = topRows(countBy(memoryNodes, (node) => humanThemeLabel(node)), 6);
  const tierRows = topRows(countBy(memoryNodes, (node) => normalizeMemoryTier(node.memory_tier)), 4);
  const categoryRows = topRows(countBy(memoryNodes, (node) => humanCategoryLabel(node.category)), 6);
  const topTopic = topicRows[0]?.label ?? "当前筛选主题";
  const highLeverage = [...memoryNodes]
    .sort((a, b) => (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0))
    .slice(0, 4);
  const staleShortCount = memoryNodes.filter(
    (node) => normalizeMemoryTier(node.memory_tier) === "临时" || node.metrics?.roi?.staleness_status === "stale_short_term",
  ).length;
  const coreCount = memoryNodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length;
  const decisionCount = memoryNodes.filter((node) => node.category === "decision").length;
  const securityCount = memoryNodes.filter((node) => node.category === "security_boundary").length;

  const rememberItems = highLeverage.length
    ? dedupeDisplayItems(highLeverage.map((node) => `${humanNodeDisplayTitle(node)}：${recommendedActionForNode(node)}`), 4)
    : ["暂无高杠杆记忆；先选择主题或层级后查看更具体的事项。"];

  return {
    topicRows,
    tierRows,
    categoryRows,
    actionItems: [
      `优先复核「${topTopic}」：这是当前记忆密度最高的主题，适合先转成下一步任务清单。`,
      `把 ${coreCount.toLocaleString()} 条核心画像沉淀成可复制的 personalization / agent 启动上下文。`,
      staleShortCount
        ? `清理但不删除 ${staleShortCount.toLocaleString()} 条临时信息：压缩成低权重背景，避免干扰长期判断。`
        : "当前短期噪音较低，下一步可以集中补齐项目索引和决策日志。",
    ],
    rememberItems,
    opportunityItems: buildOpportunityItems(topicRows, categoryRows, deltaStats),
    riskItems: [
      securityCount
        ? `${securityCount.toLocaleString()} 条安全边界需要持续遵守；涉及交易、secret、外部部署时不能跳过确认。`
        : "当前筛选没有明显安全边界，但外部写入和账户操作仍需人工确认。",
      decisionCount
        ? `${decisionCount.toLocaleString()} 条决策应进入后续默认上下文，避免重复讨论。`
        : "当前筛选决策较少，后续应把重要选择明确写入决策日志。",
      `近 30 天较前 30 天 ${formatSigned(deltaStats.deltaCount)} 条，增量变化需要和实际任务成果一起复盘。`,
    ],
  };
}

function buildOpportunityItems(
  topicRows: Array<{ label: string; count: number }>,
  categoryRows: Array<{ label: string; count: number }>,
  deltaStats: DeltaStats,
): string[] {
  const items: string[] = [];
  const topicText = topicRows.map((row) => row.label).join(" / ");
  if (topicText.includes("记忆") || topicText.includes("RAG")) {
    items.push("把长期记忆库包装成所有 agent 的 RAG / personalization 入口，减少重复解释和上下文损耗。");
  }
  if (topicText.includes("Codex") || topicText.includes("agent") || topicText.includes("workflow")) {
    items.push("把高频 Codex 工作流产品化成可复用 Skill、Task Pack、验收脚本，提升每次开发 ROI。");
  }
  if (topicText.includes("金融") || topicText.includes("交易") || topicText.includes("概率")) {
    items.push("把金融、FIFA、概率决策沉淀为研究和风控仪表盘，优先服务 paper trading / 人审决策。");
  }
  if (topicText.includes("学习") || topicText.includes("Notion")) {
    items.push("把学习记录、Notion dashboard、周/月复盘打通，形成能力成长的可观察闭环。");
  }
  if (topicText.includes("工业") || topicText.includes("回转窑")) {
    items.push("工业服务方向可继续沉淀为测量、诊断、动态调整方案，适合形成行业化交付资产。");
  }
  if (categoryRows.some((row) => row.label.includes("项目上下文"))) {
    items.push("项目上下文占比较高，适合做项目索引和路线图，减少切换成本。");
  }
  if (deltaStats.recentDecisionCount > 0) {
    items.push("近期已有新决策，建议把对应行动项同步进下周执行清单。");
  }
  return items.slice(0, 4).length ? items.slice(0, 4) : ["先从最高密度主题做一次人工复盘，找出可产品化、可自动化、可投资研究的方向。"];
}

function buildSemanticInsights(nodes: AtlasNode[]): {
  topics: SemanticInsight[];
  tiers: string[];
  matrixRows: string[];
  matrix: Map<string, SemanticMatrixCell>;
  wordCloud: WordCloudItem[];
} {
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const topicMap = new Map<string, SemanticInsight>();
  const wordMap = new Map<string, WordCloudItem>();
  const latest = maxNodeDate(memoryNodes) ?? new Date();
  const recentStart = addDays(latest, -29);

  for (const node of memoryNodes) {
    const topic = compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category);
    const current = topicMap.get(topic) ?? { label: topic, count: 0, roiScore: 0, recentCount: 0, nodes: [] };
    current.count += 1;
    current.roiScore += node.metrics?.roi?.leverage_score ?? 0;
    if (isNodeBetween(node, recentStart, latest)) current.recentCount += 1;
    current.nodes.push(node);
    topicMap.set(topic, current);

    for (const token of semanticTokensForNode(node)) {
      const row = wordMap.get(token) ?? {
        label: token,
        count: 0,
        score: 0,
        x: 8 + stableUnit(token, "word-x") * 78,
        y: 8 + stableUnit(token, "word-y") * 76,
        rotate: stableUnit(token, "word-rotate") > 0.82 ? -8 + stableUnit(token, "word-tilt") * 16 : 0,
        nodes: [],
      };
      row.count += 1;
      row.score += 1 + (node.metrics?.roi?.leverage_score ?? 0);
      row.nodes.push(node);
      wordMap.set(token, row);
    }
  }

  const topics = Array.from(topicMap.values())
    .map((topic) => ({
      ...topic,
      roiScore: topic.count ? topic.roiScore / topic.count : 0,
    }))
    .sort((a, b) => b.count - a.count || b.roiScore - a.roiScore || a.label.localeCompare(b.label, "zh-CN"));
  const tiers = ["核心画像", "一般", "临时"].filter((tier) => memoryNodes.some((node) => normalizeMemoryTier(node.memory_tier) === tier));
  const safeTiers = tiers.length ? tiers : ["未分层"];
  const matrixRows = topics.slice(0, 8).map((topic) => topic.label);
  const matrix = new Map<string, SemanticMatrixCell>();
  for (const row of matrixRows) {
    for (const tier of safeTiers) {
      const cellNodes = (topicMap.get(row)?.nodes ?? []).filter((node) => normalizeMemoryTier(node.memory_tier) === tier);
      matrix.set(`${row}::${tier}`, { topic: row, tier, count: cellNodes.length, nodes: cellNodes });
    }
  }
  const wordCloud = Array.from(wordMap.values())
    .sort((a, b) => b.score - a.score || b.count - a.count || a.label.localeCompare(b.label, "zh-CN"))
    .slice(0, 42);

  return { topics, tiers: safeTiers, matrixRows, matrix, wordCloud };
}

function semanticTokensForNode(node: AtlasNode): string[] {
  const themeTokens = humanThemeLabel(node)
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean);
  const categoryTokens = [humanCategoryLabel(node.category), normalizeMemoryTier(node.memory_tier)].filter(Boolean);
  const textTokens = `${node.label} ${node.statement ?? ""}`
    .match(/[A-Za-z][A-Za-z0-9+_-]{2,}|[\u4e00-\u9fff]{2,8}/g)
    ?.map((token) => token.trim())
    .filter((token) => token.length >= 2 && !semanticStopwords.has(token.toLowerCase()))
    .slice(0, 8) ?? [];
  return Array.from(new Set([...themeTokens, ...categoryTokens, ...textTokens]))
    .map((token) => truncate(token.replace(/^(核心画像|一般|临时)\s*·\s*/, ""), 16))
    .filter((token) => token && !semanticStopwords.has(token.toLowerCase()));
}

const semanticStopwords = new Set([
  "静态图谱低敏摘要",
  "层级",
  "分类",
  "重要性",
  "有效期",
  "主题",
  "unknown",
  "memory",
  "一般短期",
  "重要中长期",
]);

function selectRepresentativeNode(nodes: AtlasNode[]): AtlasNode | null {
  return [...nodes].sort((a, b) => {
    const roi = (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0);
    if (roi !== 0) return roi;
    if ((b.importance === "高") !== (a.importance === "高")) return b.importance === "高" ? -1 : 1;
    return (b.date ?? "").localeCompare(a.date ?? "");
  })[0] ?? null;
}

function semanticHeatStyle(count: number, maxCount: number): CSSProperties {
  const level = count <= 0 ? 0 : Math.max(1, Math.min(5, Math.ceil((count / Math.max(1, maxCount)) * 5)));
  const color = heatColorForScore(count, maxCount, level);
  return {
    "--semantic-bg": count ? `linear-gradient(145deg, ${withAlpha(color, 0.72)}, ${color})` : "rgba(15, 17, 22, 0.9)",
    "--semantic-border": count ? withAlpha(color, 0.72) : "rgba(244, 241, 232, 0.08)",
  } as CSSProperties;
}

function semanticColor(index: number): string {
  const palette = ["#7ee8d4", "#8fd3ff", "#48c7e8", "#f48fb1", "#c7a7ff", "#6ea8ff", "#94a3b8"];
  return palette[index % palette.length];
}

function wordCloudStyle(item: WordCloudItem, maxScore: number): CSSProperties {
  const ratio = Math.min(1, Math.max(0.12, item.score / Math.max(1, maxScore)));
  const size = 11 + Math.sqrt(ratio) * 23;
  return {
    "--word-x": `${item.x}%`,
    "--word-y": `${item.y}%`,
    "--word-rotate": `${item.rotate}deg`,
    "--word-size": `${size}px`,
    "--word-color": heatColorForScore(item.score, maxScore, Math.ceil(ratio * 5)),
  } as CSSProperties;
}

function buildHumanNodeSummary(node: AtlasNode, edgeCount: number) {
  const theme = humanThemeLabel(node);
  const categoryLabel = humanCategoryLabel(node.category);
  const tier = normalizeMemoryTier(node.memory_tier);
  const continuityMemory = isMemoryContinuityNode(node, theme);
  const title = humanNodeTitle(node, theme, continuityMemory);
  const topics = splitHumanTopics(theme);
  const memoryType = tier !== "未分层" ? `${tier} / ${categoryLabel}` : categoryLabel;
  const status = humanMemoryStatus(node);
  return {
    title,
    subtitle: buildHumanNodeSubtitle(node, theme, continuityMemory),
    scope: `人类视图 · ${tier !== "未分层" ? tier : categoryLabel}`,
    meaning: buildMeaningBullets(node, theme, continuityMemory),
    impact: buildHumanImpact(node, edgeCount, continuityMemory),
    futureUse: buildFutureUseItems(node, continuityMemory),
    topics,
    statusRows: [
      { label: "记忆类型", value: memoryType },
      { label: "适用对象", value: continuityMemory ? "ChatGPT / Codex / 任意 Agent" : humanApplicableScope(node) },
      { label: "首次记录", value: node.date || "未知" },
      { label: "当前状态", value: status },
      { label: "关联数量", value: edgeCount.toLocaleString() },
      { label: "可信度", value: node.confidence || "未知" },
    ],
    agentMemory: buildAgentMemoryLine(node, title, continuityMemory),
    agentMeta: buildAgentMetaLine(node, theme, status),
  };
}

function recommendedActionForNode(node: AtlasNode): string {
  if (node.category === "answering_rule") return "作为未来回答和验收标准，执行前先检查。";
  if (node.category === "decision") return "作为已做出的选择，后续方案默认继承并记录影响。";
  if (node.category === "project_context") return "用于恢复项目背景，继续任务前先读关联项目和下一步。";
  if (node.category === "workflow") return "沉淀成可复用流程、Skill 或自动化检查。";
  if (node.category === "security_boundary") return "作为硬边界处理，涉及外部写入、交易、secret 时先确认。";
  if (node.category === "deprecated_info") return "保留历史轨迹，但回答时标明可能过时，避免当成当前事实。";
  if (node.category === "temporary_or_sensitive") return "低权重召回，只在当前任务相关时读取，不要污染长期画像。";
  const tier = normalizeMemoryTier(node.memory_tier);
  if (tier === "核心画像") return "优先进入 personalization，影响所有 agent 的默认行为。";
  if (tier === "一般") return "保留为一般上下文，用于项目连续性和决策复盘。";
  return "作为背景资料保留，必要时再展开。";
}

function isMemoryContinuityNode(node: AtlasNode, theme: string): boolean {
  const text = `${node.label} ${node.statement ?? ""} ${theme} ${node.visual?.cluster ?? ""}`.toLowerCase();
  return (
    text.includes("memory-rag-continuity") ||
    text.includes("长期记忆") ||
    text.includes("memory atlas") ||
    text.includes("openaidatabase") ||
    text.includes("rag") ||
    text.includes("personalization") ||
    text.includes("agent continuity")
  );
}

function humanNodeTitle(node: AtlasNode, theme?: string, continuityMemory = false): string {
  const compactTheme = compactThemeLabel(theme ?? humanThemeLabel(node));
  if (continuityMemory && node.category === "answering_rule") {
    return `回答规则：${compactTheme || "长期记忆库"}先于执行`;
  }
  if (node.category === "answering_rule") return `回答规则：${compactTheme || "交付标准"}`;
  if (node.category === "decision") return `决策：${compactTheme || "重要选择"}`;
  if (node.category === "project_context") return `项目背景：${compactTheme || "上下文"}`;
  if (node.category === "workflow") return `工作流：${compactTheme || "可复用流程"}`;
  if (node.category === "preference") return `偏好：${compactTheme || "判断标准"}`;
  if (node.category === "security_boundary") return `安全边界：${compactTheme || "高风险动作"}`;
  if (node.category === "deprecated_info") return `历史信息：${compactTheme || "默认低权重"}`;
  return node.label
    .replace(/^(核心画像|一般|临时|重要中长期|一般短期)\s*·\s*/, "")
    .replace(/\s*·\s*/g, " / ")
    .slice(0, 72);
}

function buildHumanNodeSubtitle(node: AtlasNode, theme: string, continuityMemory: boolean): string {
  if (continuityMemory) {
    return "这条记忆的重点不是数据库字段，而是让未来任何 agent 先理解你的画像、偏好、项目历史、决策标准和回答规则，再开始工作。";
  }
  if (node.kind !== "memory") {
    return "这是一个导航节点，用来把相关主题、项目、决策、时间线和记忆连接起来，帮助你从全局理解历史轨迹。";
  }
  if (node.category === "answering_rule") return "这是一条会影响未来回答方式和交付验收标准的长期规则。";
  if (node.category === "decision") return "这记录了一个已做出的选择，后续规划和 agent 执行应默认继承。";
  if (node.category === "project_context") return "这保存项目背景，目的是降低换线程、换 agent 或隔一段时间后继续工作的成本。";
  if (node.category === "preference") return "这记录你的偏好、taste 或判断标准，未来 personalization 应优先使用。";
  return `这条记忆和「${theme}」有关，适合用于复盘、搜索、上下文恢复和未来 agent 个性化。`;
}

function buildMeaningBullets(node: AtlasNode, theme: string, continuityMemory: boolean): string[] {
  if (continuityMemory) {
    return [
      "你不希望 AI 只记住设置页里很短的 personalization，而是要有完整、长期、可追溯的记忆数据库。",
      "ChatGPT、Codex 和未来任意 agent 都应能读取同一套画像、偏好、历史项目、决策标准和回答规则。",
      "前端默认展示人类能理解的结论、机会、建议和待办；完整原文和高敏内容只给授权 agent 读取。",
    ];
  }
  if (node.kind !== "memory") {
    return [
      `它把「${theme}」相关的记忆集中到同一个导航对象。`,
      "点击它的价值是快速找到相关历史、项目、决策和行为模式。",
    ];
  }
  if (node.category === "decision") {
    return [
      "这里记录的是已经做出的选择，不应在未来任务中反复重新讨论。",
      "后续 agent 应把它作为默认背景，并在新证据出现时再提出修改建议。",
    ];
  }
  if (node.category === "answering_rule") {
    return [
      "这里记录的是未来回答和交付方式需要遵守的规则。",
      "它的用途是提高回答稳定性，减少你重复纠正同类问题的次数。",
    ];
  }
  if (node.category === "project_context") {
    return [
      "这里保存的是项目背景、历史进展或上下文，不是一次性的聊天片段。",
      "它能帮助新线程、新 agent 或未来的你快速恢复任务状态。",
    ];
  }
  const cleanStatement = humanizeStatement(node.statement);
  return [
    cleanStatement || `这是一条关于「${theme}」的记忆，适合用于搜索、复盘和上下文恢复。`,
    recommendedActionForNode(node),
  ];
}

function buildHumanImpact(node: AtlasNode, edgeCount: number, continuityMemory: boolean): string {
  if (continuityMemory) {
    return "它直接影响所有未来 AI 协作质量：减少重复解释、降低上下文成本、提高项目接续能力，并让 agent 更接近长期了解你的工作伙伴。";
  }
  if (node.category === "answering_rule") return "它能减少重复纠错，让不同 agent 在回答风格、验收标准和执行边界上更一致。";
  if (node.category === "decision") return "它能避免重复决策，让后续计划沿着既定方向推进，同时保留未来修正的证据入口。";
  if (node.category === "project_context") return "它能降低项目切换成本，让历史背景、当前状态和下一步行动更容易被恢复。";
  if (node.category === "preference") return "它会影响未来 personalization，让回答更贴近你的 taste、偏好、风险边界和决策方式。";
  if (node.category === "security_boundary") return "它属于硬边界信息，能防止 agent 在外部写入、隐私、交易或 secret 场景里越权。";
  const connectionText = edgeCount ? `当前有 ${edgeCount.toLocaleString()} 个关联，` : "";
  return `${connectionText}它的价值在于帮助你看清反复出现的主题、行为习惯和潜在机会，而不是只作为后台索引。`;
}

function buildFutureUseItems(node: AtlasNode, continuityMemory: boolean): string[] {
  if (continuityMemory) {
    return [
      "新 agent 启动前先读取 Memory Atlas / OpenAIDatabase，再生成适配你的 profile、preference 和项目上下文。",
      "回答时优先遵守你的长期偏好、交付标准、历史决策和安全边界。",
      "发现新偏好、新规则或新项目决策时，先生成可审查、可回滚的 memory update candidate。",
    ];
  }
  if (node.category === "security_boundary") {
    return ["涉及外部写入、交易、secret、隐私或权限时先停下来确认。", "把它作为 agent 执行前的硬性检查项。"];
  }
  if (node.category === "workflow") {
    return ["把它沉淀成可复用 skill、Task Pack 或自动化检查。", "未来相似任务先套用这套流程，再根据新证据调整。"];
  }
  if (node.category === "deprecated_info") {
    return ["保留历史轨迹，但回答时明确它可能过时。", "如果新资料冲突，应以更新证据为准并生成修改提案。"];
  }
  return [recommendedActionForNode(node), "如果这条记忆影响未来回答，建议在下方写回提案里补充更清晰的人类结论。"];
}

function humanNodeDisplayTitle(node: AtlasNode): string {
  const theme = humanThemeLabel(node);
  return humanNodeTitle(node, theme, isMemoryContinuityNode(node, theme));
}

function buildSearchResultPreview(node: AtlasNode, duplicateCount: number): { title: string; summary: string; meta: string } {
  const theme = humanThemeLabel(node);
  const continuityMemory = isMemoryContinuityNode(node, theme);
  const title = humanNodeTitle(node, theme, continuityMemory);
  const summary = humanizeStatement(node.statement) || buildHumanNodeSubtitle(node, theme, continuityMemory);
  const meta = [
    normalizeMemoryTier(node.memory_tier),
    humanCategoryLabel(node.category),
    node.date || "未知日期",
    duplicateCount > 1 ? `已合并 ${duplicateCount.toLocaleString()} 条同类记录` : "",
  ].filter(Boolean).join(" / ");
  return { title, summary, meta };
}

function dedupeNodesForDisplay(nodes: AtlasNode[]): Array<{ node: AtlasNode; duplicateCount: number }> {
  const rows = new Map<string, { node: AtlasNode; duplicateCount: number }>();
  for (const node of nodes) {
    const title = humanNodeDisplayTitle(node);
    const theme = humanThemeLabel(node);
    const summary = humanizeStatement(node.statement);
    const keySource = node.category === "answering_rule"
      ? `${node.kind}|${node.category}|${normalizeMemoryTier(node.memory_tier)}|${theme}`
      : `${node.kind}|${node.category}|${title}|${summary || node.label}`;
    const key = normalizeDisplayKey(keySource);
    const current = rows.get(key);
    if (current) {
      current.duplicateCount += 1;
    } else {
      rows.set(key, { node, duplicateCount: 1 });
    }
  }
  return [...rows.values()];
}

function dedupeRecommendationItems(
  items: Array<{ id: string; title: string; statement: string; evidence_count?: number; reason?: string }>,
): Array<{ item: { id: string; title: string; statement: string; evidence_count?: number; reason?: string }; duplicateCount: number }> {
  const rows = new Map<string, { item: { id: string; title: string; statement: string; evidence_count?: number; reason?: string }; duplicateCount: number }>();
  for (const item of items) {
    const key = normalizeDisplayKey(`${humanizeRecommendationTitle(item.title)}|${humanizeStatement(item.statement)}`);
    const current = rows.get(key);
    if (current) {
      current.duplicateCount += 1;
      current.item.evidence_count = Math.max(current.item.evidence_count ?? 0, item.evidence_count ?? 0);
    } else {
      rows.set(key, { item, duplicateCount: 1 });
    }
  }
  return [...rows.values()];
}

function dedupeDisplayItems(items: string[], limit: number): string[] {
  const rows = new Map<string, { text: string; count: number }>();
  for (const item of items) {
    const key = normalizeDisplayKey(item);
    const current = rows.get(key);
    if (current) {
      current.count += 1;
    } else {
      rows.set(key, { text: item, count: 1 });
    }
  }
  return [...rows.values()].slice(0, limit).map((row) => (
    row.count > 1 ? `${row.text}（另有 ${row.count - 1} 条同类记录）` : row.text
  ));
}

function humanizeRecommendationTitle(value: string): string {
  return truncate(value
    .replace(/^(Memory|Meta Data)\s*·\s*/i, "")
    .replace(/answering_rule/g, "回答规则")
    .replace(/project_context/g, "项目上下文")
    .replace(/security_boundary/g, "安全边界")
    .replace(/temporary_or_sensitive/g, "短期/敏感背景")
    .replace(/\s*·\s*/g, " / "), 72);
}

function recommendationMeta(
  item: { evidence_count?: number },
  duplicateCount: number,
): string {
  const parts = [`证据 ${item.evidence_count ?? 0}`];
  if (duplicateCount > 1) parts.push(`合并 ${duplicateCount.toLocaleString()} 条同类`);
  return parts.join(" / ");
}

function splitHumanTopics(theme: string): string[] {
  return theme
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 8);
}

function humanMemoryStatus(node: AtlasNode): string {
  if (node.category === "deprecated_info") return "保留历史，默认不作为当前事实";
  if (node.validity === "临时") return "临时有效";
  if (node.validity === "项目结束前") return "项目期内有效";
  return "有效";
}

function humanApplicableScope(node: AtlasNode): string {
  if (node.category === "answering_rule") return "所有未来回答";
  if (node.category === "preference") return "Personalization / Profile";
  if (node.category === "project_context") return "相关项目和接续任务";
  if (node.category === "workflow") return "Codex / Agent 工作流";
  if (node.category === "security_boundary") return "所有高风险动作";
  return "搜索 / 复盘 / 相关 Agent";
}

function buildAgentMemoryLine(node: AtlasNode, title: string, continuityMemory: boolean): string {
  const prefix = continuityMemory ? "核心 personalization" : humanCategoryLabel(node.category);
  return `${prefix}：${title}。未来 agent 应把这条记忆用于画像、偏好、历史上下文或回答规则恢复；新增/修改/删除需走下方写回提案。`;
}

function buildAgentMetaLine(node: AtlasNode, theme: string, status: string): string {
  return [
    `层级=${normalizeMemoryTier(node.memory_tier)}`,
    `分类=${node.category || "未知"}`,
    `重要性=${node.importance || "未知"}`,
    `有效期=${node.validity || "未知"}`,
    `状态=${status}`,
    `主题=${theme}`,
  ].join("；");
}

function humanizeStatement(value: string | undefined): string {
  if (!value) return "";
  const withoutPrefix = value
    .replace(/^静态图谱低敏摘要[：:]\s*/, "")
    .replace(/层级=/g, "层级是")
    .replace(/分类=/g, "分类是")
    .replace(/重要性=/g, "重要性是")
    .replace(/有效期=/g, "有效期是")
    .replace(/主题=/g, "主题是");
  return truncate(withoutPrefix, 150);
}

function compactThemeLabel(value: string): string {
  return value
    .replace(/agent continuity/gi, "Agent 连续性")
    .replace(/agent/gi, "Agent")
    .replace(/workflow/gi, "工作流")
    .replace(/token/gi, "Token")
    .replace(/dashboard/gi, "仪表盘")
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 2)
    .join(" / ")
    .slice(0, 38);
}

function normalizeDisplayKey(value: string): string {
  return value
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[，。；：、/|·:;,.()[\]（）【】「」]/g, "")
    .trim();
}

function humanThemeLabel(node: AtlasNode): string {
  const cluster = node.visual?.cluster;
  if (cluster) return themeLabelFromCluster(cluster);
  const parts = node.label.split("·").map((part) => part.trim()).filter(Boolean);
  return parts[2] || node.category || normalizeMemoryTier(node.memory_tier) || translateKind(node.kind);
}

function themeLabelFromCluster(cluster: string): string {
  const labels: Record<string, string> = {
    "memory-rag-continuity": "长期记忆库 / RAG / Agent 连续性",
    "codex-agent-workflow": "Codex / Agent 工作流 / Token ROI",
    "learning-notion-nitrosend": "学习系统 / Notion / 仪表盘",
    "rotary-kiln-industrial": "回转窑 / 工业服务 / 动态测量调整",
    "finance-trading-probability": "金融 / 交易 / FIFA / 概率决策",
    "course-reporting": "课程 / 公司报告 / 可持续报告",
    "ai-era-growth": "AI 时代 / 社会影响 / 个人能力突破",
    "formal-engineering-delivery": "EVA OS / 系统开发 / Task Pack",
    uncategorized: "其他待人工归类主题",
  };
  return labels[cluster] ?? cluster;
}

function humanCategoryLabel(value: string | undefined): string {
  const labels: Record<string, string> = {
    answering_rule: "回答规则",
    decision: "重要决策",
    deprecated_info: "历史/可能过时信息",
    fact: "事实资料",
    preference: "个人偏好",
    project_context: "项目上下文",
    security_boundary: "安全边界",
    temporary_or_sensitive: "短期/敏感背景",
    workflow: "工作流",
  };
  return labels[value ?? ""] ?? value ?? "未分类";
}

function countBy<T>(items: T[], getKey: (item: T) => string): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const key = getKey(item) || "未分类";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
}

function remapValues(values: Record<string, number>, mapKey: (key: string) => string): Record<string, number> {
  return Object.entries(values).reduce<Record<string, number>>((acc, [key, count]) => {
    const label = mapKey(key) || "未分类";
    acc[label] = (acc[label] ?? 0) + count;
    return acc;
  }, {});
}

function topRows(values: Record<string, number>, limit: number): Array<{ label: string; count: number }> {
  const rows = Object.entries(values)
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "zh-CN"))
    .slice(0, limit);
  return rows.length ? rows : [{ label: "暂无数据", count: 0 }];
}

function buildSearchVisualRows(nodes: AtlasNode[]): {
  topics: Array<{ label: string; count: number }>;
  tiers: Array<{ label: string; count: number }>;
  signals: Array<{ label: string; count: number }>;
} {
  const latest = maxNodeDate(nodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  return {
    topics: topRows(countBy(nodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)), 7),
    tiers: topRows(countBy(nodes, (node) => normalizeMemoryTier(node.memory_tier)), 4),
    signals: [
      { label: "近 30 天", count: nodes.filter((node) => isNodeBetween(node, recentStart, latest)).length },
      { label: "决策", count: nodes.filter((node) => node.category === "decision").length },
      { label: "核心画像", count: nodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length },
      { label: "待行动", count: nodes.filter((node) => /todo|action|执行|继续|需要|下一步/i.test(`${node.label} ${node.statement ?? ""}`)).length },
    ],
  };
}

function buildMapLayout(nodes: AtlasNode[], edges: AtlasEdge[], limit: number): { nodes: LayoutNode[]; edges: LayoutEdge[]; groups: LayoutGroup[] } {
  const degree = degreeMap(edges);
  const themes = nodes.filter((node) => node.kind === "theme");
  const displayNodes = nodes
    .filter((node) => ["theme", "project", "decision", "memory"].includes(node.kind))
    .sort((a, b) => (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0))
    .slice(0, limit);
  const themeIds = new Map(themes.map((node, index) => [node.id.replace("theme:", ""), index]));
  const layoutNodes = displayNodes.map((node, index): LayoutNode => {
    const cluster = node.visual?.cluster ?? node.id.replace("theme:", "");
    const groupIndex = themeIds.get(cluster) ?? index % Math.max(themes.length, 1);
    const groupAngle = (groupIndex / Math.max(themes.length, 1)) * Math.PI * 2 - Math.PI / 2;
    const groupX = 500 + Math.cos(groupAngle) * 265;
    const groupY = 310 + Math.sin(groupAngle) * 205;
    const localAngle = stableUnit(node.id, "map-angle") * Math.PI * 2;
    const localRadius = node.kind === "theme" ? 0 : 28 + stableUnit(node.id, "map-radius") * 82;
    return {
      node,
      x: node.kind === "theme" ? groupX : groupX + Math.cos(localAngle) * localRadius,
      y: node.kind === "theme" ? groupY : groupY + Math.sin(localAngle) * localRadius,
      r: nodeRadius(node, degree.get(node.id) ?? 0),
      color: nodeColor(node),
      label: shortNodeLabel(node, node.kind === "theme" ? 20 : 12),
      degree: degree.get(node.id) ?? 0,
    };
  });
  const byId = new Map(layoutNodes.map((node) => [node.node.id, node]));
  const layoutEdges = edges
    .map((edge): LayoutEdge | null => {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target) return null;
      return { id: edge.id, source, target, weight: edge.weight, color: source.color };
    })
    .filter((edge): edge is LayoutEdge => Boolean(edge))
    .slice(0, 420);
  const groups = themes.map((theme, index): LayoutGroup => {
    const angle = (index / Math.max(themes.length, 1)) * Math.PI * 2 - Math.PI / 2;
    return {
      id: theme.id,
      label: shortNodeLabel(theme, 18),
      x: 500 + Math.cos(angle) * 265,
      y: 310 + Math.sin(angle) * 205,
      r: 112,
      color: nodeColor(theme),
    };
  });
  return { nodes: layoutNodes, edges: layoutEdges, groups };
}

function buildObsidianLayout(
  nodes: AtlasNode[],
  edges: AtlasEdge[],
  selectedNode: AtlasNode | null,
  localOnly: boolean,
  depth: number,
): { nodes: LayoutNode[]; edges: LayoutEdge[] } {
  const visibleIds = localOnly && selectedNode ? expandGraphIds(selectedNode.id, edges, depth) : new Set(nodes.map((node) => node.id));
  const filteredNodes = nodes
    .filter((node) => visibleIds.has(node.id))
    .sort((a, b) => kindRank(a.kind) - kindRank(b.kind))
    .slice(0, 220);
  const filteredNodeIds = new Set(filteredNodes.map((node) => node.id));
  const filteredEdges = edges.filter((edge) => filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)).slice(0, 650);
  const degree = degreeMap(filteredEdges);
  const count = filteredNodes.length || 1;
  const layoutNodes = filteredNodes.map((node, index): LayoutNode => {
    const clusterSeed = clusterIndex(node);
    const ring = node.kind === "theme" ? 120 : node.kind === "memory" ? 225 : 175;
    const angle = (index / count) * Math.PI * 2 + clusterSeed * 0.38;
    const jitter = (stableUnit(node.id, "obsidian-radius") - 0.5) * 72;
    return {
      node,
      x: 500 + Math.cos(angle) * (ring + jitter),
      y: 300 + Math.sin(angle) * (ring * 0.72 + jitter * 0.45),
      r: nodeRadius(node, degree.get(node.id) ?? 0),
      color: nodeColor(node),
      label: (degree.get(node.id) ?? 0) > 6 || node.kind !== "memory" ? shortNodeLabel(node, 14) : "",
      degree: degree.get(node.id) ?? 0,
    };
  });
  const byId = new Map(layoutNodes.map((node) => [node.node.id, node]));
  const layoutEdges = filteredEdges
    .map((edge): LayoutEdge | null => {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target) return null;
      return { id: edge.id, source, target, weight: edge.weight, color: edge.kind === "belongs_to_theme" ? target.color : "rgba(244,241,232,0.7)" };
    })
    .filter((edge): edge is LayoutEdge => Boolean(edge));
  return { nodes: layoutNodes, edges: layoutEdges };
}

function buildTimelineLayout(timeline: TimelineEvent[], nodeMap: Map<string, AtlasNode>, controls: TimelineLayoutControls) {
  const allEvents = timeline
    .map((event) => ({ source: event, day: parseDay(event.date), node: nodeMap.get(event.node_id) }))
    .filter((event): event is { source: TimelineEvent; day: Date; node: AtlasNode | undefined } => Boolean(event.day))
    .sort((a, b) => a.day.getTime() - b.day.getTime());
  const minAllDay = allEvents[0]?.day ?? new Date();
  const maxAllDay = allEvents[allEvents.length - 1]?.day ?? minAllDay;
  const totalSpan = Math.max(1, maxAllDay.getTime() - minAllDay.getTime());
  const zoom = Math.min(8, Math.max(1, controls.zoom || 1));
  const visibleSpan = Math.max(1, totalSpan / zoom);
  const rawCenter = minAllDay.getTime() + totalSpan * Math.min(1, Math.max(0, controls.center));
  const minWindow = minAllDay.getTime();
  const maxWindow = maxAllDay.getTime();
  const unclampedStart = rawCenter - visibleSpan / 2;
  const windowStartMs = Math.max(minWindow, Math.min(Math.max(minWindow, maxWindow - visibleSpan), unclampedStart));
  const windowEndMs = Math.min(maxWindow, windowStartMs + visibleSpan);
  const minDay = new Date(windowStartMs);
  const maxDay = new Date(windowEndMs);
  const span = Math.max(1, windowEndMs - windowStartMs);
  const cursor = Math.min(1, Math.max(0, controls.cursor));
  const cursorMs = windowStartMs + span * cursor;
  const visibleEvents = allEvents
    .filter((event) => event.day.getTime() >= windowStartMs && event.day.getTime() <= windowEndMs)
    .slice(-260);
  const laneKeys = uniqueSorted(visibleEvents.map((event) => normalizeMemoryTier(event.source.memory_tier) || event.source.category)).slice(0, 7);
  const lanes = laneKeys.map((key, index) => ({
    key,
    label: translateTierOrKind(key),
    y: 95 + index * (410 / Math.max(laneKeys.length - 1, 1)),
    color: laneColor(key, index),
  }));
  const laneMap = new Map(lanes.map((lane) => [lane.key, lane]));
  const ticks = buildMonthTicks(minDay, maxDay, 80, 960);
  const eventTicks = buildEventDateTicks(visibleEvents, minDay, maxDay, 80, 960);
  const densityBands = buildTimelineDensityBands(allEvents, minAllDay, maxAllDay, windowStartMs, windowEndMs);
  const densityBars = buildTimelineDensityBackdrops(visibleEvents, minDay, maxDay);
  const importantCount = visibleEvents.filter((event) => event.source.importance === "高" || event.source.category === "decision").length;
  const coreCount = visibleEvents.filter((event) => normalizeMemoryTier(event.source.memory_tier) === "核心画像").length;
  return {
    lanes,
    ticks,
    eventTicks,
    densityBands,
    densityBars,
    rangeLabel: `${formatAxisDate(minDay)} - ${formatAxisDate(maxDay)}`,
    cursorLabel: formatAxisDate(new Date(cursorMs)),
    cursorX: 80 + cursor * 880,
    totalCount: allEvents.length,
    visibleCount: visibleEvents.length,
    importantCount,
    coreCount,
    peakDensity: Math.max(0, ...densityBands.map((band) => band.count)),
    events: visibleEvents.map((event, index) => {
      const lane = laneMap.get(normalizeMemoryTier(event.source.memory_tier) || event.source.category) ?? lanes[index % Math.max(lanes.length, 1)];
      const x = 80 + ((event.day.getTime() - minDay.getTime()) / span) * 880;
      const major = event.source.importance === "高" || event.source.category === "decision" || index % 11 === 0;
      return {
        id: `${event.source.date}-${event.source.node_id}-${event.source.memory_id || index}`,
        source: event.source,
        node: event.node,
        x,
        y: lane?.y ?? 300,
        radius: event.source.importance === "高" ? 9 : event.source.category === "decision" ? 8 : 5,
        color: event.node ? nodeColor(event.node) : lane?.color ?? "#94a3b8",
        major,
        future: event.day.getTime() > cursorMs,
        shortLabel: truncate(event.source.label, 18),
      };
    }),
  };
}

function buildTimelineDensityBands(
  events: Array<{ day: Date }>,
  minDay: Date,
  maxDay: Date,
  windowStartMs: number,
  windowEndMs: number,
) {
  const count = 48;
  const totalSpan = Math.max(1, maxDay.getTime() - minDay.getTime());
  const bins = Array.from({ length: count }, (_unused, index) => ({
    key: `density-${index}`,
    count: 0,
    center: (index + 0.5) / count,
    label: "",
    intensity: 0,
    active: false,
  }));
  for (const event of events) {
    const ratio = Math.min(0.999, Math.max(0, (event.day.getTime() - minDay.getTime()) / totalSpan));
    bins[Math.floor(ratio * count)].count += 1;
  }
  const peak = Math.max(1, ...bins.map((bin) => bin.count));
  return bins.map((bin, index) => {
    const start = new Date(minDay.getTime() + totalSpan * (index / count));
    const end = new Date(minDay.getTime() + totalSpan * ((index + 1) / count));
    return {
      ...bin,
      label: `${formatAxisDate(start)}-${formatAxisDate(end)}`,
      intensity: bin.count > 0 ? Math.log1p(bin.count) / Math.log1p(peak) : 0,
      active: end.getTime() >= windowStartMs && start.getTime() <= windowEndMs,
    };
  });
}

function buildTimelineDensityBackdrops(
  events: Array<{ day: Date }>,
  minDay: Date,
  maxDay: Date,
) {
  const count = 36;
  const span = Math.max(1, maxDay.getTime() - minDay.getTime());
  const bins = Array.from({ length: count }, (_unused, index) => ({ key: `timeline-band-${index}`, count: 0 }));
  for (const event of events) {
    const ratio = Math.min(0.999, Math.max(0, (event.day.getTime() - minDay.getTime()) / span));
    bins[Math.floor(ratio * count)].count += 1;
  }
  const peak = Math.max(1, ...bins.map((bin) => bin.count));
  return bins.map((bin, index) => {
    const width = 880 / count;
    const intensity = bin.count > 0 ? Math.log1p(bin.count) / Math.log1p(peak) : 0;
    return {
      key: bin.key,
      x: 80 + index * width,
      y: 540 - Math.max(12, intensity * 430),
      width: Math.max(8, width - 1),
      height: Math.max(12, intensity * 430),
    };
  });
}

function buildContributionPeriods(atlas: MemoryAtlas, nodes: AtlasNode[], filters: AtlasFilters, selectedYear: number) {
  const latest = parseDay(atlas.contribution.range_end) ?? new Date(Date.UTC(selectedYear, 11, 31));
  const year = selectedYear;
  const startYear = year - 1;
  const endYear = year;
  const globalDaily = new Map(atlas.contribution.daily.map((bucket) => [bucket.date, bucket]));
  const filteredDaily = aggregateFilteredNodes(nodes, "day");
  const yearStart = new Date(Date.UTC(year, 0, 1));
  const daysInYear = isLeapYear(year) ? 366 : 365;
  const startWeekday = mondayWeekdayIndex(yearStart);
  const weekColumns = Math.ceil((daysInYear + startWeekday) / 7);
  const periods = new Map<string, PeriodCounts & { delta: number; previousLabel: string }>();
  const filterActive =
    filters.query !== "" || filters.tier !== "all" || filters.category !== "all" || filters.theme !== "all";

  const dailyCells = Array.from({ length: daysInYear }, (_, index) => {
    const day = addDays(yearStart, index);
    const dateKey = toDayKey(day);
    const global = globalDaily.get(dateKey);
    const filtered = filteredDaily.get(dateKey);
    const weekColumn = Math.floor((index + startWeekday) / 7);
    const weekKey = calendarWeekKey(year, weekColumn);
    const count = mergePeriodCounts(dateKey, formatChineseDate(day), global, filtered, filterActive);
    periods.set(dateKey, withDelta(count, periods.get(toDayKey(addDays(day, -1)))));
    return {
      ...count,
      weekday: mondayWeekdayIndex(day),
      weekColumn,
      weekKey,
      activityLevel: count.activityLevel,
    };
  });

  const weeklyMap = aggregateCells(dailyCells, (cell) => cell.weekKey, (cell) => `第 ${cell.weekColumn + 1} 周`);
  const weekColumnByKey = new Map<string, number>();
  for (const cell of dailyCells) {
    if (!weekColumnByKey.has(cell.weekKey)) {
      weekColumnByKey.set(cell.weekKey, cell.weekColumn);
    }
  }
  const weekEntries = Array.from(weeklyMap.entries()).sort((a, b) => (weekColumnByKey.get(a[0]) ?? 0) - (weekColumnByKey.get(b[0]) ?? 0));
  weekEntries.forEach(([key, value], index) => {
    const previousValue = index > 0 ? weekEntries[index - 1][1] : undefined;
    periods.set(key, withDelta(value, previousValue));
  });
  const weekCells = weekEntries.map(([key, value]) => ({
    ...(periods.get(key) ?? withDelta(value, undefined)),
    weekKey: key,
    weekColumn: weekColumnByKey.get(key) ?? 0,
    daySlots: Array.from({ length: 7 }, (_, weekday) => dailyCells.find((cell) => cell.weekKey === key && cell.weekday === weekday) ?? null),
  }));

  const globalMonthly = new Map(atlas.contribution.monthly.map((bucket) => [bucket.date, bucket]));
  const filteredMonthly = aggregateFilteredNodes(nodes, "month");
  const monthCells = Array.from({ length: 24 }, (_, index) => {
    const cellYear = startYear + Math.floor(index / 12);
    const month = index % 12;
    const dateKey = `${cellYear}-${String(month + 1).padStart(2, "0")}`;
    const count = mergePeriodCounts(dateKey, `${cellYear} 年 ${month + 1} 月`, globalMonthly.get(dateKey), filteredMonthly.get(dateKey), filterActive);
    const previousKey = month === 0 ? `${cellYear - 1}-12` : `${cellYear}-${String(month).padStart(2, "0")}`;
    periods.set(dateKey, withDelta(count, periods.get(previousKey)));
    return {
      ...count,
      year: cellYear,
      month,
      monthLabel: `${month + 1}月`,
      daySlots: buildMonthDaySlots(cellYear, month, globalDaily, filteredDaily, filterActive),
    };
  });
  const yearlyMap = aggregateCells(monthCells, (cell) => String(cell.year), (cell) => `${cell.year} 年`);
  for (const [key, value] of yearlyMap) {
    periods.set(key, withDelta(value, periods.get(String(Number(key) - 1)) ?? yearlyMap.get(String(Number(key) - 1))));
  }
  const yearCells = [startYear, endYear].map((cellYear) => {
    const key = String(cellYear);
    const yearlyValue = periods.get(key) ?? withDelta(yearlyMap.get(key) ?? aggregateCells(monthCells.filter((cell) => cell.year === cellYear), () => key, () => `${cellYear} 年`).get(key)!, undefined);
    return {
      ...yearlyValue,
      year: cellYear,
      monthSlots: monthCells.filter((cell) => cell.year === cellYear),
    };
  });
  const latestWithinYear = latest.getUTCFullYear() === year ? latest : new Date(Date.UTC(year, 11, 31));
  const latestDayKey = toDayKey(latestWithinYear);
  const latestWeekKey = calendarWeekKey(year, Math.floor((dayOfYearIndex(latestWithinYear) + startWeekday) / 7));
  const latestMonthKey = `${year}-${String(latestWithinYear.getUTCMonth() + 1).padStart(2, "0")}`;
  const latestYearKey = String(year);
  const defaultPeriod =
    periods.get(latestDayKey) ??
    withDelta(mergePeriodCounts(latestDayKey, formatChineseDate(latestWithinYear), undefined, undefined, filterActive), undefined);
  const dayMaxActivityScore = maxActivityScore(dailyCells);
  const weekMaxActivityScore = maxActivityScore(weekCells);
  const monthMaxActivityScore = maxActivityScore(monthCells);
  const yearMaxActivityScore = maxActivityScore(yearCells);
  return {
    dailyCells,
    weekCells,
    monthCells,
    yearCells,
    periods,
    latestDayKey,
    latestWeekKey,
    latestMonthKey,
    latestYearKey,
    defaultPeriod,
    weekColumns,
    year,
    startYear,
    endYear,
    dayMaxActivityScore,
    weekMaxActivityScore,
    monthMaxActivityScore,
    yearMaxActivityScore,
  };
}

function buildMonthDaySlots(
  cellYear: number,
  month: number,
  globalDaily: Map<string, ActivityBucket>,
  filteredDaily: Map<string, ActivityBucket>,
  filterActive: boolean,
) {
  const firstDay = new Date(Date.UTC(cellYear, month, 1));
  const daysInMonth = new Date(Date.UTC(cellYear, month + 1, 0)).getUTCDate();
  return Array.from({ length: daysInMonth }, (_, index) => {
    const day = addDays(firstDay, index);
    const dateKey = toDayKey(day);
    return mergePeriodCounts(dateKey, formatChineseDate(day), globalDaily.get(dateKey), filteredDaily.get(dateKey), filterActive);
  });
}

function maxActivityScore(items: Array<{ activityScore?: number } | null>) {
  return Math.max(0, ...items.map((item) => Number(item?.activityScore ?? 0)));
}

function buildContributionPeriodDetail(
  scale: ContributionScale,
  bucket: PeriodCounts,
  nodes: AtlasNode[],
): ContributionPeriodDetail {
  const relatedNodes = nodes
    .filter((node) => nodeMatchesContributionPeriod(node, scale, bucket.date))
    .sort((a, b) => {
      const score = (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0);
      if (score !== 0) return score;
      return (b.date ?? "").localeCompare(a.date ?? "");
    });
  return { scale, bucket, relatedNodes };
}

function nodeMatchesContributionPeriod(node: AtlasNode, scale: ContributionScale, periodKey: string): boolean {
  const day = parseDay(node.date);
  if (!day) return false;
  if (scale === "day") return toDayKey(day) === periodKey;
  if (scale === "month") return `${day.getUTCFullYear()}-${String(day.getUTCMonth() + 1).padStart(2, "0")}` === periodKey;
  if (scale === "year") return String(day.getUTCFullYear()) === periodKey;
  const year = day.getUTCFullYear();
  const startWeekday = mondayWeekdayIndex(new Date(Date.UTC(year, 0, 1)));
  return calendarWeekKey(year, Math.floor((dayOfYearIndex(day) + startWeekday) / 7)) === periodKey;
}

function periodMeaningLine(bucket: PeriodCounts, scale: ContributionScale): string {
  const label = scale === "day" ? "这一天" : scale === "week" ? "这一周" : scale === "month" ? "这个月" : "这一年";
  if (bucket.activityScore <= 0) return `${label}没有明显活动，适合作为低使用或空窗期参考。`;
  if (bucket.filteredCoreCount > 0) return `${label}出现核心画像增量，说明有会影响长期 personalization 或 agent 默认行为的信息。`;
  if (bucket.filteredDecisionCount > 0) return `${label}出现新的决策记录，后续项目和 agent 执行应默认继承这些选择。`;
  if (bucket.filteredMemoryCount > 0) return `${label}沉淀了新的记忆内容，适合检查是否已经转成可执行待办或可复用上下文。`;
  return `${label}主要体现交互强度变化，具体记忆增量较少，适合用于使用行为复盘。`;
}

function periodImpactLine(bucket: PeriodCounts, relatedNodeCount: number): string {
  if (bucket.filteredCoreCount > 0) {
    return "它会影响未来 ChatGPT / Codex / 其他 agent 对你的默认理解，应该优先进入 personalization 和核心画像复盘。";
  }
  if (bucket.filteredDecisionCount > 0) {
    return "它包含决策密度，价值在于避免未来重复决策，并把当时的选择接入后续执行。";
  }
  if (relatedNodeCount > 0) {
    return `它关联 ${relatedNodeCount.toLocaleString()} 条具体记忆，可以直接回看这段时间你关注过什么、推进过什么、哪些事情值得继续。`;
  }
  if (bucket.messageCount > 0) {
    return "它说明这段时间有明显交互行为，但当前筛选下没有对应记忆，可能需要补做记忆抽取或复盘。";
  }
  return "它的价值主要是作为基线，帮助识别真正的使用高峰、低频空窗和后续增量变化。";
}

function defaultPeriodKeyForScale(
  scale: ContributionScale,
  periodData: ReturnType<typeof buildContributionPeriods>,
): string {
  if (scale === "day") return periodData.latestDayKey;
  if (scale === "week") return periodData.latestWeekKey;
  if (scale === "month") return periodData.latestMonthKey;
  return periodData.latestYearKey;
}

function aggregateFilteredNodes(nodes: AtlasNode[], period: "day" | "month") {
  const map = new Map<string, ActivityBucket>();
  for (const node of nodes) {
    const day = parseDay(node.date);
    if (!day) continue;
    const key = period === "day" ? toDayKey(day) : `${day.getUTCFullYear()}-${String(day.getUTCMonth() + 1).padStart(2, "0")}`;
    const bucket = map.get(key) ?? blankBucket(key);
    bucket.memory_count += 1;
    if (node.category === "decision") bucket.decision_count += 1;
    const tier = normalizeMemoryTier(node.memory_tier);
    if (tier === "核心画像") bucket.core_memory_count += 1;
    else if (tier === "一般") bucket.mid_long_memory_count += 1;
    else bucket.short_memory_count += 1;
    bucket.activity_score = bucket.memory_count * 3 + bucket.decision_count * 4;
    bucket.activity_level = Math.max(1, Math.min(5, Math.ceil(bucket.activity_score / 6)));
    map.set(key, bucket);
  }
  return map;
}

function mergePeriodCounts(
  dateKey: string,
  label: string,
  global: ActivityBucket | undefined,
  filtered: ActivityBucket | undefined,
  filterActive: boolean,
): PeriodCounts {
  const activityScore = filterActive ? filtered?.activity_score ?? 0 : global?.activity_score ?? filtered?.activity_score ?? 0;
  return {
    date: dateKey,
    label,
    activityScore,
    activityLevel: global?.activity_level ?? filtered?.activity_level ?? levelFromScore(activityScore),
    globalActivityScore: global?.activity_score ?? 0,
    conversationCount: global?.conversation_count ?? 0,
    messageCount: global?.message_count ?? 0,
    memoryCount: global?.memory_count ?? 0,
    decisionCount: global?.decision_count ?? 0,
    coreMemoryCount: global?.core_memory_count ?? 0,
    midLongMemoryCount: global?.mid_long_memory_count ?? 0,
    shortMemoryCount: global?.short_memory_count ?? 0,
    filteredMemoryCount: filtered?.memory_count ?? 0,
    filteredDecisionCount: filtered?.decision_count ?? 0,
    filteredCoreCount: filtered?.core_memory_count ?? 0,
    toolCallCount: global?.tool_call_count ?? 0,
    errorEventCount: global?.error_event_count ?? 0,
    abortCount: global?.abort_count ?? 0,
  };
}

function aggregateCells<T extends PeriodCounts>(cells: T[], getKey: (cell: T) => string, getLabel: (cell: T) => string) {
  const map = new Map<string, PeriodCounts>();
  for (const cell of cells) {
    const key = getKey(cell);
    const target = map.get(key) ?? {
      date: key,
      label: getLabel(cell),
      activityScore: 0,
      activityLevel: 0,
      globalActivityScore: 0,
      conversationCount: 0,
      messageCount: 0,
      memoryCount: 0,
      decisionCount: 0,
      coreMemoryCount: 0,
      midLongMemoryCount: 0,
      shortMemoryCount: 0,
      filteredMemoryCount: 0,
      filteredDecisionCount: 0,
      filteredCoreCount: 0,
      toolCallCount: 0,
      errorEventCount: 0,
      abortCount: 0,
    };
    for (const keyName of [
      "activityScore",
      "globalActivityScore",
      "conversationCount",
      "messageCount",
      "memoryCount",
      "decisionCount",
      "coreMemoryCount",
      "midLongMemoryCount",
      "shortMemoryCount",
      "filteredMemoryCount",
      "filteredDecisionCount",
      "filteredCoreCount",
      "toolCallCount",
      "errorEventCount",
      "abortCount",
    ] as const) {
      target[keyName] = (target[keyName] ?? 0) + (cell[keyName] ?? 0);
    }
    target.activityLevel = levelFromScore(target.activityScore);
    map.set(key, target);
  }
  return map;
}

function withDelta(current: PeriodCounts, previous?: PeriodCounts): PeriodCounts & { delta: number; previousLabel: string } {
  return {
    ...current,
    delta: current.activityScore - (previous?.activityScore ?? 0),
    previousLabel: previous?.label ?? "上一周期",
  };
}

function degreeMap(edges: AtlasEdge[]): Map<string, number> {
  const counts = new Map<string, number>();
  for (const edge of edges) {
    counts.set(edge.source, (counts.get(edge.source) ?? 0) + 1);
    counts.set(edge.target, (counts.get(edge.target) ?? 0) + 1);
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

function buildMonthTicks(minDay: Date, maxDay: Date, minX: number, maxX: number) {
  const ticks: Array<{ label: string; x: number }> = [];
  const start = new Date(Date.UTC(minDay.getUTCFullYear(), minDay.getUTCMonth(), 1));
  const end = new Date(Date.UTC(maxDay.getUTCFullYear(), maxDay.getUTCMonth(), 1));
  const span = Math.max(1, maxDay.getTime() - minDay.getTime());
  let cursor = start;
  while (cursor <= end) {
    const x = minX + ((cursor.getTime() - minDay.getTime()) / span) * (maxX - minX);
    ticks.push({ label: `${cursor.getUTCFullYear()}.${cursor.getUTCMonth() + 1}`, x });
    cursor = new Date(Date.UTC(cursor.getUTCFullYear(), cursor.getUTCMonth() + 1, 1));
  }
  return ticks.filter((_, index) => index % Math.max(1, Math.ceil(ticks.length / 8)) === 0);
}

function buildEventDateTicks(
  events: Array<{ source: TimelineEvent; day: Date }>,
  minDay: Date,
  maxDay: Date,
  minX: number,
  maxX: number,
) {
  const grouped = new Map<string, { date: string; day: Date; count: number; score: number }>();
  for (const event of events) {
    const date = toDayKey(event.day);
    const current = grouped.get(date) ?? { date, day: event.day, count: 0, score: 0 };
    current.count += 1;
    current.score += event.source.importance === "高" ? 8 : event.source.category === "decision" ? 6 : 1;
    grouped.set(date, current);
  }
  const all = Array.from(grouped.values()).sort((a, b) => a.day.getTime() - b.day.getTime());
  if (all.length <= 12) return all.map((tick, index) => eventDateTick(tick, index, minDay, maxDay, minX, maxX));
  const selected = new Map<string, (typeof all)[number]>();
  selected.set(all[0].date, all[0]);
  selected.set(all[all.length - 1].date, all[all.length - 1]);
  const span = Math.max(1, maxDay.getTime() - minDay.getTime());
  const xFor = (day: Date) => minX + ((day.getTime() - minDay.getTime()) / span) * (maxX - minX);
  const ranked = [...all].sort((a, b) => b.count * 3 + b.score - (a.count * 3 + a.score));
  for (const candidate of ranked) {
    if (selected.size >= 12) break;
    const candidateX = xFor(candidate.day);
    const hasSpace = Array.from(selected.values()).every((tick) => Math.abs(candidateX - xFor(tick.day)) >= 62);
    if (hasSpace) selected.set(candidate.date, candidate);
  }
  return Array.from(selected.values())
    .sort((a, b) => a.day.getTime() - b.day.getTime())
    .map((tick, index) => eventDateTick(tick, index, minDay, maxDay, minX, maxX));
}

function eventDateTick(
  tick: { date: string; day: Date; count: number },
  index: number,
  minDay: Date,
  maxDay: Date,
  minX: number,
  maxX: number,
) {
  const span = Math.max(1, maxDay.getTime() - minDay.getTime());
  return {
    date: tick.date,
    label: formatAxisDate(tick.day),
    x: minX + ((tick.day.getTime() - minDay.getTime()) / span) * (maxX - minX),
    count: tick.count,
    stagger: index % 2,
  };
}

function formatAxisDate(day: Date) {
  return `${day.getUTCFullYear()}.${day.getUTCMonth() + 1}.${day.getUTCDate()}`;
}

function filteredMetricValues(nodes: AtlasNode[], key: "memory_tier" | "category"): Record<string, number> {
  return nodes.reduce<Record<string, number>>((acc, node) => {
    const value = key === "memory_tier" ? normalizeMemoryTier(node.memory_tier) : node[key] || "unknown";
    acc[value] = (acc[value] ?? 0) + 1;
    return acc;
  }, {});
}

function topEntry(values: Record<string, number>): [string, number] | undefined {
  return Object.entries(values).sort((a, b) => b[1] - a[1])[0];
}

function nodeRadius(node: AtlasNode, degree: number): number {
  const base = node.kind === "theme" ? 18 : node.kind === "project" ? 15 : node.kind === "decision" ? 13 : 8;
  return Math.min(28, base + Math.sqrt(Math.max(0, degree)) * 1.6 + (node.metrics?.roi?.leverage_score ?? 0) * 4);
}

function nodeColor(node: AtlasNode): string {
  if (node.kind === "decision") return "#f48fb1";
  if (node.kind === "project") return "#8fd3ff";
  const tier = normalizeMemoryTier(node.memory_tier);
  if (tier === "核心画像") return "#7ee8d4";
  if (tier === "一般") return node.visual?.color ?? "#8fd3ff";
  return node.visual?.color ?? "#94a3b8";
}

function isGraphParentNode(node: AtlasNode): boolean {
  return node.kind === "theme" || node.kind === "project" || node.kind === "category" || node.kind === "tier";
}

function clusterIndex(node: AtlasNode): number {
  return Math.floor(stableUnit(node.visual?.cluster ?? node.category ?? node.id, "cluster") * 12);
}

function kindRank(kind: AtlasNode["kind"]): number {
  return { theme: 0, project: 1, decision: 2, memory: 3, category: 4, tier: 5, timeline_event: 6 }[kind] ?? 9;
}

function kindLabelSign(kind: AtlasNode["kind"]): string {
  return { theme: "主题", project: "项目", decision: "决策", memory: "记忆", category: "分类", tier: "层级", timeline_event: "事件" }[kind] ?? "节点";
}

function shortNodeLabel(node: AtlasNode, length: number): string {
  return truncate(node.kind === "memory" ? node.label : `${kindLabelSign(node.kind)} · ${node.label}`, length);
}

function laneColor(key: string, index: number): string {
  const colors = ["#7ee8d4", "#8fd3ff", "#48c7e8", "#f48fb1", "#c7a7ff", "#6ea8ff", "#94a3b8"];
  if (key === "核心画像") return "#7ee8d4";
  if (key === "一般") return "#8fd3ff";
  if (key === "decision") return "#f48fb1";
  return colors[index % colors.length];
}

function blankBucket(dateKey: string): ActivityBucket {
  return {
    date: dateKey,
    conversation_count: 0,
    message_count: 0,
    user_message_count: 0,
    assistant_message_count: 0,
    memory_count: 0,
    candidate_count: 0,
    decision_count: 0,
    core_memory_count: 0,
    mid_long_memory_count: 0,
    short_memory_count: 0,
    tool_call_count: 0,
    error_event_count: 0,
    abort_count: 0,
    codex_session_count: 0,
    activity_score: 0,
    activity_level: 0,
  };
}

function levelFromScore(score: number): number {
  if (score <= 0) return 0;
  if (score < 8) return 1;
  if (score < 24) return 2;
  if (score < 64) return 3;
  if (score < 160) return 4;
  return 5;
}

function contributionTitle(bucket: PeriodCounts) {
  return `${bucket.label}: 活动分 ${bucket.activityScore}; 全局对话 ${bucket.conversationCount}; 全局消息 ${bucket.messageCount}; 工具调用 ${bucket.toolCallCount ?? 0}; 错误事件 ${bucket.errorEventCount ?? 0}; 中断 ${bucket.abortCount ?? 0}; 筛选记忆 ${bucket.filteredMemoryCount}; 筛选决策 ${bucket.filteredDecisionCount}`;
}

function scaleLabel(scale: ContributionScale): string {
  return { day: "日", week: "周", month: "月", year: "年" }[scale];
}

function buildProposalDiff(baseText: string, proposedText: string): NonNullable<WritebackProposal["diff"]> {
  const base = normalizeTextForDiff(baseText);
  const proposed = normalizeTextForDiff(proposedText);
  const baseSegments = splitReadableSegments(base);
  const proposedSegments = splitReadableSegments(proposed);
  const baseSet = new Set(baseSegments);
  const proposedSet = new Set(proposedSegments);
  const changedSegments =
    proposedSegments.filter((segment) => !baseSet.has(segment)).length +
    baseSegments.filter((segment) => !proposedSet.has(segment)).length;
  const lengthDelta = proposed.length - base.length;
  return {
    base_text: base,
    proposed_text: proposed,
    length_delta: lengthDelta,
    changed_segments: changedSegments,
    summary: `长度 ${lengthDelta > 0 ? "+" : ""}${lengthDelta}，片段变化 ${changedSegments}`,
  };
}

function buildProposalReview(action: WritebackAction, node: AtlasNode, reason: string): NonNullable<WritebackProposal["review"]> {
  const tier = normalizeMemoryTier(node.memory_tier);
  const actionLabel = writebackActionLabels[action];
  return {
    human_summary: `${actionLabel}：${humanNodeTitle(node)}。${reason || "需要补充证据和冲突检查后再写入。"} `,
    agent_next_step: "重新读取当前主动记忆库和历史提案，核对来源、冲突、敏感字段与版本号，然后写入提案历史并提交 git 回滚点。",
    conflict_policy: `目标层级 ${tier || "未知"}；如果现有库已出现更新版本或同主题相反结论，必须先生成冲突报告，不可静默覆盖。`,
    apply_status: "proposal_only_pending_agent_apply",
  };
}

function normalizeTextForDiff(value: string | undefined): string {
  return (value ?? "").replace(/\s+/g, " ").trim();
}

function splitReadableSegments(value: string): string[] {
  return value
    .split(/[。！？!?;；\n]+/)
    .map((segment) => segment.trim())
    .filter(Boolean);
}

function loadWritebackProposals(): WritebackProposal[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(WRITEBACK_QUEUE_KEY);
    if (!raw) return [];
    const payload: unknown = JSON.parse(raw);
    if (!Array.isArray(payload)) return [];
    return payload.filter(isWritebackProposal);
  } catch {
    return [];
  }
}

function saveWritebackProposals(proposals: WritebackProposal[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(WRITEBACK_QUEUE_KEY, JSON.stringify(proposals));
}

function isWritebackProposal(value: unknown): value is WritebackProposal {
  if (!value || typeof value !== "object") return false;
  const record = value as Partial<WritebackProposal>;
  return (
    typeof record.schema_version === "string" &&
    typeof record.proposal_id === "string" &&
    typeof record.created_at === "string" &&
    record.status === "draft_pending_agent_apply" &&
    Boolean(record.target_ref) &&
    Boolean(record.payload) &&
    Boolean(record.version)
  );
}

function downloadJson(filename: string, payload: unknown) {
  const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function compactTimestamp(value: string): string {
  return value.replace(/[-:.]/g, "").replace("T", "T").replace("Z", "Z");
}

function stableHash(value: string): string {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(36).padStart(7, "0").slice(0, 7);
}

function translateKind(kind: AtlasNode["kind"]): string {
  return {
    memory: "记忆",
    theme: "主题",
    tier: "层级",
    category: "分类",
    project: "项目",
    decision: "决策",
    timeline_event: "时间事件",
  }[kind];
}

function translateTierOrKind(value: string): string {
  if (value === "decision") return "决策";
  if (value === "project") return "项目";
  if (value === "timeline_event") return "时间事件";
  return value;
}

function translateAction(value: string | undefined): string {
  return {
    keep_high_weight: "高权重保留",
    review_for_project_linkage: "复查项目连接",
    keep_low_weight_or_refresh: "低权重保留或刷新",
    keep_as_context: "作为上下文保留",
  }[value ?? ""] ?? "作为上下文保留";
}

function translateStaleness(value: string | undefined): string {
  return {
    stale_short_term: "临时信息已旧",
    needs_review: "需要复查",
    current: "当前有效",
    unknown: "未知时效",
  }[value ?? ""] ?? "未知时效";
}

function formatScore(value: number | undefined | null): string {
  return typeof value === "number" ? value.toFixed(2) : "n/a";
}

function formatSigned(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toLocaleString()}`;
}

function sumValues(values: Record<string, number>, keys: string[]): number {
  return keys.reduce((sum, key) => sum + (values[key] ?? 0), 0);
}

function parseDay(value: string | undefined): Date | null {
  if (!value) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (!match) return null;
  return new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
}

function maxNodeDate(nodes: AtlasNode[]): Date | null {
  return nodes.reduce<Date | null>((latest, node) => {
    const day = parseDay(node.date);
    if (!day) return latest;
    if (!latest || day > latest) return day;
    return latest;
  }, null);
}

function isNodeBetween(node: AtlasNode, start: Date, end: Date): boolean {
  const day = parseDay(node.date);
  return Boolean(day && day >= start && day <= end);
}

function addDays(day: Date, count: number): Date {
  const next = new Date(day.getTime());
  next.setUTCDate(next.getUTCDate() + count);
  return next;
}

function contributionYears(atlas: MemoryAtlas, nodes: AtlasNode[]): number[] {
  const years = new Set<number>();
  for (const bucket of atlas.contribution.daily) {
    const day = parseDay(bucket.date);
    if (day) years.add(day.getUTCFullYear());
  }
  for (const node of nodes) {
    const day = parseDay(node.date);
    if (day) years.add(day.getUTCFullYear());
  }
  if (!years.size) years.add(new Date().getUTCFullYear());
  return Array.from(years).sort((a, b) => a - b);
}

function buildIterationHighlights(nodes: AtlasNode[], deltaStats: DeltaStats) {
  const coreCount = nodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length;
  const decisionCount = nodes.filter((node) => node.category === "decision").length;
  const actionCount = nodes.filter((node) => /todo|action|执行|继续|需要|下一步/i.test(`${node.label} ${node.statement ?? ""}`)).length;
  return [
    {
      label: "核心画像",
      value: coreCount,
      note: "优先进入 ChatGPT / Codex Personalization，影响默认理解。",
    },
    {
      label: "决策",
      value: decisionCount,
      note: "后续 agent 执行时应继承，除非新证据明确推翻。",
    },
    {
      label: "近期增量",
      value: formatSigned(deltaStats.deltaCount),
      note: deltaStats.deltaRate === null ? "没有上一周期基准。" : `较上一周期 ${(deltaStats.deltaRate * 100).toFixed(2)}%。`,
    },
    {
      label: "可行动线索",
      value: actionCount,
      note: "适合进入下一轮任务、周复盘或项目待办。",
    },
  ];
}

function formatUpdatedAt(value: string | undefined): string {
  if (!value) return "待同步";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
}

function toDayKey(day: Date): string {
  return `${day.getUTCFullYear()}-${String(day.getUTCMonth() + 1).padStart(2, "0")}-${String(day.getUTCDate()).padStart(2, "0")}`;
}

function formatChineseDate(day: Date): string {
  return `${day.getUTCFullYear()} 年 ${day.getUTCMonth() + 1} 月 ${day.getUTCDate()} 日`;
}

function mondayWeekdayIndex(day: Date): number {
  return (day.getUTCDay() + 6) % 7;
}

function dayOfYearIndex(day: Date): number {
  const start = new Date(Date.UTC(day.getUTCFullYear(), 0, 1));
  return Math.floor((day.getTime() - start.getTime()) / 86400000);
}

function calendarWeekKey(year: number, weekColumn: number): string {
  return `${year}-CW${String(weekColumn + 1).padStart(2, "0")}`;
}

function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
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

function truncate(value: string, length: number): string {
  const text = value.replace(/\s+/g, " ").trim();
  return text.length > length ? `${text.slice(0, Math.max(0, length - 1))}…` : text;
}

function isActivationKey(event: KeyboardEvent): boolean {
  return event.key === "Enter" || event.key === " ";
}

function edgeCountFor(nodeId: string | undefined, edges: AtlasEdge[]): number {
  if (!nodeId) return 0;
  return edges.reduce((count, edge) => count + (edge.source === nodeId || edge.target === nodeId ? 1 : 0), 0);
}
