# MDARIX Case Context Architecture

`MDARIXCaseContext` is the authoritative tenant/user context record. It contains tenant, user, membership, Product, ProductVersion, signal/complaint scope, investigation, temporal mode/cutoff, decision references, context version, last page, and timestamps.

The API persists and validates context server-side. Product changes clear incompatible downstream scope; ProductVersion changes clear incompatible signal/investigation scope. Browser-supplied IDs are selectors only and never authorization. All protected routes derive tenant and identity from `AuthenticatedRequestContext`.
