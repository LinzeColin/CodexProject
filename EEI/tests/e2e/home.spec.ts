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
  await expect(page.getByRole("img", { name: /NVIDIA synthetic recursive supply-chain graph/ })).toBeVisible();
  await expect(page.getByTestId("fixture-disclosure")).toContainText("Fixture-only data");
  await expect(page.getByText("Live facts: disabled")).toBeVisible();
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
