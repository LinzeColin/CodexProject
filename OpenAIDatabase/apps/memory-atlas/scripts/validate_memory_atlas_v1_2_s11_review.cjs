#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

process.env.GIT_TERMINAL_PROMPT = process.env.GIT_TERMINAL_PROMPT || "0";
process.env.GIT_SSH_COMMAND =
  process.env.GIT_SSH_COMMAND || "ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=5 -o ServerAliveCountMax=1";

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S11-REVIEW";
const acceptanceId = "ACC-MA-V12-S11-REVIEW";
const status = "stage_s11_review_passed_pending_s12_no_github_main_upload";
const validatorName = "validate:v1.2-s11-review";
const scriptName = "validate_memory_atlas_v1_2_s11_review.cjs";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s11_review.md";

const phaseValidators = [
  ["validate:v1.2-s11-p1", "validate_memory_atlas_v1_2_s11_p1.cjs", "MA-V12-S11P1", "ACC-MA-V12-S11P1"],
  ["validate:v1.2-s11-p2", "validate_memory_atlas_v1_2_s11_p2.cjs", "MA-V12-S11P2", "ACC-MA-V12-S11P2"],
  ["validate:v1.2-s11-p3", "validate_memory_atlas_v1_2_s11_p3.cjs", "MA-V12-S11P3", "ACC-MA-V12-S11P3"],
  ["validate:v1.2-s11-p4", "validate_memory_atlas_v1_2_s11_p4.cjs", "MA-V12-S11P4", "ACC-MA-V12-S11P4"],
];

const requiredVisualIds = [
  "cluster_tree",
  "bubble_map",
  "topic_cluster_explorer",
  "task_treemap",
  "automation_vs_augmentation",
  "roi_scatter",
  "opportunity_radar",
  "agent_decision_sankey",
  "friction_heatmap",
  "latent_radar",
  "evidence_timeline",
  "formula_explorer",
];

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const textFiles = [
  reviewPath,
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
  "机器治理/README.md",
  "机器治理/可视化配置/README.md",
  "机器治理/运行门禁/README.md",
  ...recordFiles,
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s11_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s11_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s11_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s11_p4.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  "OpenAIDatabase/机器治理/可视化配置/clio_like_visuals.v1_2_s11_p1.json",
  "OpenAIDatabase/机器治理/可视化配置/economic_like_visuals.v1_2_s11_p2.json",
  "OpenAIDatabase/机器治理/可视化配置/workflow_latent_governance_visuals.v1_2_s11_p3.json",
  "OpenAIDatabase/机器治理/可视化配置/human_question_map.v1_2_s11_p4.json",
  "OpenAIDatabase/机器治理/可视化配置/README.md",
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/机器治理/README.md",
  "OpenAIDatabase/机器治理/运行门禁/README.md",
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

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: "utf8",
    stdio: "pipe",
    maxBuffer: 128 * 1024 * 1024,
    timeout: options.timeout || 0,
  });
  if (result.status !== 0) {
    const reason = result.error?.code === "ETIMEDOUT" ? " timed out" : "";
    const error = new Error(`${command} ${args.join(" ")} failed${reason} with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function parseJsonFromStdout(result) {
  const stdout = result.stdout.trim();
  return JSON.parse(stdout.slice(stdout.indexOf("{")));
}

function readRepoFile(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), "utf8");
}

function readJson(relativePath) {
  return JSON.parse(readRepoFile(relativePath));
}

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
}

function getOpenChangedPaths() {
  const result = run("git", ["-c", "core.quotepath=false", "status", "--short", "--untracked-files=all", "--", "OpenAIDatabase"], {
    cwd: worktreeRoot,
  });
  return result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .sort();
}

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s11_review_open_diff_scope",
    "Open diff is limited to S11 Review files and S11 review fix surfaces",
    "S11 Review has unrelated OpenAIDatabase changes",
    { changed, outside, allowedOpenDiffPaths },
  );
}

function validateTextFile(relativePath) {
  const source = readRepoFile(relativePath);
  assertCondition(source.endsWith("\n"), `${relativePath}:final_newline`, `${relativePath} has a final newline`, `${relativePath} is missing a final newline`);
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

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s11_review_package_script",
    "package.json exposes the v1.2 S11 Review validator",
    "package.json is missing the v1.2 S11 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateReviewArtifact() {
  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      "validate:v1.2-s11-p1",
      "validate:v1.2-s11-p2",
      "validate:v1.2-s11-p3",
      "validate:v1.2-s11-p4",
      "P0 图谱集合",
      "中文问题和行动说明",
      "source/time/project/task",
      "不是静态装饰图",
      "Visual ROI Gate",
      "行为、ROI、协作、潜性、证据、治理",
      "No GitHub main upload",
      "No remote push",
      "No raw mutation",
      "No proposal apply execution",
      "pending S12 P1",
      ...requiredVisualIds,
    ]),
    "s11_review_artifact",
    "S11 Review artifact records phase chain, visual pass gate, all P0 visual ids, boundaries and pending S12 P1",
    "S11 Review artifact is missing required review evidence",
  );
}

function validatePhaseValidators() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  const details = {};
  for (const [script, file, phaseTaskId, phaseAcceptanceId] of phaseValidators) {
    assertCondition(
      packageJson.scripts?.[script] === `node scripts/${file}`,
      `s11_review_phase_script_${script}`,
      `${script} is registered`,
      `${script} is missing from package.json`,
      { script: packageJson.scripts?.[script] },
    );
    const result = parseJsonFromStdout(run("node", [`scripts/${file}`], { cwd: appRoot, timeout: 180000 }));
    details[script] = {
      status: result.status,
      task_id: result.task_id,
      acceptance_id: result.acceptance_id,
    };
    assertCondition(
      result.status === "PASS" && result.task_id === phaseTaskId && result.acceptance_id === phaseAcceptanceId,
      `s11_review_phase_gate_${script}`,
      `${script} passes with expected task and acceptance ids`,
      `${script} did not pass with expected task and acceptance ids`,
      details[script],
    );
  }
  pass("s11_review_phase_validator_chain", "S11 P1/P2/P3/P4 validators pass in sequence", details);
}

function validateRuntimeAndConfigs() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  assertCondition(
    hasAll(app, [
      "__memoryAtlasS11Phase1",
      "__memoryAtlasS11Phase2",
      "__memoryAtlasS11Phase3",
      "__memoryAtlasS11Phase4",
      "data-s11-p1-clio-like-visuals",
      "data-s11-p2-economic-like-visuals",
      "data-s11-p3-workflow-latent-governance-visuals",
      "data-s11-p4-human-question-map",
      "source/time/project/task",
    ]),
    "s11_review_runtime_chain",
    "App.tsx exposes S11 P1-P4 runtime contracts and shared filter semantics",
    "App.tsx is missing part of the S11 runtime chain",
  );
  const configs = [
    ["机器治理/可视化配置/clio_like_visuals.v1_2_s11_p1.json", 3],
    ["机器治理/可视化配置/economic_like_visuals.v1_2_s11_p2.json", 4],
    ["机器治理/可视化配置/workflow_latent_governance_visuals.v1_2_s11_p3.json", 5],
    ["机器治理/可视化配置/human_question_map.v1_2_s11_p4.json", 12],
  ];
  const summary = {};
  for (const [relativePath, expectedCount] of configs) {
    const config = readJson(relativePath);
    const visuals = Array.isArray(config.visuals) ? config.visuals : [];
    const invalid = visuals.filter((visual) => {
      const filters = Array.isArray(visual.filter_dimensions) ? visual.filter_dimensions : [];
      return (
        !visual.id ||
        !visual.insight_header_zh ||
        !(visual.human_question_zh || visual.human_question) ||
        !(visual.action_value_zh || visual.action) ||
        visual.visual_roi_gate_pass !== true ||
        visual.static_decoration === true ||
        !["source", "time", "project", "task"].every((dimension) => filters.includes(dimension))
      );
    });
    summary[relativePath] = { visualCount: visuals.length, invalid: invalid.map((visual) => visual.id) };
    assertCondition(
      visuals.length === expectedCount && invalid.length === 0,
      `s11_review_config_${path.basename(relativePath, ".json")}`,
      `${relativePath} has expected visual count, questions, actions, filters and ROI gate pass flags`,
      `${relativePath} does not satisfy S11 review visual contract`,
      summary[relativePath],
    );
  }
  const p4 = readJson("机器治理/可视化配置/human_question_map.v1_2_s11_p4.json");
  const excluded = Array.isArray(p4.excluded_candidates) ? p4.excluded_candidates : [];
  const forbiddenP0 = excluded.filter((candidate) => candidate.visual_roi_gate_pass !== false || candidate.p0_included !== false);
  assertCondition(
    excluded.length >= 2 && forbiddenP0.length === 0,
    "s11_review_visual_roi_exclusions",
    "S11 P4 records Visual ROI Gate failures and keeps them out of P0",
    "S11 P4 does not prove failed Visual ROI candidates stay out of P0",
    { excludedCount: excluded.length, forbiddenP0 },
  );
}

function validateVisualAudits() {
  const visualRoi = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "audit", "--check", "visual-roi"], { cwd: repoRoot }));
  assertCondition(
    visualRoi.status === "PASS" && visualRoi.check === "visual-roi" && visualRoi.failed_p0_count === 0,
    "s11_review_visual_roi_audit",
    "atlasctl visual-roi audit passes with no failed P0 visuals",
    "atlasctl visual-roi audit does not pass for S11 Review",
    visualRoi,
  );
  const visual = parseJsonFromStdout(run("python3", ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", "."], { cwd: repoRoot, timeout: 180000 }));
  assertCondition(
    visual.status === "PASS",
    "s11_review_visual_acceptance_audit",
    "Visual acceptance audit passes after S11 P1-P4",
    "Visual acceptance audit does not pass after S11 P1-P4",
    { status: visual.status },
  );
}

function validateRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    "S11 P1",
    "S11 P2",
    "S11 P3",
    "S11 P4",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "No proposal apply",
    "S12 P1",
  ];
  for (const relativePath of recordFiles) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s11_review_records_${relativePath}`,
      `${relativePath} records S11 Review status, validator, boundaries and next phase`,
      `${relativePath} is missing S11 Review record fragments`,
      { missing },
    );
  }
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(quickEntry, [taskId, "S11 Review 已完成", "下一步是 S12 P1", "No GitHub main upload"]),
    "s11_review_quick_entry",
    "Quick entry records completed S11 Review and pending S12 P1",
    "Quick entry does not record completed S11 Review",
  );
  assertCondition(
    hasAll(overview, ["S11 Review 已完成", "P0 图谱集合", "Visual ROI Gate", "下一步是 S12 P1"]),
    "s11_review_overview",
    "Human overview records S11 Review pass gate and pending S12 P1",
    "Human overview is missing S11 Review pass gate",
  );
  assertCondition(
    hasAll(machineReadme, [taskId, acceptanceId, status, validatorName, "S12 P1"]),
    "s11_review_machine_readme",
    "Machine README records S11 Review gate and next phase",
    "Machine README is missing S11 Review gate",
  );
  assertCondition(
    hasAll(runGate, [taskId, acceptanceId, status, validatorName, "S11 Review 产物", "S12 P1"]),
    "s11_review_run_gate",
    "Run gate README records S11 Review artifact, validator and next phase",
    "Run gate README is missing S11 Review gate",
  );
}

function validateNoRawOrForbiddenChanges() {
  const changed = getOpenChangedPaths();
  const forbiddenOpenChanges = changed.filter(
    (file) =>
      file.includes("/data/raw/") ||
      file.includes("/data/private_imports/") ||
      file.includes("/data/raw_encrypted/") ||
      file.endsWith(".env") ||
      file.includes("secrets") ||
      file.includes("credentials"),
  );
  const publicRawDiff = run("git", ["diff", "--", "OpenAIDatabase/data/public_raw", "OpenAIDatabase/data/raw"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    forbiddenOpenChanges.length === 0 && publicRawDiff.length === 0,
    "s11_review_no_raw_or_secret_open_changes",
    "S11 Review open diff does not modify raw, private imports, credentials or secrets",
    "S11 Review has forbidden raw or secret changes",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    for (const file of textFiles) validateTextFile(file);
    validateReviewArtifact();
    validatePhaseValidators();
    validateRuntimeAndConfigs();
    validateVisualAudits();
    validateRecords();
    validateNoRawOrForbiddenChanges();
    console.log(JSON.stringify({ status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.error(JSON.stringify({
      status: "FAIL",
      validator: scriptName.replace(/\.cjs$/, ""),
      task_id: taskId,
      acceptance_id: acceptanceId,
      error: error.message,
      details: error.details || {},
      stdout: error.stdout,
      stderr: error.stderr,
      checks,
    }, null, 2));
    process.exit(1);
  }
}

main();
