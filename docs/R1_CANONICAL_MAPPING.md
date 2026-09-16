# MDARIX R1 Canonical Mapping

## QMS

QMS complaints map to canonical `complaints` using `COMPLAINT_SOURCE_ID_V1`. Product version references resolve through `PRODUCT_VERSION_COMPOSITE_V1` or source aliases. Missing lot references remain visible.

QMS investigations map to canonical `investigations` using `INVESTIGATION_SOURCE_ID_V1`.

QMS risks, failure modes, and controls map by exact identifiers.

## PLM

PLM products map to `products`.

PLM product versions map to `product_versions` using product context plus normalized revision.

PLM components map to `components` by identifier and revision.

PLM requirements and changes map to their canonical tables by explicit identifiers.

## ERP/MES

ERP/MES suppliers map to `suppliers`, preserving alias provenance.

ERP/MES manufacturing sites map to `manufacturing_sites`.

ERP/MES lots map to `lot_batches` using lot, product-version, and site context.

## Evidence

Evidence metadata maps to canonical `evidence`. Evidence Markdown files link back to the matching evidence identifier without AI extraction.

## Relationships

Day 5 resolves supported lifecycle relationships, including:

- LotBatch -> ProductVersion
- Component -> Supplier

No causal relationship is created by Day 5.
