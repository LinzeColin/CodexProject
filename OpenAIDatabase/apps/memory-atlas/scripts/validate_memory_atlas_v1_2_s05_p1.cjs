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

const taskId = "MA-V12-S05P1";
const acceptanceId = "ACC-MA-V12-S05P1";
const status = "phase_s05_p1_facet_schema_completed_pending_s05_p2";
const validatorName = "validate:v1.2-s05-p1";
const scriptName = "validate_memory_atlas_v1_2_s05_p1.cjs";
const schemaPath = "机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json";
const humanPagePath = "人类可读/12_Facet字段与事件语义说明.md";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s05_p1_facet_schema.md";
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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p1.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/scripts/atlasctl.py",
  "OpenAIDatabase/scripts/extract_memory_atlas_facets.py",
  "OpenAIDatabase/scripts/build_memory_atlas_clusters.py",
  "OpenAIDatabase/tests/test_s05p2_facet_extractor.py",
  "OpenAIDatabase/tests/test_s05p3_facet_evidence_refs.py",
  "OpenAIDatabase/tests/test_s06p1_cluster_builder.py",
  `OpenAIDatabase/${schemaPath}`,
  `OpenAIDatabase/${humanPagePath}`,
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s05_p2_facet_extractor.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s05_p3_evidence_refs.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s05_review.md",
  "OpenAIDatabase/data/derived/behavior_intelligence/events.json",
  "OpenAIDatabase/data/derived/behavior_intelligence/clusters.json",
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
  "OpenAIDatabase/机器治理/同步与备份/README.md",
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
    maxBuffer: 64 * 1024 * 1024,
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

function currentStateIsS05P2() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S05 P2", "MA-V12-S05P2", "ACC-MA-V12-S05P2", "下一步只允许进入 S05 P3"]) &&
    hasAll(overview, ["S05 P2 已完成", "facet extractor", "下一步是 S05 P3"]) &&
    hasAll(machine, ["当前为 S05 P2", "extract_memory_atlas_facets.py", eventsPath, "下一步是 S05 P3"]) &&
    hasAll(runGate, ["当前阶段是 S05 P2", "MA-V12-S05P2", "ACC-MA-V12-S05P2", "validate:v1.2-s05-p2"])
  );
}

function currentStateIsS05P3() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S05 P3", "MA-V12-S05P3", "ACC-MA-V12-S05P3", "下一步只允许进入 S05 Review"]) &&
    hasAll(overview, ["S05 P3 已完成", "evidence_refs", "下一步是 S05 Review"]) &&
    hasAll(machine, ["当前为 S05 P3", "evidence_refs", eventsPath, "下一步是 S05 Review"]) &&
    hasAll(runGate, ["当前阶段是 S05 P3", "MA-V12-S05P3", "ACC-MA-V12-S05P3", "validate:v1.2-s05-p3"])
  );
}

function currentStateIsS05P2OrLater() {
  return (
    currentStateIsS05P2() ||
    currentStateIsS05P3() ||
    currentStateIsS05Review() ||
    currentStateIsS06P1() ||
    currentStateIsS06P2() ||
    currentStateIsS06P3() ||
    currentStateIsS06Review()
  );
}

function currentStateIsS05Review() {
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  return (
    hasAll(quick, ["当前阶段是 S05 Review", "MA-V12-S05-REVIEW", "ACC-MA-V12-S05-REVIEW", "下一步只允许进入 S06 P1"]) &&
    hasAll(overview, ["S05 Review 已通过", "S05 整体复审已通过", "下一步是 S06 P1"]) &&
    hasAll(machine, ["当前为 S05 Review", "MA-V12-S05-REVIEW", "validate:v1.2-s05-review", "下一步是 S06 P1"]) &&
    hasAll(runGate, ["当前阶段是 S05 Review", "MA-V12-S05-REVIEW", "ACC-MA-V12-S05-REVIEW", "validate:v1.2-s05-review"])
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
    "s05p1_package_script",
    "package.json exposes the v1.2 S05 P1 validator",
    "package.json is missing the v1.2 S05 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s05p1_previous_phase_deferred_scope",
      "S04 Review execution is deferred only because open diff is limited to S05 P1 files and validator compatibility files",
      "S04 Review execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s05p1_previous_phase_deferred_until_clean_tree", "S04 Review validator will run on a clean tree after S05 P1 commit", { changed });
    return;
  }

  if (currentStateIsS05P2OrLater()) {
    pass(
      "s05p1_previous_phase_already_validated_before_s05p2",
      "S05 P1 is accepted as historical because the current state has advanced beyond S05 P1 with its own validator",
    );
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s04_review.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  });
  const parsed = parseJsonFromStdout(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S04-REVIEW",
    "s05p1_previous_s04_review",
    "S04 Review validator returns PASS before accepting S05 P1",
    "S04 Review validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateSchema() {
  validateTextFile(schemaPath);
  const schema = JSON.parse(readRepoFile(schemaPath));
  assertCondition(
    schema.task_id === taskId && schema.acceptance_id === acceptanceId && schema.status === status,
    "s05p1_schema_identity",
    "Facet schema records S05 P1 identity and status",
    "Facet schema identity is incomplete",
    { task_id: schema.task_id, acceptance_id: schema.acceptance_id, status: schema.status },
  );
  assertCondition(
    requiredFacetFields.every((field) => schema.required_fields?.includes(field)),
    "s05p1_required_fields",
    "Facet schema defines all required S05 P1 fields",
    "Facet schema is missing required S05 P1 fields",
    { requiredFacetFields, schemaFields: schema.required_fields },
  );
  assertCondition(
    schema.required_fields.every((field) => /^[a-z][a-z0-9_]*$/.test(field)),
    "s05p1_english_machine_fields",
    "Facet schema uses English snake_case machine field names",
    "Facet schema has non-English or non-snake_case field names",
    { schemaFields: schema.required_fields },
  );
  assertCondition(
    requiredFacetFields.every((field) => schema.field_contract?.[field]?.description_zh),
    "s05p1_field_contract_chinese_explanations",
    "Every required facet field has a Chinese machine-contract explanation",
    "Some required facet fields lack Chinese explanations",
    { missing: requiredFacetFields.filter((field) => !schema.field_contract?.[field]?.description_zh) },
  );
  assertCondition(
    ["chatgpt", "codex", "future_agent"].every((source) => schema.source_coverage_contract?.[source]) &&
      schema.field_contract?.source?.allowed_values?.includes("chatgpt") &&
      schema.field_contract?.source?.allowed_values?.includes("codex") &&
      schema.field_contract?.source?.allowed_values?.includes("future_agent"),
    "s05p1_source_coverage",
    "Facet schema covers ChatGPT, Codex and future agent sources",
    "Facet schema does not cover all required source types",
    schema.source_coverage_contract,
  );
  assertCondition(
    schema.phase_boundary?.does_not_implement_extractor === true &&
      schema.phase_boundary?.does_not_generate_events_json === true &&
      schema.phase_boundary?.does_not_modify_raw === true &&
      schema.phase_boundary?.next_phase === "S05 P2 extractor",
    "s05p1_phase_boundary",
    "Facet schema keeps S05 P1 bounded to schema-only work",
    "S05 P1 phase boundary is incomplete",
    schema.phase_boundary,
  );
}

function validateNoPrematureDerivedEvents() {
  const eventsAbsolutePath = path.join(repoRoot, eventsPath);
  if (currentStateIsS05P2OrLater()) {
    assertCondition(
      fs.existsSync(eventsAbsolutePath),
      "s05p1_events_json_allowed_after_s05p2",
      "events.json exists only after current state advanced beyond S05 P1",
      "Current state says S05 P2 or later but events.json is missing",
      { eventsPath },
    );
    return;
  }
  assertCondition(
    !fs.existsSync(eventsAbsolutePath),
    "s05p1_no_events_json",
    "S05 P1 does not generate data/derived/behavior_intelligence/events.json",
    "S05 P1 generated derived events before extractor phase",
    { eventsPath },
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
  assertCondition(
    hasAll(human, [
      taskId,
      acceptanceId,
      status,
      schemaPath,
      "不抽取真实事件",
      "不生成 `events.json`",
      "不把机器字段堆到首屏",
      "下一步是 S05 P2",
      ...requiredFacetFields.map((field) => `\`${field}\``),
    ]),
    "s05p1_human_page",
    "Human page explains all facet fields in Chinese and preserves no-UI-schema-dump boundary",
    "Human facet explanation page is incomplete",
  );

  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  const review = readRepoFile(reviewPath);
  const s05p2State = currentStateIsS05P2OrLater();

  assertCondition(
    s05p2State || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S05 P1", "Facet schema", "下一步只允许进入 S05 P2"]),
    "s05p1_quick_entry",
    "Human quick entry records S05 P1 state or later S05 P2 state",
    "Human quick entry is missing S05 P1 state",
  );
  assertCondition(
    s05p2State || hasAll(overview, ["S05 P1 已完成", "Facet schema", "future_agent_source", "下一步是 S05 P2"]),
    "s05p1_overview",
    "Human overview records S05 P1 state or later S05 P2 state",
    "Human overview is missing S05 P1 state",
  );
  assertCondition(
    s05p2State || hasAll(machine, ["当前为 S05 P1", taskId, acceptanceId, validatorName, "facet_event_schema.v1_2_s05_p1.json", "下一步是 S05 P2"]),
    "s05p1_machine_readme",
    "Machine README records S05 P1 identity or later S05 P2 state",
    "Machine README is missing S05 P1 state",
  );
  assertCondition(
    s05p2State || hasAll(dataContract, ["当前 S05 P1 已完成", schemaPath, "source", "future_agent_source", "下一步是 S05 P2"]),
    "s05p1_data_contract_readme",
    "Data contract README records S05 P1 schema or later S05 P2 state",
    "Data contract README is missing S05 P1 state",
  );
  assertCondition(
    s05p2State || hasAll(behavior, ["当前 S05 P1 已完成", "facets", "canonical events", "不生成 fake events", "下一步是 S05 P2"]),
    "s05p1_behavior_readme",
    "Behavior model README records S05 P1 schema boundary or later S05 P2 state",
    "Behavior model README is missing S05 P1 state",
  );
  assertCondition(
    s05p2State || hasAll(runGate, ["当前阶段是 S05 P1", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S05 P2"]),
    "s05p1_run_gate",
    "Run gate README records S05 P1 validator or later S05 P2 state",
    "Run gate README is missing S05 P1 state",
  );
  assertCondition(
    hasAll(review, [taskId, acceptanceId, status, schemaPath, humanPagePath, "No extractor in this phase", "No fake events in this phase", "S05 P2 extractor"]),
    "s05p1_review_artifact",
    "Review artifact records S05 P1 schema, boundaries and next gate",
    "S05 P1 review artifact is incomplete",
  );

  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S05 P1", "No GitHub main upload in this phase", "No extractor in this phase", "pending S05 P2"]),
      `s05p1_records_${name}`,
      `${name} records S05 P1 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S05 P1 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s05p1_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s05p1_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S05 P1 branch",
    { branch, branchName },
  );

  const remoteDevQuery = queryRemoteDevBranch();
  assertCondition(
    remoteDevQuery.output === "",
    "s05p1_no_remote_development_branch",
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
    "s05p1_open_diff_scope",
    "Open diff is limited to S05 P1 files and validator compatibility files",
    "Open diff contains files outside S05 P1 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  const s05p2OrLaterState = currentStateIsS05P2OrLater();
  const forbiddenOpenChanges = changed.filter((file) =>
    file.startsWith("OpenAIDatabase/data/public_raw/") ||
    (!s05p2OrLaterState && file === `OpenAIDatabase/${eventsPath}`) ||
    file.includes(".env") ||
    file.includes("cookies") ||
    file.includes("session_token"),
  );
  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s05p1_no_raw_events_or_secret_open_changes",
    "S05 P1 open diff does not modify raw or secret/config files; generated events are allowed only after S05 P2",
    "S05 P1 open diff modifies forbidden raw, generated event or secret-like files",
    { changed, forbiddenOpenChanges, s05p2OrLaterState },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateSchema();
    validateNoPrematureDerivedEvents();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s05_p1", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s05_p1",
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
