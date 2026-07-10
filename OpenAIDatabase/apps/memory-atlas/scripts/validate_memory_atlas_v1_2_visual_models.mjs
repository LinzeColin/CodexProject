import assert from "node:assert/strict";

import {
  buildVisualFilterSignature,
  buildVisualWorkflowOptions,
  computeFormulaWhatIfScore,
  filterVisualFacetEvents,
} from "../src/visualWorkflows.ts";


const events = [
  {
    event_id: "event_latest",
    occurred_at: "2026-07-01T00:00:00Z",
    source_id: "codex",
    project: "Memory Atlas",
    task_type: "engineering",
    topic: "R6 visual workflow",
    intent: "implementation",
    friction: ["scope_creep"],
    value_signal: ["reusable_asset"],
    evidence_refs: [{ ref_id: "ref_latest", ref_type: "manifest", source_id: "codex", evidence_level: "processed_manifest", path: "", reason: "" }],
  },
  {
    event_id: "event_recent",
    occurred_at: "2026-06-20T00:00:00Z",
    source_id: "chatgpt",
    project: "Finance",
    task_type: "design",
    topic: "Finance interaction design",
    intent: "research",
    friction: [],
    value_signal: ["decision_support"],
    evidence_refs: [{ ref_id: "ref_recent", ref_type: "manifest", source_id: "chatgpt", evidence_level: "processed_manifest", path: "", reason: "" }],
  },
  {
    event_id: "event_old",
    occurred_at: "2026-03-01T00:00:00Z",
    source_id: "codex",
    project: "KMFA",
    task_type: "automation",
    topic: "KMFA automation",
    intent: "execution",
    friction: ["rework"],
    value_signal: ["time_saved"],
    evidence_refs: [{ ref_id: "ref_old", ref_type: "manifest", source_id: "codex", evidence_level: "processed_manifest", path: "", reason: "" }],
  },
  {
    event_id: "event_invalid_date",
    occurred_at: "",
    source_id: "codex",
    project: "Finance",
    task_type: "data",
    topic: "Undated data task",
    intent: "analysis",
    friction: ["evidence_gap"],
    value_signal: [],
    evidence_refs: [],
  },
];

const allFilters = { source: "all", time: "all", project: "all", task: "all" };
const options = buildVisualWorkflowOptions(events);
assert.deepEqual(options.sources, ["chatgpt", "codex"]);
assert.deepEqual(options.projects, ["Finance", "KMFA", "Memory Atlas"]);
assert.deepEqual(options.tasks, ["automation", "data", "design", "engineering"]);
assert.deepEqual(options.times.map((item) => item.id), ["all", "30d", "90d", "365d"]);

assert.deepEqual(filterVisualFacetEvents(events, allFilters).map((item) => item.event_id), [
  "event_latest",
  "event_recent",
  "event_old",
  "event_invalid_date",
]);
assert.deepEqual(
  filterVisualFacetEvents(events, { ...allFilters, source: "codex" }).map((item) => item.event_id),
  ["event_latest", "event_old", "event_invalid_date"],
);
assert.deepEqual(
  filterVisualFacetEvents(events, { ...allFilters, time: "30d" }).map((item) => item.event_id),
  ["event_latest", "event_recent"],
);
assert.deepEqual(
  filterVisualFacetEvents(events, { ...allFilters, project: "Finance" }).map((item) => item.event_id),
  ["event_recent", "event_invalid_date"],
);
assert.deepEqual(
  filterVisualFacetEvents(events, { ...allFilters, task: "automation" }).map((item) => item.event_id),
  ["event_old"],
);
assert.deepEqual(
  filterVisualFacetEvents(events, { source: "codex", time: "365d", project: "KMFA", task: "automation" }).map((item) => item.event_id),
  ["event_old"],
);

const initialSignature = buildVisualFilterSignature(events, allFilters);
assert.equal(initialSignature, buildVisualFilterSignature([...events].reverse(), allFilters));
assert.notEqual(initialSignature, buildVisualFilterSignature(events, { ...allFilters, source: "codex" }));
assert.notEqual(initialSignature, buildVisualFilterSignature(events, { ...allFilters, time: "30d" }));
assert.notEqual(initialSignature, buildVisualFilterSignature(events, { ...allFilters, project: "Finance" }));
assert.notEqual(initialSignature, buildVisualFilterSignature(events, { ...allFilters, task: "automation" }));

const preview = {
  schema_version: "memory_atlas_formula_what_if_display.v1_2_r6",
  simulator_mode: "config_preview_only",
  base_score: 74,
  summary_zh: "内部 proxy 预览。",
  score_floor: 0,
  score_ceiling: 100,
  neutral_rework_score: 50,
  rework_penalty_scale: 0.35,
  default_weights: {
    time_saved_weight: 1,
    reuse_value_weight: 1,
    opportunity_value_weight: 1,
    skill_compounding_weight: 1,
    automation_alignment_weight: 1,
    rework_cost_weight: 1,
    low_value_loop_penalty_weight: 1,
  },
  adjustable_weight_bounds: Object.fromEntries(
    [
      "time_saved_weight",
      "reuse_value_weight",
      "opportunity_value_weight",
      "skill_compounding_weight",
      "automation_alignment_weight",
      "rework_cost_weight",
      "low_value_loop_penalty_weight",
    ].map((key) => [key, { min: 0.25, max: 2, step: 0.05, explanation_zh: `调整 ${key}` }]),
  ),
  baseline_signals: {
    time_saved_proxy: 100,
    reuse_value_proxy: 80,
    opportunity_score_proxy: 60,
    skill_compounding_proxy: 90,
    automation_enhancement_ratio_proxy: 40,
  },
  rework_score: 60,
  formula_source: "机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json",
  formula_expression_zh: "What-if 分 = clamp(加权正向 proxy 分 - 返工惩罚, 0, 100)",
  formula_interpretation_zh: "不是收入预测。",
  scenarios: [],
  safety: {
    active_config_write: false,
    proposal_required_before_apply: true,
    raw_mutation: false,
    financial_advice: false,
    precise_income_prediction: false,
  },
};

const baseline = computeFormulaWhatIfScore(preview, preview.default_weights);
assert.equal(baseline.score, 71);
assert.equal(baseline.delta, -3);
assert.deepEqual(baseline.weights, preview.default_weights);

const changed = computeFormulaWhatIfScore(preview, {
  ...preview.default_weights,
  time_saved_weight: 9,
});
assert.equal(changed.weights.time_saved_weight, 2);
assert.equal(changed.score, 75);
assert.notEqual(changed.score, baseline.score);

const reset = computeFormulaWhatIfScore(preview, preview.default_weights);
assert.deepEqual(reset, baseline);

process.stdout.write(`${JSON.stringify({
  status: "PASS",
  event_count: events.length,
  option_counts: {
    source: options.sources.length,
    project: options.projects.length,
    task: options.tasks.length,
  },
  baseline_score: baseline.score,
  changed_score: changed.score,
})}\n`);
