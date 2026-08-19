---
name: frontend-design
description: UI/UX, responsive layouts, accessibility, and framework-specific frontend rules.
user-invocable: true
---

# Frontend Design


## When to use

Use for UI, UX, design systems, frontends, landing pages, dashboards, and app screens.

## Inputs to check

- `design.md`
- selected framework
- target devices
- brand direction
- required pages
- accessibility needs

## Workflow

1. Read design.md.
2. If missing, create minimal design system first.
3. Confirm selected framework.
4. Build responsive layout.
5. Add loading, empty, error, success states.
6. Add accessibility and keyboard support.
7. Verify mobile and desktop behavior.

## Output format

- Design summary
- Components created/changed
- Responsive behavior
- Accessibility notes
- Files changed

## Quality checklist

- [ ] Does not assume React unless selected
- [ ] Mobile responsive
- [ ] Semantic HTML where applicable
- [ ] Loading/error/empty states included
- [ ] Accessible focus and contrast

## Stop conditions

Stop if design.md conflicts with the brief; document the conflict before implementation.
