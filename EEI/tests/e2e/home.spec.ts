import { expect, test } from "@playwright/test";

test("renders the watchlist-first EEI workspace", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("main")).toBeVisible();
  await expect(page.getByRole("heading", { name: "NVIDIA" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "主导航" })).toContainText("商业版图");
  await expect(page.getByRole("img", { name: /NVIDIA synthetic recursive supply-chain graph/ })).toBeVisible();
  await expect(page.getByTestId("fixture-disclosure")).toContainText("Fixture-only data");
  await expect(page.getByText("Live facts: disabled")).toBeVisible();
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

  await page.getByRole("button", { name: "以 Synthetic Advanced Foundry 为中心" }).click();
  await expect(page.getByRole("heading", { name: "Synthetic Advanced Foundry" })).toBeVisible();

  await page.getByRole("button", { name: "以 Synthetic Lithography Equipment Co. 为中心" }).click();
  await expect(page.getByRole("heading", { name: "Synthetic Lithography Equipment Co." })).toBeVisible();

  await page.getByRole("button", { name: "以 Synthetic Specialty Materials Co. 为中心" }).click();
  await expect(page.getByRole("heading", { name: "Synthetic Specialty Materials Co." })).toBeVisible();

  const breadcrumb = page.getByTestId("reroot-breadcrumb");
  await expect(breadcrumb).toContainText("NVIDIA");
  await expect(breadcrumb).toContainText("Synthetic Advanced Foundry");
  await expect(breadcrumb).toContainText("Synthetic Lithography Equipment Co.");
  await expect(breadcrumb).toContainText("Synthetic Specialty Materials Co.");
  await expect(page.getByText("Live facts: disabled")).toBeVisible();
});
