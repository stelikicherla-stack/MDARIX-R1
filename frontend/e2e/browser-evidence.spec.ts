import { test, expect } from "@playwright/test";

async function signIn(page: any, email: string, password: string) {
  await page.goto("/signin");
  await page.getByLabel("User ID or work email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/app/);
}

test.describe("MDARIX browser evidence", () => {
  test("desktop/mobile sign-in error and keyboard focus", async ({ page }) => {
    await page.goto("/signin");
    await expect(page.getByRole("heading", { name: /sign in to mdarix/i })).toBeVisible();
    await page.keyboard.press("Tab");
    await expect(page.locator(":focus")).toBeVisible();
    await page.getByLabel("User ID or work email").fill("invalid@example.invalid");
    await page.getByLabel("Password").fill("InvalidPassword123!");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.locator('[role="alert"], [role="status"]').first()).toBeVisible();
    await page.screenshot({ path: "artifacts/browser-signin-error.png", fullPage: true });
  });

  test("authenticated Platform Admin workflow and screenshots", async ({ page }, testInfo) => {
    await signIn(page, "r1-user-01@synthetic.invalid", "Temp@1234password");
    for (const [route, name, expected] of [["/app/admin", "admin", /govern the mdarix platform/i], ["/app/admin/mapping-studio", "mapping-studio", /mapping studio/i], ["/app/decision", "decision", /decision center|decision readiness/i]] as const) {
      await page.goto(route);
      await expect(page.locator("body")).not.toContainText("Checking your session");
      await expect(page.locator("body")).not.toContainText("Loading tenant administration");
      await expect(page.locator("body")).not.toContainText("Administration unavailable");
      await expect(page.locator("body")).toContainText(expected);
      await page.screenshot({ path: `artifacts/browser-${testInfo.project.name}-admin-${name}.png`, fullPage: true });
    }
  });

  test("Platform Admin navigation opens every domain and subsection", async ({ page }) => {
    test.setTimeout(60_000);
    await signIn(page, "r1-user-01@synthetic.invalid", "Temp@1234password");
    await page.goto("/app/admin");
    const navigation = page.getByRole("complementary", { name: "Platform administration domains" });
    const domains: Record<string, string[]> = {
      "Customers & Tenants": ["Customers", "Tenants", "Administrators", "Provisioning", "Tenant health"],
      "Plans & Licensing": ["Plans", "Entitlements", "Subscriptions", "Expirations", "Reminder rules"],
      "Identity & Access": ["Platform users", "Platform roles", "Permission sets", "MFA & SSO", "Sessions"],
      "Data & Configuration": ["Master data", "Data mapping", "Mapping versions", "Configuration releases"],
      "Integrations": ["Connector catalog", "Customer integrations", "Webhooks", "Integration health", "Failures & logs"],
      "AI Control Center": ["AI overview", "Models & versions", "Agents & prompts", "Evaluations", "Guardrails", "AI executions"],
      "Security & Compliance": ["Security overview", "Tenant isolation", "Encryption & residency", "Retention", "Access reviews"],
      "Audit & Evidence": ["Platform audit trail", "Configuration changes", "Electronic signatures", "Release evidence"],
      "Operations & Setup": ["System health", "Jobs & queues", "Storage", "Incidents", "System settings"],
    };
    for (const [domain, items] of Object.entries(domains)) {
      await navigation.getByRole("button", { name: new RegExp(`^${domain}`) }).click();
      for (const item of items) {
        await navigation.getByRole("button", { name: item, exact: true }).click();
        await expect(page.getByRole("heading", { name: item, exact: true, level: 2 })).toBeVisible();
        await expect(page.locator("main.platform-admin-workspace")).toHaveAttribute("data-admin-view", `${domain}:${item}`);
      }
    }
  });

  test("authenticated Customer Admin workflow and screenshot", async ({ page }, testInfo) => {
    await signIn(page, "stelikicherla3008@gmail.com", "Temp@1234password");
    await page.goto("/app/customer-admin");
    await expect(page.locator("body")).not.toContainText("Checking your session");
    await expect(page.locator("body")).toContainText(/customer administration/i);
    await page.screenshot({ path: `artifacts/browser-${testInfo.project.name}-customer-admin.png`, fullPage: true });
  });

  test("protected routes expose a nonblank state", async ({ page }) => {
    await signIn(page, "r1-user-01@synthetic.invalid", "Temp@1234password");
    for (const route of ["/app/admin", "/app/customer-admin", "/app/admin/mapping-studio", "/app/decision"]) {
      await page.goto(route);
      await expect(page.locator("body")).not.toContainText("Checking your session");
      await expect(page.locator("body")).not.toBeEmpty();
      await expect(page.locator("body")).not.toContainText("Administration unavailable");
    }
  });

  test("home workflow is keyboard reachable", async ({ page }, testInfo) => {
    await signIn(page, "r1-user-01@synthetic.invalid", "Temp@1234password");
    await page.goto("/app");
    await expect(page.locator("body")).not.toBeEmpty();
    await page.waitForTimeout(1500);
    const interactive = page.locator("a,button,input,select,textarea");
    expect(await interactive.count()).toBeGreaterThan(0);
    await page.keyboard.press("Tab");
    await expect(page.locator(":focus")).toBeVisible();
    await page.screenshot({ path: `artifacts/browser-${testInfo.project.name}-home.png`, fullPage: true });
  });

  test("authenticated AI workflow surfaces grounded review state", async ({ page }, testInfo) => {
    await signIn(page, "r1-user-01@synthetic.invalid", "Temp@1234password");
    await page.goto("/app/ask");
    await expect(page.locator("body")).not.toBeEmpty();
    await expect(page.locator("body")).toContainText(/Ask MDARIX|authorized|human review/i);
    await page.screenshot({ path: `artifacts/browser-${testInfo.project.name}-ai-ask.png`, fullPage: true });
    await page.goto("/app/investigations");
    await expect(page.locator("body")).not.toBeEmpty();
    await expect(page.locator("body")).toContainText(/investigat|evidence|review/i);
    await page.screenshot({ path: `artifacts/browser-${testInfo.project.name}-ai-investigation.png`, fullPage: true });
  });
});
