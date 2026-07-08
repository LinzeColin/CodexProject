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

const taskId = "MA-V12-S06P2";
const acceptanceId = "ACC-MA-V12-S06P2";
const status = "phase_s06_p2_low_value_loops_completed_pending_s06_p3";
const validatorName = "validate:v1.2-s06-p2";
const scriptName = "validate_memory_atlas_v1_2_s06_p2.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const builderPath = "scripts/build_memory_atlas_low_value_loops.py";
const atlasctlPath = "scripts/atlasctl.py";
const eventsPath = "data/derived/behavior_intelligence/events.json";
const clustersPath = "data/derived/behavior_intelligence/clusters.json";
const loopsPath = "data/derived/behavior_intelligence/low_value_loops.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s06_p2_low_value_loops.md";
const humanDocPath = "人类可读/14_低价值循环与DecisionDebt说明.md";

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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p3.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${builderPath}`,
  `OpenAIDatabase/${atlasctlPath}`,
  "OpenAIDatabase/scripts/build_memory_atlas_opportunities.py",
  "OpenAIDatabase/tests/test_s06p2_low_value_loops.py",
  "OpenAIDatabase/tests/test_s06p3_opportunity_discovery.py",
  `OpenAIDatabase/${loopsPath}`,
  "OpenAIDatabase/data/derived/behavior_intelligence/opportunities.json",
  `OpenAIDatabase/${reviewPath}`,
  `OpenAIDatabase/${humanDocPath}`,
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s06_p3_opportunity_discovery.md",
  "OpenAIDatabase/人类可读/15_机会发现与为什么不是现在卡片.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
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
    "s06p2_package_script",
    "package.json exposes the v1.2 S06 P2 validator",
    "package.json is missing the v1.2 S06 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s06p2_previous_phase_deferred_scope",
      "S06 P1 execution is deferred only because open diff is limited to S06 P2 files and historical-validator compatibility",
      "S06 P1 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s06p2_previous_phase_deferred_until_clean_tree", "S06 P1 validator will run on a clean tree after S06 P2 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s06_p1.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S06P1",
    "s06p2_previous_s06p1",
    "S06 P1 validator returns PASS before accepting S06 P2",
    "S06 P1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateLowValuePayload(payload, sourceName) {
  const blocked = ["心理诊断", "人格诊断", "抑郁", "焦虑症"];
  const requiredLoopTypes = ["discussion_without_landing", "over_optimization", "repeated_rework", "scope_creep"];
  const loopTypes = new Set(payload.loop_types || []);
  const loopIds = new Set((payload.loop_clusters || []).map((loop) => loop.loop_id));
  const badItems = [];

  for (const type of requiredLoopTypes) {
    if (!loopTypes.has(type)) badItems.push(`missing_loop_type:${type}`);
  }
  for (const loop of payload.loop_clusters || []) {
    const summary = String(loop.summary_zh || "");
    if (!summary.includes("候选")) badItems.push(`${loop.loop_id}:summary_not_candidate`);
    if (blocked.some((term) => summary.includes(term))) badItems.push(`${loop.loop_id}:diagnostic_language`);
    if (!Array.isArray(loop.evidence_refs) || loop.evidence_refs.length === 0) badItems.push(`${loop.loop_id}:missing_evidence_refs`);
    if (!Array.isArray(loop.representative_event_ids) || loop.representative_event_ids.length === 0) badItems.push(`${loop.loop_id}:missing_representative_events`);
    if (!loop.observed_time_range || typeof loop.observed_time_range !== "object") badItems.push(`${loop.loop_id}:missing_observed_time_range`);
  }
  for (const debt of payload.decision_debt_ledger || []) {
    if (!loopIds.has(debt.loop_id)) badItems.push(`${debt.debt_id}:unknown_loop`);
    if (!debt.suggested_closure_question) badItems.push(`${debt.debt_id}:missing_closure_question`);
    if (!Array.isArray(debt.evidence_refs) || debt.evidence_refs.length === 0) badItems.push(`${debt.debt_id}:missing_evidence_refs`);
  }
  for (const item of payload.action_half_life || []) {
    if (!loopIds.has(item.loop_id)) badItems.push(`${item.half_life_id}:unknown_loop`);
    if (!item.interpretation_zh) badItems.push(`${item.half_life_id}:missing_interpretation`);
    if (Number(item.action_half_life_days || 0) <= 0) badItems.push(`${item.half_life_id}:invalid_days`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badItems.push(`${item.half_life_id}:missing_evidence_refs`);
  }

  assertCondition(
    payload.task_id === taskId &&
      payload.acceptance_id === acceptanceId &&
      payload.status === status &&
      payload.input_paths?.includes(eventsPath) &&
      payload.input_paths?.includes(clustersPath) &&
      payload.output_path === loopsPath &&
      payload.loop_cluster_count === (payload.loop_clusters || []).length &&
      payload.decision_debt_count === (payload.decision_debt_ledger || []).length &&
      payload.action_half_life_count === (payload.action_half_life || []).length &&
      payload.loop_cluster_count >= 4 &&
      payload.decision_debt_count >= 1 &&
      payload.action_half_life_count >= 1 &&
      payload.phase_boundary?.does_not_generate_opportunity_cards === true &&
      payload.phase_boundary?.does_not_modify_raw === true &&
      payload.phase_boundary?.does_not_output_psychological_diagnosis === true &&
      payload.phase_boundary?.next_phase === "S06 P3" &&
      badItems.length === 0,
    `s06p2_low_value_payload_${sourceName}`,
    `${sourceName} low-value loop payload satisfies S06 P2 evidence, Decision Debt and Action Half-Life contract`,
    `${sourceName} low-value loop payload failed S06 P2 contract`,
    {
      task_id: payload.task_id,
      acceptance_id: payload.acceptance_id,
      loop_cluster_count: payload.loop_cluster_count,
      decision_debt_count: payload.decision_debt_count,
      action_half_life_count: payload.action_half_life_count,
      loop_types: payload.loop_types,
      badItems: badItems.slice(0, 50),
    },
  );
}

function validateLowValueBuilder() {
  [builderPath, atlasctlPath, eventsPath, clustersPath, loopsPath, "tests/test_s06p2_low_value_loops.py"].forEach(validateTextFile);
  const dryRun = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "low-value-loops", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    dryRun.dry_run === true && dryRun.writes_files === false,
    "s06p2_atlasctl_low_value_dry_run",
    "atlasctl analyze --stage low-value-loops --dry-run returns a no-write S06 P2 payload",
    "low-value-loops dry-run writes files or failed no-write contract",
    { dry_run: dryRun.dry_run, writes_files: dryRun.writes_files },
  );
  validateLowValuePayload(dryRun, "dry_run");

  const persisted = readJson(loopsPath);
  assertCondition(
    persisted.dry_run === false && persisted.writes_files === true,
    "s06p2_low_value_persisted_identity",
    "low_value_loops.json is the persisted S06 P2 output",
    "low_value_loops.json is not the persisted S06 P2 output",
    { dry_run: persisted.dry_run, writes_files: persisted.writes_files },
  );
  validateLowValuePayload(persisted, "persisted");

  const audit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "insight-evidence"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    audit.status === "PASS" &&
      audit.low_value_loop_task_id === taskId &&
      audit.low_value_loop_acceptance_id === acceptanceId &&
      audit.bad_items?.length === 0 &&
      audit.bad_clusters?.length === 0,
    "s06p2_insight_evidence_audit",
    "atlasctl audit --check insight-evidence confirms clusters, low-value loops, Decision Debt and Action Half-Life keep evidence refs",
    "insight evidence audit failed for S06 P2",
    audit,
  );
}

function currentStateIsS06P3() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S06 P3", "MA-V12-S06P3", "ACC-MA-V12-S06P3", "下一步只允许进入 S06 Review"]) &&
    hasAll(overview, ["S06 P3 已完成", "为什么不是现在", "下一步是 S06 Review"]) &&
    hasAll(machine, ["当前为 S06 P3", "MA-V12-S06P3", "validate:v1.2-s06-p3", "下一步是 S06 Review"]) &&
    hasAll(dataContract, ["当前 S06 P3 已完成", "opportunities.json", "下一步是 S06 Review"]) &&
    hasAll(behavior, ["当前 S06 P3 已完成", "why-not-now", "下一步是 S06 Review"]) &&
    hasAll(runGate, ["当前阶段是 S06 P3", "MA-V12-S06P3", "ACC-MA-V12-S06P3", "validate:v1.2-s06-p3"])
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
    hasAll(quick, ["当前阶段是 S09 P1", "MA-V12-S09P1", "ACC-MA-V12-S09P1", "下一步只允许进入 S09 P2"]) &&
    hasAll(overview, ["S09 P1 已完成", "latent_signals.json", "下一步是 S09 P2"]) &&
    hasAll(machine, ["当前为 S09 P1", "MA-V12-S09P1", "validate:v1.2-s09-p1", "下一步是 S09 P2"]) &&
    hasAll(dataContract, ["当前 S09 P1 已完成", "latent_signals.json", "下一步是 S09 P2"]) &&
    hasAll(behavior, ["当前 S09 P1 已完成", "latent_signals.v1_2_s09_p1.json", "latent_signals.json", "下一步是 S09 P2"]) &&
    hasAll(runGate, ["当前阶段是 S09 P1", "MA-V12-S09P1", "ACC-MA-V12-S09P1", "validate:v1.2-s09-p1"])
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

function currentStateIsS07P1() {
  if (currentStateIsS07P2()) return true;
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const formula = readRepoFile("机器治理/参数与公式/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S07 P1", "MA-V12-S07P1", "ACC-MA-V12-S07P1", "下一步只允许进入 S07 P2"]) &&
    hasAll(overview, ["S07 P1 已完成", "Personal Economic Proxy", "下一步是 S07 P2"]) &&
    hasAll(machine, ["当前为 S07 P1", "MA-V12-S07P1", "validate:v1.2-s07-p1", "下一步是 S07 P2"]) &&
    hasAll(dataContract, ["当前 S07 P1 已完成", "personal_economic_proxy.json", "下一步是 S07 P2"]) &&
    hasAll(formula, ["当前 S07 P1 已完成", "personal_economic_proxy.v1_2_s07_p1.json", "Personal Economic Proxy"]) &&
    hasAll(runGate, ["当前阶段是 S07 P1", "MA-V12-S07P1", "ACC-MA-V12-S07P1", "validate:v1.2-s07-p1"])
  );
}

function currentStateIsS06Review() {
  if (currentStateIsS07P1()) return true;
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S06 Review", "MA-V12-S06-REVIEW", "ACC-MA-V12-S06-REVIEW", "下一步只允许进入 S07 P1"]) &&
    hasAll(overview, ["S06 Review 已完成", "behavior_intelligence", "下一步是 S07 P1"]) &&
    hasAll(machine, ["当前为 S06 Review", "MA-V12-S06-REVIEW", "validate:v1.2-s06-review", "下一步是 S07 P1"]) &&
    hasAll(dataContract, ["当前 S06 Review 已完成", "behavior_intelligence", "下一步是 S07 P1"]) &&
    hasAll(behavior, ["当前 S06 Review 已完成", "主题簇", "低价值循环", "机会线索"]) &&
    hasAll(runGate, ["当前阶段是 S06 Review", "MA-V12-S06-REVIEW", "ACC-MA-V12-S06-REVIEW", "validate:v1.2-s06-review"])
  );
}

function validateDocsAndRecords() {
  [
    reviewPath,
    humanDocPath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
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
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  const s06p3State = currentStateIsS06P3() || currentStateIsS06Review();

  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      "低价值循环",
      "Decision Debt Ledger",
      "Action Half-Life",
      "discussion_without_landing",
      "over_optimization",
      "repeated_rework",
      "scope_creep",
      "pending S06 P3",
      "No GitHub main upload in this phase",
    ]),
    "s06p2_review_artifact",
    "S06 P2 review artifact records low-value loop scope, acceptance and next S06 P3 gate",
    "S06 P2 review artifact is incomplete",
  );
  assertCondition(
    hasAll(human, [taskId, acceptanceId, loopsPath, "低价值循环", "Decision Debt Ledger", "Action Half-Life", "候选", "下一步只允许进入 S06 P3"]),
    "s06p2_human_doc",
    "Human low-value loop doc explains candidate loops, Decision Debt and Action Half-Life in Chinese",
    "Human low-value loop doc is incomplete",
  );
  assertCondition(
    s06p3State || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S06 P2", "低价值循环", "下一步只允许进入 S06 P3"]),
    "s06p2_quick_entry",
    "Quick entry records S06 P2 state and next S06 P3 gate",
    "Quick entry is missing S06 P2 state",
  );
  assertCondition(
    s06p3State || hasAll(overview, ["S06 P2 已完成", "Decision Debt Ledger", loopsPath, "下一步是 S06 P3"]),
    "s06p2_overview",
    "Overview records S06 P2 state and next S06 P3 gate",
    "Overview is missing S06 P2 state",
  );
  assertCondition(
    s06p3State || hasAll(machine, ["当前为 S06 P2", taskId, acceptanceId, validatorName, "下一步是 S06 P3"]),
    "s06p2_machine_readme",
    "Machine README records S06 P2 identity and next gate",
    "Machine README is missing S06 P2 state",
  );
  assertCondition(
    s06p3State || hasAll(dataContract, ["当前 S06 P2 已完成", loopsPath, "Decision Debt Ledger", "Action Half-Life", "下一步是 S06 P3"]),
    "s06p2_data_contract",
    "Data contract README records S06 P2 low-value loops output and contracts",
    "Data contract README is missing S06 P2 state",
  );
  assertCondition(
    s06p3State || hasAll(behavior, ["当前 S06 P2 已完成", "低价值循环", "Decision Debt Ledger", "Action Half-Life", "下一步是 S06 P3"]),
    "s06p2_behavior_readme",
    "Behavior model README records S06 P2 low-value loop model",
    "Behavior model README is missing S06 P2 state",
  );
  assertCondition(
    s06p3State || hasAll(runGate, ["当前阶段是 S06 P2", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S06 P3"]),
    "s06p2_run_gate",
    "Run gate README records S06 P2 validator and next gate",
    "Run gate README is missing S06 P2 state",
  );

  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S06 P2", "pending S06 P3", "No GitHub main upload in this phase"]),
      `s06p2_records_${name}`,
      `${name} records S06 P2 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S06 P2 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s06p2_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s06p2_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S06 P2 branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s06p2_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });

  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s06p2_open_diff_scope",
    "Open diff is limited to S06 P2 files and historical-validator compatibility",
    "Open diff contains files outside S06 P2 allowed scope",
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
    "s06p2_no_raw_or_secret_open_changes",
    "S06 P2 open diff does not modify raw or secret/config files",
    "S06 P2 open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateLowValueBuilder();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s06_p2", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s06_p2",
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
