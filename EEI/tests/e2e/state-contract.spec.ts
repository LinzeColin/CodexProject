import { expect, test, type Locator, type Page } from "@playwright/test";

const expectedContext = {
  modelVersion: "business-empire-model-v2",
  profileVersion: "balanced-v2@2",
  dataSnapshot: "fixture-v1",
  scoreSnapshot: "score-fixture-v1"
};

async function expectActiveContext(target: Locator) {
  await expect(target).toHaveAttribute("data-active-model-version", expectedContext.modelVersion);
  await expect(target).toHaveAttribute("data-active-profile-version", expectedContext.profileVersion);
  await expect(target).toHaveAttribute("data-active-data-snapshot", expectedContext.dataSnapshot);
  await expect(target).toHaveAttribute("data-active-score-snapshot", expectedContext.scoreSnapshot);
}

async function expectCloudState(page: Page) {
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Cloud Customer");
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic AI Data Center Campus");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-active-lens", "supply_chain");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", "L2");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-active-time", "2026-06-12");
}

test("stores subject selected node lens time filters and zoom in URL session and reload state", async ({
  page
}) => {
  await page.goto(
    "/?subject=cloud&selected=datacenter&lens=supply_chain&zoom=L2&asOf=2026-06-12&path=nvidia.cloud"
  );

  await expectCloudState(page);
  await expect(page).toHaveURL(/subject=cloud/);
  await expect(page).toHaveURL(/selected=datacenter/);
  await expect(page).toHaveURL(/filters=supply_chain/);
  await expect(page).toHaveURL(/path=nvidia\.cloud/);
  await expect(page.getByTestId("timeline-controls")).toHaveAttribute(
    "data-active-as-of",
    "2026-06-12"
  );

  const sessionState = await page.evaluate(() =>
    JSON.parse(window.sessionStorage.getItem("eei.workspaceState.v1") ?? "{}")
  );
  expect(sessionState).toMatchObject({
    focusKey: "cloud",
    selectedKey: "datacenter",
    activeLens: "supply_chain",
    semanticZoom: "L2",
    asOf: "2026-06-12"
  });

  await page.reload();
  await expectCloudState(page);
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-path-length", "2");
});

test("restores identical subject state through browser back app back and breadcrumb", async ({
  page
}) => {
  await page.goto("/");

  await page.getByRole("button", { name: "以 Synthetic Advanced Foundry 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
  await page.getByRole("button", { name: "以 Synthetic Lithography Equipment Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );

  await page.goBack();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");

  await page.getByRole("button", { name: "以 Synthetic Lithography Equipment Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
  await page.getByTestId("app-back").click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");

  await page.getByRole("button", { name: "以 Synthetic Lithography Equipment Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
  await page.getByTestId("breadcrumb-subject-nvidia-0").click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-path-length", "1");
});

test("saves versioned views restores deterministically and shows as-of change overlays", async ({
  page
}) => {
  await page.goto(
    "/?subject=cloud&selected=datacenter&lens=supply_chain&zoom=L2&asOf=2026-06-12&path=nvidia.cloud"
  );

  await expectCloudState(page);
  await expect(page.getByTestId("change-overlay")).toHaveAttribute(
    "data-timeline-mode",
    "as-of-snapshot"
  );
  await expect(page.getByTestId("change-overlay")).toContainText("As of 2026-06-12");
  await expect(page.getByTestId("change-overlay")).toContainText("not real-time");

  await page.getByTestId("save-current-view").click();
  await expect(page.getByTestId("saved-view-status")).toHaveText("saved");
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-saved-view-version",
    "saved-view-v1"
  );
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-saved-view-id",
    "sv-cloud-supply_chain-L2-2026-06-12"
  );

  await page.getByTestId("timeline-2026-06-01").click();
  await page.getByTestId("lens-policy_risk").click();
  await page.getByRole("button", { name: "回到 NVIDIA" }).click();
  await page.reload();

  await page.getByTestId("restore-saved-view").click();
  await expectCloudState(page);
  await expect(page.getByTestId("saved-view-status")).toHaveText("restored");
  await expect(page.getByTestId("saved-view-contract")).toContainText("Synthetic Cloud Customer");
  await expect(page.getByTestId("saved-view-contract")).toContainText("supply_chain / 2026-06-12");
  await expect(page.getByTestId("saved-view-contract")).toContainText(
    "upstream-left focus-center downstream-right capital-top policy-bottom"
  );
  await expect(page.getByTestId("saved-view-contract")).toContainText(
    "Synthetic Cloud Customer / supply_chain / 2026-06-12"
  );
});

test("reports one active model profile data and score snapshot across visible modules", async ({
  page
}) => {
  await page.goto("/");
  await expectActiveContext(page.getByTestId("workspace-shell"));
  await expect(page.getByTestId("model-contract-state")).toContainText(
    "formula-registry-v4.2"
  );
  await expect(page.getByTestId("model-contract-state")).toContainText(
    "parameter-catalog-v4.2"
  );
  await expect(page.getByTestId("model-contract-state")).toContainText(
    "threshold-registry-v4.2"
  );

  await page.goto("/industries");
  await expectActiveContext(page.getByTestId("industry-landscape-page"));

  await page.goto("/objects-scope");
  await expectActiveContext(page.getByTestId("objects-scope-screen"));
});
