---
name: frontend-design
description: Intentional visual-design guidance for creating or substantially reshaping a web interface. Use when the task requires visual direction, page composition, typography, hierarchy, interaction feel, or a distinctive UI; do not use as the primary accessibility audit skill.
metadata:
  source_type: vendor-grounded-adaptation
  vendor: Anthropic
---

# Frontend Design

Create interfaces that look intentional and specific to the product rather than generic templates.

## Before implementation

- Identify the product, audience, primary task, information hierarchy, and brand constraints.
- If the brief lacks a visual direction, establish one coherent direction before coding.
- Reuse an existing design system when the project already has one.
- Respect product accessibility, performance, framework, and component-library constraints.

## Visual direction

- Use hierarchy to communicate meaning: scale, spacing, contrast, typography, alignment, density, and grouping must have a reason.
- Choose typography deliberately and keep readable line length and spacing.
- Use color as a system with accessible contrast, not as decoration scattered across components.
- Avoid uniform "card everywhere" layouts when information relationships call for another structure.
- Do not add badges, gradients, glass effects, shadows, numbered labels, or motion merely because they are fashionable.
- Make empty, loading, error, success, and disabled states visually coherent with the primary experience.
- Keep interaction feedback immediate and meaningful.

## Responsive behavior

- Design from content and task priorities, not arbitrary device mockups.
- Prevent layout shifts, clipped content, unusable tap targets, and hidden critical actions.
- Treat mobile as a real interaction mode rather than a compressed desktop.

## Motion

- Use motion to explain change, preserve spatial context, or direct attention.
- Respect reduced-motion preferences.
- Avoid repeated entrance animations or decorative transitions that slow routine work.

## Final critique

Before declaring the UI done, inspect it at representative viewport sizes and ask:
- Is the visual hierarchy obvious?
- Does the design look specific to this product?
- Are important actions discoverable?
- Is the page still useful without animation?
- Are states and edge cases designed, not merely functional?
- Did implementation preserve the approved design system?

For accessibility and detailed interface review, also load `web-design-guidelines`.
