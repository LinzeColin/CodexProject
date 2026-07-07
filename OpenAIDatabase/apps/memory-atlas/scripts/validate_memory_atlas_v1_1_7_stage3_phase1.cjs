#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-S3P01";
const acceptanceId = "ACC-MA-V117-S3P01";
const status = "phase_3_1_default_home_structure_completed_pending_stage3_review";
const validatorName = "validate:v1.1.7-stage3-phase1";
const stage2ValidatorName = "validate:v1.1.7-stage2";
const stage2ValidatorScript = "validate_memory_atlas_v1_1_7_stage2.cjs";
const structureVersion = "memory_overview_default_home.v1_1_7_stage3_phase1";
const sectionIds = [
  "status_summary",
  "suggested_actions",
  "weather",
  "black_holes",
  "proto_stars",
  "assets",
  "themes",
  "entry_points",
];

const allowedChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3_phase1.cjs",
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/docs/acceptance/memory_atlas_v1_1_7_stage3_phase1_default_home_acceptance.md",
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

function validateStage2Continuity() {
  const changed = getOpenAIDatabaseChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "stage3_phase1_open_diff_scope",
      "Open diff is limited to Stage 3 Phase 3.1 default home structure files",
      "Unexpected files changed outside Stage 3 Phase 3.1 scope",
      { changed, outside },
    );

    const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
    const scriptPath = path.join(appRoot, "scripts", stage2ValidatorScript);
    assertCondition(
      fs.existsSync(scriptPath) && packageJson.scripts?.[stage2ValidatorName] === `node scripts/${stage2ValidatorScript}`,
      "stage2_validator_registered_for_post_commit_run",
      "Stage 2 validator exists and is registered for clean-tree execution after this phase is committed",
      "Stage 2 validator is missing or not registered",
      { script: packageJson.scripts?.[stage2ValidatorName] },
    );
    pass(
      "stage2_validator_deferred_until_clean_tree",
      "Stage 2 validator enforces its own changed-path scope; run this validator again after commit to execute it on a clean tree",
      { changed },
    );
    return;
  }

  const result = run("node", [`scripts/${stage2ValidatorScript}`], { cwd: appRoot });
  const output = result.stdout.trim();
  const parsed = JSON.parse(output.slice(output.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V117-S2-REVIEW",
    "stage2_validator",
    "Stage 2 review validator returned PASS before Stage 3 Phase 3.1 acceptance",
    "Stage 2 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateDefaultHomeSource() {
  ["apps/memory-atlas/src/App.tsx", "apps/memory-atlas/src/styles.css", "apps/memory-atlas/package.json"].forEach(
    validateTextFile,
  );

  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");

  assertCondition(
    hasAll(app, [
      "DEFAULT_MEMORY_ATLAS_VIEW",
      'DEFAULT_MEMORY_ATLAS_VIEW: ViewKey = "home"',
      "MEMORY_OVERVIEW_STRUCTURE_VERSION",
      structureVersion,
      "MEMORY_OVERVIEW_SECTION_ORDER",
      "activeView: DEFAULT_MEMORY_ATLAS_VIEW",
      "data-memory-overview-default-route=\"true\"",
      "data-default-route-view={DEFAULT_MEMORY_ATLAS_VIEW}",
      "data-memory-overview-structure={MEMORY_OVERVIEW_STRUCTURE_VERSION}",
      "data-home-section-anchor={section.id}",
      "activeView === \"home\"",
      "HomeOverviewView",
      "data-memory-weather-v2=\"true\"",
      "overview.nextBestActionsTitle",
      "home-preview-grid",
      "home-inspector-link-list",
      "home-tier-asset-panel",
      "home-topic-detail-panel",
    ].concat(sectionIds.map((id) => `id: "${id}"`))),
    "stage3_phase1_default_home_source",
    "App.tsx records a versioned default home route and the required Memory Overview structure sections",
    "App.tsx is missing the Stage 3 Phase 3.1 default home structure contract",
  );

  assertCondition(
    hasAll(app, sectionIds.map((id) => `data-home-section="${id}"`)),
    "stage3_phase1_section_surfaces",
    "Every required Memory Overview section has a machine-readable surface marker",
    "One or more required Memory Overview sections are missing data-home-section markers",
  );

  assertCondition(
    hasAll(styles, [
      ".home-structure-rail",
      ".home-structure-rail span",
      ".home-structure-rail span::before",
      "@media (max-width: 760px)",
    ]),
    "stage3_phase1_structure_styles",
    "styles.css includes compact responsive styling for the default-home structure rail",
    "styles.css is missing responsive structure-rail styling",
  );
}

function validateProductDocs() {
  const productPath = "docs/product/memory_overview_product_contract.md";
  const acceptancePath = "docs/acceptance/memory_atlas_v1_1_7_stage3_phase1_default_home_acceptance.md";
  [productPath, acceptancePath, "config/visualization/model_parameters.universe_state.yaml"].forEach(validateTextFile);

  const product = readRepoFile(productPath);
  const acceptance = readRepoFile(acceptancePath);
  const params = readRepoFile("config/visualization/model_parameters.universe_state.yaml");
  const requiredFragments = [
    structureVersion,
    taskId,
    acceptanceId,
    status,
    validatorName,
    "Default Home Structure",
    "default route",
    "status summary",
    "suggested actions",
    "weather",
    "black holes",
    "proto-stars",
    "assets",
    "themes",
    "entry points",
    "not a pile of cards",
    "core 4 sections",
    "No Stage 3 Phase 3.2",
    "No GitHub main upload",
  ].concat(sectionIds);

  assertCondition(
    hasAll(product, requiredFragments),
    "stage3_phase1_product_contract",
    "Product contract captures the default-home IA, anti-card-pile rule, rollback and boundaries",
    "Product contract is missing required Stage 3 Phase 3.1 fragments",
  );

  assertCondition(
    hasAll(acceptance, requiredFragments.concat(["App.tsx", "styles.css", "memory_overview_product_contract.md"])),
    "stage3_phase1_acceptance_doc",
    "Acceptance doc records implementation files, validation command and Stage 3.1 boundaries",
    "Acceptance doc is incomplete",
  );

  assertCondition(
    hasAll(params, [
      structureVersion,
      "default_home_structure",
      "default_view: home",
      "structure_sections",
    ].concat(sectionIds)),
    "stage3_phase1_model_parameters",
    "Universe-state model parameters record the default-home structure contract",
    "Model parameters are missing Stage 3 Phase 3.1 default-home structure parameters",
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
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3_phase1.cjs",
  ];

  recordPaths.forEach(validateTextFile);

  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_stage3_phase1.cjs",
    "stage3_phase1_package_script",
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
        structureVersion,
        "Default Home Structure",
        "No Stage 3 Phase 3.2",
        "No GitHub main upload",
      ]),
      `${recordPath}:stage3_phase1_record`,
      `${recordPath} records Stage 3 Phase 3.1 task, acceptance, status, validator and boundaries`,
      `${recordPath} is missing Stage 3 Phase 3.1 record fields`,
    );
  }
}

function main() {
  validateStage2Continuity();
  validateDefaultHomeSource();
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
