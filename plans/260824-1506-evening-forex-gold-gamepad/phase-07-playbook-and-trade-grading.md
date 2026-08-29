---
title: "Phase 7: Playbook, rule registry, and trade grading"
status: todo
phase: 7
priority: P1
effort: 12h
dependencies: [2, 3, 4]
---

# Phase 7: Playbook, rule registry, and trade grading

## Overview

TradeZella's best idea, on a gamepad: a **playbook** is a named setup with explicit rules, every
fire is **graded** against the playbook that was active when it fired, and the grade is visible in
the confirm overlay **before you commit**. Per-playbook statistics then answer "which of my setups
actually works" instead of "how did I do".

The rule that keeps this honest: **risk rules are enforced, playbook rules are graded.** Both come
from one registry so they cannot drift, but a player-authored playbook rule can never become a
trade blocker.

## Context Links

- [plan.md](./plan.md)
- [Phase 2 — risk rules are exported, not private](./phase-02-ctrader-exec-and-socket-gateway.md)
- [Phase 3 — confirm overlay and safe GameOverlay navigation](./phase-03-web-game-and-8bitdo-client-agent.md)
- [Phase 4 — Volman M5 detectors emit setup tags](./phase-04-ai-desk-sentinel-news-volman.md)
- [Phase 6 — adherence reuses one rule set](./phase-06-performance-and-psychology-deck.md)

## Requirements

### Rule registry (one definition, two consequences)

- Functional: `apps/gateway/method/rules.py` exports a registry of
  `{ code, label, scope: 'risk' | 'playbook', kind: 'auto' | 'manual', evaluate(ctx) -> { ok, actual, expected } }`
- Functional: phase 2 `risk/rules.py` imports the `scope: 'risk'` subset and **enforces** it — a failing
  risk rule rejects the intent server-side, exactly as it does today
- Functional: grading imports the whole registry and **scores** it; the phase 11 deck extension
  consumes these grades. Phase 6's already-delivered risk adherence remains unchanged
- Non-functional: a `scope: 'playbook'` rule **never** rejects an intent. Assert it in a test —
  this is the failure mode that would silently turn the journal into a trade blocker
- Non-functional: phase 2 keeps enforcing what it enforces today; this phase changes where the
  rules live, not which ones bite

### Playbook

- Functional: `playbook(id, name, slug UNIQUE, method, symbols JSON, detector_tag, narrative, active, created_at, retired_at)`;
  `method` is `volman_m5` or `custom`; `narrative` is player prose
- Functional: `playbook_rule(id, playbook_id, ord, kind, code, params JSON, label, required)`;
  `code` references a registry entry, `params` parameterises it, `required` rules gate `clean`
- Functional: seed playbooks from the phase 4 Volman detectors (range box, break, pullback test,
  false break, block break) so the player starts with a real book, not an empty one
- Functional: playbooks are editable at `/playbooks` (same origin) and selectable from the phase 3
  GameOverlay's Playbook destination; D-pad selects and A applies. The active playbook is part of
  session state. No `Menu + D-pad` shortcut exists outside the overlay
- Functional: retiring a playbook sets `retired_at` and hides it from selection; historical grades
  keep resolving, so the deck never loses a month

### Grading

- Functional: `trade_grade(cid PK, playbook_id, evaluated_at, results JSON, required_pass, required_total, clean)`
- Functional: keyed on **`cid` (one fire)**, not on a closed position — declines and rejects are
  gradeable too, and the phase 6 declined-count depends on that
- Functional: `auto` rules evaluate at ARM against live context (price, EMA20, ATR, spread, session
  clock, sentinel state, open positions) and re-evaluate at FIRE; the ARM result drives the overlay
- Functional: `manual` rules ("I waited for the retest") are answered by a **3-tap post-trade
  checklist** on close. Skipping marks them `unknown` — excluded from `required_total`, so a skip is
  neither pass nor fail and never costs the player anything
- Functional: no playbook selected -> graded against the implicit `__unplanned__` playbook (risk
  rules only), which reads honestly as "unplanned" on the deck
- Functional: `grade` message pushed on the `session` channel at ARM and at FIRE
- Non-functional: grading is a **pure function over context**; no LLM grades a trade

## Architecture

```
apps/gateway/method/rules.py   registry: code -> evaluate(ctx)
        |                    \
   scope:'risk'               scope:'playbook' + all
        |                              |
  gateway risk/rules.py               grading/grade.py
  ENFORCE (reject)              SCORE (never rejects)
                                       |
                        trade_grade row + `grade` WS message
                                       |
                          ARM confirm overlay  /  phase 6 deck  /  phase 9 tilt
```

The confirm overlay is where this feature earns its keep:

```
BUY 0.10 XAUUSD @ 2345.12
[M5 second-chance break]  4/5 rules OK  ·  ✗ price > 1.5 ATR from EMA20
```

## Related Code Files

- Create: `apps/gateway/method/rules.py` (registry + `evaluate` implementations)
- Create: `apps/gateway/method/test_rules.py` (each rule against fixtures; playbook rules never reject)
- Create: `apps/gateway/grading/grade.py` (evaluate a playbook against context, write `trade_grade`)
- Create: `apps/gateway/grading/test_grade.py` (unplanned fallback, unknown manual answers, low-N)
- Create: `apps/gateway/grading/routes.py` (`GET|POST /api/playbooks`, `POST /api/playbooks/:id/retire`)
- Create: `apps/gateway/grading/seed.py` (Volman starter playbooks)
- Create: `apps/gateway/db/migrations/005-playbooks.sql`
- Create: `apps/web/src/playbook/PlaybookEditor.tsx`
- Create: `apps/web/src/playbook/PlaybookPicker.tsx` (pad-driven inside GameOverlay)
- Create: `apps/web/src/playbook/PostTradeChecklist.tsx` (3-tap, skippable)
- Modify: `apps/gateway/risk/rules.py` (import the registry instead of inlining rules)
- Modify: `apps/web/src/hud/ConfirmOverlay.tsx` (render the live grade)
- Modify: `apps/gateway/journal/writer.py` (playbook, playbook_rule, trade_grade writes)
- Modify: `config/default.yaml` (`playbook.*`)
- Modify: `README.md` (what a playbook is; risk vs playbook rules)

## Implementation Steps

1. Extract the registry from phase 2's `risk/rules.py`; make `risk/rules.py` import it. Existing risk tests must
   pass untouched — that is the proof the extraction was behaviour-preserving.
2. Add `scope: 'playbook'` rules and the assertion test that they cannot reject an intent.
3. Apply `005-playbooks.sql` + seed the Volman starter playbooks.
4. `grade.py` pure evaluation; fixture tests including `__unplanned__`.
5. Wire ARM/FIRE grading into the gateway; push `grade` on `session`.
6. Confirm overlay renders the grade; GameOverlay Playbook destination owns selection.
7. Post-trade checklist on close, skippable, `unknown` on skip.
8. `/playbooks` editor, same origin, escaped player text.

## Todo

- [ ] Rule registry extracted; risk/rules.py imports it; existing tests green
- [ ] Playbook rules provably cannot reject an intent
- [ ] `005-playbooks.sql` + Volman starter seed
- [ ] Grading pure functions + fixtures
- [ ] `grade` at ARM and FIRE
- [ ] Confirm overlay shows the grade before commit
- [ ] GameOverlay playbook picker; no competing Menu shortcut
- [ ] Post-trade checklist, skip = unknown
- [ ] `/playbooks` editor

## Success Criteria

- [ ] The confirm overlay names the active playbook and shows `n/m rules OK` **before** the fire
- [ ] A failing **playbook** rule still lets the trade through; a failing **risk** rule still rejects it
- [ ] Firing with no playbook selected produces an `__unplanned__` grade, not a crash and not a block
- [ ] Skipping the post-trade checklist leaves `unknown`, and `required_total` shrinks accordingly
- [ ] A cancelled ARM during a stand-down still writes a `trade_grade` row (phase 6 counts it)
- [ ] Retiring a playbook keeps last month's deck numbers resolving
- [ ] `risk/rules.py` contains no rule logic of its own — only registry calls

## Risk Assessment

- **A playbook rule silently blocks a fire** — signal: an intent rejected with a rule code whose
  scope is `playbook`. Response: the scope split is asserted in a test, not just documented.
- **Rule extraction changes what the gateway enforces** — signal: a phase 2 risk test fails.
  Response: extract first, add playbook rules second; the phase 2 suite is the regression gate.
- **The editor becomes a config chore nobody uses** — signal: only `__unplanned__` grades after two
  weeks. Response: ship real Volman starter playbooks; the empty state is the failure state.
- **Checklist fatigue** — signal: `unknown` on every manual rule. Response: 3 taps, skippable,
  never penalised; the same mitigation phase 6 applies to the check-in.
- **ARM-time context differs from FIRE-time context** — signal: overlay said 5/5, grade says 4/5.
  Response: store both evaluations; the FIRE grade is authoritative, the ARM grade is advisory.

## Security Considerations

- `narrative`, `label`, and playbook names are player text: escape, never `{@html}`.
- `/api/playbooks*` is same-origin behind the existing token; no new public surface.
- Rule `params` are validated against the registry entry's schema before they are stored.

## Next Steps

Phase 9 consumes grades as tilt's rule-break signal. Phase 11 consumes them as the score's
Adherence axis.
