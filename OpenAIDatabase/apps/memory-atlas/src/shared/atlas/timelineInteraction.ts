import type { PointerEvent } from "react";
import { normalizeMemoryTier, uniqueSorted } from "../../data/atlas";
import type { AtlasNode } from "../../types";
import { TimelineBrushDraft, TimelineEvent, TimelineFeedbackSettings, TimelineLayoutControls, TimelineTimeRangeSelection } from "./contracts";
import { buildEventDateTicks, buildMonthTicks, formatAxisDate, laneColor, nodeColor } from "./contributionModels";
import { stableHash } from "./inspectorWriteback";
import { buildTimelineDensityBackdrops, buildTimelineDensityBands } from "./memoryRiverModels";
import { MEMORY_RIVER_MAX_X, MEMORY_RIVER_MIN_X, MEMORY_RIVER_WIDTH, TIMELINE_FEEDBACK_SETTINGS_KEY } from "./runtimeConfig";
import { compactThemeLabel, countBy, humanThemeLabel, topRows } from "./semanticHuman";
import { parseTimelineUtcDay, timelineUtcMs, toDayKey, translateTierOrKind, truncate } from "./utils";



export function buildTimelineLayout(timeline: TimelineEvent[], nodeMap: Map<string, AtlasNode>, controls: TimelineLayoutControls) {
  const allEvents = timeline
    .map((event) => ({ source: event, day: parseTimelineUtcDay(event.date), node: nodeMap.get(event.node_id) }))
    .filter((event): event is { source: TimelineEvent; day: Date; node: AtlasNode | undefined } => Boolean(event.day))
    .sort((a, b) => timelineUtcMs(a.day) - timelineUtcMs(b.day));
  const minAllDay = allEvents[0]?.day ?? new Date();
  const maxAllDay = allEvents[allEvents.length - 1]?.day ?? minAllDay;
  const minAllMs = timelineUtcMs(minAllDay);
  const maxAllMs = timelineUtcMs(maxAllDay);
  const totalSpan = Math.max(1, maxAllMs - minAllMs);
  const zoom = Math.min(8, Math.max(1, controls.zoom || 1));
  const visibleSpan = Math.max(1, totalSpan / zoom);
  const rawCenter = minAllMs + totalSpan * Math.min(1, Math.max(0, controls.center));
  const minWindow = minAllMs;
  const maxWindow = maxAllMs;
  const unclampedStart = rawCenter - visibleSpan / 2;
  const windowStartMs = Math.max(minWindow, Math.min(Math.max(minWindow, maxWindow - visibleSpan), unclampedStart));
  const windowEndMs = Math.min(maxWindow, windowStartMs + visibleSpan);
  const minDay = new Date(windowStartMs);
  const maxDay = new Date(windowEndMs);
  const span = Math.max(1, windowEndMs - windowStartMs);
  const cursor = Math.min(1, Math.max(0, controls.cursor));
  const cursorMs = windowStartMs + span * cursor;
  const visibleEvents = allEvents
    .filter((event) => timelineUtcMs(event.day) >= windowStartMs && timelineUtcMs(event.day) <= windowEndMs)
    .slice(-260);
  const laneKeys = uniqueSorted(visibleEvents.map((event) => normalizeMemoryTier(event.source.memory_tier) || event.source.category)).slice(0, 7);
  const lanes = laneKeys.map((key, index) => ({
    key,
    label: translateTierOrKind(key),
    y: 95 + index * (410 / Math.max(laneKeys.length - 1, 1)),
    color: laneColor(key, index),
  }));
  const laneMap = new Map(lanes.map((lane) => [lane.key, lane]));
  const ticks = buildMonthTicks(minDay, maxDay, MEMORY_RIVER_MIN_X, MEMORY_RIVER_MAX_X);
  const eventTicks = buildEventDateTicks(visibleEvents, minDay, maxDay, MEMORY_RIVER_MIN_X, MEMORY_RIVER_MAX_X);
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
    cursorX: MEMORY_RIVER_MIN_X + cursor * MEMORY_RIVER_WIDTH,
    windowStartMs,
    windowEndMs,
    totalCount: allEvents.length,
    visibleCount: visibleEvents.length,
    importantCount,
    coreCount,
    peakDensity: Math.max(0, ...densityBands.map((band) => band.count)),
    events: visibleEvents.map((event, index) => {
      const lane = laneMap.get(normalizeMemoryTier(event.source.memory_tier) || event.source.category) ?? lanes[index % Math.max(lanes.length, 1)];
      const eventMs = timelineUtcMs(event.day);
      const x = MEMORY_RIVER_MIN_X + ((eventMs - timelineUtcMs(minDay)) / span) * MEMORY_RIVER_WIDTH;
      const major = event.source.importance === "高" || event.source.category === "decision" || index % 11 === 0;
      return {
        id: `${event.source.date}-${event.source.node_id}-${event.source.memory_id || index}`,
        source: event.source,
        node: event.node,
        day: event.day,
        utcDate: toDayKey(event.day),
        x,
        y: lane?.y ?? 300,
        radius: event.source.importance === "高" ? 9 : event.source.category === "decision" ? 8 : 5,
        color: event.node ? nodeColor(event.node) : lane?.color ?? "#94a3b8",
        major,
        future: eventMs > cursorMs,
        shortLabel: truncate(event.source.label, 18),
      };
    }),
  };
}



export function getInitialTimelineFeedbackSettings(): TimelineFeedbackSettings {
  const reducedMotion = typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const defaults: TimelineFeedbackSettings = { reducedMotion: Boolean(reducedMotion), pseudoHaptic: false, audio: false };
  if (typeof window === "undefined") return defaults;
  try {
    const stored = window.localStorage.getItem(TIMELINE_FEEDBACK_SETTINGS_KEY);
    if (!stored) return defaults;
    const parsed = JSON.parse(stored) as Partial<TimelineFeedbackSettings>;
    return {
      reducedMotion: Boolean(parsed.reducedMotion ?? defaults.reducedMotion),
      pseudoHaptic: Boolean(parsed.pseudoHaptic),
      audio: Boolean(parsed.audio),
    };
  } catch {
    return defaults;
  }
}



export function persistTimelineFeedbackSettings(settings: TimelineFeedbackSettings): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(TIMELINE_FEEDBACK_SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    // Preference persistence is best-effort for locked-down local previews.
  }
}



export function timelineRangeSummary(range: TimelineTimeRangeSelection | null): string | null {
  if (!range) return null;
  return `时间河选择 ${range.label} · ${range.eventCount.toLocaleString()} 事件 · ${range.topTheme}`;
}



export function memoryRiverPointerX(event: PointerEvent<SVGSVGElement>): number {
  const rect = event.currentTarget.getBoundingClientRect();
  const ratio = rect.width > 0 ? (event.clientX - rect.left) / rect.width : 0;
  return clampMemoryRiverX(ratio * 1000);
}



export function clampMemoryRiverX(value: number): number {
  return Math.min(MEMORY_RIVER_MAX_X, Math.max(MEMORY_RIVER_MIN_X, value));
}



export function memoryRiverXToRatio(x: number): number {
  return Math.min(1, Math.max(0, (clampMemoryRiverX(x) - MEMORY_RIVER_MIN_X) / MEMORY_RIVER_WIDTH));
}



export function memoryRiverDateAtX(display: ReturnType<typeof buildTimelineLayout>, x: number): Date {
  const ratio = memoryRiverXToRatio(x);
  return new Date(display.windowStartMs + (display.windowEndMs - display.windowStartMs) * ratio);
}



export function memoryRiverXForUtcMs(display: ReturnType<typeof buildTimelineLayout>, utcMs: number): number {
  const span = Math.max(1, display.windowEndMs - display.windowStartMs);
  return MEMORY_RIVER_MIN_X + ((utcMs - display.windowStartMs) / span) * MEMORY_RIVER_WIDTH;
}



export function buildTimelineRangeSelection(
  display: ReturnType<typeof buildTimelineLayout>,
  startX: number,
  endX: number,
): TimelineTimeRangeSelection | null {
  const left = clampMemoryRiverX(Math.min(startX, endX));
  const right = clampMemoryRiverX(Math.max(startX, endX));
  if (right - left < 14) return null;
  const startDate = memoryRiverDateAtX(display, left);
  const endDate = memoryRiverDateAtX(display, right);
  const startKey = toDayKey(startDate);
  const endKey = toDayKey(endDate);
  const events = display.events.filter((event) => event.utcDate >= startKey && event.utcDate <= endKey);
  const topTheme = topRows(countBy(events, (event) => event.node ? compactThemeLabel(humanThemeLabel(event.node)) || "未归类主题" : "未归类主题"), 1)[0]?.label ?? "暂无主题";
  return {
    id: `memory-river-brush-${startKey}-${endKey}-${stableHash(`${startKey}:${endKey}:${events.length}`)}`,
    source: "memory-river-brush",
    startDate: startKey,
    endDate: endKey,
    label: `${formatAxisDate(startDate)} - ${formatAxisDate(endDate)}`,
    eventCount: events.length,
    decisionCount: events.filter((event) => event.source.category === "decision").length,
    coreMemoryCount: events.filter((event) => normalizeMemoryTier(event.source.memory_tier) === "核心画像").length,
    topTheme,
  };
}



export function buildMemoryRiverRangeOverlay(range: TimelineTimeRangeSelection | null, display: ReturnType<typeof buildTimelineLayout>) {
  if (!range) return null;
  const startDay = parseTimelineUtcDay(range.startDate);
  const endDay = parseTimelineUtcDay(range.endDate);
  if (!startDay || !endDay) return null;
  const startX = memoryRiverXForUtcMs(display, timelineUtcMs(startDay));
  const endX = memoryRiverXForUtcMs(display, timelineUtcMs(endDay));
  if (endX < MEMORY_RIVER_MIN_X || startX > MEMORY_RIVER_MAX_X) return null;
  const x = clampMemoryRiverX(Math.min(startX, endX));
  const right = clampMemoryRiverX(Math.max(startX, endX));
  const width = Math.max(3, right - x);
  return { x, width, labelX: x + width / 2, label: `${range.label} · ${range.eventCount}` };
}



export function buildMemoryRiverDraftOverlay(draft: TimelineBrushDraft) {
  const x = clampMemoryRiverX(Math.min(draft.startX, draft.endX));
  const right = clampMemoryRiverX(Math.max(draft.startX, draft.endX));
  return { x, width: Math.max(3, right - x) };
}



export function emitTimelineFeedback(settings: TimelineFeedbackSettings, kind: "pan" | "brush" | "event"): void {
  if (settings.reducedMotion) return;
  if (settings.pseudoHaptic && typeof navigator !== "undefined" && navigator.vibrate) {
    navigator.vibrate(kind === "brush" ? [8, 24, 8] : 10);
  }
  if (!settings.audio || typeof window === "undefined" || typeof window.AudioContext === "undefined") return;
  try {
    const context = new window.AudioContext();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.frequency.value = kind === "event" ? 660 : kind === "brush" ? 520 : 390;
    gain.gain.value = 0.018;
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start();
    window.setTimeout(() => {
      oscillator.stop();
      void context.close();
    }, 55);
  } catch {
    // Optional audio feedback must never break the visualization.
  }
}
