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

const taskId = "MA-V12-S06P1";
const acceptanceId = "ACC-MA-V12-S06P1";
const status = "phase_s06_p1_cluster_builder_completed_pending_s06_p2";
const validatorName = "validate:v1.2-s06-p1";
const scriptName = "validate_memory_atlas_v1_2_s06_p1.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const builderPath = "scripts/build_memory_atlas_clusters.py";
const atlasctlPath = "scripts/atlasctl.py";
const eventsPath = "data/derived/behavior_intelligence/events.json";
const clustersPath = "data/derived/behavior_intelligence/clusters.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s06_p1_cluster_builder.md";
const humanClusterDocPath = "人类可读/13_行为簇与层级簇说明.md";

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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p3.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${builderPath}`,
  `OpenAIDatabase/${atlasctlPath}`,
  "OpenAIDatabase/scripts/build_memory_atlas_low_value_loops.py",
  "OpenAIDatabase/scripts/build_memory_atlas_opportunities.py",
  "OpenAIDatabase/tests/test_s06p1_cluster_builder.py",
  "OpenAIDatabase/tests/test_s06p2_low_value_loops.py",
  "OpenAIDatabase/tests/test_s06p3_opportunity_discovery.py",
  `OpenAIDatabase/${clustersPath}`,
  "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json",
  "OpenAIDatabase/data/derived/behavior_intelligence/opportunities.json",
  `OpenAIDatabase/${reviewPath}`,
  `OpenAIDatabase/${humanClusterDocPath}`,
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s06_p2_low_value_loops.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s06_p3_opportunity_discovery.md",
  "OpenAIDatabase/人类可读/15_机会发现与为什么不是现在卡片.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/人类可读/14_低价值循环与DecisionDebt说明.md",
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
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s06p1_package_script",
    "package.json exposes the v1.2 S06 P1 validator",
    "package.json is missing the v1.2 S06 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousStageGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s06p1_previous_stage_deferred_scope",
      "S05 Review execution is deferred only because open diff is limited to S06 P1 files and historical-validator compatibility",
      "S05 Review execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s06p1_previous_stage_deferred_until_clean_tree", "S05 Review validator will run on a clean tree after S06 P1 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s05_review.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S05-REVIEW",
    "s06p1_previous_s05_review",
    "S05 Review validator returns PASS before accepting S06 P1",
    "S05 Review validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateClustersPayload(payload, sourceName) {
  const allClusters = [...(payload.topic_clusters || []), ...(payload.hierarchy_clusters || [])];
  const badClusters = [];
  const blocked = ["心理诊断", "人格诊断", "抑郁", "焦虑症"];
  for (const cluster of allClusters) {
    const summary = String(cluster.summary_zh || "");
    if (!summary || summary.length < 28) badClusters.push(`${cluster.cluster_id}:weak_summary`);
    if (blocked.some((term) => summary.includes(term))) badClusters.push(`${cluster.cluster_id}:diagnostic_language`);
    if (!Array.isArray(cluster.evidence_refs) || cluster.evidence_refs.length === 0) badClusters.push(`${cluster.cluster_id}:missing_evidence_refs`);
    if (!Array.isArray(cluster.representative_event_ids) || cluster.representative_event_ids.length === 0) {
      badClusters.push(`${cluster.cluster_id}:missing_representative_events`);
    }
    for (const field of ["source", "time", "project", "task", "language"]) {
      if (!cluster.filter_dimensions?.[field]) badClusters.push(`${cluster.cluster_id}:missing_filter:${field}`);
    }
  }
  assertCondition(
    payload.task_id === taskId &&
      payload.acceptance_id === acceptanceId &&
      payload.status === status &&
      payload.input_path === eventsPath &&
      payload.filtered_event_count > 0 &&
      payload.topic_cluster_count > 0 &&
      payload.hierarchy_cluster_count > 0 &&
      payload.cluster_count === allClusters.length &&
      payload.filter_contract?.supported_filters?.join(",") === "source,time,project,task,language" &&
      payload.phase_boundary?.does_not_modify_raw === true &&
      payload.phase_boundary?.does_not_identify_low_value_loops === true &&
      payload.phase_boundary?.does_not_generate_opportunity_cards === true &&
      badClusters.length === 0,
    `s06p1_clusters_${sourceName}`,
    `${sourceName} clusters payload satisfies S06 P1 topic/hierarchy/evidence/filter boundary`,
    `${sourceName} clusters payload failed S06 P1 contract`,
    {
      task_id: payload.task_id,
      acceptance_id: payload.acceptance_id,
      filtered_event_count: payload.filtered_event_count,
      topic_cluster_count: payload.topic_cluster_count,
      hierarchy_cluster_count: payload.hierarchy_cluster_count,
      cluster_count: payload.cluster_count,
      badClusters: badClusters.slice(0, 50),
    },
  );
}

function validateClusterBuilder() {
  [builderPath, atlasctlPath, eventsPath, clustersPath, "tests/test_s06p1_cluster_builder.py"].forEach(validateTextFile);
  const dryRun = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "clusters", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    dryRun.dry_run === true && dryRun.writes_files === false,
    "s06p1_atlasctl_clusters_dry_run",
    "atlasctl analyze --stage clusters --dry-run returns the no-write cluster contract",
    "atlasctl clusters dry-run writes files or failed no-write contract",
    { dry_run: dryRun.dry_run, writes_files: dryRun.writes_files },
  );
  validateClustersPayload(dryRun, "dry_run");

  const persisted = JSON.parse(readRepoFile(clustersPath));
  assertCondition(
    persisted.dry_run === false && persisted.writes_files === true,
    "s06p1_clusters_persisted_identity",
    "clusters.json is the persisted S06 P1 output",
    "clusters.json is not the persisted S06 P1 output",
    { dry_run: persisted.dry_run, writes_files: persisted.writes_files },
  );
  validateClustersPayload(persisted, "persisted");

  const filtered = parseJsonFromStdout(run("python", [
    atlasctlPath,
    "analyze",
    "--stage",
    "clusters",
    "--dry-run",
    "--source",
    "chatgpt",
    "--language",
    "zh",
  ], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    filtered.filtered_event_count > 0 &&
      filtered.filter_contract?.active_filters?.source === "chatgpt" &&
      filtered.filter_contract?.active_filters?.language === "zh",
    "s06p1_cluster_filters",
    "Cluster builder supports source/time/project/task/language filter contract and applies source/language filters",
    "Cluster builder did not apply filter contract",
    { active_filters: filtered.filter_contract?.active_filters, filtered_event_count: filtered.filtered_event_count },
  );

  const audit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "insight-evidence"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    audit.status === "PASS" && audit.task_id === taskId && audit.acceptance_id === acceptanceId && audit.bad_clusters?.length === 0,
    "s06p1_insight_evidence_audit",
    "atlasctl audit --check insight-evidence confirms cluster summaries keep evidence refs",
    "insight evidence audit failed",
    audit,
  );
}

function currentStateIsS06P2() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S06 P2", "MA-V12-S06P2", "ACC-MA-V12-S06P2", "下一步只允许进入 S06 P3"]) &&
    hasAll(overview, ["S06 P2 已完成", "Decision Debt Ledger", "下一步是 S06 P3"]) &&
    hasAll(machine, ["当前为 S06 P2", "MA-V12-S06P2", "validate:v1.2-s06-p2", "下一步是 S06 P3"]) &&
    hasAll(dataContract, ["当前 S06 P2 已完成", "low_value_loops.json", "下一步是 S06 P3"]) &&
    hasAll(behavior, ["当前 S06 P2 已完成", "Decision Debt Ledger", "下一步是 S06 P3"]) &&
    hasAll(runGate, ["当前阶段是 S06 P2", "MA-V12-S06P2", "ACC-MA-V12-S06P2", "validate:v1.2-s06-p2"])
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
    hasAll(quick, ["当前阶段是 S09 P2", "MA-V12-S09P2", "ACC-MA-V12-S09P2", "下一步只允许进入 S09 P3"]) &&
    hasAll(overview, ["S09 P2 已完成", "self_iteration_suggestions.json", "下一步是 S09 P3"]) &&
    hasAll(machine, ["当前为 S09 P2", "MA-V12-S09P2", "validate:v1.2-s09-p2", "下一步是 S09 P3"]) &&
    hasAll(dataContract, ["当前 S09 P2 已完成", "self_iteration_suggestions.json", "下一步是 S09 P3"]) &&
    hasAll(behavior, ["当前 S09 P2 已完成", "self_iteration.v1_2_s09_p2.json", "self_iteration_suggestions.json", "下一步是 S09 P3"]) &&
    hasAll(runGate, ["当前阶段是 S09 P2", "MA-V12-S09P2", "ACC-MA-V12-S09P2", "validate:v1.2-s09-p2"])
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
    humanClusterDocPath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/数据契约/README.md",
    "机器治理/行为智能模型/README.md",
    "机器治理/运行门禁/README.md",
    ...recordFiles,
  ].forEach(validateTextFile);

  const review = readRepoFile(reviewPath);
  const human = readRepoFile(humanClusterDocPath);
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  const s06p2State = currentStateIsS06P2() || currentStateIsS06P3() || currentStateIsS06Review();

  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      "主题簇和层级簇",
      "source/time/project/task/language",
      "中文摘要",
      "evidence_refs",
      "不识别低价值循环",
      "不生成机会卡片",
      "pending S06 P2",
      "No GitHub main upload in this phase",
    ]),
    "s06p1_review_artifact",
    "S06 P1 review artifact records cluster builder scope, acceptance and next S06 P2 gate",
    "S06 P1 review artifact is incomplete",
  );
  assertCondition(
    hasAll(human, [taskId, acceptanceId, clustersPath, "主题簇", "层级簇", "中文摘要", "evidence_refs", "下一步只允许进入 S06 P2"]),
    "s06p1_human_cluster_doc",
    "Human cluster doc explains topic/hierarchy clusters and evidence refs in Chinese",
    "Human cluster doc is incomplete",
  );
  assertCondition(
    s06p2State || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S06 P1", "Cluster builder", "下一步只允许进入 S06 P2"]),
    "s06p1_quick_entry",
    "Quick entry records S06 P1 state and next S06 P2 gate",
    "Quick entry is missing S06 P1 state",
  );
  assertCondition(
    s06p2State || hasAll(overview, ["S06 P1 已完成", "Cluster builder", clustersPath, "下一步是 S06 P2"]),
    "s06p1_overview",
    "Overview records S06 P1 state and next S06 P2 gate",
    "Overview is missing S06 P1 state",
  );
  assertCondition(
    s06p2State || hasAll(machine, ["当前为 S06 P1", taskId, acceptanceId, validatorName, "下一步是 S06 P2"]),
    "s06p1_machine_readme",
    "Machine README records S06 P1 identity and next gate",
    "Machine README is missing S06 P1 state",
  );
  assertCondition(
    s06p2State || hasAll(dataContract, ["当前 S06 P1 已完成", clustersPath, "source/time/project/task/language", "下一步是 S06 P2"]),
    "s06p1_data_contract",
    "Data contract README records S06 P1 clusters output and filter contract",
    "Data contract README is missing S06 P1 state",
  );
  assertCondition(
    s06p2State || hasAll(behavior, ["当前 S06 P1 已完成", "主题簇", "层级簇", "evidence_refs", "下一步是 S06 P2"]),
    "s06p1_behavior_readme",
    "Behavior model README records S06 P1 cluster builder",
    "Behavior model README is missing S06 P1 state",
  );
  assertCondition(
    s06p2State || hasAll(runGate, ["当前阶段是 S06 P1", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S06 P2"]),
    "s06p1_run_gate",
    "Run gate README records S06 P1 validator and next gate",
    "Run gate README is missing S06 P1 state",
  );

  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S06 P1", "pending S06 P2", "No GitHub main upload in this phase"]),
      `s06p1_records_${name}`,
      `${name} records S06 P1 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S06 P1 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s06p1_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s06p1_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S06 P1 branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s06p1_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });

  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s06p1_open_diff_scope",
    "Open diff is limited to S06 P1 files and historical-validator compatibility",
    "Open diff contains files outside S06 P1 allowed scope",
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
    "s06p1_no_raw_or_secret_open_changes",
    "S06 P1 open diff does not modify raw or secret/config files",
    "S06 P1 open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousStageGate();
    validateClusterBuilder();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s06_p1", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s06_p1",
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
