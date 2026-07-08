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

const taskId = "MA-V12-S06P3";
const acceptanceId = "ACC-MA-V12-S06P3";
const status = "phase_s06_p3_opportunity_discovery_completed_pending_s06_review";
const validatorName = "validate:v1.2-s06-p3";
const scriptName = "validate_memory_atlas_v1_2_s06_p3.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const builderPath = "scripts/build_memory_atlas_opportunities.py";
const atlasctlPath = "scripts/atlasctl.py";
const eventsPath = "data/derived/behavior_intelligence/events.json";
const clustersPath = "data/derived/behavior_intelligence/clusters.json";
const loopsPath = "data/derived/behavior_intelligence/low_value_loops.json";
const opportunitiesPath = "data/derived/behavior_intelligence/opportunities.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s06_p3_opportunity_discovery.md";
const humanDocPath = "人类可读/15_机会发现与为什么不是现在卡片.md";

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
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/scripts/build_memory_atlas_opportunities.py",
  "OpenAIDatabase/scripts/build_memory_atlas_low_value_loops.py",
  `OpenAIDatabase/${atlasctlPath}`,
  "OpenAIDatabase/tests/test_s06p3_opportunity_discovery.py",
  "OpenAIDatabase/tests/test_s06p2_low_value_loops.py",
  `OpenAIDatabase/${opportunitiesPath}`,
  `OpenAIDatabase/${reviewPath}`,
  `OpenAIDatabase/${humanDocPath}`,
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
    "s06p3_package_script",
    "package.json exposes the v1.2 S06 P3 validator",
    "package.json is missing the v1.2 S06 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s06p3_previous_phase_deferred_scope",
      "S06 P2 execution is deferred only because open diff is limited to S06 P3 files and historical-validator compatibility",
      "S06 P2 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s06p3_previous_phase_deferred_until_clean_tree", "S06 P2 validator will run on a clean tree after S06 P3 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s06_p2.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S06P2",
    "s06p3_previous_s06p2",
    "S06 P2 validator returns PASS before accepting S06 P3",
    "S06 P2 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateOpportunityPayload(payload, sourceName) {
  const blocked = ["心理诊断", "人格诊断", "抑郁", "焦虑症"];
  const requiredTypes = ["automation", "productization", "template", "compounding", "defer"];
  const opportunityTypes = new Set(payload.opportunity_types || []);
  const badItems = [];
  for (const type of requiredTypes) {
    if (!opportunityTypes.has(type)) badItems.push(`missing_opportunity_type:${type}`);
  }
  for (const item of payload.opportunity_clusters || []) {
    const summary = String(item.summary_zh || "");
    if (!summary.includes("候选机会")) badItems.push(`${item.opportunity_id}:summary_not_candidate`);
    if (blocked.some((term) => summary.includes(term))) badItems.push(`${item.opportunity_id}:diagnostic_language`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badItems.push(`${item.opportunity_id}:missing_evidence_refs`);
    if (!item.next_step_zh) badItems.push(`${item.opportunity_id}:missing_next_step`);
    if (Number(item.opportunity_half_life_days || 0) <= 0 && !item.defer_reason_zh) badItems.push(`${item.opportunity_id}:missing_half_life_or_defer_reason`);
    const card = item.why_not_now_card || {};
    if (!card.reason_zh || card.not_pressure_list !== true || !Array.isArray(card.evidence_refs) || card.evidence_refs.length === 0) {
      badItems.push(`${item.opportunity_id}:invalid_why_not_now_card`);
    }
  }

  assertCondition(
    payload.task_id === taskId &&
      payload.acceptance_id === acceptanceId &&
      payload.status === status &&
      payload.input_paths?.includes(eventsPath) &&
      payload.input_paths?.includes(clustersPath) &&
      payload.input_paths?.includes(loopsPath) &&
      payload.output_path === opportunitiesPath &&
      payload.opportunity_count === (payload.opportunity_clusters || []).length &&
      payload.opportunity_count >= 5 &&
      payload.opportunity_count <= 12 &&
      payload.defer_card_count === payload.opportunity_count &&
      payload.selection_policy?.candidate_only_not_pressure_list === true &&
      payload.selection_policy?.max_opportunities === 12 &&
      payload.phase_boundary?.does_not_use_external_economic_database === true &&
      payload.phase_boundary?.does_not_create_infinite_pressure_list === true &&
      payload.phase_boundary?.does_not_modify_raw === true &&
      payload.phase_boundary?.does_not_output_psychological_diagnosis === true &&
      payload.phase_boundary?.next_phase === "S06 Review" &&
      badItems.length === 0,
    `s06p3_opportunity_payload_${sourceName}`,
    `${sourceName} opportunity payload satisfies S06 P3 evidence, next-step, half-life/defer and no-pressure contract`,
    `${sourceName} opportunity payload failed S06 P3 contract`,
    {
      task_id: payload.task_id,
      acceptance_id: payload.acceptance_id,
      opportunity_count: payload.opportunity_count,
      defer_card_count: payload.defer_card_count,
      opportunity_types: payload.opportunity_types,
      badItems: badItems.slice(0, 50),
    },
  );
}

function validateOpportunityBuilder() {
  [builderPath, atlasctlPath, eventsPath, clustersPath, loopsPath, opportunitiesPath, "tests/test_s06p3_opportunity_discovery.py"].forEach(validateTextFile);
  const dryRun = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "opportunities", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    dryRun.dry_run === true && dryRun.writes_files === false,
    "s06p3_atlasctl_opportunities_dry_run",
    "atlasctl analyze --stage opportunities --dry-run returns a no-write S06 P3 payload",
    "opportunities dry-run writes files or failed no-write contract",
    { dry_run: dryRun.dry_run, writes_files: dryRun.writes_files },
  );
  validateOpportunityPayload(dryRun, "dry_run");

  const persisted = readJson(opportunitiesPath);
  assertCondition(
    persisted.dry_run === false && persisted.writes_files === true,
    "s06p3_opportunities_persisted_identity",
    "opportunities.json is the persisted S06 P3 output",
    "opportunities.json is not the persisted S06 P3 output",
    { dry_run: persisted.dry_run, writes_files: persisted.writes_files },
  );
  validateOpportunityPayload(persisted, "persisted");

  const audit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "insight-evidence"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    audit.status === "PASS" &&
      audit.opportunity_task_id === taskId &&
      audit.opportunity_acceptance_id === acceptanceId &&
      audit.bad_items?.length === 0 &&
      audit.bad_clusters?.length === 0,
    "s06p3_insight_evidence_audit",
    "atlasctl audit --check insight-evidence confirms clusters, loops and opportunity cards keep evidence refs",
    "insight evidence audit failed for S06 P3",
    audit,
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

  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      "机会发现",
      "为什么不是现在",
      "automation",
      "productization",
      "template",
      "compounding",
      "defer",
      "pending S06 Review",
      "No GitHub main upload in this phase",
    ]),
    "s06p3_review_artifact",
    "S06 P3 review artifact records opportunity discovery scope, acceptance and next S06 Review gate",
    "S06 P3 review artifact is incomplete",
  );
  assertCondition(
    hasAll(human, [taskId, acceptanceId, opportunitiesPath, "机会发现", "为什么不是现在", "候选机会", "下一步只允许进入 S06 Review"]),
    "s06p3_human_doc",
    "Human opportunity doc explains candidate opportunities and why-not-now cards in Chinese",
    "Human opportunity doc is incomplete",
  );
  assertCondition(
    hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S06 P3", "机会发现", "下一步只允许进入 S06 Review"]),
    "s06p3_quick_entry",
    "Quick entry records S06 P3 state and next S06 Review gate",
    "Quick entry is missing S06 P3 state",
  );
  assertCondition(
    hasAll(overview, ["S06 P3 已完成", "为什么不是现在", opportunitiesPath, "下一步是 S06 Review"]),
    "s06p3_overview",
    "Overview records S06 P3 state and next S06 Review gate",
    "Overview is missing S06 P3 state",
  );
  assertCondition(
    hasAll(machine, ["当前为 S06 P3", taskId, acceptanceId, validatorName, "下一步是 S06 Review"]),
    "s06p3_machine_readme",
    "Machine README records S06 P3 identity and next gate",
    "Machine README is missing S06 P3 state",
  );
  assertCondition(
    hasAll(dataContract, ["当前 S06 P3 已完成", opportunitiesPath, "为什么不是现在", "下一步是 S06 Review"]),
    "s06p3_data_contract",
    "Data contract README records S06 P3 opportunities output and contracts",
    "Data contract README is missing S06 P3 state",
  );
  assertCondition(
    hasAll(behavior, ["当前 S06 P3 已完成", "机会发现", "why-not-now", "下一步是 S06 Review"]),
    "s06p3_behavior_readme",
    "Behavior model README records S06 P3 opportunity model",
    "Behavior model README is missing S06 P3 state",
  );
  assertCondition(
    hasAll(runGate, ["当前阶段是 S06 P3", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S06 Review"]),
    "s06p3_run_gate",
    "Run gate README records S06 P3 validator and next review gate",
    "Run gate README is missing S06 P3 state",
  );

  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S06 P3", "pending S06 Review", "No GitHub main upload in this phase"]),
      `s06p3_records_${name}`,
      `${name} records S06 P3 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S06 P3 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s06p3_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s06p3_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S06 P3 branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s06p3_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });

  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s06p3_open_diff_scope",
    "Open diff is limited to S06 P3 files and historical-validator compatibility",
    "Open diff contains files outside S06 P3 allowed scope",
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
    "s06p3_no_raw_or_secret_open_changes",
    "S06 P3 open diff does not modify raw or secret/config files",
    "S06 P3 open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateOpportunityBuilder();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s06_p3", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s06_p3",
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
