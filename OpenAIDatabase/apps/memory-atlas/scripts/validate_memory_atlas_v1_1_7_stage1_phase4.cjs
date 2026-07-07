#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S1P04";
const acceptanceId = "ACC-MA-V117-S1P04";
const status = "phase_1_4_topic_classification_detail_completed_pending_stage1_review";
const validatorName = "validate:v1.1.7-stage1-phase4";

const requiredTopicFields = [
  "topic_id",
  "topic_label",
  "parent_topic",
  "category",
  "topic_state",
  "topic_strength",
  "trend",
  "roi_score",
  "conflict_score",
  "confidence",
  "record_count",
  "recent_count",
  "representative_record_ids",
  "evidence_refs",
  "matched_reason",
  "linked_asset_ids",
  "linked_action_ids",
  "starfield_handoff",
  "river_handoff",
  "proposal_hint",
  "rollback_hint",
  "proposal_only",
];

const requiredTopicStates = [
  "dominant",
  "rising",
  "declining",
  "emerging",
  "conflict",
  "black_hole",
  "stale",
];

function pass(name, evidence, details) {
  checks.push({ name, status: "PASS", evidence, ...(details ? { details } : {}) });
}

function assertCondition(condition, name, evidence, failure, details = {}) {
  if (condition) {
    pass(name, evidence, details);
    return;
  }
  const error = new Error(failure);
  error.details = details;
  throw error;
}

function readRepoFile(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), "utf8");
}

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: "utf8",
    stdio: "pipe",
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function validateTextFile(relativePath) {
  const source = readRepoFile(relativePath);
  assertCondition(
    source.endsWith("\n"),
    `${relativePath}:final_newline`,
    `${relativePath} has a final newline`,
    `${relativePath} is missing a final newline`,
  );

  const blocked = [String.fromCharCode(0xfffd), String.fromCharCode(0x00c2), String.fromCharCode(0x00c3)];
  const badLines = [];
  source.split("\n").forEach((line, index) => {
    if (line.trimEnd() !== line) badLines.push(`${index + 1}:trailing`);
    if (blocked.some((char) => line.includes(char))) badLines.push(`${index + 1}:mojibake`);
  });
  assertCondition(
    badLines.length === 0,
    `${relativePath}:text_clean`,
    `${relativePath} has no blocked mojibake characters, null bytes or trailing whitespace`,
    `${relativePath} contains blocked characters or trailing whitespace`,
    { badLines: badLines.slice(0, 20) },
  );
}

function validateProductModelAndAcceptance() {
  const model = readRepoFile("docs/architecture/theme_category_model.md");
  const acceptance = readRepoFile("docs/acceptance/memory_atlas_v1_1_7_stage1_phase4_topic_classification_acceptance.md");
  const params = readRepoFile("config/visualization/model_parameters.universe_state.yaml");

  assertCondition(
    hasAll(model, [
      "theme_category_model_v1_1_7_stage1_phase4",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "Topic Classification",
      "ThemeDetailPanel",
      "Starfield handoff",
      "River handoff",
      "No raw/private",
      "No direct writeback",
      "No proposal write",
      "No GitHub main upload",
    ].concat(requiredTopicFields, requiredTopicStates)),
    "stage1_phase4_theme_category_model",
    "Theme category model defines topic states, required fields, handoffs and safety boundary",
    "Theme category model is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 1 Phase 1.4 Topic Classification Acceptance",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "ThemeDetailPanel",
      "Topic Classification",
      "No raw/private",
      "No direct writeback",
      "No proposal write",
      "Stop after Stage 1 Phase 1.4",
    ].concat(requiredTopicFields, requiredTopicStates)),
    "stage1_phase4_acceptance_contract",
    "Acceptance contract covers fields, UI behavior, safety, failure conditions, validation and stop boundary",
    "Stage 1 Phase 1.4 acceptance contract is incomplete",
  );

  assertCondition(
    hasAll(params, [
      "v1_1_7_stage1_phase4:",
      `task_id: ${taskId}`,
      `acceptance_id: ${acceptanceId}`,
      `status: ${status}`,
      `required_validator: ${validatorName}`,
      "topic_state_values",
      "topic_classification_sort_weights",
      "strength_weight",
      "trend_weight",
      "confidence_weight",
      "conflict_penalty_weight",
      "top_topic_limit: 10",
      "proposal_only_required: true",
    ].concat(requiredTopicFields, requiredTopicStates)),
    "stage1_phase4_parameter_template",
    "Universe State parameter template records topic fields, topic states, sort weights and proposal-only boundary",
    "Universe State parameter template is missing Stage 1 Phase 1.4 anchors",
  );
}

function validateRuntimeImplementation() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const panel = readRepoFile("apps/memory-atlas/src/components/ThemeDetailPanel.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");

  assertCondition(
    hasAll(app, [
      "TopicClassificationDetail",
      "buildTopicClassificationDetails",
      "topicClassificationSortScore",
      "selectedTopicDetail",
      "setSelectedTopicDetail",
      "ThemeDetailPanel",
      "data-topic-detail-card",
      "data-topic-strength",
      "data-topic-state",
      "data-theme-detail-panel-host",
      "proposal_only: true",
      "slice(0, TOPIC_CLASSIFICATION_TOP_LIMIT)",
    ].concat(requiredTopicFields, requiredTopicStates)),
    "stage1_phase4_app_runtime",
    "App builds sortable topic classification details, renders explainable cards and hosts the theme detail panel",
    "App runtime is missing topic classification detail implementation",
  );

  assertCondition(
    hasAll(panel, [
      "ThemeDetailPanel",
      "TopicClassificationDetail",
      "data-theme-detail-panel",
      "data-proposal-only=\"true\"",
      "data-active-memory-mutation=\"false\"",
    ].concat(requiredTopicFields)),
    "stage1_phase4_theme_detail_panel",
    "ThemeDetailPanel renders state, trend, ROI, conflict, evidence, linked context, handoffs and safety hints",
    "ThemeDetailPanel component is incomplete",
  );

  assertCondition(
    hasAll(styles, [
      ".home-topic-detail-panel",
      ".home-topic-detail-grid",
      ".home-topic-detail-card",
      ".topic-detail-meta-grid",
      ".theme-detail-panel",
      ".theme-detail-panel-grid",
      ".theme-detail-evidence-list",
      ".theme-detail-safety-strip",
      "@media (max-width: 760px)",
    ]),
    "stage1_phase4_styles",
    "Styles define stable topic detail card/panel layout and responsive behavior",
    "Stage 1 Phase 1.4 styles are incomplete",
  );
}

function validateRecords() {
  const records = [
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  ];

  for (const relativePath of records) {
    const source = readRepoFile(relativePath);
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        "Topic Classification",
        "ThemeDetailPanel",
        "topic_strength",
        "matched_reason",
        "proposal_only",
      ]),
      `stage1_phase4_records_${relativePath}`,
      `${relativePath} registers Stage 1 Phase 1.4 task, acceptance, status, validator and topic fields`,
      `${relativePath} is missing Stage 1 Phase 1.4 records`,
    );
  }
}

function validatePackageScript() {
  const pkg = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  assertCondition(
    pkg.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage1_phase4.cjs",
    "stage1_phase4_package_script",
    `Package script exposes ${validatorName}`,
    `Package script ${validatorName} is missing`,
    { script: pkg.scripts?.[validatorName] },
  );
}

function validateChangeScope() {
  const result = run("git", ["-c", "core.quotepath=false", "diff", "--name-only", "HEAD", "--", "OpenAIDatabase"], { cwd: worktreeRoot });
  const changed = result.stdout.trim().split("\n").filter(Boolean);
  const allowed = [
    "OpenAIDatabase/CHANGELOG.md",
    "OpenAIDatabase/apps/memory-atlas/package.json",
    "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase4.cjs",
    "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
    "OpenAIDatabase/apps/memory-atlas/src/components/ThemeDetailPanel.tsx",
    "OpenAIDatabase/apps/memory-atlas/src/styles.css",
    "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
    "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "OpenAIDatabase/docs/acceptance/memory_atlas_v1_1_7_stage1_phase4_topic_classification_acceptance.md",
    "OpenAIDatabase/docs/architecture/theme_category_model.md",
    "OpenAIDatabase/功能清单.md",
    "OpenAIDatabase/开发记录.md",
    "OpenAIDatabase/模型参数文件.md",
  ];
  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage1_phase4_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 1 Phase 1.4 topic model, panel, validator and records",
    "Unexpected files changed outside Stage 1 Phase 1.4 scope",
    { changed, outside },
  );
}

function validateBoundary() {
  const panel = readRepoFile("apps/memory-atlas/src/components/ThemeDetailPanel.tsx");
  assertCondition(
    !panel.includes("localStorage.setItem") &&
      !panel.includes("fetch(") &&
      !panel.includes("writeback_allowed: true") &&
      !panel.includes("direct_frontend_mutation_of_active_memory: true"),
    "stage1_phase4_boundary",
    "No Stage 2 proposal editor, raw/private read, direct writeback, proposal write, build, deploy, app install or GitHub main upload is included",
    "Stage 1 Phase 1.4 boundary violation detected",
  );
}

function main() {
  try {
    [
      "docs/architecture/theme_category_model.md",
      "docs/acceptance/memory_atlas_v1_1_7_stage1_phase4_topic_classification_acceptance.md",
      "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase4.cjs",
    ].forEach(validateTextFile);
    validateProductModelAndAcceptance();
    validateRuntimeImplementation();
    validateRecords();
    validatePackageScript();
    validateChangeScope();
    validateBoundary();
    console.log(JSON.stringify({ status: "PASS", stage: "v1.1.7-stage1-phase4", acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.error(JSON.stringify({
      status: "FAIL",
      stage: "v1.1.7-stage1-phase4",
      error: error.message,
      stdout: error.stdout ?? null,
      stderr: error.stderr ?? null,
      details: error.details ?? null,
      checks,
    }, null, 2));
    process.exit(1);
  }
}

main();
