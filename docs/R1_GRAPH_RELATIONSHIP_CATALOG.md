# MDARIX R1 Graph Relationship Catalog

| Type | Direction | Assertion | Meaning |
| --- | --- | --- | --- |
| `PRODUCT_HAS_VERSION` | Product -> ProductVersion | Deterministically derived | Product owns a version |
| `VERSION_USES_COMPONENT` | ProductVersion -> Component | Deterministically derived | Version configuration includes component |
| `COMPONENT_SUPPLIED_BY` | Component -> Supplier | Deterministically derived | Component supplier relationship |
| `CHANGE_AFFECTS_COMPONENT` | Change -> Component | Source asserted | Change references a component |
| `CHANGE_AFFECTS_PRODUCT_VERSION` | Change -> ProductVersion | Source asserted | Change references a product version |
| `CHANGE_AFFECTS_SUPPLIER` | Change -> Supplier | Source asserted | Change references a supplier |
| `LOT_PRODUCED_AT_SITE` | LotBatch -> ManufacturingSite | Source asserted | Lot was produced at site |
| `LOT_FOR_PRODUCT_VERSION` | LotBatch -> ProductVersion | Source asserted or derived | Lot belongs to product version |
| `COMPLAINT_ASSOCIATED_WITH_PRODUCT` | Complaint -> Product | Source asserted | Complaint references product |
| `COMPLAINT_ASSOCIATED_WITH_VERSION` | Complaint -> ProductVersion | Source asserted | Complaint references product version |
| `COMPLAINT_ASSOCIATED_WITH_LOT` | Complaint -> LotBatch | Source asserted | Complaint references resolved lot |
| `INVESTIGATION_ASSOCIATED_WITH_PRODUCT` | Investigation -> Product | Source asserted | Investigation concerns product |
| `INVESTIGATION_INCLUDES_COMPLAINT` | Investigation -> Complaint | Deterministically derived | Investigation product context includes complaint set |
| `INVESTIGATION_USES_EVIDENCE` | Investigation -> Evidence | Source asserted | Evidence metadata references investigation |
| `RISK_ASSOCIATED_WITH_PRODUCT` | Risk -> Product | Source asserted | Risk references product |

No relationship type in Day 6 means cause, root cause, or failure chain.
