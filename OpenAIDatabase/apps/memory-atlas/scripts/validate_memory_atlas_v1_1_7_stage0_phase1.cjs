#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");

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

function walkFiles(relativeDir) {
  const absoluteDir = path.join(repoRoot, relativeDir);
  if (!fs.existsSync(absoluteDir)) return [];
  const result = [];
  const stack = [absoluteDir];
  while (stack.length) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const absolutePath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "node_modules" || entry.name === "dist") continue;
        stack.push(absolutePath);
      } else {
        result.push(path.relative(repoRoot, absolutePath));
      }
    }
  }
  return result.sort();
}

function selectedTextFiles() {
  const allowedExtensions = new Set([".md", ".json", ".ts", ".tsx", ".css", ".csv", ".yaml", ".yml"]);
  const files = [
    ...walkFiles("apps/memory-atlas/src"),
    ...walkFiles("docs/product"),
    ...walkFiles("docs/acceptance"),
    ...walkFiles("config/visualization"),
    "data/derived/visualization/memory_atlas.json",
    "CHANGELOG.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  ];
  return [...new Set(files)]
    .filter((relativePath) => fs.existsSync(path.join(repoRoot, relativePath)))
    .filter((relativePath) => allowedExtensions.has(path.extname(relativePath)));
}

function validateTextCleanliness() {
  const blockedChars = [String.fromCharCode(0xfffd), String.fromCharCode(0x00c2), String.fromCharCode(0x00c3), "\u0000"];
  const bad = [];
  for (const relativePath of selectedTextFiles()) {
    const source = readRepoFile(relativePath);
    if (!source.endsWith("\n")) bad.push(`${relativePath}:final_newline`);
    source.split("\n").forEach((line, index) => {
      if (line.trimEnd() !== line) bad.push(`${relativePath}:${index + 1}:trailing`);
      if (blockedChars.some((char) => line.includes(char))) bad.push(`${relativePath}:${index + 1}:mojibake`);
    });
    if (relativePath.endsWith(".json")) {
      try {
        JSON.parse(source);
      } catch (error) {
        bad.push(`${relativePath}:json:${error.message}`);
      }
    }
  }
  assertCondition(
    bad.length === 0,
    "stage0_phase1_utf8_text_scan",
    "Selected Memory Atlas Markdown, JSON, TS/TSX, CSS, CSV and YAML files are text-clean",
    "Selected files contain mojibake, trailing whitespace, invalid JSON or missing final newline",
    { bad: bad.slice(0, 40), scannedFileCount: selectedTextFiles().length },
  );
}

function validateRegistry() {
  const types = readRepoFile("apps/memory-atlas/src/i18n/types.ts");
  const copy = readRepoFile("apps/memory-atlas/src/i18n/zh-CN.ts");
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");

  assertCondition(
    hasAll(types, [
      "export interface ChineseUiCopy",
      "navigation",
      "filters",
      "states",
      "overview",
      "inspector",
      "proposal",
      "Record<ViewKey, string>",
    ]),
    "stage0_phase1_registry_types",
    "Chinese UI copy types include required groups and view-key coverage",
    "Chinese UI copy types are incomplete",
  );

  assertCondition(
    hasAll(copy, [
      "export const zhCNCopy",
      "记忆总览",
      "银河星云",
      "星图读取失败",
      "Memory Weather v2",
      "选择一个节点",
      "写回提案",
      "只生成提案 JSON",
      "不直接改主动记忆",
      "保存 JSON 提案",
    ]),
    "stage0_phase1_registry_copy",
    "Chinese UI copy registry contains navigation, state, overview, Inspector and proposal labels",
    "Chinese UI copy registry is incomplete",
  );

  assertCondition(
    hasAll(app, [
      "import { zhCNCopy } from \"./i18n/zh-CN\"",
      "const uiCopy = zhCNCopy",
      "uiCopy.navigation.views.home",
      "uiCopy.filters.searchPlaceholder",
      "uiCopy.states.loadFailedTitle",
      "uiCopy.overview.nextBestActionsTitle",
      "uiCopy.inspector.emptyTitle",
      "uiCopy.proposal.buttons.save",
    ]),
    "stage0_phase1_registry_runtime_usage",
    "App shell, filters, overview, Inspector and proposal surfaces consume the Chinese UI registry",
    "App runtime does not consume the Chinese UI registry across required surfaces",
  );
}

function validateStyles() {
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");
  assertCondition(
    hasAll(styles, [
      "--memory-atlas-font-family",
      "PingFang SC",
      "Hiragino Sans GB",
      "Heiti SC",
      "Noto Sans CJK SC",
      "Microsoft YaHei",
      "overflow-wrap: anywhere",
      "word-break: normal",
      "line-break: loose",
      "min-width: 0",
      ".writeback-panel",
      ".inspector",
      ".home-overview-view",
    ]),
    "stage0_phase1_chinese_layout_tolerance",
    "Global styles define Chinese font fallback and long-text layout tolerance for app, Inspector and proposal surfaces",
    "Chinese font fallback or layout tolerance is incomplete",
  );
}

function validateContractsAndRecords() {
  const product = readRepoFile("docs/product/memory_atlas_v1_1_7_stage0_phase1_chinese_display_contract.md");
  const acceptance = readRepoFile("docs/acceptance/memory_atlas_v1_1_7_stage0_phase1_chinese_display_acceptance.md");
  const packageJson = readRepoFile("apps/memory-atlas/package.json");
  const records = [
    ["CHANGELOG.md", readRepoFile("CHANGELOG.md")],
    ["功能清单.md", readRepoFile("功能清单.md")],
    ["开发记录.md", readRepoFile("开发记录.md")],
    ["模型参数文件.md", readRepoFile("模型参数文件.md")],
    ["docs/MEMORY_ATLAS_DELIVERY_RECORD.md", readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md")],
    ["docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md", readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md")],
  ];

  assertCondition(
    hasAll(product, [
      "Memory Atlas v1.1.7 Stage 0 Phase 1 Chinese Display Contract",
      "MA-V117-S0P01",
      "ACC-MA-V117-S0P01",
      "phase_0_1_chinese_display_foundation_completed_pending_stage0_review",
      "validate:v1.1.7-stage0-phase1",
      "No GitHub main upload in this phase",
    ]) &&
      hasAll(acceptance, [
        "Memory Atlas v1.1.7 Stage 0 Phase 1 Chinese Display Acceptance",
        "ACC-MA-V117-S0P01",
        "UTF-8 scan",
        "Copy registry",
        "Runtime usage",
        "Font fallback",
        "Text tolerance",
      ]),
    "stage0_phase1_contract_acceptance",
    "Stage 0 Phase 1 product contract and acceptance checklist are present and aligned",
    "Stage 0 Phase 1 contract or acceptance is incomplete",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.7-stage0-phase1": "node scripts/validate_memory_atlas_v1_1_7_stage0_phase1.cjs"'),
    "stage0_phase1_package_script",
    "package.json exposes validate:v1.1.7-stage0-phase1",
    "package.json is missing validate:v1.1.7-stage0-phase1",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        "MA-V117-S0P01",
        "ACC-MA-V117-S0P01",
        "phase_0_1_chinese_display_foundation_completed_pending_stage0_review",
        "validate:v1.1.7-stage0-phase1",
      ]),
      `stage0_phase1_records_${name}`,
      `${name} registers Stage 0 Phase 1 status, acceptance and validator`,
      `${name} is missing Stage 0 Phase 1 record tokens`,
    );
  }
}

function main() {
  validateTextCleanliness();
  validateRegistry();
  validateStyles();
  validateContractsAndRecords();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage0-phase1",
        acceptance_id: "ACC-MA-V117-S0P01",
        checks,
      },
      null,
      2,
    ),
  );
}

try {
  main();
} catch (error) {
  console.error(
    JSON.stringify(
      {
        status: "FAIL",
        stage: "v1.1.7-stage0-phase1",
        error: error.message,
        details: error.details || null,
        checks,
      },
      null,
      2,
    ),
  );
  process.exit(1);
}
