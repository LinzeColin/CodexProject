#!/usr/bin/env node
import { createRequire } from "node:module";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";


const require = createRequire(import.meta.url);
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, index, values) => {
  if (value.startsWith("--")) pairs.push([value.slice(2), values[index + 1]]);
  return pairs;
}, []));
const baseUrl = String(args["base-url"] || "").replace(/\/$/, "");
const outputDir = path.resolve(String(args["output-dir"] || ""));
const rawTrace = path.resolve(String(args["raw-trace"] || ""));
const chromePath = path.resolve(String(args.chrome || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"));
const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
if (!baseUrl || !outputDir || !rawTrace || !moduleDir) {
  throw new Error("base URL, output directory, raw trace and cached Playwright module are required");
}
const { chromium } = require(path.join(moduleDir, "playwright"));


function browserArgs() {
  return [
    "--disable-background-networking", "--disable-component-update", "--disable-default-apps",
    "--disable-domain-reliability", "--disable-extensions",
    "--disable-features=OptimizationHints,MediaRouter,ServiceWorker", "--disable-sync",
    "--metrics-recording-only", "--no-first-run", "--no-default-browser-check",
  ];
}


function safeAxNode(node) {
  return {
    ignored: Boolean(node.ignored),
    role: String(node.role?.value || ""),
    name: String(node.name?.value || ""),
    description: String(node.description?.value || ""),
  };
}


await mkdir(outputDir, { recursive: true });
const diagnostics = {
  consoleErrors: [], pageErrors: [], unexpectedHttpErrors: [], blockedExternal: [],
  requestedOrigins: new Set(),
};
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: browserArgs() });
let tracingStarted = false;
try {
  const context = await browser.newContext({
    locale: "en-AU",
    serviceWorkers: "block",
    viewport: { width: 1440, height: 1000 },
  });
  const allowedOrigin = new URL(baseUrl).origin;
  await context.route("**/*", async (route) => {
    const requestUrl = route.request().url();
    const parsed = new URL(requestUrl);
    if (["data:", "blob:", "about:"].includes(parsed.protocol) || parsed.origin === allowedOrigin) {
      if (parsed.origin === allowedOrigin) diagnostics.requestedOrigins.add(parsed.origin);
      await route.continue();
      return;
    }
    diagnostics.blockedExternal.push({ protocol: parsed.protocol, host: parsed.host });
    await route.abort("blockedbyclient");
  });
  await context.tracing.start({ screenshots: false, snapshots: true, sources: false });
  tracingStarted = true;
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") diagnostics.consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(String(error?.message || error)));
  page.on("response", (response) => {
    if (response.status() >= 400 && !response.url().endsWith("/application-route")) {
      diagnostics.unexpectedHttpErrors.push({ status: response.status(), path: new URL(response.url()).pathname });
    }
  });

  const mainResponse = await page.goto(`${baseUrl}/`, { waitUntil: "networkidle" });
  const main = await page.evaluate(() => {
    const destinationClass = (href) => href.startsWith("#") ? "fragment" : "external-public";
    return {
      title: document.title,
      language: document.documentElement.lang,
      surface: document.body.dataset.pfiPublicSurface || "",
      h1: document.querySelector("h1")?.textContent?.replace(/\s+/g, " ").trim() || "",
      headingCount: document.querySelectorAll("h1,h2,h3").length,
      scriptCount: document.scripts.length,
      forbiddenInteractiveElementCount: document.querySelectorAll("button,form,input,select,textarea").length,
      applicationMarkerCount: document.querySelectorAll("[data-workspace],[data-primary-entry],.app-shell").length,
      anchorCount: document.querySelectorAll("a").length,
      anchors: [...document.querySelectorAll("a")].map((anchor) => ({
        label: anchor.textContent?.replace(/\s+/g, " ").trim() || "",
        destinationClass: destinationClass(anchor.getAttribute("href") || ""),
      })),
      containsPrivateMarker: /\/Users\/|PRIVATE_USER|PRIVATE_DERIVED|pfi_context\.v1|net_worth_state/i.test(document.documentElement.outerHTML),
      horizontalOverflowPx: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
    };
  });
  await page.screenshot({ path: path.join(outputDir, "public_boundary.png"), fullPage: true });

  const manifest = await page.evaluate(async () => {
    const response = await fetch("/public-surface.json", { cache: "no-store" });
    return { status: response.status, payload: await response.json() };
  });
  const cdp = await context.newCDPSession(page);
  await cdp.send("Accessibility.enable");
  const rawAx = await cdp.send("Accessibility.getFullAXTree");
  const axNodes = rawAx.nodes.filter((node) => !node.ignored).map(safeAxNode);
  const accessibility = {
    schema: "PFIV025Stage11PublicBoundaryAccessibilityTreeV1",
    status: axNodes.length > 0 && axNodes.some((node) => node.role === "heading" && node.name.includes("description of PFI")) ? "pass" : "fail",
    source: "Accessibility.getFullAXTree",
    nodeCount: axNodes.length,
    nodes: axNodes,
    containsPrivateValues: false,
    containsAbsolutePaths: false,
  };
  await writeFile(path.join(outputDir, "accessibility_tree.json"), `${JSON.stringify(accessibility, null, 2)}\n`, "utf8");

  const mainConsoleErrorCount = diagnostics.consoleErrors.length;
  const notFoundResponse = await page.goto(`${baseUrl}/application-route`, { waitUntil: "networkidle" });
  const notFound = await page.evaluate(() => ({
    title: document.title,
    h1: document.querySelector("h1")?.textContent?.replace(/\s+/g, " ").trim() || "",
    scriptCount: document.scripts.length,
    applicationMarkerCount: document.querySelectorAll("[data-workspace],[data-primary-entry],.app-shell").length,
  }));

  const manifestPayload = manifest.payload;
  const checks = {
    main_http_200: mainResponse?.status() === 200,
    static_surface_marker: main.surface === "static-boundary-notice",
    public_h1_present: main.h1.includes("description of PFI"),
    no_scripts: main.scriptCount === 0 && notFound.scriptCount === 0,
    no_form_controls: main.forbiddenInteractiveElementCount === 0,
    no_application_markers: main.applicationMarkerCount === 0 && notFound.applicationMarkerCount === 0,
    no_private_markers: main.containsPrivateMarker === false,
    no_horizontal_overflow: main.horizontalOverflowPx === 0,
    manifest_http_200: manifest.status === 200,
    manifest_static_boundary: manifestPayload.surface_type === "static_boundary_notice",
    manifest_no_active_ui: manifestPayload.active_ui === false,
    manifest_no_runtime: manifestPayload.worker_runtime_enabled === false && manifestPayload.local_runtime_connection === false,
    manifest_no_context: manifestPayload.pfi_context_export_exposed === false,
    manifest_no_data_sources: Array.isArray(manifestPayload.data_sources) && manifestPayload.data_sources.length === 0,
    unknown_route_http_404: notFoundResponse?.status() === 404,
    unknown_route_is_boundary_404: notFound.h1 === "There is no application route here.",
    accessibility_tree_pass: accessibility.status === "pass",
    main_console_errors_zero: mainConsoleErrorCount === 0,
    intentional_404_console_only: diagnostics.consoleErrors.slice(mainConsoleErrorCount).every(
      (message) => message.includes("Failed to load resource") && message.includes("404"),
    ),
    page_errors_zero: diagnostics.pageErrors.length === 0,
    unexpected_http_errors_zero: diagnostics.unexpectedHttpErrors.length === 0,
    blocked_external_requests_zero: diagnostics.blockedExternal.length === 0,
    loopback_origin_only: diagnostics.requestedOrigins.size === 1 && diagnostics.requestedOrigins.has(allowedOrigin),
  };
  const payload = {
    schema: "PFIV025Stage11PublicBoundaryBrowserValidationV1",
    status: Object.values(checks).every(Boolean) ? "pass" : "fail",
    checkCount: Object.keys(checks).length,
    checks,
    main,
    manifest: {
      status: manifest.status,
      surfaceType: manifestPayload.surface_type,
      activeUi: manifestPayload.active_ui,
      workerRuntimeEnabled: manifestPayload.worker_runtime_enabled,
      localRuntimeConnection: manifestPayload.local_runtime_connection,
      contextExportExposed: manifestPayload.pfi_context_export_exposed,
      dataSourceCount: manifestPayload.data_sources?.length ?? -1,
    },
    notFound: { status: notFoundResponse?.status() ?? 0, ...notFound },
    diagnostics: {
      consoleErrors: diagnostics.consoleErrors,
      pageErrors: diagnostics.pageErrors,
      unexpectedHttpErrors: diagnostics.unexpectedHttpErrors,
      blockedExternal: diagnostics.blockedExternal,
      requestedOriginCount: diagnostics.requestedOrigins.size,
    },
    loopbackOnly: true,
    externalNetworkCalls: 0,
    containsPrivateValues: false,
    containsAbsolutePaths: false,
    finderUsed: false,
    launchServicesUsed: false,
    guiFileOperationsUsed: false,
  };
  await writeFile(path.join(outputDir, "browser_validation.json"), `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  await writeFile(path.join(outputDir, "dom_snapshot.json"), `${JSON.stringify({
    schema: "PFIV025Stage11PublicBoundaryDOMSnapshotV1",
    status: payload.status,
    main,
    notFound: payload.notFound,
    containsPrivateValues: false,
    containsAbsolutePaths: false,
  }, null, 2)}\n`, "utf8");
  await context.tracing.stop({ path: rawTrace });
  tracingStarted = false;
  process.stdout.write(`${JSON.stringify({ status: payload.status, checkCount: payload.checkCount })}\n`);
  if (payload.status !== "pass") process.exitCode = 2;
} finally {
  if (tracingStarted) {
    try { await browser.contexts()[0]?.tracing.stop({ path: rawTrace }); } catch {}
  }
  await browser.close();
}
