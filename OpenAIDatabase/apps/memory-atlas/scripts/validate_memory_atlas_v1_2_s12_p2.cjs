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

const taskId = "MA-V12-S12P2";
const acceptanceId = "ACC-MA-V12-S12P2";
const status = "phase_s12_p2_personalization_prompt_completed_pending_s12_p3";
const validatorName = "validate:v1.2-s12-p2";
const scriptName = "validate_memory_atlas_v1_2_s12_p2.cjs";
const promptVersion = "personalization_prompt.v1_2_s12_p2";
const previousValidatorName = "validate:v1.2-s12-p1";
const previousAcceptanceId = "ACC-MA-V12-S12P1";

const reviewPath = "docs/reviews/memory_atlas_v1_2_s12_p2_personalization_prompt.md";
const humanDocPath = "人类可读/32_PersonalizationPrompt说明.md";
const promptConfigPath = "机器治理/运行门禁/personalization_prompt.v1_2_s12_p2.json";
const outputs = {
  humanZh: "data/derived/personalization/personalization_prompt_human_zh.md",
  chatgpt: "data/derived/personalization/chatgpt_personalization.md",
  codex: "data/derived/personalization/codex_personalization.md",
  otherAgent: "data/derived/personalization/other_agent_personalization.md",
  machine: "data/derived/personalization/personalization_export.json",
};

const sourceReports = [
  "data/derived/personalization/personalization_export.json",
  "data/derived/behavior_intelligence/events.json",
  "data/derived/behavior_intelligence/clusters.json",
  "data/derived/behavior_intelligence/latent_signals.json",
  "data/derived/behavior_intelligence/self_iteration_suggestions.json",
  "data/derived/behavior_intelligence/decision_debt_ledger.json",
  "data/derived/agent_collaboration/agent_collaboration_quality_report.json",
];

const targetIds = ["chatgpt", "codex", "other_agent"];
const targetFiles = [outputs.chatgpt, outputs.codex, outputs.otherAgent];
const targetLabels = ["ChatGPT", "Codex", "other agent"];
const forbiddenFragments = [
  "BEGIN OPENAI",
  "sk-",
  "sessionid=",
  "cookie:",
  "authorization:",
  "auto_submit_chatgpt",
  "deep_explore_chatgpt",
  "apply_proposal",
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
  promptConfigPath,
  outputs.humanZh,
  outputs.chatgpt,
  outputs.codex,
  outputs.otherAgent,
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
  "机器治理/README.md",
  "机器治理/运行门禁/README.md",
  ...recordFiles,
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s12_p1.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/scripts/atlasctl.py",
  "OpenAIDatabase/scripts/build_personalization_exports.py",
  `OpenAIDatabase/${reviewPath}`,
  `OpenAIDatabase/${humanDocPath}`,
  `OpenAIDatabase/${promptConfigPath}`,
  `OpenAIDatabase/${outputs.humanZh}`,
  `OpenAIDatabase/${outputs.chatgpt}`,
  `OpenAIDatabase/${outputs.codex}`,
  `OpenAIDatabase/${outputs.otherAgent}`,
  `OpenAIDatabase/${outputs.machine}`,
  "OpenAIDatabase/data/run_logs/evidence/TASK-OAI-D-001-build-exports.txt",
  "OpenAIDatabase/data/run_logs/export_runs/2026-07-08.jsonl",
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
    "s12p2_open_diff_scope",
    "Open diff is limited to S12 P2 Personalization Prompt files and governance records",
    "S12 P2 has unrelated OpenAIDatabase changes",
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
    "s12p2_package_script",
    "package.json exposes the v1.2 S12 P2 validator",
    "package.json is missing the v1.2 S12 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateBuilderContract() {
  const builder = readRepoFile("scripts/build_personalization_exports.py");
  const atlasctl = readRepoFile("scripts/atlasctl.py");
  assertCondition(
    hasAll(builder, [
      `S12_P2_PROMPT_VERSION = "${promptVersion}"`,
      "OTHER_AGENT_EXPORT",
      "HUMAN_ZH_EXPORT",
      "render_other_agent",
      "render_human_zh",
      "machine_copyable_prompt",
      "source_report_freshness",
      ...sourceReports,
    ]) &&
      hasAll(atlasctl, [
        "ACC-MA-V12-S12P2",
        "MA-V12-S12P2",
        promptVersion,
        outputs.humanZh,
        outputs.otherAgent,
      ]),
    "s12p2_builder_contract",
    "Personalization builder and atlasctl expose S12 P2 prompt-generation contracts",
    "Personalization builder or atlasctl is missing S12 P2 prompt-generation contract",
  );
}

function validatePromptOutputs() {
  const machine = readJson(outputs.machine);
  const prompts = machine.prompts && typeof machine.prompts === "object" ? machine.prompts : {};
  const freshness = machine.source_report_freshness && typeof machine.source_report_freshness === "object" ? machine.source_report_freshness : {};
  const missingReports = sourceReports.filter((source) => !freshness[source] || freshness[source].exists !== true);
  const missingTargets = targetIds.filter((target) => {
    const prompt = prompts[target];
    return !prompt || !prompt.machine_copyable_text || !prompt.human_explanation_zh || prompt.user_trigger_required !== true;
  });
  assertCondition(
    machine.schema_version === "openai_database.personalization_export.v1_2_s12_p2" &&
      machine.task_id === taskId &&
      machine.acceptance_id === acceptanceId &&
      machine.prompt_version === promptVersion &&
      targetIds.every((target) => Array.isArray(machine.targets) && machine.targets.includes(target)) &&
      missingTargets.length === 0 &&
      missingReports.length === 0 &&
      machine.safety?.raw_private_data_included === false &&
      machine.safety?.plaintext_secrets_included === false &&
      machine.safety?.sends_to_chatgpt === false,
    "s12p2_machine_export",
    "Machine export contains S12 P2 identity, prompt targets, source freshness and safety boundaries",
    "Machine export does not satisfy S12 P2 prompt contract",
    { schema_version: machine.schema_version, task_id: machine.task_id, acceptance_id: machine.acceptance_id, missingTargets, missingReports },
  );

  const human = readRepoFile(outputs.humanZh);
  assertCondition(
    hasAll(human, [
      taskId,
      acceptanceId,
      status,
      promptVersion,
      "中文人类说明",
      "机器可复制文本",
      "ChatGPT",
      "Codex",
      "other agent",
      "No automatic send",
      "No raw mutation",
      "No proposal apply execution",
      "No S12 P3 ChatGPT deep explore execution",
      ...sourceReports,
    ]),
    "s12p2_human_zh_export",
    "Chinese human explanation export records prompt sources, targets and boundaries",
    "Chinese human explanation export is missing S12 P2 required content",
  );

  for (const relativePath of targetFiles) {
    const source = readRepoFile(relativePath);
    const targetLabel = relativePath === outputs.chatgpt ? "ChatGPT" : relativePath === outputs.codex ? "Codex" : "other agent";
    assertCondition(
      hasAll(source, [
        "机器可复制文本",
        "```text",
        taskId,
        acceptanceId,
        promptVersion,
        targetLabel,
        "latest memory",
        "behavior",
        "latent",
        "self_iteration",
        "No automatic send",
        "No raw mutation",
      ]),
      `s12p2_target_export_${path.basename(relativePath)}`,
      `${relativePath} contains a machine-copyable prompt for ${targetLabel}`,
      `${relativePath} is missing the S12 P2 machine-copyable prompt contract`,
    );
  }
}

function validateAtlasctlGenerate() {
  const result = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "generate-personalization-prompt"], { cwd: repoRoot, timeout: 180000 }));
  assertCondition(
    result.status === "PASS" &&
      result.task_id === taskId &&
      result.acceptance_id === acceptanceId &&
      result.prompt_version === promptVersion &&
      Array.isArray(result.outputs) &&
      [outputs.humanZh, outputs.chatgpt, outputs.codex, outputs.otherAgent, outputs.machine].every((output) => result.outputs.includes(output)) &&
      result.sends_to_chatgpt === false &&
      result.raw_mutation === false,
    "s12p2_atlasctl_generate",
    "atlasctl generate-personalization-prompt creates S12 P2 prompt outputs without sending or raw mutation",
    "atlasctl generate-personalization-prompt does not satisfy S12 P2 contract",
    result,
  );
}

function validateNoForbiddenPromptContent() {
  const searched = [outputs.humanZh, outputs.chatgpt, outputs.codex, outputs.otherAgent, outputs.machine, promptConfigPath, reviewPath, humanDocPath];
  const hits = [];
  for (const relativePath of searched) {
    const source = readRepoFile(relativePath).toLowerCase();
    for (const fragment of forbiddenFragments) {
      if (source.includes(fragment.toLowerCase())) hits.push(`${relativePath}:${fragment}`);
    }
  }
  assertCondition(
    hits.length === 0,
    "s12p2_no_forbidden_prompt_content",
    "S12 P2 prompt outputs do not include cookies, tokens, auto-submit, proposal apply or deep-explore commands",
    "S12 P2 prompt outputs contain forbidden content",
    { hits },
  );
}

function validateConfigReviewAndRecords() {
  const config = readJson(promptConfigPath);
  assertCondition(
    config.schema_version === promptVersion &&
      config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.status === status &&
      targetIds.every((target) => Array.isArray(config.targets) && config.targets.includes(target)) &&
      sourceReports.every((source) => Array.isArray(config.source_reports) && config.source_reports.includes(source)) &&
      config.boundaries?.no_automatic_send === true &&
      config.boundaries?.no_raw_mutation === true &&
      config.boundaries?.no_proposal_apply_execution === true &&
      config.boundaries?.no_s12_p3_chatgpt_deep_explore_execution === true,
    "s12p2_prompt_config",
    "S12 P2 prompt config records targets, source reports and phase boundaries",
    "S12 P2 prompt config is missing required contract fields",
  );

  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      validatorName,
      promptVersion,
      "ChatGPT",
      "Codex",
      "other agent",
      "中文人类说明",
      "机器可复制文本",
      "latest memory",
      "behavior",
      "latent",
      "self_iteration",
      "No automatic send",
      "No GitHub main upload",
      "No remote push",
      "No raw mutation",
      "No proposal apply execution",
      "No S12 P3 ChatGPT deep explore execution",
      "pending S12 P3",
    ]),
    "s12p2_review_artifact",
    "S12 P2 review artifact records sources, prompt outputs, boundaries and pending S12 P3",
    "S12 P2 review artifact is missing required evidence",
  );

  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    promptVersion,
    "ChatGPT",
    "Codex",
    "other agent",
    "中文人类说明",
    "机器可复制文本",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "No proposal apply",
    "S12 P3",
  ];
  for (const relativePath of recordFiles) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s12p2_records_${relativePath}`,
      `${relativePath} records S12 P2 status, validator, boundaries and next phase`,
      `${relativePath} is missing S12 P2 record fragments`,
      { missing },
    );
  }

  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(quickEntry, [taskId, "S12 P2 已完成", "Personalization Prompt", "下一步是 S12 P3", "No GitHub main upload"]),
    "s12p2_quick_entry",
    "Quick entry records completed S12 P2 and pending S12 P3",
    "Quick entry does not record completed S12 P2",
  );
  assertCondition(
    hasAll(overview, ["S12 P2 已完成", "Personalization Prompt", "ChatGPT", "Codex", "other agent", "下一步是 S12 P3"]),
    "s12p2_overview",
    "Human overview records S12 P2 Personalization Prompt and pending S12 P3",
    "Human overview is missing S12 P2 status",
  );
  assertCondition(
    hasAll(machineReadme, [taskId, acceptanceId, status, validatorName, promptVersion, "S12 P3"]),
    "s12p2_machine_readme",
    "Machine README records S12 P2 gate and next phase",
    "Machine README is missing S12 P2 gate",
  );
  assertCondition(
    hasAll(runGate, [taskId, acceptanceId, status, validatorName, "S12 P2 产物", "S12 P3"]),
    "s12p2_run_gate",
    "Run gate README records S12 P2 artifact, validator and next phase",
    "Run gate README is missing S12 P2 gate",
  );
}

function validatePreviousGate() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("s12p2_previous_s12p1_deferred_until_clean_tree", "S12 P1 clean-tree validator will be re-run after S12 P2 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s12_p1.cjs"], { cwd: appRoot, timeout: 300000 }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === previousAcceptanceId,
    "s12p2_previous_s12p1",
    "S12 P1 validator passes before accepting S12 P2",
    "S12 P1 validator did not pass before S12 P2",
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
    "s12p2_no_raw_or_secret_open_changes",
    "S12 P2 open diff does not modify raw, private imports, credentials or secrets",
    "S12 P2 has forbidden raw or secret changes",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    validateBuilderContract();
    for (const file of textFiles) validateTextFile(file);
    validatePromptOutputs();
    validateAtlasctlGenerate();
    validateNoForbiddenPromptContent();
    validateConfigReviewAndRecords();
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
