---
title: "Phase 13: Reports Settings and Data Portability"
status: in-progress
phase: 13
priority: P1
effort: 18h
dependencies: [12]
---

# Phase 13: Reports Settings and Data Portability

## Overview

Make the single-account journal operable for the long term: safe settings, printable reports,
portable exports, complete backup/restore, and an explicit delete-all path. Desktop Chrome and dark
theme remain the product boundary.

## Context Links

- [plan.md](./plan.md)
- [Phase 1 — safety config and deployment shape](./phase-01-repo-protocol-docker-config.md)
- [Phase 7 — playbook settings](./phase-07-playbook-and-trade-grading.md)
- [Phase 12 — complete journal cockpit](./phase-12-daily-journal-cockpit-and-preparation.md)

## Requirements

### Settings boundary

- Functional: `/settings` edits safe preferences only: enabled symbols within the server allowlist,
  chart timeframes, evening schedule/timezone, gamepad calibration, rumble, mic/PTT, TTS, journal
  retention, and report defaults.
- Functional: the configured cTrader account is a read-only identity. No second account can be
  added and no broker credentials, live-mode switch, secrets, bind address, or AI order permission
  appear in the UI.
- Functional: playbook editing links to phase 7; philosophy/principles links to phase 12. Do not
  duplicate either editor.
- Functional: migration `010-settings-data.sql` owns validated user preferences and data-operation
  audit rows. Hard safety invariants remain YAML/env boot-fails, not mutable database preferences.
- Non-functional: dark theme only; no light-mode toggle. Desktop layout only; no mobile trading or
  mobile journal commitment.

### Reports and exports

- Functional: report builder selects week, month, custom period, or one session and includes a
  process-first cover, heatmap, Process Score, adherence, mistakes, playbook/setup cuts, and an
  optional Outcome appendix.
- Functional: PDF export uses a dedicated print stylesheet and the browser's Save as PDF flow. No
  Chromium/Puppeteer binary is added to the VPS.
- Functional: streamed CSV export contains trade facts and flattened review dimensions; streamed
  JSON export contains sessions, plans, grades, reviews, scores, analyses, and attachment metadata.
- Non-functional: exports never include env values, OAuth/WS/webhook/API tokens, raw config secrets,
  or absolute VPS paths.

### Backup, restore, delete

- Functional: backup creates a manifest-versioned archive from a consistent SQLite backup plus
  voice audio, chart attachments, and trade tapes. Whisper models, Docker images, caches, `.env`,
  and tokens are excluded because they are replaceable or secret.
- Functional: every archive member has path, size, and SHA-256 in the manifest; archive creation is
  streamed with a temporary size cap and cleans partial files after failure.
- Functional: restore is allowed only while the session is locked, no position is open, and no
  transcription/tape job is running. Validate manifest, checksums, schema compatibility, and archive
  paths before changing current data.
- Functional: restore creates a short-lived pre-restore rollback snapshot, migrates a staged copy,
  atomically swaps it into place, verifies counts, then removes the rollback snapshot only after
  success. Failure leaves current data untouched.
- Functional: delete-all requires the exact confirmation phrase plus a two-second gamepad/keyboard
  hold, refuses while a position or session is active, deletes DB rows/audio/attachments/tapes, and
  vacuums storage. Config, models, app binaries, credentials, and one content-free action/time/count
  audit record remain; no journal content or personal note remains.
- Functional: the UI offers backup before delete but never creates a hidden recovery copy after the
  final confirmation.
- Non-functional: restore of this app's own backup is supported; cTrader/MT5/broker-history import is
  explicitly out of scope.

## Architecture

```text
/settings -> validated safe preferences -> settings table
/reports  -> existing journal queries -> print stylesheet -> browser Save as PDF
/api/export/* -> streamed CSV / JSON
/api/data/backup -> SQLite snapshot + media -> manifest archive
/api/data/restore -> validate -> stage -> migrate -> atomic swap
/api/data/all -> confirmed delete while locked
```

## Related Code Files

- Create: `apps/gateway/db/migrations/010-settings-data.sql`
- Create: `apps/gateway/settings/schema.py`
- Create: `apps/gateway/settings/routes.py`
- Create: `apps/gateway/reports/routes.py`
- Create: `apps/gateway/data/export.py`
- Create: `apps/gateway/data/backup.py`
- Create: `apps/gateway/data/restore.py`
- Create: `apps/gateway/data/delete.py`
- Create: `apps/gateway/data/test_backup.py`
- Create: `apps/gateway/data/test_restore.py`
- Create: `apps/web/src/settings/Settings.tsx`
- Create: `apps/web/src/reports/ReportBuilder.tsx`
- Create: `apps/web/src/reports/report-print.css`
- Create: `apps/web/src/settings/DataManagement.tsx`
- Modify: `apps/web/src/App.tsx` (settings/report routes)
- Modify: `apps/web/src/game-overlay/GameOverlay.tsx` (settings/report destinations)
- Modify: `README.md` (backup/restore/export/delete runbook)

## Implementation Steps

1. Add safe-preference schemas, migration, routes, and hard rejection of secret/safety keys.
2. Build desktop dark-only settings, reusing playbook/system editors by link.
3. Build report query composition and print stylesheet; verify browser Save as PDF.
4. Add streaming CSV and JSON exports with secret/path redaction tests.
5. Implement consistent backup archive, manifest, checksums, caps, and partial cleanup.
6. Implement staged restore, schema migration, atomic swap, verification, and rollback.
7. Implement delete-all safety gate and storage cleanup.
8. Run backup -> mutate disposable data -> restore -> compare counts/checksums round-trip.

## Todo

- [x] Safe settings schema + desktop dark-only UI
- [x] Single account identity read-only; no secrets/safety toggles
- [x] Process-first report builder + browser PDF
- [x] Streamed CSV and JSON exports
- [x] Manifested backup excluding secrets/models
- [x] Staged atomic restore + rollback
- [x] Explicit delete-all flow
- [x] Backup/restore round-trip and corruption tests
- [x] README data-management runbook

## Success Criteria

- [x] `/settings` cannot change demo/live mode, account credentials, bind address, or tool permissions
- [x] No light theme or mobile-only layout is introduced
- [x] A monthly report saves as a readable PDF with process pages first and Outcome optional
- [x] CSV and JSON exports contain requested journal data and zero secret/env/path values
- [x] Backup includes DB, tapes, voice, and chart attachments but excludes models and credentials
- [x] A corrupt checksum, traversal path, unsupported schema, active position, or busy background job
      rejects restore before current data changes
- [x] Successful restore reproduces row counts and attachment hashes from the backup manifest
- [x] Delete-all cannot run during a session and leaves no DB journal rows or retained user media
- [x] No MT5, broker-history, CSV, or general trade import endpoint exists

## Verification Status

Gateway `uv run pytest -q`: **525 passed, 1 skipped** (the skip is phase 2's broker volume test,
still waiting on a real cTrader dump); `uv run ruff check .` clean. Web `npm test`: **182 passed**
(19 new); `npx tsc --noEmit` and `npm run build` clean.

| Claim | Proof |
|---|---|
| No setting can reach a safety property | Two independent nets: an allowlist, and `FORBIDDEN_SEGMENTS`/`FORBIDDEN_PHRASES` checked at **construction**, so `broker.mode`, `gateway.bind`, `broker.client_secret`, `copilot.on_hot_path`, `tilt.gate_close` and `tradingview.auto_trade` all fail at import rather than at runtime. `test_defining_a_dangerous_setting_fails_at_construction` asserts each one |
| An unknown key is refused, not ignored | The whole batch rejects; a test sends one good key with one bad one and asserts the good half was **not** applied. A silently dropped write is a setting the player thinks they changed |
| The symbol list narrows but never widens | The validator takes the server's own symbol set; `BTCUSD` is refused with the reason |
| The UI offers nothing the gateway would refuse | `settings.test.ts` asserts the form is generated from `view.schema`, and that the page mentions no live/bind/credential/boot-fail control and has no account `<select>` |
| Exports carry no secret and no path | Built from explicit column allowlists; a test greps every export for the redaction list, for the literal temp path, and for the token planted in `secure/` |
| The backup excludes the tokens and the models | Asserted against the real archive's member list *and* its concatenated bytes — the planted `super-secret` string is absent |
| A capped backup leaves nothing behind | The archive, the `.partial`, and the staging directory are all asserted gone after the failure |
| The snapshot is consistent | Taken through `sqlite3.Connection.backup()` while an open write transaction is in flight |
| Restore refuses before touching anything | Separate tests for an unlocked session, an open position, a running job, a corrupt checksum, a traversal path, a symlink member, an undeclared member, a missing member, a newer manifest, unknown migrations, a decompression bomb, a non-archive, and a missing file — each asserting the current journal afterwards |
| The round trip reproduces counts and hashes | The journal is genuinely moved on (trades deleted, analysis rewritten, the PNG overwritten) before the restore, so a no-op restore cannot pass |
| Delete needs all four conditions | Each is asserted to refuse individually, with the journal intact after all four refusals |
| Delete leaves one content-free audit row | The row is asserted to carry only `rows`/`files`/`tables` and not to contain the planted note text |
| Nothing is copied aside after the final confirmation | `delete.py` is greped (docstrings stripped) for `create(`, `backup(`, `snapshot_db`, `copytree`, `copy2` |
| No import path exists | Every data module is greped for `mt5`, `metatrader`, `broker_history`, `import_trades`, `csv_import`; the UI is greped for `/api/import` and `upload` |
| Process pages lead the report | `PROCESS_ONLY_KEYS` pins the exact key set when the appendix is off, and the cover is asserted money-free in **both** configurations |
| PDF is the browser's own | `window.print()` over a print stylesheet; the builder is greped for puppeteer/playwright/chromium/jspdf/html2canvas |

## Deviations

- **A settings key/value table, with the validation in code.** The plan says the migration "owns
  validated user preferences". Validation lives in `settings/schema.py` rather than in SQL because
  a `CHECK` constraint cannot express "an IANA zone this machine can resolve" or "engage above
  release", and — more importantly — because adding a row must not be the same act as adding a
  setting. The table is dumb on purpose; the allowlist is the gate.
- **The segment guard, learned twice.** `FORBIDDEN_SEGMENTS` matches whole dot/underscore segments
  rather than substrings, because `report.default_period` contains "port" and a guard that rejects
  the report defaults is a guard nobody keeps. This is the same fix phase 12's `key_levels` forced
  on phase 11's schema guard; it is now the house pattern.
- **Two exceptions were escaping `inspect()`.** A missing manifest member raised `KeyError` and a
  missing file raised `FileNotFoundError`, both of which would have surfaced as a 500 rather than
  a refusal with a reason. Found by the tests, fixed in `restore.py` and `backup.py`.
- **`settings/routes.py`, `reports/routes.py` and `data/*` routes are registered in `main.py`.**
  The same call phases 10, 11 and 12 made: repositories and builders in their own modules, routes
  where every other route in this build lives.
- **The report is served as data and rendered by the client.** The plan implies a server-rendered
  print surface; splitting it means the print stylesheet lives with the component that uses it and
  the same JSON is reusable. The "process first" ordering is enforced on **both** sides — the
  gateway does not assemble the outcome section unless asked, and the CSS puts the cover on its own
  page.
- **Print is the one place the product is not dark-only.** A black A4 page is unreadable and wastes
  a cartridge, so `@media print` inverts to ink. The screen theme is untouched, and a test asserts
  the inversion appears nowhere outside the print block.
- **Attachments were already excluded from backup by construction, not by filter.** `MEDIA_DIRS` is
  an allowlist of two directories; `secure/` and `models/` are not "filtered out", they were never
  candidates. `EXCLUDED` documents why, and the test reads both.
- **Restore's readiness is declared by the caller.** The gateway has no cross-request view of an
  open position, so `locked`, `positionsOpen` and `jobsRunning` arrive in the request. That is
  honest about where the check happens — and the delete gate's phrase and hold are re-checked
  server-side regardless, so the destructive path is never protected by the client alone.

## Risk Assessment

- **Restore destroys good data** — signal: row/hash mismatch after swap. Response: stage and verify;
  atomic swap only after validation; rollback snapshot retained until post-swap checks pass.
- **Backup leaks secrets** — signal: env key or absolute path appears in archive search. Response:
  explicit allowlist, redaction test, and manifest built from logical names only.
- **Large archive exhausts VPS disk** — signal: temp usage crosses configured cap. Response: stream,
  preflight free space, stop at cap, and remove partial archive.
- **Settings weaken safety** — signal: UI payload contains `mode`, host, secret, bind, or tool keys.
  Response: strict allowlist schema; hard config stays outside the database.

## Security Considerations

- Restore rejects absolute paths, `..`, symlinks, duplicate members, decompression bombs, and
  unexpected MIME/types before extraction.
- Backup download and destructive routes require the existing bearer plus recent re-auth/confirmation.
- Data-operation audit rows contain action/time/counts only, never secrets or deleted content.

## Next Steps

Phase 14 proves the entire first-run-to-recovery journey on real demo infrastructure and hardware.
