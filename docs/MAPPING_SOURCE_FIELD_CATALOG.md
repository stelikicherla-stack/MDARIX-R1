# MDARIX R1 — Source Field Catalog

Source fields are server-owned metadata filtered by application, connector version, and source object. Each field exposes its stable identifier, name/label, group, data type, required/nullable flags, sample metadata, enum values, schema version, lifecycle status, standard/customer classification, and sensitivity classification.

The TrackWise Complaint catalog and field groups are seeded in `backend/app/mapping_catalog_router.py`. Frontend controls consume these APIs rather than maintaining a second field array.
