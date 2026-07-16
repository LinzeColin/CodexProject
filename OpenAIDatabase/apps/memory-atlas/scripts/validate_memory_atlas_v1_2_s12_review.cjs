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

const taskId = "MA-V12-S12-REVIEW";
const acceptanceId = "ACC-MA-V12-S12-REVIEW";
const status = "stage_s12_review_passed_pending_s13_no_github_main_upload";
const validatorName = "validate:v1.2-s12-review";
const scriptName = "validate_memory_atlas_v1_2_s12_review.cjs";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s12_review.md";
const commandPaletteVersion = "command_palette.v1_2_s12_p1";
const personalizationVersion = "personalization_prompt.v1_2_s12_p2";
const chatgptDeepExploreVersion = "chatgpt_deep_explore.v1_2_s12_p3";

const phaseValidators = [
  ["validate:v1.2-s12-p1", "validate_memory_atlas_v1_2_s12_p1.cjs", "MA-V12-S12P1", "ACC-MA-V12-S12P1"],
  ["validate:v1.2-s12-p2", "validate_memory_atlas_v1_2_s12_p2.cjs", "MA-V12-S12P2", "ACC-MA-V12-S12P2"],
  ["validate:v1.2-s12-p3", "validate_memory_atlas_v1_2_s12_p3.cjs", "MA-V12-S12P3", "ACC-MA-V12-S12P3"],
];

const acceptedRuntimeCommandIds = [
  "sync_chatgpt",
  "sync_codex",
  "generate_weekly_report",
  "view_pending_proposals",
  "generate_personalization_prompt",
  "chatgpt_deep_explore",
];

const forbiddenRuntimeCommandIds = [
  "push_github_main",
  "apply_proposal",
  "modify_raw",
  "deploy_cloudflare",
  "sync_gmail",
  "auto_submit_chatgpt",
  "deep_explore_chatgpt",
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
  `OpenAIDatabase/${reviewPath}`,
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
  "OPENAI_API_KEY",
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

function runAllowFailure(command, args, options = {}) {
  return spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: "utf8",
    stdio: "pipe",
    maxBuffer: 128 * 1024 * 1024,
    timeout: options.timeout || 0,
  });
}

function parseJsonFromStdout(result) {
  const stdout = result.stdout.trim();
  const start = stdout.indexOf("{");
  if (start < 0) throw new Error("stdout does not contain JSON object");
  return JSON.parse(stdout.slice(start));
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
    "s12_review_open_diff_scope",
    "Open diff is limited to S12 Review files and governance records",
    "S12 Review has unrelated OpenAIDatabase changes",
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
    "s12_review_package_script",
    "package.json exposes the v1.2 S12 Review validator",
    "package.json is missing the v1.2 S12 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePhaseValidators() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("s12_review_phase_validators_deferred_until_clean_tree", "S12 P1/P2/P3 clean-tree validators will be re-run after S12 Review commit", { changed });
    return;
  }
  const packageJson = readJson("apps/memory-atlas/package.json");
  const details = {};
  for (const [script, file, phaseTaskId, phaseAcceptanceId] of phaseValidators) {
    assertCondition(
      packageJson.scripts?.[script] === `node scripts/${file}`,
      `s12_review_phase_script_${script}`,
      `${script} is registered`,
      `${script} is missing from package.json`,
      { script: packageJson.scripts?.[script] },
    );
    const result = parseJsonFromStdout(run("node", [`scripts/${file}`], { cwd: appRoot, timeout: 300000 }));
    details[script] = {
      status: result.status,
      task_id: result.task_id,
      acceptance_id: result.acceptance_id,
    };
    assertCondition(
      result.status === "PASS" && result.task_id === phaseTaskId && result.acceptance_id === phaseAcceptanceId,
      `s12_review_phase_gate_${script}`,
      `${script} passes with expected task and acceptance ids`,
      `${script} did not pass with expected task and acceptance ids`,
      details[script],
    );
  }
  pass("s12_review_phase_validator_chain", "S12 P1/P2/P3 validators pass in sequence", details);
}

function validateCommandPaletteAcceptance() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const commandsStart = app.indexOf("const commands: CommandPaletteCommand[] = [");
  const commandsEnd = app.indexOf("  return {\n    version: COMMAND_PALETTE_VERSION", commandsStart);
  assertCondition(
    commandsStart >= 0 && commandsEnd > commandsStart,
    "s12_review_command_palette_source_region",
    "App.tsx contains a parseable S12 command palette command region",
    "App.tsx command palette command region could not be found",
  );
  const commandRegion = app.slice(commandsStart, commandsEnd);
  const runtimeIds = Array.from(commandRegion.matchAll(/id: "([^"]+)"/g)).map((match) => match[1]);
  const unexpected = runtimeIds.filter((id) => !acceptedRuntimeCommandIds.includes(id));
  const missing = acceptedRuntimeCommandIds.filter((id) => !runtimeIds.includes(id));
  const forbiddenPresent = forbiddenRuntimeCommandIds.filter((id) => app.includes(id));

  assertCondition(
    runtimeIds.length === acceptedRuntimeCommandIds.length && missing.length === 0 && unexpected.length === 0 && forbiddenPresent.length === 0,
    "s12_review_command_palette_accepted_ids",
    "Runtime command palette exposes only the accepted S12 commands",
    "Runtime command palette contains missing, unexpected or forbidden command ids",
    { runtimeIds, expected: acceptedRuntimeCommandIds, missing, unexpected, forbiddenPresent },
  );
  assertCondition(
    hasAll(app, [
      commandPaletteVersion,
      "sync_chatgpt",
      "sync_codex",
      "generate_weekly_report",
      "view_pending_proposals",
      "generate_personalization_prompt",
      "chatgpt_deep_explore",
      "data-s12-p1-command-palette",
      "data-s12-p3-chatgpt-deep-explore-command",
      "打开 ChatGPT 深度探索",
      "No silent send",
      "No cookie/token/secret export",
    ]),
    "s12_review_command_palette_runtime_contract",
    "App.tsx records command panel controls, personalization entry and ChatGPT deep exploration entry",
    "App.tsx is missing required S12 command palette runtime fragments",
  );

  const commandConfig = readJson("机器治理/运行门禁/command_palette.v1_2_s12_p1.json");
  const configIds = Array.isArray(commandConfig.commands) ? commandConfig.commands.map((command) => command.id) : [];
  assertCondition(
    commandConfig.schema_version === commandPaletteVersion &&
      commandConfig.personalization_command_id === "generate_personalization_prompt" &&
      JSON.stringify(configIds) === JSON.stringify(acceptedRuntimeCommandIds.slice(0, 5)) &&
      commandConfig.boundaries?.s12_p3_chatgpt_deep_explore_execution === false,
    "s12_review_command_palette_config",
    "Command palette config keeps the accepted P1 commands and defers ChatGPT execution to S12 P3 runtime contract",
    "Command palette config does not match accepted command contract",
    { configIds },
  );
}

function validatePersonalizationAndChatgptContracts() {
  const personalizationConfig = readJson("机器治理/运行门禁/personalization_prompt.v1_2_s12_p2.json");
  assertCondition(
    personalizationConfig.schema_version === personalizationVersion &&
      personalizationConfig.task_id === "MA-V12-S12P2" &&
      personalizationConfig.acceptance_id === "ACC-MA-V12-S12P2" &&
      personalizationConfig.boundaries?.no_automatic_send === true &&
      personalizationConfig.boundaries?.no_cookie_token_secret_export === true &&
      (personalizationConfig.boundaries?.raw_mutation === false || personalizationConfig.boundaries?.no_raw_mutation === true) &&
      (personalizationConfig.boundaries?.proposal_apply_execution === false ||
        personalizationConfig.boundaries?.no_proposal_apply_execution === true),
    "s12_review_personalization_config",
    "S12 P2 personalization prompt config preserves no-send/no-secret/no-raw boundaries",
    "S12 P2 personalization prompt config is missing safety boundaries",
  );

  const promptDryRun = parseJsonFromStdout(
    run("python3", ["scripts/atlasctl.py", "generate-personalization-prompt", "--dry-run"], { cwd: repoRoot, timeout: 180000 }),
  );
  assertCondition(
    promptDryRun.status === "PASS" &&
      promptDryRun.task_id === "MA-V12-S12P2" &&
      promptDryRun.acceptance_id === "ACC-MA-V12-S12P2" &&
      promptDryRun.dry_run === true &&
      promptDryRun.writes_files === false &&
      promptDryRun.sends_to_chatgpt === false,
    "s12_review_personalization_dry_run",
    "atlasctl personalization prompt dry-run is no-write and no-send",
    "atlasctl personalization prompt dry-run does not satisfy S12 Review boundary",
    promptDryRun,
  );

  const chatgptConfig = readJson("机器治理/运行门禁/chatgpt_deep_explore.v1_2_s12_p3.json");
  assertCondition(
    chatgptConfig.schema_version === chatgptDeepExploreVersion &&
      chatgptConfig.task_id === "MA-V12-S12P3" &&
      chatgptConfig.acceptance_id === "ACC-MA-V12-S12P3" &&
      chatgptConfig.default_mode === "prefill_only" &&
      chatgptConfig.boundaries?.no_silent_send === true &&
      chatgptConfig.boundaries?.no_cookie_token_secret_export === true &&
      chatgptConfig.boundaries?.raw_mutation === false &&
      chatgptConfig.boundaries?.proposal_apply_execution === false &&
      chatgptConfig.failure_explanations_zh?.auto_submit_not_enabled,
    "s12_review_chatgpt_config",
    "S12 P3 ChatGPT deep exploration config preserves prefill_only default and auto_submit gate",
    "S12 P3 ChatGPT deep exploration config is missing safety boundaries",
  );

  const chatgptDryRun = parseJsonFromStdout(
    run("python3", ["scripts/atlasctl.py", "chatgpt-deep-explore", "--mode", "prefill_only", "--dry-run"], { cwd: repoRoot, timeout: 180000 }),
  );
  assertCondition(
    chatgptDryRun.status === "PASS" &&
      chatgptDryRun.task_id === "MA-V12-S12P3" &&
      chatgptDryRun.acceptance_id === "ACC-MA-V12-S12P3" &&
      chatgptDryRun.dry_run === true &&
      chatgptDryRun.writes_files === false &&
      chatgptDryRun.opens_browser === false &&
      chatgptDryRun.sends_to_chatgpt === false &&
      chatgptDryRun.mode === "prefill_only",
    "s12_review_chatgpt_prefill_dry_run",
    "atlasctl ChatGPT deep exploration prefill dry-run is no-write, no-open and no-send",
    "atlasctl ChatGPT deep exploration dry-run does not satisfy S12 Review boundary",
    chatgptDryRun,
  );

  const autoSubmit = runAllowFailure("python3", ["scripts/atlasctl.py", "chatgpt-deep-explore", "--mode", "auto_submit", "--apply"], {
    cwd: repoRoot,
    timeout: 180000,
  });
  const autoSubmitJson = parseJsonFromStdout(autoSubmit);
  assertCondition(
    autoSubmit.status === 2 &&
      autoSubmitJson.status === "FAIL_CLOSED" &&
      autoSubmitJson.task_id === "MA-V12-S12P3" &&
      autoSubmitJson.acceptance_id === "ACC-MA-V12-S12P3" &&
      autoSubmitJson.mode === "auto_submit" &&
      autoSubmitJson.sends_to_chatgpt === false &&
      typeof autoSubmitJson.failure_explanation_zh === "string" &&
      autoSubmitJson.failure_explanation_zh.includes("auto_submit 未开启"),
    "s12_review_chatgpt_auto_submit_fail_closed",
    "auto_submit fails closed with Chinese explanation and sends nothing",
    "auto_submit did not fail closed as required",
    { status: autoSubmit.status, stdout: autoSubmitJson },
  );
}

function validateReviewArtifact() {
  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      validatorName,
      "S12 Review",
      "S12 P1",
      "S12 P2",
      "S12 P3",
      "Command Palette",
      "Personalization Prompt",
      "ChatGPT 深度探索",
      commandPaletteVersion,
      personalizationVersion,
      chatgptDeepExploreVersion,
      "sync_chatgpt",
      "sync_codex",
      "generate_weekly_report",
      "view_pending_proposals",
      "generate_personalization_prompt",
      "chatgpt_deep_explore",
      "prefill_only",
      "auto_submit",
      "FAIL_CLOSED",
      "No silent send",
      "No cookie/token/secret export",
      "No GitHub main upload",
      "No remote push",
      "No raw mutation",
      "No proposal apply execution",
      "pending S13 P1",
    ]),
    "s12_review_artifact",
    "S12 Review artifact records phase chain, accepted commands, prompt/deep-explore gates, boundaries and pending S13 P1",
    "S12 Review artifact is missing required review evidence",
  );
}

function validateRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    "S12 Review",
    "S12 P1",
    "S12 P2",
    "S12 P3",
    "Command Palette",
    "Personalization Prompt",
    "ChatGPT 深度探索",
    "prefill_only",
    "auto_submit",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "No proposal apply",
    "S13 P1",
  ];
  for (const relativePath of recordFiles) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s12_review_records_${relativePath}`,
      `${relativePath} records S12 Review status, validator, boundaries and next phase`,
      `${relativePath} is missing S12 Review record fragments`,
      { missing },
    );
  }
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(quickEntry, [taskId, "S12 Review 已完成", "下一步是 S13 P1", "No GitHub main upload"]),
    "s12_review_quick_entry",
    "Quick entry records completed S12 Review and pending S13 P1",
    "Quick entry does not record completed S12 Review",
  );
  assertCondition(
    hasAll(overview, ["S12 Review 已完成", "Command Palette", "Personalization Prompt", "ChatGPT 深度探索", "下一步是 S13 P1"]),
    "s12_review_overview",
    "Human overview records S12 Review pass gate and pending S13 P1",
    "Human overview is missing S12 Review pass gate",
  );
  assertCondition(
    hasAll(machineReadme, [taskId, acceptanceId, status, validatorName, "S13 P1"]),
    "s12_review_machine_readme",
    "Machine README records S12 Review gate and next phase",
    "Machine README is missing S12 Review gate",
  );
  assertCondition(
    hasAll(runGate, [taskId, acceptanceId, status, validatorName, "S12 Review 产物", "S13 P1"]),
    "s12_review_run_gate",
    "Run gate README records S12 Review artifact, validator and next phase",
    "Run gate README is missing S12 Review gate",
  );
}

function validateNoForbiddenContent() {
  const searched = [
    reviewPath,
    "data/derived/personalization/personalization_export.json",
    "data/derived/personalization/chatgpt_personalization.md",
    "data/derived/personalization/codex_personalization.md",
    "data/derived/personalization/other_agent_personalization.md",
    "data/derived/chatgpt_deep_explore/latest_memory_analysis_prompt.md",
    "data/derived/chatgpt_deep_explore/chatgpt_deep_explore_export.json",
  ];
  const hits = [];
  for (const relativePath of searched) {
    const source = readRepoFile(relativePath).toLowerCase();
    for (const fragment of forbiddenSecretFragments) {
      if (source.includes(fragment.toLowerCase())) hits.push(`${relativePath}:${fragment}`);
    }
  }
  assertCondition(
    hits.length === 0,
    "s12_review_no_forbidden_secret_content",
    "S12 review outputs do not include cookie headers, tokens, API keys or authorization material",
    "S12 review outputs contain forbidden secret-like content",
    { hits },
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
    "s12_review_no_raw_or_secret_open_changes",
    "S12 Review open diff does not modify raw, private imports, credentials or secrets",
    "S12 Review has forbidden raw or secret changes",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    for (const file of textFiles) validateTextFile(file);
    validateReviewArtifact();
    validateCommandPaletteAcceptance();
    validatePersonalizationAndChatgptContracts();
    validatePhaseValidators();
    validateRecords();
    validateNoForbiddenContent();
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
