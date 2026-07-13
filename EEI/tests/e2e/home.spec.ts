import { expect, test, type Locator } from "@playwright/test";

async function boxFor(locator: Locator) {
  const box = await locator.boundingBox();
  expect(box).not.toBeNull();
  return box!;
}

function centerX(box: { x: number; width: number }) {
  return box.x + box.width / 2;
}

function centerY(box: { y: number; height: number }) {
  return box.y + box.height / 2;
}

test("renders the watchlist-first EEI workspace", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("main")).toBeVisible();
  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-workspace-model",
    "recursive-enterprise-map"
  );
  await expect(page.getByRole("navigation", { name: "主导航" })).toContainText("商业版图");
  await expect(page.getByLabel("系统模块")).toContainText("对象与范围");
  await expect(page.getByRole("img", { name: /NVIDIA synthetic recursive supply-chain graph/ })).toBeVisible();
  await expect(page.getByTestId("fixture-disclosure")).toContainText("Fixture-only data");
  await expect(page.getByText("Live facts: disabled")).toBeVisible();
});

test("shows user-oriented home contract entry points and model freshness", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("home-global-search")).toHaveAttribute(
    "data-endpoint",
    "/v1/entities"
  );
  await expect(page.getByTestId("home-global-search")).toHaveAttribute(
    "data-supported-types",
    "legal_entity,industry,theme,facility"
  );
  await expect(page.getByTestId("global-search-input")).toBeVisible();
  await expect(page.getByTestId("global-search-results")).toContainText("NVIDIA Corporation");
  await expect(page.getByTestId("home-industries")).toContainText("Semiconductors");
  await expect(page.getByTestId("home-industries")).toContainText("AI cloud infrastructure");
  await expect(page.getByTestId("home-watchlist")).toContainText("NVIDIA");
  await expect(page.getByTestId("home-watchlist")).toContainText("unread");
  await expect(page.getByTestId("home-recent-explorations")).toContainText(
    "NVIDIA -> Foundry"
  );
  await expect(page.getByTestId("home-changes")).toContainText("Capital/control signal refreshed");
  await expect(page.getByTestId("home-freshness")).toContainText("synthetic_fixture");
  await expect(page.getByTestId("home-freshness")).toContainText("Attempt none");
  await expect(page.getByTestId("home-freshness")).toContainText("Success none");
  await expect(page.getByTestId("home-freshness")).toContainText("Failure none");
  await expect(page.getByTestId("home-freshness")).toContainText("1 sources");
  await expect(page.getByTestId("home-freshness")).toContainText("3 documents");
  await expect(page.getByTestId("home-model-status")).toContainText("Balanced v2");
  await expect(page.getByTestId("home-model-status")).toContainText("scheduled / 14d");
  await expect(page.getByTestId("home-model-status")).toContainText("2026-07-03");
});

test("A104 hydrates connector and content freshness without conflating dates", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      "eei.productionDataApiBaseUrl.v1",
      "http://eei-a104.test"
    );
  });
  await page.route("http://eei-a104.test/**", async (route) => {
    if (!route.request().url().endsWith("/v1/sources/freshness")) {
      await route.fulfill({ status: 404, contentType: "application/json", body: "{}" });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        schema_version: "source-freshness-v1",
        as_of: "2026-07-13T00:10:00Z",
        summary: {
          status: "degraded",
          source_count: 1,
          available_source_count: 0,
          failed_source_count: 1,
          running_source_count: 0,
          attempt_count: 3,
          success_count: 2,
          failure_count: 1,
          document_count: 2,
          last_attempt_at: "2026-07-13T00:09:00Z",
          last_success_at: "2026-07-13T00:05:00Z",
          last_failure_at: "2026-07-13T00:09:01Z",
          latest_document_date: "2025-02-10T00:00:00Z",
          latest_report_period_end: "2024-12-31"
        },
        sources: [
          {
            source_id: "00000000-0000-4000-8000-000000000104",
            source_code: "sec_edgar_synthetic_fixture",
            source_name: "SEC EDGAR synthetic fixtures",
            source_tier: 5,
            expected_cadence: "fixture-only",
            typical_disclosure_lag: "not-applicable",
            last_verified_at: null,
            record_modes: ["fixture"],
            data_mode: "fixture",
            freshness_status: "failed",
            attempt_count: 3,
            success_count: 2,
            failure_count: 1,
            last_attempt_at: "2026-07-13T00:09:00Z",
            last_attempt_finished_at: "2026-07-13T00:09:01Z",
            last_attempt_status: "failed",
            last_success_at: "2026-07-13T00:05:00Z",
            last_failure_at: "2026-07-13T00:09:01Z",
            last_error_class: "TimeoutError",
            last_error_message: "deterministic A104 browser fixture",
            document_count: 2,
            latest_document_date: "2025-02-10T00:00:00Z",
            latest_report_period_start: "2024-01-01",
            latest_report_period_end: "2024-12-31",
            latest_observed_at: "2025-02-10T00:00:00Z",
            latest_retrieved_at: "2026-07-13T00:05:00Z"
          }
        ],
        semantics: {
          attempt_time_is_document_time: false,
          attempt_time_is_report_period: false,
          document_date_source: "source_documents.document_date",
          report_period_source: "validated_raw_source_snapshot_payload"
        }
      })
    });
  });

  await page.goto("/");
  const freshness = page.getByTestId("home-freshness");
  await expect(freshness).toHaveAttribute("data-sync-mode", "server");
  await expect(freshness).toHaveAttribute(
    "data-endpoint",
    "http://eei-a104.test/v1/sources/freshness"
  );
  await expect(freshness).toHaveAttribute("data-last-attempt-at", "2026-07-13T00:09:00Z");
  await expect(freshness).toHaveAttribute("data-last-success-at", "2026-07-13T00:05:00Z");
  await expect(freshness).toHaveAttribute("data-last-failure-at", "2026-07-13T00:09:01Z");
  await expect(freshness).toHaveAttribute("data-document-date", "2025-02-10T00:00:00Z");
  await expect(freshness).toHaveAttribute("data-report-period-end", "2024-12-31");
  await expect(freshness).toContainText("degraded");
  await expect(freshness).toContainText("sec_edgar_synthetic_fixture");
  await expect(freshness).toContainText("Attempt 2026-07-13T00:09:00Z");
  await expect(freshness).toContainText("Success 2026-07-13T00:05:00Z");
  await expect(freshness).toContainText("Failure 2026-07-13T00:09:01Z");
  await expect(freshness).toContainText("Document 2025-02-10T00:00:00Z");
  await expect(freshness).toContainText("Report 2024-12-31");
});

test("A211 exposes WorkspaceContext routes controls disabled entries and persisted query wiring", async ({
  page
}) => {
  await page.goto("/");

  const context = page.getByTestId("workspace-context-contract");
  await expect(context).toHaveAttribute("data-context-version", "workspace-context-v1");
  await expect(context).toHaveAttribute("data-module-count", "16");
  await expect(context).toHaveAttribute(
    "data-query-keys",
    "subject,selected,lens,zoom,asOf,path"
  );
  await expect(context).toHaveAttribute("data-state-persistence", "url,sessionStorage,localStorage");
  await expect(context).toHaveAttribute("data-workspace-state-storage-key", "eei.workspaceState.v1");
  await expect(context).toHaveAttribute("data-saved-view-storage-key", "eei.savedView.current.v1");
  await expect(context).toHaveAttribute(
    "data-disabled-unfinished",
    "ma_transactions,control_relationships,strategic_signals"
  );
  const serverEndpoints = await context.getAttribute("data-server-endpoints");
  expect(serverEndpoints).toContain("/v1/saved-views");
  expect(serverEndpoints).toContain("/v1/scoring/active-context");
  expect(serverEndpoints).toContain("/v1/scoring/recompute");

  await expect(page.getByTestId("main-nav-business_map")).toHaveAttribute("href", "/");
  await expect(page.getByTestId("main-nav-business_map")).toHaveAttribute(
    "data-control-kind",
    "route"
  );
  await page.getByTestId("main-nav-supply_chain").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-lens",
    "supply_chain"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-last-nav-action",
    "lens:supply_chain:supply_chain"
  );
  await expect(page).toHaveURL(/lens=supply_chain/);

  await page.getByTestId("main-nav-time_evolution").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-last-nav-action",
    "section:time_evolution:timeline-controls"
  );
  await page.getByTestId("main-nav-evidence_center").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-last-nav-action",
    "section:evidence_center:evidence-center"
  );

  await expect(page.getByTestId("main-nav-ma_transactions")).toBeDisabled();
  await expect(page.getByTestId("main-nav-ma_transactions")).toHaveAttribute(
    "data-route-state",
    "planned"
  );
  await expect(page.getByTestId("main-nav-ma_transactions")).toHaveAttribute(
    "data-disabled-reason",
    /Requires reviewed M&A transaction facts/
  );
  await expect(page.getByTestId("main-nav-control_relationships")).toBeDisabled();
  await expect(page.getByTestId("main-nav-strategic_signals")).toBeDisabled();

  await page.getByTestId("main-nav-system_status").click();
  await expect(page).toHaveURL(/\/development-status$/);
});

test("exposes eight company layers and separates structure object types", async ({ page }) => {
  await page.goto("/");

  const layerStrip = page.getByTestId("workspace-layer-strip");
  await expect(layerStrip).toHaveAttribute("data-layer-count", "8");
  await expect(layerStrip).toHaveAttribute(
    "data-required-layers",
    "group_structure,business_segments,supply_chain,capital_network,ma_transactions,control_relationships,policy_environment,strategic_signals"
  );
  for (const layer of [
    "group_structure",
    "business_segments",
    "supply_chain",
    "capital_network",
    "ma_transactions",
    "control_relationships",
    "policy_environment",
    "strategic_signals"
  ]) {
    await expect(page.getByTestId(`workspace-layer-${layer}`)).toBeVisible();
  }
  await page.getByTestId("workspace-layer-business_segments").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-lens",
    "business_segments"
  );

  const structure = page.getByTestId("company-structure-matrix");
  await expect(structure).toHaveAttribute(
    "data-separates",
    "legal_group,business_segment,brand,product,facility"
  );
  await expect(structure).toHaveAttribute("data-commercial-empire-control-claim", "false");
  await expect(structure).toContainText("商业版图不是法律控制声明");
  await expect(page.getByTestId("structure-row-legal_group")).toContainText(
    "NVIDIA Corporation"
  );
  await expect(page.getByTestId("structure-row-business_segment")).toHaveAttribute(
    "data-relationship",
    "segment_of"
  );
  await expect(page.getByTestId("structure-row-brand")).toHaveAttribute(
    "data-scope",
    "missing"
  );
  await expect(page.getByTestId("structure-row-product")).toContainText(
    "AI Accelerator Platform"
  );
  await expect(page.getByTestId("structure-row-facility")).toHaveAttribute(
    "data-scope",
    "adjacent"
  );
  await expect(page.getByTestId("structure-row-facility")).toHaveAttribute(
    "data-control-claim",
    "false"
  );
  await expect(page.getByTestId("structure-row-facility")).toContainText(
    "不表示 NVIDIA 拥有或运营"
  );
});

test("reaches company focus within three actions and keeps home controls keyboard reachable", async ({
  page
}) => {
  await page.goto("/");

  await expect(page.getByTestId("home-global-search")).toHaveAttribute(
    "data-primary-actions-to-focus",
    "2"
  );
  await page.getByTestId("global-search-input").focus();
  await page.getByTestId("global-search-input").fill("tsmc");
  await page.getByTestId("global-search-input").press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");

  await page.getByTestId("home-industry-semiconductors").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");

  await page.getByTestId("home-watchlist-cloud").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Cloud Customer");

  await page.getByTestId("home-recent-equipment").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );

  await page.getByTestId("home-change-policy").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Export Control Context"
  );
});

test("shows watchlist unread changes and restores saved view profile state", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("watchlist-saved-state-cloud")).toContainText("2 unread");
  await expect(page.getByTestId("watchlist-saved-state-cloud")).toContainText("supply_chain");
  await expect(page.getByTestId("watchlist-saved-state-cloud")).toContainText("L2");
  await expect(page.getByTestId("watchlist-saved-state-cloud")).toContainText("Balanced v2");

  await page.getByTestId("lens-capital_transactions").click();
  await page.getByTestId("zoom-L0").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-lens",
    "capital_transactions"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", "L0");

  await page.getByTestId("home-watchlist-cloud").click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Cloud Customer");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-lens",
    "supply_chain"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", "L2");
});

test("exposes the Objects and Scope navigation screen with counts definitions and exports", async ({
  page
}) => {
  await page.goto("/");
  await page.getByTestId("objects-scope-nav-link").click();

  await expect(page).toHaveURL(/\/objects-scope$/);
  await expect(page.getByTestId("objects-scope-screen")).toBeVisible();
  await expect(page.getByTestId("objects-scope-nav-active")).toHaveAttribute("aria-current", "page");
  await expect(page.getByTestId("object-scope-catalog-count")).toHaveText("10");
  await expect(page.getByTestId("object-scope-total-rows")).toHaveText("363");

  await expect(page.getByTestId("object-scope-coverage-relationship_types")).toContainText("52");
  await expect(page.getByTestId("object-scope-coverage-companies")).toContainText("140");
  await expect(page.getByTestId("object-scope-catalog-relationship")).toContainText("关系类型");
  await expect(page.getByTestId("object-scope-definition-relationship")).toContainText(
    "Fifty-two machine-readable relationship types"
  );
  await expect(page.getByTestId("object-scope-catalog-domain-object")).toContainText(
    "领域对象"
  );
  await expect(page.getByTestId("object-scope-export-relationship-json")).toHaveAttribute(
    "href",
    "/v1/catalogs/relationship"
  );
  await expect(page.getByTestId("object-scope-export-relationship-csv")).toHaveAttribute(
    "href",
    "/v1/catalogs/relationship?format=csv"
  );
  await expect(page.locator("article[data-testid^='object-scope-catalog-']")).toHaveCount(10);

  const screenBox = await boxFor(page.getByTestId("objects-scope-screen"));
  const summaryBox = await boxFor(page.getByLabel("覆盖摘要"));
  const matrixBox = await boxFor(page.getByLabel("目录定义与导出"));
  expect(summaryBox.width / screenBox.width).toBeGreaterThan(0.55);
  expect(matrixBox.height).toBeGreaterThan(400);
});

test("measures visual-first relationship layout and critical relationship layers", async ({ page }) => {
  await page.goto("/");

  const canvasBox = await boxFor(page.getByTestId("visual-canvas"));
  const mapBox = await boxFor(page.getByTestId("ecosystem-map-surface"));
  const visualCoverage = (mapBox.width * mapBox.height) / (canvasBox.width * canvasBox.height);
  expect(visualCoverage).toBeGreaterThanOrEqual(0.6);

  const focus = await boxFor(page.getByTestId("graph-node-nvidia"));
  const materials = await boxFor(page.getByTestId("graph-node-materials"));
  const equipment = await boxFor(page.getByTestId("graph-node-equipment"));
  const foundry = await boxFor(page.getByTestId("graph-node-foundry"));
  const systems = await boxFor(page.getByTestId("graph-node-systems"));
  const cloud = await boxFor(page.getByTestId("graph-node-cloud"));
  const capital = await boxFor(page.getByTestId("graph-node-capital"));
  const policy = await boxFor(page.getByTestId("graph-node-policy"));

  expect(centerX(materials)).toBeLessThan(centerX(focus));
  expect(centerX(equipment)).toBeLessThan(centerX(focus));
  expect(centerX(foundry)).toBeLessThan(centerX(focus));
  expect(centerX(systems)).toBeGreaterThan(centerX(focus));
  expect(centerX(cloud)).toBeGreaterThan(centerX(focus));
  expect(centerY(capital)).toBeLessThan(centerY(focus));
  expect(centerY(policy)).toBeGreaterThan(centerY(focus));

  await expect(page.getByTestId("graph-node-business")).toBeVisible();
  await expect(page.getByTestId("edge-label-nvidia-business")).toContainText("operates business segment");
  await expect(page.getByTestId("edge-label-capital-nvidia")).toContainText("capital and control signal for");
  await expect(page.getByTestId("edge-label-policy-nvidia")).toContainText("policy risk constrains");
  await expect(page.locator(".edge[marker-end='url(#arrow)']")).toHaveCount(11);
});

test("selects node context without changing subject and supports primary inspector actions", async ({
  page
}) => {
  await page.goto("/");

  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");
  await page.getByTestId("graph-node-foundry").click();
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic Advanced Foundry");
  await expect(page.getByTestId("selected-node-card")).toContainText("SC-06 Manufacturing");
  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");

  const actions = page.getByLabel("主体操作");
  await expect(actions.getByTestId("primary-set-center")).toContainText(
    "以 Synthetic Advanced Foundry 为中心"
  );
  for (const action of [
    "展开上游",
    "展开下游",
    "固定节点",
    "加入比较",
    "加入关注",
    "查看路径",
    "打开证据"
  ]) {
    await expect(actions.getByRole("button", { name: action })).toBeVisible();
  }
  await actions.getByTestId("node-action-pin").click();
  await expect(page.getByTestId("pinned-node-list")).toContainText("Synthetic Advanced Foundry");
  await actions.getByTestId("node-action-compare").click();
  await expect(page.getByTestId("comparison-node-list")).toContainText(
    "Synthetic Advanced Foundry"
  );
  await actions.getByTestId("node-action-watchlist").click();
  await expect(page.getByTestId("watchlist-node-list")).toContainText(
    "Synthetic Advanced Foundry"
  );
  await actions.getByTestId("node-action-path").click();
  await expect(page.getByTestId("node-action-status")).toHaveText("path:foundry");
  await actions.getByTestId("node-action-evidence").click();
  await expect(page.getByTestId("node-action-status")).toHaveText("evidence:foundry");

  await actions.getByTestId("primary-set-center").click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
});

test("switches lenses on the persistent canvas while preserving exploration state", async ({
  page
}) => {
  await page.goto("/");

  await page.getByTestId("graph-node-foundry").click();
  await page.getByTestId("node-action-pin").click();
  await page.getByTestId("node-action-compare").click();
  await page.getByTestId("zoom-L2").click();

  const beforeViewport = await page.getByTestId("workspace-shell").getAttribute("data-viewport-anchor");
  const beforePathLength = await page.getByTestId("workspace-shell").getAttribute("data-path-length");

  await page.getByTestId("lens-capital_transactions").click();

  await expect(page).toHaveURL(/lens=capital_transactions/);
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-workspace-model",
    "recursive-enterprise-map"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-lens",
    "capital_transactions"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", "L2");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-viewport-anchor",
    beforeViewport ?? ""
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-path-length",
    beforePathLength ?? ""
  );
  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic Advanced Foundry");
  await expect(page.getByTestId("edge-group-capital-nvidia")).toHaveAttribute(
    "data-lens-state",
    "active"
  );
  await expect(page.getByTestId("edge-group-materials-foundry")).toHaveAttribute(
    "data-lens-state",
    "faded"
  );
  await page.getByTestId("zoom-L3").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", "L3");
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic Advanced Foundry");
  await expect(page.getByTestId("pinned-node-list")).toContainText("Synthetic Advanced Foundry");
  await expect(page.getByTestId("comparison-node-list")).toContainText(
    "Synthetic Advanced Foundry"
  );
});

test("offers a filterable graph table alternative and explicit visual semantics", async ({
  page
}) => {
  await page.goto("/");

  await expect(page.getByTestId("visual-semantics-notice")).toHaveAttribute(
    "data-control-semantics",
    "layout-position-not-control"
  );
  await expect(page.getByTestId("visual-semantics-notice")).toHaveAttribute(
    "data-color-independent-encoding",
    "labels,arrows,stages,roles,evidence"
  );
  await expect(page.locator(".edge[marker-end='url(#arrow)']").first()).toBeVisible();
  await expect(page.getByTestId("edge-label-materials-foundry")).toContainText(
    "material provider to"
  );

  const table = page.getByTestId("graph-table-alternative");
  await expect(table).toBeVisible();
  await expect(table).toHaveAttribute("data-accessibility-equivalent", "graph-relationships");
  await expect(table).toHaveAttribute(
    "data-equivalent-fields",
    "direction,type,evidence_status,observed_at"
  );
  await expect(table).toHaveAttribute(
    "data-color-independent-encoding",
    "labels,arrows,stages,roles,evidence"
  );
  await expect(page.getByTestId("graph-table-row-materials-foundry")).toHaveAttribute(
    "data-direction",
    "materials->foundry"
  );
  await expect(page.getByTestId("graph-table-row-materials-foundry")).toHaveAttribute(
    "data-relationship-type",
    "supply_chain"
  );
  await expect(page.getByTestId("graph-table-row-materials-foundry")).toHaveAttribute(
    "data-evidence-status",
    "fixture-evidence"
  );
  await expect(page.getByTestId("graph-table-row-materials-foundry")).toHaveAttribute(
    "data-observed-at",
    "2026-06-19"
  );
  await expect(page.getByTestId("graph-table-row-materials-foundry")).toContainText(
    "fixture evidence"
  );
  await page.getByTestId("graph-table-filter").selectOption("supply_chain");
  await expect(table.locator("tbody tr").first()).toHaveAttribute("data-lens", "supply_chain");
  expect(await table.locator("tbody tr:not([data-lens='supply_chain'])").count()).toBe(0);
  await expect(table).toContainText("wafer foundry for");
});

test("keeps graph-equivalent controls keyboard reachable with visible focus and target size", async ({
  page
}) => {
  await page.goto("/");

  const foundryNode = page.getByTestId("graph-node-foundry");
  await foundryNode.focus();
  await expect(foundryNode).toBeFocused();
  const foundryBox = await boxFor(foundryNode);
  expect(foundryBox.width).toBeGreaterThanOrEqual(24);
  expect(foundryBox.height).toBeGreaterThanOrEqual(24);
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic Advanced Foundry");

  const primaryAction = page.getByTestId("primary-set-center");
  await primaryAction.focus();
  await expect(primaryAction).toBeFocused();
  const primaryBox = await boxFor(primaryAction);
  expect(primaryBox.width).toBeGreaterThanOrEqual(24);
  expect(primaryBox.height).toBeGreaterThanOrEqual(24);
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");

  const tableFilter = page.getByTestId("graph-table-filter");
  await tableFilter.focus();
  await expect(tableFilter).toBeFocused();
  const filterBox = await boxFor(tableFilter);
  expect(filterBox.width).toBeGreaterThanOrEqual(24);
  expect(filterBox.height).toBeGreaterThanOrEqual(24);
});

test("implements semantic zoom levels and grouped dense-node list view", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("semantic-zoom-controls")).toHaveAttribute(
    "data-zoom-contract",
    "L0,L1,L2,L3"
  );

  for (const zoom of ["L0", "L1", "L2", "L3"]) {
    await page.getByTestId(`zoom-${zoom}`).click();
    await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", zoom);
  }

  await expect(page.getByText("fixture evidence").first()).toBeVisible();
  await expect(page.getByText("current focus").first()).toBeVisible();

  await page.getByTestId("zoom-L0").click();
  const groupNode = page.getByTestId("graph-node-systemMakersGroup");
  await expect(groupNode).toBeVisible();
  await expect(groupNode).toHaveAttribute("data-node-kind", "aggregate");
  await expect(groupNode).toHaveAttribute("data-aggregate-count", "8");

  await groupNode.click();
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic System Makers Group");
  await expect(page.getByTestId("primary-set-center")).toBeDisabled();
  await page.getByTestId("open-group-list").click();
  await expect(page.getByTestId("group-list")).toBeVisible();
  await expect(page.getByTestId("group-list").locator("li")).toHaveCount(8);
});

test("keeps the default graph bounded below the first-screen hairball budget", async ({
  page
}) => {
  await page.goto("/");

  const renderedNodeCount = await page.locator("[data-testid^='graph-node-']").count();
  const renderedEdgeCount = await page.locator(".edge").count();

  expect(renderedNodeCount).toBeLessThanOrEqual(42);
  expect(renderedEdgeCount).toBeLessThanOrEqual(40);
  await expect(page.getByTestId("budget-state")).toContainText("max 40 first-screen edges");
  const inclusionPolicy = page.getByTestId("inclusion-truncation-explanation");
  await expect(inclusionPolicy).toBeVisible();
  await expect(inclusionPolicy).toHaveAttribute(
    "data-sort-keys",
    "active-lens,evidence,confidence,observed_at,id"
  );
  await expect(inclusionPolicy).toHaveAttribute(
    "data-truncation-contract",
    "edge_budget,node_budget,returned_counts,continuation"
  );
  await expect(inclusionPolicy).toHaveAttribute(
    "data-continuation-endpoint",
    "/v1/explore/expand"
  );
  await expect(inclusionPolicy).toContainText(
    "Active lens, evidence-bearing edges, confidence, observed time, stable id"
  );
  await expect(inclusionPolicy).toContainText("edge_budget and node_budget");
  await expect(inclusionPolicy).toContainText("/v1/explore/expand");
});

test("preserves directional grammar during reroot and keeps a nonblank fallback state", async ({
  page
}) => {
  await page.goto("/");

  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-layout-grammar",
    "upstream-left focus-center downstream-right capital-top policy-bottom"
  );

  await page.getByRole("button", { name: "以 Synthetic Advanced Foundry 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");

  const focus = await boxFor(page.getByTestId("graph-node-foundry"));
  const materials = await boxFor(page.getByTestId("graph-node-materials"));
  const equipment = await boxFor(page.getByTestId("graph-node-equipment"));
  const nvidia = await boxFor(page.getByTestId("graph-node-nvidia"));

  expect(centerX(materials)).toBeLessThan(centerX(focus));
  expect(centerX(equipment)).toBeLessThan(centerX(focus));
  expect(centerX(nvidia)).toBeGreaterThan(centerX(focus));
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-layout-grammar",
    "upstream-left focus-center downstream-right capital-top policy-bottom"
  );

  await page.evaluate(() => {
    window.dispatchEvent(new CustomEvent("eei:request-center", { detail: "missing-subject" }));
  });
  await expect(page.getByTestId("transition-fallback")).toBeVisible();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
  expect(await page.locator("[data-testid^='graph-node-']").count()).toBeGreaterThan(0);
});

test("uses keyboard or touch-style single actions for primary navigation", async ({ page }) => {
  await page.goto("/");

  const equipment = page.getByTestId("graph-node-equipment");
  await equipment.focus();
  await equipment.press("Enter");
  await expect(page.getByTestId("selected-node-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");

  await page.getByTestId("primary-set-center").click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
});

test("marks synthetic fixtures and completes NVIDIA recursive supply-chain reroot path", async ({
  page
}) => {
  await page.goto("/");

  const stageCoverage = page.getByLabel("供应链阶段覆盖");
  for (const stage of [
    "SC-02 Materials",
    "SC-04 Equipment",
    "SC-05 Design / IP",
    "SC-06 Manufacturing",
    "SC-09 System",
    "SC-10 Data center / Energy",
    "SC-12 Customer"
  ]) {
    await expect(stageCoverage.getByText(stage)).toBeVisible();
  }

  await expect(page.getByText("Synthetic fixture").first()).toBeVisible();
  await expect(page.getByText("Synthetic fixture for interaction and data-model tests.").first()).toBeVisible();

  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-workspace-model",
    "recursive-enterprise-map"
  );

  await page.getByRole("button", { name: "以 Synthetic Advanced Foundry 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
  await expect(page.getByTestId("visual-canvas")).toBeVisible();

  await page.getByRole("button", { name: "以 Synthetic Lithography Equipment Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
  await expect(page.getByTestId("visual-canvas")).toBeVisible();

  await page.getByRole("button", { name: "以 Synthetic Specialty Materials Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Specialty Materials Co."
  );
  await expect(page.getByTestId("visual-canvas")).toBeVisible();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-workspace-model",
    "recursive-enterprise-map"
  );

  const breadcrumb = page.getByTestId("reroot-breadcrumb");
  await expect(breadcrumb).toContainText("NVIDIA");
  await expect(breadcrumb).toContainText("Synthetic Advanced Foundry");
  await expect(breadcrumb).toContainText("Synthetic Lithography Equipment Co.");
  await expect(breadcrumb).toContainText("Synthetic Specialty Materials Co.");
  await expect(page.getByText("Live facts: disabled")).toBeVisible();
});
