import { defineConfig, devices } from "@playwright/test";

const installedChrome = process.env.MDARIX_E2E_CHROME_PATH ??
  (process.platform === "win32" ? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" : undefined);

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  reporter: [["list"], ["json", { outputFile: "artifacts/browser-evidence.json" }]],
  use: { baseURL: "http://127.0.0.1:5177", trace: "retain-on-failure", screenshot: "only-on-failure", launchOptions: installedChrome ? { executablePath: installedChrome } : undefined },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 5"] } },
  ],
});
