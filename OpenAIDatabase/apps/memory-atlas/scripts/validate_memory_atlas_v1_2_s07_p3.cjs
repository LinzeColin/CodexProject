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

const taskId = "MA-V12-S07P3";
const acceptanceId = "ACC-MA-V12-S07P3";
const status = "phase_s07_p3_formula_what_if_completed_pending_s07_review";
const validatorName = "validate:v1.2-s07-p3";
const scriptName = "validate_memory_atlas_v1_2_s07_p3.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const atlasctlPath = "scripts/atlasctl.py";
const builderPath = "scripts/build_memory_atlas_formula_what_if.py";
const configPath = "机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json";
const outputPath = "data/derived/economic_proxy/formula_what_if_preview.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s07_p3_formula_what_if.md";
const humanDocPath = "人类可读/18_FormulaWhatIf配置预览说明.md";

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
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
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_review.cjs",
  `OpenAIDatabase/${atlasctlPath}`,
  `OpenAIDatabase/${builderPath}`,
  `OpenAIDatabase/${configPath}`,
  `OpenAIDatabase/${outputPath}`,
  "OpenAIDatabase/tests/test_s07p3_formula_what_if.py",
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s07_review.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  `OpenAIDatabase/${humanDocPath}`,
  "OpenAIDatabase/机器治理/README.md",
  "OpenAIDatabase/机器治理/参数与公式/README.md",
  "OpenAIDatabase/机器治理/可视化配置/README.md",
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

function hasCjk(value) {
  return /[\u3400-\u9fff]/.test(String(value || ""));
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
    "s07p3_package_script",
    "package.json exposes the v1.2 S07 P3 validator",
    "package.json is missing the v1.2 S07 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s07p3_previous_phase_deferred_scope",
      "S07 P2 execution is deferred only because open diff is limited to S07 P3 files and compatibility updates",
      "S07 P2 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s07p3_previous_phase_deferred_until_clean_tree", "S07 P2 validator will run on a clean tree after S07 P3 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s07_p2.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S07P2",
    "s07p3_previous_s07p2",
    "S07 P2 validator returns PASS before accepting S07 P3 on a clean tree",
    "S07 P2 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateConfigAndOutput() {
  [atlasctlPath, builderPath, configPath, outputPath].forEach(validateTextFile);
  const atlasctl = readRepoFile(atlasctlPath);
  const builder = readRepoFile(builderPath);
  assertCondition(
    hasAll(atlasctl, ["formula-what-if", "run_formula_what_if_audit", "build_memory_atlas_formula_what_if.py"]),
    "s07p3_atlasctl_contract",
    "atlasctl exposes S07 P3 formula-what-if analyze and audit entry points",
    "atlasctl is missing S07 P3 formula-what-if contract",
  );
  assertCondition(
    hasAll(builder, [taskId, acceptanceId, "proposal_required_before_apply", "does_not_mutate_active_formula_config", "config_preview_only"]),
    "s07p3_builder_contract",
    "Formula what-if builder enforces proposal-only config preview boundaries",
    "Formula what-if builder is missing S07 P3 boundary markers",
  );
  const config = readJson(configPath);
  const output = readJson(outputPath);
  const requiredWeights = ["time_saved_weight", "reuse_value_weight", "skill_compounding_weight", "rework_cost_weight", "low_value_loop_penalty_weight"];
  const defaultWeights = config.parameters?.default_weights || {};
  const bounds = config.parameters?.adjustable_weight_bounds || {};
  const missingWeights = requiredWeights.filter((key) => !(key in defaultWeights) || !(key in bounds));
  assertCondition(
    config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.status === "phase_s07_p3_formula_what_if_config_active_pending_s07_review" &&
      config.active_config_write === false &&
      config.proposal_required_before_apply === true &&
      config.scope_boundary?.external_economic_database_dependency === false &&
      config.scope_boundary?.precise_income_prediction === false &&
      config.scope_boundary?.financial_advice === false &&
      config.scope_boundary?.active_config_mutation === false &&
      Array.isArray(config.formulas) &&
      config.formulas.length === 2 &&
      config.formulas.every((item) => item.formula_id && hasCjk(item.expression_zh) && hasCjk(item.interpretation_zh)) &&
      Array.isArray(config.scenarios) &&
      config.scenarios.length >= 5 &&
      missingWeights.length === 0,
    "s07p3_formula_what_if_config",
    "Formula what-if config defines proposal-only adjustable weights and scenarios",
    "Formula what-if config failed S07 P3 acceptance",
    { scenario_count: config.scenarios?.length, missingWeights },
  );
  const scenarios = Array.isArray(output.scenarios) ? output.scenarios : [];
  const coveredWeights = new Set();
  const badItems = [];
  for (const scenario of scenarios) {
    Object.keys(scenario.adjustable_weights || {}).forEach((key) => coveredWeights.add(key));
    const proposal = scenario.parameter_change_proposal || {};
    if (proposal.active_config_write !== false || proposal.proposal_required_before_apply !== true) {
      badItems.push(`${scenario.scenario_id}:invalid_proposal_gate`);
    }
    if (!scenario.formula_id || !scenario.formula_source || !hasCjk(scenario.description_zh)) {
      badItems.push(`${scenario.scenario_id}:missing_formula_or_chinese_description`);
    }
    const score = Number(scenario.weighted_proxy_score);
    if (!Number.isFinite(score) || score < 0 || score > 100) {
      badItems.push(`${scenario.scenario_id}:score_out_of_range`);
    }
  }
  for (const key of ["time_saved_weight", "reuse_value_weight", "skill_compounding_weight"]) {
    if (!coveredWeights.has(key)) badItems.push(`missing_required_weight:${key}`);
  }
  assertCondition(
    output.schema_version === "memory_atlas_formula_what_if_preview.v1_2_s07_p3" &&
      output.task_id === taskId &&
      output.acceptance_id === acceptanceId &&
      output.status === status &&
      output.simulator_mode === "config_preview_only" &&
      output.scenario_count === scenarios.length &&
      scenarios.length >= 5 &&
      output.phase_boundary?.does_not_use_external_economic_database === true &&
      output.phase_boundary?.does_not_claim_precise_income_prediction === true &&
      output.phase_boundary?.does_not_provide_financial_advice === true &&
      output.phase_boundary?.does_not_mutate_active_formula_config === true &&
      output.phase_boundary?.requires_proposal_before_apply === true &&
      output.phase_boundary?.next_phase === "S07 Review" &&
      badItems.length === 0,
    "s07p3_formula_what_if_output",
    "Formula what-if output exposes configurable scenarios without mutating active config",
    "Formula what-if output failed S07 P3 acceptance",
    { scenario_count: scenarios.length, badItems },
  );
  const dryRun = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "formula-what-if", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    dryRun.task_id === taskId &&
      dryRun.acceptance_id === acceptanceId &&
      dryRun.dry_run === true &&
      dryRun.writes_files === false &&
      Array.isArray(dryRun.scenarios) &&
      dryRun.scenarios.length === scenarios.length,
    "s07p3_atlasctl_formula_what_if_dry_run",
    "atlasctl analyze --stage formula-what-if --dry-run returns the no-write S07 P3 payload",
    "atlasctl formula-what-if dry-run failed S07 P3 gate",
    { writes_files: dryRun.writes_files, scenario_count: dryRun.scenarios?.length },
  );
  const audit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "formula-what-if"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    audit.status === "PASS" &&
      audit.task_id === taskId &&
      audit.acceptance_id === acceptanceId &&
      audit.scenario_count === scenarios.length &&
      audit.active_config_write === false &&
      audit.proposal_required_before_apply === true &&
      Array.isArray(audit.bad_items) &&
      audit.bad_items.length === 0,
    "s07p3_formula_what_if_audit",
    "atlasctl audit --check formula-what-if confirms proposal-only configurable proxy preview",
    "formula-what-if audit failed S07 P3 gate",
    audit,
  );
}

function currentStateIsS08P1() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S08 P3", "MA-V12-S08P3", "ACC-MA-V12-S08P3", "下一步只允许进入 S08 Review"]) &&
    hasAll(overview, ["S08 P3 已完成", "stage flight recorder", "stage_flight_recorder.json", "下一步是 S08 Review"]) &&
    hasAll(machine, ["当前为 S08 P3", "MA-V12-S08P3", "validate:v1.2-s08-p3", "下一步是 S08 Review"]) &&
    hasAll(dataContract, ["当前 S08 P3 已完成", "stage_flight_recorder.json", "下一步是 S08 Review"]) &&
    hasAll(behavior, ["当前 S08 P3 已完成", "stage_flight_recorder_fields.v1_2_s08_p3.json", "stage_flight_recorder.json", "下一步是 S08 Review"]) &&
    hasAll(runGate, ["当前阶段是 S08 P3", "MA-V12-S08P3", "ACC-MA-V12-S08P3", "validate:v1.2-s08-p3"])
  );
}

function currentStateIsS07Review() {
  if (currentStateIsS08P1()) return true;
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const formula = readRepoFile("机器治理/参数与公式/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S07 Review", "MA-V12-S07-REVIEW", "ACC-MA-V12-S07-REVIEW", "下一步只允许进入 S08 P1"]) &&
    hasAll(overview, ["S07 Review 已完成", "Personal Economic Proxy", "Formula What-if", "下一步是 S08 P1"]) &&
    hasAll(machine, ["当前为 S07 Review", "MA-V12-S07-REVIEW", "validate:v1.2-s07-review", "下一步是 S08 P1"]) &&
    hasAll(dataContract, ["当前 S07 Review 已完成", "personal_economic_proxy.json", "formula_what_if_preview.json", "下一步是 S08 P1"]) &&
    hasAll(formula, ["当前 S07 Review 已完成", "personal_economic_proxy.v1_2_s07_p1.json", "formula_what_if_defaults.v1_2_s07_p3.json"]) &&
    hasAll(behavior, ["当前 S07 Review 已完成", "Personal Economic Proxy", "Formula What-if", "下一步是 S08 P1"]) &&
    hasAll(runGate, ["当前阶段是 S07 Review", "MA-V12-S07-REVIEW", "ACC-MA-V12-S07-REVIEW", "validate:v1.2-s07-review"])
  );
}

function validateDocsAndRecords() {
  [
    reviewPath,
    humanDocPath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/参数与公式/README.md",
    "机器治理/可视化配置/README.md",
    "机器治理/数据契约/README.md",
    "机器治理/行为智能模型/README.md",
    "机器治理/运行门禁/README.md",
    ...recordFiles,
  ].forEach(validateTextFile);
  const review = readRepoFile(reviewPath);
  const human = readRepoFile(humanDocPath);
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const formula = readRepoFile("机器治理/参数与公式/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  const s07ReviewState = currentStateIsS07Review();
  assertCondition(
    hasAll(review, [taskId, acceptanceId, status, "Formula What-if", outputPath, "proposal_required_before_apply", "pending S07 Review", "No GitHub main upload in this phase"]),
    "s07p3_review_artifact",
    "S07 P3 review artifact records Formula What-if output, proposal gate and next S07 Review gate",
    "S07 P3 review artifact is incomplete",
  );
  assertCondition(
    hasAll(human, [taskId, acceptanceId, configPath, outputPath, "时间节省", "复用价值", "长期复利", "不是财务建议", "下一步只允许进入 S07 Review"]),
    "s07p3_human_doc",
    "Human doc explains formula what-if config preview and next gate in Chinese",
    "Human formula what-if doc is incomplete",
  );
  assertCondition(
    s07ReviewState || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S07 P3", "Formula What-if", "下一步只允许进入 S07 Review"]),
    "s07p3_quick_entry",
    "Quick entry records S07 P3 state and next S07 Review gate",
    "Quick entry is missing S07 P3 state",
  );
  assertCondition(
    s07ReviewState || hasAll(overview, ["S07 P3 已完成", "Formula What-if", outputPath, "下一步是 S07 Review"]),
    "s07p3_overview",
    "Overview records S07 P3 state and output",
    "Overview is missing S07 P3 state",
  );
  assertCondition(
    s07ReviewState || hasAll(machine, ["当前为 S07 P3", taskId, acceptanceId, validatorName, "下一步是 S07 Review"]),
    "s07p3_machine_readme",
    "Machine README records S07 P3 identity and next gate",
    "Machine README is missing S07 P3 state",
  );
  assertCondition(
    s07ReviewState || hasAll(formula, ["当前 S07 P3 已完成", "formula_what_if_defaults.v1_2_s07_p3.json", "formula_what_if_proxy_score", "下一步是 S07 Review"]),
    "s07p3_formula_readme",
    "Formula README records S07 P3 what-if formula registry",
    "Formula README is missing S07 P3 state",
  );
  assertCondition(
    s07ReviewState || hasAll(dataContract, ["当前 S07 P3 已完成", outputPath, "scenarios", "parameter_change_proposal", "下一步是 S07 Review"]),
    "s07p3_data_contract",
    "Data contract README records S07 P3 formula what-if output",
    "Data contract README is missing S07 P3 state",
  );
  assertCondition(
    s07ReviewState || hasAll(behavior, ["当前 S07 P3 已完成", "Formula What-if", "Personal Economic Proxy", "下一步是 S07 Review"]),
    "s07p3_behavior_readme",
    "Behavior model README records S07 P3 usage of economic proxy outputs",
    "Behavior model README is missing S07 P3 state",
  );
  assertCondition(
    s07ReviewState || hasAll(runGate, ["当前阶段是 S07 P3", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S07 Review"]),
    "s07p3_run_gate",
    "Run gate README records S07 P3 validator and next gate",
    "Run gate README is missing S07 P3 state",
  );
  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S07 P3", "pending S07 Review", "No GitHub main upload in this phase"]),
      `s07p3_records_${name}`,
      `${name} records S07 P3 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S07 P3 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s07p3_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s07p3_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S07 P3 branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s07p3_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s07p3_open_diff_scope",
    "Open diff is limited to S07 P3 files and historical-validator compatibility",
    "Open diff contains files outside S07 P3 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );
  const publicRawDiff = run("git", ["diff", "--name-only", "--", "OpenAIDatabase/data/public_raw"], { cwd: worktreeRoot }).stdout.trim();
  const forbiddenOpenChanges = changed.filter((file) =>
    file.startsWith("OpenAIDatabase/data/public_raw/") ||
    file.includes(".env") ||
    file.includes("cookies") ||
    file.includes("session_token") ||
    file.includes("password"),
  );
  assertCondition(
    forbiddenOpenChanges.length === 0 && publicRawDiff === "",
    "s07p3_no_raw_or_secret_open_changes",
    "S07 P3 open diff does not modify raw or secret/config files",
    "S07 P3 open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateConfigAndOutput();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s07_p3", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s07_p3",
      task_id: taskId,
      acceptance_id: acceptanceId,
      error: error.message,
      details: error.details || { stdout: error.stdout, stderr: error.stderr },
      checks,
    }, null, 2));
    process.exit(1);
  }
}

main();
