import type { KeyboardEvent } from "react";
import { normalizeMemoryTier } from "../../data/atlas";
import type { AtlasEdge, AtlasNode, MemoryAtlas } from "../../types";
import { DeltaStats } from "./contracts";



export function parseTimelineUtcDay(value: string | undefined): Date | null {
  return parseDay(value);
}



export function timelineUtcMs(day: Date): number {
  return Date.UTC(day.getUTCFullYear(), day.getUTCMonth(), day.getUTCDate());
}



export function translateKind(kind: AtlasNode["kind"]): string {
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



export function translateTierOrKind(value: string): string {
  if (value === "decision") return "决策";
  if (value === "project") return "项目";
  if (value === "timeline_event") return "时间事件";
  return value;
}



export function translateAction(value: string | undefined): string {
  return {
    keep_high_weight: "高权重保留",
    review_for_project_linkage: "复查项目连接",
    keep_low_weight_or_refresh: "低权重保留或刷新",
    keep_as_context: "作为上下文保留",
  }[value ?? ""] ?? "作为上下文保留";
}



export function translateStaleness(value: string | undefined): string {
  return {
    stale_short_term: "临时信息已旧",
    needs_review: "需要复查",
    current: "当前有效",
    unknown: "未知时效",
  }[value ?? ""] ?? "未知时效";
}



export function formatScore(value: number | undefined | null): string {
  return typeof value === "number" ? value.toFixed(2) : "n/a";
}



export function formatSigned(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toLocaleString()}`;
}



export function sumValues(values: Record<string, number>, keys: string[]): number {
  return keys.reduce((sum, key) => sum + (values[key] ?? 0), 0);
}



export function parseDay(value: string | undefined): Date | null {
  if (!value) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (!match) return null;
  return new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
}



export function maxNodeDate(nodes: AtlasNode[]): Date | null {
  return nodes.reduce<Date | null>((latest, node) => {
    const day = parseDay(node.date);
    if (!day) return latest;
    if (!latest || day > latest) return day;
    return latest;
  }, null);
}



export function isNodeBetween(node: AtlasNode, start: Date, end: Date): boolean {
  const day = parseDay(node.date);
  return Boolean(day && day >= start && day <= end);
}



export function addDays(day: Date, count: number): Date {
  const next = new Date(day.getTime());
  next.setUTCDate(next.getUTCDate() + count);
  return next;
}



export function contributionYears(atlas: MemoryAtlas, nodes: AtlasNode[]): number[] {
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



export function buildIterationHighlights(nodes: AtlasNode[], deltaStats: DeltaStats) {
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



export function formatUpdatedAt(value: string | undefined): string {
  if (!value) return "待同步";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
}



export function toDayKey(day: Date): string {
  return `${day.getUTCFullYear()}-${String(day.getUTCMonth() + 1).padStart(2, "0")}-${String(day.getUTCDate()).padStart(2, "0")}`;
}



export function formatChineseDate(day: Date): string {
  return `${day.getUTCFullYear()} 年 ${day.getUTCMonth() + 1} 月 ${day.getUTCDate()} 日`;
}



export function mondayWeekdayIndex(day: Date): number {
  return (day.getUTCDay() + 6) % 7;
}



export function dayOfYearIndex(day: Date): number {
  const start = new Date(Date.UTC(day.getUTCFullYear(), 0, 1));
  return Math.floor((day.getTime() - start.getTime()) / 86400000);
}



export function calendarWeekKey(year: number, weekColumn: number): string {
  return `${year}-CW${String(weekColumn + 1).padStart(2, "0")}`;
}



export function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}



export function stableUnit(value: string, salt: string): number {
  let hash = 2166136261;
  const input = `${salt}:${value}`;
  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return (hash % 1000000) / 1000000;
}



export function truncate(value: string, length: number): string {
  const text = value.replace(/\s+/g, " ").trim();
  return text.length > length ? `${text.slice(0, Math.max(0, length - 1))}…` : text;
}



export function isActivationKey(event: KeyboardEvent): boolean {
  return event.key === "Enter" || event.key === " ";
}



export function edgeCountFor(nodeId: string | undefined, edges: AtlasEdge[]): number {
  if (!nodeId) return 0;
  return edges.reduce((count, edge) => count + (edge.source === nodeId || edge.target === nodeId ? 1 : 0), 0);
}
