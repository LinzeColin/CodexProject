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

const taskId = "MA-V12-S06-REVIEW";
const acceptanceId = "ACC-MA-V12-S06-REVIEW";
const status = "stage_s06_review_passed_pending_s07_no_github_main_upload";
const validatorName = "validate:v1.2-s06-review";
const scriptName = "validate_memory_atlas_v1_2_s06_review.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const atlasctlPath = "scripts/atlasctl.py";
const visualizationBuilderPath = "scripts/build_memory_atlas_data.py";
const clustersPath = "data/derived/behavior_intelligence/clusters.json";
const loopsPath = "data/derived/behavior_intelligence/low_value_loops.json";
const opportunitiesPath = "data/derived/behavior_intelligence/opportunities.json";
const visualizationPath = "data/derived/visualization/memory_atlas.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s06_review.md";

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
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  "OpenAIDatabase/apps/memory-atlas/src/types.ts",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p3.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p1.cjs",
  `OpenAIDatabase/${visualizationBuilderPath}`,
  "OpenAIDatabase/scripts/atlasctl.py",
  "OpenAIDatabase/scripts/build_memory_atlas_economic_proxy.py",
  `OpenAIDatabase/${visualizationPath}`,
  "OpenAIDatabase/data/derived/economic_proxy/personal_economic_proxy.json",
  "OpenAIDatabase/tests/test_s07p1_economic_proxy.py",
  "OpenAIDatabase/机器治理/参数与公式/README.md",
  "OpenAIDatabase/机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json",
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s07_p1_economic_proxy.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/人类可读/16_PersonalEconomicProxy公式说明.md",
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
    "s06_review_package_script",
    "package.json exposes the v1.2 S06 Review validator",
    "package.json is missing the v1.2 S06 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s06_review_previous_phase_deferred_scope",
      "S06 P3 execution is deferred only because open diff is limited to S06 Review files and compatibility updates",
      "S06 P3 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s06_review_previous_phase_deferred_until_clean_tree", "S06 P3 validator will run on a clean tree after S06 Review commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s06_p3.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S06P3",
    "s06_review_previous_s06p3",
    "S06 P3 validator returns PASS before accepting S06 Review on a clean tree",
    "S06 P3 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateClusterPayload(payload) {
  const allClusters = [...(payload.topic_clusters || []), ...(payload.hierarchy_clusters || [])];
  const badClusters = [];
  const blocked = ["心理诊断", "人格诊断", "抑郁", "焦虑症"];
  for (const item of allClusters.slice(0, 30)) {
    const summary = String(item.summary_zh || "");
    if (!hasCjk(summary) || summary.length < 28) badClusters.push(`${item.cluster_id}:weak_chinese_summary`);
    if (blocked.some((term) => summary.includes(term))) badClusters.push(`${item.cluster_id}:diagnostic_language`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badClusters.push(`${item.cluster_id}:missing_evidence_refs`);
    if (!Array.isArray(item.representative_event_ids) || item.representative_event_ids.length === 0) {
      badClusters.push(`${item.cluster_id}:missing_representative_events`);
    }
    for (const field of ["source", "time", "project", "task", "language"]) {
      if (!item.filter_dimensions?.[field]) badClusters.push(`${item.cluster_id}:missing_filter:${field}`);
    }
  }
  assertCondition(
    payload.task_id === "MA-V12-S06P1" &&
      payload.acceptance_id === "ACC-MA-V12-S06P1" &&
      payload.topic_cluster_count > 0 &&
      payload.hierarchy_cluster_count > 0 &&
      payload.cluster_count === allClusters.length &&
      badClusters.length === 0,
    "s06_review_cluster_acceptance",
    "S06 behavior clusters have Chinese summaries, evidence refs, representative events and filter dimensions",
    "S06 cluster output failed review acceptance",
    { cluster_count: payload.cluster_count, topic_cluster_count: payload.topic_cluster_count, hierarchy_cluster_count: payload.hierarchy_cluster_count, badClusters },
  );
}

function validateLoopPayload(payload) {
  const badLoops = [];
  for (const item of payload.loop_clusters || []) {
    const summary = String(item.summary_zh || "");
    if (!summary.includes("候选低价值循环") || !hasCjk(summary)) badLoops.push(`${item.loop_id}:weak_candidate_summary`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badLoops.push(`${item.loop_id}:missing_evidence_refs`);
  }
  for (const item of payload.decision_debt_ledger || []) {
    if (!item.suggested_closure_question || !Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) {
      badLoops.push(`${item.debt_id}:invalid_decision_debt`);
    }
  }
  for (const item of payload.action_half_life || []) {
    if (Number(item.action_half_life_days || 0) <= 0 || !Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) {
      badLoops.push(`${item.half_life_id}:invalid_action_half_life`);
    }
  }
  assertCondition(
    payload.task_id === "MA-V12-S06P2" &&
      payload.acceptance_id === "ACC-MA-V12-S06P2" &&
      payload.loop_cluster_count > 0 &&
      payload.decision_debt_count === payload.loop_cluster_count &&
      payload.action_half_life_count === payload.loop_cluster_count &&
      payload.phase_boundary?.does_not_output_psychological_diagnosis === true &&
      badLoops.length === 0,
    "s06_review_low_value_loop_acceptance",
    "S06 low-value loops include candidate summaries, Decision Debt Ledger and Action Half-Life evidence",
    "S06 low-value loop output failed review acceptance",
    {
      loop_cluster_count: payload.loop_cluster_count,
      decision_debt_count: payload.decision_debt_count,
      action_half_life_count: payload.action_half_life_count,
      badLoops: badLoops.slice(0, 50),
    },
  );
}

function validateOpportunityPayload(payload) {
  const badItems = [];
  const requiredTypes = ["automation", "productization", "template", "compounding", "defer"];
  const opportunityTypes = new Set(payload.opportunity_types || []);
  for (const type of requiredTypes) {
    if (!opportunityTypes.has(type)) badItems.push(`missing_opportunity_type:${type}`);
  }
  for (const item of payload.opportunity_clusters || []) {
    const card = item.why_not_now_card || {};
    if (!String(item.summary_zh || "").includes("候选机会")) badItems.push(`${item.opportunity_id}:summary_not_candidate`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badItems.push(`${item.opportunity_id}:missing_evidence_refs`);
    if (!item.next_step_zh) badItems.push(`${item.opportunity_id}:missing_next_step`);
    if (Number(item.opportunity_half_life_days || 0) <= 0 && !item.defer_reason_zh) {
      badItems.push(`${item.opportunity_id}:missing_half_life_or_defer_reason`);
    }
    if (!card.reason_zh || card.not_pressure_list !== true || !Array.isArray(card.evidence_refs) || card.evidence_refs.length === 0) {
      badItems.push(`${item.opportunity_id}:invalid_why_not_now_card`);
    }
  }
  assertCondition(
    payload.task_id === "MA-V12-S06P3" &&
      payload.acceptance_id === "ACC-MA-V12-S06P3" &&
      payload.opportunity_count >= 5 &&
      payload.opportunity_count <= 12 &&
      payload.defer_card_count === payload.opportunity_count &&
      payload.phase_boundary?.does_not_use_external_economic_database === true &&
      payload.phase_boundary?.does_not_create_infinite_pressure_list === true &&
      payload.phase_boundary?.does_not_modify_raw === true &&
      payload.phase_boundary?.does_not_output_psychological_diagnosis === true &&
      badItems.length === 0,
    "s06_review_opportunity_acceptance",
    "S06 opportunities include evidence, next steps, half-life/defer logic and why-not-now cards",
    "S06 opportunity output failed review acceptance",
    { opportunity_count: payload.opportunity_count, opportunity_types: payload.opportunity_types, badItems: badItems.slice(0, 50) },
  );
}

function validateVisualizationPayload(atlas, clusters, loops, opportunities) {
  const behavior = atlas.behavior_intelligence || {};
  const badItems = [];
  for (const item of behavior.clusters || []) {
    if (!item.summary_zh || !Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badItems.push(`${item.cluster_id}:invalid_display_cluster`);
  }
  for (const item of behavior.low_value_loops || []) {
    if (!item.summary_zh || !Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badItems.push(`${item.loop_id}:invalid_display_loop`);
  }
  for (const item of behavior.opportunities || []) {
    if (!item.summary_zh || !item.next_step_zh || !Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) {
      badItems.push(`${item.opportunity_id}:invalid_display_opportunity`);
    }
  }
  assertCondition(
    behavior.schema_version === "memory_atlas_behavior_intelligence_display.v1_2_s06_review" &&
      behavior.status === status &&
      behavior.counts?.clusters === clusters.cluster_count &&
      behavior.counts?.low_value_loops === loops.loop_cluster_count &&
      behavior.counts?.opportunities === opportunities.opportunity_count &&
      behavior.task_ids?.includes("MA-V12-S06P1") &&
      behavior.task_ids?.includes("MA-V12-S06P2") &&
      behavior.task_ids?.includes("MA-V12-S06P3") &&
      behavior.acceptance_ids?.includes("ACC-MA-V12-S06P1") &&
      behavior.acceptance_ids?.includes("ACC-MA-V12-S06P2") &&
      behavior.acceptance_ids?.includes("ACC-MA-V12-S06P3") &&
      behavior.source_files?.clusters === clustersPath &&
      behavior.source_files?.low_value_loops === loopsPath &&
      behavior.source_files?.opportunities === opportunitiesPath &&
      behavior.phase_boundary?.does_not_modify_raw === true &&
      behavior.phase_boundary?.does_not_output_psychological_diagnosis === true &&
      behavior.phase_boundary?.does_not_create_infinite_pressure_list === true &&
      behavior.phase_boundary?.does_not_use_external_economic_database === true &&
      (behavior.clusters || []).length >= 3 &&
      (behavior.low_value_loops || []).length >= 3 &&
      (behavior.opportunities || []).length >= 3 &&
      badItems.length === 0,
    "s06_review_visualization_payload",
    "memory_atlas.json exposes S06 clusters, low-value loops and opportunities for display with evidence",
    "memory_atlas.json is missing S06 display payload",
    { counts: behavior.counts, badItems },
  );
}

function validateBehaviorOutputs() {
  [
    visualizationBuilderPath,
    atlasctlPath,
    clustersPath,
    loopsPath,
    opportunitiesPath,
    visualizationPath,
    "apps/memory-atlas/src/App.tsx",
    "apps/memory-atlas/src/styles.css",
    "apps/memory-atlas/src/types.ts",
  ].forEach(validateTextFile);

  const clusters = readJson(clustersPath);
  const loops = readJson(loopsPath);
  const opportunities = readJson(opportunitiesPath);
  const atlas = readJson(visualizationPath);
  validateClusterPayload(clusters);
  validateLoopPayload(loops);
  validateOpportunityPayload(opportunities);
  validateVisualizationPayload(atlas, clusters, loops, opportunities);

  const dryRun = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "clusters", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    dryRun.task_id === "MA-V12-S06P1" && dryRun.acceptance_id === "ACC-MA-V12-S06P1" && dryRun.writes_files === false,
    "s06_review_atlasctl_clusters_dry_run",
    "atlasctl analyze --stage clusters --dry-run returns the S06 P1 no-write payload",
    "atlasctl clusters dry-run failed S06 review gate",
    { task_id: dryRun.task_id, acceptance_id: dryRun.acceptance_id, writes_files: dryRun.writes_files },
  );
  const audit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "insight-evidence"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    audit.status === "PASS" && audit.bad_clusters?.length === 0 && audit.bad_items?.length === 0,
    "s06_review_insight_evidence_audit",
    "atlasctl audit --check insight-evidence confirms S06 insight outputs keep evidence refs",
    "insight evidence audit failed in S06 Review",
    audit,
  );
}

function validateDisplayIntegration() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");
  const types = readRepoFile("apps/memory-atlas/src/types.ts");
  const builder = readRepoFile(visualizationBuilderPath);
  assertCondition(
    hasAll(app, [
      "BehaviorIntelligencePanel",
      "data-home-section=\"behavior_intelligence\"",
      "data-s06-review-display=\"behavior-clusters-low-value-loops-opportunities\"",
      "data-s06-cluster-count",
      "data-s06-loop-count",
      "data-s06-opportunity-count",
    ]),
    "s06_review_app_display_contract",
    "App.tsx renders the S06 behavior intelligence display section with validator-visible markers",
    "App.tsx is missing S06 behavior intelligence display markers",
  );
  assertCondition(
    hasAll(styles, [
      ".home-behavior-intelligence-panel",
      ".home-behavior-card-grid",
      ".home-behavior-card",
      ".home-behavior-item",
      ".home-behavior-count-row",
    ]),
    "s06_review_css_display_contract",
    "styles.css includes responsive S06 behavior intelligence panel styles",
    "styles.css is missing S06 behavior intelligence styles",
  );
  assertCondition(
    hasAll(types, [
      "BehaviorIntelligenceSummary",
      "BehaviorClusterSummary",
      "LowValueLoopSummary",
      "OpportunitySummary",
      "behavior_intelligence?: BehaviorIntelligenceSummary",
    ]),
    "s06_review_types_contract",
    "types.ts defines the optional S06 behavior intelligence payload contract",
    "types.ts is missing S06 behavior intelligence types",
  );
  assertCondition(
    hasAll(builder, [
      "BEHAVIOR_CLUSTER_SOURCE",
      "LOW_VALUE_LOOP_SOURCE",
      "OPPORTUNITY_SOURCE",
      "build_behavior_intelligence_summary",
      "\"behavior_intelligence\": behavior_intelligence",
    ]),
    "s06_review_builder_contract",
    "build_memory_atlas_data.py injects the S06 behavior intelligence summary into memory_atlas.json",
    "build_memory_atlas_data.py is missing S06 behavior intelligence integration",
  );
}

function currentStateIsS07P1() {
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

function validateDocsAndRecords() {
  [
    reviewPath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/数据契约/README.md",
    "机器治理/行为智能模型/README.md",
    "机器治理/运行门禁/README.md",
    ...recordFiles,
  ].forEach(validateTextFile);

  const review = readRepoFile(reviewPath);
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  const s07p1State = currentStateIsS07P1();

  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      "160",
      "23",
      "12",
      "behavior_intelligence",
      "data-s06-review-display",
      "No GitHub main upload in this phase",
      "pending S07 P1",
    ]),
    "s06_review_artifact",
    "S06 Review artifact records counts, display gate, acceptance and no-upload boundary",
    "S06 Review artifact is incomplete",
  );
  assertCondition(
    s07p1State || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S06 Review", "下一步只允许进入 S07 P1"]),
    "s06_review_quick_entry",
    "Quick entry records S06 Review state and next S07 P1 gate",
    "Quick entry is missing S06 Review state",
  );
  assertCondition(
    s07p1State || hasAll(overview, ["S06 Review 已完成", "behavior_intelligence", visualizationPath, "下一步是 S07 P1"]),
    "s06_review_overview",
    "Overview records S06 Review state and display integration",
    "Overview is missing S06 Review state",
  );
  assertCondition(
    s07p1State || hasAll(machine, ["当前为 S06 Review", taskId, acceptanceId, validatorName, "下一步是 S07 P1"]),
    "s06_review_machine_readme",
    "Machine README records S06 Review identity and next gate",
    "Machine README is missing S06 Review state",
  );
  assertCondition(
    s07p1State || hasAll(dataContract, ["当前 S06 Review 已完成", visualizationPath, "behavior_intelligence", "下一步是 S07 P1"]),
    "s06_review_data_contract",
    "Data contract README records S06 display payload and next gate",
    "Data contract README is missing S06 Review state",
  );
  assertCondition(
    s07p1State || hasAll(behavior, ["当前 S06 Review 已完成", "主题簇", "低价值循环", "机会线索", "下一步是 S07 P1"]),
    "s06_review_behavior_readme",
    "Behavior model README records S06 Review pass gate",
    "Behavior model README is missing S06 Review state",
  );
  assertCondition(
    s07p1State || hasAll(runGate, ["当前阶段是 S06 Review", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S07 P1"]),
    "s06_review_run_gate",
    "Run gate README records S06 Review validator and next gate",
    "Run gate README is missing S06 Review state",
  );

  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S06 Review", "pending S07 P1", "No GitHub main upload in this phase"]),
      `s06_review_records_${name}`,
      `${name} records S06 Review status, acceptance, validator and no-upload boundary`,
      `${name} is missing S06 Review record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s06_review_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s06_review_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S06 Review branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s06_review_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });

  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s06_review_open_diff_scope",
    "Open diff is limited to S06 Review files and historical-validator compatibility",
    "Open diff contains files outside S06 Review allowed scope",
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
    "s06_review_no_raw_or_secret_open_changes",
    "S06 Review open diff does not modify raw or secret/config files",
    "S06 Review open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateBehaviorOutputs();
    validateDisplayIntegration();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s06_review", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s06_review",
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
