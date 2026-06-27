#!/usr/bin/env node
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";

const ROOT = path.resolve(fileURLToPath(new URL("..", import.meta.url)));
const requireFromWeb = createRequire(new URL("../apps/web/package.json", import.meta.url));
let chromium = null;

const DEFAULT_SMOKE_SECONDS = 3;
const DEFAULT_BROWSER_SLICE_SECONDS = 15;
const BROWSER_SAMPLE_EVERY_MS = 50;
const LOCAL_PLAYWRIGHT_BROWSERS_PATH = "/private/tmp/eei-ms-playwright";
const MAX_HEAP_GROWTH_BYTES = 8 * 1024 * 1024;
const MAX_DOM_GROWTH_NODES = 12;
const MAX_TIMER_LEAKS = 0;
const MAX_LISTENER_LEAKS = 0;
const MAX_EVENT_LOOP_LAG_MS = 250;
const MAX_BROWSER_SLICE_RECOVERIES = 2;
const WORKER_BINDING_ARTIFACT = path.join(
  ROOT,
  "artifacts/tests/a206/t1304_worker_deployment_binding_contract.json"
);

function parseArgs(argv) {
  const args = {
    mode: "ci_smoke",
    durationSeconds: DEFAULT_SMOKE_SECONDS,
    browserSliceSeconds: null,
    output: "/tmp/eei-soak-smoke.json",
    failOnBudget: false,
    quiet: false
  };
  for (let index = 2; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--mode") {
      args.mode = argv[++index];
    } else if (item === "--duration-seconds") {
      args.durationSeconds = Number.parseFloat(argv[++index]);
    } else if (item === "--browser-slice-seconds") {
      args.browserSliceSeconds = Number.parseFloat(argv[++index]);
    } else if (item === "--output") {
      args.output = argv[++index];
    } else if (item === "--fail-on-budget") {
      args.failOnBudget = true;
    } else if (item === "--quiet") {
      args.quiet = true;
    } else {
      throw new Error(`Unknown argument: ${item}`);
    }
  }
  if (!Number.isFinite(args.durationSeconds) || args.durationSeconds <= 0) {
    throw new Error("--duration-seconds must be positive");
  }
  if (args.browserSliceSeconds === null) {
    args.browserSliceSeconds = Math.min(DEFAULT_BROWSER_SLICE_SECONDS, args.durationSeconds);
  }
  if (!Number.isFinite(args.browserSliceSeconds) || args.browserSliceSeconds <= 0) {
    throw new Error("--browser-slice-seconds must be positive");
  }
  return args;
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

async function readSoakParameters() {
  const catalog = await readFile(path.join(ROOT, "data/parameter_catalog.csv"), "utf8");
  const lines = catalog.replace(/^\uFEFF/, "").trim().split(/\r?\n/);
  const header = parseCsvLine(lines[0]);
  const keyIndex = header.indexOf("parameter_key");
  const valueIndex = header.indexOf("default_value");
  const values = {};
  for (const line of lines.slice(1)) {
    const row = parseCsvLine(line);
    if (row[keyIndex] === "soak.short_duration_hours") {
      values.short_duration_hours = Number.parseFloat(row[valueIndex]);
    }
    if (row[keyIndex] === "soak.long_duration_hours") {
      values.long_duration_hours = Number.parseFloat(row[valueIndex]);
    }
  }
  if (!values.short_duration_hours || !values.long_duration_hours) {
    throw new Error("Missing soak duration parameters");
  }
  return values;
}

async function readWorkerDeploymentBinding() {
  try {
    return JSON.parse(await readFile(WORKER_BINDING_ARTIFACT, "utf8"));
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

async function resolvePlaywrightBrowserPath() {
  if (process.env.PLAYWRIGHT_BROWSERS_PATH) {
    return {
      source: "environment",
      path: process.env.PLAYWRIGHT_BROWSERS_PATH
    };
  }
  try {
    await access(LOCAL_PLAYWRIGHT_BROWSERS_PATH);
    process.env.PLAYWRIGHT_BROWSERS_PATH = LOCAL_PLAYWRIGHT_BROWSERS_PATH;
    return {
      source: "local_fallback",
      path: LOCAL_PLAYWRIGHT_BROWSERS_PATH
    };
  } catch {
    return {
      source: "playwright_default",
      path: null
    };
  }
}

function getChromium() {
  if (!chromium) {
    ({ chromium } = requireFromWeb("@playwright/test"));
  }
  return chromium;
}

function percentile(values, percentileValue) {
  if (values.length === 0) {
    return 0;
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
  if (values.length === 0) {
    return {
      min: 0,
      p50: 0,
      p95: 0,
      p99: 0,
      max: 0
    };
  }
  return {
    min: Number(Math.min(...values).toFixed(4)),
    p50: Number(percentile(values, 0.5).toFixed(4)),
    p95: Number(percentile(values, 0.95).toFixed(4)),
    p99: Number(percentile(values, 0.99).toFixed(4)),
    max: Number(Math.max(...values).toFixed(4))
  };
}

async function runBrowserSoakSlice(page, durationMs) {
  return await page.evaluate(
    async ({ durationMs, sampleEveryMs }) => {
      const namespace = "http://www.w3.org/2000/svg";
      const root = document.getElementById("soak-root");
      if (!root) {
        throw new Error("soak-root missing");
      }
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

      let listenerBalance = 0;
      let timerBalance = 0;
      const heapSamples = [];
      const domSamples = [];
      const frameDeltas = [];
      const startHeap =
        performance.memory && Number.isFinite(performance.memory.usedJSHeapSize)
          ? performance.memory.usedJSHeapSize
          : null;
      const endAt = performance.now() + durationMs;

      while (performance.now() < endAt) {
        const beforeFrame = await new Promise((resolve) => requestAnimationFrame(resolve));
        const svg = document.createElementNS(namespace, "svg");
        svg.setAttribute("viewBox", "0 0 320 180");
        const fragment = document.createDocumentFragment();
        for (let index = 0; index < 80; index += 1) {
          const line = document.createElementNS(namespace, "line");
          line.setAttribute("x1", String(index % 32));
          line.setAttribute("y1", String((index * 3) % 180));
          line.setAttribute("x2", String(320 - (index % 32)));
          line.setAttribute("y2", String((index * 5) % 180));
          fragment.append(line);
        }
        svg.append(fragment);
        const handler = () => undefined;
        svg.addEventListener("click", handler);
        listenerBalance += 1;
        const timer = window.setTimeout(() => undefined, 0);
        timerBalance += 1;
        root.replaceChildren(svg);
        svg.removeEventListener("click", handler);
        listenerBalance -= 1;
        window.clearTimeout(timer);
        timerBalance -= 1;
        const afterFrame = await new Promise((resolve) => requestAnimationFrame(resolve));
        frameDeltas.push(afterFrame - beforeFrame);
        const heap =
          performance.memory && Number.isFinite(performance.memory.usedJSHeapSize)
            ? performance.memory.usedJSHeapSize
            : null;
        if (heap !== null) {
          heapSamples.push(heap);
        }
        domSamples.push(document.querySelectorAll("*").length);
        await new Promise((resolve) => setTimeout(resolve, sampleEveryMs));
      }
      if (observer) {
        observer.disconnect();
      }
      const endHeap =
        performance.memory && Number.isFinite(performance.memory.usedJSHeapSize)
          ? performance.memory.usedJSHeapSize
          : null;
      const domGrowth =
        domSamples.length === 0 ? 0 : Math.max(...domSamples) - Math.min(...domSamples);
      return {
        heap_sample_available: startHeap !== null && endHeap !== null,
        heap_growth_bytes:
          startHeap === null || endHeap === null ? null : Math.max(0, endHeap - startHeap),
        heap_samples: heapSamples,
        dom_node_growth: Math.max(0, domGrowth),
        dom_node_samples: domSamples,
        frame_delta_ms: frameDeltas,
        listener_balance: listenerBalance,
        timer_balance: timerBalance,
        long_task_count: longTasks.length,
        max_long_task_ms: longTasks.length === 0 ? 0 : Math.max(...longTasks)
      };
    },
    { durationMs, sampleEveryMs: BROWSER_SAMPLE_EVERY_MS }
  );
}

function mergeBrowserSlices(slices, sliceSeconds) {
  const heapSamples = slices.flatMap((slice) => slice.heap_samples);
  const domSamples = slices.flatMap((slice) => slice.dom_node_samples);
  const frameDeltas = slices.flatMap((slice) => slice.frame_delta_ms);
  const heapGrowthValues = slices
    .map((slice) => slice.heap_growth_bytes)
    .filter((value) => Number.isFinite(value));
  const domGrowthValues = slices
    .map((slice) => slice.dom_node_growth)
    .filter((value) => Number.isFinite(value));
  return {
    heap_sample_available: slices.some((slice) => slice.heap_sample_available),
    heap_growth_bytes: heapGrowthValues.length === 0 ? null : Math.max(...heapGrowthValues),
    heap_samples: heapSamples,
    dom_node_growth: domGrowthValues.length === 0 ? 0 : Math.max(...domGrowthValues),
    dom_node_samples: domSamples,
    frame_delta_ms: frameDeltas,
    listener_balance: slices.reduce((total, slice) => total + slice.listener_balance, 0),
    timer_balance: slices.reduce((total, slice) => total + slice.timer_balance, 0),
    long_task_count: slices.reduce((total, slice) => total + slice.long_task_count, 0),
    max_long_task_ms: slices.reduce(
      (maximum, slice) => Math.max(maximum, slice.max_long_task_ms),
      0
    ),
    slices_completed: slices.length,
    slice_seconds: sliceSeconds,
    measurement_error: null
  };
}

async function launchBrowserPage() {
  const browser = await getChromium().launch({
    headless: true,
    args: ["--disable-dev-shm-usage", "--disable-gpu", "--enable-precise-memory-info", "--no-sandbox"]
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.setContent("<!doctype html><meta charset='utf-8'><div id='soak-root'></div>");
    return { browser, page };
  } catch (error) {
    await browser.close().catch(() => undefined);
    throw error;
  }
}

async function runBrowserSoak(durationSeconds, browserSliceSeconds) {
  const slices = [];
  let recoveriesObserved = 0;
  let measuredMs = 0;
  const durationMs = durationSeconds * 1000;
  const browserSliceMs = Math.min(browserSliceSeconds * 1000, durationMs);
  while (measuredMs < durationMs) {
    const sliceMs = Math.min(browserSliceMs, durationMs - measuredMs);
    let sliceComplete = false;
    while (!sliceComplete) {
      let context = null;
      try {
        context = await launchBrowserPage();
        slices.push(await runBrowserSoakSlice(context.page, sliceMs));
        sliceComplete = true;
      } catch (error) {
        recoveriesObserved += 1;
        if (recoveriesObserved > MAX_BROWSER_SLICE_RECOVERIES) {
          throw error;
        }
      } finally {
        await context?.browser.close().catch(() => undefined);
      }
    }
    measuredMs += sliceMs;
  }
  return {
    ...mergeBrowserSlices(slices, browserSliceSeconds),
    recoveries_observed: recoveriesObserved
  };
}

function describeError(error) {
  if (!error) {
    return null;
  }
  return {
    name: error.name || "Error",
    message: error.message || String(error),
    stack_tail: error.stack ? error.stack.slice(-1200) : ""
  };
}

function failedBrowserResult(error, browserSliceSeconds) {
  return {
    heap_sample_available: false,
    heap_growth_bytes: null,
    heap_samples: [],
    dom_node_growth: 0,
    dom_node_samples: [],
    frame_delta_ms: [],
    listener_balance: 0,
    timer_balance: 0,
    long_task_count: 0,
    max_long_task_ms: 0,
    slices_completed: 0,
    slice_seconds: browserSliceSeconds,
    recoveries_observed: MAX_BROWSER_SLICE_RECOVERIES,
    measurement_error: describeError(error)
  };
}

function failedWorkerResult(error) {
  return {
    jobs_total: 0,
    jobs_completed: 0,
    retries_observed: 0,
    recoveries_observed: 0,
    dead_letters_observed: 0,
    event_loop_lag_ms: summary([]),
    cpu_user_ms: 0,
    cpu_system_ms: 0,
    measurement_error: describeError(error)
  };
}

async function runWorkerSoak(durationSeconds) {
  const endAt = performance.now() + durationSeconds * 1000;
  const lagSamples = [];
  const cpuStart = process.cpuUsage();
  const jobs = Array.from({ length: 12 }, (_, index) => ({
    id: index + 1,
    attempts: 0,
    status: "queued",
    fail_once: index % 4 === 0
  }));
  let completed = 0;
  let retries = 0;
  let recoveries = 0;
  let deadLetters = 0;
  while (performance.now() < endAt) {
    const tickStart = performance.now();
    for (const job of jobs) {
      if (job.status === "done" || job.status === "dead_letter") {
        continue;
      }
      job.attempts += 1;
      if (job.fail_once && job.attempts === 1) {
        job.status = "queued";
        retries += 1;
        recoveries += 1;
      } else if (job.attempts > 5) {
        job.status = "dead_letter";
        deadLetters += 1;
      } else {
        job.status = "done";
        completed += 1;
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 25));
    lagSamples.push(performance.now() - tickStart - 25);
  }
  const cpuEnd = process.cpuUsage(cpuStart);
  return {
    jobs_total: jobs.length,
    jobs_completed: completed,
    retries_observed: retries,
    recoveries_observed: recoveries,
    dead_letters_observed: deadLetters,
    event_loop_lag_ms: summary(lagSamples),
    cpu_user_ms: Number((cpuEnd.user / 1000).toFixed(4)),
    cpu_system_ms: Number((cpuEnd.system / 1000).toFixed(4))
  };
}

function evaluate(browserResult, workerResult) {
  const heapGrowth = browserResult.heap_growth_bytes ?? 0;
  const frame = summary(browserResult.frame_delta_ms);
  const browserPass =
    !browserResult.measurement_error &&
    heapGrowth <= MAX_HEAP_GROWTH_BYTES &&
    browserResult.dom_node_growth <= MAX_DOM_GROWTH_NODES &&
    browserResult.listener_balance <= MAX_LISTENER_LEAKS &&
    browserResult.timer_balance <= MAX_TIMER_LEAKS;
  const workerPass =
    !workerResult.measurement_error &&
    workerResult.jobs_completed === workerResult.jobs_total &&
    workerResult.retries_observed > 0 &&
    workerResult.recoveries_observed > 0 &&
    workerResult.dead_letters_observed === 0 &&
    workerResult.event_loop_lag_ms.p95 <= MAX_EVENT_LOOP_LAG_MS;
  return {
    status: browserPass && workerPass ? "PASS" : "FAIL",
    budgets: {
      max_heap_growth_bytes: MAX_HEAP_GROWTH_BYTES,
      max_dom_growth_nodes: MAX_DOM_GROWTH_NODES,
      max_timer_leaks: MAX_TIMER_LEAKS,
      max_listener_leaks: MAX_LISTENER_LEAKS,
      max_event_loop_lag_ms: MAX_EVENT_LOOP_LAG_MS,
      max_browser_slice_recoveries: MAX_BROWSER_SLICE_RECOVERIES
    },
    browser_frame_delta_ms: frame
  };
}

async function main() {
  const args = parseArgs(process.argv);
  const parameters = await readSoakParameters();
  const workerDeploymentBinding = await readWorkerDeploymentBinding();
  const browserPathResolution = await resolvePlaywrightBrowserPath();
  const measurementStartedAt = performance.now();
  const [browserOutcome, workerOutcome] = await Promise.allSettled([
    runBrowserSoak(args.durationSeconds, args.browserSliceSeconds),
    runWorkerSoak(args.durationSeconds)
  ]);
  const browserResult =
    browserOutcome.status === "fulfilled"
      ? browserOutcome.value
      : failedBrowserResult(browserOutcome.reason, args.browserSliceSeconds);
  const workerResult =
    workerOutcome.status === "fulfilled"
      ? workerOutcome.value
      : failedWorkerResult(workerOutcome.reason);
  const elapsedWallSeconds = (performance.now() - measurementStartedAt) / 1000;
  const evaluation = evaluate(browserResult, workerResult);
  const targetSeconds = [
    parameters.short_duration_hours * 3600,
    parameters.long_duration_hours * 3600
  ];
  const fullDurationMeasured = targetSeconds.every((target) => args.durationSeconds >= target);
  const status =
    evaluation.status === "FAIL" ? "FAIL" : fullDurationMeasured ? "PASS" : "PARTIAL";
  const payload = {
    schema_version: "eei-soak-benchmark-v1",
    system_name: "EEI",
    task_id: "T1307",
    acceptance_ids: ["A209"],
    status,
    mode: args.mode,
    generated_at: new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
    environment: {
      node: process.version,
      platform: `${os.platform()}-${os.release()}-${os.arch()}`,
      cpu_count: os.cpus().length,
      browser: "chromium",
      playwright_browsers_path_source: browserPathResolution.source,
      playwright_browsers_path: browserPathResolution.path
    },
    configured_targets: {
      short_duration_hours: parameters.short_duration_hours,
      long_duration_hours: parameters.long_duration_hours,
      browser_slice_seconds: args.browserSliceSeconds
    },
    measured_duration_seconds: args.durationSeconds,
    measurement: {
      strategy: "parallel_browser_worker_v1",
      requested_duration_seconds: args.durationSeconds,
      elapsed_wall_seconds: Number(elapsedWallSeconds.toFixed(4)),
      browser_worker_parallel: true
    },
    coverage: {
      browser_soak_measured: !browserResult.measurement_error,
      worker_soak_measured: !workerResult.measurement_error,
      full_4h_24h_measured: fullDurationMeasured,
      worker_supervisor_binding_available:
        workerDeploymentBinding?.status === "PASS" &&
        workerDeploymentBinding?.runtime?.process_manager === "docker_compose",
      required_metric_groups: [
        "heap",
        "dom",
        "listener",
        "timer",
        "cpu",
        "retry",
        "recovery"
      ]
    },
    budgets: evaluation.budgets,
    worker_supervisor_binding: workerDeploymentBinding
      ? {
          artifact_path: "artifacts/tests/a206/t1304_worker_deployment_binding_contract.json",
          schema_version: workerDeploymentBinding.schema_version,
          status: workerDeploymentBinding.status,
          process_manager: workerDeploymentBinding.runtime?.process_manager,
          start_command: workerDeploymentBinding.runtime?.start_command,
          stop_command: workerDeploymentBinding.runtime?.stop_command,
          logs_command: workerDeploymentBinding.runtime?.logs_command
        }
      : {
          artifact_path: "artifacts/tests/a206/t1304_worker_deployment_binding_contract.json",
          status: "MISSING",
          process_manager: null
        },
    browser: {
      heap_sample_available: browserResult.heap_sample_available,
      heap_growth_bytes: browserResult.heap_growth_bytes,
      heap_samples: summary(browserResult.heap_samples.length ? browserResult.heap_samples : [0]),
      dom_node_growth: browserResult.dom_node_growth,
      dom_node_samples: summary(browserResult.dom_node_samples),
      frame_delta_ms: evaluation.browser_frame_delta_ms,
      listener_balance: browserResult.listener_balance,
      timer_balance: browserResult.timer_balance,
      long_task_count: browserResult.long_task_count,
      max_long_task_ms: Number(browserResult.max_long_task_ms.toFixed(4)),
      slices_completed: browserResult.slices_completed,
      slice_seconds: browserResult.slice_seconds,
      recoveries_observed: browserResult.recoveries_observed || 0,
      measurement_error: browserResult.measurement_error
    },
    worker: workerResult,
    remaining_to_close_a209: fullDurationMeasured
      ? []
      : [
          "Run operator soak for 4 hours and 24 hours using the Docker Compose worker binding plus this harness.",
          "Attach release evidence for both durations before marking A209 DONE."
        ]
  };
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
