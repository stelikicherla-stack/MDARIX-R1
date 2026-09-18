# MDARIX UI Design System Plan

This is the implementation contract for the enterprise UI professionalization
work. It applies to public marketing pages and the authenticated investigation
workspace without changing backend contracts or authorization behavior.

## Visual language

- Navy communicates authority, governance, and medical-device seriousness.
- Enterprise blue communicates navigation and primary information.
- Teal communicates verified, active, or selected workflow states.
- Light blue and cyan surfaces separate evidence, intelligence, and guidance
  without relying on decoration.
- Amber and red are reserved for limitations, warnings, and blocked actions.
- Use one strong page title, one supporting sentence, and one primary action per
  page section.

## Tokens

```css
:root {
  --md-navy: #0b1f33;
  --md-blue: #145da0;
  --md-intelligence: #2477c8;
  --md-teal: #0f9d9a;
  --md-cyan: #ddf5f4;
  --md-canvas: #f4f8fc;
  --md-surface: #ffffff;
  --md-border: #dde5ec;
  --md-text: #102334;
  --md-muted: #526575;
}
```

## Shared components

`AppShell`, `PublicHeader`, `PrivateSidebar`, `PageHero`, `SectionHeader`,
`StoryRail`, `Panel`, `MetricCard`, `StatusBadge`, `EvidenceCard`,
`EmptyState`, `ErrorState`, `DataTable`, `StepRail`, and `PrimaryAction` should
be reusable and accessible. Components must expose visible focus states, use
semantic headings, and keep action labels explicit.

## Page patterns

- Public pages use a compact header, a topic-specific hero, a visual or
  diagrammatic story block, capability sections, and a final CTA.
- Auth pages use labeled fields, inline validation, security context, and a
  single focused form column.
- Private pages use a persistent vertical workflow, a context header, a page
  hero, primary content, limitations, and related evidence/actions.
- Ask MDARIX presents question, scope, time basis, retrieval plan, evidence,
  limitations, and human decision boundaries as distinct states.

## Responsive and accessibility rules

- Collapse public navigation into a keyboard-accessible menu below the desktop
  breakpoint; close menus after navigation.
- Keep private workflow navigation vertical on desktop and collapsible on small
  screens; never rely on horizontal scrolling for primary navigation.
- Preserve logical tab order, visible `:focus-visible`, accessible names, and
  error text associated with fields.
- Avoid decorative images that compete with evidence or decision content. Any
  product visual must have useful alt text or be explicitly decorative.
- Prefer CSS and existing local assets before adding external dependencies.

## Delivery guardrails

The UI work must not alter API URLs, request/response contracts, tenant
derivation, entitlements, authorization, audit behavior, signing controls, or
Ask MDARIX security boundaries. Each UI increment must pass the frontend
production build and the relevant existing tests before it is committed.
