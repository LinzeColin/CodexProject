import { normalizeMemoryTier } from "../../data/atlas";
import { MemoryRiverEvidenceLayer, MemoryRiverEvidencePoint, MemoryRiverLane, MemoryRiverLayout, MemoryRiverLevel, MemoryRiverLevelBand, MemoryRiverMarker, MemoryRiverRoiGradient, MemoryRiverRoiGradientBand, TimelineDisplayEvent } from "./contracts";
import { formatAxisDate, laneColor } from "./contributionModels";
import { stableHash } from "./inspectorWriteback";
import { isBlackHoleCandidate, isProtoStarCandidate } from "./previewWeatherModels";
import { MEMORY_RIVER_MAX_X, MEMORY_RIVER_MIN_X, MEMORY_RIVER_WIDTH } from "./runtimeConfig";
import { compactThemeLabel, humanCategoryLabel, humanThemeLabel } from "./semanticHuman";
import { addDays, formatScore, stableUnit, timelineUtcMs, translateTierOrKind, truncate } from "./utils";
import { clamp } from "../ui/visualStyles";



export function buildMemoryRiverLayout(events: TimelineDisplayEvent[], cursorX: number): MemoryRiverLayout {
  const levelSpecs: Array<MemoryRiverLevelBand & { maxLanes: number }> = [
    { level: "Macro", note: "层级 / 长期记忆气候", y: 118, maxLanes: 3 },
    { level: "Meso", note: "主题 / 项目迁移", y: 294, maxLanes: 4 },
    { level: "Micro", note: "分类 / 事件波纹", y: 464, maxLanes: 4 },
  ];
  const levelCounts: Record<MemoryRiverLevel, number> = { Macro: 0, Meso: 0, Micro: 0 };
  const lanes: MemoryRiverLane[] = [];
  const laneLookup = new Map<string, MemoryRiverLane>();

  for (const spec of levelSpecs) {
    const buckets = new Map<string, { key: string; label: string; events: TimelineDisplayEvent[]; score: number }>();
    for (const event of events) {
      const group = memoryRiverGroup(event, spec.level);
      const bucket = buckets.get(group.key) ?? { key: group.key, label: group.label, events: [], score: 0 };
      bucket.events.push(event);
      bucket.score += memoryRiverEventScore(event);
      buckets.set(group.key, bucket);
    }
    levelCounts[spec.level] = buckets.size;
    const selected = Array.from(buckets.values())
      .sort((a, b) => b.events.length - a.events.length || b.score - a.score || a.label.localeCompare(b.label, "zh-CN"))
      .slice(0, spec.maxLanes);
    const spacing = selected.length > 1 ? Math.min(42, 98 / Math.max(1, selected.length - 1)) : 0;
    selected.forEach((bucket, index) => {
      const y = spec.y + (index - (selected.length - 1) / 2) * spacing;
      const color = memoryRiverLaneColor(bucket.key, spec.level, index);
      const strokeWidth = Math.max(8, Math.min(34, 7 + Math.log1p(bucket.events.length) * 9 + bucket.score * 0.03));
      const lane: MemoryRiverLane = {
        id: `river-${spec.level.toLowerCase()}-${stableHash(`${spec.level}:${bucket.key}`)}`,
        groupKey: bucket.key,
        level: spec.level,
        label: truncate(bucket.label, spec.level === "Macro" ? 16 : 18),
        count: bucket.events.length,
        path: buildMemoryRiverPath(bucket.events, y),
        color,
        gradientId: `memory-river-gradient-${spec.level.toLowerCase()}-${index}-${stableHash(bucket.key)}`,
        strokeWidth,
        labelX: Math.max(96, Math.min(820, bucket.events[0]?.x ?? 120)),
        labelY: y - Math.max(14, strokeWidth / 2 + 7),
        y,
      };
      lanes.push(lane);
      laneLookup.set(`${spec.level}:${bucket.key}`, lane);
    });
  }

  const markerEvents = events
    .filter((event) => event.major || event.source.importance === "高" || ["decision", "deprecated_info", "temporary_or_sensitive"].includes(event.source.category))
    .sort((a, b) => timelineUtcMs(a.day) - timelineUtcMs(b.day))
    .slice(-64);
  const markers = markerEvents.map((event): MemoryRiverMarker => {
    const level = memoryRiverMarkerLevel(event);
    const group = memoryRiverGroup(event, level);
    const lane = laneLookup.get(`${level}:${group.key}`) ?? lanes.find((candidate) => candidate.level === level) ?? lanes[0];
    const kind = memoryRiverMarkerKind(event);
    return {
      id: `river-marker-${event.id}`,
      kind,
      event,
      title: `${event.utcDate} UTC · ${kind === "black-hole" ? "Black Hole" : kind === "proto-star" ? "Proto-Star" : "Memory Event"} · ROI ${formatScore(event.node?.metrics?.roi?.leverage_score)} · ${event.source.label}`,
      x: Math.max(86, Math.min(954, event.x)),
      y: (lane?.y ?? 300) + (stableUnit(`${event.id}:${level}`, "memory-river-marker-y") - 0.5) * 26,
      radius: kind === "black-hole" ? Math.max(6, event.radius + 2) : kind === "proto-star" ? Math.max(5, event.radius + 1) : event.radius,
    };
  });
  const visibleLanes = lanes.length ? lanes : buildEmptyMemoryRiverLanes(levelSpecs, cursorX);
  const evidenceLayers = buildMemoryRiverEvidenceLayers(events, laneLookup, visibleLanes);
  const roiGradient = buildMemoryRiverRoiGradient(events);

  return {
    levels: levelSpecs.map(({ level, note, y }) => ({ level, note, y })),
    lanes: visibleLanes,
    evidenceLayers,
    roiGradient,
    markers,
    levelCounts,
  };
}



export function buildMemoryRiverRoiGradient(events: TimelineDisplayEvent[]): MemoryRiverRoiGradient {
  const bandCount = 12;
  const bandWidth = MEMORY_RIVER_WIDTH / bandCount;
  const bands: MemoryRiverRoiGradientBand[] = [];
  const scoredEvents = events.map((event) => ({
    event,
    roi: event.node?.metrics?.roi?.leverage_score ?? 0,
    capability: isCapabilityGrowthEvent(event),
  }));
  for (let index = 0; index < bandCount; index += 1) {
    const x = MEMORY_RIVER_MIN_X + index * bandWidth;
    const right = x + bandWidth;
    const inBand = scoredEvents.filter(({ event }) => event.x >= x && event.x < right);
    const averageRoi = inBand.length ? inBand.reduce((sum, item) => sum + item.roi, 0) / inBand.length : 0;
    const capabilityCount = inBand.filter((item) => item.capability).length;
    const score = clamp(averageRoi * 0.74 + Math.min(1, capabilityCount / 4) * 0.26, 0, 1);
    bands.push({
      id: `roi-gradient-${index}`,
      x: x + 1,
      y: 112,
      width: Math.max(2, bandWidth - 2),
      height: 402,
      score,
      color: roiGradientColor(score),
      label: `${index + 1}/${bandCount} · ROI ${formatScore(averageRoi)} · capability ${capabilityCount.toLocaleString()}`,
    });
  }
  const averageRoiScore = scoredEvents.length ? scoredEvents.reduce((sum, item) => sum + item.roi, 0) / scoredEvents.length : 0;
  const highLeverageCount = scoredEvents.filter((item) => item.roi >= 0.54).length;
  const capabilityGrowthCount = scoredEvents.filter((item) => item.capability).length;
  return {
    label: `ROI gradient · avg ${formatScore(averageRoiScore)}`,
    signal: `${highLeverageCount.toLocaleString()} high leverage / ${capabilityGrowthCount.toLocaleString()} capability-growth events`,
    averageRoiScore,
    highLeverageCount,
    capabilityGrowthCount,
    bands,
  };
}



export function isCapabilityGrowthEvent(event: TimelineDisplayEvent): boolean {
  const roi = event.node?.metrics?.roi?.leverage_score ?? 0;
  const text = `${event.source.label} ${event.node?.statement ?? ""}`;
  return roi >= 0.54 || event.source.category === "decision" || event.source.category === "project_context" || /机会|增长|下一步|能力|capability|workflow/i.test(text);
}



export function roiGradientColor(score: number): string {
  if (score >= 0.72) return `rgba(126, 232, 212, ${0.11 + score * 0.12})`;
  if (score >= 0.48) return `rgba(143, 211, 255, ${0.09 + score * 0.1})`;
  if (score > 0) return `rgba(199, 167, 255, ${0.07 + score * 0.08})`;
  return "rgba(244, 241, 232, 0.025)";
}



export function buildMemoryRiverEvidenceLayers(
  events: TimelineDisplayEvent[],
  laneLookup: Map<string, MemoryRiverLane>,
  lanes: MemoryRiverLane[],
): MemoryRiverEvidenceLayer[] {
  if (!events.length) return [];
  const latest = events.reduce((max, event) => Math.max(max, timelineUtcMs(event.day)), 0);
  const latestDay = latest > 0 ? new Date(latest) : new Date();
  const recentStart = addDays(latestDay, -29);
  const blackHoleEvents = events.filter(isMemoryRiverBlackHoleEvent);
  const protoStarEvents = events.filter((event) => isMemoryRiverProtoStarEvent(event, recentStart, latestDay));
  const staleEvents = events.filter(isMemoryRiverStaleDeprecatedEvent);
  return [
    buildBlackHoleLifecycleLayer(blackHoleEvents, laneLookup, lanes),
    buildProtoStarLifecycleLayer(protoStarEvents, laneLookup, lanes),
    buildStaleDeprecatedLayer(staleEvents),
  ].filter((layer): layer is MemoryRiverEvidenceLayer => Boolean(layer));
}



export function buildBlackHoleLifecycleLayer(
  events: TimelineDisplayEvent[],
  laneLookup: Map<string, MemoryRiverLane>,
  lanes: MemoryRiverLane[],
): MemoryRiverEvidenceLayer | null {
  const sorted = [...events].sort((a, b) => a.x - b.x);
  if (!sorted.length) return null;
  const range = memoryRiverEvidenceRange(sorted, 46);
  const y = 500;
  const width = Math.max(44, range.endX - range.startX);
  const peak = sorted[Math.max(0, sorted.length - 1)];
  const microLane = laneForMemoryRiverEvent(peak, "Micro", laneLookup, lanes);
  return {
    id: "memory-river-black-hole-lifecycle",
    kind: "black-hole-lifecycle",
    label: `黑洞生命周期 · ${sorted.length}`,
    detail: "与首页风险循环一致：stale / needs_review / deprecated / 临时低权重信号",
    startX: range.startX,
    endX: range.endX,
    labelX: Math.min(900, range.startX + width / 2),
    labelY: y - 12,
    count: sorted.length,
    path: `M ${range.startX} ${y + 28} C ${range.startX + width * 0.28} ${y + 6}, ${range.endX - width * 0.24} ${y + 50}, ${range.endX} ${y + 22}`,
    points: sorted.slice(-6).map((event, index) => ({
      id: `black-hole-point-${event.id}`,
      x: Math.max(MEMORY_RIVER_MIN_X, Math.min(MEMORY_RIVER_MAX_X, event.x)),
      y: (microLane?.y ?? y) + (index % 2 ? 18 : -10),
      radius: Math.max(4.5, Math.min(9, event.radius + 1.5)),
      label: `${event.utcDate} UTC · 黑洞增强 · ${event.source.label}`,
    })),
    segments: [
      {
        id: "black-hole-band",
        x: range.startX,
        y,
        width,
        height: 42,
        label: `低价值循环从 ${sorted[0].utcDate} 到 ${sorted[sorted.length - 1].utcDate} 可见增强`,
        strength: Math.min(1, sorted.length / 8),
      },
    ],
  };
}



export function buildProtoStarLifecycleLayer(
  events: TimelineDisplayEvent[],
  laneLookup: Map<string, MemoryRiverLane>,
  lanes: MemoryRiverLane[],
): MemoryRiverEvidenceLayer | null {
  const sorted = [...events].sort((a, b) => a.x - b.x).slice(-10);
  if (!sorted.length) return null;
  const points = sorted.map((event, index) => {
    const lane = laneForMemoryRiverEvent(event, "Meso", laneLookup, lanes);
    return {
      id: `proto-star-point-${event.id}`,
      x: Math.max(MEMORY_RIVER_MIN_X, Math.min(MEMORY_RIVER_MAX_X, event.x)),
      y: (lane?.y ?? 294) + (index % 2 ? -22 : 20),
      radius: Math.max(4.5, Math.min(8.5, event.radius + 1)),
      label: `${event.utcDate} UTC · 机会成长 · ${event.source.label}`,
    };
  });
  const range = memoryRiverEvidenceRange(sorted, 34);
  return {
    id: "memory-river-proto-star-lifecycle",
    kind: "proto-star-lifecycle",
    label: `机会生命周期 · ${sorted.length}`,
    detail: "decision / project_context / high-leverage / 高重要信号形成增长路径",
    startX: range.startX,
    endX: range.endX,
    labelX: Math.min(900, range.startX + Math.max(48, range.endX - range.startX) / 2),
    labelY: 224,
    count: sorted.length,
    path: memoryRiverEvidencePath(points),
    points,
    segments: [],
  };
}



export function buildStaleDeprecatedLayer(events: TimelineDisplayEvent[]): MemoryRiverEvidenceLayer | null {
  const sorted = [...events].sort((a, b) => a.x - b.x).slice(-18);
  if (!sorted.length) return null;
  const range = memoryRiverEvidenceRange(sorted, 38);
  const segments = sorted.map((event, index) => ({
    id: `stale-fade-${event.id}`,
    x: Math.max(MEMORY_RIVER_MIN_X, Math.min(MEMORY_RIVER_MAX_X - 18, event.x - 9)),
    y: 405 + (index % 3) * 16,
    width: 24 + Math.min(34, event.radius * 3),
    height: 86 - (index % 3) * 10,
    label: `${event.utcDate} UTC · 冷却/废弃 · ${event.source.label}`,
    strength: Math.min(1, 0.35 + index / Math.max(1, sorted.length)),
  }));
  return {
    id: "memory-river-stale-deprecated-layer",
    kind: "stale-deprecated",
    label: `冷却/废弃层 · ${sorted.length}`,
    detail: "stale_short_term / deprecated_info / temporary_or_sensitive 仅作为可读冷却状态显示",
    startX: range.startX,
    endX: range.endX,
    labelX: Math.min(900, range.startX + Math.max(48, range.endX - range.startX) / 2),
    labelY: 392,
    count: sorted.length,
    points: [],
    segments,
  };
}



export function laneForMemoryRiverEvent(
  event: TimelineDisplayEvent,
  level: MemoryRiverLevel,
  laneLookup: Map<string, MemoryRiverLane>,
  lanes: MemoryRiverLane[],
): MemoryRiverLane | undefined {
  const group = memoryRiverGroup(event, level);
  return laneLookup.get(`${level}:${group.key}`) ?? lanes.find((lane) => lane.level === level);
}



export function memoryRiverEvidenceRange(events: TimelineDisplayEvent[], minWidth: number): { startX: number; endX: number } {
  const xs = events.map((event) => Math.max(MEMORY_RIVER_MIN_X, Math.min(MEMORY_RIVER_MAX_X, event.x))).sort((a, b) => a - b);
  const left = xs[0] ?? MEMORY_RIVER_MIN_X;
  const right = xs[xs.length - 1] ?? left;
  const midpoint = (left + right) / 2;
  const half = Math.max(minWidth / 2, (right - left) / 2);
  return {
    startX: Math.max(MEMORY_RIVER_MIN_X, midpoint - half),
    endX: Math.min(MEMORY_RIVER_MAX_X, midpoint + half),
  };
}



export function memoryRiverEvidencePath(points: MemoryRiverEvidencePoint[]): string | undefined {
  if (!points.length) return undefined;
  if (points.length === 1) return `M ${points[0].x - 14} ${points[0].y} C ${points[0].x - 4} ${points[0].y - 18}, ${points[0].x + 10} ${points[0].y + 18}, ${points[0].x + 26} ${points[0].y}`;
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1];
    const current = points[index];
    const midX = previous.x + (current.x - previous.x) / 2;
    path += ` C ${midX} ${previous.y}, ${midX} ${current.y}, ${current.x} ${current.y}`;
  }
  return path;
}



export function isMemoryRiverBlackHoleEvent(event: TimelineDisplayEvent): boolean {
  return memoryRiverMarkerKind(event) === "black-hole" || Boolean(event.node && isBlackHoleCandidate(event.node));
}



export function isMemoryRiverProtoStarEvent(event: TimelineDisplayEvent, recentStart: Date, latest: Date): boolean {
  return memoryRiverMarkerKind(event) === "proto-star" || Boolean(event.node && isProtoStarCandidate(event.node, recentStart, latest));
}



export function isMemoryRiverStaleDeprecatedEvent(event: TimelineDisplayEvent): boolean {
  const stale = event.node?.metrics?.roi?.staleness_status ?? "";
  return (
    stale.includes("stale") ||
    stale === "needs_review" ||
    event.source.category === "deprecated_info" ||
    event.source.category === "temporary_or_sensitive" ||
    normalizeMemoryTier(event.source.memory_tier) === "临时"
  );
}



export function buildEmptyMemoryRiverLanes(levels: Array<MemoryRiverLevelBand & { maxLanes: number }>, cursorX: number): MemoryRiverLane[] {
  return levels.map((level, index) => ({
    id: `river-empty-${level.level.toLowerCase()}`,
    groupKey: "empty",
    level: level.level,
    label: "暂无可渲染事件",
    count: 0,
    path: `M 80 ${level.y} C ${Math.max(120, cursorX - 90)} ${level.y}, ${Math.min(920, cursorX + 90)} ${level.y}, 960 ${level.y}`,
    color: memoryRiverLaneColor("empty", level.level, index),
    gradientId: `memory-river-gradient-empty-${level.level.toLowerCase()}`,
    strokeWidth: 8,
    labelX: 110,
    labelY: level.y - 14,
    y: level.y,
  }));
}



export function memoryRiverGroup(event: TimelineDisplayEvent, level: MemoryRiverLevel): { key: string; label: string } {
  if (level === "Macro") {
    const tier = normalizeMemoryTier(event.source.memory_tier) || "未分层";
    return { key: tier, label: translateTierOrKind(tier) };
  }
  if (level === "Meso") {
    const theme = event.node ? compactThemeLabel(humanThemeLabel(event.node)) || event.node.visual?.cluster || "未归类主题" : "未归类主题";
    return { key: event.node?.visual?.cluster ?? theme, label: theme };
  }
  const category = event.source.category || "unknown";
  return { key: category, label: humanCategoryLabel(category) };
}



export function memoryRiverEventScore(event: TimelineDisplayEvent): number {
  const tier = normalizeMemoryTier(event.source.memory_tier);
  return (
    (event.source.importance === "高" ? 12 : event.source.importance === "中" ? 6 : 2) +
    (event.source.category === "decision" ? 8 : 0) +
    (tier === "核心画像" ? 8 : tier === "一般" ? 4 : 0)
  );
}



export function memoryRiverLaneColor(key: string, level: MemoryRiverLevel, index: number): string {
  if (level === "Macro") return laneColor(key, index);
  const mesoColors = ["#8fd3ff", "#7ee8d4", "#f48fb1", "#6ea8ff", "#c7a7ff"];
  const microColors = ["#f48fb1", "#c7a7ff", "#94a3b8", "#48c7e8", "#7ee8d4"];
  return (level === "Meso" ? mesoColors : microColors)[(index + Math.floor(stableUnit(key, `river-${level}`) * 10)) % (level === "Meso" ? mesoColors.length : microColors.length)];
}



export function buildMemoryRiverPath(events: TimelineDisplayEvent[], baseY: number): string {
  const sorted = [...events].sort((a, b) => a.x - b.x);
  const anchors = [
    { x: 80, y: baseY },
    ...sorted.map((event) => ({
      x: Math.max(80, Math.min(960, event.x)),
      y: baseY + (stableUnit(event.id, "memory-river-wave") - 0.5) * 38,
    })),
    { x: 960, y: baseY },
  ];
  let path = `M ${anchors[0].x} ${anchors[0].y}`;
  for (let index = 1; index < anchors.length; index += 1) {
    const previous = anchors[index - 1];
    const current = anchors[index];
    const midX = previous.x + (current.x - previous.x) / 2;
    path += ` C ${midX} ${previous.y}, ${midX} ${current.y}, ${current.x} ${current.y}`;
  }
  return path;
}



export function memoryRiverMarkerLevel(event: TimelineDisplayEvent): MemoryRiverLevel {
  if (event.source.category === "deprecated_info" || event.source.category === "temporary_or_sensitive") return "Micro";
  if (event.source.category === "decision" || event.source.importance === "高") return "Meso";
  return "Macro";
}



export function memoryRiverMarkerKind(event: TimelineDisplayEvent): MemoryRiverMarker["kind"] {
  const text = `${event.source.label} ${event.node?.statement ?? ""}`;
  if (event.source.category === "deprecated_info" || event.source.category === "temporary_or_sensitive") return "black-hole";
  if (event.source.category === "decision" || event.source.importance === "高" || /机会|增长|突破|下一步|opportunity|next/i.test(text)) return "proto-star";
  return "memory-event";
}



export function buildTimelineDensityBands(
  events: Array<{ day: Date }>,
  minDay: Date,
  maxDay: Date,
  windowStartMs: number,
  windowEndMs: number,
) {
  const count = 48;
  const minMs = timelineUtcMs(minDay);
  const maxMs = timelineUtcMs(maxDay);
  const totalSpan = Math.max(1, maxMs - minMs);
  const bins = Array.from({ length: count }, (_unused, index) => ({
    key: `density-${index}`,
    count: 0,
    center: (index + 0.5) / count,
    label: "",
    intensity: 0,
    active: false,
  }));
  for (const event of events) {
    const ratio = Math.min(0.999, Math.max(0, (timelineUtcMs(event.day) - minMs) / totalSpan));
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



export function buildTimelineDensityBackdrops(
  events: Array<{ day: Date }>,
  minDay: Date,
  maxDay: Date,
) {
  const count = 36;
  const minMs = timelineUtcMs(minDay);
  const span = Math.max(1, timelineUtcMs(maxDay) - minMs);
  const bins = Array.from({ length: count }, (_unused, index) => ({ key: `timeline-band-${index}`, count: 0 }));
  for (const event of events) {
    const ratio = Math.min(0.999, Math.max(0, (timelineUtcMs(event.day) - minMs) / span));
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
