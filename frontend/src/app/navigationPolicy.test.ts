import { describe, expect, it } from "vitest";
import { APP_ROUTES, viewFromPath } from "./router";
import { AUTH_ENDPOINTS, allowedViewsForRole, apiErrorMessage, clearTenantScopedCache, isCustomerAdminRole, isPlatformAdminRole, MOBILE_FOCUS_ORDER } from "./navigationPolicy";

describe("authentication and role navigation", () => {
  it("uses the session, signin, and signout API contracts", () => {
    expect(AUTH_ENDPOINTS).toEqual({ session: "/api/v1/auth/session", signin: "/api/v1/auth/signin", signout: "/api/v1/auth/signout" });
  });

  it("recognizes platform and customer administrator roles", () => {
    expect(isPlatformAdminRole("Administrator")).toBe(true);
    expect(isPlatformAdminRole("Viewer")).toBe(false);
    expect(isCustomerAdminRole("CUSTOMER_ADMIN")).toBe(true);
    expect(isCustomerAdminRole("Administrator")).toBe(false);
  });

  it("routes each administrator to only its own protected area", () => {
    expect(allowedViewsForRole("Administrator")).toContain("admin");
    expect(allowedViewsForRole("Administrator")).not.toContain("customer-admin");
    expect(allowedViewsForRole("Customer Admin")).toEqual(["customer-admin"]);
    expect(allowedViewsForRole("Viewer")).toBeNull();
  });

  it("keeps every declared admin route addressable", () => {
    for (const [view, path] of Object.entries(APP_ROUTES)) expect(viewFromPath(path)).toBe(view);
  });
});

describe("tenant cache and API failure boundaries", () => {
  it("clears tenant and context cache entries while preserving unrelated settings", () => {
    const values = new Map([["mdarix:tenant:a:products", "a"], ["mdarix:context:a", "a"], ["mdarix:ui:theme", "dark"]]);
    const storage = { get length() { return values.size; }, key: (index: number) => [...values.keys()][index] ?? null, removeItem: (key: string) => values.delete(key) };
    expect(clearTenantScopedCache(storage)).toBe(2);
    expect(values.has("mdarix:ui:theme")).toBe(true);
  });

  it("surfaces structured API errors and safe fallback errors", () => {
    expect(apiErrorMessage({ detail: { message: "Tenant denied" } })).toBe("Tenant denied");
    expect(apiErrorMessage({ detail: "Unavailable" })).toBe("Unavailable");
    expect(apiErrorMessage({})).toBe("The request could not be completed.");
  });
});

describe("Mapping Studio, onboarding, mobile and keyboard contracts", () => {
  it("keeps Mapping Studio and onboarding routes explicit", () => {
    expect(APP_ROUTES["admin-mapping"]).toBe("/app/admin/mapping-studio");
    expect(APP_ROUTES["admin-create-customer"]).toBe("/app/admin/customers/new");
  });

  it("defines a deterministic mobile keyboard focus order", () => {
    expect([...MOBILE_FOCUS_ORDER]).toEqual(["menu", "user-context", "primary-content", "logout"]);
  });
});
