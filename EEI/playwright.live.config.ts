import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: ["saved-view-live.spec.ts"],
  timeout: 45_000,
  expect: {
    timeout: 7_500
  },
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry"
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } }
    }
  ],
  webServer: [
    {
      command:
        "EEI_ALLOW_DB_RESET_FOR_E2E=1 EEI_CORS_ALLOW_ORIGINS=http://127.0.0.1:3000 bash scripts/run_live_e2e_api.sh",
      url: "http://127.0.0.1:8000/health/ready",
      reuseExistingServer: false,
      timeout: 180_000
    },
    {
      command:
        "NEXT_PUBLIC_EEI_API_BASE_URL=http://127.0.0.1:8000 npx --yes pnpm@11.8.0 --filter @eei/web dev",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: false,
      timeout: 120_000
    }
  ]
});
