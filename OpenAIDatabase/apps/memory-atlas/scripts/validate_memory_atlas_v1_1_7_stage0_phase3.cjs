#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const checks = [];

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

function selectedTextFiles() {
  return [
    "docs/product/detail_visibility_contract.md",
    "docs/acceptance/memory_atlas_v1_1_7_stage0_phase3_detail_visibility_acceptance.md",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage0_phase3.cjs",
    "apps/memory-atlas/package.json",
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  ].filter((relativePath) => fs.existsSync(path.join(repoRoot, relativePath)));
}

function validateTextCleanliness() {
  const blockedChars = [String.fromCharCode(0xfffd), String.fromCharCode(0x00c2), String.fromCharCode(0x00c3), "\u0000"];
  const bad = [];
  for (const relativePath of selectedTextFiles()) {
    const source = readRepoFile(relativePath);
    if (!source.endsWith("\n")) bad.push(`${relativePath}:final_newline`);
    source.split("\n").forEach((line, index) => {
      if (line.trimEnd() !== line) bad.push(`${relativePath}:${index + 1}:trailing`);
      if (blockedChars.some((char) => line.includes(char))) bad.push(`${relativePath}:${index + 1}:mojibake`);
    });
    if (relativePath.endsWith(".json")) {
      try {
        JSON.parse(source);
      } catch (error) {
        bad.push(`${relativePath}:json:${error.message}`);
      }
    }
  }
  assertCondition(
    bad.length === 0,
    "stage0_phase3_text_cleanliness",
    "Stage 0 Phase 3 contract, acceptance, validator and records are text-clean",
    "Selected Stage 0 Phase 3 files contain mojibake, trailing whitespace, invalid JSON or missing final newline",
    { bad: bad.slice(0, 40), scannedFileCount: selectedTextFiles().length },
  );
}

function validateDetailContract() {
  const product = readRepoFile("docs/product/detail_visibility_contract.md");

  assertCondition(
    hasAll(product, [
      "Memory Atlas v1.1.7 Stage 0 Phase 3 Detail Visibility Field Contract",
      "memory_atlas_v1_1_7_stage0_phase3_detail_visibility_contract",
      "MA-V117-S0P03",
      "ACC-MA-V117-S0P03",
      "phase_0_3_detail_visibility_contract_completed_pending_stage0_review",
      "source_scope",
      "display_surface",
      "edit_permission",
      "No raw/private",
      "No GitHub",
      "main upload",
    ]),
    "stage0_phase3_contract_header_scope",
    "Detail visibility contract identifies v1.1.7 Phase 0.3, shared rules and no-upload boundary",
    "Detail visibility contract header or shared boundary is incomplete",
  );

  assertCondition(
    hasAll(product, [
      "Object key: `suggested_action_detail`",
      "| `action_id` | yes",
      "| `title` | yes",
      "| `action_type` | yes",
      "| `reason` | yes",
      "| `roi_score` | yes",
      "| `effort_cost` | yes",
      "| `urgency` | yes",
      "| `confidence` | yes",
      "| `evidence_count` | yes",
      "| `evidence_refs` | yes",
      "| `matched_reason` | yes",
      "| `linked_topic_ids` | yes",
      "| `linked_asset_ids` | yes",
      "| `next_step` | yes",
      "| `recommended_time_window` | yes",
      "| `proposal_hint` | yes",
      "| `rollback_hint` | yes",
    ]),
    "stage0_phase3_suggested_action_fields",
    "Suggested action detail defines required reason, ROI, effort, urgency, evidence and next-step fields",
    "Suggested action detail field contract is incomplete",
  );

  assertCondition(
    hasAll(product, [
      "Object key: `tier_asset_detail`",
      "`core_profile`",
      "`project`",
      "`decision`",
      "`workflow`",
      "`knowledge`",
      "`opportunity`",
      "`stale`",
      "| `asset_id` | yes",
      "| `asset_tier` | yes",
      "| `summary` | yes",
      "| `importance` | yes",
      "| `priority` | yes",
      "| `staleness_status` | yes",
      "| `last_seen_range` | yes",
      "| `linked_action_ids` | yes",
      "| `linked_topic_ids` | yes",
      "| `recommended_asset_action` | yes",
    ]),
    "stage0_phase3_tier_asset_fields",
    "Tier asset detail defines asset tiers, importance, priority, freshness, evidence and linked action/topic fields",
    "Tier asset detail field contract is incomplete",
  );

  assertCondition(
    hasAll(product, [
      "Object key: `topic_classification_detail`",
      "`dominant`",
      "`rising`",
      "`declining`",
      "`emerging`",
      "`conflict`",
      "`black_hole`",
      "| `topic_id` | yes",
      "| `topic_label` | yes",
      "| `topic_state` | yes",
      "| `topic_strength` | yes",
      "| `trend` | yes",
      "| `record_count` | yes",
      "| `related_topic_ids` | yes",
      "| `linked_starfield_cluster_id` | yes",
      "| `linked_river_range` | yes",
      "| `recommended_topic_action` | yes",
    ]),
    "stage0_phase3_topic_classification_fields",
    "Topic classification detail defines strength, trend, confidence, record/evidence counts, related links and next action fields",
    "Topic classification detail field contract is incomplete",
  );

  assertCondition(
    hasAll(product, [
      "read_only",
      "proposal_only",
      "system_generated",
      "directly mutate active memory",
      "source snapshots",
      "model parameter files",
      "generated evidence refs",
      "long-term memory",
      "Missing required values must render an empty/error explanation",
      "must not be replaced with mock data",
    ]),
    "stage0_phase3_edit_and_fallback_policy",
    "Contract defines edit permissions, no-direct-writeback and no-mock fallback policy",
    "Edit permission or fallback policy is incomplete",
  );
}

function validateAcceptanceAndRecords() {
  const acceptance = readRepoFile("docs/acceptance/memory_atlas_v1_1_7_stage0_phase3_detail_visibility_acceptance.md");
  const packageJson = readRepoFile("apps/memory-atlas/package.json");
  const records = [
    ["CHANGELOG.md", readRepoFile("CHANGELOG.md")],
    ["功能清单.md", readRepoFile("功能清单.md")],
    ["开发记录.md", readRepoFile("开发记录.md")],
    ["模型参数文件.md", readRepoFile("模型参数文件.md")],
    ["docs/MEMORY_ATLAS_DELIVERY_RECORD.md", readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md")],
    ["docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md", readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md")],
  ];

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 0 Phase 3 Detail Visibility Acceptance",
      "ACC-MA-V117-S0P03",
      "MA-V117-S0P03",
      "validate:v1.1.7-stage0-phase3",
      "Suggested action fields",
      "Tier asset fields",
      "Topic classification fields",
      "Source and display",
      "Edit permissions",
      "Safety boundary",
      "contract-only",
    ]),
    "stage0_phase3_acceptance",
    "Stage 0 Phase 3 acceptance checklist is present and aligned",
    "Stage 0 Phase 3 acceptance checklist is incomplete",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.7-stage0-phase3": "node scripts/validate_memory_atlas_v1_1_7_stage0_phase3.cjs"'),
    "stage0_phase3_package_script",
    "package.json exposes validate:v1.1.7-stage0-phase3",
    "package.json is missing validate:v1.1.7-stage0-phase3",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        "MA-V117-S0P03",
        "ACC-MA-V117-S0P03",
        "phase_0_3_detail_visibility_contract_completed_pending_stage0_review",
        "validate:v1.1.7-stage0-phase3",
      ]),
      `stage0_phase3_records_${name}`,
      `${name} registers Stage 0 Phase 3 status, acceptance and validator`,
      `${name} is missing Stage 0 Phase 3 record tokens`,
    );
  }
}

function main() {
  validateTextCleanliness();
  validateDetailContract();
  validateAcceptanceAndRecords();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage0-phase3",
        acceptance_id: "ACC-MA-V117-S0P03",
        checks,
      },
      null,
      2,
    ),
  );
}

try {
  main();
} catch (error) {
  console.error(
    JSON.stringify(
      {
        status: "FAIL",
        stage: "v1.1.7-stage0-phase3",
        error: error.message,
        details: error.details || null,
        checks,
      },
      null,
      2,
    ),
  );
  process.exit(1);
}
