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

const taskId = "MA-V12-S12P3";
const acceptanceId = "ACC-MA-V12-S12P3";
const status = "phase_s12_p3_chatgpt_deep_explore_completed_pending_s12_review";
const validatorName = "validate:v1.2-s12-p3";
const scriptName = "validate_memory_atlas_v1_2_s12_p3.cjs";
const contractVersion = "chatgpt_deep_explore.v1_2_s12_p3";
const previousValidatorName = "validate:v1.2-s12-p2";
const previousAcceptanceId = "ACC-MA-V12-S12P2";

const builderPath = "scripts/build_chatgpt_deep_explore_prompt.py";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s12_p3_chatgpt_deep_explore.md";
const humanDocPath = "人类可读/33_ChatGPT深度探索说明.md";
const configPath = "机器治理/运行门禁/chatgpt_deep_explore.v1_2_s12_p3.json";
const outputPromptPath = "data/derived/chatgpt_deep_explore/latest_memory_analysis_prompt.md";
const outputMachinePath = "data/derived/chatgpt_deep_explore/chatgpt_deep_explore_export.json";

const sourceReports = [
  "data/derived/personalization/personalization_export.json",
  "data/derived/personalization/personalization_prompt_human_zh.md",
  "data/derived/behavior_intelligence/latent_signals.json",
  "data/derived/behavior_intelligence/self_iteration_suggestions.json",
  "data/derived/behavior_intelligence/decision_debt_ledger.json",
  "data/derived/agent_collaboration/agent_collaboration_quality_report.json",
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
  builderPath,
  reviewPath,
  humanDocPath,
  configPath,
  outputPromptPath,
  outputMachinePath,
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
  `OpenAIDatabase/${builderPath}`,
  `OpenAIDatabase/${reviewPath}`,
  `OpenAIDatabase/${humanDocPath}`,
  `OpenAIDatabase/${configPath}`,
  `OpenAIDatabase/${outputPromptPath}`,
  `OpenAIDatabase/${outputMachinePath}`,
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

const forbiddenSecretFragments = [
  "BEGIN OPENAI",
  "sk-",
  "sessionid=",
  "cookie:",
  "authorization:",
  "access_token",
  "refresh_token",
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
    "s12p3_open_diff_scope",
    "Open diff is limited to S12 P3 ChatGPT deep exploration files and governance records",
    "S12 P3 has unrelated OpenAIDatabase changes",
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
    "s12p3_package_script",
    "package.json exposes the v1.2 S12 P3 validator",
    "package.json is missing the v1.2 S12 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
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
      "prefill_only",
      "auto_submit",
      "latest_memory_analysis_prompt.md",
      "chatgpt_deep_explore_export.json",
      "failure_explanation_zh",
      "sanitize_prompt",
      ...sourceReports,
    ]) &&
      hasAll(atlasctl, [
        "chatgpt-deep-explore",
        taskId,
        acceptanceId,
        contractVersion,
        builderPath,
      ]),
    "s12p3_builder_atlasctl_contract",
    "Builder and atlasctl expose S12 P3 ChatGPT deep exploration contracts",
    "Builder or atlasctl is missing S12 P3 ChatGPT deep exploration contract",
  );
}

function validateRuntimeContract() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  assertCondition(
    hasAll(app, [
      "chatgpt_deep_explore",
      "data-s12-p3-chatgpt-deep-explore",
      "打开 ChatGPT 深度探索",
      "prefill_only",
      "auto_submit",
      "No silent send",
      "No cookie/token/secret export",
      "python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only --dry-run",
    ]),
    "s12p3_runtime_contract",
    "App.tsx exposes a user-triggered S12 P3 ChatGPT deep exploration command",
    "App.tsx is missing the S12 P3 ChatGPT deep exploration command",
  );
}

function validateConfigOutputsAndAtlasctl() {
  const config = readJson(configPath);
  assertCondition(
    config.schema_version === contractVersion &&
      config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.status === status &&
      config.default_mode === "prefill_only" &&
      Array.isArray(config.allowed_modes) &&
      config.allowed_modes.includes("prefill_only") &&
      config.allowed_modes.includes("auto_submit") &&
      config.boundaries?.user_trigger_required === true &&
      config.boundaries?.no_silent_send === true &&
      config.boundaries?.no_cookie_token_secret_export === true &&
      config.boundaries?.raw_mutation === false &&
      config.boundaries?.proposal_apply_execution === false &&
      config.failure_explanations_zh?.auto_submit_not_enabled,
    "s12p3_config",
    "S12 P3 config records prefill_only default, auto_submit gate and safety boundaries",
    "S12 P3 config is missing required contract fields",
  );

  const dryRun = parseJsonFromStdout(
    run("python3", ["scripts/atlasctl.py", "chatgpt-deep-explore", "--mode", "prefill_only", "--dry-run"], { cwd: repoRoot, timeout: 180000 }),
  );
  assertCondition(
    dryRun.status === "PASS" &&
      dryRun.task_id === taskId &&
      dryRun.acceptance_id === acceptanceId &&
      dryRun.contract_version === contractVersion &&
      dryRun.dry_run === true &&
      dryRun.writes_files === false &&
      dryRun.opens_browser === false &&
      dryRun.sends_to_chatgpt === false &&
      dryRun.mode === "prefill_only" &&
      dryRun.boundary?.user_trigger_required === true,
    "s12p3_atlasctl_dry_run",
    "atlasctl chatgpt-deep-explore dry-run returns the no-write/no-send contract",
    "atlasctl chatgpt-deep-explore dry-run does not satisfy S12 P3 contract",
    dryRun,
  );

  const generate = parseJsonFromStdout(
    run("python3", ["scripts/atlasctl.py", "chatgpt-deep-explore", "--mode", "prefill_only"], { cwd: repoRoot, timeout: 180000 }),
  );
  assertCondition(
    generate.status === "PASS" &&
      generate.task_id === taskId &&
      generate.acceptance_id === acceptanceId &&
      generate.mode === "prefill_only" &&
      generate.opened_chatgpt === false &&
      generate.sends_to_chatgpt === false &&
      Array.isArray(generate.outputs) &&
      generate.outputs.includes(outputPromptPath) &&
      generate.outputs.includes(outputMachinePath) &&
      typeof generate.launch_url === "string" &&
      generate.launch_url.startsWith("https://chatgpt.com/"),
    "s12p3_atlasctl_generate",
    "atlasctl generates S12 P3 prompt payload and ChatGPT launch URL without opening or sending",
    "atlasctl chatgpt-deep-explore generation does not satisfy S12 P3 contract",
    generate,
  );

  const machine = readJson(outputMachinePath);
  assertCondition(
    machine.schema_version === "openai_database.chatgpt_deep_explore.v1_2_s12_p3" &&
      machine.task_id === taskId &&
      machine.acceptance_id === acceptanceId &&
      machine.contract_version === contractVersion &&
      machine.mode === "prefill_only" &&
      machine.safety?.sends_to_chatgpt === false &&
      machine.safety?.no_silent_send === true &&
      machine.safety?.no_cookie_token_secret_export === true &&
      machine.prompt_payload?.machine_copyable_text &&
      sourceReports.every((source) => machine.source_report_freshness?.[source]?.exists === true),
    "s12p3_machine_export",
    "Machine export records prompt payload, launch URL, source freshness and safety boundaries",
    "S12 P3 machine export does not satisfy the expected contract",
  );

  const prompt = readRepoFile(outputPromptPath);
  assertCondition(
    hasAll(prompt, [
      taskId,
      acceptanceId,
      contractVersion,
      "最新记忆分析报告",
      "深度探索提示",
      "prefill_only",
      "No silent send",
      "No cookie/token/secret export",
    ]),
    "s12p3_prompt_output",
    "Prompt output contains latest memory analysis report and exploration prompt",
    "S12 P3 prompt output is missing required content",
  );
}

function validateReviewDocsAndRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    contractVersion,
    "ChatGPT 深度探索",
    "prefill_only",
    "auto_submit",
    "用户触发",
    "No silent send",
    "No cookie/token/secret export",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "No proposal apply execution",
    "pending S12 Review",
  ];
  for (const relativePath of [reviewPath, humanDocPath, ...recordFiles]) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s12p3_records_${relativePath}`,
      `${relativePath} records S12 P3 status, validator, boundaries and next review`,
      `${relativePath} is missing S12 P3 record fragments`,
      { missing },
    );
  }

  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(quickEntry, [taskId, "S12 P3 已完成", "ChatGPT 深度探索", "下一步是 S12 Review", "No GitHub main upload"]),
    "s12p3_quick_entry",
    "Quick entry records completed S12 P3 and pending S12 Review",
    "Quick entry does not record completed S12 P3",
  );
  assertCondition(
    hasAll(overview, ["S12 P3 已完成", "ChatGPT 深度探索", "prefill_only", "auto_submit", "下一步是 S12 Review"]),
    "s12p3_overview",
    "Human overview records S12 P3 and pending S12 Review",
    "Human overview is missing S12 P3 status",
  );
  assertCondition(
    hasAll(machineReadme, [taskId, acceptanceId, status, validatorName, contractVersion, "S12 Review"]),
    "s12p3_machine_readme",
    "Machine README records S12 P3 gate and next review",
    "Machine README is missing S12 P3 gate",
  );
  assertCondition(
    hasAll(runGate, [taskId, acceptanceId, status, validatorName, "S12 P3 产物", "S12 Review"]),
    "s12p3_run_gate",
    "Run gate README records S12 P3 artifacts, validator and next review",
    "Run gate README is missing S12 P3 gate",
  );
}

function validateNoForbiddenContent() {
  const searched = [configPath, outputPromptPath, outputMachinePath, reviewPath, humanDocPath];
  const hits = [];
  for (const relativePath of searched) {
    const source = readRepoFile(relativePath).toLowerCase();
    for (const fragment of forbiddenSecretFragments) {
      if (source.includes(fragment.toLowerCase())) hits.push(`${relativePath}:${fragment}`);
    }
  }
  assertCondition(
    hits.length === 0,
    "s12p3_no_forbidden_secret_content",
    "S12 P3 outputs do not include cookie headers, tokens, API keys or authorization material",
    "S12 P3 outputs contain forbidden secret-like content",
    { hits },
  );
}

function validatePreviousGate() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("s12p3_previous_s12p2_deferred_until_clean_tree", "S12 P2 clean-tree validator will be re-run after S12 P3 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s12_p2.cjs"], { cwd: appRoot, timeout: 300000 }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === previousAcceptanceId,
    "s12p3_previous_s12p2",
    "S12 P2 validator passes before accepting S12 P3",
    "S12 P2 validator did not pass before S12 P3",
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
    "s12p3_no_raw_or_secret_open_changes",
    "S12 P3 open diff does not modify raw, private imports, credentials or secrets",
    "S12 P3 has forbidden raw or secret changes",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    validateBuilderAndAtlasctlContract();
    validateRuntimeContract();
    for (const file of textFiles) validateTextFile(file);
    validateConfigOutputsAndAtlasctl();
    validateReviewDocsAndRecords();
    validateNoForbiddenContent();
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
