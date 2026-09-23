# Mapping Studio Metadata Architecture

Stage 1 establishes server-owned catalogs for external applications, source objects and fields, MDARIX canonical entities and fields, transformations, validation rules, source priorities, and tenant override policies. The frontend consumes these contracts; it does not own a duplicate field model.

Protected canonical fields (`id`, `tenant_id`, provenance, audit, authorization, and mapping-version metadata) are returned as `PLATFORM_ONLY` and are not tenant-mappable.
