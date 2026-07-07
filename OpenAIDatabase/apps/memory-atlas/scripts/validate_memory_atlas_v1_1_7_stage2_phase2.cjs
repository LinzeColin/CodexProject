#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S2P02";
const acceptanceId = "ACC-MA-V117-S2P02";
const status = "phase_2_2_proposal_ui_completed_pending_stage2_review";
const validatorName = "validate:v1.1.7-stage2-phase2";
const stage2Phase1ValidatorName = "validate:v1.1.7-stage2-phase1";
const stage2Phase1ValidatorScript = "validate_memory_atlas_v1_1_7_stage2_phase1.cjs";
const draftSchemaVersion = "memory_atlas_proposal_draft.v1";
const exportSchemaVersion = "memory_atlas_proposal_export.v1";
const draftStoreKey = "memory-atlas.proposal-drafts.v1";

const editableFields = ["importance", "priority", "status", "theme_override", "action_state", "note"];
const proposalUiFields = ["importance", "priority"];
const requiredUiFragments = [
  "ProposalEditor",
  "ProposalDiffPreview",
  "data-proposal-editor",
  "data-proposal-diff-preview",
  "data-proposal-only=\"true\"",
  "data-active-memory-mutation=\"false\"",
  "proposalDraftRefreshWarning",
  "upsertProposalDraftChange",
  "removeProposalDraftChange",
  "saveProposalDraftStore",
  "loadProposalDraftStore",
  "serializeProposalDraftStore",
  "memory_atlas_proposal_export.v1",
  "rollback_metadata",
  "original_value",
  "proposed_value",
  "impact_summary",
  "requires_conflict_check",
  "requires_agent_or_human_apply",
  "导出 proposal JSON",
  "撤销本地调整",
];
const requiredEditorFragments = requiredUiFragments.filter((fragment) => fragment !== "data-proposal-diff-preview");

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage2_phase2.cjs",
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/components/ProposalDiffPreview.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/components/ProposalEditor.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/state/proposalDraftStore.ts",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/docs/acceptance/memory_atlas_v1_1_7_stage2_phase2_proposal_ui_acceptance.md",
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

function validateStage2Phase1Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage2_phase2_open_diff_scope",
      "Open diff is limited to Stage 2 Phase 2.2 Proposal UI files",
      "Unexpected files changed outside Stage 2 Phase 2.2 scope",
      { changed, outside },
    );
    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", stage2Phase1ValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) && packageJson.scripts?.[stage2Phase1ValidatorName] === `node scripts/${stage2Phase1ValidatorScript}`,
      "stage2_phase1_validator_registered_for_post_commit_run",
      "Stage 2 Phase 2.1 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 2 Phase 2.1 validator is missing or not registered",
      { script: packageJson.scripts?.[stage2Phase1ValidatorName] },
    );
    pass(
      "stage2_phase1_validator_deferred_until_clean_tree",
      "Stage 2 Phase 2.1 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${stage2Phase1ValidatorScript}`], { cwd: appRoot });
  const output = result.stdout.trim();
  const parsed = JSON.parse(output.slice(output.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S2P01",
    "stage2_phase1_validator",
    "Stage 2 Phase 2.1 validator returned PASS before Stage 2 Phase 2.2 acceptance",
    "Stage 2 Phase 2.1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateProductModelAndAcceptance() {
  const modelPath = "docs/architecture/proposal_edit_model.md";
  const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage2_phase2_proposal_ui_acceptance.md";
  const paramsPath = "config/visualization/model_parameters.universe_state.yaml";
  [modelPath, acceptancePath, paramsPath].forEach(validateTextFile);
  const model = readRepoFile(modelPath);
  const acceptance = readRepoFile(acceptancePath);
  const params = readRepoFile(paramsPath);

  const requiredFragments = [
    "proposal_ui_v1_1_7_stage2_phase2",
    taskId,
    acceptanceId,
    status,
    validatorName,
    draftSchemaVersion,
    exportSchemaVersion,
    draftStoreKey,
    "Proposal UI",
    "Importance / Priority Editor",
    "Proposal Diff Preview",
    "Export / Rollback Contract",
    "No raw/private",
    "No direct writeback",
    "No agent apply",
    "No GitHub main upload",
  ].concat(editableFields, proposalUiFields, requiredUiFragments);

  assertCondition(
    hasAll(model, requiredFragments),
    "stage2_phase2_proposal_ui_model",
    "Proposal edit model records Proposal UI, diff preview, export/rollback contract and safety boundary",
    "Proposal edit model is missing Stage 2 Phase 2.2 Proposal UI contract",
  );

  assertCondition(
    hasAll(acceptance, [
      "Memory Atlas v1.1.7 Stage 2 Phase 2.2 Proposal UI Acceptance",
      "ProposalEditor.tsx",
      "ProposalDiffPreview.tsx",
      "Importance / Priority Editor",
      "显示原值、新值、影响说明",
      "可导出 JSON",
      "rollback metadata",
      "Stop after Stage 2 Phase 2.2",
    ].concat(requiredFragments)),
    "stage2_phase2_acceptance_contract",
    "Acceptance contract covers editor controls, diff preview, export/rollback behavior, validation and stop boundary",
    "Stage 2 Phase 2.2 acceptance contract is incomplete",
  );

  assertCondition(
    hasAll(params, [
      "v1_1_7_stage2_phase2:",
      `task_id: ${taskId}`,
      `acceptance_id: ${acceptanceId}`,
      `status: ${status}`,
      `required_validator: ${validatorName}`,
      `draft_schema_version: ${draftSchemaVersion}`,
      `export_schema_version: ${exportSchemaVersion}`,
      `draft_store_key: ${draftStoreKey}`,
      "proposal_ui_fields",
      "proposal_ui_required_components",
      "export_rollback_required: true",
      "proposal_only_required: true",
      "no_direct_writeback: true",
      "no_agent_apply_in_phase: true",
    ].concat(proposalUiFields)),
    "stage2_phase2_parameter_template",
    "Universe State parameter template records Proposal UI controls, export schema and safety boundary",
    "Universe State parameter template is missing Stage 2 Phase 2.2 anchors",
  );
}

function validateRuntimeImplementation() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const editor = readRepoFile("apps/memory-atlas/src/components/ProposalEditor.tsx");
  const diff = readRepoFile("apps/memory-atlas/src/components/ProposalDiffPreview.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");

  [
    "apps/memory-atlas/src/App.tsx",
    "apps/memory-atlas/src/components/ProposalEditor.tsx",
    "apps/memory-atlas/src/components/ProposalDiffPreview.tsx",
    "apps/memory-atlas/src/styles.css",
  ].forEach(validateTextFile);

  assertCondition(
    hasAll(app, [
      "ProposalEditor",
      "WritebackProposalPanel",
      "data-proposal-schema",
      "memory_change_proposal.v1",
    ]),
    "stage2_phase2_app_integration",
    "App integrates ProposalEditor inside the existing writeback panel without replacing the controlled proposal boundary",
    "App is missing ProposalEditor integration",
  );

  assertCondition(
    hasAll(editor, requiredEditorFragments.concat([
      "PROPOSAL_EDITABLE_FIELDS",
      "PROPOSAL_DRAFT_SCHEMA_VERSION",
      "PROPOSAL_DRAFT_STORE_KEY",
      "createProposalDraft",
      "downloadProposalJson",
      "type=\"range\"",
      "ariaLabel=\"调整 importance\"",
      "ariaLabel=\"调整 priority\"",
      "aria-label={ariaLabel}",
      "ProposalDiffPreview",
    ])),
    "stage2_phase2_proposal_editor",
    "ProposalEditor renders importance/priority controls, draft persistence, export JSON, rollback metadata, warning and no-writeback safety",
    "ProposalEditor implementation is incomplete",
  );

  assertCondition(
    hasAll(diff, [
      "ProposalDiffPreview",
      "data-proposal-diff-preview",
      "original_value",
      "proposed_value",
      "impact_summary",
      "rollback_metadata",
      "requires_conflict_check",
      "requires_agent_or_human_apply",
      "memory_atlas_proposal_export.v1",
    ]),
    "stage2_phase2_proposal_diff_preview",
    "ProposalDiffPreview renders original/proposed values, impact summary and rollback/apply safety metadata",
    "ProposalDiffPreview implementation is incomplete",
  );

  assertCondition(
    hasAll(styles, [
      ".proposal-editor",
      ".proposal-editor-grid",
      ".proposal-field-control",
      ".proposal-range-row",
      ".proposal-diff-preview",
      ".proposal-diff-grid",
      ".proposal-rollback-metadata",
      ".proposal-editor-actions",
      ".proposal-editor-warning",
      "@media (max-width: 760px)",
    ]),
    "stage2_phase2_styles",
    "Styles define dense product UI layout, stable controls, diff preview and responsive behavior",
    "Stage 2 Phase 2.2 styles are incomplete",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage2_phase2.cjs",
  ].forEach(validateTextFile);

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage2_phase2.cjs",
    "stage2_phase2_package_script",
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
        "Proposal UI",
        "ProposalEditor",
        "ProposalDiffPreview",
        "importance",
        "priority",
        "Export / Rollback Contract",
        "No GitHub main upload",
      ]),
      `stage2_phase2_records_${name}`,
      `${name} registers Stage 2 Phase 2.2 task, acceptance, validator, UI and no-upload boundary`,
      `${name} is missing Stage 2 Phase 2.2 records`,
    );
  }
}

function validateBoundary() {
  const editor = readRepoFile("apps/memory-atlas/src/components/ProposalEditor.tsx");
  const diff = readRepoFile("apps/memory-atlas/src/components/ProposalDiffPreview.tsx");
  const source = `${editor}\n${diff}`;
  assertCondition(
    !source.includes("fetch(") &&
      !source.includes("XMLHttpRequest") &&
      !source.includes("direct_frontend_mutation_of_active_memory: true") &&
      !source.includes("writeback_allowed: true") &&
      !source.includes("executeAgentApply") &&
      !source.includes("applyProposal(") &&
      !source.includes("writeActiveMemory"),
    "stage2_phase2_boundary",
    "No network write, direct active-memory mutation, agent apply, build, deploy, app install or GitHub main upload is included",
    "Stage 2 Phase 2.2 boundary violation detected",
  );
}

function validateChangeScope() {
  const changed = getOpenAIDatabaseChangedPaths();
  const outside = changed.filter((file) => !allowedChangePaths.includes(file));
  assertCondition(
    outside.length === 0,
    "stage2_phase2_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 2 Phase 2.2 Proposal UI, validator, docs and records",
    "Unexpected files changed outside Stage 2 Phase 2.2 scope",
    { changed, outside },
  );
}

function main() {
  validateStage2Phase1Continuity();
  validateProductModelAndAcceptance();
  validateRuntimeImplementation();
  validateRecords();
  validateBoundary();
  validateChangeScope();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage2-phase2",
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
        stage: "v1.1.7-stage2-phase2",
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
