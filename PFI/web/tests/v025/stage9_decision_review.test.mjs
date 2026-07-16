import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";


const require = createRequire(import.meta.url);
const testDir = path.dirname(fileURLToPath(import.meta.url));
const pfiRoot = path.resolve(testDir, "../../..");
const data = require("../../app/pages/reports/stage9DecisionReviewData.js");
const api = require("../../app/pages/reports/stage9DecisionReview.js");
const snapshot = JSON.parse(await readFile(
  path.join(pfiRoot, "config/reports/v025_phase93_decision_snapshot.json"),
  "utf8",
));
const indexMarkup = await readFile(path.join(pfiRoot, "web/index.html"), "utf8");
const shellSource = await readFile(path.join(pfiRoot, "web/app/shell.js"), "utf8");

assert.equal(api.schema, "PFIV025Stage9Phase93DecisionReviewUIAPIv1");
assert.equal(api.phaseId, "V025-S9-P9.3");
assert.equal(data.packHash, snapshot.pack_hash);
assert.deepEqual(data.uiContract, snapshot.ui_contract);
assert.deepEqual(api.embeddedContract(), snapshot.ui_contract);

const view = api.buildPhase93ViewModel();
assert.equal(view.validation.status, "pass");
assert.equal(view.validation.decisionCount, 2);
assert.equal(view.validation.counterEvidenceCount, 4);
assert.equal(view.validation.invalidationConditionCount, 4);
assert.equal(view.validation.exportFormatCount, 4);
assert.equal(view.automatic_trading_allowed, false);
assert.equal(view.trade_execution_available, false);
assert.equal(view.stage_9_whole_stage_review_done, false);
assert.equal((await api.validateReviewLedger(view)).status, "pass");

const accepted = await api.applyHumanReview(
  view,
  "DEC-PFI-V025-REVIEW-QUEUE",
  "accepted",
  {
    reviewerRef: "local_owner",
    reasonZh: "接受分类复核，不执行交易。",
    observedAt: "2026-07-15T16:45:00+10:00",
  },
);
const acceptedDecision = accepted.decision_cards.find((item) => item.decision_id === "DEC-PFI-V025-REVIEW-QUEUE");
assert.equal(acceptedDecision.status, "accepted");
assert.equal(acceptedDecision.review_history.length, 2);
assert.equal(acceptedDecision.automatic_trading_allowed, false);
assert.equal(acceptedDecision.trade_execution_available, false);
assert.equal((await api.validateReviewLedger(accepted)).status, "pass");
await assert.rejects(
  api.applyHumanReview(accepted, acceptedDecision.decision_id, "rejected", {
    reviewerRef: "local_owner",
    reasonZh: "无效转换",
    observedAt: "2026-07-15T16:46:00+10:00",
  }),
  /invalid review transition/,
);

for (const format of ["html", "pdf", "csv", "markdown"]) {
  const validation = await api.verifyExportAsset(format);
  assert.equal(validation.status, "pass");
  assert.equal(validation.sourceSnapshotHash, snapshot.export_snapshot_hash);
  assert.ok(api.exportBytes(format).byteLength > 0);
}
assert.match(Buffer.from(api.exportBytes("pdf")).subarray(0, 5).toString(), /^%PDF-/);

const tamperedTrade = structuredClone(snapshot.ui_contract);
tamperedTrade.trade_execution_available = true;
assert.equal(api.validatePhase93ViewModel(tamperedTrade).status, "fail");
const tamperedCounter = structuredClone(snapshot.ui_contract);
tamperedCounter.decision_cards[0].counter_evidence = [];
assert.equal(api.validatePhase93ViewModel(tamperedCounter).status, "fail");
const tamperedSnapshot = structuredClone(snapshot.ui_contract);
tamperedSnapshot.export_cards[0].source_snapshot_hash = `sha256:${"0".repeat(64)}`;
assert.equal(api.validatePhase93ViewModel(tamperedSnapshot).status, "fail");

function memoryStorage(value = null) {
  return {
    value,
    getItem() { return this.value; },
    setItem(_key, next) { this.value = next; },
    removeItem() { this.value = null; },
  };
}

const validStorage = memoryStorage();
assert.equal(await api.persistViewModel(accepted, validStorage), true);
const persistedDelta = JSON.parse(validStorage.value);
assert.equal(persistedDelta.schema, "PFIV025Stage9Phase93ReviewDeltaV1");
assert.equal(persistedDelta.pack_hash, data.packHash);
assert.equal(Object.hasOwn(persistedDelta, "decision_cards"), false);
assert.equal(JSON.stringify(persistedDelta).includes("thesis"), false);
assert.equal(JSON.stringify(persistedDelta).includes("export_cards"), false);
const restored = await api.loadPersistedViewModel(validStorage);
assert.equal(restored.decision_cards[0].thesis.statement_zh, view.decision_cards[0].thesis.statement_zh);
assert.deepEqual(restored.export_cards, view.export_cards);
assert.equal(restored.decision_cards.find((item) => item.decision_id === acceptedDecision.decision_id).status, "accepted");

const immutableDrift = structuredClone(accepted);
immutableDrift.decision_cards[0].thesis.statement_zh = "stale local thesis";
assert.equal(await api.persistViewModel(immutableDrift, memoryStorage()), false);
const legacyFullPayload = memoryStorage(JSON.stringify(immutableDrift));
assert.equal(await api.loadPersistedViewModel(legacyFullPayload), null);
assert.equal(legacyFullPayload.value, null);

for (const mutate of [
  (delta) => { delta.pack_hash = `sha256:${"0".repeat(64)}`; },
  (delta) => { delta.review_records[0].review_history[1].event_hash = `sha256:${"0".repeat(64)}`; },
  (delta) => { delta.review_records[0].review_history[1].prior_event_hash = `sha256:${"0".repeat(64)}`; },
  (delta) => { delta.review_records[0].status = "rejected"; },
]) {
  const invalid = structuredClone(persistedDelta);
  mutate(invalid);
  const storage = memoryStorage(JSON.stringify(invalid));
  assert.equal(await api.loadPersistedViewModel(storage), null);
  assert.equal(storage.value, null);
}

const dataScriptIndex = indexMarkup.indexOf("./app/pages/reports/stage9DecisionReviewData.js");
const reviewScriptIndex = indexMarkup.indexOf("./app/pages/reports/stage9DecisionReview.js");
const shellScriptIndex = indexMarkup.indexOf("./app/shell.js");
assert.ok(dataScriptIndex > 0 && dataScriptIndex < reviewScriptIndex && reviewScriptIndex < shellScriptIndex);
assert.match(shellSource, /applyV025Stage9Phase93DecisionReview\(\);/);
assert.match(shellSource, /data-v025-stage9-phase93/);
assert.match(shellSource, /renderStage9DecisionReviewPanel/);

console.log("stage9 phase 9.3 decision review frontend contract: pass");
