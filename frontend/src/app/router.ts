export type AppView = "home" | "products" | "signals" | "story" | "persona" | "investigations" | "evidence" | "decision" | "assurance" | "audit" | "admin" | "admin-manage" | "admin-audit";

export const APP_ROUTES: Record<AppView, string> = {
  home: "/app",
  products: "/app/products",
  signals: "/app/signals",
  story: "/app/story",
  persona: "/app/persona",
  investigations: "/app/investigations",
  evidence: "/app/evidence",
  decision: "/app/decision",
  assurance: "/app/assurance",
  audit: "/app/audit",
  admin: "/app/admin",
  "admin-manage": "/app/admin/customers",
  "admin-audit": "/app/admin/audit",
};

export function viewFromPath(pathname: string): AppView {
  const match = (Object.entries(APP_ROUTES) as [AppView, string][]).find(([, path]) => pathname === path);
  return match?.[0] ?? "home";
}

export function navigateTo(view: AppView) {
  const path = APP_ROUTES[view];
  if (window.location.pathname !== path) window.history.pushState({ view }, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
