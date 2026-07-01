#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDir, "..");
const repoRoot = resolve(appRoot, "../..");

const packageSource = readFileSync(resolve(appRoot, "package.json"), "utf8");
const galaxySource = readFileSync(resolve(appRoot, "src/components/GalaxyScene.tsx"), "utf8");
const appSource = readFileSync(resolve(appRoot, "src/App.tsx"), "utf8");
const visualAudit = readFileSync(resolve(repoRoot, "scripts/audit_memory_atlas_visual_acceptance.py"), "utf8");
const modelParameters = readFileSync(resolve(repoRoot, "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md"), "utf8");
const deliveryRecord = readFileSync(resolve(repoRoot, "docs/MEMORY_ATLAS_DELIVERY_RECORD.md"), "utf8");
const changelog = readFileSync(resolve(repoRoot, "CHANGELOG.md"), "utf8");
const stageReview = readFileSync(resolve(repoRoot, "docs/reviews/memory_atlas_v1_1_5_stage7_review.md"), "utf8");
const phaseReviews = [
  "memory_atlas_v1_1_5_stage7_1_review.md",
  "memory_atlas_v1_1_5_stage7_2_review.md",
  "memory_atlas_v1_1_5_stage7_3_review.md",
].map((name) => readFileSync(resolve(repoRoot, `docs/reviews/${name}`), "utf8"));

const checks = [];

requireCheck(
  "stage7_phase_reviews_complete",
  phaseReviews[0].includes("Stage 7.1 is review-passed")
    && phaseReviews[1].includes("Stage 7.2 is review-passed")
    && phaseReviews[2].includes("Stage 7.3 is review-passed")
    && hasAll(stageReview, [
      "Stage 7 is review-passed",
      "7.1 Visual Acceptance",
      "7.2 Performance Acceptance",
      "7.3 Privacy and Accessibility",
      "No raw/private/cookie/session/secret fields were introduced",
      "No Cloudflare deployment or Access policy change was performed",
      "No direct frontend writeback was added",
    ]),
  "Stage 7.1/7.2/7.3 phase reviews and whole-stage review all record PASS boundaries",
  "Stage 7 phase review or whole-stage review PASS evidence is missing",
);

requireCheck(
  "stage7_validators_and_visual_audit_cover_all_phases",
  hasAll(packageSource, [
    '"validate:stage7-visual": "node scripts/validate_stage7_visual_acceptance.cjs"',
    '"validate:stage7-performance": "node scripts/validate_stage7_performance_acceptance.cjs"',
    '"validate:stage7-privacy-accessibility": "node scripts/validate_stage7_privacy_accessibility.cjs"',
    '"validate:stage7": "node scripts/validate_memory_atlas_stage7.mjs"',
  ]) && hasAll(visualAudit, [
    "stage7_1_visual_acceptance_ready",
    "stage7_2_performance_acceptance_ready",
    "stage7_3_privacy_accessibility_ready",
  ]),
  "Package scripts and visual acceptance audit cover Stage 7.1 visual, Stage 7.2 performance, and Stage 7.3 privacy/accessibility",
  "Stage 7 validators or visual audit hooks do not cover every phase",
);

requireCheck(
  "stage7_visual_performance_privacy_contracts_intact",
  hasAll(galaxySource, [
    "__memoryAtlasGalaxySignal",
    "GalaxyPerformanceSnapshot",
    "__memoryAtlasGalaxyLifecycle",
    "className=\"galaxy-performance-overlay\"",
    "renderer.forceContextLoss()",
  ]) && hasAll(appSource, [
    'data-feedback-defaults={feedbackSettings.pseudoHaptic || feedbackSettings.audio ? "opted-in" : "silent-by-default"}',
    'data-feedback-pseudo-haptic={feedbackSettings.pseudoHaptic ? "enabled" : "disabled"}',
    'data-feedback-audio={feedbackSettings.audio ? "enabled" : "disabled"}',
    'window.matchMedia?.("(prefers-reduced-motion: reduce)").matches',
    "navigator.vibrate",
    "new window.AudioContext()",
  ]),
  "Galaxy visual/performance cleanup contracts and Timeline privacy/accessibility feedback contracts remain intact",
  "Stage 7 runtime contracts for visual, performance, cleanup, reduced motion, or silent feedback are missing",
);

requireCheck(
  "stage7_model_parameters_reviewed",
  hasAll(modelParameters, [
    "Stage 7.1 视觉验收模型",
    "Stage 7.2 性能验收模型",
    "Stage 7.3 隐私与无障碍验收模型",
    "stage_7_whole_stage_review_passed",
    "Stage 7 整体复审已确认",
    "source_contract.mode == \"public_redacted_read_only_visualization\"",
    "direct_frontend_mutation_of_active_memory == false",
  ]),
  "Model parameters record Stage 7 visual, performance, privacy/accessibility, and whole-stage review status",
  "Model parameters lack Stage 7 whole-stage review status or required safety thresholds",
);

requireCheck(
  "stage7_delivery_record_current",
  hasAll(deliveryRecord, [
    "完成 Memory Atlas v1.1.5 Stage 7 整体复审",
    "Stage 7 整阶段复审通过",
    "Stage 8: 打包、部署、回滚",
  ]) && !deliveryRecord.includes("Stage 7 整体复审：确认 7.1 Visual、7.2 Performance、7.3 Privacy/Accessibility 全部通过后再上传 GitHub main。"),
  "Delivery record marks Stage 7 reviewed and moves the next gate to Stage 8 packaging/deploy/rollback",
  "Delivery record still lists Stage 7 whole-stage review as pending or lacks Stage 8 follow-up gate",
);

requireCheck(
  "stage7_changelog_current",
  hasAll(changelog, [
    "Memory Atlas v1.1.5 Stage 7 Whole-Stage Review",
    "Completed the Stage 7 whole-stage review",
    "`validate:stage7`",
    "No ingestion, raw/private data access, direct writeback",
    "Cloudflare live deploy",
    "external account operation was added",
  ]),
  "Changelog records Stage 7 whole-stage review and preserves non-goal boundaries",
  "Changelog lacks Stage 7 whole-stage review status or boundary statement",
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
