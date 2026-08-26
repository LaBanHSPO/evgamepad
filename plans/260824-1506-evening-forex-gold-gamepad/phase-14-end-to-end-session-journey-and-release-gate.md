---
title: "Phase 14: End-to-End Session Journey and Release Gate"
status: todo
phase: 14
priority: P1
effort: 14h
dependencies: [13]
---

# Phase 14: End-to-End Session Journey and Release Gate

## Overview

Prove one complete evening on the target Mac, 8BitDo, Ubuntu VPS, and IC Markets cTrader demo:
first-run setup, preparation, safe execution, session close, journal review, export, backup/restore,
and recovery from the failures that matter. No feature is considered complete only because its
isolated phase test passes.

## Context Links

- [plan.md](./plan.md)
- [Phase 5 — deployed runtime](./phase-05-ubuntu-docker-deploy.md)
- [Phase 12 — journal cockpit](./phase-12-daily-journal-cockpit-and-preparation.md)
- [Phase 13 — reports and data portability](./phase-13-reports-settings-and-data-portability.md)

## Requirements

### Journey contract

1. **First run:** open the same-origin app, paste the memory-only WS token, connect/calibrate the
   2.4G pad, verify demo account/feed, optionally enable mic, and inspect readiness.
2. **Prepare:** complete or skip the advisory checklist, write daily analysis, inspect news/calendar,
   choose a playbook, calculate size, and acknowledge the session plan.
3. **Play:** preview relative SL/TP and R, clutch+confirm a demo market order, stage an SL/TP edit in
   the locked overlay and confirm it with LT+RT after returning to the game, record a memo, receive
   async coach text, then close or panic without AI/voice/tilt delaying the exit.
4. **Close:** lock the session, finish post check-in/checklist, allow pending tape/STT jobs to settle,
   and compute the auditable Process Score. UI shows `review processing` until dependencies settle;
   it never writes a partial score as final.
5. **Review:** open the day heatmap, trade detail, Actual vs Plan, mistake trend, replay, and the
   process-first deck. Verify Outcome remains behind its tab.
6. **Own the data:** export CSV/JSON, save a PDF, create a backup, restore it into a disposable data
   volume, compare manifest/counts, then exercise delete-all only on that disposable volume.

### Automated gates

- Functional: one deterministic browser suite covers overlay navigation, hidden-tab lock, relative
  SL/TP preview, no accidental fire, journal routes, report printing, and data-management guards.
- Functional: gateway integration suite uses recorded official-shaped protocol fixtures for failure
  branches but the release smoke uses the real cTrader demo account; no fake matcher or fake P/L.
- Functional: protocol/config/migration tests run from a fresh database through migration 010 and
  from a restored older backup through the same target version.
- Functional: failure matrix covers feed stale, WS reconnect with unknown cid, cTrader maintenance,
  calendar offline, AI offline, mic denied, whisper killed, full attachment disk, corrupt backup,
  and browser hidden/unplugged.
- Functional: accessibility gate covers keyboard-only overlay/data management, focus trapping,
  visible focus, form labels, status announcements, and reduced motion on the dark desktop UI.

### Manual target-environment gates

- Functional: 8BitDo 2.4G primary and wired fallback both complete calibration, open, amend, close,
  panic, overlay navigation, PTT, and replay controls in focused desktop Chrome.
- Functional: measure pad->intent, home->VPS, gateway risk, cTrader ack, whisper RTF, and order-ack
  p99 during transcription. Record actual values; do not rewrite the plan to claim the target passed.
- Functional: reboot VPS with no position, then with a demo position, and verify compose recovery,
  OAuth refresh, reconcile, journal consistency, and safe UI state.
- Non-functional: release remains single-account, cTrader-demo-only, desktop, dark-only. Any live
  endpoint/account still boot-fails.

## Architecture

```text
FIRST RUN -> PREPARE -> LIVE SESSION -> CLOSE/SETTLE -> DAILY REVIEW -> EXPORT/BACKUP
    |            |            |              |               |              |
 pad/feed     checklist    real demo      score final      replay       restore drill
 calibration analysis     SL/TP amend    only when ready   mistakes     disposable volume
```

## Related Code Files

- Create: `tests/e2e/first-run-session-review.spec.ts`
- Create: `tests/e2e/failure-degradation.spec.ts`
- Create: `tests/e2e/data-portability.spec.ts`
- Create: `tests/e2e/accessibility.spec.ts`
- Create: `tests/smoke/real-demo-session.md` (manual evidence checklist, no secrets)
- Create: `scripts/verify-release.sh`
- Create: `docs/release-checklist.md`
- Modify: `deploy/README.md` (complete evening and recovery runbook)
- Modify: `README.md` (verified journey and known empirical limits)

## Implementation Steps

1. Add a journey state contract so first-run, preflight, live, closing, processing, and review have
   explicit transitions and recovery states.
2. Build the deterministic browser/integration suites around real contracts and recorded fixtures.
3. Add fresh/install/upgrade/restore migration gates and data-portability corruption cases.
4. Run the complete target-hardware demo journey and record measurements without secrets.
5. Run the degradation matrix; fix plan-scope defects rather than weakening assertions.
6. Run reboot/reconcile and disposable backup/restore/delete drills.
7. Produce the release checklist with passed evidence, empirical values, and any blocked criterion.

## Todo

- [ ] Journey states + review-processing semantics
- [ ] Browser happy-path E2E
- [ ] Failure/degradation E2E
- [ ] Migration + restore compatibility gate
- [ ] Accessibility gate
- [ ] 2.4G and wired manual matrix
- [ ] Real cTrader demo order/SLTP/close/panic smoke
- [ ] Whisper load and latency measurements
- [ ] VPS reboot/reconcile drill
- [ ] Export/PDF/backup/restore/delete disposable drill
- [ ] Release checklist and runbook

## Success Criteria

- [ ] A new user can complete first run through reviewed session without an undocumented step
- [ ] One real demo trade records plan, relative SL/TP, fill, amendment, close, grade, memo, tape,
      score, review, mistake evidence, and exports under the same `cid`/session
- [ ] Menu overlay navigation/apply never emits open/modify; dedicated close/panic still work, and
      broker-changing SL/TP apply still requires LT+RT
- [ ] With AI, calendar, mic, or whisper unavailable, demo execution and manual journal remain usable
- [ ] With tilt forced to 1.0 or the browser hidden/unplugged, close and panic remain available
- [ ] Backup/restore round-trip matches manifest/counts; corrupt restore leaves current data untouched
- [ ] Delete-all works only on the locked disposable profile and leaves no user journal/media data
- [ ] Fresh DB and restored older backup both reach migration 010 without manual SQL
- [ ] All automated gates pass; all target-hardware manual gates have dated evidence
- [ ] Any unresolved empirical target is reported as blocked, never silently accepted

## Risk Assessment

- **Test harness proves a simulator, not the product** — signal: release passes without Spotware or
  the target pad. Response: deterministic fixtures cover failures; the release smoke requires the
  real demo account and hardware.
- **Session closes before async artifacts settle** — signal: final score/replay misses memo or tape.
  Response: explicit processing state, idempotent recompute, and timeout with visible pending items.
- **Destructive drill touches primary data** — signal: delete route points at the normal volume.
  Response: disposable compose project/volume with a visible environment assertion; never run the
  delete drill against the primary journal.

## Security Considerations

- Evidence and runbooks redact origin tokens, account IDs where unnecessary, local paths, and logs.
- E2E secrets come from env/CI secret storage and are never saved in traces, screenshots, or videos.
- Release script refuses live host/account and refuses destructive data tests without the disposable
  profile marker.

## Next Steps

After this gate is green, implementation is ready for code review and shipping. Until then, the
plan remains incomplete even if phases 1–13 are individually checked.
