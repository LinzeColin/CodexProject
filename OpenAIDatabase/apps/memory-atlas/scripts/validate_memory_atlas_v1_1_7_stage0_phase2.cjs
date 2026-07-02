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
    "apps/memory-atlas/package.json",
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
    "stage0_phase2_utf8_text_scan",
    "Selected Memory Atlas text surfaces remain clean after Help and state copy additions",
    "Selected files contain mojibake, trailing whitespace, invalid JSON or missing final newline",
    { bad: bad.slice(0, 40), scannedFileCount: selectedTextFiles().length },
  );
}

function validateRegistryAndRuntime() {
  const types = readRepoFile("apps/memory-atlas/src/i18n/types.ts");
  const copy = readRepoFile("apps/memory-atlas/src/i18n/zh-CN.ts");
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");

  assertCondition(
    hasAll(types, [
      "help",
      "threeMinutePath",
      "presentation",
      "analysis",
      "emptyAtlasTitle",
      "noFilteredResultsTitle",
      "webglUnavailableTitle",
      "proposalUnavailableTitle",
    ]),
    "stage0_phase2_registry_types",
    "Chinese UI copy types include Help, 3-minute path and empty/error state fields",
    "Chinese UI copy types are missing Stage 0 Phase 0.2 fields",
  );

  assertCondition(
    hasAll(copy, [
      "3 分钟使用路径",
      "看当前状态",
      "看建议和证据",
      "调整 proposal 并复盘",
      "Presentation",
      "Analysis",
      "当前没有可展示的记忆数据",
      "当前筛选没有匹配结果",
      "WebGL 不可用",
      "当前不能写入 proposal",
    ]),
    "stage0_phase2_registry_copy",
    "Chinese UI copy registry contains usage path, mode explanation and four empty/error states",
    "Chinese UI copy registry is missing Stage 0 Phase 0.2 copy",
  );

  assertCondition(
    hasAll(app, [
      "import { EmptyState } from \"./components/EmptyState\"",
      "import { ErrorState } from \"./components/ErrorState\"",
      "import { MemoryAtlasHelpPanel } from \"./components/help/MemoryAtlasHelpPanel\"",
      "const [helpOpen, setHelpOpen] = useState(false)",
      "className=\"help-launch-button\"",
      "uiCopy.help.buttonLabel",
      "MemoryAtlasHelpPanel",
      "viewEmptyState(atlas, slice)",
      "dataState=\"empty-atlas\"",
      "actionLabel={uiCopy.states.emptyAtlasAction}",
      "onShowHelp",
      "dataState=\"no-filtered-results\"",
      "onResetFilters",
      "dataState=\"load-failed\"",
      "dataState=\"proposal-not-writable\"",
    ]),
    "stage0_phase2_runtime_usage",
    "App exposes Help, empty snapshot, no-result, load-error and proposal-not-writable states",
    "App runtime is missing required Stage 0 Phase 0.2 state wiring",
  );
}

function validateComponentsAndStyles() {
  const helpPanel = readRepoFile("apps/memory-atlas/src/components/help/MemoryAtlasHelpPanel.tsx");
  const emptyState = readRepoFile("apps/memory-atlas/src/components/EmptyState.tsx");
  const errorState = readRepoFile("apps/memory-atlas/src/components/ErrorState.tsx");
  const galaxyScene = readRepoFile("apps/memory-atlas/src/components/GalaxyScene.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");

  assertCondition(
    hasAll(helpPanel, [
      "data-memory-atlas-help-panel=\"stage0-phase2\"",
      "data-three-minute-path=\"true\"",
      "copy.threeMinutePath.map",
      "copy.modes.presentation",
      "copy.modes.analysis",
      "copy.workflowNotes.map",
      "onSelectView(step.view)",
    ]),
    "stage0_phase2_help_panel_component",
    "Help panel renders 3-minute path, reading modes and workflow notes",
    "Help panel component is incomplete",
  );

  assertCondition(
    hasAll(emptyState, [
      "data-memory-atlas-empty-state",
      "role=\"status\"",
      "actionLabel",
      "onAction",
    ]) &&
      hasAll(errorState, [
        "data-memory-atlas-error-state",
        "role=\"alert\"",
        "details",
        "compact",
      ]),
    "stage0_phase2_state_components",
    "EmptyState and ErrorState expose deterministic data attributes and action/detail support",
    "EmptyState or ErrorState component is incomplete",
  );

  assertCondition(
    hasAll(galaxyScene, [
      "import { zhCNCopy } from \"../i18n/zh-CN\"",
      "data-memory-atlas-error-state=\"webgl-unavailable\"",
      "uiCopy.states.webglUnavailableTitle",
      "uiCopy.states.webglUnavailableDescription",
      "uiCopy.states.webglUnavailableAction",
    ]),
    "stage0_phase2_webgl_fallback",
    "GalaxyScene WebGL fallback uses Chinese registry copy and recovery guidance",
    "Galaxy WebGL fallback is missing Stage 0 Phase 0.2 copy or data attribute",
  );

  assertCondition(
    hasAll(styles, [
      ".topbar-actions",
      ".help-launch-button",
      ".help-backdrop",
      ".help-panel",
      ".help-path-list",
      ".empty-state",
      ".error-state",
      ".proposal-unavailable-state",
      ".galaxy-fallback small",
    ]),
    "stage0_phase2_styles",
    "Styles cover Help panel, state components, proposal unavailable state and WebGL fallback detail",
    "Stage 0 Phase 0.2 styles are incomplete",
  );
}

function validateContractsAndRecords() {
  const product = readRepoFile("docs/product/memory_atlas_v1_1_7_stage0_phase2_usage_help_contract.md");
  const acceptance = readRepoFile("docs/acceptance/memory_atlas_v1_1_7_stage0_phase2_usage_help_acceptance.md");
  const guide = readRepoFile("docs/product/memory_atlas_usage_guide.md");
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
      "Memory Atlas v1.1.7 Stage 0 Phase 2 Usage Help Contract",
      "MA-V117-S0P02",
      "ACC-MA-V117-S0P02",
      "phase_0_2_usage_help_completed_pending_stage0_review",
      "validate:v1.1.7-stage0-phase2",
      "No GitHub main upload in this phase",
    ]) &&
      hasAll(acceptance, [
        "Memory Atlas v1.1.7 Stage 0 Phase 2 Usage Help Acceptance",
        "ACC-MA-V117-S0P02",
        "Help entry",
        "3-minute path",
        "Empty snapshot",
        "No filtered results",
        "WebGL fallback",
        "Proposal not writable",
      ]) &&
      hasAll(guide, [
        "Memory Atlas Usage Guide",
        "3-Minute Path",
        "Empty And Error States",
        "Proposal not writable",
        "不得直接写入长期记忆",
      ]),
    "stage0_phase2_contract_acceptance_guide",
    "Stage 0 Phase 2 product contract, acceptance checklist and usage guide are present",
    "Stage 0 Phase 2 contract, acceptance or guide is incomplete",
  );

  assertCondition(
    packageJson.includes('"validate:v1.1.7-stage0-phase2": "node scripts/validate_memory_atlas_v1_1_7_stage0_phase2.cjs"'),
    "stage0_phase2_package_script",
    "package.json exposes validate:v1.1.7-stage0-phase2",
    "package.json is missing validate:v1.1.7-stage0-phase2",
  );

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        "MA-V117-S0P02",
        "ACC-MA-V117-S0P02",
        "phase_0_2_usage_help_completed_pending_stage0_review",
        "validate:v1.1.7-stage0-phase2",
      ]),
      `stage0_phase2_records_${name}`,
      `${name} registers Stage 0 Phase 2 status, acceptance and validator`,
      `${name} is missing Stage 0 Phase 2 record tokens`,
    );
  }
}

function main() {
  validateTextCleanliness();
  validateRegistryAndRuntime();
  validateComponentsAndStyles();
  validateContractsAndRecords();
  console.log(
    JSON.stringify(
      {
        status: "PASS",
        stage: "v1.1.7-stage0-phase2",
        acceptance_id: "ACC-MA-V117-S0P02",
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
        stage: "v1.1.7-stage0-phase2",
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
