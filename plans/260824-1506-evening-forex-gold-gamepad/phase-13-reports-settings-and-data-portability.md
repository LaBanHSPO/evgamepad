---
title: "Phase 13: Reports Settings and Data Portability"
status: todo
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

- Create: `apps/gateway/src/db/migrations/010-settings-data.sql`
- Create: `apps/gateway/src/settings/schema.ts`
- Create: `apps/gateway/src/settings/routes.ts`
- Create: `apps/gateway/src/reports/routes.ts`
- Create: `apps/gateway/src/data/export.ts`
- Create: `apps/gateway/src/data/backup.ts`
- Create: `apps/gateway/src/data/restore.ts`
- Create: `apps/gateway/src/data/delete.ts`
- Create: `apps/gateway/src/data/backup.test.ts`
- Create: `apps/gateway/src/data/restore.test.ts`
- Create: `apps/web/src/settings/Settings.svelte`
- Create: `apps/web/src/reports/ReportBuilder.svelte`
- Create: `apps/web/src/reports/report-print.css`
- Create: `apps/web/src/settings/DataManagement.svelte`
- Modify: `apps/web/src/App.svelte` (settings/report routes)
- Modify: `apps/web/src/game-overlay/GameOverlay.svelte` (settings/report destinations)
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

- [ ] Safe settings schema + desktop dark-only UI
- [ ] Single account identity read-only; no secrets/safety toggles
- [ ] Process-first report builder + browser PDF
- [ ] Streamed CSV and JSON exports
- [ ] Manifested backup excluding secrets/models
- [ ] Staged atomic restore + rollback
- [ ] Explicit delete-all flow
- [ ] Backup/restore round-trip and corruption tests
- [ ] README data-management runbook

## Success Criteria

- [ ] `/settings` cannot change demo/live mode, account credentials, bind address, or tool permissions
- [ ] No light theme or mobile-only layout is introduced
- [ ] A monthly report saves as a readable PDF with process pages first and Outcome optional
- [ ] CSV and JSON exports contain requested journal data and zero secret/env/path values
- [ ] Backup includes DB, tapes, voice, and chart attachments but excludes models and credentials
- [ ] A corrupt checksum, traversal path, unsupported schema, active position, or busy background job
      rejects restore before current data changes
- [ ] Successful restore reproduces row counts and attachment hashes from the backup manifest
- [ ] Delete-all cannot run during a session and leaves no DB journal rows or retained user media
- [ ] No MT5, broker-history, CSV, or general trade import endpoint exists

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
