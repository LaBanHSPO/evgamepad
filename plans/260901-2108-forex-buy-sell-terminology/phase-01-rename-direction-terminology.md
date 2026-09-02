---
title: "Rename direction terminology"
status: completed
phase: 1
priority: P2
effort: 1h
dependencies: []
---

# Rename direction terminology

## Context

- [Plan](./plan.md)
- [Design system](../../docs/design_system.md)
- [Application](../../app/src/)
- [Project overview](../../README.md)

## Requirements

- Change user-visible trading directions from long/short to buy/sell.
- Change prototype component direction types from `"long" | "short"` to `"buy" | "sell"`.
- Rename direction-specific CSS custom properties to `--side-buy` and `--side-sell`.
- Update direction-specific comments and tests where they explain forex side-of-book behavior.
- Preserve protocol, gateway, and journal contracts already using `buy | sell`.
- Leave non-trading uses of the words long/short unchanged.

## Files

- Modify relevant files under `app/src/`.
- Modify `README.md` and maintained documentation under `docs/` where semantic direction wording
  remains.
- Modify gateway comments/tests only where long/short names trading direction.

## Implementation

1. Rename UI sample values, labels, component props, and style tokens.
2. Rename direction-specific local variables and test descriptions without changing calculations.
3. Update maintained documentation to state buy/sell terminology.
4. Scan for remaining semantic occurrences and classify any retained matches as ordinary English.

## Validation

- Focused terminology scan.
- `npm test` in `app/`.
- `npm run typecheck` in `app/`.
- `npm run build` in `app/`.
- Focused gateway tests if executable Python files change.

## Risks and rollback

- Risk: broad text replacement could corrupt ordinary English or unrelated identifiers such as
  navigation `short` labels. Mitigation: edit only classified direction occurrences.
- Risk: token renames could leave unresolved CSS variables. Mitigation: scan old and new token names,
  then build.
- Rollback: revert only the terminology-specific files; no persisted data or external contract changes.

