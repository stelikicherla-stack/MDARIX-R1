import { describe, expect, it } from "vitest";
import { APP_ROUTES, isKnownRoute, routeForView, viewFromPath } from "./router";

describe("formal application route registry", () => {
  it("resolves query strings and trailing slashes without changing route identity", () => {
    expect(viewFromPath("/app/admin/mapping-studio/?tenant=tenant-a")).toBe("admin-mapping");
    expect(viewFromPath("/app/customer-admin?section=Users")).toBe("customer-admin");
  });

  it("keeps route generation centralized", () => {
    expect(routeForView("admin-mapping")).toBe(APP_ROUTES["admin-mapping"]);
    expect(isKnownRoute("/app")).toBe(true);
    expect(isKnownRoute("/app/not-a-route")).toBe(false);
  });
});
