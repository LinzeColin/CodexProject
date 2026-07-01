#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDir, "..");
const repoRoot = resolve(appRoot, "../..");

const packageSource = readFileSync(resolve(appRoot, "package.json"), "utf8");
const appSource = readFileSync(resolve(appRoot, "src/App.tsx"), "utf8");
const stateSource = readFileSync(resolve(appRoot, "src/state/sharedAtlasState.ts"), "utf8");
const visualAudit = readFileSync(resolve(repoRoot, "scripts/audit_memory_atlas_visual_acceptance.py"), "utf8");
const modelParameters = readFileSync(resolve(repoRoot, "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md"), "utf8");
const deliveryRecord = readFileSync(resolve(repoRoot, "docs/MEMORY_ATLAS_DELIVERY_RECORD.md"), "utf8");
const changelog = readFileSync(resolve(repoRoot, "CHANGELOG.md"), "utf8");
const stageReview = readFileSync(resolve(repoRoot, "docs/reviews/memory_atlas_v1_1_5_stage6_review.md"), "utf8");
const phaseReviews = [
  "memory_atlas_v1_1_5_stage6_1_review.md",
  "memory_atlas_v1_1_5_stage6_2_review.md",
].map((name) => readFileSync(resolve(repoRoot, `docs/reviews/${name}`), "utf8"));

const checks = [];

requireCheck(
  "stage6_phase_reviews_complete",
  phaseReviews[0].includes("Stage 6.1 is review-passed")
    && phaseReviews[1].includes("Stage 6.2 is review-passed")
    && hasAll(stageReview, [
      "Stage 6 is review-passed",
      "6.1 Shared State Store",
      "6.2 Inspector and Proposal",
      "No raw/private/cookie/session/secret fields were introduced",
      "No Cloudflare deployment or Access policy change was performed",
      "No direct frontend writeback was added",
    ]),
  "Stage 6.1/6.2 phase reviews and whole-stage review all record PASS boundaries",
  "Stage 6 phase review or whole-stage review PASS evidence is missing",
);

requireCheck(
  "stage6_validators_and_visual_audit_cover_all_phases",
  hasAll(packageSource, [
    '"validate:shared-state": "node --experimental-strip-types scripts/validate_shared_state_store.mjs"',
    '"validate:inspector-proposal": "node scripts/validate_inspector_proposal.mjs"',
    '"validate:stage6": "node scripts/validate_memory_atlas_stage6.mjs"',
  ]) && hasAll(visualAudit, [
    "stage6_1_shared_state_store_ready",
    "stage6_2_inspector_proposal_ready",
  ]),
  "Package scripts and visual acceptance audit cover Stage 6.1 shared state and Stage 6.2 Inspector/Proposal",
  "Stage 6 validators or visual audit hooks do not cover every phase",
);

requireCheck(
  "stage6_shared_state_and_inspector_contracts_intact",
  hasAll(stateSource, [
    "export interface SharedAtlasSelectionState",
    "export interface SharedAtlasFilterState",
    "export interface SharedAtlasFocusState",
    "export function sharedAtlasReducer",
    "loopGuard",
  ]) && hasAll(appSource, [
    "useReducer(",
    "sharedAtlasReducer",
    "function InspectorExplanationPanel",
    "function buildWritebackProposalDraft",
    'data-debug-lite={debugOpen ? "open" : "closed"}',
    'data-proposal-only="true"',
    'data-active-memory-mutation="false"',
    "direct_frontend_mutation_of_active_memory: false",
  ]),
  "Shared-state reducer, Inspector explanation, Debug separation and proposal-only safety contracts remain intact",
  "Stage 6 shared-state or Inspector/Proposal source contracts are missing",
);

requireCheck(
  "stage6_model_parameters_reviewed",
  hasAll(modelParameters, [
    "Shared State Store 状态模型",
    "Inspector 解释与 Proposal 安全模型",
    "stage_6_whole_stage_review_passed",
    "Stage 6 整体复审已确认",
    "direct_frontend_mutation_of_active_memory = false",
    "requires_agent_or_human_apply = true",
  ]),
  "Model parameters record Stage 6 shared-state and Inspector/Proposal review status with fail-closed writeback safety",
  "Model parameters lack Stage 6 whole-stage review status or safety settings",
);

requireCheck(
  "stage6_delivery_record_current",
  hasAll(deliveryRecord, [
    "完成 Memory Atlas v1.1.5 Stage 6 整体复审",
    "Stage 6 整阶段复审通过",
    "Stage 7",
  ]) && !deliveryRecord.includes("Stage 6 整体复审：复核 6.1 shared state"),
  "Delivery record marks Stage 6 reviewed and keeps later Stage 7 gates active",
  "Delivery record still lists Stage 6 whole-stage review as pending or lacks Stage 7 follow-up gates",
);

requireCheck(
  "stage6_changelog_current",
  hasAll(changelog, [
    "Memory Atlas v1.1.5 Stage 6 Whole-Stage Review",
    "Completed the Stage 6 whole-stage review",
    "`validate:stage6`",
    "No ingestion, raw/private data access, direct writeback",
    "Cloudflare live deploy, GitHub main upload",
    "external account operation was",
    "added.",
  ]),
  "Changelog records Stage 6 whole-stage review and preserves non-goal boundaries",
  "Changelog lacks Stage 6 whole-stage review status or boundary statement",
);

const failed = checks.filter((check) => check.status !== "PASS");
const result = { status: failed.length ? "FAIL" : "PASS", checks };
console.log(JSON.stringify(result, null, 2));
if (failed.length) process.exit(1);

function requireCheck(name, condition, evidence, failure) {
  checks.push({ name, status: condition ? "PASS" : "FAIL", evidence: condition ? evidence : failure });
}

function hasAll(source, needles) {
  return needles.every((needle) => source.includes(needle));
}
