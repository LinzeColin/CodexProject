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

const taskId = "MA-V12-S07-REVIEW";
const acceptanceId = "ACC-MA-V12-S07-REVIEW";
const status = "stage_s07_review_passed_pending_s08_no_github_main_upload";
const validatorName = "validate:v1.2-s07-review";
const scriptName = "validate_memory_atlas_v1_2_s07_review.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const atlasctlPath = "scripts/atlasctl.py";
const economicConfigPath = "机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json";
const informationConfigPath = "机器治理/参数与公式/information_roi.v1_2_s07_p2.json";
const visualConfigPath = "机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json";
const whatIfConfigPath = "机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json";
const economicOutputPath = "data/derived/economic_proxy/personal_economic_proxy.json";
const informationOutputPath = "data/derived/information_roi/information_roi_gate.json";
const whatIfOutputPath = "data/derived/economic_proxy/formula_what_if_preview.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s07_review.md";

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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p3.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
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
    "s07_review_package_script",
    "package.json exposes the v1.2 S07 Review validator",
    "package.json is missing the v1.2 S07 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s07_review_previous_phase_deferred_scope",
      "S07 P3 execution is deferred only because open diff is limited to S07 Review files and compatibility updates",
      "S07 P3 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s07_review_previous_phase_deferred_until_clean_tree", "S07 P3 validator will run on a clean tree after S07 Review commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s07_p3.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S07P3",
    "s07_review_previous_s07p3",
    "S07 P3 validator returns PASS before accepting S07 Review on a clean tree",
    "S07 P3 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateFormulaConfigs() {
  [economicConfigPath, informationConfigPath, visualConfigPath, whatIfConfigPath].forEach(validateTextFile);
  const economicConfig = readJson(economicConfigPath);
  const informationConfig = readJson(informationConfigPath);
  const whatIfConfig = readJson(whatIfConfigPath);
  const visualConfig = readJson(visualConfigPath);
  const configBad = [];
  for (const [name, config, expectedTask, expectedAcceptance] of [
    ["economic", economicConfig, "MA-V12-S07P1", "ACC-MA-V12-S07P1"],
    ["information_roi", informationConfig, "MA-V12-S07P2", "ACC-MA-V12-S07P2"],
    ["formula_what_if", whatIfConfig, "MA-V12-S07P3", "ACC-MA-V12-S07P3"],
  ]) {
    if (config.task_id !== expectedTask || config.acceptance_id !== expectedAcceptance) configBad.push(`${name}:identity_mismatch`);
    if (config.scope_boundary?.external_economic_database_dependency !== false) configBad.push(`${name}:external_database_dependency`);
    if (config.scope_boundary?.precise_income_prediction !== false) configBad.push(`${name}:precise_income_prediction`);
    if (config.scope_boundary?.financial_advice !== false) configBad.push(`${name}:financial_advice`);
    if (!Array.isArray(config.formulas) || config.formulas.length === 0) configBad.push(`${name}:missing_formulas`);
    for (const formula of config.formulas || []) {
      if (!formula.formula_id || !formula.score_key || !hasCjk(formula.expression_zh) || !hasCjk(formula.interpretation_zh)) {
        configBad.push(`${name}:${formula.score_key || "unknown"}:weak_formula_record`);
      }
    }
  }
  if (visualConfig.task_id !== "MA-V12-S07P2" || visualConfig.acceptance_id !== "ACC-MA-V12-S07P2") {
    configBad.push("visual_gate:identity_mismatch");
  }
  if (!Array.isArray(visualConfig.p0_visuals) || visualConfig.p0_visuals.length < 10) {
    configBad.push("visual_gate:p0_visuals_missing");
  }
  assertCondition(
    configBad.length === 0,
    "s07_review_formula_configs",
    "S07 formula and visual gate configs preserve identity, formula sources, Chinese explanations and no external DB boundaries",
    "S07 formula configs failed review acceptance",
    { configBad },
  );
}

function validateEconomicOutput() {
  validateTextFile(economicOutputPath);
  const output = readJson(economicOutputPath);
  const cards = Array.isArray(output.score_cards) ? output.score_cards : [];
  const required = new Set([
    "time_saved_proxy",
    "reuse_value_proxy",
    "rework_cost_proxy",
    "opportunity_score_proxy",
    "skill_compounding_proxy",
    "automation_enhancement_ratio_proxy",
  ]);
  const seen = new Set(cards.map((item) => item.score_key));
  const badItems = [];
  for (const key of required) {
    if (!seen.has(key)) badItems.push(`missing_score_card:${key}`);
  }
  for (const item of cards) {
    const score = Number(item.score);
    if (!Number.isFinite(score) || score < 0 || score > 100) badItems.push(`${item.score_key}:score_out_of_range`);
    if (!hasCjk(item.explanation_zh) || !hasCjk(item.formula_expression_zh)) badItems.push(`${item.score_key}:missing_chinese_explanation_or_formula`);
    if (!item.formula_id || item.formula_source !== economicConfigPath) badItems.push(`${item.score_key}:missing_formula_source`);
    if (!Array.isArray(item.parameter_refs) || item.parameter_refs.length === 0) badItems.push(`${item.score_key}:missing_parameter_refs`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badItems.push(`${item.score_key}:missing_evidence_refs`);
  }
  assertCondition(
    output.task_id === "MA-V12-S07P1" &&
      output.acceptance_id === "ACC-MA-V12-S07P1" &&
      output.external_economic_database?.current_dependency === false &&
      output.external_economic_database?.v2_interface === "reserved_not_implemented" &&
      output.phase_boundary?.does_not_claim_precise_income_prediction === true &&
      output.phase_boundary?.does_not_use_external_economic_database === true &&
      badItems.length === 0,
    "s07_review_economic_proxy_output",
    "Personal Economic Proxy can be generated with Chinese formula-backed score cards and no external DB dependency",
    "Personal Economic Proxy output failed S07 Review",
    { score_card_count: cards.length, badItems },
  );
}

function validateInformationOutput() {
  validateTextFile(informationOutputPath);
  const output = readJson(informationOutputPath);
  const roiItems = Array.isArray(output.roi_items) ? output.roi_items : [];
  const itemTypes = new Set(roiItems.map((item) => item.item_type));
  const badItems = [];
  for (const item of roiItems) {
    if (!item.formula_id || !item.formula_source) badItems.push(`${item.item_id}:missing_formula_source`);
    if (!hasCjk(item.decision_summary_zh)) badItems.push(`${item.item_id}:missing_chinese_summary`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badItems.push(`${item.item_id}:missing_evidence_refs`);
    const score = Number(item.information_roi_score);
    if (!Number.isFinite(score) || score < 0 || score > 100) badItems.push(`${item.item_id}:score_out_of_range`);
    if (item.item_type === "chart" && item.p0_candidate === true) {
      if (!hasCjk(item.human_question) || !hasCjk(item.action_zh) || item.visual_roi_gate_pass !== true) {
        badItems.push(`${item.item_id}:invalid_visual_roi_gate`);
      }
    }
  }
  assertCondition(
    output.task_id === "MA-V12-S07P2" &&
      output.acceptance_id === "ACC-MA-V12-S07P2" &&
      itemTypes.has("insight") &&
      itemTypes.has("card") &&
      itemTypes.has("chart") &&
      output.visual_roi_gate?.p0_candidate_count === 10 &&
      output.visual_roi_gate?.failed_p0_count === 0 &&
      output.external_economic_database?.current_dependency === false &&
      output.phase_boundary?.does_not_claim_precise_income_prediction === true &&
      badItems.length === 0,
    "s07_review_information_roi_output",
    "Information ROI covers insight/card/chart and Visual ROI Gate keeps low-value charts out of P0",
    "Information ROI output failed S07 Review",
    { roi_item_count: roiItems.length, item_types: [...itemTypes], badItems },
  );
}

function validateWhatIfOutput() {
  validateTextFile(whatIfOutputPath);
  const output = readJson(whatIfOutputPath);
  const scenarios = Array.isArray(output.scenarios) ? output.scenarios : [];
  const coveredWeights = new Set();
  const badItems = [];
  for (const scenario of scenarios) {
    Object.keys(scenario.adjustable_weights || {}).forEach((key) => coveredWeights.add(key));
    const proposal = scenario.parameter_change_proposal || {};
    if (proposal.active_config_write !== false || proposal.proposal_required_before_apply !== true) {
      badItems.push(`${scenario.scenario_id}:invalid_proposal_gate`);
    }
    if (!scenario.formula_id || scenario.formula_source !== whatIfConfigPath || !hasCjk(scenario.description_zh)) {
      badItems.push(`${scenario.scenario_id}:missing_formula_or_chinese_description`);
    }
    const score = Number(scenario.weighted_proxy_score);
    if (!Number.isFinite(score) || score < 0 || score > 100) badItems.push(`${scenario.scenario_id}:score_out_of_range`);
  }
  for (const key of ["time_saved_weight", "reuse_value_weight", "skill_compounding_weight"]) {
    if (!coveredWeights.has(key)) badItems.push(`missing_required_weight:${key}`);
  }
  assertCondition(
    output.task_id === "MA-V12-S07P3" &&
      output.acceptance_id === "ACC-MA-V12-S07P3" &&
      output.simulator_mode === "config_preview_only" &&
      output.scenario_count === scenarios.length &&
      scenarios.length >= 5 &&
      output.phase_boundary?.does_not_use_external_economic_database === true &&
      output.phase_boundary?.does_not_claim_precise_income_prediction === true &&
      output.phase_boundary?.does_not_provide_financial_advice === true &&
      output.phase_boundary?.does_not_mutate_active_formula_config === true &&
      output.phase_boundary?.requires_proposal_before_apply === true &&
      badItems.length === 0,
    "s07_review_formula_what_if_output",
    "Formula what-if is viewable/configurable and proposal-only without active config mutation",
    "Formula what-if output failed S07 Review",
    { scenario_count: scenarios.length, coveredWeights: [...coveredWeights].sort(), badItems },
  );
}

function validateAtlasctlGates() {
  const economic = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "economic-proxy", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    economic.task_id === "MA-V12-S07P1" && economic.acceptance_id === "ACC-MA-V12-S07P1" && economic.writes_files === false,
    "s07_review_atlasctl_economic_proxy_dry_run",
    "atlasctl can generate Personal Economic Proxy dry-run payload",
    "atlasctl economic-proxy dry-run failed S07 Review",
    { task_id: economic.task_id, acceptance_id: economic.acceptance_id, writes_files: economic.writes_files },
  );
  const formulaAudit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "formulas"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const visualAudit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "visual-roi"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const whatIfAudit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "formula-what-if"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    formulaAudit.status === "PASS" &&
      visualAudit.status === "PASS" &&
      whatIfAudit.status === "PASS" &&
      Array.isArray(formulaAudit.bad_items) &&
      formulaAudit.bad_items.length === 0 &&
      Array.isArray(visualAudit.bad_items) &&
      visualAudit.bad_items.length === 0 &&
      Array.isArray(whatIfAudit.bad_items) &&
      whatIfAudit.bad_items.length === 0,
    "s07_review_atlasctl_audits",
    "atlasctl formula, visual-roi and formula-what-if audits pass for S07 Review",
    "atlasctl S07 audits failed",
    { formulaAudit, visualAudit, whatIfAudit },
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
    hasAll(quick, ["当前阶段是 S09 P2", "MA-V12-S09P2", "ACC-MA-V12-S09P2", "下一步只允许进入 S09 P3"]) &&
    hasAll(overview, ["S09 P2 已完成", "self_iteration_suggestions.json", "下一步是 S09 P3"]) &&
    hasAll(machine, ["当前为 S09 P2", "MA-V12-S09P2", "validate:v1.2-s09-p2", "下一步是 S09 P3"]) &&
    hasAll(dataContract, ["当前 S09 P2 已完成", "self_iteration_suggestions.json", "下一步是 S09 P3"]) &&
    hasAll(behavior, ["当前 S09 P2 已完成", "self_iteration.v1_2_s09_p2.json", "self_iteration_suggestions.json", "下一步是 S09 P3"]) &&
    hasAll(runGate, ["当前阶段是 S09 P2", "MA-V12-S09P2", "ACC-MA-V12-S09P2", "validate:v1.2-s09-p2"])
  );
}

function validateDocsAndRecords() {
  [
    reviewPath,
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
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const formula = readRepoFile("机器治理/参数与公式/README.md");
  const visual = readRepoFile("机器治理/可视化配置/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  const s08p1State = currentStateIsS08P1();
  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      "Personal Economic Proxy",
      "Information ROI",
      "Formula What-if",
      "No GitHub main upload in this phase",
      "pending S08 P1",
    ]),
    "s07_review_artifact",
    "S07 Review artifact records stage acceptance, S07 P1/P2/P3 outputs and no-upload boundary",
    "S07 Review artifact is incomplete",
  );
  assertCondition(
    s08p1State || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S07 Review", "下一步只允许进入 S08 P1"]),
    "s07_review_quick_entry",
    "Quick entry records S07 Review state and next S08 P1 gate",
    "Quick entry is missing S07 Review state",
  );
  assertCondition(
    s08p1State || hasAll(overview, ["S07 Review 已完成", "Personal Economic Proxy", "Formula What-if", "下一步是 S08 P1"]),
    "s07_review_overview",
    "Overview records S07 Review state and next S08 P1 gate",
    "Overview is missing S07 Review state",
  );
  assertCondition(
    s08p1State || hasAll(machine, ["当前为 S07 Review", taskId, acceptanceId, validatorName, "下一步是 S08 P1"]),
    "s07_review_machine_readme",
    "Machine README records S07 Review identity and next gate",
    "Machine README is missing S07 Review state",
  );
  assertCondition(
    s08p1State || hasAll(formula, ["当前 S07 Review 已完成", "personal_economic_proxy.v1_2_s07_p1.json", "formula_what_if_defaults.v1_2_s07_p3.json", "下一步是 S08 P1"]),
    "s07_review_formula_readme",
    "Formula README records S07 Review pass gate and formula sources",
    "Formula README is missing S07 Review state",
  );
  assertCondition(
    s08p1State || hasAll(visual, ["当前 S07 Review 已完成", "Visual ROI Gate", "Formula What-if", "下一步是 S08 P1"]),
    "s07_review_visual_readme",
    "Visualization README records S07 Review visual ROI and config preview boundaries",
    "Visualization README is missing S07 Review state",
  );
  assertCondition(
    s08p1State || hasAll(dataContract, ["当前 S07 Review 已完成", economicOutputPath, informationOutputPath, whatIfOutputPath, "下一步是 S08 P1"]),
    "s07_review_data_contract",
    "Data contract README records all S07 derived outputs",
    "Data contract README is missing S07 Review state",
  );
  assertCondition(
    s08p1State || hasAll(behavior, ["当前 S07 Review 已完成", "Personal Economic Proxy", "Information ROI", "Formula What-if", "下一步是 S08 P1"]),
    "s07_review_behavior_readme",
    "Behavior model README records S07 Review usage of behavior-derived inputs",
    "Behavior model README is missing S07 Review state",
  );
  assertCondition(
    s08p1State || hasAll(runGate, ["当前阶段是 S07 Review", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S08 P1"]),
    "s07_review_run_gate",
    "Run gate README records S07 Review validator and next gate",
    "Run gate README is missing S07 Review state",
  );
  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      s08p1State || hasAll(source, [taskId, acceptanceId, status, validatorName, "S07 Review", "pending S08 P1", "No GitHub main upload in this phase"]),
      `s07_review_records_${name}`,
      `${name} records S07 Review status, acceptance, validator and no-upload boundary`,
      `${name} is missing S07 Review record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s07_review_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s07_review_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S07 Review branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s07_review_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s07_review_open_diff_scope",
    "Open diff is limited to S07 Review files and historical-validator compatibility",
    "Open diff contains files outside S07 Review allowed scope",
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
    "s07_review_no_raw_or_secret_open_changes",
    "S07 Review open diff does not modify raw or secret/config files",
    "S07 Review open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateFormulaConfigs();
    validateEconomicOutput();
    validateInformationOutput();
    validateWhatIfOutput();
    validateAtlasctlGates();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s07_review", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s07_review",
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
