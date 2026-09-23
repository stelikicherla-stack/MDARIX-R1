# Product 360 UX Specification

Product 360 is the governed entry point for Product and ProductVersion context. Its persistent header shows ProductVersion, temporal mode, cutoff, tenant, and selected investigation.

Sections: Overview, Configuration, Manufacturing, Field, Evidence, Risk, Changes, Timeline, Investigation, and Ask MDARIX. Product switching cascades to the selected version, evidence, investigations, and timeline; stale child selections are cleared.

All counts and lists come from tenant-scoped backend services. Empty states say “not recorded” or “no authorized records available,” never “none occurred.”
