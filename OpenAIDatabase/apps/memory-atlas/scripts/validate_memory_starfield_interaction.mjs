#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDir, "..");
const repoRoot = resolve(appRoot, "../..");

const galaxyScene = readFileSync(resolve(appRoot, "src/components/GalaxyScene.tsx"), "utf8");
const cssSource = readFileSync(resolve(appRoot, "src/styles.css"), "utf8");
const visualAudit = readFileSync(resolve(repoRoot, "scripts/audit_memory_atlas_visual_acceptance.py"), "utf8");

const checks = [];

function requireCheck(name, condition, evidence, failure) {
  checks.push({ name, status: condition ? "PASS" : "FAIL", evidence: condition ? evidence : failure });
}

function hasAll(source, needles) {
  return needles.every((needle) => source.includes(needle));
}

requireCheck(
  "hover_preview_does_not_select",
  hasAll(galaxyScene, [
    "function updateHoverPreview",
    "hoveredIdRef.current = item.node.id",
    "setHoverPreview({",
    "function onPointerUp",
    "if (item) onSelectNode(item.node)",
  ]) && cssSource.includes("pointer-events: none;"),
  "hover uses transient preview state; selected node changes only in pointer-up click handling",
  "hover preview may mutate selected node state or lack transient preview evidence",
);

requireCheck(
  "click_focus_is_capped_and_inspector_synced",
  hasAll(galaxyScene, [
    "function updateCameraFocus",
    "camera.position.lerp(cameraTargetPosition",
    "buildFocusedNeighborhood",
    "MAX_FOCUS_PRIMARY_NEIGHBORS",
    "MAX_FOCUS_SECONDARY_NEIGHBORS",
    "MAX_FOCUS_VISIBLE_NEIGHBORS",
    "hiddenNeighborCount",
    "primaryNeighborCards",
    "onClick={() => onSelectNode(node)}",
  ]),
  "click focus keeps camera fly-in, capped local neighborhood, folded high-degree neighbors and Inspector synchronization",
  "click focus may lack camera fly-in, capped neighborhood, folded high-degree protection or Inspector sync",
);

requireCheck(
  "freeze_resume_flow_exists",
  hasAll(galaxyScene, [
    "const [flowPaused, setFlowPaused]",
    "flowPausedRef",
    "dataset.flowFrozen",
    "Freeze Flow Field",
    "Resume Flow Field",
    "if (flowPausedRef.current) return;",
    "const frozen = rendererMode === \"memory-starfield\" && flowPausedRef.current",
    "if (!frozen) frame += 1",
  ]),
  "Freeze/Resume control pauses flow time, auto rotation, pulse updates and exposes debug dataset/signal state",
  "Freeze/Resume flow control or frozen render-loop behavior is missing",
);

requireCheck(
  "presentation_analysis_mode_exists",
  hasAll(galaxyScene, [
    "type StarfieldViewMode = \"presentation\" | \"analysis\"",
    "const [starfieldMode, setStarfieldMode]",
    "Starfield mode selector",
    "Presentation Mode",
    "Analysis Mode",
    "data-starfield-mode={starfieldMode}",
    "starfieldMode === \"analysis\"",
    "Starfield formula summary",
    "Analysis inspector summary",
  ]),
  "Presentation/Analysis segmented mode keeps Presentation clean and shows formulas, terrain legend and Inspector context only in Analysis",
  "Presentation/Analysis mode, formula summary, legend or Inspector explanation is missing",
);

requireCheck(
  "interaction_styles_and_audit_contract_exist",
  hasAll(cssSource, [
    ".galaxy-mode-tabs",
    ".terrain-formula-grid",
    ".terrain-inspector-strip",
  ]) && hasAll(visualAudit, [
    "galaxy_stage4_3_interaction_ready",
    "Freeze Flow Field",
    "Starfield mode selector",
  ]),
  "styles and visual audit cover Stage 4.3 interaction controls and Analysis panel layout",
  "Stage 4.3 interaction styles or visual audit contract are missing",
);

const failed = checks.filter((check) => check.status !== "PASS");
const result = { status: failed.length ? "FAIL" : "PASS", checks };
console.log(JSON.stringify(result, null, 2));
if (failed.length) process.exit(1);
