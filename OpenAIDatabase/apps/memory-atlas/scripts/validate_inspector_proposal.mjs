#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDir, "..");
const repoRoot = resolve(appRoot, "../..");

const appSource = readFileSync(resolve(appRoot, "src/App.tsx"), "utf8");
const cssSource = readFileSync(resolve(appRoot, "src/styles.css"), "utf8");
const packageSource = readFileSync(resolve(appRoot, "package.json"), "utf8");
const visualAudit = readFileSync(resolve(repoRoot, "scripts/audit_memory_atlas_visual_acceptance.py"), "utf8");

const failures = [];

validateExplanationPanel(failures);
validateProposalOnlyWriteback(failures);
validateDebugSeparation(failures);
validateStageHooks(failures);

if (failures.length) {
  console.error(JSON.stringify({ ok: false, failures }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({
  ok: true,
  stage: "6.2",
  checks: [
    "Inspector explanation panel exposes formulas, parameters, redacted evidence and human-readable summary",
    "Writeback UI only creates proposal JSON with direct active-memory mutation disabled",
    "Agent/debug fields and low-sensitivity database summaries are hidden behind a user-controlled Debug panel",
    "Package and visual acceptance hooks include Stage 6.2 regression coverage",
  ],
}, null, 2));

function validateExplanationPanel(failures) {
  const required = [
    "interface InspectorExplanation",
    "function buildInspectorExplanation",
    "function InspectorExplanationPanel",
    "memory_weight = tier*0.5 + importance*0.3 + confidence*0.2",
    "leverage_score = max(0, memory_weight + decision_impact*0.15 - sensitivity_penalty)",
    "sharedAtlasReducer -> focus(inspector/home/galaxy/timeline/roi)",
    'className="inspector-explanation-panel"',
    'data-raw-display="false"',
    "脱敏派生快照",
  ];
  if (!hasAll(appSource, required)) failures.push("Inspector explanation panel lacks formulas, parameters, redacted evidence, or no-raw marker");
  if (!hasAll(cssSource, [
    ".inspector-explanation-panel",
    ".inspector-formula-grid",
    ".inspector-formula-card",
    ".inspector-evidence-grid",
    ".inspector-safety-list",
  ])) {
    failures.push("Inspector explanation panel styles are missing");
  }
}

function validateProposalOnlyWriteback(failures) {
  const required = [
    "interface WritebackProposalDraftInput",
    "function buildWritebackProposalDraft",
    'proposalIdPrefix: "atlas_preview"',
    'data-proposal-only="true"',
    'data-active-memory-mutation="false"',
    "proposalJsonPreview",
    "JSON 提案预览",
    "direct_frontend_mutation_of_active_memory: false",
    "requires_agent_or_human_apply: true",
    "requires_conflict_check: true",
    "保存 JSON 提案",
  ];
  if (!hasAll(appSource, required)) failures.push("Writeback panel does not expose proposal-only JSON contract or safety fields");
  if (!hasAll(cssSource, [
    ".writeback-safety-strip",
    ".writeback-json-preview",
    ".writeback-json-preview pre",
  ])) {
    failures.push("Writeback proposal JSON preview styles are missing");
  }
}

function validateDebugSeparation(failures) {
  const required = [
    "const [debugOpen, setDebugOpen] = useState(false)",
    'data-debug-lite={debugOpen ? "open" : "closed"}',
    'data-default-raw-summary="hidden"',
    'className="inspector-debug-toggle"',
    'data-debug-panel="true"',
    "隐藏 Debug",
    "显示 Debug",
  ];
  if (!hasAll(appSource, required)) failures.push("Debug panel is not default-closed, toggleable, or explicitly marked");
  const debugPanelIndex = appSource.indexOf('data-debug-panel="true"');
  const rawSummaryIndex = appSource.indexOf('className="raw-summary-inline"');
  if (rawSummaryIndex === -1 || debugPanelIndex === -1 || rawSummaryIndex < debugPanelIndex) {
    failures.push("Low-sensitivity summary is not isolated inside the Debug panel");
  }
  if (!hasAll(cssSource, [
    ".inspector-debug-toggle",
    ".inspector-debug-panel",
  ])) {
    failures.push("Debug separation styles are missing");
  }
}

function validateStageHooks(failures) {
  if (!packageSource.includes('"validate:inspector-proposal": "node scripts/validate_inspector_proposal.mjs"')) {
    failures.push("package.json lacks validate:inspector-proposal script");
  }
  if (!visualAudit.includes("stage6_2_inspector_proposal_ready")) {
    failures.push("visual acceptance audit lacks Stage 6.2 Inspector/Proposal hook");
  }
}

function hasAll(source, needles) {
  return needles.every((needle) => source.includes(needle));
}
