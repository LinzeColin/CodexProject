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

const taskId = "MA-V12-S07P1";
const acceptanceId = "ACC-MA-V12-S07P1";
const status = "phase_s07_p1_economic_proxy_completed_pending_s07_p2";
const validatorName = "validate:v1.2-s07-p1";
const scriptName = "validate_memory_atlas_v1_2_s07_p1.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const atlasctlPath = "scripts/atlasctl.py";
const builderPath = "scripts/build_memory_atlas_economic_proxy.py";
const formulaConfigPath = "机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json";
const outputPath = "data/derived/economic_proxy/personal_economic_proxy.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s07_p1_economic_proxy.md";
const humanDocPath = "人类可读/16_PersonalEconomicProxy公式说明.md";

const requiredScoreKeys = [
  "time_saved_proxy",
  "reuse_value_proxy",
  "rework_cost_proxy",
  "opportunity_score_proxy",
  "skill_compounding_proxy",
  "automation_enhancement_ratio_proxy",
];

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
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p2.cjs",
  `OpenAIDatabase/${atlasctlPath}`,
  `OpenAIDatabase/${builderPath}`,
  "OpenAIDatabase/scripts/build_memory_atlas_information_roi.py",
  `OpenAIDatabase/${formulaConfigPath}`,
  "OpenAIDatabase/机器治理/参数与公式/information_roi.v1_2_s07_p2.json",
  "OpenAIDatabase/机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json",
  `OpenAIDatabase/${outputPath}`,
  "OpenAIDatabase/data/derived/information_roi/information_roi_gate.json",
  "OpenAIDatabase/tests/test_s07p1_economic_proxy.py",
  "OpenAIDatabase/tests/test_s07p2_information_roi.py",
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s07_p2_information_roi.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  `OpenAIDatabase/${humanDocPath}`,
  "OpenAIDatabase/人类可读/17_InformationROI与VisualROIGate说明.md",
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
    "s07p1_package_script",
    "package.json exposes the v1.2 S07 P1 validator",
    "package.json is missing the v1.2 S07 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s07p1_previous_phase_deferred_scope",
      "S06 Review execution is deferred only because open diff is limited to S07 P1 files and compatibility updates",
      "S06 Review execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s07p1_previous_phase_deferred_until_clean_tree", "S06 Review validator will run on a clean tree after S07 P1 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s06_review.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S06-REVIEW",
    "s07p1_previous_s06_review",
    "S06 Review validator returns PASS before accepting S07 P1 on a clean tree",
    "S06 Review validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateFormulaConfig(config) {
  const boundary = config.scope_boundary || {};
  const formulas = Array.isArray(config.formulas) ? config.formulas : [];
  const parameters = config.parameters && typeof config.parameters === "object" ? config.parameters : {};
  const scoreKeys = new Set(formulas.map((item) => item.score_key));
  const missing = requiredScoreKeys.filter((key) => !scoreKeys.has(key));
  const badItems = [];

  for (const item of formulas) {
    if (!item.formula_id || !item.name_zh || !item.expression_zh || !item.interpretation_zh) {
      badItems.push(`${item.score_key || "unknown"}:missing_formula_fields`);
    }
    if (!hasCjk(item.expression_zh) || !hasCjk(item.interpretation_zh)) {
      badItems.push(`${item.score_key || "unknown"}:missing_chinese_explanation`);
    }
    for (const paramRef of item.parameter_refs || []) {
      if (!Object.prototype.hasOwnProperty.call(parameters, paramRef)) {
        badItems.push(`${item.score_key || "unknown"}:unknown_parameter:${paramRef}`);
      }
    }
  }

  assertCondition(
    config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.status === "phase_s07_p1_formula_config_active_pending_s07_p2" &&
      missing.length === 0 &&
      formulas.length === requiredScoreKeys.length &&
      Object.keys(parameters).length > 0 &&
      boundary.external_economic_database_dependency === false &&
      boundary.external_economic_database_v2_interface === "reserved_not_implemented" &&
      boundary.precise_income_prediction === false &&
      boundary.financial_advice === false &&
      boundary.raw_mutation === false &&
      badItems.length === 0,
    "s07p1_formula_config",
    "Formula config defines six S07 P1 proxy formulas, parameters and stop-condition boundaries",
    "Formula config failed S07 P1 acceptance",
    { formula_count: formulas.length, missing, badItems },
  );
}

function validateScoreCards(payload) {
  const badItems = [];
  const cards = Array.isArray(payload.score_cards) ? payload.score_cards : [];
  const keys = new Set(cards.map((item) => item.score_key));
  for (const key of requiredScoreKeys) {
    if (!keys.has(key)) badItems.push(`missing_score_card:${key}`);
  }
  for (const card of cards) {
    const score = Number(card.score);
    if (!card.formula_id || card.formula_source !== formulaConfigPath) badItems.push(`${card.score_key}:missing_formula_source`);
    if (!Array.isArray(card.parameter_refs) || card.parameter_refs.length === 0) badItems.push(`${card.score_key}:missing_parameter_refs`);
    if (!Array.isArray(card.evidence_refs) || card.evidence_refs.length === 0) badItems.push(`${card.score_key}:missing_evidence_refs`);
    if (!hasCjk(card.explanation_zh) || !hasCjk(card.formula_expression_zh)) badItems.push(`${card.score_key}:missing_chinese_formula_or_explanation`);
    if (!Number.isFinite(score) || score < 0 || score > 100) badItems.push(`${card.score_key}:score_out_of_range`);
  }
  assertCondition(
    cards.length === requiredScoreKeys.length && badItems.length === 0,
    "s07p1_score_cards",
    "Economic proxy output exposes six score cards with Chinese explanation, formula source, parameters and evidence",
    "Economic proxy score cards failed S07 P1 acceptance",
    { score_card_count: cards.length, badItems },
  );
}

function validateEconomicProxyOutput(output) {
  const summaryScore = Number(output.proxy_summary?.personal_ai_economic_index_score);
  const boundary = output.phase_boundary || {};
  assertCondition(
    output.schema_version === "memory_atlas_personal_economic_proxy.v1_2_s07_p1" &&
      output.task_id === taskId &&
      output.acceptance_id === acceptanceId &&
      output.status === status &&
      output.formula_config_path === formulaConfigPath &&
      output.external_economic_database?.current_dependency === false &&
      output.external_economic_database?.v2_interface === "reserved_not_implemented" &&
      boundary.does_not_use_external_economic_database === true &&
      boundary.does_not_claim_precise_income_prediction === true &&
      boundary.does_not_modify_raw === true &&
      boundary.does_not_generate_information_roi_gate === true &&
      boundary.does_not_generate_what_if_ui === true &&
      boundary.next_phase === "S07 P2" &&
      Number.isFinite(summaryScore) &&
      summaryScore >= 0 &&
      summaryScore <= 100 &&
      hasCjk(output.proxy_summary?.explanation_zh) &&
      hasCjk(output.proxy_summary?.limitation_zh),
    "s07p1_economic_proxy_output",
    "Personal Economic Proxy output has identity, bounded score, v2-only external DB reservation and phase boundaries",
    "Personal Economic Proxy output failed S07 P1 acceptance",
    { summaryScore, boundary, external_economic_database: output.external_economic_database },
  );
  validateScoreCards(output);
}

function validateAtlasctlContracts() {
  const dryRun = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "economic-proxy", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    dryRun.task_id === taskId &&
      dryRun.acceptance_id === acceptanceId &&
      dryRun.dry_run === true &&
      dryRun.writes_files === false &&
      dryRun.status === status &&
      Array.isArray(dryRun.score_cards) &&
      dryRun.score_cards.length === requiredScoreKeys.length,
    "s07p1_atlasctl_analyze_dry_run",
    "atlasctl analyze --stage economic-proxy --dry-run returns the no-write S07 P1 proxy payload",
    "atlasctl economic-proxy dry-run failed S07 P1 gate",
    { task_id: dryRun.task_id, acceptance_id: dryRun.acceptance_id, writes_files: dryRun.writes_files, score_card_count: dryRun.score_cards?.length },
  );
  const audit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "formulas"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    audit.status === "PASS" &&
      audit.task_id === taskId &&
      audit.acceptance_id === acceptanceId &&
      audit.formula_count === requiredScoreKeys.length &&
      audit.score_card_count === requiredScoreKeys.length &&
      Array.isArray(audit.bad_items) &&
      audit.bad_items.length === 0 &&
      audit.external_economic_database_dependency === false,
    "s07p1_atlasctl_formula_audit",
    "atlasctl audit --check formulas confirms formula sources, Chinese explanations, parameters and no external DB dependency",
    "atlasctl formula audit failed S07 P1 gate",
    audit,
  );
}

function validateEconomicProxyArtifacts() {
  [atlasctlPath, builderPath, formulaConfigPath, outputPath].forEach(validateTextFile);
  const atlasctl = readRepoFile(atlasctlPath);
  const builder = readRepoFile(builderPath);
  assertCondition(
    hasAll(atlasctl, ["economic-proxy", "run_formula_audit", "audit.add_argument(\"--check\"", "formulas", "build_memory_atlas_economic_proxy.py"]),
    "s07p1_atlasctl_contract",
    "atlasctl exposes S07 P1 analyze and formula audit entry points",
    "atlasctl is missing S07 P1 economic-proxy or formula audit contract",
  );
  assertCondition(
    hasAll(builder, [taskId, acceptanceId, "does_not_generate_information_roi_gate", "does_not_generate_what_if_ui", "reserved_not_implemented"]),
    "s07p1_builder_contract",
    "Economic proxy builder enforces S07 P1 phase boundary and reserved external DB interface",
    "Economic proxy builder is missing S07 P1 boundary markers",
  );
  validateFormulaConfig(readJson(formulaConfigPath));
  validateEconomicProxyOutput(readJson(outputPath));
  validateAtlasctlContracts();
}

function currentStateIsS08P1() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S08 Review", "MA-V12-S08-REVIEW", "ACC-MA-V12-S08-REVIEW", "下一步只允许进入 S09 P1"]) &&
    hasAll(overview, ["S08 Review 已完成", "Codex/Agent 协作质量", "stage flight recorder", "下一步是 S09 P1"]) &&
    hasAll(machine, ["当前为 S08 Review", "MA-V12-S08-REVIEW", "validate:v1.2-s08-review", "下一步是 S09 P1"]) &&
    hasAll(dataContract, ["当前 S08 Review 已完成", "agent_collaboration_quality_report.json", "agent_authorization_boundary_report.json", "stage_flight_recorder.json", "下一步是 S09 P1"]) &&
    hasAll(behavior, ["当前 S08 Review 已完成", "Codex/Agent 协作质量", "授权边界", "stage flight recorder", "下一步是 S09 P1"]) &&
    hasAll(runGate, ["当前阶段是 S08 Review", "MA-V12-S08-REVIEW", "ACC-MA-V12-S08-REVIEW", "validate:v1.2-s08-review"])
  );
}

function currentStateIsS07P2() {
  if (currentStateIsS08P1()) return true;
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const formula = readRepoFile("机器治理/参数与公式/README.md");
  const visual = readRepoFile("机器治理/可视化配置/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  if (
    hasAll(quick, ["当前阶段是 S07 Review", "MA-V12-S07-REVIEW", "ACC-MA-V12-S07-REVIEW", "下一步只允许进入 S08 P1"]) &&
    hasAll(overview, ["S07 Review 已完成", "Personal Economic Proxy", "Formula What-if", "下一步是 S08 P1"]) &&
    hasAll(machine, ["当前为 S07 Review", "MA-V12-S07-REVIEW", "validate:v1.2-s07-review", "下一步是 S08 P1"]) &&
    hasAll(dataContract, ["当前 S07 Review 已完成", "personal_economic_proxy.json", "formula_what_if_preview.json", "下一步是 S08 P1"]) &&
    hasAll(formula, ["当前 S07 Review 已完成", "personal_economic_proxy.v1_2_s07_p1.json", "formula_what_if_defaults.v1_2_s07_p3.json"]) &&
    hasAll(behavior, ["当前 S07 Review 已完成", "Personal Economic Proxy", "Formula What-if", "下一步是 S08 P1"]) &&
    hasAll(runGate, ["当前阶段是 S07 Review", "MA-V12-S07-REVIEW", "ACC-MA-V12-S07-REVIEW", "validate:v1.2-s07-review"])
  ) {
    return true;
  }
  if (
    hasAll(quick, ["当前阶段是 S07 P3", "MA-V12-S07P3", "ACC-MA-V12-S07P3", "下一步只允许进入 S07 Review"]) &&
    hasAll(overview, ["S07 P3 已完成", "Formula What-if", "下一步是 S07 Review"]) &&
    hasAll(machine, ["当前为 S07 P3", "MA-V12-S07P3", "validate:v1.2-s07-p3", "下一步是 S07 Review"]) &&
    hasAll(dataContract, ["当前 S07 P3 已完成", "formula_what_if_preview.json", "下一步是 S07 Review"]) &&
    hasAll(formula, ["当前 S07 P3 已完成", "formula_what_if_defaults.v1_2_s07_p3.json", "formula_what_if_proxy_score"]) &&
    hasAll(behavior, ["当前 S07 P3 已完成", "Formula What-if", "下一步是 S07 Review"]) &&
    hasAll(runGate, ["当前阶段是 S07 P3", "MA-V12-S07P3", "ACC-MA-V12-S07P3", "validate:v1.2-s07-p3"])
  ) {
    return true;
  }
  return (
    hasAll(quick, ["当前阶段是 S07 P2", "MA-V12-S07P2", "ACC-MA-V12-S07P2", "下一步只允许进入 S07 P3"]) &&
    hasAll(overview, ["S07 P2 已完成", "Visual ROI Gate", "下一步是 S07 P3"]) &&
    hasAll(machine, ["当前为 S07 P2", "MA-V12-S07P2", "validate:v1.2-s07-p2", "下一步是 S07 P3"]) &&
    hasAll(dataContract, ["当前 S07 P2 已完成", "information_roi_gate.json", "下一步是 S07 P3"]) &&
    hasAll(formula, ["当前 S07 P2 已完成", "information_roi.v1_2_s07_p2.json", "information_roi_score"]) &&
    hasAll(visual, ["当前 S07 P2 已完成", "visual_roi_gate.v1_2_s07_p2.json", "没有决策价值的图表不进 P0"]) &&
    hasAll(behavior, ["当前 S07 P2 已完成", "Information ROI", "Visual ROI Gate", "下一步是 S07 P3"]) &&
    hasAll(runGate, ["当前阶段是 S07 P2", "MA-V12-S07P2", "ACC-MA-V12-S07P2", "validate:v1.2-s07-p2"])
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
  const s07p2State = currentStateIsS07P2();

  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      "Personal Economic Proxy",
      formulaConfigPath,
      outputPath,
      "personal_ai_economic_index_score",
      "不接入外部经济数据库",
      "不是精确收入预测",
      "pending S07 P2",
      "No GitHub main upload in this phase",
    ]),
    "s07p1_review_artifact",
    "S07 P1 review artifact records formula sources, output, limits and next S07 P2 gate",
    "S07 P1 review artifact is incomplete",
  );
  assertCondition(
    hasAll(human, [taskId, acceptanceId, formulaConfigPath, outputPath, "时间节省", "复用价值", "返工成本", "机会分", "技能复利", "自动化/增强比例", "不是精确收入预测", "下一步只允许进入 S07 P2"]),
    "s07p1_human_formula_doc",
    "Human formula doc explains all six proxy formulas, limits and next gate in Chinese",
    "Human formula doc is incomplete",
  );
  assertCondition(
    s07p2State || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S07 P1", "Personal Economic Proxy", "下一步只允许进入 S07 P2"]),
    "s07p1_quick_entry",
    "Quick entry records S07 P1 state and next S07 P2 gate",
    "Quick entry is missing S07 P1 state",
  );
  assertCondition(
    s07p2State || hasAll(overview, ["S07 P1 已完成", "Personal Economic Proxy", outputPath, "下一步是 S07 P2"]),
    "s07p1_overview",
    "Overview records S07 P1 state and economic proxy output",
    "Overview is missing S07 P1 state",
  );
  assertCondition(
    s07p2State || hasAll(machine, ["当前为 S07 P1", taskId, acceptanceId, validatorName, "下一步是 S07 P2"]),
    "s07p1_machine_readme",
    "Machine README records S07 P1 identity and next gate",
    "Machine README is missing S07 P1 state",
  );
  assertCondition(
    s07p2State || hasAll(formula, ["当前 S07 P1 已完成", "Personal Economic Proxy", formulaConfigPath, "time_saved_proxy", "automation_enhancement_ratio_proxy", "下一步是 S07 P2"]),
    "s07p1_formula_readme",
    "Formula README records S07 P1 formula registry and next gate",
    "Formula README is missing S07 P1 state",
  );
  assertCondition(
    s07p2State || hasAll(dataContract, ["当前 S07 P1 已完成", outputPath, "score_cards", "external_economic_database", "下一步是 S07 P2"]),
    "s07p1_data_contract",
    "Data contract README records S07 P1 economic proxy output",
    "Data contract README is missing S07 P1 state",
  );
  assertCondition(
    s07p2State || hasAll(behavior, ["当前 S07 P1 已完成", "S06", "Personal Economic Proxy", "下一步是 S07 P2"]),
    "s07p1_behavior_readme",
    "Behavior model README records S07 P1 usage of S06 behavior outputs",
    "Behavior model README is missing S07 P1 state",
  );
  assertCondition(
    s07p2State || hasAll(runGate, ["当前阶段是 S07 P1", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S07 P2"]),
    "s07p1_run_gate",
    "Run gate README records S07 P1 validator and next gate",
    "Run gate README is missing S07 P1 state",
  );

  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S07 P1", "pending S07 P2", "No GitHub main upload in this phase"]),
      `s07p1_records_${name}`,
      `${name} records S07 P1 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S07 P1 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s07p1_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s07p1_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S07 P1 branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s07p1_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });

  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s07p1_open_diff_scope",
    "Open diff is limited to S07 P1 files and historical-validator compatibility",
    "Open diff contains files outside S07 P1 allowed scope",
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
    "s07p1_no_raw_or_secret_open_changes",
    "S07 P1 open diff does not modify raw or secret/config files",
    "S07 P1 open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateEconomicProxyArtifacts();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s07_p1", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s07_p1",
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
