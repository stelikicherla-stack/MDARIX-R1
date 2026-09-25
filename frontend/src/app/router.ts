export type AppView = "home" | "products" | "signals" | "story" | "persona" | "ask" | "investigations" | "evidence" | "decision" | "assurance" | "audit" | "customer-admin" | "admin" | "admin-stage2" | "admin-product-configuration" | "admin-subscriptions" | "admin-mapping" | "admin-customers" | "admin-create-customer" | "admin-customer-360" | "admin-manage" | "admin-audit";

export const APP_ROUTES: Record<AppView, string> = {
  home: "/app",
  products: "/app/products",
  signals: "/app/signals",
  story: "/app/story",
  persona: "/app/persona",
  ask: "/app/ask",
  investigations: "/app/investigations",
  evidence: "/app/evidence",
  decision: "/app/decision",
  assurance: "/app/assurance",
  audit: "/app/audit",
  "customer-admin": "/app/customer-admin",
  admin: "/app/admin",
  "admin-stage2": "/app/admin/stage2",
  "admin-product-configuration": "/app/admin/product-configuration",
  "admin-subscriptions": "/app/admin/subscriptions",
  "admin-mapping": "/app/admin/mapping-studio",
  "admin-customers": "/app/admin/customers",
  "admin-create-customer": "/app/admin/customers/new",
  "admin-customer-360": "/app/admin/customers/detail",
  "admin-manage": "/app/admin/customer-admins",
  "admin-audit": "/app/admin/audit",
};

export function viewFromPath(pathname: string): AppView {
  const normalized = pathname.split("?")[0].replace(/\/$/, "") || "/";
  const match = (Object.entries(APP_ROUTES) as [AppView, string][]).find(([, path]) => path === normalized);
  return match?.[0] ?? "home";
}

export function routeForView(view: AppView): string {
  return APP_ROUTES[view];
}

export function isKnownRoute(pathname: string): boolean {
  return viewFromPath(pathname) !== "home" || pathname.split("?")[0].replace(/\/$/, "") === APP_ROUTES.home;
}

export function navigateTo(view: AppView) {
  const path = routeForView(view);
  if (window.location.pathname !== path) window.history.pushState({ view }, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
