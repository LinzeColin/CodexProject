import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";


const require = createRequire(import.meta.url);
const testDir = path.dirname(fileURLToPath(import.meta.url));
const pfiRoot = path.resolve(testDir, "../../..");
const data = require("../../app/pages/reports/stage9AnalysisData.js");
const api = require("../../app/pages/reports/stage9Analysis.js");
const snapshot = JSON.parse(await readFile(
  path.join(pfiRoot, "config/reports/v025_stage9_reviewed_analysis_snapshot.json"),
  "utf8",
));
const indexMarkup = await readFile(path.join(pfiRoot, "web/index.html"), "utf8");
const shellSource = await readFile(path.join(pfiRoot, "web/app/shell.js"), "utf8");

assert.equal(api.schema, "PFIV025Stage9ReviewedAnalysisUIAPIv1");
assert.equal(api.phaseId, "V025-S9-WHOLE-REVIEW");
assert.equal(snapshot.schema, "PFIV025Stage9ReviewedAnalysisPackV1");
assert.equal(snapshot.phase_id, "V025-S9-WHOLE-REVIEW");
assert.equal(snapshot.phase_9_3_candidate_complete, true);
assert.equal(snapshot.stage_9_whole_stage_review_done, false);
assert.equal(snapshot.stage_10_started, false);
assert.equal(snapshot.automatic_trading_allowed, false);
assert.equal(snapshot.financial_values_emitted, 0);
assert.equal(snapshot.contains_private_values, false);
assert.equal(api.snapshotBinding.packHash, snapshot.pack_hash);
assert.equal(data.packHash, snapshot.pack_hash);
assert.deepEqual(api.embeddedSnapshot(), snapshot.ui_contract);

const view = api.buildPhase92ViewModel(snapshot.ui_contract);
assert.equal(view.validation.status, "pass");
assert.equal(view.validation.reportCount, 5);
assert.equal(view.validation.formulaCount, 6);
assert.equal(view.validation.sensitivityCount, 4);
assert.equal(view.validation.modelCount, 1);
assert.equal(view.validation.reviewCount, 7);
assert.equal(view.validation.componentCount, 4);
assert.equal(view.validation.blockedCount, 3);
assert.equal(view.validation.partialCount, 2);
assert.deepEqual(
  Object.fromEntries(view.report_cards.map((report) => [report.report_type, report.status])),
  {
    net_worth: "blocked",
    cash: "blocked",
    investment: "blocked",
    consumption: "partial",
    cashflow: "partial",
  },
);
assert.deepEqual(
  Object.fromEntries(view.formula_cards.map((formula) => [formula.formula_id, formula.validation_status])),
  {
    "FORM-PFI-015": "validated_real_snapshot",
    "FORM-PFI-016": "blocked_missing_required_sources",
    "FORM-PFI-017": "blocked_missing_required_sources",
    "FORM-PFI-018": "blocked_insufficient_chain",
    "FORM-PFI-019": "validated_real_snapshot",
    "FORM-PFI-020": "validated_structure_only",
  },
);
assert.equal(view.model_cards[0].historical_out_of_sample_status, "blocked_insufficient_ground_truth");
assert.equal(view.model_cards[0].metamorphic_status, "pass");
assert.deepEqual(view.component_cards.map((item) => item.label_zh), [
  "消费总流出",
  "生活消费",
  "投资资金流出",
  "投资域内配置",
]);
assert.ok(view.component_cards.every((item) => item.status === "ready"));
assert.match(view.component_cards[0].scope_zh, /不等于净资产损失/);
for (const item of [...view.report_cards, ...view.formula_cards, ...view.sensitivity_cards, ...view.review_cards]) {
  const route = item.primary_review_route || item.review_route;
  assert.match(route, /^\//);
}

const serialized = JSON.stringify(view);
assert.doesNotMatch(serialized, /\bCNY\s+-?[0-9]/);
assert.doesNotMatch(serialized, /"(?:value|amount|financial_value)"\s*:/);
assert.doesNotMatch(serialized, /"[a-z0-9_]+_cny"\s*:/);
assert.equal(view.phase_9_3_candidate_complete, true);
assert.equal(view.stage_9_whole_stage_review_done, false);
assert.equal(view.stage_10_started, false);
assert.equal(view.automatic_trading_allowed, false);
assert.equal(view.financial_values_emitted, 0);
assert.equal(view.contains_private_values, false);

const tampered = structuredClone(snapshot.ui_contract);
tampered.report_cards[0].status = "complete";
assert.equal(api.validatePhase92ViewModel(tampered).status, "fail");
assert.throws(() => api.buildPhase92ViewModel(tampered), /invalid PFI v0\.2\.5 Stage 9 Phase 9\.2 UI contract/);

const dataScriptIndex = indexMarkup.indexOf("./app/pages/reports/stage9AnalysisData.js");
const stage9ScriptIndex = indexMarkup.indexOf("./app/pages/reports/stage9Analysis.js");
const shellScriptIndex = indexMarkup.indexOf("./app/shell.js");
assert.ok(dataScriptIndex > 0 && dataScriptIndex < stage9ScriptIndex && stage9ScriptIndex < shellScriptIndex);
assert.match(shellSource, /applyV025Stage5FinancialModelToSurfaces\(statusPayload\.stage5_financial_model\);\s+applyV025Stage9Phase92Analysis\(\);/);
assert.match(shellSource, /data-v025-stage9-phase92/);
assert.match(shellSource, /data-v025-stage9-component-count/);

console.log("stage9 reviewed reports frontend contract: pass");
