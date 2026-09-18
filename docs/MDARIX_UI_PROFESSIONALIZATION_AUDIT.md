# MDARIX UI Professionalization Audit

## Audit scope

Reviewed the existing Vite/React frontend, public navigation, authentication
routes, private application shell, Product 360, Investigations, Evidence,
Decision Center, AI Assurance, Audit Trail, and current Ask MDARIX story.

The redesign must preserve backend APIs, authentication, tenant controls,
authorization, entitlements, Day 25 boundaries, and Day 26 Ask controls.

## Current strengths

- MDARIX already has a distinct medical-device lifecycle and investigation story.
- Public navigation includes Platform, Solutions, Product Lifecycle, Why MDARIX,
  Resources, and Plans.
- Authenticated application navigation separates workspace, investigation, and
  decision/trust concerns.
- Product 360 exposes ProductVersion, temporal context, evidence, limitations,
  and provenance.
- AI Assurance and Audit Trail are visible in the private shell.
- Public and private surfaces already use restrained navy, blue, teal, and light
  neutral surfaces.

## Current inconsistencies to address

- Public and private headers use different navigation and spacing systems.
- CSS contains legacy and compressed one-line rules alongside newer components,
  making visual changes difficult to govern consistently.
- Some pages rely on large empty panels instead of a clear narrative hierarchy.
- Public mega-menu and page content can feel like separate layers rather than a
  single product story.
- Authentication forms need stronger field-label hierarchy, validation states,
  and enterprise trust context without adding marketing clutter.
- Ask MDARIX is currently represented as a story/entry point; its controlled
  interface should visibly distinguish question, scope, time basis,
  clarification, limitations, and evidence context.
- Responsive behavior and keyboard/focus treatment need a systematic review.

## Proposed design system

Use shared CSS tokens rather than page-specific colors:

```css
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
```

Shared primitives should cover `Shell`, `Header`, `Sidebar`, `PageHero`,
`SectionHeader`, `Panel`, `Metric`, `StatusBadge`, `EmptyState`, `ErrorState`,
`DataTable`, `StepRail`, and `PrimaryAction`. The system should retain generous
white/light-blue surfaces, use navy for authority, and reserve teal for selected
states and intelligence accents.

## Route and workflow plan

1. Public homepage: medical-device-specific hero, connected lifecycle story,
   evidence-before-inference, enterprise controls, and one clear CTA.
2. Public solution/resource pages: consistent hero, topic visual, concise
   capability sections, and no dead links.
3. Auth: compact professional forms with visible labels, accessible errors, and
   verification/reset states.
4. Private shell: persistent context header, vertical workflow navigation,
   consistent page rhythm, and meaningful empty/loading/error states.
5. Ask MDARIX: controlled investigation workspace, not a generic chatbot.
6. Core pages: Product 360, Investigations, Evidence, Decision Center, AI
   Assurance, and Audit Trail share the same layout primitives.

## Implementation sequence

1. Establish tokens and shared primitives.
2. Refine the public homepage and responsive header.
3. Refine auth screens.
4. Refine private shell and Product 360.
5. Surface the controlled Ask MDARIX workflow.
6. Run keyboard, responsive, production-build, and functional regression checks.

No backend or security architecture needs to be weakened for this plan. No
visual redesign should be mixed into the formal Day 26 completion commit.
