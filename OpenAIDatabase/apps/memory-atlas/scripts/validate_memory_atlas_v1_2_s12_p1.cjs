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

const taskId = "MA-V12-S12P1";
const acceptanceId = "ACC-MA-V12-S12P1";
const status = "phase_s12_p1_command_palette_completed_pending_s12_p2";
const validatorName = "validate:v1.2-s12-p1";
const scriptName = "validate_memory_atlas_v1_2_s12_p1.cjs";
const commandPaletteVersion = "command_palette.v1_2_s12_p1";
const laterPromptTaskId = "MA-V12-S12P2";
const laterPromptAcceptanceId = "ACC-MA-V12-S12P2";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s12_p1_command_palette.md";
const humanDocPath = "人类可读/31_CommandPalette命令面板说明.md";
const commandConfigPath = "机器治理/运行门禁/command_palette.v1_2_s12_p1.json";

const acceptedCoreCommandIds = [
  "sync_chatgpt",
  "sync_codex",
  "generate_weekly_report",
  "view_pending_proposals",
];
const personalizationCommandId = "generate_personalization_prompt";
const requiredCommandIds = [...acceptedCoreCommandIds, personalizationCommandId];
const forbiddenCommandIds = [
  "deep_explore_chatgpt",
  "auto_submit_chatgpt",
  "sync_gmail",
  "deploy_cloudflare",
  "push_github_main",
  "apply_proposal",
  "modify_raw",
];

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const textFiles = [
  reviewPath,
  humanDocPath,
  commandConfigPath,
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
  "机器治理/README.md",
  "机器治理/运行门禁/README.md",
  ...recordFiles,
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  "OpenAIDatabase/scripts/atlasctl.py",
  `OpenAIDatabase/${reviewPath}`,
  `OpenAIDatabase/${humanDocPath}`,
  `OpenAIDatabase/${commandConfigPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/机器治理/README.md",
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

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s12p1_open_diff_scope",
    "Open diff is limited to S12 P1 Command Palette files and governance records",
    "S12 P1 has unrelated OpenAIDatabase changes",
    { changed, outside, allowedOpenDiffPaths },
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
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s12p1_package_script",
    "package.json exposes the v1.2 S12 P1 validator",
    "package.json is missing the v1.2 S12 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateRuntimeContract() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");
  assertCondition(
    hasAll(app, [
      `const COMMAND_PALETTE_VERSION = "${commandPaletteVersion}" as const;`,
      "__memoryAtlasS12Phase1",
      "data-s12-p1-command-palette",
      "data-s12-p1-command-id",
      "data-s12-p1-command-count",
      "data-s12-p1-personalization-targets",
      "命令面板",
      "同步 ChatGPT",
      "同步 Codex",
      "生成本周报告",
      "查看待授权 proposal",
      "生成 personalization prompt",
      "No automatic send",
      "No raw mutation",
      "No proposal apply execution",
      ...requiredCommandIds,
    ]),
    "s12p1_runtime_contract",
    "App.tsx exposes S12 P1 command palette runtime contract and accepted commands",
    "App.tsx is missing S12 P1 command palette runtime contract",
  );
  const forbiddenPresent = forbiddenCommandIds.filter((id) => app.includes(`"${id}"`) || app.includes(`'${id}'`) || app.includes(`data-s12-p1-command-id="${id}"`));
  assertCondition(
    forbiddenPresent.length === 0,
    "s12p1_no_unaccepted_runtime_commands",
    "S12 P1 runtime does not expose unaccepted, auto-submit, apply, raw or push commands",
    "S12 P1 runtime exposes commands outside the accepted P1 scope",
    { forbiddenPresent },
  );
  assertCondition(
    hasAll(styles, [".command-palette", ".command-palette-grid", ".command-palette-action", ".command-palette-safety"]),
    "s12p1_styles",
    "S12 P1 command palette has dedicated responsive styles",
    "S12 P1 command palette styles are missing",
  );
}

function validateConfig() {
  const config = readJson(commandConfigPath);
  const commands = Array.isArray(config.commands) ? config.commands : [];
  const commandIds = commands.map((command) => command.id).sort();
  const expectedIds = [...requiredCommandIds].sort();
  const invalid = commands.filter((command) => {
    const targets = Array.isArray(command.personalization_targets) ? command.personalization_targets : [];
    return (
      !command.id ||
      !command.label_zh ||
      !command.human_action_zh ||
      command.accepted !== true ||
      command.user_trigger_required !== true ||
      command.auto_submit === true ||
      command.sends_secrets === true ||
      command.modifies_raw === true ||
      command.applies_proposal === true ||
      (command.id === personalizationCommandId && !["chatgpt", "codex", "other_agent"].every((target) => targets.includes(target)))
    );
  });
  assertCondition(
    config.schema_version === commandPaletteVersion &&
      config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      JSON.stringify(commandIds) === JSON.stringify(expectedIds) &&
      invalid.length === 0,
    "s12p1_command_config",
    "Command palette config contains only accepted P1 commands and safe personalization target coverage",
    "Command palette config does not satisfy S12 P1 command contract",
    { commandIds, expectedIds, invalid: invalid.map((command) => command.id) },
  );
}

function validateAtlasctlPromptDryRun() {
  const result = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "generate-personalization-prompt", "--dry-run"], { cwd: repoRoot }));
  const identityOk =
    (result.task_id === taskId && result.acceptance_id === acceptanceId) ||
    (result.task_id === laterPromptTaskId && result.acceptance_id === laterPromptAcceptanceId);
  assertCondition(
    result.status === "PASS" &&
      identityOk &&
      result.command === "generate-personalization-prompt" &&
      result.dry_run === true &&
      result.writes_files === false &&
      result.sends_to_chatgpt === false &&
      ["chatgpt", "codex", "other_agent"].every((target) => Array.isArray(result.targets) && result.targets.includes(target)) &&
      Array.isArray(result.source_reports) &&
      result.source_reports.includes("data/derived/behavior_intelligence/latent_signals.json") &&
      result.boundary?.user_trigger_required === true &&
      result.boundary?.no_automatic_send === true,
    "s12p1_atlasctl_prompt_dry_run",
    "atlasctl generate-personalization-prompt --dry-run exposes a safe no-write prompt contract",
    "atlasctl generate-personalization-prompt --dry-run does not satisfy S12 P1 contract",
    result,
  );
}

function validateReviewAndRecords() {
  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      validatorName,
      commandPaletteVersion,
      "同步 ChatGPT",
      "同步 Codex",
      "生成本周报告",
      "查看待授权 proposal",
      "生成 personalization prompt",
      "ChatGPT",
      "Codex",
      "other agent",
      "No automatic send",
      "No GitHub main upload",
      "No remote push",
      "No raw mutation",
      "No proposal apply execution",
      "No S12 P2 Personalization Prompt completion",
      "No S12 P3 ChatGPT deep explore execution",
      "pending S12 P2",
      ...requiredCommandIds,
    ]),
    "s12p1_review_artifact",
    "S12 P1 review artifact records accepted commands, prompt command, boundaries and pending S12 P2",
    "S12 P1 review artifact is missing required evidence",
  );
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    commandPaletteVersion,
    "同步 ChatGPT",
    "同步 Codex",
    "生成本周报告",
    "查看待授权 proposal",
    "generate_personalization_prompt",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "No proposal apply",
    "S12 P2",
  ];
  for (const relativePath of recordFiles) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s12p1_records_${relativePath}`,
      `${relativePath} records S12 P1 status, validator, boundaries and next phase`,
      `${relativePath} is missing S12 P1 record fragments`,
      { missing },
    );
  }
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(quickEntry, [taskId, "S12 P1 已完成", "命令面板", "下一步是 S12 P2", "No GitHub main upload"]),
    "s12p1_quick_entry",
    "Quick entry records completed S12 P1 and pending S12 P2",
    "Quick entry does not record completed S12 P1",
  );
  assertCondition(
    hasAll(overview, ["S12 P1 已完成", "命令面板", "同步 ChatGPT", "生成 personalization prompt", "下一步是 S12 P2"]),
    "s12p1_overview",
    "Human overview records S12 P1 command palette and pending S12 P2",
    "Human overview is missing S12 P1 status",
  );
  assertCondition(
    hasAll(machineReadme, [taskId, acceptanceId, status, validatorName, commandPaletteVersion, "S12 P2"]),
    "s12p1_machine_readme",
    "Machine README records S12 P1 gate and next phase",
    "Machine README is missing S12 P1 gate",
  );
  assertCondition(
    hasAll(runGate, [taskId, acceptanceId, status, validatorName, "S12 P1 产物", "S12 P2"]),
    "s12p1_run_gate",
    "Run gate README records S12 P1 artifact, validator and next phase",
    "Run gate README is missing S12 P1 gate",
  );
}

function validatePreviousGate() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("s12p1_previous_s11_review_deferred_until_clean_tree", "S11 Review clean-tree validator will be re-run after S12 P1 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s11_review.cjs"], { cwd: appRoot, timeout: 300000 }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S11-REVIEW",
    "s12p1_previous_s11_review",
    "S11 Review validator passes before accepting S12 P1",
    "S11 Review validator did not pass before S12 P1",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateNoRawOrForbiddenChanges() {
  const changed = getOpenChangedPaths();
  const forbiddenOpenChanges = changed.filter(
    (file) =>
      file.includes("/data/raw/") ||
      file.includes("/data/private_imports/") ||
      file.includes("/data/raw_encrypted/") ||
      file.endsWith(".env") ||
      file.includes("secrets") ||
      file.includes("credentials"),
  );
  const publicRawDiff = run("git", ["diff", "--", "OpenAIDatabase/data/public_raw", "OpenAIDatabase/data/raw"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    forbiddenOpenChanges.length === 0 && publicRawDiff.length === 0,
    "s12p1_no_raw_or_secret_open_changes",
    "S12 P1 open diff does not modify raw, private imports, credentials or secrets",
    "S12 P1 has forbidden raw or secret changes",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    validateRuntimeContract();
    validateAtlasctlPromptDryRun();
    validateConfig();
    for (const file of textFiles) validateTextFile(file);
    validateReviewAndRecords();
    validatePreviousGate();
    validateNoRawOrForbiddenChanges();
    console.log(JSON.stringify({ status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.error(JSON.stringify({
      status: "FAIL",
      validator: scriptName.replace(/\.cjs$/, ""),
      task_id: taskId,
      acceptance_id: acceptanceId,
      error: error.message,
      details: error.details || {},
      stdout: error.stdout,
      stderr: error.stderr,
      checks,
    }, null, 2));
    process.exit(1);
  }
}

main();
