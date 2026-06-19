import type { AtlasFilters, AtlasMetric, AtlasNode, MemoryAtlas } from "../types";

const tierAliases: Record<string, string> = {
  "重要中长期": "一般",
  "一般短期": "临时",
};

export function normalizeMemoryTier(value: string | undefined): string {
  if (!value) return "未分层";
  return tierAliases[value] ?? value;
}

export const emptyAtlas: MemoryAtlas = {
  schema_version: "memory_atlas.empty",
  overview: {
    active_memory_count: 0,
    candidate_count_latest_snapshot: 0,
    conversation_count: 0,
    node_count: 0,
    edge_count: 0,
    memory_node_count: 0,
    theme_node_count: 0,
    generated_at: "",
  },
  source_contract: {
    mode: "empty",
    export_profile: "empty",
    source_files: {},
    writeback_policy: {
      frontend_can_request_writeback: false,
      writeback_must_use_proposals: true,
      proposal_dir: "",
      history_dir: "",
      rollback_unit: "",
      proposal_schema_version: "",
      editable_fields: [],
      direct_frontend_mutation_of_active_memory: false,
    },
  },
  visual_layers: {
    primary: "galaxy",
    secondary: [],
    navigation: "left_sidebar",
  },
  nodes: [],
  edges: [],
  timeline: [],
  contribution: {
    metric_note: "",
    score_version: "",
    range_start: "",
    range_end: "",
    max_activity_score: 0,
    quantiles: {},
    daily: [],
    weekly: [],
    monthly: [],
    yearly: [],
  },
  metrics: [],
  data_sources: [],
  agent_recommendations: {
    schema_version: "codex_agent_recommendations.empty",
    memory: { current: [], added: [], modified: [], deleted: [] },
    meta_data: { current: [], added: [], modified: [], deleted: [] },
  },
};

export async function loadMemoryAtlas(signal?: AbortSignal): Promise<MemoryAtlas> {
  const url = new URL("/memory_atlas.json", window.location.origin);
  url.searchParams.set("snapshot", String(Date.now()));
  const response = await fetch(url, {
    cache: "no-store",
    headers: { "Cache-Control": "no-cache" },
    signal,
  });
  if (!response.ok) {
    throw new Error(`Unable to load memory_atlas.json (${response.status})`);
  }
  const payload: unknown = await response.json();
  if (!isMemoryAtlas(payload)) {
    throw new Error("memory_atlas.json failed runtime contract validation");
  }
  return payload;
}

export function isMemoryAtlas(value: unknown): value is MemoryAtlas {
  if (!isRecord(value)) return false;
  return (
    value.schema_version === "memory_atlas.v1" &&
    isRecord(value.overview) &&
    typeof value.overview.active_memory_count === "number" &&
    typeof value.overview.node_count === "number" &&
    typeof value.overview.edge_count === "number" &&
    Array.isArray(value.nodes) &&
    Array.isArray(value.edges) &&
    Array.isArray(value.timeline) &&
    isRecord(value.contribution) &&
    Array.isArray(value.contribution.daily) &&
    Array.isArray(value.metrics) &&
    (value.data_sources === undefined || Array.isArray(value.data_sources)) &&
    isValidWritebackPolicy(value.source_contract)
  );
}

function isValidWritebackPolicy(value: unknown): boolean {
  if (!isRecord(value) || !isRecord(value.writeback_policy)) return false;
  return (
    value.mode === "public_redacted_read_only_visualization" &&
    value.writeback_policy.frontend_can_request_writeback === true &&
    value.writeback_policy.writeback_must_use_proposals === true &&
    value.writeback_policy.direct_frontend_mutation_of_active_memory === false
  );
}

function isRecord(value: unknown): value is Record<string, any> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function getMemoryNodes(atlas: MemoryAtlas): AtlasNode[] {
  return atlas.nodes.filter((node) => node.kind === "memory");
}

export function getThemeNodes(atlas: MemoryAtlas): AtlasNode[] {
  return atlas.nodes.filter((node) => node.kind === "theme");
}

export function getNodeMap(atlas: MemoryAtlas): Map<string, AtlasNode> {
  return new Map(atlas.nodes.map((node) => [node.id, node]));
}

export function filterMemoryNodes(nodes: AtlasNode[], filters: AtlasFilters): AtlasNode[] {
  const query = filters.query.trim().toLowerCase();
  return nodes.filter((node) => {
    const matchesQuery =
      !query ||
      [
        node.label,
        node.statement,
        node.category,
        node.memory_tier,
        normalizeMemoryTier(node.memory_tier),
        node.source_kind,
        node.source_label,
        node.data_source,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query));
    const matchesTier = filters.tier === "all" || normalizeMemoryTier(node.memory_tier) === filters.tier;
    const matchesSource = filters.source === "all" || (node.data_source ?? "memory_atlas") === filters.source;
    const matchesCategory = filters.category === "all" || node.category === filters.category;
    const matchesTheme = filters.theme === "all" || node.visual?.cluster === filters.theme;
    return matchesQuery && matchesSource && matchesTier && matchesCategory && matchesTheme;
  });
}

export function visibleGraphFor(atlas: MemoryAtlas, filteredMemoryNodes: AtlasNode[]) {
  const visibleIds = new Set(filteredMemoryNodes.map((node) => node.id));
  const seedIds = new Set(visibleIds);

  for (const edge of atlas.edges) {
    if (seedIds.has(edge.source)) visibleIds.add(edge.target);
    if (seedIds.has(edge.target)) visibleIds.add(edge.source);
  }

  const nodes = atlas.nodes.filter((node) => visibleIds.has(node.id));
  const edges = atlas.edges.filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target));
  return { nodes, edges };
}

export function metricValues(atlas: MemoryAtlas, kind: string): Record<string, number> {
  const values = atlas.metrics.find((metric: AtlasMetric) => metric.kind === kind)?.values ?? {};
  if (kind !== "tier") return values;
  return Object.entries(values).reduce<Record<string, number>>((acc, [key, value]) => {
    const normalized = normalizeMemoryTier(key);
    acc[normalized] = (acc[normalized] ?? 0) + value;
    return acc;
  }, {});
}

export function uniqueSorted(values: Array<string | undefined>): string[] {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value)))).sort((a, b) =>
    a.localeCompare(b, "zh-CN"),
  );
}
