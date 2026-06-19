import { expect, test } from "@playwright/test";

test("shows industry landscape stages subindustries entities bottlenecks capital policy and changes", async ({
  page
}) => {
  await page.goto("/industries");

  await expect(page.getByTestId("industry-landscape-page")).toBeVisible();
  await expect(page.getByTestId("industry-title")).toHaveText("Semiconductors");
  await expect(page.getByTestId("industry-taxonomy")).toContainText("taxonomy-v4.2");

  await expect(page.getByTestId("industry-chain-stages")).toBeVisible();
  await expect(page.locator("[data-testid^='industry-stage-']")).toHaveCount(6);
  for (const section of [
    "industry-subindustries",
    "industry-entities",
    "industry-bottlenecks",
    "industry-capital",
    "industry-policy",
    "industry-changes"
  ]) {
    await expect(page.getByTestId(section)).toBeVisible();
  }

  await expect(page.getByTestId("industry-subindustries")).toContainText("Advanced packaging");
  await expect(page.getByTestId("industry-entities")).toContainText("NVIDIA");
  await expect(page.getByTestId("industry-bottlenecks")).toContainText("EUV exposure capacity");
  await expect(page.getByTestId("industry-capital")).toContainText("Foundry capex");
  await expect(page.getByTestId("industry-policy")).toContainText("Export controls");
  await expect(page.getByTestId("industry-changes")).toContainText("Packaging demand");
});

test("visibly supports cross-industry navigation from semiconductors to energy and cloud", async ({
  page
}) => {
  await page.goto("/industries");

  await expect(page.getByTestId("cross-industry-links")).toContainText(
    "Power and data-center energy"
  );
  await page.getByTestId("cross-industry-energy").click();
  await expect(page.getByTestId("industry-title")).toHaveText("Power and data-center energy");
  await expect(page.getByTestId("cross-industry-notice")).toContainText(
    "Semiconductors -> Power and data-center energy"
  );
  await expect(page.getByTestId("industry-policy")).toContainText("Rate-base approval");

  await page.getByTestId("cross-industry-ai-cloud").click();
  await expect(page.getByTestId("industry-title")).toHaveText("AI cloud infrastructure");
  await expect(page.getByTestId("cross-industry-notice")).toContainText(
    "Semiconductors -> Power and data-center energy -> AI cloud infrastructure"
  );
  await expect(page.getByTestId("industry-chain-stages")).toContainText("Accelerators");
});
