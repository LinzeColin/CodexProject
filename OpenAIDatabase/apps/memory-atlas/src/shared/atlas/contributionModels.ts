import { normalizeMemoryTier } from "../../data/atlas";
import type { ActivityBucket, AtlasEdge, AtlasFilters, AtlasNode, MemoryAtlas } from "../../types";
import { ContributionPeriodDetail, ContributionScale, PeriodCounts, TimelineEvent } from "./contracts";
import { addDays, calendarWeekKey, dayOfYearIndex, formatChineseDate, isLeapYear, mondayWeekdayIndex, parseDay, stableUnit, timelineUtcMs, toDayKey, truncate } from "./utils";



export function buildContributionPeriods(atlas: MemoryAtlas, nodes: AtlasNode[], filters: AtlasFilters, selectedYear: number) {
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



export function buildMonthDaySlots(
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



export function maxActivityScore(items: Array<{ activityScore?: number } | null>) {
  return Math.max(0, ...items.map((item) => Number(item?.activityScore ?? 0)));
}



export function buildContributionPeriodDetail(
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



export function nodeMatchesContributionPeriod(node: AtlasNode, scale: ContributionScale, periodKey: string): boolean {
  const day = parseDay(node.date);
  if (!day) return false;
  if (scale === "day") return toDayKey(day) === periodKey;
  if (scale === "month") return `${day.getUTCFullYear()}-${String(day.getUTCMonth() + 1).padStart(2, "0")}` === periodKey;
  if (scale === "year") return String(day.getUTCFullYear()) === periodKey;
  const year = day.getUTCFullYear();
  const startWeekday = mondayWeekdayIndex(new Date(Date.UTC(year, 0, 1)));
  return calendarWeekKey(year, Math.floor((dayOfYearIndex(day) + startWeekday) / 7)) === periodKey;
}



export function periodMeaningLine(bucket: PeriodCounts, scale: ContributionScale): string {
  const label = scale === "day" ? "这一天" : scale === "week" ? "这一周" : scale === "month" ? "这个月" : "这一年";
  if (bucket.activityScore <= 0) return `${label}没有明显活动，适合作为低使用或空窗期参考。`;
  if (bucket.filteredCoreCount > 0) return `${label}出现核心画像增量，说明有会影响长期 personalization 或 agent 默认行为的信息。`;
  if (bucket.filteredDecisionCount > 0) return `${label}出现新的决策记录，后续项目和 agent 执行应默认继承这些选择。`;
  if (bucket.filteredMemoryCount > 0) return `${label}沉淀了新的记忆内容，适合检查是否已经转成可执行待办或可复用上下文。`;
  return `${label}主要体现交互强度变化，具体记忆增量较少，适合用于使用行为复盘。`;
}



export function periodImpactLine(bucket: PeriodCounts, relatedNodeCount: number): string {
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



export function defaultPeriodKeyForScale(
  scale: ContributionScale,
  periodData: ReturnType<typeof buildContributionPeriods>,
): string {
  if (scale === "day") return periodData.latestDayKey;
  if (scale === "week") return periodData.latestWeekKey;
  if (scale === "month") return periodData.latestMonthKey;
  return periodData.latestYearKey;
}



export function aggregateFilteredNodes(nodes: AtlasNode[], period: "day" | "month") {
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



export function mergePeriodCounts(
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



export function aggregateCells<T extends PeriodCounts>(cells: T[], getKey: (cell: T) => string, getLabel: (cell: T) => string) {
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



export function withDelta(current: PeriodCounts, previous?: PeriodCounts): PeriodCounts & { delta: number; previousLabel: string } {
  return {
    ...current,
    delta: current.activityScore - (previous?.activityScore ?? 0),
    previousLabel: previous?.label ?? "上一周期",
  };
}



export function degreeMap(edges: AtlasEdge[]): Map<string, number> {
  const counts = new Map<string, number>();
  for (const edge of edges) {
    counts.set(edge.source, (counts.get(edge.source) ?? 0) + 1);
    counts.set(edge.target, (counts.get(edge.target) ?? 0) + 1);
  }
  return counts;
}



export function expandGraphIds(rootId: string, edges: AtlasEdge[], depth: number): Set<string> {
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



export function buildMonthTicks(minDay: Date, maxDay: Date, minX: number, maxX: number) {
  const ticks: Array<{ label: string; x: number }> = [];
  const start = new Date(Date.UTC(minDay.getUTCFullYear(), minDay.getUTCMonth(), 1));
  const end = new Date(Date.UTC(maxDay.getUTCFullYear(), maxDay.getUTCMonth(), 1));
  const minMs = timelineUtcMs(minDay);
  const span = Math.max(1, timelineUtcMs(maxDay) - minMs);
  let cursor = start;
  while (cursor <= end) {
    const x = minX + ((timelineUtcMs(cursor) - minMs) / span) * (maxX - minX);
    ticks.push({ label: `${cursor.getUTCFullYear()}.${cursor.getUTCMonth() + 1}`, x });
    cursor = new Date(Date.UTC(cursor.getUTCFullYear(), cursor.getUTCMonth() + 1, 1));
  }
  return ticks.filter((_, index) => index % Math.max(1, Math.ceil(ticks.length / 8)) === 0);
}



export function buildEventDateTicks(
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
  const all = Array.from(grouped.values()).sort((a, b) => timelineUtcMs(a.day) - timelineUtcMs(b.day));
  if (all.length <= 12) return all.map((tick, index) => eventDateTick(tick, index, minDay, maxDay, minX, maxX));
  const selected = new Map<string, (typeof all)[number]>();
  selected.set(all[0].date, all[0]);
  selected.set(all[all.length - 1].date, all[all.length - 1]);
  const minMs = timelineUtcMs(minDay);
  const span = Math.max(1, timelineUtcMs(maxDay) - minMs);
  const xFor = (day: Date) => minX + ((timelineUtcMs(day) - minMs) / span) * (maxX - minX);
  const ranked = [...all].sort((a, b) => b.count * 3 + b.score - (a.count * 3 + a.score));
  for (const candidate of ranked) {
    if (selected.size >= 12) break;
    const candidateX = xFor(candidate.day);
    const hasSpace = Array.from(selected.values()).every((tick) => Math.abs(candidateX - xFor(tick.day)) >= 62);
    if (hasSpace) selected.set(candidate.date, candidate);
  }
  return Array.from(selected.values())
    .sort((a, b) => timelineUtcMs(a.day) - timelineUtcMs(b.day))
    .map((tick, index) => eventDateTick(tick, index, minDay, maxDay, minX, maxX));
}



export function eventDateTick(
  tick: { date: string; day: Date; count: number },
  index: number,
  minDay: Date,
  maxDay: Date,
  minX: number,
  maxX: number,
) {
  const minMs = timelineUtcMs(minDay);
  const span = Math.max(1, timelineUtcMs(maxDay) - minMs);
  return {
    date: tick.date,
    label: formatAxisDate(tick.day),
    x: minX + ((timelineUtcMs(tick.day) - minMs) / span) * (maxX - minX),
    count: tick.count,
    stagger: index % 2,
  };
}



export function formatAxisDate(day: Date) {
  return `${day.getUTCFullYear()}.${day.getUTCMonth() + 1}.${day.getUTCDate()}`;
}



export function filteredMetricValues(nodes: AtlasNode[], key: "memory_tier" | "category"): Record<string, number> {
  return nodes.reduce<Record<string, number>>((acc, node) => {
    const value = key === "memory_tier" ? normalizeMemoryTier(node.memory_tier) : node[key] || "unknown";
    acc[value] = (acc[value] ?? 0) + 1;
    return acc;
  }, {});
}



export function topEntry(values: Record<string, number>): [string, number] | undefined {
  return Object.entries(values).sort((a, b) => b[1] - a[1])[0];
}



export function nodeRadius(node: AtlasNode, degree: number): number {
  const base = node.kind === "theme" ? 18 : node.kind === "project" ? 15 : node.kind === "decision" ? 13 : 8;
  return Math.min(28, base + Math.sqrt(Math.max(0, degree)) * 1.6 + (node.metrics?.roi?.leverage_score ?? 0) * 4);
}



export function nodeColor(node: AtlasNode): string {
  if (node.kind === "decision") return "#f48fb1";
  if (node.kind === "project") return "#8fd3ff";
  const tier = normalizeMemoryTier(node.memory_tier);
  if (tier === "核心画像") return "#7ee8d4";
  if (tier === "一般") return node.visual?.color ?? "#8fd3ff";
  return node.visual?.color ?? "#94a3b8";
}



export function isGraphParentNode(node: AtlasNode): boolean {
  return node.kind === "theme" || node.kind === "project" || node.kind === "category" || node.kind === "tier";
}



export function clusterIndex(node: AtlasNode): number {
  return Math.floor(stableUnit(node.visual?.cluster ?? node.category ?? node.id, "cluster") * 12);
}



export function kindRank(kind: AtlasNode["kind"]): number {
  return { theme: 0, project: 1, decision: 2, memory: 3, category: 4, tier: 5, timeline_event: 6 }[kind] ?? 9;
}



export function kindLabelSign(kind: AtlasNode["kind"]): string {
  return { theme: "主题", project: "项目", decision: "决策", memory: "记忆", category: "分类", tier: "层级", timeline_event: "事件" }[kind] ?? "节点";
}



export function shortNodeLabel(node: AtlasNode, length: number): string {
  return truncate(node.kind === "memory" ? node.label : `${kindLabelSign(node.kind)} · ${node.label}`, length);
}



export function laneColor(key: string, index: number): string {
  const colors = ["#7ee8d4", "#8fd3ff", "#48c7e8", "#f48fb1", "#c7a7ff", "#6ea8ff", "#94a3b8"];
  if (key === "核心画像") return "#7ee8d4";
  if (key === "一般") return "#8fd3ff";
  if (key === "decision") return "#f48fb1";
  return colors[index % colors.length];
}



export function blankBucket(dateKey: string): ActivityBucket {
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



export function levelFromScore(score: number): number {
  if (score <= 0) return 0;
  if (score < 8) return 1;
  if (score < 24) return 2;
  if (score < 64) return 3;
  if (score < 160) return 4;
  return 5;
}



export function contributionTitle(bucket: PeriodCounts) {
  return `${bucket.label}: 活动分 ${bucket.activityScore}; 全局对话 ${bucket.conversationCount}; 全局消息 ${bucket.messageCount}; 工具调用 ${bucket.toolCallCount ?? 0}; 错误事件 ${bucket.errorEventCount ?? 0}; 中断 ${bucket.abortCount ?? 0}; 筛选记忆 ${bucket.filteredMemoryCount}; 筛选决策 ${bucket.filteredDecisionCount}`;
}



export function scaleLabel(scale: ContributionScale): string {
  return { day: "日", week: "周", month: "月", year: "年" }[scale];
}
