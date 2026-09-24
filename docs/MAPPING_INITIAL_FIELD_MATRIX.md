# MDARIX R1 — Initial Field Matrix

The initial matrix is represented by the controlled `INITIAL_MAPPINGS` catalog and includes TrackWise Complaint and Teamcenter ProductVersion mappings. Required relationship mappings include Product, ProductVersion, and Lot lookup transformations; source timestamps are preserved in canonical source-time fields.

The matrix is intentionally server-owned and can be extended through versioned mapping records without changing released versions in place.
