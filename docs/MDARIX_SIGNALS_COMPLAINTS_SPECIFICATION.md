# Signals & Complaints Specification

Signals is a first-class view of complaint-derived attention. It supports filtering by ProductVersion, severity, failure mode, country, lot, status, and event/knowledge time. It distinguishes source-recorded complaint facts from derived clusters.

The Stage 2 read-only endpoint `/api/v1/analytics/signals` returns tenant-scoped complaint rows and limitations. Clustering, trend detection, and signal identifiers require persisted source/analytics records; the UI must label these as unavailable rather than fabricate them.
