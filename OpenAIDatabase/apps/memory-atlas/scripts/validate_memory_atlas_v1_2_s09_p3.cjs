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

const taskId = "MA-V12-S09P3";
const acceptanceId = "ACC-MA-V12-S09P3";
const status = "phase_s09_p3_decision_debt_completed_pending_s09_review";
const validatorName = "validate:v1.2-s09-p3";
const scriptName = "validate_memory_atlas_v1_2_s09_p3.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const configPath = "机器治理/行为智能模型/decision_debt.v1_2_s09_p3.json";
const builderPath = "scripts/build_memory_atlas_decision_debt.py";
const outputPath = "data/derived/behavior_intelligence/decision_debt_ledger.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s09_p3_decision_debt.md";
const humanPath = "人类可读/23_决策债说明.md";
const testPath = "tests/test_s09p3_decision_debt.py";

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const historicalValidatorPaths = [
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s09_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s09_p2.cjs",
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  ...historicalValidatorPaths,
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${configPath}`,
  `OpenAIDatabase/${builderPath}`,
  `OpenAIDatabase/${outputPath}`,
  `OpenAIDatabase/${reviewPath}`,
  `OpenAIDatabase/${humanPath}`,
  `OpenAIDatabase/${testPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/scripts/atlasctl.py",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/机器治理/README.md",
  "OpenAIDatabase/机器治理/数据契约/README.md",
  "OpenAIDatabase/机器治理/行为智能模型/README.md",
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
    "s09p3_package_script",
    "package.json exposes the v1.2 S09 P3 validator",
    "package.json is missing the v1.2 S09 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s09p3_previous_phase_deferred_scope",
      "S09 P2 execution is deferred only because open diff is limited to S09 P3 files and compatibility updates",
      "S09 P2 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s09p3_previous_phase_deferred_until_clean_tree", "S09 P2 validator will run on a clean tree after S09 P3 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s09_p2.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S09P2",
    "s09p3_previous_s09p2",
    "S09 P2 validator returns PASS before accepting S09 P3 on a clean tree",
    "S09 P2 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateDecisionDebtArtifacts() {
  [configPath, builderPath, outputPath, reviewPath, humanPath, testPath].forEach(validateTextFile);
  const config = readJson(configPath);
  const output = readJson(outputPath);
  const requiredFields = new Set(["decision_debt_id", "source_debt_ids", "debt_type", "decision_area_zh", "repeated_discussion_signal_zh", "evidence_refs", "minimal_next_step", "linked_self_iteration_suggestion_ids", "confidence", "not_pressure_list"]);
  const configuredFields = new Set(config.required_debt_fields || []);
  const missingConfigFields = [...requiredFields].filter((field) => !configuredFields.has(field));
  const ledger = Array.isArray(output.decision_debt_ledger) ? output.decision_debt_ledger : [];
  const badItems = [];
  const blockedTerms = config.blocked_output_terms || [];
  const maxConfidence = Number(config.confidence_policy?.max_confidence || 0.75);
  for (const item of ledger) {
    const itemId = item.decision_debt_id;
    for (const field of requiredFields) {
      if (item[field] === undefined || item[field] === null || item[field] === "" || (Array.isArray(item[field]) && item[field].length === 0)) {
        badItems.push(`${itemId}:missing_${field}`);
      }
    }
    if (Number(item.confidence || 0) > maxConfidence) badItems.push(`${itemId}:confidence_too_high`);
    if (item.not_pressure_list !== true) badItems.push(`${itemId}:pressure_list_boundary_missing`);
    if (item.not_psychological_diagnosis !== true) badItems.push(`${itemId}:psychological_boundary_missing`);
    if (item.not_personality_label !== true) badItems.push(`${itemId}:personality_boundary_missing`);
    if (item.not_applied !== true) badItems.push(`${itemId}:applied_in_current_phase`);
    const step = item.minimal_next_step || {};
    for (const field of ["step_zh", "expected_artifact_zh", "stop_condition_zh"]) {
      if (!String(step[field] || "").trim()) badItems.push(`${itemId}:minimal_next_step_missing_${field}`);
    }
    if (Number(step.effort_minutes_max || 0) <= 0) badItems.push(`${itemId}:minimal_next_step_invalid_effort`);
    const joined = [item.decision_area_zh, item.repeated_discussion_signal_zh, item.evidence_summary_zh, step.step_zh, step.stop_condition_zh].join(" ");
    if (blockedTerms.some((term) => term && joined.includes(term))) badItems.push(`${itemId}:blocked_term`);
  }
  const boundary = output.phase_boundary || {};
  const summary = output.safety_summary || {};
  assertCondition(
    config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      missingConfigFields.length === 0 &&
      config.ledger_policy?.pressure_list_allowed === false &&
      config.scope_boundary?.raw_mutation === false &&
      config.scope_boundary?.proposal_apply_execution === false &&
      config.scope_boundary?.stage_review === "deferred_to_s09_review" &&
      output.task_id === taskId &&
      output.acceptance_id === acceptanceId &&
      output.status === status &&
      output.decision_debt_count >= Number(config.ledger_policy?.min_entries || 3) &&
      ledger.length === output.decision_debt_count &&
      summary.all_items_have_minimal_next_step === true &&
      summary.pressure_list_created === false &&
      summary.proposal_apply_execution === false &&
      summary.raw_mutation === false &&
      summary.psychological_diagnosis_output === false &&
      summary.personality_label_output === false &&
      boundary.does_not_generate_pressure_list === true &&
      boundary.does_not_apply_proposals === true &&
      boundary.does_not_modify_raw === true &&
      boundary.next_phase === "S09 Review" &&
      badItems.length === 0,
    "s09p3_decision_debt_artifacts",
    "S09 P3 config and output contain minimal next steps, no pressure list and no-apply boundaries",
    "S09 P3 decision debt artifacts are incomplete",
    { missingConfigFields, decision_debt_count: output.decision_debt_count, badItems },
  );
}

function validateAtlasctl() {
  const python = process.env.PYTHON || "python3";
  const dryRun = parseJsonFromStdout(run(python, ["scripts/atlasctl.py", "analyze", "--stage", "decision-debt", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    dryRun.status === status && dryRun.dry_run === true && dryRun.writes_files === false && dryRun.task_id === taskId,
    "s09p3_atlasctl_decision_debt_dry_run",
    "atlasctl analyze --stage decision-debt --dry-run returns S09 P3 without writing files",
    "atlasctl decision-debt dry-run is invalid",
    { status: dryRun.status, writes_files: dryRun.writes_files },
  );
  const audit = parseJsonFromStdout(run(python, ["scripts/atlasctl.py", "audit", "--check", "decision-debt-safety"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    audit.status === "PASS" &&
      audit.bad_items?.length === 0 &&
      audit.decision_debt_count >= 3 &&
      audit.all_items_have_minimal_next_step === true &&
      audit.pressure_list_created === false &&
      audit.proposal_apply_execution === false &&
      audit.raw_mutation === false &&
      audit.psychological_diagnosis_output === false &&
      audit.personality_label_output === false,
    "s09p3_atlasctl_decision_debt_safety",
    "atlasctl audit --check decision-debt-safety returns PASS with no bad items",
    "atlasctl decision-debt-safety audit failed",
    audit,
  );
}

function validateDocsAndRecords() {
  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [taskId, acceptanceId, status, validatorName, outputPath, "minimal next step", "no pressure list", "pending S09 Review"]),
    "s09p3_review_doc",
    "S09 P3 review doc records acceptance fields, minimal next steps and no pressure list",
    "S09 P3 review doc is missing required fragments",
  );
  const human = readRepoFile(humanPath);
  const heavyTermCount = (human.match(/决策债|Decision Debt|压力清单|最小下一步|分析|验证/g) || []).length;
  assertCondition(
    hasAll(human, [outputPath, "8 条", "下一步只允许进入 S09 Review", "整体 S01-S14 全部完成前不上传 GitHub main"]) &&
      heavyTermCount <= 12,
    "s09p3_human_doc",
    "Human S09 P3 page is concise and does not overstack analysis terms",
    "Human S09 P3 page is missing required fragments or overuses analysis terms",
    { heavyTermCount },
  );
  for (const file of recordFiles) {
    const source = readRepoFile(file);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S09 P3", "pending S09 Review", "No GitHub main upload in this phase"]),
      `${file}:s09p3_record`,
      `${file} records S09 P3 status, acceptance, validator and no-upload boundary`,
      `${file} is missing S09 P3 record fragments`,
    );
  }
}

function validateCurrentStateDocs() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(quick, ["当前阶段是 S09 P3", taskId, acceptanceId, "下一步只允许进入 S09 Review"]) &&
      hasAll(overview, ["S09 P3 已完成", "decision_debt_ledger.json", "下一步是 S09 Review"]) &&
      hasAll(machine, ["当前为 S09 P3", taskId, validatorName, "下一步是 S09 Review"]) &&
      hasAll(dataContract, ["当前 S09 P3 已完成", "decision_debt_ledger.json", "下一步是 S09 Review"]) &&
      hasAll(behavior, ["当前 S09 P3 已完成", "decision_debt.v1_2_s09_p3.json", "decision_debt_ledger.json", "下一步是 S09 Review"]) &&
      hasAll(runGate, ["当前阶段是 S09 P3", taskId, acceptanceId, validatorName]),
    "s09p3_current_state_docs",
    "Current human and machine docs now point to S09 P3 and pending S09 Review",
    "Current state docs do not point to S09 P3",
  );
}

function validateBranchAndRemote() {
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s09p3_branch",
    "Current branch is either the local v1.2 stage branch or main for final reconciliation",
    "Current branch is not the approved S09 P3 branch",
    { branch },
  );
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s09p3_remote",
    "Origin remote is LinzeColin/CodexProject",
    "Origin remote is not LinzeColin/CodexProject",
    { remote },
  );
  const remoteBranch = spawnSync("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    encoding: "utf8",
    stdio: "pipe",
    timeout: 30000,
  });
  assertCondition(
    remoteBranch.status === 0 && remoteBranch.stdout.trim() === "",
    "s09p3_no_remote_branch",
    "No remote branch exists for the local S09 P3 work branch",
    "Remote branch exists or remote branch check failed",
    { status: remoteBranch.status, stdout: remoteBranch.stdout.trim(), stderr: remoteBranch.stderr.trim() },
  );
}

function validateOpenDiffScopeAndSafety() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s09p3_open_diff_scope",
    "Open diff is limited to S09 P3 files and historical-validator compatibility",
    "Open diff contains files outside S09 P3 allowed scope",
    { changed, outside },
  );
  const forbidden = changed.filter((file) =>
    file.includes("data/public_raw/") ||
    file.includes("data/raw/") ||
    /credential|secret|token|password|private_key|cookies/i.test(file)
  );
  assertCondition(
    forbidden.length === 0,
    "s09p3_no_raw_or_secret_diff",
    "S09 P3 open diff does not modify raw or secret/config files",
    "S09 P3 open diff modifies forbidden raw or secret-like files",
    { forbidden },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateDecisionDebtArtifacts();
    validateAtlasctl();
    validateDocsAndRecords();
    validateCurrentStateDocs();
    validateBranchAndRemote();
    validateOpenDiffScopeAndSafety();
    console.log(JSON.stringify({
      status: "PASS",
      task_id: taskId,
      acceptance_id: acceptanceId,
      validator: validatorName,
      checks,
    }, null, 2));
  } catch (error) {
    console.error(JSON.stringify({
      status: "FAIL",
      task_id: taskId,
      acceptance_id: acceptanceId,
      validator: validatorName,
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
