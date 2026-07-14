#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S1P03";
const acceptanceId = "ACC-MA-V117-S1P03";
const status = "phase_1_3_tier_asset_detail_completed_pending_stage1_review";
const validatorName = "validate:v1.1.7-stage1-phase3";

const requiredAssetFields = [
  "asset_id",
  "asset_tier",
  "title",
  "summary",
  "theme",
  "value_score",
  "updated_at",
  "importance",
  "priority",
  "confidence",
  "staleness_status",
  "last_seen_range",
  "evidence_count",
  "evidence_refs",
  "source_scope",
  "linked_action_ids",
  "linked_topic_ids",
  "recommended_asset_action",
  "proposal_hint",
  "rollback_hint",
  "proposal_only",
];

const requiredAssetTiers = [
  "core_profile",
  "project",
  "decision",
  "workflow",
  "knowledge",
  "opportunity",
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
  const model = readRepoFile("docs/architecture/level_asset_model.md");
  const acceptance = readRepoFile("docs/acceptance/memory_atlas_v1_1_7_stage1_phase3_tier_asset_acceptance.md");
  const params = readRepoFile("config/visualization/model_parameters.universe_state.yaml");

  assertCondition(
    hasAll(model, [
      "level_asset_model_v1_1_7_stage1_phase3",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "Level Asset",
      "AssetDetailPanel",
      "No raw/private",
      "No direct writeback",
      "No proposal write",
      "No GitHub main upload",
    ].concat(requiredAssetFields, requiredAssetTiers)),
    "stage1_phase3_level_asset_model",
    "Level Asset model defines seven asset tiers, required fields, derivation, fallback and safety boundary",
    "Level Asset model is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 1 Phase 1.3 Tier Asset Acceptance",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "AssetDetailPanel",
      "Level Assets",
      "No raw/private",
      "No direct writeback",
      "No proposal write",
      "Stop after Stage 1 Phase 1.3",
    ].concat(requiredAssetFields, requiredAssetTiers)),
    "stage1_phase3_acceptance_contract",
    "Acceptance contract covers fields, UI behavior, safety, failure conditions, validation and stop boundary",
    "Stage 1 Phase 1.3 acceptance contract is incomplete",
  );

  assertCondition(
    hasAll(params, [
      "v1_1_7_stage1_phase3:",
      `task_id: ${taskId}`,
      `acceptance_id: ${acceptanceId}`,
      `status: ${status}`,
      `required_validator: ${validatorName}`,
      "asset_tier_values",
      "tier_asset_sort_weights",
      "value_weight",
      "importance_weight",
      "confidence_weight",
      "staleness_penalty_weight",
      "top_asset_limit: 7",
      "proposal_only_required: true",
    ].concat(requiredAssetFields, requiredAssetTiers)),
    "stage1_phase3_parameter_template",
    "Universe State parameter template records asset fields, tier values, sort weights and proposal-only boundary",
    "Universe State parameter template is missing Stage 1 Phase 1.3 anchors",
  );
}

function validateRuntimeImplementation() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const panel = readRepoFile("apps/memory-atlas/src/components/AssetDetailPanel.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");

  assertCondition(
    hasAll(app, [
      "TierAssetDetail",
      "buildTierAssetDetails",
      "tierAssetSortScore",
      "selectedTierAsset",
      "setSelectedTierAsset",
      "AssetDetailPanel",
      "data-tier-asset-card",
      "data-tier-asset-value",
      "data-tier-asset-staleness",
      "data-asset-detail-panel-host",
      "proposal_only: true",
      "slice(0, TIER_ASSET_TOP_LIMIT)",
    ].concat(requiredAssetFields, requiredAssetTiers)),
    "stage1_phase3_app_runtime",
    "App builds sortable tier asset details, renders explainable cards and hosts the asset detail panel",
    "App runtime is missing tier asset detail implementation",
  );

  assertCondition(
    hasAll(panel, [
      "AssetDetailPanel",
      "TierAssetDetail",
      "data-asset-detail-panel",
      "data-proposal-only=\"true\"",
      "data-active-memory-mutation=\"false\"",
    ].concat(requiredAssetFields)),
    "stage1_phase3_asset_detail_panel",
    "AssetDetailPanel renders summary, value, staleness, evidence, linked context, recommended action and safety hints",
    "AssetDetailPanel component is incomplete",
  );

  assertCondition(
    hasAll(styles, [
      ".home-tier-asset-panel",
      ".home-tier-asset-grid",
      ".home-tier-asset-card",
      ".tier-asset-meta-grid",
      ".asset-detail-panel",
      ".asset-detail-panel-grid",
      ".asset-detail-evidence-list",
      ".asset-detail-safety-strip",
      "@media (max-width: 760px)",
    ]),
    "stage1_phase3_styles",
    "Styles define stable tier asset card/detail panel layout and responsive behavior",
    "Stage 1 Phase 1.3 styles are incomplete",
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
        "Level Asset",
        "AssetDetailPanel",
        "value_score",
        "staleness_status",
        "proposal_only",
      ]),
      `stage1_phase3_records_${relativePath}`,
      `${relativePath} registers Stage 1 Phase 1.3 task, acceptance, status, validator and asset fields`,
      `${relativePath} is missing Stage 1 Phase 1.3 records`,
    );
  }

  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  assertCondition(
    packageSource.includes('"validate:v1.1.7-stage1-phase3": "node scripts/validate_memory_atlas_v1_1_7_stage1_phase3.cjs"'),
    "stage1_phase3_package_script",
    "Package script exposes validate:v1.1.7-stage1-phase3",
    "Package script validate:v1.1.7-stage1-phase3 is missing",
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
    "docs/acceptance/memory_atlas_v1_1_7_stage1_phase3_tier_asset_acceptance.md",
    "docs/architecture/level_asset_model.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase3.cjs",
    "apps/memory-atlas/src/App.tsx",
    "apps/memory-atlas/src/components/AssetDetailPanel.tsx",
    "apps/memory-atlas/src/styles.css",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];
  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage1_phase3_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 1 Phase 1.3 level asset model, panel, validator and records",
    "Unexpected OpenAIDatabase paths changed",
    { changed, outside },
  );
}

try {
  [
    "docs/acceptance/memory_atlas_v1_1_7_stage1_phase3_tier_asset_acceptance.md",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase3.cjs",
  ].forEach(validateTextFile);
  validateProductModelAndAcceptance();
  validateRuntimeImplementation();
  validateRecords();
  validateChangeScope();
  pass("stage1_phase3_boundary", "No Phase 1.4, raw/private read, direct writeback, proposal write, build, deploy, app install or GitHub main upload is included");
  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.7-stage1-phase3", acceptance_id: acceptanceId, checks }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    stage: "v1.1.7-stage1-phase3",
    acceptance_id: acceptanceId,
    error: error.message,
    details: error.details || null,
    stdout: error.stdout || undefined,
    stderr: error.stderr || undefined,
    checks,
  }, null, 2));
  process.exit(1);
}
