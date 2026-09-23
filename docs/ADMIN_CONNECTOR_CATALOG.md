# Stage 2 — Connector catalog and health

Connector configuration is metadata-only and tenant-scoped. The catalog supports TrackWise Digital, Veeva Vault QMS, MasterControl, SAP, Oracle, Salesforce, Teamcenter, Windchill, LIMS, MES, RIM and safety-system connector types through versioned configuration records. Versions, authentication type, supported objects, transformation version, compatibility, customer usage and limitations are represented in configuration metadata.

Connection test/execute endpoints never return source business data. Health checks report status, last successful sync, last failure and retry metadata. Real provider credentials and external connectivity remain deployment gates.
