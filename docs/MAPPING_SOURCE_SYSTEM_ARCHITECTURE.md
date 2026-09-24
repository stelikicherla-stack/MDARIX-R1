# MDARIX R1 — Mapping Source-System Architecture

## Boundary

External systems remain systems of record. MDARIX receives source records through connector contracts, preserves source identity and timestamps, and maps records into tenant-scoped canonical entities. MDARIX never queries a simulator database directly and never treats source payloads as authorization authority.

## Supported MVP source domains

TrackWise Digital/QMS, Veeva Vault QMS, Teamcenter and Windchill PLM, SAP and Oracle ERP, Salesforce Service, Risk, RIM/Vigilance, Safety/Field Action, LIMS, and MES.

## Contract flow

`ConnectorConfiguration → ConnectorVersion → SourceObject → SourceField → MasterMapping → TenantMappingVersion → Canonical Entity`

Provider health/schema access is server-side, authenticated, bounded by timeout, and sanitized. The deterministic simulator contract is used for local tests; a real provider is an operational gate.
