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

const taskId = "MA-V12-S05P2";
const acceptanceId = "ACC-MA-V12-S05P2";
const status = "phase_s05_p2_facet_extractor_completed_pending_s05_p3";
const s05p3TaskId = "MA-V12-S05P3";
const s05p3AcceptanceId = "ACC-MA-V12-S05P3";
const s05p3Status = "phase_s05_p3_evidence_refs_completed_pending_s05_review";
const s05ReviewTaskId = "MA-V12-S05-REVIEW";
const s05ReviewAcceptanceId = "ACC-MA-V12-S05-REVIEW";
const validatorName = "validate:v1.2-s05-p2";
const scriptName = "validate_memory_atlas_v1_2_s05_p2.cjs";
const extractorPath = "scripts/extract_memory_atlas_facets.py";
const atlasctlPath = "scripts/atlasctl.py";
const schemaPath = "机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json";
const humanPagePath = "人类可读/12_Facet字段与事件语义说明.md";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s05_p2_facet_extractor.md";
const eventsPath = "data/derived/behavior_intelligence/events.json";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p1.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${atlasctlPath}`,
  `OpenAIDatabase/${extractorPath}`,
  "OpenAIDatabase/scripts/build_memory_atlas_clusters.py",
  "OpenAIDatabase/tests/test_s05p2_facet_extractor.py",
  "OpenAIDatabase/tests/test_s05p3_facet_evidence_refs.py",
  "OpenAIDatabase/tests/test_s06p1_cluster_builder.py",
  `OpenAIDatabase/${eventsPath}`,
  "OpenAIDatabase/data/derived/behavior_intelligence/clusters.json",
  `OpenAIDatabase/${humanPagePath}`,
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s05_p3_evidence_refs.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s05_review.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s06_p1_cluster_builder.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/人类可读/13_行为簇与层级簇说明.md",
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

const githubHttpsRemote = "https://github.com/LinzeColin/CodexProject.git";

function queryRemoteDevBranch() {
  try {
    return {
      method: "origin",
      output: run("git", ["ls-remote", "--heads", "origin", branchName], {
        cwd: worktreeRoot,
        timeout: 60000,
      }).stdout.trim(),
    };
  } catch (originError) {
    return {
      method: "https_fallback",
      originError: originError.message,
      originStderr: originError.stderr?.slice(-1000),
      output: run("git", ["ls-remote", "--heads", githubHttpsRemote, branchName], {
        cwd: worktreeRoot,
        timeout: 60000,
      }).stdout.trim(),
    };
  }
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

function currentStateIsS05P3() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S05 P3", s05p3TaskId, s05p3AcceptanceId, "下一步只允许进入 S05 Review"]) &&
    hasAll(overview, ["S05 P3 已完成", "evidence_refs", "下一步是 S05 Review"]) &&
    hasAll(machine, ["当前为 S05 P3", "evidence_refs", eventsPath, "下一步是 S05 Review"]) &&
    hasAll(runGate, ["当前阶段是 S05 P3", s05p3TaskId, s05p3AcceptanceId, "validate:v1.2-s05-p3"])
  );
}

function currentStateIsS05Review() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S05 Review", s05ReviewTaskId, s05ReviewAcceptanceId, "下一步只允许进入 S06 P1"]) &&
    hasAll(overview, ["S05 Review 已通过", "S05 整体复审已通过", "下一步是 S06 P1"]) &&
    hasAll(machine, ["当前为 S05 Review", s05ReviewTaskId, "validate:v1.2-s05-review", "下一步是 S06 P1"]) &&
    hasAll(runGate, ["当前阶段是 S05 Review", s05ReviewTaskId, s05ReviewAcceptanceId, "validate:v1.2-s05-review"])
  );
}

function currentStateIsS05P3OrLater() {
  return (
    currentStateIsS05P3() ||
    currentStateIsS05Review() ||
    currentStateIsS06P1() ||
    currentStateIsS06P2() ||
    currentStateIsS06P3() ||
    currentStateIsS06Review()
  );
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
    hasAll(quick, ["当前阶段是 S08 P3", "MA-V12-S08P3", "ACC-MA-V12-S08P3", "下一步只允许进入 S08 Review"]) &&
    hasAll(overview, ["S08 P3 已完成", "stage flight recorder", "stage_flight_recorder.json", "下一步是 S08 Review"]) &&
    hasAll(machine, ["当前为 S08 P3", "MA-V12-S08P3", "validate:v1.2-s08-p3", "下一步是 S08 Review"]) &&
    hasAll(dataContract, ["当前 S08 P3 已完成", "stage_flight_recorder.json", "下一步是 S08 Review"]) &&
    hasAll(behavior, ["当前 S08 P3 已完成", "stage_flight_recorder_fields.v1_2_s08_p3.json", "stage_flight_recorder.json", "下一步是 S08 Review"]) &&
    hasAll(runGate, ["当前阶段是 S08 P3", "MA-V12-S08P3", "ACC-MA-V12-S08P3", "validate:v1.2-s08-p3"])
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
  assertCondition(
    source.endsWith("\n"),
    `${relativePath}:final_newline`,
    `${relativePath} has a final newline`,
    `${relativePath} is missing a final newline`,
  );

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
    "s05p2_package_script",
    "package.json exposes the v1.2 S05 P2 validator",
    "package.json is missing the v1.2 S05 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s05p2_previous_phase_deferred_scope",
      "S05 P1 execution is deferred only because open diff is limited to S05 P2 files and S05 P1 compatibility",
      "S05 P1 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s05p2_previous_phase_deferred_until_clean_tree", "S05 P1 validator will run on a clean tree after S05 P2 commit", { changed });
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s05_p1.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  });
  const parsed = parseJsonFromStdout(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S05P1",
    "s05p2_previous_s05p1",
    "S05 P1 validator returns PASS before accepting S05 P2",
    "S05 P1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateExtractorRuntime() {
  validateTextFile(extractorPath);
  validateTextFile(atlasctlPath);
  const result = run("python", [atlasctlPath, "analyze", "--stage", "facets", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  });
  const parsed = parseJsonFromStdout(result);
  const currentOrLaterIdentity =
    (parsed.task_id === taskId && parsed.acceptance_id === acceptanceId && parsed.status === status) ||
    (parsed.task_id === s05p3TaskId && parsed.acceptance_id === s05p3AcceptanceId && parsed.status === s05p3Status);
  assertCondition(
    currentOrLaterIdentity &&
      parsed.dry_run === true &&
      parsed.writes_files === false &&
      parsed.output_path === eventsPath &&
      parsed.phase_boundary?.does_not_modify_raw === true &&
      parsed.phase_boundary?.does_not_generate_fake_records_for_missing_data === true,
    "s05p2_atlasctl_analyze_dry_run",
    "atlasctl analyze --stage facets --dry-run returns the S05 P2 or later no-write extractor contract",
    "atlasctl analyze dry-run contract is incomplete",
    {
      task_id: parsed.task_id,
      acceptance_id: parsed.acceptance_id,
      status: parsed.status,
      dry_run: parsed.dry_run,
      writes_files: parsed.writes_files,
      output_path: parsed.output_path,
      phase_boundary: parsed.phase_boundary,
    },
  );
}

function validateEventsPayload() {
  const payload = JSON.parse(readRepoFile(eventsPath));
  const currentOrLaterIdentity =
    (payload.task_id === taskId && payload.acceptance_id === acceptanceId && payload.status === status) ||
    (payload.task_id === s05p3TaskId && payload.acceptance_id === s05p3AcceptanceId && payload.status === s05p3Status);
  assertCondition(
    currentOrLaterIdentity &&
      payload.schema_ref === schemaPath &&
      payload.output_path === eventsPath &&
      payload.phase_boundary?.does_not_modify_raw === true &&
      payload.phase_boundary?.does_not_generate_fake_records_for_missing_data === true,
    "s05p2_events_identity",
    "events.json records S05 P2 or later identity, schema ref, output path and raw/no-fake boundary",
    "events.json identity or phase boundary is incomplete",
    {
      task_id: payload.task_id,
      acceptance_id: payload.acceptance_id,
      status: payload.status,
      schema_ref: payload.schema_ref,
      output_path: payload.output_path,
      event_count: payload.event_count,
      phase_boundary: payload.phase_boundary,
    },
  );
  assertCondition(
    Number.isInteger(payload.event_count) && payload.event_count === payload.events?.length && payload.event_count > 0,
    "s05p2_event_count",
    "events.json has at least one real extracted event and count matches events length",
    "events.json event_count is invalid",
    { event_count: payload.event_count, actual: payload.events?.length },
  );
  assertCondition(
    payload.source_status?.chatgpt?.event_count > 0 &&
      payload.source_status?.codex?.event_count > 0 &&
      payload.source_status?.future_agent?.missing_reason,
    "s05p2_source_status",
    "source_status covers ChatGPT, Codex and future_agent missing-data behavior",
    "source_status does not cover required source states",
    payload.source_status,
  );

  const sources = new Set();
  const badEvents = [];
  const eventIds = new Set();
  for (const event of payload.events) {
    sources.add(event.source);
    if (eventIds.has(event.event_id)) badEvents.push(`${event.event_id}:duplicate`);
    eventIds.add(event.event_id);
    for (const field of requiredFacetFields) {
      if (!(field in event)) badEvents.push(`${event.event_id}:missing:${field}`);
    }
    if (!(event.raw_ref || event.manifest_ref || event.derived_ref || event.evidence_missing_reason)) {
      badEvents.push(`${event.event_id}:missing_evidence`);
    }
    if (!Array.isArray(event.friction) || !Array.isArray(event.value_signal)) {
      badEvents.push(`${event.event_id}:array_fields`);
    }
    if (!Number.isInteger(event.turn_count) || event.turn_count < 0) {
      badEvents.push(`${event.event_id}:turn_count`);
    }
    if ((event.source === "future_agent" || event.source === "other_agent") && !event.future_agent_source) {
      badEvents.push(`${event.event_id}:future_agent_source`);
    }
  }
  assertCondition(
    badEvents.length === 0 && sources.has("chatgpt") && sources.has("codex"),
    "s05p2_event_rows",
    "Each event has required facet fields plus evidence ref or missing reason; current data yields ChatGPT and Codex events",
    "events.json has invalid event rows",
    { badEvents: badEvents.slice(0, 50), sources: Array.from(sources).sort() },
  );
}

function validateDocsAndRecords() {
  [
    humanPagePath,
    reviewPath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/数据契约/README.md",
    "机器治理/行为智能模型/README.md",
    "机器治理/运行门禁/README.md",
    ...recordFiles,
  ].forEach(validateTextFile);

  const human = readRepoFile(humanPagePath);
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  const review = readRepoFile(reviewPath);
  const s05p3State = currentStateIsS05P3OrLater();

  assertCondition(
    s05p3State || hasAll(human, [
      "S05 P2 已完成",
      eventsPath,
      extractorPath,
      "processed_manifest_without_public_raw_ref",
      "不生成 fake events",
      "下一步只允许进入 S05 P3",
    ]),
    "s05p2_human_page",
    "Human facet page records extractor result without turning schema fields into first-screen UI",
    "Human facet page is missing S05 P2 extractor fragments",
  );
  assertCondition(
    s05p3State || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S05 P2", "facet extractor", "下一步只允许进入 S05 P3"]),
    "s05p2_quick_entry",
    "Human quick entry records S05 P2 state and next S05 P3 gate",
    "Human quick entry is missing S05 P2 state",
  );
  assertCondition(
    s05p3State || hasAll(overview, ["S05 P2 已完成", "facet extractor", eventsPath, "下一步是 S05 P3"]),
    "s05p2_overview",
    "Human overview records S05 P2 state and next S05 P3 gate",
    "Human overview is missing S05 P2 state",
  );
  assertCondition(
    s05p3State || hasAll(machine, ["当前为 S05 P2", taskId, acceptanceId, validatorName, extractorPath, eventsPath, "下一步是 S05 P3"]),
    "s05p2_machine_readme",
    "Machine README records S05 P2 identity, extractor and next gate",
    "Machine README is missing S05 P2 state",
  );
  assertCondition(
    s05p3State || hasAll(dataContract, ["当前 S05 P2 已完成", eventsPath, "ChatGPT", "Codex", "future_agent", "下一步是 S05 P3"]),
    "s05p2_data_contract_readme",
    "Data contract README records S05 P2 events output and source coverage",
    "Data contract README is missing S05 P2 state",
  );
  assertCondition(
    s05p3State || hasAll(behavior, ["当前 S05 P2 已完成", "facet extractor", eventsPath, "不生成 fake events", "下一步是 S05 P3"]),
    "s05p2_behavior_readme",
    "Behavior model README records S05 P2 extractor behavior and boundaries",
    "Behavior model README is missing S05 P2 state",
  );
  assertCondition(
    s05p3State || hasAll(runGate, ["当前阶段是 S05 P2", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S05 P3"]),
    "s05p2_run_gate",
    "Run gate README records S05 P2 validator and next gate",
    "Run gate README is missing S05 P2 state",
  );
  assertCondition(
    hasAll(review, [taskId, acceptanceId, status, extractorPath, eventsPath, "217", "ChatGPT", "Codex", "future_agent", "No fake events", "No raw mutation", "S05 P3"]),
    "s05p2_review_artifact",
    "Review artifact records S05 P2 extractor, generated events and boundaries",
    "S05 P2 review artifact is incomplete",
  );

  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S05 P2", "No GitHub main upload in this phase", "No raw mutation in this phase", "pending S05 P3"]),
      `s05p2_records_${name}`,
      `${name} records S05 P2 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S05 P2 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s05p2_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s05p2_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S05 P2 branch",
    { branch, branchName },
  );

  const remoteDevQuery = queryRemoteDevBranch();
  assertCondition(
    remoteDevQuery.output === "",
    "s05p2_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists unexpectedly",
    {
      branchName,
      remoteDev: remoteDevQuery.output,
      remote_query_method: remoteDevQuery.method,
      origin_error: remoteDevQuery.originError,
      origin_stderr: remoteDevQuery.originStderr,
    },
  );

  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s05p2_open_diff_scope",
    "Open diff is limited to S05 P2 files and S05 P1 compatibility",
    "Open diff contains files outside S05 P2 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  const forbiddenOpenChanges = changed.filter((file) =>
    file.startsWith("OpenAIDatabase/data/public_raw/") ||
    file.includes(".env") ||
    file.includes("cookies") ||
    file.includes("session_token") ||
    file.includes("password"),
  );
  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s05p2_no_raw_or_secret_open_changes",
    "S05 P2 open diff does not modify raw or secret/config files",
    "S05 P2 open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateExtractorRuntime();
    validateEventsPayload();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s05_p2", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s05_p2",
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
