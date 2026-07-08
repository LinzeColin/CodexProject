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

const taskId = "MA-V12-S13P2";
const acceptanceId = "ACC-MA-V12-S13P2";
const status = "phase_s13_p2_diff_narrator_completed_pending_s13_p3";
const validatorName = "validate:v1.2-s13-p2";
const scriptName = "validate_memory_atlas_v1_2_s13_p2.cjs";
const contractVersion = "diff_narrator.v1_2_s13_p2";
const previousValidatorName = "validate:v1.2-s13-p1";
const previousAcceptanceId = "ACC-MA-V12-S13P1";

const builderPath = "scripts/build_memory_atlas_diff_narrator.py";
const configPath = "机器治理/运行门禁/diff_narrator.v1_2_s13_p2.json";
const outputPath = "data/derived/proposals/diff_narrator_report.json";
const machineDiffPath = "机器治理/证据与日志/proposal_diffs/diff_narrator_machine_diff.v1_2_s13_p2.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s13_p2_diff_narrator.md";
const humanDocPath = "人类可读/35_DiffNarrator说明.md";

const requiredNarratorSections = [
  "what_changed_zh",
  "why_changed_zh",
  "affected_surfaces_zh",
  "how_to_verify_zh",
  "how_to_rollback_zh",
];

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const requiredFiles = [
  builderPath,
  configPath,
  outputPath,
  machineDiffPath,
  reviewPath,
  humanDocPath,
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
  "机器治理/README.md",
  "机器治理/运行门禁/README.md",
  "机器治理/证据与日志/README.md",
  ...recordFiles,
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/scripts/atlasctl.py",
  `OpenAIDatabase/${builderPath}`,
  `OpenAIDatabase/${configPath}`,
  `OpenAIDatabase/${outputPath}`,
  `OpenAIDatabase/${machineDiffPath}`,
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
  "OpenAIDatabase/机器治理/运行门禁/README.md",
  "OpenAIDatabase/机器治理/证据与日志/README.md",
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
  const start = stdout.indexOf("{");
  if (start < 0) throw new Error("stdout does not contain JSON object");
  return JSON.parse(stdout.slice(start));
}

function repoPath(relativePath) {
  return path.join(repoRoot, relativePath);
}

function readRepoFile(relativePath) {
  return fs.readFileSync(repoPath(relativePath), "utf8");
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

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s13p2_package_script",
    "package.json exposes the v1.2 S13 P2 validator",
    "package.json is missing the v1.2 S13 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s13p2_open_diff_scope",
    "Open diff is limited to S13 P2 diff narrator files and governance records",
    "S13 P2 has unrelated OpenAIDatabase changes",
    { changed, outside, allowedOpenDiffPaths },
  );
}

function validateRequiredFilesExist() {
  const missing = requiredFiles.filter((relativePath) => !fs.existsSync(repoPath(relativePath)));
  assertCondition(
    missing.length === 0,
    "s13p2_required_files_exist",
    "S13 P2 diff narrator files exist",
    "S13 P2 is missing required diff narrator files",
    { missing },
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

function validateConfig() {
  const config = readJson(configPath);
  const sections = config.diff_narrator?.required_human_sections || [];
  const missingSections = requiredNarratorSections.filter((section) => !sections.includes(section));
  assertCondition(
    config.schema_version === contractVersion &&
      config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.status === status &&
      config.validator === validatorName &&
      missingSections.length === 0 &&
      config.diff_narrator?.language === "zh" &&
      config.diff_narrator?.human_homepage_policy?.no_full_machine_diff === true &&
      config.diff_narrator?.machine_diff_evidence_path === machineDiffPath &&
      config.scope_boundary?.raw_mutation === false &&
      config.scope_boundary?.proposal_apply_execution === false &&
      config.scope_boundary?.rollback_execution === false &&
      config.scope_boundary?.github_main_upload === false &&
      config.scope_boundary?.remote_push === false,
    "s13p2_config",
    "S13 P2 config records Chinese diff narrator sections, machine evidence path and no-apply boundaries",
    "S13 P2 config does not satisfy diff narrator contract",
    { missingSections },
  );
}

function validateBuilderAndAtlasctlContract() {
  const builder = readRepoFile(builderPath);
  const atlasctl = readRepoFile("scripts/atlasctl.py");
  assertCondition(
    hasAll(builder, [
      taskId,
      acceptanceId,
      contractVersion,
      status,
      "what_changed_zh",
      "why_changed_zh",
      "affected_surfaces_zh",
      "how_to_verify_zh",
      "how_to_rollback_zh",
      "diff_narrator_report.json",
      "diff_narrator_machine_diff.v1_2_s13_p2.json",
    ]) &&
      hasAll(atlasctl, [
        "diff-narrator",
        taskId,
        acceptanceId,
        contractVersion,
        builderPath,
      ]),
    "s13p2_builder_atlasctl_contract",
    "Builder and atlasctl expose S13 P2 diff narrator contracts",
    "Builder or atlasctl is missing S13 P2 diff narrator contract",
  );
}

function validateOutputAndMachineEvidence() {
  const output = readJson(outputPath);
  const machine = readJson(machineDiffPath);
  const narrations = Array.isArray(output.narrations) ? output.narrations : [];
  const machineDiffs = Array.isArray(machine.machine_diffs) ? machine.machine_diffs : [];
  const invalid = [];
  for (const item of narrations) {
    const id = item.proposal_id || "unknown";
    for (const section of requiredNarratorSections) {
      if (!item[section] || String(item[section]).trim().length < 8) invalid.push(`${id}:${section}`);
    }
    if (item.machine_diff_inline_in_human_summary !== false) invalid.push(`${id}:machine_diff_inline`);
    if (item.machine_diff_ref !== machineDiffPath) invalid.push(`${id}:machine_diff_ref`);
    if (item.apply_execution_allowed !== false) invalid.push(`${id}:apply_allowed`);
    if (item.raw_apply_target_allowed !== false) invalid.push(`${id}:raw_allowed`);
  }
  for (const item of machineDiffs) {
    const id = item.proposal_id || "unknown";
    if (!item.before_after_diff || typeof item.before_after_diff !== "object") invalid.push(`${id}:missing_machine_diff`);
    if (!Array.isArray(item.target_files) || item.target_files.length === 0) invalid.push(`${id}:missing_target_files`);
  }
  assertCondition(
    output.schema_version === "openai_database.diff_narrator.v1_2_s13_p2" &&
      output.task_id === taskId &&
      output.acceptance_id === acceptanceId &&
      output.status === status &&
      output.contract_version === contractVersion &&
      output.summary?.narration_count >= 5 &&
      output.summary?.all_narrations_have_required_sections === true &&
      output.summary?.machine_diff_kept_out_of_human_homepage === true &&
      output.summary?.proposal_apply_execution === false &&
      output.summary?.raw_mutation === false &&
      output.machine_diff_evidence_path === machineDiffPath &&
      output.phase_boundary?.does_not_apply_proposals === true &&
      output.phase_boundary?.does_not_modify_raw === true &&
      output.phase_boundary?.next_phase === "S13 P3" &&
      machine.schema_version === "openai_database.diff_narrator_machine_diff.v1_2_s13_p2" &&
      machine.task_id === taskId &&
      machine.acceptance_id === acceptanceId &&
      machineDiffs.length === narrations.length &&
      invalid.length === 0,
    "s13p2_output_machine_evidence",
    "S13 P2 output records Chinese narrations and keeps machine diff evidence out of the human homepage",
    "S13 P2 output or machine evidence does not satisfy diff narrator contract",
    { narrationCount: narrations.length, machineDiffCount: machineDiffs.length, invalid },
  );

  const dryRun = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "proposals", "--view", "diff-narrator", "--dry-run"], { cwd: repoRoot, timeout: 180000 }));
  assertCondition(
    dryRun.status === "PASS" &&
      dryRun.task_id === taskId &&
      dryRun.acceptance_id === acceptanceId &&
      dryRun.contract_version === contractVersion &&
      dryRun.dry_run === true &&
      dryRun.writes_files === false &&
      dryRun.applies_proposals === false &&
      dryRun.raw_mutation === false &&
      dryRun.output_contract?.report === outputPath &&
      dryRun.output_contract?.machine_diff_evidence === machineDiffPath &&
      dryRun.summary?.machine_diff_kept_out_of_human_homepage === true,
    "s13p2_atlasctl_diff_narrator_dry_run",
    "atlasctl proposals --view diff-narrator --dry-run returns the no-write/no-apply S13 P2 contract",
    "atlasctl diff narrator dry-run does not satisfy S13 P2 contract",
    dryRun,
  );
}

function validateDocsAndRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    contractVersion,
    "S13 P2",
    "Diff narrator",
    "改了什么",
    "为什么改",
    "影响什么",
    "如何验证",
    "如何回滚",
    "机器 diff",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "No proposal apply execution",
    "pending S13 P3",
  ];
  for (const relativePath of [reviewPath, humanDocPath, ...recordFiles]) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s13p2_records_${relativePath}`,
      `${relativePath} records S13 P2 status, narrator sections, validator, boundaries and next phase`,
      `${relativePath} is missing S13 P2 record fragments`,
      { missing },
    );
  }

  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  assertCondition(
    hasAll(quickEntry, ["MA-V12-S13P2", "S13 P2 已完成", "Diff narrator", "机器 diff", "下一步是 S13 P3", "No GitHub main upload"]),
    "s13p2_quick_entry",
    "Quick entry records completed S13 P2 and pending S13 P3 without full machine diff",
    "Quick entry does not record S13 P2 completion",
  );

  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  assertCondition(
    hasAll(overview, ["S13 P2 已完成", "Diff narrator", "改了什么", "如何验证", "下一步是 S13 P3"]),
    "s13p2_overview",
    "Human overview records S13 P2 diff narrator and pending S13 P3",
    "Human overview does not record S13 P2 completion",
  );

  const machineReadme = readRepoFile("机器治理/README.md");
  assertCondition(
    hasAll(machineReadme, [taskId, acceptanceId, status, validatorName, contractVersion, "S13 P3"]),
    "s13p2_machine_readme",
    "Machine README records S13 P2 gate and next phase",
    "Machine README does not record S13 P2 gate",
  );

  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(runGate, [taskId, acceptanceId, status, validatorName, "S13 P2 产物", "S13 P2 gate", "S13 P3"]),
    "s13p2_run_gate",
    "Run gate README records S13 P2 artifacts, validator and next phase",
    "Run gate README does not record S13 P2",
  );

  const evidenceReadme = readRepoFile("机器治理/证据与日志/README.md");
  assertCondition(
    hasAll(evidenceReadme, [machineDiffPath, "机器 diff", "Diff narrator", "S13 P2"]),
    "s13p2_evidence_readme",
    "Evidence README records the S13 P2 machine diff evidence file",
    "Evidence README does not record S13 P2 machine diff evidence",
  );
}

function validatePreviousGate() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("s13p2_previous_s13p1_deferred_until_clean_tree", "S13 P1 clean-tree validator will be re-run after S13 P2 commit", { changed });
    return;
  }
  const result = parseJsonFromStdout(run("pnpm", ["--dir", "apps/memory-atlas", "run", previousValidatorName], { cwd: repoRoot, timeout: 300000 }));
  assertCondition(
    result.status === "PASS" && result.acceptance_id === previousAcceptanceId,
    "s13p2_previous_s13p1",
    "S13 P1 validator passes before accepting S13 P2",
    "S13 P1 validator failed before accepting S13 P2",
    { status: result.status, acceptance_id: result.acceptance_id },
  );
}

function validateNoRawOrSecretOpenChanges() {
  const changed = getOpenChangedPaths();
  const forbiddenOpenChanges = changed.filter((file) =>
    file.includes("/data/public_raw/") ||
    file.includes("/data/raw/") ||
    file.includes("/data/private_imports/") ||
    file.toLowerCase().includes("credentials") ||
    file.toLowerCase().includes("cookies") ||
    file.toLowerCase().includes("tokens"),
  );
  const publicRawDiff = spawnSync("git", ["diff", "--", "OpenAIDatabase/data/public_raw", "OpenAIDatabase/data/raw", "OpenAIDatabase/data/private_imports"], {
    cwd: worktreeRoot,
    encoding: "utf8",
    stdio: "pipe",
    maxBuffer: 64 * 1024 * 1024,
  });
  assertCondition(
    forbiddenOpenChanges.length === 0 && publicRawDiff.stdout.trim() === "",
    "s13p2_no_raw_or_secret_open_changes",
    "S13 P2 open diff does not modify raw, private imports, credentials or secrets",
    "S13 P2 open diff touches raw/private/credential paths",
    { changed, forbiddenOpenChanges, publicRawDiff: publicRawDiff.stdout.slice(0, 2000) },
  );
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    validateRequiredFilesExist();
    for (const file of requiredFiles) validateTextFile(file);
    validateConfig();
    validateBuilderAndAtlasctlContract();
    validateOutputAndMachineEvidence();
    validateDocsAndRecords();
    validatePreviousGate();
    validateNoRawOrSecretOpenChanges();
    console.log(JSON.stringify({ status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.error(
      JSON.stringify(
        {
          status: "FAIL",
          validator: "validate_memory_atlas_v1_2_s13_p2",
          task_id: taskId,
          acceptance_id: acceptanceId,
          error: error.message,
          details: error.details || {},
          checks,
        },
        null,
        2,
      ),
    );
    process.exit(1);
  }
}

main();
