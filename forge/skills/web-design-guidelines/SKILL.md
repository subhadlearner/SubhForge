---
name: web-design-guidelines
description: Review an existing web UI for accessibility, UX, interaction, form, responsive, semantic HTML, keyboard, focus, motion, content, and interface-quality problems. Use for UI reviews and audits rather than initial visual direction.
metadata:
  source_type: vendor-grounded-adaptation
  vendor: Vercel
---

# Web Interface Review

Review rendered behavior and source together where practical.

## Accessibility and semantics

- Prefer semantic HTML before ARIA.
- Ensure interactive elements are reachable and operable by keyboard.
- Preserve visible focus indication.
- Associate form controls with labels and validation messages.
- Give images meaningful alternative text when they convey content; use empty alt text for purely decorative images.
- Maintain sufficient text and control contrast.
- Do not communicate state using color alone.
- Respect reduced-motion preferences.
- Verify heading hierarchy and landmark structure.

## Interaction

- Buttons perform actions; links navigate.
- Controls need clear hover/focus/pressed/disabled/loading states where applicable.
- Avoid tiny click/tap targets and hover-only functionality.
- Do not steal focus or scroll unexpectedly.
- Confirmation and destructive-action patterns must match consequence and reversibility.

## Forms

- Validate close to the field while preserving a useful submission-level summary when needed.
- Preserve user input after recoverable errors.
- Use correct input types and browser autocomplete hints where appropriate.
- Avoid disabling paste into credential or verification fields without a strong requirement.

## Responsive and content quality

- Check narrow, medium, and wide layouts.
- Prevent horizontal overflow and clipped dialogs/menus.
- Avoid layout shifts from unloaded media.
- Make long labels, translations, empty states, error states, and large data values survivable.
- Keep important actions and status understandable without relying on icon interpretation alone.

## Performance-sensitive UI

- Use appropriately sized images and lazy loading where suitable.
- Avoid loading large client bundles for behavior that can remain server-rendered or progressive.
- Avoid expensive animations and layout thrashing.

## Output

Report concrete findings with severity and file/component/location when available. Distinguish defects from optional polish. Do not redesign the whole interface unless asked.
