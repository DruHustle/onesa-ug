import { defineConfig } from "@playwright/test";
import { fileURLToPath } from "node:url";
const workspace = fileURLToPath(new URL("../../", import.meta.url));
export default defineConfig({
  testDir: "./tests",
  testMatch: "**/*.spec.ts",
  timeout: 90000,
  expect: { timeout: 10000 },
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:3400",
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: "../.venv311/bin/python ../scripts/browser_fixture.py",
      cwd: workspace,
      url: "http://127.0.0.1:8400/api/v1/health",
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command: "npm run dev",
      cwd: workspace,
      url: "http://127.0.0.1:3400",
      reuseExistingServer: false,
      timeout: 30000,
    },
  ],
  reporter: [
    ["list"],
    ["json", { outputFile: "../artifacts/browser-results.json" }],
  ],
});
