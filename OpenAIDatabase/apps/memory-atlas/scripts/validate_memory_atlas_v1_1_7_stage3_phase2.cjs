#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S3P02";
const acceptanceId = "ACC-MA-V117-S3P02";
const status = "phase_3_2_home_detail_operations_completed_pending_stage3_review";
const validatorName = "validate:v1.1.7-stage3-phase2";
const stage3Phase1ValidatorName = "validate:v1.1.7-stage3-phase1";
const stage3Phase1ValidatorScript = "validate_memory_atlas_v1_1_7_stage3_phase1.cjs";
const operationVersion = "memory_overview_detail_operations.v1_1_7_stage3_phase2";
const actionSectionVersion = "top_actions_section.v1_1_7_stage3_phase2";
const assetSectionVersion = "level_assets_section.v1_1_7_stage3_phase2";
const themeSectionVersion = "theme_categories_section.v1_1_7_stage3_phase2";
const operationSections = ["top_actions", "level_assets", "theme_categories"];
const assetGroups = ["core_profile", "project", "decision", "temporary", "stale"];
const themeCategoryStates = ["rising", "declining", "conflict", "opportunity", "stable"];

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3_phase2.cjs",
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/docs/acceptance/memory_atlas_v1_1_7_stage3_phase2_home_detail_operations_acceptance.md",
  "OpenAIDatabase/docs/product/memory_overview_product_contract.md",
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

function validateStage3Phase1Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage3_phase2_open_diff_scope",
      "Open diff is limited to Stage 3 Phase 3.2 home detail operation files",
      "Unexpected files changed outside Stage 3 Phase 3.2 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", stage3Phase1ValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) &&
        packageJson.scripts?.[stage3Phase1ValidatorName] === `node scripts/${stage3Phase1ValidatorScript}`,
      "stage3_phase1_validator_registered_for_post_commit_run",
      "Stage 3 Phase 3.1 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 3 Phase 3.1 validator is missing or not registered",
      { script: packageJson.scripts?.[stage3Phase1ValidatorName] },
    );
    pass(
      "stage3_phase1_validator_deferred_until_clean_tree",
      "Stage 3 Phase 3.1 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${stage3Phase1ValidatorScript}`], { cwd: appRoot });
  const output = result.stdout.trim();
  const parsed = JSON.parse(output.slice(output.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S3P01",
    "stage3_phase1_validator",
    "Stage 3 Phase 3.1 validator returned PASS before Stage 3 Phase 3.2 acceptance",
    "Stage 3 Phase 3.1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateHomeOperationSource() {
  ["apps/memory-atlas/src/App.tsx", "apps/memory-atlas/src/styles.css", "apps/memory-atlas/package.json"].forEach(
    validateTextFile,
  );

  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");

  assertCondition(
    hasAll(app, [
      "MEMORY_OVERVIEW_OPERATION_VERSION",
      operationVersion,
      "HOME_ACTION_SECTION_VERSION",
      actionSectionVersion,
      "HOME_LEVEL_ASSET_SECTION_VERSION",
      assetSectionVersion,
      "HOME_THEME_CATEGORY_SECTION_VERSION",
      themeSectionVersion,
      "data-memory-overview-operations={MEMORY_OVERVIEW_OPERATION_VERSION}",
      "data-top-actions-section={HOME_ACTION_SECTION_VERSION}",
      "data-level-assets-section={HOME_LEVEL_ASSET_SECTION_VERSION}",
      "data-theme-categories-section={HOME_THEME_CATEGORY_SECTION_VERSION}",
      "data-next-action-status={action.status}",
      "data-next-action-detail-entry=\"ActionDetailDrawer\"",
      "data-tier-asset-detail-entry=\"AssetDetailPanel\"",
      "data-theme-category-detail-entry=\"ThemeDetailPanel\"",
      "ActionDetailDrawer",
      "AssetDetailPanel",
      "ThemeDetailPanel",
      "nextActionSortScore",
      "tierAssetSortScore",
      "topicClassificationSortScore",
    ]),
    "stage3_phase2_operation_source",
    "App.tsx records versioned top action, level asset and theme category operation sections",
    "App.tsx is missing the Stage 3 Phase 3.2 home operation source contract",
  );

  assertCondition(
    hasAll(app, operationSections.map((section) => `data-home-operation-section="${section}"`)),
    "stage3_phase2_operation_sections",
    "Every Stage 3 Phase 3.2 home operation section has a machine-readable marker",
    "One or more Stage 3 Phase 3.2 home operation section markers are missing",
  );

  assertCondition(
    hasAll(app, ["data-level-asset-group={group.id}"].concat(assetGroups.map((group) => `id: "${group}"`))),
    "stage3_phase2_asset_groups",
    "Level Assets section exposes core profile, project, decision, temporary and stale groups",
    "Level Assets section is missing required group markers",
  );

  assertCondition(
    hasAll(app, ["data-theme-category-state={state.id}"].concat(themeCategoryStates.map((state) => `id: "${state}"`))),
    "stage3_phase2_theme_categories",
    "Theme Categories section exposes rising, declining, conflict, opportunity and stable categories",
    "Theme Categories section is missing required state markers",
  );

  assertCondition(
    hasAll(styles, [
      ".home-section-summary-row",
      ".home-operation-chip",
      ".home-operation-chip strong",
      ".home-action-status",
      ".home-operation-chip-grid",
      "@media (max-width: 720px)",
    ]),
    "stage3_phase2_operation_styles",
    "styles.css includes compact responsive styling for Stage 3 Phase 3.2 operation chips",
    "styles.css is missing responsive operation-chip styling",
  );
}

function validateProductDocs() {
  const productPath = "docs/product/memory_overview_product_contract.md";
  const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage3_phase2_home_detail_operations_acceptance.md";
  [productPath, acceptancePath, "config/visualization/model_parameters.universe_state.yaml"].forEach(validateTextFile);

  const product = readRepoFile(productPath);
  const acceptance = readRepoFile(acceptancePath);
  const params = readRepoFile("config/visualization/model_parameters.universe_state.yaml");
  const requiredFragments = [
    operationVersion,
    actionSectionVersion,
    assetSectionVersion,
    themeSectionVersion,
    taskId,
    acceptanceId,
    status,
    validatorName,
    "Home Detail Operations",
    "Top Actions Section",
    "Level Assets Section",
    "Theme Categories Section",
    "clickable detail entry",
    "proposal-only",
    "suggestion",
    "reason",
    "priority",
    "status",
    "core_profile",
    "project",
    "decision",
    "temporary",
    "stale",
    "rising",
    "declining",
    "conflict",
    "opportunity",
    "stable",
    "ActionDetailDrawer",
    "AssetDetailPanel",
    "ThemeDetailPanel",
    "No Stage 3 Review",
    "No GitHub main upload",
  ];

  assertCondition(
    hasAll(product, requiredFragments),
    "stage3_phase2_product_contract",
    "Product contract captures the home detail operation sections, safety mode and boundaries",
    "Product contract is missing required Stage 3 Phase 3.2 fragments",
  );

  assertCondition(
    hasAll(acceptance, requiredFragments.concat(["App.tsx", "styles.css", "memory_overview_product_contract.md"])),
    "stage3_phase2_acceptance_doc",
    "Acceptance doc records implementation files, validation command and Stage 3.2 boundaries",
    "Acceptance doc is incomplete",
  );

  assertCondition(
    hasAll(params, [
      operationVersion,
      "home_detail_operations",
      "operation_sections",
      "asset_groups",
      "theme_category_states",
    ].concat(operationSections, assetGroups, themeCategoryStates)),
    "stage3_phase2_model_parameters",
    "Universe-state model parameters record the home detail operation contract",
    "Model parameters are missing Stage 3 Phase 3.2 home detail operation parameters",
  );
}

function validateRecords() {
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  const recordPaths = [
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3_phase2.cjs",
  ];

  recordPaths.forEach(validateTextFile);

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage3_phase2.cjs",
    "stage3_phase2_package_script",
    `package.json exposes ${validatorName}`,
    `package.json is missing ${validatorName}`,
    { script: packageJson.scripts?.[validatorName] },
  );

  for (const recordPath of recordPaths.slice(0, 6)) {
    const source = readRepoFile(recordPath);
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        operationVersion,
        "Home Detail Operations",
        "No Stage 3 Review",
        "No GitHub main upload",
      ]),
      `${recordPath}:stage3_phase2_record`,
      `${recordPath} records Stage 3 Phase 3.2 task, acceptance, status, validator and boundaries`,
      `${recordPath} is missing Stage 3 Phase 3.2 record fields`,
    );
  }
}

function main() {
  validateStage3Phase1Continuity();
  validateHomeOperationSource();
  validateProductDocs();
  validateRecords();

  console.log(
    JSON.stringify(
      {
        status: "PASS",
        task_id: taskId,
        acceptance_id: acceptanceId,
        phase_status: status,
        validator: validatorName,
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
        task_id: taskId,
        acceptance_id: acceptanceId,
        phase_status: status,
        validator: validatorName,
        error: error.message,
        details: error.details || {},
        stdout: error.stdout || "",
        stderr: error.stderr || "",
        checks,
      },
      null,
      2,
    ),
  );
  process.exit(1);
}
