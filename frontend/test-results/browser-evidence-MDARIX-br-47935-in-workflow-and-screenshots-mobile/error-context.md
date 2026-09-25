# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: browser-evidence.spec.ts >> MDARIX browser evidence >> authenticated Platform Admin workflow and screenshots
- Location: e2e\browser-evidence.spec.ts:24:3

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('body')
Timeout: 5000ms
Expected pattern: /create customer administrator/i
Received string:  "
    Northstar QualityProduct Lifecycle Intelligence · developmentAdministrator control planeAdministration Identity, access & configurationPlans & Integrations Subscriptions, connectors & mappingsProduct Configuration Products, versions, APIs & mappingsSubscriptions & Notifications Expiry, reminders & templatesMapping Studio Catalog, versions, dry run & driftCustomers / Tenants Search and review customersCreate Customer Provision a tenant and limitsCustomer Administrators Search, update or retire accountsRecent platform administration activity Review user changes and audit evidenceEvidence before inference.Authorized humans decide.LogoutAdministration unavailableThe request could not be completed.Privacy and compliance noticeMDARIX uses essential session storage and tenant-scoped audit records to operate this workspace. Review your organization's GDPR/HIPAA obligations before entering regulated data.DismissAcknowledge·········
"

Call log:
  - Expect "toContainText" locator('body') with timeout 5000ms
  - waiting for locator('body')
    5 × locator resolved to <body>…</body>
      - unexpected value "
    MDARIXProduct Lifecycle Intelligence · environmentWorkspaceHomeProductsSignals & ComplaintsStory ViewPersona DashboardAsk MDARIXInvestigationInvestigationsEvidenceDecision & TrustDecision CenterAI Assurance Inspect AI trust controlsAudit Trail Review recorded activityEvidence before inference.Authorized humans decide.LogoutPrivacy and compliance noticeMDARIX uses essential session storage and tenant-scoped audit records to operate this workspace. Review your organization's GDPR/HIPAA obligations before entering regulated data.DismissAcknowledge
    
  

"
    - locator resolved to <body>…</body>
    - unexpected value "
    Northstar QualityProduct Lifecycle Intelligence · developmentAdministrator control planeAdministration Identity, access & configurationPlans & Integrations Subscriptions, connectors & mappingsProduct Configuration Products, versions, APIs & mappingsSubscriptions & Notifications Expiry, reminders & templatesMapping Studio Catalog, versions, dry run & driftCustomers / Tenants Search and review customersCreate Customer Provision a tenant and limitsCustomer Administrators Search, update or retire accountsRecent platform administration activity Review user changes and audit evidenceEvidence before inference.Authorized humans decide.LogoutAdministrator control planeLoading tenant administration…Privacy and compliance noticeMDARIX uses essential session storage and tenant-scoped audit records to operate this workspace. Review your organization's GDPR/HIPAA obligations before entering regulated data.DismissAcknowledge
    
  

"
    8 × locator resolved to <body>…</body>
      - unexpected value "
    Northstar QualityProduct Lifecycle Intelligence · developmentAdministrator control planeAdministration Identity, access & configurationPlans & Integrations Subscriptions, connectors & mappingsProduct Configuration Products, versions, APIs & mappingsSubscriptions & Notifications Expiry, reminders & templatesMapping Studio Catalog, versions, dry run & driftCustomers / Tenants Search and review customersCreate Customer Provision a tenant and limitsCustomer Administrators Search, update or retire accountsRecent platform administration activity Review user changes and audit evidenceEvidence before inference.Authorized humans decide.LogoutAdministration unavailableThe request could not be completed.Privacy and compliance noticeMDARIX uses essential session storage and tenant-scoped audit records to operate this workspace. Review your organization's GDPR/HIPAA obligations before entering regulated data.DismissAcknowledge
    
  

"

```

```yaml
- main:
  - button "Sign out of MDARIX": Logout
  - heading "Administration unavailable" [level=2]
  - paragraph: The request could not be completed.
- dialog "Privacy and compliance consent":
  - strong: Privacy and compliance notice
  - paragraph: MDARIX uses essential session storage and tenant-scoped audit records to operate this workspace. Review your organization's GDPR/HIPAA obligations before entering regulated data.
  - button "Dismiss"
  - button "Acknowledge"
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | async function signIn(page: any, email: string, password: string) {
  4  |   await page.goto("/signin");
  5  |   await page.getByLabel("User ID or work email").fill(email);
  6  |   await page.getByLabel("Password").fill(password);
  7  |   await page.getByRole("button", { name: /sign in/i }).click();
  8  |   await expect(page).toHaveURL(/\/app/);
  9  | }
  10 | 
  11 | test.describe("MDARIX browser evidence", () => {
  12 |   test("desktop/mobile sign-in error and keyboard focus", async ({ page }) => {
  13 |     await page.goto("/signin");
  14 |     await expect(page.getByRole("heading", { name: /sign in to mdarix/i })).toBeVisible();
  15 |     await page.keyboard.press("Tab");
  16 |     await expect(page.locator(":focus")).toBeVisible();
  17 |     await page.getByLabel("User ID or work email").fill("invalid@example.invalid");
  18 |     await page.getByLabel("Password").fill("InvalidPassword123!");
  19 |     await page.getByRole("button", { name: /sign in/i }).click();
  20 |     await expect(page.locator('[role="alert"], [role="status"]').first()).toBeVisible();
  21 |     await page.screenshot({ path: "artifacts/browser-signin-error.png", fullPage: true });
  22 |   });
  23 | 
  24 |   test("authenticated Platform Admin workflow and screenshots", async ({ page }, testInfo) => {
  25 |     await signIn(page, "r1-user-01@synthetic.invalid", "Temp@1234password");
  26 |     for (const [route, name, expected] of [["/app/admin", "admin", /create customer administrator/i], ["/app/admin/mapping-studio", "mapping-studio", /mapping studio/i], ["/app/decision", "decision", /decision center|decision readiness/i]] as const) {
  27 |       await page.goto(route);
  28 |       await expect(page.locator("body")).not.toContainText("Checking your session");
  29 |       await expect(page.locator("body")).not.toContainText("Loading tenant administration");
  30 |       await expect(page.locator("body")).not.toContainText("Administration unavailable");
> 31 |       await expect(page.locator("body")).toContainText(expected);
     |                                          ^ Error: expect(locator).toContainText(expected) failed
  32 |       await page.screenshot({ path: `artifacts/browser-${testInfo.project.name}-admin-${name}.png`, fullPage: true });
  33 |     }
  34 |   });
  35 | 
  36 |   test("authenticated Customer Admin workflow and screenshot", async ({ page }, testInfo) => {
  37 |     await signIn(page, "stelikicherla3008@gmail.com", "Temp@1234password");
  38 |     await page.goto("/app/customer-admin");
  39 |     await expect(page.locator("body")).not.toContainText("Checking your session");
  40 |     await expect(page.locator("body")).toContainText(/customer administration/i);
  41 |     await page.screenshot({ path: `artifacts/browser-${testInfo.project.name}-customer-admin.png`, fullPage: true });
  42 |   });
  43 | 
  44 |   test("protected routes expose a nonblank state", async ({ page }) => {
  45 |     await signIn(page, "r1-user-01@synthetic.invalid", "Temp@1234password");
  46 |     for (const route of ["/app/admin", "/app/customer-admin", "/app/admin/mapping-studio", "/app/decision"]) {
  47 |       await page.goto(route);
  48 |       await expect(page.locator("body")).not.toContainText("Checking your session");
  49 |       await expect(page.locator("body")).not.toBeEmpty();
  50 |       await expect(page.locator("body")).not.toContainText("Administration unavailable");
  51 |     }
  52 |   });
  53 | 
  54 |   test("home workflow is keyboard reachable", async ({ page }, testInfo) => {
  55 |     await signIn(page, "r1-user-01@synthetic.invalid", "Temp@1234password");
  56 |     await page.goto("/app");
  57 |     await expect(page.locator("body")).not.toBeEmpty();
  58 |     await page.waitForTimeout(1500);
  59 |     const interactive = page.locator("a,button,input,select,textarea");
  60 |     expect(await interactive.count()).toBeGreaterThan(0);
  61 |     await page.keyboard.press("Tab");
  62 |     await expect(page.locator(":focus")).toBeVisible();
  63 |     await page.screenshot({ path: `artifacts/browser-${testInfo.project.name}-home.png`, fullPage: true });
  64 |   });
  65 | 
  66 |   test("authenticated AI workflow surfaces grounded review state", async ({ page }, testInfo) => {
  67 |     await signIn(page, "r1-user-01@synthetic.invalid", "Temp@1234password");
  68 |     await page.goto("/app/ask");
  69 |     await expect(page.locator("body")).not.toBeEmpty();
  70 |     await expect(page.locator("body")).toContainText(/Ask MDARIX|authorized|human review/i);
  71 |     await page.screenshot({ path: `artifacts/browser-${testInfo.project.name}-ai-ask.png`, fullPage: true });
  72 |     await page.goto("/app/investigations");
  73 |     await expect(page.locator("body")).not.toBeEmpty();
  74 |     await expect(page.locator("body")).toContainText(/investigat|evidence|review/i);
  75 |     await page.screenshot({ path: `artifacts/browser-${testInfo.project.name}-ai-investigation.png`, fullPage: true });
  76 |   });
  77 | });
  78 | 
```