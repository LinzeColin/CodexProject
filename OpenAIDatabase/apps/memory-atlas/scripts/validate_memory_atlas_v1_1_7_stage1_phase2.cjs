#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S1P02";
const acceptanceId = "ACC-MA-V117-S1P02";
const status = "phase_1_2_next_action_detail_completed_pending_stage1_review";
const validatorName = "validate:v1.1.7-stage1-phase2";

const requiredActionFields = [
  "action_id",
  "title",
  "action_type",
  "reason",
  "roi_score",
  "effort_cost",
  "urgency",
  "confidence",
  "source",
  "status",
  "evidence_count",
  "evidence_refs",
  "matched_reason",
  "linked_topic_ids",
  "linked_asset_ids",
  "next_step",
  "recommended_time_window",
  "proposal_hint",
  "rollback_hint",
  "proposal_only",
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
  const model = readRepoFile("docs/architecture/next_action_model.md");
  const acceptance = readRepoFile("docs/acceptance/memory_atlas_v1_1_7_stage1_phase2_next_action_acceptance.md");
  const params = readRepoFile("config/visualization/model_parameters.universe_state.yaml");

  assertCondition(
    hasAll(model, [
      "next_action_model_v1_1_7_stage1_phase2",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "Top 5",
      "nextActionSortScore",
      "roi_score",
      "effort_cost",
      "urgency",
      "No raw/private",
      "No direct writeback",
      "No proposal write",
      "No GitHub main upload",
    ].concat(requiredActionFields)),
    "stage1_phase2_next_action_model",
    "Next Action model defines required fields, sorting, Top 5 cap, fallback and safety boundary",
    "Next Action model is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 1 Phase 1.2 Next Action Acceptance",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "Action Detail Drawer",
      "ROI",
      "effort",
      "urgency",
      "No raw/private",
      "No direct writeback",
      "No proposal write",
      "Stop after this phase",
    ].concat(requiredActionFields)),
    "stage1_phase2_acceptance_contract",
    "Acceptance contract covers evidence, fields, failure conditions, validation and stop boundary",
    "Stage 1 Phase 1.2 acceptance contract is incomplete",
  );

  assertCondition(
    hasAll(params, [
      "v1_1_7_stage1_phase2:",
      `task_id: ${taskId}`,
      `acceptance_id: ${acceptanceId}`,
      `status: ${status}`,
      `required_validator: ${validatorName}`,
      "next_action_sort_weights",
      "roi_weight",
      "urgency_weight",
      "confidence_weight",
      "effort_penalty_weight",
      "top_action_limit: 5",
      "proposal_only_required: true",
    ].concat(requiredActionFields)),
    "stage1_phase2_parameter_template",
    "Universe State parameter template records next action fields, sort weights and proposal-only boundary",
    "Universe State parameter template is missing Stage 1 Phase 1.2 anchors",
  );
}

function validateRuntimeImplementation() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const drawer = readRepoFile("apps/memory-atlas/src/components/ActionDetailDrawer.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");

  assertCondition(
    hasAll(app, [
      "HomeActionDetail",
      "buildNextActionDetails",
      "nextActionSortScore",
      "selectedActionDetail",
      "setSelectedActionDetail",
      "ActionDetailDrawer",
      "data-next-action-card",
      "data-next-action-roi",
      "data-next-action-urgency",
      "data-action-detail-drawer-host",
      "proposal_only: true",
      "slice(0, NEXT_ACTION_TOP_LIMIT)",
    ].concat(requiredActionFields)),
    "stage1_phase2_app_runtime",
    "App builds sortable action details, renders explainable cards and hosts the detail drawer",
    "App runtime is missing next action detail implementation",
  );

  assertCondition(
    hasAll(drawer, [
      "ActionDetailDrawer",
      "HomeActionDetail",
      "data-action-detail-drawer",
      "data-proposal-only=\"true\"",
      "data-active-memory-mutation=\"false\"",
      "roi_score",
      "effort_cost",
      "urgency",
      "evidence_refs",
      "matched_reason",
      "linked_topic_ids",
      "linked_asset_ids",
      "next_step",
      "recommended_time_window",
      "proposal_hint",
      "rollback_hint",
    ]),
    "stage1_phase2_drawer_component",
    "ActionDetailDrawer renders reason, ROI, urgency, evidence, linked context, next step and safety hints",
    "ActionDetailDrawer component is incomplete",
  );

  assertCondition(
    hasAll(styles, [
      ".home-action-meta-grid",
      ".home-action-next-step",
      ".action-detail-drawer",
      ".action-detail-drawer-grid",
      ".action-detail-evidence-list",
      ".action-detail-safety-strip",
      "@media (max-width: 760px)",
    ]),
    "stage1_phase2_styles",
    "Styles define stable action card/detail drawer layout and responsive behavior",
    "Stage 1 Phase 1.2 styles are incomplete",
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
        "Next Action",
        "Action Detail Drawer",
        "roi_score",
        "urgency",
        "proposal_only",
      ]),
      `stage1_phase2_records_${relativePath}`,
      `${relativePath} registers Stage 1 Phase 1.2 task, acceptance, status, validator and action fields`,
      `${relativePath} is missing Stage 1 Phase 1.2 records`,
    );
  }

  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  assertCondition(
    packageSource.includes('"validate:v1.1.7-stage1-phase2": "node scripts/validate_memory_atlas_v1_1_7_stage1_phase2.cjs"'),
    "stage1_phase2_package_script",
    "Package script exposes validate:v1.1.7-stage1-phase2",
    "Package script validate:v1.1.7-stage1-phase2 is missing",
  );
}

function validateChangeScope() {
  const result = run("git", ["-c", "core.quotePath=false", "status", "--short", "--", "OpenAIDatabase"], {
    cwd: worktreeRoot,
  });
  const changed = result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3))
    .map((line) => line.replace(/^OpenAIDatabase\//, ""))
    .map((line) => line.replace(/^\"(.+)\"$/, "$1"))
    .filter(Boolean);

  const allowed = [
    "CHANGELOG.md",
    "config/visualization/model_parameters.universe_state.yaml",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/acceptance/memory_atlas_v1_1_7_stage1_phase2_next_action_acceptance.md",
    "docs/architecture/next_action_model.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase2.cjs",
    "apps/memory-atlas/src/App.tsx",
    "apps/memory-atlas/src/components/ActionDetailDrawer.tsx",
    "apps/memory-atlas/src/styles.css",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];
  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage1_phase2_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 1 Phase 1.2 action model, drawer, validator and records",
    "Unexpected OpenAIDatabase paths changed",
    { changed, outside },
  );
}

try {
  [
    "docs/acceptance/memory_atlas_v1_1_7_stage1_phase2_next_action_acceptance.md",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase2.cjs",
  ].forEach(validateTextFile);
  validateProductModelAndAcceptance();
  validateRuntimeImplementation();
  validateRecords();
  validateChangeScope();
  pass("stage1_phase2_boundary", "No Phase 1.3, raw/private read, direct writeback, proposal write, build, deploy, app install or GitHub main upload is included");
  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.7-stage1-phase2", acceptance_id: acceptanceId, checks }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    stage: "v1.1.7-stage1-phase2",
    acceptance_id: acceptanceId,
    error: error.message,
    details: error.details || null,
    stdout: error.stdout || undefined,
    stderr: error.stderr || undefined,
    checks,
  }, null, 2));
  process.exit(1);
}
