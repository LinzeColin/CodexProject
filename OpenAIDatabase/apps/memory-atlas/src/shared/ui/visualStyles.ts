import type { CSSProperties } from "react";
import type { AtlasFilters } from "../../types";
import { FilterKey, PeriodCounts, SourceOption, TrendSlot } from "../atlas/contracts";
import { maxActivityScore } from "../atlas/contributionModels";
import { emptyHeatColor } from "../atlas/runtimeConfig";
import { heatColorForScore, heatIntensityForScore, humanCategoryLabel, interpolateHeatColor, themeLabelFromCluster, withAlpha } from "../atlas/semanticHuman";



export function activeFilterChips(filters: AtlasFilters, sourceOptions: SourceOption[]): Array<{ key: FilterKey; label: string; value: string }> {
  const chips: Array<{ key: FilterKey; label: string; value: string }> = [];
  if (filters.source !== "all") chips.push({ key: "source", label: "对象", value: sourceOptions.find((source) => source.id === filters.source)?.label ?? filters.source });
  if (filters.query.trim()) chips.push({ key: "query", label: "搜索", value: filters.query.trim() });
  if (filters.tier !== "all") chips.push({ key: "tier", label: "层级", value: filters.tier });
  if (filters.category !== "all") chips.push({ key: "category", label: "分类", value: humanCategoryLabel(filters.category) });
  if (filters.theme !== "all") chips.push({ key: "theme", label: "主题", value: themeLabelFromCluster(filters.theme) });
  return chips;
}



export function trendGradient(slots: TrendSlot[], direction: "90deg" | "180deg", maxScore = maxActivityScore(slots)) {
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



export function trendIntensity(slot: TrendSlot, maxScore: number) {
  if (!slot) return 0;
  const score = Number(slot.activityScore ?? 0);
  if (score <= 0 && slot.activityLevel <= 0) return 0;
  return heatIntensityForScore(score, maxScore, slot.activityLevel);
}



export function smoothTrendIntensities(values: number[]) {
  if (!values.some((value) => value > 0)) return values;
  return values.map((value, index) => {
    const previous = values[index - 1] ?? value;
    const next = values[index + 1] ?? value;
    const interpolated = previous * 0.2 + value * 0.6 + next * 0.2;
    return Math.min(1, Math.max(interpolated, value * 0.72));
  });
}



export function fluidTrendIntensities(values: number[]) {
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



export function smoothStep(value: number) {
  const t = clamp(value, 0, 1);
  return t * t * (3 - 2 * t);
}



export function catmullRom(p0: number, p1: number, p2: number, p3: number, t: number) {
  const t2 = t * t;
  const t3 = t2 * t;
  return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3);
}



export function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}



export function trendColorFromIntensity(value: number) {
  return value <= 0 ? emptyHeatColor : interpolateHeatColor(value);
}



export function trendColor(slotOrLevel: TrendSlot | number, maxScore = 0) {
  if (slotOrLevel === null) return "rgba(9, 10, 13, 0.44)";
  const score = typeof slotOrLevel === "number" ? 0 : Number(slotOrLevel.activityScore ?? 0);
  const level = typeof slotOrLevel === "number" ? slotOrLevel : slotOrLevel.activityLevel;
  if (score <= 0 && level <= 0) return emptyHeatColor;
  return heatColorForScore(score, maxScore, level);
}



export function trendSegmentStyle(slot: TrendSlot, maxScore: number): CSSProperties {
  const base = !slot
    ? heatCellStyle({ activityScore: 0, activityLevel: 0 }, maxScore)
    : heatCellStyle({ activityScore: Number(slot.activityScore ?? 0), activityLevel: slot.activityLevel }, maxScore);
  return {
    ...base,
    "--segment-color": trendColor(slot, maxScore),
  } as CSSProperties;
}


export function heatCellStyle(bucket: Pick<PeriodCounts, "activityScore" | "activityLevel">, maxScore: number): CSSProperties {
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



export function yearCellStyle(bucket: Pick<PeriodCounts, "activityScore" | "activityLevel">, maxScore: number): CSSProperties {
  return {
    ...heatCellStyle(bucket, maxScore),
    "--year-accent": heatColorForScore(bucket.activityScore, maxScore, bucket.activityLevel),
  } as CSSProperties;
}



export function monthBarStyle(slot: Pick<PeriodCounts, "activityScore" | "activityLevel">, slots: Array<Pick<PeriodCounts, "activityScore">>): CSSProperties {
  const maxScore = maxActivityScore(slots);
  const score = Math.max(0, slot.activityScore);
  const ratio = maxScore > 0 ? score / maxScore : 0;
  const height = score > 0 ? Math.round(24 + Math.sqrt(ratio) * 76) : 9;
  return {
    "--month-color": trendColor(slot, maxScore),
    "--month-height": `${height}%`,
  } as CSSProperties;
}
