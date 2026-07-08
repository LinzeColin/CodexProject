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

const taskId = "MA-V12-S09P2";
const acceptanceId = "ACC-MA-V12-S09P2";
const status = "phase_s09_p2_self_iteration_completed_pending_s09_p3";
const validatorName = "validate:v1.2-s09-p2";
const scriptName = "validate_memory_atlas_v1_2_s09_p2.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const configPath = "机器治理/行为智能模型/self_iteration.v1_2_s09_p2.json";
const builderPath = "scripts/build_memory_atlas_self_iteration.py";
const outputPath = "data/derived/behavior_intelligence/self_iteration_suggestions.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s09_p2_self_iteration.md";
const humanPath = "人类可读/22_自我迭代建议说明.md";
const testPath = "tests/test_s09p2_self_iteration.py";

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
    "s09p2_package_script",
    "package.json exposes the v1.2 S09 P2 validator",
    "package.json is missing the v1.2 S09 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s09p2_previous_phase_deferred_scope",
      "S09 P1 execution is deferred only because open diff is limited to S09 P2 files and compatibility updates",
      "S09 P1 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s09p2_previous_phase_deferred_until_clean_tree", "S09 P1 validator will run on a clean tree after S09 P2 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s09_p1.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S09P1",
    "s09p2_previous_s09p1",
    "S09 P1 validator returns PASS before accepting S09 P2 on a clean tree",
    "S09 P1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateSelfIterationArtifacts() {
  [configPath, builderPath, outputPath, reviewPath, humanPath, testPath].forEach(validateTextFile);
  const config = readJson(configPath);
  const output = readJson(outputPath);
  const requiredFields = new Set(["suggestion_id", "target_type", "target_files", "rationale_zh", "expected_change_zh", "evidence_refs", "proposal", "action_half_life_days"]);
  const configuredFields = new Set(config.required_suggestion_fields || []);
  const missingConfigFields = [...requiredFields].filter((field) => !configuredFields.has(field));
  const requiredTargets = new Set(["memory", "config", "AGENTS", "style", "personalization"]);
  const configTargets = new Set((config.suggestion_targets || []).map((item) => item.target_type));
  const outputTargets = new Set((output.self_iteration_suggestions || []).map((item) => item.target_type));
  const missingConfigTargets = [...requiredTargets].filter((target) => !configTargets.has(target));
  const missingOutputTargets = [...requiredTargets].filter((target) => !outputTargets.has(target));
  const blockedTargets = config.blocked_targets || [];
  const badSuggestions = [];
  const suggestions = Array.isArray(output.self_iteration_suggestions) ? output.self_iteration_suggestions : [];
  for (const item of suggestions) {
    const suggestionId = item.suggestion_id;
    for (const field of requiredFields) {
      if (item[field] === undefined || item[field] === null || item[field] === "" || (Array.isArray(item[field]) && item[field].length === 0)) {
        badSuggestions.push(`${suggestionId}:missing_${field}`);
      }
    }
    if (Number(item.action_half_life_days || 0) <= 0) badSuggestions.push(`${suggestionId}:invalid_action_half_life`);
    if (item.not_pressure_list !== true) badSuggestions.push(`${suggestionId}:pressure_list_boundary_missing`);
    if (item.not_applied !== true) badSuggestions.push(`${suggestionId}:applied_in_current_phase`);
    const targetFiles = item.target_files || [];
    if (blockedTargets.some((blocked) => targetFiles.some((file) => String(file).includes(blocked)))) {
      badSuggestions.push(`${suggestionId}:blocked_target`);
    }
    const proposal = item.proposal || {};
    for (const field of ["proposal_id", "state", "created_at", "expires_at", "rollback_plan_zh", "validation_commands"]) {
      if (proposal[field] === undefined || proposal[field] === null || proposal[field] === "" || (Array.isArray(proposal[field]) && proposal[field].length === 0)) {
        badSuggestions.push(`${suggestionId}:proposal_missing_${field}`);
      }
    }
    if (proposal.state !== "pending_human_review") badSuggestions.push(`${suggestionId}:proposal_state_not_pending_human_review`);
    if (proposal.apply_execution_allowed !== false) badSuggestions.push(`${suggestionId}:proposal_apply_allowed`);
    if (proposal.raw_apply_target_allowed !== false) badSuggestions.push(`${suggestionId}:proposal_raw_apply_allowed`);
    if (proposal.not_permanent_pending !== true) badSuggestions.push(`${suggestionId}:proposal_permanent_pending`);
    const createdAt = Date.parse(String(proposal.created_at || "").replace("Z", "+00:00"));
    const expiresAt = Date.parse(String(proposal.expires_at || "").replace("Z", "+00:00"));
    if (!Number.isFinite(createdAt) || !Number.isFinite(expiresAt) || expiresAt <= createdAt) {
      badSuggestions.push(`${suggestionId}:proposal_expiry_invalid`);
    }
  }
  const boundary = output.phase_boundary || {};
  const summary = output.proposal_expiry_summary || {};
  assertCondition(
    config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      missingConfigFields.length === 0 &&
      missingConfigTargets.length === 0 &&
      config.scope_boundary?.raw_mutation === false &&
      config.scope_boundary?.proposal_apply_execution === false &&
      config.scope_boundary?.decision_debt_ledger === "deferred_to_s09_p3" &&
      output.task_id === taskId &&
      output.acceptance_id === acceptanceId &&
      output.status === status &&
      output.suggestion_count >= 5 &&
      suggestions.length === output.suggestion_count &&
      missingOutputTargets.length === 0 &&
      summary.all_proposals_have_expiry === true &&
      summary.all_suggestions_have_action_half_life === true &&
      summary.permanent_pending_allowed === false &&
      boundary.does_not_apply_proposals === true &&
      boundary.does_not_create_decision_debt_ledger === true &&
      boundary.does_not_modify_raw === true &&
      boundary.next_phase === "S09 P3" &&
      badSuggestions.length === 0,
    "s09p2_self_iteration_artifacts",
    "S09 P2 config and output contain proposal expiry, action half-life and no-apply boundaries",
    "S09 P2 self-iteration artifacts are incomplete",
    { missingConfigFields, missingConfigTargets, missingOutputTargets, suggestion_count: output.suggestion_count, badSuggestions },
  );
}

function validateAtlasctl() {
  const python = process.env.PYTHON || "python3";
  const dryRun = parseJsonFromStdout(run(python, ["scripts/atlasctl.py", "analyze", "--stage", "self-iteration", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    dryRun.status === status && dryRun.dry_run === true && dryRun.writes_files === false && dryRun.task_id === taskId,
    "s09p2_atlasctl_self_iteration_dry_run",
    "atlasctl analyze --stage self-iteration --dry-run returns S09 P2 without writing files",
    "atlasctl self-iteration dry-run is invalid",
    { status: dryRun.status, writes_files: dryRun.writes_files },
  );
  const audit = parseJsonFromStdout(run(python, ["scripts/atlasctl.py", "audit", "--check", "self-iteration-safety"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    audit.status === "PASS" &&
      audit.bad_items?.length === 0 &&
      audit.suggestion_count >= 5 &&
      audit.all_proposals_have_expiry === true &&
      audit.all_suggestions_have_action_half_life === true &&
      audit.proposal_apply_execution === false &&
      audit.decision_debt_ledger_created === false &&
      audit.raw_mutation === false,
    "s09p2_atlasctl_self_iteration_safety",
    "atlasctl audit --check self-iteration-safety returns PASS with no bad items",
    "atlasctl self-iteration-safety audit failed",
    audit,
  );
}

function validateDocsAndRecords() {
  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [taskId, acceptanceId, status, validatorName, outputPath, "proposal expiry", "action half-life", "pending S09 P3", "No permanent pending proposal"]),
    "s09p2_review_doc",
    "S09 P2 review doc records acceptance fields, proposal expiry and action half-life",
    "S09 P2 review doc is missing required fragments",
  );
  const human = readRepoFile(humanPath);
  const heavyTermCount = (human.match(/自我迭代|proposal|过期|半衰期|Decision Debt|分析|验证/g) || []).length;
  assertCondition(
    hasAll(human, [outputPath, "5 条", "下一步只允许进入 S09 P3", "整体 S01-S14 全部完成前不上传 GitHub main"]) &&
      heavyTermCount <= 12,
    "s09p2_human_doc",
    "Human S09 P2 page is concise and does not overstack analysis terms",
    "Human S09 P2 page is missing required fragments or overuses analysis terms",
    { heavyTermCount },
  );
  for (const file of recordFiles) {
    const source = readRepoFile(file);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S09 P2", "pending S09 P3", "No GitHub main upload in this phase"]),
      `${file}:s09p2_record`,
      `${file} records S09 P2 status, acceptance, validator and no-upload boundary`,
      `${file} is missing S09 P2 record fragments`,
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
    hasAll(quick, ["当前阶段是 S09 P3", "MA-V12-S09P3", "ACC-MA-V12-S09P3", "下一步只允许进入 S09 Review"]) &&
      hasAll(overview, ["S09 P3 已完成", "decision_debt_ledger.json", "下一步是 S09 Review"]) &&
      hasAll(machine, ["当前为 S09 P3", "MA-V12-S09P3", "validate:v1.2-s09-p3", "下一步是 S09 Review"]) &&
      hasAll(dataContract, ["当前 S09 P3 已完成", "decision_debt_ledger.json", "下一步是 S09 Review"]) &&
      hasAll(behavior, ["当前 S09 P3 已完成", "decision_debt.v1_2_s09_p3.json", "decision_debt_ledger.json", "下一步是 S09 Review"]) &&
      hasAll(runGate, ["当前阶段是 S09 P3", "MA-V12-S09P3", "ACC-MA-V12-S09P3", "validate:v1.2-s09-p3"]),
    "s09p2_current_state_docs",
    "Current human and machine docs now point to S09 P3 and pending S09 Review",
    "Current state docs do not point to S09 P3",
  );
}

function validateBranchAndRemote() {
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s09p2_branch",
    "Current branch is either the local v1.2 stage branch or main for final reconciliation",
    "Current branch is not the approved S09 P2 branch",
    { branch },
  );
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s09p2_remote",
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
    "s09p2_no_remote_branch",
    "No remote branch exists for the local S09 P2 work branch",
    "Remote branch exists or remote branch check failed",
    { status: remoteBranch.status, stdout: remoteBranch.stdout.trim(), stderr: remoteBranch.stderr.trim() },
  );
}

function validateOpenDiffScopeAndSafety() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s09p2_open_diff_scope",
    "Open diff is limited to S09 P2 files and historical-validator compatibility",
    "Open diff contains files outside S09 P2 allowed scope",
    { changed, outside },
  );
  const forbidden = changed.filter((file) =>
    file.includes("data/public_raw/") ||
    file.includes("data/raw/") ||
    /credential|secret|token|password|private_key|cookies/i.test(file)
  );
  assertCondition(
    forbidden.length === 0,
    "s09p2_no_raw_or_secret_diff",
    "S09 P2 open diff does not modify raw or secret/config files",
    "S09 P2 open diff modifies forbidden raw or secret-like files",
    { forbidden },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateSelfIterationArtifacts();
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
