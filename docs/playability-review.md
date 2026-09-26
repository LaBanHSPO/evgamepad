# Playability review, 26 September 2026

The biggest obstacle was telling a working demo-account desk apart from prototype screens. The first-run route showed fixed scores, an example plan and a claimed live connection. That could make a new player trust information that did not belong to their account.

## Changes made

| Finding | Change |
|---|---|
| First run led through fixed-data screens | Start now offers a local controls lesson and a clearly separate demo desk. Original artboards remain labeled as samples. |
| No place to practise cancelling or closing without setup | Five steps teach unlock, cancel, confirm, close and sit out. Mouse, keyboard and controller use the existing control state machine. No network client is used by the lesson. |
| Holding RT before arming could submit immediately | Arming now requires a subsequent confirm press. Regression coverage includes held and simultaneous inputs. |
| LT and B in the same frame could miss SELL | The clutch state now determines whether B prepares SELL. |
| Connection sent subscriptions while the socket was still opening | Subscriptions and position snapshots now follow connection opening in both demo-desk implementations. |
| Leaving the main desk did not close its socket; pending retries could reopen it | Unmount disconnects. Disconnect cancels reconnect timers and removes socket callbacks. |
| Offline actions could become deferred requests | New offline intents are ignored. Only previously sent, unresolved requests retain their IDs for reconnect. |
| Unlocking could bypass the local unresolved-request phase | The agent checks the outstanding-request ledger before sending a new entry. Exit requests remain available. |
| View only changed the local lock | Explicit lock/unlock now sends the existing gateway session message. |
| Closing with no position could leave the controller waiting forever | The agent returns to idle without sending a request when no position exists. The desk disables that close button. |
| Every subscribed market could overwrite the selected price | The desk caches quotes by symbol and renders only the selected market. Prices older than five seconds are hidden and labeled. This display threshold does not replace gateway risk checks. |
| R values assumed a fixed 20 USD unit | The desk reads the configured risk unit from the gateway and shows unavailable when it cannot be verified. |
| Failed check-in/checklist saves could appear successful | Success messages now require successful HTTP responses. |
| Menu mixed account screens and prototype actions | Samples have their own group. The menu supports keyboard focus, wraps on narrow screens and scrolls its selected destination into view. |

## Checked locally

- Production build, TypeScript checking and protocol schema check.
- Frontend automated tests covering the lesson, held-confirm protection, pending-request guard, connection timing and reconnect cancellation.
- Chrome: full five-step mouse walkthrough with a simulated SELL and close, then sit-out completion.
- Chrome: disconnected demo desk, dummy-token connection failure, retry controls, disabled order/preview actions while disconnected.
- Layout inspection at the normal desktop viewport and a 390px viewport.

## Still needs an account and physical hardware

No cTrader credentials or demo orders were used during this review. This work does not claim a completed broker release gate.

Check physical 8BitDo detection, the complete demo-account entry/exit sequence, broker rejection messages, a connection drop with an unresolved request, and the positions reported after reconnect. Also test that leaving the desk stops controller input while any existing demo positions remain visible in cTrader.

The original sample screens are still prototypes. Their controls, account status and scores are examples, even when they look interactive. The local lesson measures completion of control actions, not trading ability or future returns.
