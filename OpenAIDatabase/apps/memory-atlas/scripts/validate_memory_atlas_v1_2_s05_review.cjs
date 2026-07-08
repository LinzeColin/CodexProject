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

const taskId = "MA-V12-S05-REVIEW";
const acceptanceId = "ACC-MA-V12-S05-REVIEW";
const status = "stage_s05_review_passed_pending_s06_no_github_main_upload";
const validatorName = "validate:v1.2-s05-review";
const scriptName = "validate_memory_atlas_v1_2_s05_review.cjs";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s05_review.md";
const eventsPath = "data/derived/behavior_intelligence/events.json";
const schemaPath = "机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json";
const facetDocPath = "人类可读/12_Facet字段与事件语义说明.md";
const atlasctlPath = "scripts/atlasctl.py";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p3.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/scripts/atlasctl.py",
  "OpenAIDatabase/scripts/build_memory_atlas_clusters.py",
  "OpenAIDatabase/scripts/build_memory_atlas_low_value_loops.py",
  "OpenAIDatabase/scripts/build_memory_atlas_opportunities.py",
  "OpenAIDatabase/tests/test_s06p1_cluster_builder.py",
  "OpenAIDatabase/tests/test_s06p2_low_value_loops.py",
  "OpenAIDatabase/tests/test_s06p3_opportunity_discovery.py",
  "OpenAIDatabase/data/derived/behavior_intelligence/clusters.json",
  "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json",
  "OpenAIDatabase/data/derived/behavior_intelligence/opportunities.json",
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s06_p1_cluster_builder.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s06_p2_low_value_loops.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s06_p3_opportunity_discovery.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  `OpenAIDatabase/${facetDocPath}`,
  "OpenAIDatabase/人类可读/13_行为簇与层级簇说明.md",
  "OpenAIDatabase/人类可读/14_低价值循环与DecisionDebt说明.md",
  "OpenAIDatabase/人类可读/15_机会发现与为什么不是现在卡片.md",
  "OpenAIDatabase/机器治理/README.md",
  "OpenAIDatabase/机器治理/数据契约/README.md",
  "OpenAIDatabase/机器治理/行为智能模型/README.md",
  "OpenAIDatabase/机器治理/运行门禁/README.md",
];

const requiredFacetFields = [
  "source",
  "topic",
  "intent",
  "task_type",
  "project",
  "output_type",
  "language",
  "tool",
  "turn_count",
  "friction",
  "value_signal",
  "future_agent_source",
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

function currentStateIsS06P1() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S06 P1", "MA-V12-S06P1", "ACC-MA-V12-S06P1", "下一步只允许进入 S06 P2"]) &&
    hasAll(overview, ["S06 P1 已完成", "Cluster builder", "下一步是 S06 P2"]) &&
    hasAll(machine, ["当前为 S06 P1", "MA-V12-S06P1", "validate:v1.2-s06-p1", "下一步是 S06 P2"]) &&
    hasAll(runGate, ["当前阶段是 S06 P1", "MA-V12-S06P1", "ACC-MA-V12-S06P1", "validate:v1.2-s06-p1"])
  );
}

function currentStateIsS06P2() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S06 P2", "MA-V12-S06P2", "ACC-MA-V12-S06P2", "下一步只允许进入 S06 P3"]) &&
    hasAll(overview, ["S06 P2 已完成", "Decision Debt Ledger", "下一步是 S06 P3"]) &&
    hasAll(machine, ["当前为 S06 P2", "MA-V12-S06P2", "validate:v1.2-s06-p2", "下一步是 S06 P3"]) &&
    hasAll(runGate, ["当前阶段是 S06 P2", "MA-V12-S06P2", "ACC-MA-V12-S06P2", "validate:v1.2-s06-p2"])
  );
}

function currentStateIsS06P3() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S06 P3", "MA-V12-S06P3", "ACC-MA-V12-S06P3", "下一步只允许进入 S06 Review"]) &&
    hasAll(overview, ["S06 P3 已完成", "为什么不是现在", "下一步是 S06 Review"]) &&
    hasAll(machine, ["当前为 S06 P3", "MA-V12-S06P3", "validate:v1.2-s06-p3", "下一步是 S06 Review"]) &&
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
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S06 Review", "MA-V12-S06-REVIEW", "ACC-MA-V12-S06-REVIEW", "下一步只允许进入 S07 P1"]) &&
    hasAll(overview, ["S06 Review 已完成", "behavior_intelligence", "下一步是 S07 P1"]) &&
    hasAll(machine, ["当前为 S06 Review", "MA-V12-S06-REVIEW", "validate:v1.2-s06-review", "下一步是 S07 P1"]) &&
    hasAll(runGate, ["当前阶段是 S06 Review", "MA-V12-S06-REVIEW", "ACC-MA-V12-S06-REVIEW", "validate:v1.2-s06-review"])
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
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s05_review_package_script",
    "package.json exposes the v1.2 S05 Review validator",
    "package.json is missing the v1.2 S05 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s05_review_previous_phase_deferred_scope",
      "S05 P3 execution is deferred only because open diff is limited to S05 Review files and compatibility updates",
      "S05 P3 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s05_review_previous_phase_deferred_until_clean_tree", "S05 P3 validator will run on a clean tree after S05 Review commit", { changed });
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s05_p3.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  });
  const parsed = parseJsonFromStdout(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S05P3",
    "s05_review_previous_s05p3",
    "S05 P3 validator returns PASS before accepting S05 Review",
    "S05 P3 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validatePhaseValidatorsOnCleanTree() {
  if (getOpenChangedPaths().length > 0) {
    pass("s05_review_phase_validators_deferred_until_clean_tree", "S05 P1/P2/P3 validator chain will run on a clean tree after S05 Review commit");
    return;
  }
  for (const [name, script, acceptance] of [
    ["s05_review_s05p1_validator", "validate_memory_atlas_v1_2_s05_p1.cjs", "ACC-MA-V12-S05P1"],
    ["s05_review_s05p2_validator", "validate_memory_atlas_v1_2_s05_p2.cjs", "ACC-MA-V12-S05P2"],
    ["s05_review_s05p3_validator", "validate_memory_atlas_v1_2_s05_p3.cjs", "ACC-MA-V12-S05P3"],
  ]) {
    const parsed = parseJsonFromStdout(run("node", [`scripts/${script}`], { cwd: appRoot, timeout: 300000 }));
    assertCondition(parsed.status === "PASS" && parsed.acceptance_id === acceptance, name, `${script} returns PASS`, `${script} did not return PASS`, {
      status: parsed.status,
      acceptance_id: parsed.acceptance_id,
    });
  }
}

function validateS05EventsAndPassGate() {
  validateTextFile(atlasctlPath);
  validateTextFile(schemaPath);
  validateTextFile(facetDocPath);
  const dryRun = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "facets", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    dryRun.task_id === "MA-V12-S05P3" &&
      dryRun.acceptance_id === "ACC-MA-V12-S05P3" &&
      dryRun.dry_run === true &&
      dryRun.writes_files === false &&
      dryRun.phase_boundary?.does_not_modify_raw === true,
    "s05_review_atlasctl_facets_dry_run",
    "atlasctl analyze --stage facets dry-run returns the S05 no-write contract",
    "atlasctl analyze --stage facets dry-run contract failed",
    {
      task_id: dryRun.task_id,
      acceptance_id: dryRun.acceptance_id,
      dry_run: dryRun.dry_run,
      writes_files: dryRun.writes_files,
      phase_boundary: dryRun.phase_boundary,
    },
  );

  const payload = JSON.parse(readRepoFile(eventsPath));
  const badEvents = [];
  const sources = new Set();
  for (const event of payload.events || []) {
    sources.add(event.source);
    for (const field of requiredFacetFields) {
      if (!(field in event)) badEvents.push(`${event.event_id}:missing:${field}`);
    }
    for (const reusableField of ["source_id", "occurred_at", "topic", "task_type", "project", "language", "friction", "value_signal"]) {
      if (!(reusableField in event)) badEvents.push(`${event.event_id}:not_reusable:${reusableField}`);
    }
    if (!(event.raw_ref || event.manifest_ref || event.derived_ref || event.evidence_missing_reason)) {
      badEvents.push(`${event.event_id}:missing_pointer_or_reason`);
    }
    if (!Array.isArray(event.evidence_refs) || event.evidence_refs.length === 0) {
      badEvents.push(`${event.event_id}:missing_evidence_refs`);
    }
    if ((event.source === "future_agent" || event.source === "other_agent") && !event.future_agent_source) {
      badEvents.push(`${event.event_id}:future_agent_source`);
    }
  }
  assertCondition(
    payload.task_id === "MA-V12-S05P3" &&
      payload.acceptance_id === "ACC-MA-V12-S05P3" &&
      payload.status === "phase_s05_p3_evidence_refs_completed_pending_s05_review" &&
      payload.schema_ref === schemaPath &&
      payload.event_count === payload.events?.length &&
      payload.event_count > 0 &&
      payload.evidence_ref_count >= payload.event_count &&
      payload.source_status?.chatgpt?.event_count > 0 &&
      payload.source_status?.codex?.event_count > 0 &&
      payload.source_status?.future_agent?.missing_reason &&
      sources.has("chatgpt") &&
      sources.has("codex") &&
      badEvents.length === 0,
    "s05_review_events_reusable",
    "S05 events satisfy schema, source coverage, evidence refs and cluster/ROI/latent/visualization reuse fields",
    "S05 events do not satisfy review pass gate",
    {
      task_id: payload.task_id,
      acceptance_id: payload.acceptance_id,
      event_count: payload.event_count,
      evidence_ref_count: payload.evidence_ref_count,
      sources: Array.from(sources).sort(),
      source_status: payload.source_status,
      badEvents: badEvents.slice(0, 50),
    },
  );

  const schema = JSON.parse(readRepoFile(schemaPath));
  const schemaRequiredFields = Array.isArray(schema.required_fields) ? schema.required_fields : [];
  assertCondition(
    requiredFacetFields.every((field) => schemaRequiredFields.includes(field) && schema.field_contract?.[field]) &&
      schema.source_coverage_contract?.chatgpt &&
      schema.source_coverage_contract?.codex &&
      schema.source_coverage_contract?.future_agent,
    "s05_review_schema_contract",
    "Facet schema covers required fields and ChatGPT/Codex/future agent",
    "Facet schema is missing required fields or source coverage",
    { requiredFacetFields, schemaRequiredFields, schemaFieldContracts: Object.keys(schema.field_contract || {}) },
  );

  const facetDoc = readRepoFile(facetDocPath);
  assertCondition(
    hasAll(facetDoc, ["source", "topic", "intent", "task_type", "future_agent_source", "S05 P3 已完成", "evidence_refs", "下一步只允许进入 S05 Review"]),
    "s05_review_human_facet_doc",
    "Human facet doc explains fields and S05 evidence refs in Chinese",
    "Human facet doc is missing field explanations or evidence refs",
  );
}

function validateDocsAndRecords() {
  [
    reviewPath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    facetDocPath,
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
  const s06p1State = currentStateIsS06P1() || currentStateIsS06P2() || currentStateIsS06P3() || currentStateIsS06Review();

  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      "canonical event 可覆盖 ChatGPT/Codex/future agent",
      "每条 event 有 evidence ref 或缺失原因",
      "人类文件能解释 facet 含义",
      "不输出纯机器字段给首屏",
      "extractor 为缺失数据生成假记录",
      "人类 UI 直接展示 schema 字段堆",
      "evidence ref 完全缺失",
      "行为事件与 facets 可被后续 cluster、ROI、latent、visualization 复用",
      "pending S06 P1",
      "No GitHub main upload in this review",
    ]),
    "s05_review_artifact",
    "S05 Review artifact records acceptance, stop conditions, pass gate and next S06 P1",
    "S05 Review artifact is incomplete",
  );
  assertCondition(
    s06p1State || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S05 Review", "S05 整体复审已通过", "下一步只允许进入 S06 P1"]),
    "s05_review_quick_entry",
    "Quick entry records S05 Review state and next S06 P1 gate",
    "Quick entry is missing S05 Review state",
  );
  assertCondition(
    s06p1State || hasAll(overview, ["S05 Review 已通过", "S05 整体复审已通过", "下一步是 S06 P1"]),
    "s05_review_overview",
    "Overview records S05 Review state and next S06 P1 gate",
    "Overview is missing S05 Review state",
  );
  assertCondition(
    s06p1State || hasAll(machine, ["当前为 S05 Review", taskId, acceptanceId, validatorName, "下一步是 S06 P1"]),
    "s05_review_machine_readme",
    "Machine README records S05 Review identity and next gate",
    "Machine README is missing S05 Review state",
  );
  assertCondition(
    s06p1State || hasAll(dataContract, ["当前 S05 Review 已通过", "canonical event", "evidence_refs", "下一步是 S06 P1"]),
    "s05_review_data_contract",
    "Data contract README records S05 Review result",
    "Data contract README is missing S05 Review state",
  );
  assertCondition(
    s06p1State || hasAll(behavior, ["当前 S05 Review 已通过", "cluster、ROI、latent、visualization", "下一步是 S06 P1"]),
    "s05_review_behavior_readme",
    "Behavior model README records S05 Review pass gate",
    "Behavior model README is missing S05 Review state",
  );
  assertCondition(
    s06p1State || hasAll(runGate, ["当前阶段是 S05 Review", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S06 P1"]),
    "s05_review_run_gate",
    "Run gate README records S05 Review validator and next gate",
    "Run gate README is missing S05 Review state",
  );

  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S05 Review", "pending S06 P1", "No GitHub main upload in this review"]),
      `s05_review_records_${name}`,
      `${name} records S05 Review status, acceptance, validator and no-upload boundary`,
      `${name} is missing S05 Review record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s05_review_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s05_review_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S05 Review branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s05_review_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });

  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s05_review_open_diff_scope",
    "Open diff is limited to S05 Review files and validator compatibility",
    "Open diff contains files outside S05 Review allowed scope",
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
    "s05_review_no_raw_or_secret_open_changes",
    "S05 Review open diff does not modify raw or secret/config files",
    "S05 Review open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validatePhaseValidatorsOnCleanTree();
    validateS05EventsAndPassGate();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s05_review", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s05_review",
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
