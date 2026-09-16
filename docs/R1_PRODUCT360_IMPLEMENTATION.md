# MDARIX R1 Product 360 Implementation

## Purpose

Product 360 gives regulated investigation users a focused lifecycle view of a medical-device product. It answers what is connected to the product without presenting risk, causality, or root-cause conclusions.

## User

The primary user is a quality, regulatory, safety, post-market, or engineering investigation participant.

## Architecture

The frontend renders backend Product 360 APIs. Identity, relationship, temporal, and provenance logic remains in backend services.

Backend service:

- `backend/app/product360/service.py`
- `/api/v1/products`
- `/api/v1/products/{product_id}/product-360`
- `/api/v1/products/{product_id}/timeline`

Frontend:

- React + TypeScript + Vite
- Tailwind CSS
- Product list, version selector, as-of selector, Product 360 sections, timeline, provenance, and limitations

## Sections

- Header
- Overview counts
- Configuration
- Component/Supplier context
- Changes
- Manufacturing/Lots
- Field/Complaints
- Risk/Controls
- Evidence
- Provenance
- Lifecycle Timeline

## Version Handling

Version selection is explicit. Historical versions remain distinct from current product context.

## Historical View

The API supports `as_of` and `mode` parameters. `mode=event` answers what had happened/effective by a time. `mode=known` answers what was recorded or known by that time.

## Provenance

Product 360 returns source-canonical link provenance for important facts. The default UI shows a bounded provenance table.

## Data Quality

Incomplete traceability, missing lot references, late-arriving evidence, and the absence of causal conclusions are surfaced as limitations.

## Security

The UI does not expose Ground Truth, credentials, raw source payloads, arbitrary SQL, or arbitrary graph queries.

## Known Limitations

The Day 7 UI is intentionally focused and does not include Product 360 editing, graph visualization, AI investigation, or evidence intelligence.
