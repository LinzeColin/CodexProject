import type { FormulaWhatIfPreview, VisualFacetEvent } from "./types.ts";


export type VisualTimeFilter = "all" | "30d" | "90d" | "365d";

export interface VisualWorkflowFilters {
  source: string;
  time: VisualTimeFilter;
  project: string;
  task: string;
}

export interface VisualWorkflowOptions {
  sources: string[];
  projects: string[];
  tasks: string[];
  times: Array<{ id: VisualTimeFilter; label: string }>;
}

export type FormulaWeightKey =
  | "time_saved_weight"
  | "reuse_value_weight"
  | "opportunity_value_weight"
  | "skill_compounding_weight"
  | "automation_alignment_weight"
  | "rework_cost_weight"
  | "low_value_loop_penalty_weight";

export type FormulaWeights = Record<FormulaWeightKey, number>;

export interface FormulaWhatIfResult {
  score: number;
  delta: number;
  positiveScore: number;
  reworkPenalty: number;
  weights: FormulaWeights;
}

const DAY_MS = 24 * 60 * 60 * 1000;
const TIME_WINDOW_DAYS: Record<Exclude<VisualTimeFilter, "all">, number> = {
  "30d": 30,
  "90d": 90,
  "365d": 365,
};
const TIME_OPTIONS: VisualWorkflowOptions["times"] = [
  { id: "all", label: "全部时间" },
  { id: "30d", label: "近 30 天" },
  { id: "90d", label: "近 90 天" },
  { id: "365d", label: "近 1 年" },
];
const FORMULA_WEIGHT_KEYS: FormulaWeightKey[] = [
  "time_saved_weight",
  "reuse_value_weight",
  "opportunity_value_weight",
  "skill_compounding_weight",
  "automation_alignment_weight",
  "rework_cost_weight",
  "low_value_loop_penalty_weight",
];
const POSITIVE_SIGNAL_KEYS: Array<{ weight: FormulaWeightKey; signal: keyof FormulaWhatIfPreview["baseline_signals"] }> = [
  { weight: "time_saved_weight", signal: "time_saved_proxy" },
  { weight: "reuse_value_weight", signal: "reuse_value_proxy" },
  { weight: "opportunity_value_weight", signal: "opportunity_score_proxy" },
  { weight: "skill_compounding_weight", signal: "skill_compounding_proxy" },
  { weight: "automation_alignment_weight", signal: "automation_enhancement_ratio_proxy" },
];

export function buildVisualWorkflowOptions(events: VisualFacetEvent[]): VisualWorkflowOptions {
  return {
    sources: uniqueSorted(events.map((event) => event.source_id)),
    projects: uniqueSorted(events.map((event) => event.project)),
    tasks: uniqueSorted(events.map((event) => event.task_type)),
    times: TIME_OPTIONS.map((option) => ({ ...option })),
  };
}

export function filterVisualFacetEvents(
  events: VisualFacetEvent[],
  filters: VisualWorkflowFilters,
): VisualFacetEvent[] {
  const latestTimestamp = latestValidTimestamp(events);
  const minimumTimestamp = filters.time === "all" || latestTimestamp === null
    ? null
    : latestTimestamp - TIME_WINDOW_DAYS[filters.time] * DAY_MS;

  return events.filter((event) => {
    if (filters.source !== "all" && event.source_id !== filters.source) return false;
    if (filters.project !== "all" && event.project !== filters.project) return false;
    if (filters.task !== "all" && event.task_type !== filters.task) return false;
    if (filters.time === "all") return true;
    const timestamp = parseTimestamp(event.occurred_at);
    if (timestamp === null || latestTimestamp === null || minimumTimestamp === null) return false;
    return timestamp >= minimumTimestamp && timestamp <= latestTimestamp;
  });
}

export function buildVisualFilterSignature(
  events: VisualFacetEvent[],
  filters: VisualWorkflowFilters,
): string {
  const ids = filterVisualFacetEvents(events, filters)
    .map((event) => event.event_id)
    .sort((left, right) => left.localeCompare(right, "zh-CN"));
  return [filters.source, filters.time, filters.project, filters.task, String(ids.length), ...ids].join("|");
}

export function computeFormulaWhatIfScore(
  preview: FormulaWhatIfPreview,
  requestedWeights: Partial<FormulaWeights>,
): FormulaWhatIfResult {
  const weights = Object.fromEntries(
    FORMULA_WEIGHT_KEYS.map((key) => {
      const fallback = finiteNumber(preview.default_weights[key], 1);
      const requested = finiteNumber(requestedWeights[key], fallback);
      const bounds = preview.adjustable_weight_bounds[key];
      return [key, clamp(requested, finiteNumber(bounds?.min, 0.25), finiteNumber(bounds?.max, 2))];
    }),
  ) as FormulaWeights;

  let weightedTotal = 0;
  let positiveWeightTotal = 0;
  for (const mapping of POSITIVE_SIGNAL_KEYS) {
    const weight = weights[mapping.weight];
    weightedTotal += finiteNumber(preview.baseline_signals[mapping.signal], 0) * weight;
    positiveWeightTotal += weight;
  }
  const positiveScore = positiveWeightTotal > 0 ? weightedTotal / positiveWeightTotal : 0;
  const excessRework = Math.max(0, finiteNumber(preview.rework_score, 0) - finiteNumber(preview.neutral_rework_score, 50));
  const reworkPenalty = excessRework
    * weights.rework_cost_weight
    * weights.low_value_loop_penalty_weight
    * finiteNumber(preview.rework_penalty_scale, 0.35);
  const score = Math.round(clamp(
    positiveScore - reworkPenalty,
    finiteNumber(preview.score_floor, 0),
    finiteNumber(preview.score_ceiling, 100),
  ));

  return {
    score,
    delta: score - Math.round(finiteNumber(preview.base_score, score)),
    positiveScore,
    reworkPenalty,
    weights,
  };
}

function uniqueSorted(values: string[]): string[] {
  return Array.from(new Set(values.filter((value) => value.trim().length > 0)))
    .sort((left, right) => left.localeCompare(right, "zh-CN"));
}

function latestValidTimestamp(events: VisualFacetEvent[]): number | null {
  const timestamps = events
    .map((event) => parseTimestamp(event.occurred_at))
    .filter((timestamp): timestamp is number => timestamp !== null);
  return timestamps.length ? Math.max(...timestamps) : null;
}

function parseTimestamp(value: string): number | null {
  if (!value.trim()) return null;
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : null;
}

function finiteNumber(value: number | undefined, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function clamp(value: number, minimum: number, maximum: number): number {
  if (maximum < minimum) return minimum;
  return Math.min(maximum, Math.max(minimum, value));
}
