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
  for (const action of ["展开上游", "展开下游", "加入关注", "查看路径", "打开证据"]) {
    await expect(actions.getByRole("button", { name: action })).toBeVisible();
  }

  await actions.getByTestId("primary-set-center").click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
});

test("switches lenses on the persistent canvas while preserving exploration state", async ({
  page
}) => {
  await page.goto("/");

  await page.getByTestId("graph-node-foundry").click();
  await page.getByTestId("zoom-L2").click();

  const beforeUrl = page.url();
  const beforeViewport = await page.getByTestId("workspace-shell").getAttribute("data-viewport-anchor");
  const beforePathLength = await page.getByTestId("workspace-shell").getAttribute("data-path-length");

  await page.getByTestId("lens-capital_transactions").click();

  await expect(page).toHaveURL(beforeUrl);
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
  await expect(page.getByTestId("transition-loading")).toBeVisible();
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
  await expect(page.getByTestId("transition-loading")).toBeVisible();
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
