#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const checks = [];

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
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function validateTextFile(relativePath) {
  const source = readRepoFile(relativePath);
  assertCondition(
    source.endsWith("\n"),
    `${relativePath}:final_newline`,
    `${relativePath} has a final newline`,
    `${relativePath} is missing a final newline`,
  );

  const blocked = [String.fromCharCode(0xfffd), String.fromCharCode(0x00c2), String.fromCharCode(0x00c3)];
  const badLines = [];
  source.split("\n").forEach((line, index) => {
    if (line.trimEnd() !== line) badLines.push(`${index + 1}:trailing`);
    if (blocked.some((char) => line.includes(char))) badLines.push(`${index + 1}:mojibake`);
  });
  assertCondition(
    badLines.length === 0,
    `${relativePath}:text_clean`,
    `${relativePath} has no blocked mojibake characters or trailing whitespace`,
    `${relativePath} contains blocked characters or trailing whitespace`,
    { badLines: badLines.slice(0, 20) },
  );
}

function validatePhase01() {
  const contract = readRepoFile("docs/product/chinese_ui_quality_contract.md");
  const audit = readRepoFile("docs/acceptance/chinese_text_audit.md");

  assertCondition(
    hasAll(contract, [
      "Memory Atlas 中文 UI 质量合同",
      "v1.1.6 Stage 0 Phase 0.1",
      "UTF-8",
      "中文主标签",
      "表格",
      "Inspector",
      "proposal-only",
      "低宽度视口",
      "不改变运行时行为",
    ]),
    "phase_0_1_chinese_ui_contract",
    "Chinese UI contract covers encoding, labels, table/text boundaries, Inspector, proposal-only wording, low-width viewport, and runtime non-goals",
    "Chinese UI quality contract is incomplete",
  );

  assertCondition(
    hasAll(audit, [
      "Memory Atlas 中文文本审计验收",
      "v1.1.6 Stage 0 Phase 0.1",
      "U+FFFD",
      "U+00C2",
      "U+00C3",
      "中文 UI 检查表",
      "Desktop: `1440x900`",
      "Tablet: `768x1024`",
      "Mobile: `390x844`",
      "不新增核心 UI 实现",
      "不读取 raw/private",
      "不直接写长期记忆",
    ]),
    "phase_0_1_text_audit",
    "Chinese text audit defines blocked character checks, UI checklist, viewport screenshot plan, and non-goal boundaries",
    "Chinese text audit is incomplete",
  );
}

function validatePhase02() {
  const density = readRepoFile("docs/acceptance/visual_density_baseline.md");
  assertCondition(
    hasAll(density, [
      "Memory Atlas 页面视觉密度基线",
      "v1.1.6 Stage 0 Phase 0.2",
      "记忆总览 | >= 70%",
      "记忆星系 | >= 90%",
      "记忆时间河 | >= 85%",
      "数据导图 | >= 80%",
      "截图验收矩阵",
      "Desktop 1440x900",
      "Tablet 768x1024",
      "Mobile 390x844",
      "反退化规则",
      "不新增核心 UI 实现",
      "不读取 raw/private",
      "不直接写长期记忆",
    ]),
    "phase_0_2_visual_density_baseline",
    "Visual density baseline covers four page thresholds, screenshot matrix, anti-regression rules, and non-goal boundaries",
    "Visual density baseline is incomplete",
  );
}

function validateRecords() {
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const features = readRepoFile("功能清单.md");
  const dev = readRepoFile("开发记录.md");
  const modelIndex = readRepoFile("模型参数文件.md");
  const changelog = readRepoFile("CHANGELOG.md");
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_6_stage0_review.md");
  const packageSource = readRepoFile("apps/memory-atlas/package.json");

  assertCondition(
    hasAll(delivery, [
      "Stage 0 Phase 0.1：Encoding & Text Audit",
      "Stage 0 Phase 0.2：Visual Readability Baseline",
      "Stage 0 整体复审",
      "stage_0_review_passed_pending_upload",
      "validate:v1.1.6-stage0",
      "不上传 GitHub main",
    ]),
    "delivery_record_stage0_review",
    "Delivery record captures both phases, whole-stage review, validator, upload boundary, and pending-upload status",
    "Delivery record is missing Stage 0 review state",
  );

  assertCondition(
    hasAll(model, [
      "v1.1.6 Stage 0 Phase 0.1 中文文本质量门槛",
      "v1.1.6 Stage 0 Phase 0.2 视觉密度基线门槛",
      "v1.1.6 Stage 0 整体复审门槛",
      "stage_0_review_passed_pending_upload",
      "validate:v1.1.6-stage0",
    ]),
    "model_parameters_stage0_review",
    "Model parameters document text, visual-density, and stage-review gates",
    "Model parameters are missing Stage 0 review gate",
  );

  assertCondition(
    hasAll(features, [
      "FEAT-MA-V116-S0P01",
      "FEAT-MA-V116-S0P02",
      "FEAT-MA-V116-S0-REVIEW",
      "EVID-MA-V116-S0-REVIEW",
    ]),
    "feature_list_stage0_review",
    "Feature list records Phase 0.1, Phase 0.2, and whole-stage review evidence",
    "Feature list is missing Stage 0 review evidence",
  );

  assertCondition(
    hasAll(dev, [
      "MA-V116-S0P01",
      "MA-V116-S0P02",
      "MA-V116-S0-REVIEW",
      "stage_0_review_passed_pending_upload",
      "下一步只允许 final remote checks、commit 和 GitHub main 上传",
    ]),
    "development_record_stage0_review",
    "Development record captures phase completion, stage review, stop point, and next gate",
    "Development record is missing Stage 0 review stop point",
  );

  assertCondition(
    hasAll(modelIndex, [
      "MOD-MA-V116-S0P01",
      "MOD-MA-V116-S0P02",
      "MOD-MA-V116-S0-REVIEW",
      "PARAM-MA-V116-S0-REVIEW-001",
    ]),
    "model_index_stage0_review",
    "Root model parameter file records Phase 0.1, Phase 0.2, and review gates",
    "Root model parameter file is missing Stage 0 review gate",
  );

  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.6 Stage 0 Review",
      "validate:v1.1.6-stage0",
      "No runtime UI implementation",
      "No raw/private data read",
      "No direct writeback",
      "No GitHub main upload",
    ]),
    "changelog_stage0_review",
    "Changelog records whole-stage review and non-goal boundaries",
    "Changelog is missing Stage 0 review entry",
  );

  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.1.6 Stage 0 Review",
      "Stage 0 is review-passed",
      "Phase 0.1",
      "Phase 0.2",
      "validate:v1.1.6-stage0",
      "No runtime UI implementation",
      "No raw/private/cookie/session/secret data access",
      "No direct frontend writeback",
      "No GitHub main upload",
    ]),
    "review_doc_stage0",
    "Review document records result, phase coverage, validation, boundaries, and upload gate",
    "Stage 0 review document is incomplete",
  );

  assertCondition(
    packageSource.includes('"validate:v1.1.6-stage0": "node scripts/validate_memory_atlas_v1_1_6_stage0.cjs"'),
    "package_script_stage0",
    "Package script exposes validate:v1.1.6-stage0",
    "Package script validate:v1.1.6-stage0 is missing",
  );
}

function validateChangeScope() {
  const result = run("git", ["-c", "core.quotePath=false", "status", "--short", "--", "."], { cwd: repoRoot });
  const changed = result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3))
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.replace(/^\"(.+)\"$/, "$1"));
  const allowed = [
    "CHANGELOG.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "docs/product/chinese_ui_quality_contract.md",
    "docs/acceptance/chinese_text_audit.md",
    "docs/acceptance/visual_density_baseline.md",
    "docs/reviews/memory_atlas_v1_1_6_stage0_review.md",
    "apps/memory-atlas/package.json",
    "apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage0.cjs",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
  ];
  const outside = changed.filter((file) => !allowed.includes(file));
  assertCondition(
    outside.length === 0,
    "stage0_change_scope",
    "Current OpenAIDatabase changes are limited to Stage 0 contracts, records, review, validator, and package script",
    "Unexpected OpenAIDatabase paths changed",
    { changed, outside },
  );
}

try {
  [
    "docs/product/chinese_ui_quality_contract.md",
    "docs/acceptance/chinese_text_audit.md",
    "docs/acceptance/visual_density_baseline.md",
    "docs/reviews/memory_atlas_v1_1_6_stage0_review.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "CHANGELOG.md",
  ].forEach(validateTextFile);
  validatePhase01();
  validatePhase02();
  validateRecords();
  validateChangeScope();
  pass("stage0_boundary", "No runtime UI/CSS/raw-private/direct-writeback/Stage1/upload work is required or present in the Stage 0 review artifact");
  console.log(JSON.stringify({ status: "PASS", stage: "v1.1.6-stage0", checks }, null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    stage: "v1.1.6-stage0",
    error: error.message,
    details: error.details || null,
    checks,
  }, null, 2));
  process.exit(1);
}
