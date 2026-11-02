import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 60_000,
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:5173",
    channel: process.env.E2E_BROWSER_CHANNEL || "chrome",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
  },
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: "npm run dev",
        url: "http://127.0.0.1:5173",
        reuseExistingServer: !process.env.CI,
        env: { VITE_DATA_SOURCE: "http" },
      },
});
