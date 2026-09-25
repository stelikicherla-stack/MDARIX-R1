import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, requestJson } from "./apiClient";

describe("shared API client", () => {
  beforeEach(() => {
    vi.stubGlobal("window", { setTimeout, clearTimeout });
  });
  afterEach(() => vi.restoreAllMocks());

  it("sends same-origin credentials and parses successful JSON", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "ok" }), { status: 200 })));
    await expect(requestJson<{ status: string }>("/api/v1/session/context")).resolves.toEqual({ status: "ok" });
    expect(fetch).toHaveBeenCalledWith("/api/v1/session/context", expect.objectContaining({ credentials: "same-origin" }));
  });

  it("converts structured API failures into safe ApiError values", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: { code: "TENANT_DENIED", message: "Tenant denied" } }), { status: 403, statusText: "Forbidden" })));
    await expect(requestJson("/api/v1/admin/customers")).rejects.toMatchObject({ name: "ApiError", status: 403, code: "TENANT_DENIED", message: "Tenant denied" });
  });

  it("does not retry state-changing requests by default", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Rejected" }), { status: 409, statusText: "Conflict" })));
    await expect(requestJson("/api/v1/admin/customers", { method: "POST", body: "{}" })).rejects.toBeInstanceOf(ApiError);
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});
