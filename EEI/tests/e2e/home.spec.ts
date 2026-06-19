import { expect, test } from "@playwright/test";

test("renders the watchlist-first EEI workspace", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("main")).toBeVisible();
  await expect(page.getByRole("heading", { name: "NVIDIA" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "主导航" })).toContainText("商业版图");
  await expect(page.getByRole("img", { name: /NVIDIA to TSMC to ASML/ })).toBeVisible();
});

