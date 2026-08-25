---
title: "Phase 5: Ubuntu Docker deploy"
status: todo
phase: 5
priority: P1
effort: 7h
dependencies: [2, 3, 4]
---

# Phase 5: Ubuntu Docker deploy

## Overview

Put **docker compose** on the existing Ubuntu VPS. Existing TLS on 443 reverse-proxies to `127.0.0.1:8444`. `ev-exec` has no published ports. This is not an MT5 stub phase. cTrader is already live from phase 2; this phase is production packaging, Origin, secrets, and runbook.

## Context Links

- [plan.md](./plan.md)
- [cTrader research](./research/researcher-05-ctrader-docker.md)

## Requirements

- Functional: inspect VPS OS/region and the **live** TLS terminator; write them into `deploy/README.md`
- Functional: `docker compose up -d` on Ubuntu 22.04/24.04
- Functional: compose publishes **only** `127.0.0.1:8444:8444` for gateway
- Functional: `ev-exec` :9101 on the internal network only
- Functional: gateway serves `apps/web/dist` at `/` and the game socket at `/ws`; the existing 443 vhost proxies both to `127.0.0.1:8444`. One origin, one Origin-allowlist entry
<!-- Updated: Validation Session 2 - no phase served the built SPA; copilot is not a service -->
- Functional: volumes for sqlite journal + OAuth refresh token + voice audio archive + whisper models
- Functional: **record the CPU probe** into `deploy/README.md` — `nproc`, `lscpu | grep -E 'Model name|avx2'`, `free -m`, `df -h`. Phase 8's model tier and the decision to keep whisper as a gateway subprocess both hang on it. Expected: 4+ vCPU / 4 GB+, which selects `small.en`
- Functional: run `deploy/fetch-models.sh` once on the box so `small.en` lands in the journal volume; the baked `tiny.en` floor means voice still works if this fails
<!-- Updated: Validation Session 4 - phase 8 needs the model on the box and the probe recorded -->
- Functional: `restart: unless-stopped`; healthchecks
- Functional: live host / live account still cannot start
- Non-functional: no CDN on the execution WebSocket
- Non-functional: no Windows, no Wine, no `ctrader-console-docker` (that is not Open API)

## Architecture

```
Internet --TLS--> host :443 (existing caddy/nginx)
                    → 127.0.0.1:8444  ev-gateway   ( / = HUD build, /ws = game socket )
                         ├─ copilot child process
                         └─ whisper.cpp child (batch, nice + taskset, concurrency 1)
                         → ev-exec:9101
                              → demo.ctraderapi.com:5035
```

Firewall: 443 + SSH. Drop 8444 from WAN (loopback bind).

## Related Code Files

- Modify: `compose.yaml` (prod env_file, volumes, logging)
- Create: `deploy/reverse-proxy.md` (nginx **or** Caddy snippet after inspect)
- Create: `deploy/README.md` (OAuth, 2FA TV webhook, 8BitDo, dual-screen)
- Modify: `.env.example`

## Implementation Steps

1. Inspect Ubuntu version, compose plugin, existing 443 vhost.
2. Build `apps/web`; bake `dist` into the gateway image. Fill `public_origin`. Add proxy location; do not steal 443.
3. Copy env (never commit). `compose up`. Confirm spots from home Chrome.
4. Reboot VPS; stack returns; cTrader session re-auths; open position still matches `Reconcile`.
5. CPU probe recorded in `deploy/README.md`; `deploy/fetch-models.sh` run once; confirm the gateway
   logs the selected whisper tier at boot rather than degrading silently.
6. Runbook: evening start (compose ps, Chrome, pad dongle, TV on other screen, webhook URL).

## Todo

- [ ] Inspect VPS + terminator
- [ ] Loopback publish only
- [ ] Reverse proxy snippet
- [ ] Reboot restore + Reconcile
- [ ] CPU probe recorded; whisper tier logged at boot
- [ ] `deploy/fetch-models.sh` run once; models in the volume
- [ ] Runbook README

## Success Criteria

- [ ] From the Mac, Chrome WSS to the VPS **cTrader-demo-trades** with the 8BitDo
- [ ] Loading `https://<origin>/` in Chrome serves the HUD and its `/ws` connects with no cross-origin exception
- [ ] `docker compose ps` healthy after reboot
- [ ] `ss -lntp` shows 8444 on 127.0.0.1 only
- [ ] Live credentials cannot start the stack
- [ ] Deploy README has no secrets
- [ ] `deploy/README.md` records `nproc` / AVX2 / RAM / disk, and the gateway boot log names the
      selected whisper tier
- [ ] Deleting the model volume still leaves voice working on the baked `tiny.en` floor

## Risk Assessment

- **Existing terminator is not Caddy** — inspect first; snippet for nginx and Caddy.
- **Spotware IP blocked by VPS firewall** — allow egress 5035.
- **Clock drift vs session window** — container `TZ` is not the session TZ; session uses config IANA.
- **Box is smaller than stated** — signal: `nproc` reports 1. Response: whisper as a gateway
  subprocess is only defensible at 2+ cores because `taskset` is what protects the order path. On a
  single core, revisit the two-service decision in favour of an STT service with a hard `cpus` quota.

## Security Considerations

- Rotate `EV_WS_TOKEN` and `TV_WEBHOOK_SECRET`.
- cTrader tokens never in the browser.
- Webhook path rate-limited.

## Next Steps

Play an evening. Phase 6 turns those evenings into a process scoreboard. Do not add a second broker.
