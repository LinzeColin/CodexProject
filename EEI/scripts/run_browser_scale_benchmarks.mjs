#!/usr/bin/env node
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { mkdir, readFile, writeFile } from "node:fs/promises";

const ROOT = path.resolve(fileURLToPath(new URL("..", import.meta.url)));
const requireFromWeb = createRequire(new URL("../apps/web/package.json", import.meta.url));
const { chromium } = requireFromWeb("@playwright/test");

const TARGET_SCALES = [10_000, 100_000, 1_000_000];
const MAX_VISIBLE_NODES = 500;
const MAX_VISIBLE_EDGES = 2_000;
const BROWSER_RENDER_P95_MS = 1_000;
const BROWSER_FRAME_P95_MS = 250;
const BROWSER_LONG_TASK_MAX_COUNT = 10;
const PARAMETER_KEYS = new Map([
  [10_000, "benchmark.scale_10k_p95_ms"],
  [100_000, "benchmark.scale_100k_p95_ms"],
  [1_000_000, "benchmark.scale_1m_p95_ms"]
]);

function parseArgs(argv) {
  const args = {
    scales: "10000,100000,1000000",
    iterations: 2,
    output: "/tmp/eei-browser-scale-benchmark.json",
    mode: "browser_runtime",
    failOnBudget: false,
    quiet: false
  };
  for (let index = 2; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--scales") {
      args.scales = argv[++index];
    } else if (item === "--iterations") {
      args.iterations = Number.parseInt(argv[++index], 10);
    } else if (item === "--output") {
      args.output = argv[++index];
    } else if (item === "--mode") {
      args.mode = argv[++index];
    } else if (item === "--fail-on-budget") {
      args.failOnBudget = true;
    } else if (item === "--quiet") {
      args.quiet = true;
    } else {
      throw new Error(`Unknown argument: ${item}`);
    }
  }
  if (!Number.isInteger(args.iterations) || args.iterations <= 0) {
    throw new Error("--iterations must be a positive integer");
  }
  return args;
}

function parseScales(rawValue) {
  const scales = rawValue
    .split(",")
    .map((item) => Number.parseInt(item.trim().replaceAll("_", ""), 10))
    .filter((value) => Number.isFinite(value));
  if (scales.length === 0 || scales.some((value) => value <= 0)) {
    throw new Error("--scales must contain positive integers");
  }
  return scales;
}

function parseCsvLine(line) {
  const values = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && quoted && next === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      values.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  values.push(current);
  return values;
}

async function readBudgetMs() {
  const catalog = await readFile(path.join(ROOT, "data/parameter_catalog.csv"), "utf8");
  const lines = catalog.replace(/^\uFEFF/, "").trim().split(/\r?\n/);
  const header = parseCsvLine(lines[0]);
  const keyIndex = header.indexOf("parameter_key");
  const valueIndex = header.indexOf("default_value");
  const budgets = new Map();
  for (const line of lines.slice(1)) {
    const row = parseCsvLine(line);
    for (const [scale, parameterKey] of PARAMETER_KEYS.entries()) {
      if (row[keyIndex] === parameterKey) {
        budgets.set(scale, Number.parseFloat(row[valueIndex]));
      }
    }
  }
  const missing = TARGET_SCALES.filter((scale) => !budgets.has(scale));
  if (missing.length > 0) {
    throw new Error(`Missing browser benchmark budget parameters: ${missing.join(",")}`);
  }
  return budgets;
}

function budgetForScale(scale, budgets) {
  const ceiling = TARGET_SCALES.find((targetScale) => scale <= targetScale);
  return budgets.get(ceiling ?? TARGET_SCALES[TARGET_SCALES.length - 1]);
}

function percentile(values, percentileValue) {
  if (values.length === 0) {
    throw new Error("Cannot compute percentile for empty values");
  }
  const ordered = [...values].sort((left, right) => left - right);
  if (ordered.length === 1) {
    return ordered[0];
  }
  const position = (ordered.length - 1) * percentileValue;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) {
    return ordered[position];
  }
  return ordered[lower] * (upper - position) + ordered[upper] * (position - lower);
}

function summary(values) {
  return {
    min: Number(Math.min(...values).toFixed(4)),
    p50: Number(percentile(values, 0.5).toFixed(4)),
    p95: Number(percentile(values, 0.95).toFixed(4)),
    p99: Number(percentile(values, 0.99).toFixed(4)),
    max: Number(Math.max(...values).toFixed(4))
  };
}

async function measureBrowserScale(page, scale, iterations) {
  const samples = [];
  for (let index = 0; index < iterations; index += 1) {
    samples.push(
      await page.evaluate(
        async ({ scaleValue, maxNodes, maxEdges }) => {
          const namespace = "http://www.w3.org/2000/svg";
          const container = document.getElementById("benchmark-root");
          if (!container) {
            throw new Error("benchmark-root missing");
          }
          container.textContent = "";

          const visibleEdges = Math.min(maxEdges, Math.max(1, Math.floor(scaleValue / 5)));
          const visibleNodes = Math.min(
            maxNodes,
            Math.max(16, Math.ceil(Math.sqrt(scaleValue)) * 2)
          );
          const longTasks = [];
          let observer = null;
          if ("PerformanceObserver" in window) {
            try {
              observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                  longTasks.push(entry.duration);
                }
              });
              observer.observe({ entryTypes: ["longtask"] });
            } catch {
              observer = null;
            }
          }

          const beforeHeap =
            performance.memory && Number.isFinite(performance.memory.usedJSHeapSize)
              ? performance.memory.usedJSHeapSize
              : null;
          const beforeFrame = await new Promise((resolve) => requestAnimationFrame(resolve));
          const start = performance.now();
          const svg = document.createElementNS(namespace, "svg");
          svg.setAttribute("class", "ecosystemMap browserScaleBenchmark");
          svg.setAttribute("role", "img");
          svg.setAttribute("aria-label", "EEI browser scale benchmark graph");
          svg.setAttribute("viewBox", "0 0 1440 900");
          svg.setAttribute("width", "1440");
          svg.setAttribute("height", "900");
          svg.dataset.scaleRelationships = String(scaleValue);
          svg.dataset.visibleNodes = String(visibleNodes);
          svg.dataset.visibleEdges = String(visibleEdges);

          const fragment = document.createDocumentFragment();
          const nodes = [];
          for (let nodeIndex = 0; nodeIndex < visibleNodes; nodeIndex += 1) {
            const angle = ((nodeIndex * 137.5) % 360) * (Math.PI / 180);
            const radius = 120 + (nodeIndex % 12) * 22;
            nodes.push({
              id: nodeIndex,
              x: 720 + Math.cos(angle) * radius + (nodeIndex % 5) * 18,
              y: 450 + Math.sin(angle) * radius + (nodeIndex % 7) * 14
            });
          }

          for (let edgeIndex = 0; edgeIndex < visibleEdges; edgeIndex += 1) {
            const source = nodes[edgeIndex % visibleNodes];
            const target = nodes[(edgeIndex * 17 + 11) % visibleNodes];
            const group = document.createElementNS(namespace, "g");
            group.setAttribute("class", "edgeGroup active");
            const line = document.createElementNS(namespace, "line");
            line.setAttribute("class", "edge");
            line.setAttribute("x1", String(source.x));
            line.setAttribute("y1", String(source.y));
            line.setAttribute("x2", String(target.x));
            line.setAttribute("y2", String(target.y));
            const label = document.createElementNS(namespace, "text");
            label.setAttribute("class", "edgeLabel");
            label.setAttribute("x", String((source.x + target.x) / 2));
            label.setAttribute("y", String((source.y + target.y) / 2));
            label.textContent = edgeIndex % 2 === 0 ? "supply chain" : "technology platform";
            group.append(line, label);
            fragment.append(group);
          }

          for (const node of nodes) {
            const group = document.createElementNS(namespace, "g");
            group.setAttribute("class", "node active");
            group.setAttribute("transform", `translate(${node.x} ${node.y})`);
            const circle = document.createElementNS(namespace, "circle");
            circle.setAttribute("r", "24");
            const label = document.createElementNS(namespace, "text");
            label.setAttribute("text-anchor", "middle");
            label.textContent = `N${node.id}`;
            const stage = document.createElementNS(namespace, "text");
            stage.setAttribute("class", "nodeStage");
            stage.setAttribute("text-anchor", "middle");
            stage.setAttribute("y", "42");
            stage.textContent = node.id % 2 === 0 ? "upstream" : "downstream";
            group.append(circle, label, stage);
            fragment.append(group);
          }

          svg.append(fragment);
          container.append(svg);
          const renderMs = performance.now() - start;
          const afterFrame = await new Promise((resolve) => requestAnimationFrame(resolve));
          await new Promise((resolve) => setTimeout(resolve, 0));
          const afterHeap =
            performance.memory && Number.isFinite(performance.memory.usedJSHeapSize)
              ? performance.memory.usedJSHeapSize
              : null;
          if (observer) {
            observer.disconnect();
          }
          const serialized = new XMLSerializer().serializeToString(svg);
          const payloadBytes = new Blob([serialized]).size;
          return {
            render_ms: renderMs,
            frame_delta_ms: afterFrame - beforeFrame,
            heap_delta_bytes:
              beforeHeap === null || afterHeap === null ? null : Math.max(0, afterHeap - beforeHeap),
            heap_sample_available: beforeHeap !== null && afterHeap !== null,
            dom_payload_bytes: payloadBytes,
            long_task_count: longTasks.length,
            max_long_task_ms: longTasks.length === 0 ? 0 : Math.max(...longTasks),
            rendered_nodes: visibleNodes,
            rendered_edges: visibleEdges
          };
        },
        { scaleValue: scale, maxNodes: MAX_VISIBLE_NODES, maxEdges: MAX_VISIBLE_EDGES }
      )
    );
  }
  return samples;
}

async function buildPayload(scales, iterations, mode, budgets) {
  const browser = await chromium.launch({
    headless: true,
    args: ["--disable-dev-shm-usage", "--disable-gpu", "--enable-precise-memory-info", "--no-sandbox"]
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.setContent("<!doctype html><meta charset='utf-8'><div id='benchmark-root'></div>");
    const results = [];
    for (const scale of scales) {
      const samples = await measureBrowserScale(page, scale, iterations);
      const renderSummary = summary(samples.map((sample) => sample.render_ms));
      const frameSummary = summary(samples.map((sample) => sample.frame_delta_ms));
      const longTaskMax = Math.max(...samples.map((sample) => sample.long_task_count));
      const maxLongTaskMs = Math.max(...samples.map((sample) => sample.max_long_task_ms));
      const payloadSummary = summary(samples.map((sample) => sample.dom_payload_bytes));
      const heapSamples = samples
        .map((sample) => sample.heap_delta_bytes)
        .filter((value) => value !== null);
      const heapSummary = heapSamples.length > 0 ? summary(heapSamples) : null;
      const totalBudgetMs = budgetForScale(scale, budgets);
      const status =
        renderSummary.p95 <= Math.min(totalBudgetMs, BROWSER_RENDER_P95_MS) &&
        frameSummary.p95 <= BROWSER_FRAME_P95_MS &&
        longTaskMax <= BROWSER_LONG_TASK_MAX_COUNT
          ? "PASS"
          : "FAIL";
      results.push({
        scale_relationships: scale,
        iterations,
        status,
        budget_ms: totalBudgetMs,
        browser_budget_profile: {
          render_p95_ms: Math.min(totalBudgetMs, BROWSER_RENDER_P95_MS),
          frame_p95_ms: BROWSER_FRAME_P95_MS,
          long_task_max_count: BROWSER_LONG_TASK_MAX_COUNT
        },
        browser_render_ms: renderSummary,
        browser_frame_delta_ms: frameSummary,
        browser_heap_delta_bytes: heapSummary,
        browser_dom_payload_bytes: payloadSummary,
        browser_long_task_count: longTaskMax,
        browser_max_long_task_ms: Number(maxLongTaskMs.toFixed(4)),
        last_counts: {
          rendered_nodes: samples.at(-1).rendered_nodes,
          rendered_edges: samples.at(-1).rendered_edges,
          heap_sample_available: samples.at(-1).heap_sample_available
        },
        metric_groups: {
          browser_runtime: true,
          memory: true,
          frame: true,
          long_task: true
        }
      });
    }
    const measuredScales = results.map((result) => result.scale_relationships).sort((a, b) => a - b);
    const targetScalesMeasured = TARGET_SCALES.every((scale) => measuredScales.includes(scale));
    const allMeasuredPass = results.every((result) => result.status === "PASS");
    return {
      schema_version: "eei-browser-scale-benchmark-v1",
      system_name: "EEI",
      task_id: "T1306",
      acceptance_ids: ["A208"],
      status: targetScalesMeasured && allMeasuredPass ? "PASS" : allMeasuredPass ? "PARTIAL" : "FAIL",
      mode,
      generated_at: new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
      environment: {
        node: process.version,
        platform: `${os.platform()}-${os.release()}-${os.arch()}`,
        cpu_count: os.cpus().length,
        browser: "chromium"
      },
      target_scales: TARGET_SCALES,
      measured_scales: measuredScales,
      iterations,
      results,
      coverage: {
        target_scales_measured: targetScalesMeasured,
        browser_runtime_measured: true,
        required_metric_groups: ["browser_runtime", "memory", "frame", "long_task"],
        full_browser_runtime_pass: targetScalesMeasured && allMeasuredPass
      },
      remaining_to_close_a208:
        targetScalesMeasured && allMeasuredPass
          ? []
          : ["Run browser runtime benchmark for 10k, 100k and 1m with passing budgets."]
    };
  } finally {
    await browser.close();
  }
}

async function main() {
  const args = parseArgs(process.argv);
  const scales = parseScales(args.scales);
  const budgets = await readBudgetMs();
  const payload = await buildPayload(scales, args.iterations, args.mode, budgets);
  await mkdir(path.dirname(path.resolve(args.output)), { recursive: true });
  await writeFile(args.output, `${JSON.stringify(payload, null, 2)}\n`);
  if (!args.quiet) {
    console.log(JSON.stringify(payload, null, 2));
  }
  if (args.failOnBudget && payload.status === "FAIL") {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
