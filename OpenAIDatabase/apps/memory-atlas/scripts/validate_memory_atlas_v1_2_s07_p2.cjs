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

const taskId = "MA-V12-S07P2";
const acceptanceId = "ACC-MA-V12-S07P2";
const status = "phase_s07_p2_information_roi_completed_pending_s07_p3";
const validatorName = "validate:v1.2-s07-p2";
const scriptName = "validate_memory_atlas_v1_2_s07_p2.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const atlasctlPath = "scripts/atlasctl.py";
const builderPath = "scripts/build_memory_atlas_information_roi.py";
const formulaConfigPath = "机器治理/参数与公式/information_roi.v1_2_s07_p2.json";
const visualGateConfigPath = "机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json";
const outputPath = "data/derived/information_roi/information_roi_gate.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s07_p2_information_roi.md";
const humanDocPath = "人类可读/17_InformationROI与VisualROIGate说明.md";

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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p1.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p3.cjs",
  `OpenAIDatabase/${atlasctlPath}`,
  `OpenAIDatabase/${builderPath}`,
  "OpenAIDatabase/scripts/build_memory_atlas_formula_what_if.py",
  `OpenAIDatabase/${formulaConfigPath}`,
  `OpenAIDatabase/${visualGateConfigPath}`,
  "OpenAIDatabase/机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json",
  `OpenAIDatabase/${outputPath}`,
  "OpenAIDatabase/data/derived/economic_proxy/formula_what_if_preview.json",
  "OpenAIDatabase/tests/test_s07p2_information_roi.py",
  "OpenAIDatabase/tests/test_s07p3_formula_what_if.py",
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s07_p3_formula_what_if.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  `OpenAIDatabase/${humanDocPath}`,
  "OpenAIDatabase/人类可读/18_FormulaWhatIf配置预览说明.md",
  "OpenAIDatabase/机器治理/README.md",
  "OpenAIDatabase/机器治理/参数与公式/README.md",
  "OpenAIDatabase/机器治理/可视化配置/README.md",
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
    "s07p2_package_script",
    "package.json exposes the v1.2 S07 P2 validator",
    "package.json is missing the v1.2 S07 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s07p2_previous_phase_deferred_scope",
      "S07 P1 execution is deferred only because open diff is limited to S07 P2 files and compatibility updates",
      "S07 P1 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s07p2_previous_phase_deferred_until_clean_tree", "S07 P1 validator will run on a clean tree after S07 P2 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s07_p1.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S07P1",
    "s07p2_previous_s07p1",
    "S07 P1 validator returns PASS before accepting S07 P2 on a clean tree",
    "S07 P1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateConfigAndOutput() {
  [atlasctlPath, builderPath, formulaConfigPath, visualGateConfigPath, outputPath].forEach(validateTextFile);
  const atlasctl = readRepoFile(atlasctlPath);
  const builder = readRepoFile(builderPath);
  assertCondition(
    hasAll(atlasctl, ["information-roi", "run_visual_roi_audit", "visual-roi", "build_memory_atlas_information_roi.py"]),
    "s07p2_atlasctl_contract",
    "atlasctl exposes S07 P2 information-roi analyze and visual-roi audit entry points",
    "atlasctl is missing S07 P2 information-roi or visual-roi contract",
  );
  assertCondition(
    hasAll(builder, [taskId, acceptanceId, "does_not_generate_what_if_ui", "does_not_modify_runtime_ui", "Visual ROI Gate"]),
    "s07p2_builder_contract",
    "Information ROI builder enforces S07 P2 phase boundary and Visual ROI Gate",
    "Information ROI builder is missing S07 P2 boundary markers",
  );
  const config = readJson(formulaConfigPath);
  const visualConfig = readJson(visualGateConfigPath);
  const output = readJson(outputPath);
  assertCondition(
    config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.status === "phase_s07_p2_formula_config_active_pending_s07_p3" &&
      config.scope_boundary?.external_economic_database_dependency === false &&
      config.scope_boundary?.precise_income_prediction === false &&
      Array.isArray(config.formulas) &&
      config.formulas.length === 2 &&
      config.formulas.every((item) => item.formula_id && hasCjk(item.expression_zh) && hasCjk(item.interpretation_zh)),
    "s07p2_formula_config",
    "Information ROI formula config defines information_roi_score and visual_roi_gate formulas with no external DB dependency",
    "Information ROI formula config failed S07 P2 acceptance",
    { formula_count: config.formulas?.length },
  );
  assertCondition(
    visualConfig.task_id === taskId &&
      visualConfig.acceptance_id === acceptanceId &&
      visualConfig.status === "phase_s07_p2_visual_roi_gate_active_pending_s07_p3" &&
      Array.isArray(visualConfig.p0_visuals) &&
      visualConfig.p0_visuals.length === 10 &&
      visualConfig.p0_visuals.every((item) => item.id && hasCjk(item.human_question) && hasCjk(item.action)) &&
      Array.isArray(visualConfig.excluded_from_p0_examples) &&
      visualConfig.excluded_from_p0_examples.length >= 1,
    "s07p2_visual_gate_config",
    "Visual ROI Gate config binds every P0 visual to human question and action and keeps low-value examples out of P0",
    "Visual ROI Gate config failed S07 P2 acceptance",
    { p0_visual_count: visualConfig.p0_visuals?.length },
  );
  const roiItems = Array.isArray(output.roi_items) ? output.roi_items : [];
  const itemTypes = new Set(roiItems.map((item) => item.item_type));
  const badItems = [];
  for (const item of roiItems) {
    if (!item.formula_id || !item.formula_source) badItems.push(`${item.item_id}:missing_formula_source`);
    if (!hasCjk(item.decision_summary_zh)) badItems.push(`${item.item_id}:missing_chinese_summary`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badItems.push(`${item.item_id}:missing_evidence_refs`);
    if (Number(item.information_roi_score) < 0 || Number(item.information_roi_score) > 100) badItems.push(`${item.item_id}:score_out_of_range`);
    if (item.item_type === "chart" && item.p0_candidate === true) {
      if (!hasCjk(item.human_question) || !hasCjk(item.action_zh) || item.visual_roi_gate_pass !== true) {
        badItems.push(`${item.item_id}:invalid_p0_visual_gate`);
      }
    }
  }
  assertCondition(
    output.schema_version === "memory_atlas_information_roi_gate.v1_2_s07_p2" &&
      output.task_id === taskId &&
      output.acceptance_id === acceptanceId &&
      output.status === status &&
      output.roi_summary?.item_count === roiItems.length &&
      itemTypes.has("insight") &&
      itemTypes.has("card") &&
      itemTypes.has("chart") &&
      output.visual_roi_gate?.p0_candidate_count === 10 &&
      output.visual_roi_gate?.failed_p0_count === 0 &&
      Array.isArray(output.visual_roi_gate?.excluded_from_p0) &&
      output.visual_roi_gate.excluded_from_p0.length >= 1 &&
      output.phase_boundary?.does_not_use_external_economic_database === true &&
      output.phase_boundary?.does_not_claim_precise_income_prediction === true &&
      output.phase_boundary?.does_not_generate_what_if_ui === true &&
      output.phase_boundary?.does_not_modify_raw === true &&
      badItems.length === 0,
    "s07p2_information_roi_output",
    "Information ROI output covers insights, cards and charts with formula source, evidence and a passing Visual ROI Gate",
    "Information ROI output failed S07 P2 acceptance",
    {
      roi_summary: output.roi_summary,
      visual_roi_gate: {
        p0_candidate_count: output.visual_roi_gate?.p0_candidate_count,
        failed_p0_count: output.visual_roi_gate?.failed_p0_count,
      },
      badItems: badItems.slice(0, 50),
    },
  );
  const dryRun = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "information-roi", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    dryRun.task_id === taskId &&
      dryRun.acceptance_id === acceptanceId &&
      dryRun.dry_run === true &&
      dryRun.writes_files === false &&
      Array.isArray(dryRun.roi_items) &&
      dryRun.roi_items.length === roiItems.length,
    "s07p2_atlasctl_information_roi_dry_run",
    "atlasctl analyze --stage information-roi --dry-run returns the no-write S07 P2 payload",
    "atlasctl information-roi dry-run failed S07 P2 gate",
    { writes_files: dryRun.writes_files, roi_item_count: dryRun.roi_items?.length },
  );
  const audit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "visual-roi"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    audit.status === "PASS" &&
      audit.task_id === taskId &&
      audit.acceptance_id === acceptanceId &&
      audit.roi_item_count === roiItems.length &&
      audit.p0_visual_count === 10 &&
      audit.failed_p0_count === 0 &&
      Array.isArray(audit.bad_items) &&
      audit.bad_items.length === 0,
    "s07p2_visual_roi_audit",
    "atlasctl audit --check visual-roi confirms information ROI formulas, P0 visual gate and no external DB dependency",
    "visual-roi audit failed S07 P2 gate",
    audit,
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

function currentStateIsS07P3() {
  if (currentStateIsS08P1()) return true;
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const formula = readRepoFile("机器治理/参数与公式/README.md");
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
  return (
    hasAll(quick, ["当前阶段是 S07 P3", "MA-V12-S07P3", "ACC-MA-V12-S07P3", "下一步只允许进入 S07 Review"]) &&
    hasAll(overview, ["S07 P3 已完成", "Formula What-if", "下一步是 S07 Review"]) &&
    hasAll(machine, ["当前为 S07 P3", "MA-V12-S07P3", "validate:v1.2-s07-p3", "下一步是 S07 Review"]) &&
    hasAll(dataContract, ["当前 S07 P3 已完成", "formula_what_if_preview.json", "下一步是 S07 Review"]) &&
    hasAll(formula, ["当前 S07 P3 已完成", "formula_what_if_defaults.v1_2_s07_p3.json", "formula_what_if_proxy_score"]) &&
    hasAll(behavior, ["当前 S07 P3 已完成", "Formula What-if", "下一步是 S07 Review"]) &&
    hasAll(runGate, ["当前阶段是 S07 P3", "MA-V12-S07P3", "ACC-MA-V12-S07P3", "validate:v1.2-s07-p3"])
  );
}

function validateDocsAndRecords() {
  [
    reviewPath,
    humanDocPath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/参数与公式/README.md",
    "机器治理/可视化配置/README.md",
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
  const formula = readRepoFile("机器治理/参数与公式/README.md");
  const visual = readRepoFile("机器治理/可视化配置/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  const s07p3State = currentStateIsS07P3();

  assertCondition(
    hasAll(review, [taskId, acceptanceId, status, "Information ROI", "Visual ROI Gate", outputPath, "failed_p0_count", "pending S07 P3", "No GitHub main upload in this phase"]),
    "s07p2_review_artifact",
    "S07 P2 review artifact records information ROI, Visual ROI Gate, output and next S07 P3 gate",
    "S07 P2 review artifact is incomplete",
  );
  assertCondition(
    hasAll(human, [taskId, acceptanceId, formulaConfigPath, visualGateConfigPath, outputPath, "insight", "card", "chart", "没有决策价值的图表不进 P0", "下一步只允许进入 S07 P3"]),
    "s07p2_human_doc",
    "Human doc explains information ROI, Visual ROI Gate and next gate in Chinese",
    "Human information ROI doc is incomplete",
  );
  assertCondition(
    s07p3State || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S07 P2", "Information ROI", "下一步只允许进入 S07 P3"]),
    "s07p2_quick_entry",
    "Quick entry records S07 P2 state and next S07 P3 gate",
    "Quick entry is missing S07 P2 state",
  );
  assertCondition(
    s07p3State || hasAll(overview, ["S07 P2 已完成", "Visual ROI Gate", outputPath, "下一步是 S07 P3"]),
    "s07p2_overview",
    "Overview records S07 P2 state and output",
    "Overview is missing S07 P2 state",
  );
  assertCondition(
    s07p3State || hasAll(machine, ["当前为 S07 P2", taskId, acceptanceId, validatorName, "下一步是 S07 P3"]),
    "s07p2_machine_readme",
    "Machine README records S07 P2 identity and next gate",
    "Machine README is missing S07 P2 state",
  );
  assertCondition(
    s07p3State || hasAll(formula, ["当前 S07 P2 已完成", "information_roi.v1_2_s07_p2.json", "information_roi_score", "visual_roi_gate", "下一步是 S07 P3"]),
    "s07p2_formula_readme",
    "Formula README records S07 P2 formula registry",
    "Formula README is missing S07 P2 state",
  );
  assertCondition(
    s07p3State || hasAll(visual, ["当前 S07 P2 已完成", "visual_roi_gate.v1_2_s07_p2.json", "没有决策价值的图表不进 P0", "下一步是 S07 P3"]),
    "s07p2_visual_readme",
    "Visualization README records S07 P2 Visual ROI Gate",
    "Visualization README is missing S07 P2 state",
  );
  assertCondition(
    s07p3State || hasAll(dataContract, ["当前 S07 P2 已完成", outputPath, "roi_items", "visual_roi_gate", "下一步是 S07 P3"]),
    "s07p2_data_contract",
    "Data contract README records S07 P2 information ROI output",
    "Data contract README is missing S07 P2 state",
  );
  assertCondition(
    s07p3State || hasAll(behavior, ["当前 S07 P2 已完成", "Information ROI", "Visual ROI Gate", "下一步是 S07 P3"]),
    "s07p2_behavior_readme",
    "Behavior model README records S07 P2 usage of behavior and economic proxy outputs",
    "Behavior model README is missing S07 P2 state",
  );
  assertCondition(
    s07p3State || hasAll(runGate, ["当前阶段是 S07 P2", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S07 P3"]),
    "s07p2_run_gate",
    "Run gate README records S07 P2 validator and next gate",
    "Run gate README is missing S07 P2 state",
  );
  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S07 P2", "pending S07 P3", "No GitHub main upload in this phase"]),
      `s07p2_records_${name}`,
      `${name} records S07 P2 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S07 P2 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s07p2_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s07p2_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S07 P2 branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s07p2_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s07p2_open_diff_scope",
    "Open diff is limited to S07 P2 files and historical-validator compatibility",
    "Open diff contains files outside S07 P2 allowed scope",
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
    "s07p2_no_raw_or_secret_open_changes",
    "S07 P2 open diff does not modify raw or secret/config files",
    "S07 P2 open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateConfigAndOutput();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s07_p2", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s07_p2",
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
