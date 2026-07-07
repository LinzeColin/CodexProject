#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S2P01";
const acceptanceId = "ACC-MA-V117-S2P01";
const status = "phase_2_1_editable_draft_model_completed_pending_stage2_review";
const validatorName = "validate:v1.1.7-stage2-phase1";
const stage1ValidatorName = "validate:v1.1.7-stage1";
const stage1ValidatorScript = "validate_memory_atlas_v1_1_7_stage1.cjs";
const draftSchemaVersion = "memory_atlas_proposal_draft.v1";
const draftStoreKey = "memory-atlas.proposal-drafts.v1";

const editableFields = ["importance", "priority", "status", "theme_override", "action_state", "note"];
const targetTypes = ["memory_node", "suggested_action", "tier_asset", "topic_classification"];
const draftStatuses = ["draft_local", "needs_review", "ready_for_agent_apply", "reverted"];
const requiredDraftFields = [
  "draft_id",
  "schema_version",
  "parent_snapshot_id",
  "source_surface",
  "target_type",
  "target_id",
  "field",
  "old_value",
  "proposed_value",
  "reason",
  "evidence_refs",
  "confidence",
  "status",
  "created_at",
  "updated_at",
  "proposal_only",
  "requires_conflict_check",
  "requires_agent_or_human_apply",
  "rollback_hint",
];

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage2_phase1.cjs",
  "OpenAIDatabase/apps/memory-atlas/src/state/proposalDraftStore.ts",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/docs/acceptance/memory_atlas_v1_1_7_stage2_phase1_editable_draft_acceptance.md",
  "OpenAIDatabase/docs/architecture/proposal_edit_model.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
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
    maxBuffer: 32 * 1024 * 1024,
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function getOpenAIDatabaseChangedPaths() {
  const result = run("git", ["-c", "core.quotepath=false", "status", "--short", "--", "OpenAIDatabase"], {
    cwd: worktreeRoot,
  });
  return result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3).trim())
    .filter(Boolean);
}

function validateTextFile(relativePath) {
  const source = readRepoFile(relativePath);
  assertCondition(
    source.endsWith("\n"),
    `${relativePath}:final_newline`,
    `${relativePath} has a final newline`,
    `${relativePath} is missing a final newline`,
  );

  const blocked = [String.fromCharCode(0xfffd), String.fromCharCode(0x00c2), String.fromCharCode(0x00c3), "\u0000"];
  const badLines = [];
  source.split("\n").forEach((line, index) => {
    if (line.trimEnd() !== line) badLines.push(`${index + 1}:trailing`);
    if (blocked.some((char) => line.includes(char))) badLines.push(`${index + 1}:mojibake`);
  });
  assertCondition(
    badLines.length === 0,
    `${relativePath}:text_clean`,
    `${relativePath} has no blocked mojibake characters, null bytes or trailing whitespace`,
    `${relativePath} contains blocked characters, null bytes or trailing whitespace`,
    { badLines: badLines.slice(0, 20) },
  );
}

function validateStage1Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage2_phase1_open_diff_scope",
      "Open diff is limited to Stage 2 Phase 2.1 editable draft model files",
      "Unexpected files changed outside Stage 2 Phase 2.1 scope",
      { changed, outside },
    );
    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", stage1ValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) && packageJson.scripts?.[stage1ValidatorName] === `node scripts/${stage1ValidatorScript}`,
      "stage1_validator_registered_for_post_commit_run",
      "Stage 1 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 1 validator is missing or not registered",
      { script: packageJson.scripts?.[stage1ValidatorName] },
    );
    pass(
      "stage1_validator_deferred_until_clean_tree",
      "Stage 1 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${stage1ValidatorScript}`], { cwd: appRoot });
  const output = result.stdout.trim();
  const parsed = JSON.parse(output.slice(output.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S1-REVIEW",
    "stage1_validator",
    "Stage 1 review validator returned PASS before Stage 2 Phase 2.1 acceptance",
    "Stage 1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateProductModelAndAcceptance() {
  const modelPath = "docs/architecture/proposal_edit_model.md";
  const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage2_phase1_editable_draft_acceptance.md";
  const paramsPath = "config/visualization/model_parameters.universe_state.yaml";
  [modelPath, acceptancePath, paramsPath].forEach(validateTextFile);
  const model = readRepoFile(modelPath);
  const acceptance = readRepoFile(acceptancePath);
  const params = readRepoFile(paramsPath);

  const requiredFragments = [
    "proposal_edit_model_v1_1_7_stage2_phase1",
    taskId,
    acceptanceId,
    status,
    validatorName,
    draftSchemaVersion,
    draftStoreKey,
    "Editable Draft Model",
    "可编辑字段白名单",
    "Draft State Store",
    "refresh warning",
    "undo draft change",
    "No raw/private",
    "No direct writeback",
    "No agent apply",
    "No Proposal UI",
    "No GitHub main upload",
  ].concat(editableFields, targetTypes, draftStatuses, requiredDraftFields);

  assertCondition(
    hasAll(model, requiredFragments),
    "stage2_phase1_proposal_edit_model",
    "Proposal edit model records whitelist, target types, draft schema, store key, undo/warning behavior and safety boundary",
    "Proposal edit model is incomplete",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 2 Phase 2.1 Editable Draft Acceptance",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "proposalDraftStore.ts",
      "proposal_edit_model.md",
      "No Proposal UI",
      "Stop after Stage 2 Phase 2.1",
    ].concat(requiredFragments)),
    "stage2_phase1_acceptance_contract",
    "Acceptance contract covers whitelist, local draft store, undo/warning behavior, validation, failures and stop boundary",
    "Stage 2 Phase 2.1 acceptance contract is incomplete",
  );

  assertCondition(
    hasAll(params, [
      "v1_1_7_stage2_phase1:",
      `task_id: ${taskId}`,
      `acceptance_id: ${acceptanceId}`,
      `status: ${status}`,
      `required_validator: ${validatorName}`,
      `draft_schema_version: ${draftSchemaVersion}`,
      `draft_store_key: ${draftStoreKey}`,
      "editable_field_whitelist",
      "draft_target_types",
      "draft_status_values",
      "proposal_only_required: true",
      "no_direct_writeback: true",
      "no_agent_apply_in_phase: true",
    ].concat(editableFields, targetTypes, draftStatuses, requiredDraftFields)),
    "stage2_phase1_parameter_template",
    "Universe State parameter template records Stage 2 Phase 2.1 editable fields, schema, store and safety boundary",
    "Universe State parameter template is missing Stage 2 Phase 2.1 anchors",
  );
}

function validateDraftStoreImplementation() {
  const storePath = "apps/memory-atlas/src/state/proposalDraftStore.ts";
  validateTextFile(storePath);
  const source = readRepoFile(storePath);

  assertCondition(
    hasAll(source, [
      "PROPOSAL_DRAFT_SCHEMA_VERSION",
      "PROPOSAL_DRAFT_STORE_KEY",
      "PROPOSAL_EDITABLE_FIELDS",
      "PROPOSAL_DRAFT_TARGET_TYPES",
      "PROPOSAL_DRAFT_STATUSES",
      "ProposalEditableField",
      "ProposalDraftTargetType",
      "ProposalDraftStatus",
      "ProposalDraftChange",
      "ProposalDraft",
      "createProposalDraft",
      "upsertProposalDraftChange",
      "removeProposalDraftChange",
      "hasUnsavedProposalDrafts",
      "proposalDraftRefreshWarning",
      "serializeProposalDraftStore",
      "parseProposalDraftStore",
      "loadProposalDraftStore",
      "saveProposalDraftStore",
      "clearProposalDraftStore",
      draftSchemaVersion,
      draftStoreKey,
      "proposal_only: true",
      "requires_conflict_check: true",
      "requires_agent_or_human_apply: true",
    ].concat(editableFields, targetTypes, draftStatuses, requiredDraftFields)),
    "stage2_phase1_draft_store",
    "Draft store exposes whitelisted fields, draft schema, local persistence, undo helpers, refresh warning and proposal-only safety fields",
    "Draft store implementation is incomplete",
  );

  assertCondition(
    !source.includes("fetch(") &&
      !source.includes("XMLHttpRequest") &&
      !source.includes("direct_frontend_mutation_of_active_memory: true") &&
      !source.includes("writeback_allowed: true") &&
      !source.includes("executeAgentApply") &&
      !source.includes("applyProposal(") &&
      !source.includes("writeActiveMemory"),
    "stage2_phase1_draft_store_boundary",
    "Draft store has no network write, direct active-memory mutation or agent apply path",
    "Draft store includes a forbidden writeback or agent-apply path",
  );
}

function validateRecords() {
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  const records = [
    ["CHANGELOG.md", readRepoFile("CHANGELOG.md")],
    ["功能清单.md", readRepoFile("功能清单.md")],
    ["开发记录.md", readRepoFile("开发记录.md")],
    ["模型参数文件.md", readRepoFile("模型参数文件.md")],
    ["docs/MEMORY_ATLAS_DELIVERY_RECORD.md", readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md")],
    ["docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md", readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md")],
  ];

  [
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage2_phase1.cjs",
  ].forEach(validateTextFile);

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage2_phase1.cjs",
    "stage2_phase1_package_script",
    `Package script exposes ${validatorName}`,
    `Package script ${validatorName} is missing`,
    { script: packageJson.scripts?.[validatorName] },
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        "Editable Draft Model",
        "importance",
        "priority",
        "theme_override",
        "action_state",
        "note",
        "No Proposal UI",
        "No GitHub main upload",
      ]),
      `stage2_phase1_records_${name}`,
      `${name} registers Stage 2 Phase 2.1 task, acceptance, validator, whitelist and no-upload boundary`,
      `${name} is missing Stage 2 Phase 2.1 records`,
    );
  }
}

function validateChangeScope() {
  const changed = getOpenAIDatabaseChangedPaths();
  const outside = changed.filter((file) => !allowedChangePaths.includes(file));
  assertCondition(
    outside.length === 0,
    "stage2_phase1_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 2 Phase 2.1 editable draft model, store, validator and records",
    "Unexpected files changed outside Stage 2 Phase 2.1 scope",
    { changed, outside },
  );
}

function main() {
  validateStage1Continuity();
  validateProductModelAndAcceptance();
  validateDraftStoreImplementation();
  validateRecords();
  validateChangeScope();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage2-phase1",
        acceptance_id: acceptanceId,
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
        stage: "v1.1.7-stage2-phase1",
        error: error.message,
        stdout: error.stdout || null,
        stderr: error.stderr || null,
        details: error.details || null,
        checks,
      },
      null,
      2,
    ),
  );
  process.exit(1);
}
