# Practise, connect, review

Open the game in desktop Chrome. The start screen offers two paths:

- **Start practice:** a guided controls lesson. No gateway, token, controller, or account is required.
- **Open demo desk:** connect the configured cTrader demo account. This needs the gateway, its session token, and a controller for entries.

## First session: learn the controls

Choose **Start practice**, press Enter, or press Start on the controller.

1. **Unlock:** tap View. This does not submit anything.
2. **Cancel:** hold LT, tap A to prepare BUY, then release LT. Nothing opens.
3. **Confirm:** hold LT, tap A for BUY or B for SELL, read the armed side, then press RT.
4. **Close:** hold LT, tap X, then press RT. The simulated position closes.
5. **Sit out:** click **Sit out this setup**, or release LT and tap A. Choosing to wait is part of the lesson.

The lesson uses the same control rules as the demo desk, but all results stay in the browser. It does not send orders, generate prices, calculate profit, or write to your journal.

In **Mouse / keyboard** mode, click the buttons. LT is a toggle for this lesson only. On a physical controller, hold LT down.

| Keyboard key in practice | Action |
|---|---|
| V | Unlock / lock |
| Hold Shift | Hold LT |
| A / B | Prepare BUY / SELL |
| X / Y | Prepare close / close all |
| Enter | Confirm when focus is outside a button |
| M / Escape | Open the menu and pause |

When a button has keyboard focus, Enter and Space activate that button normally. Shortcuts are ignored while writing a note.

Choose **Controller** to use the pad in practice. Set it to XInput, connect the dongle or USB cable, then press a button. If the controller is not detected, return to mouse controls.

There is no time limit. Pausing locks the controls and keeps the current lesson step. Leaving the lesson resets it. The optional reflection note clears when you leave.

## Connect your demo account

1. Configure and run the Python gateway using the [project setup instructions](../../README.md#local-development).
2. Open **Demo desk** and paste the gateway's `EV_WS_TOKEN`. This is not your cTrader password. The token stays in memory and clears when you leave the desk.
3. Choose **Connect demo account**. Check the separate connection, broker, price and session-window indicators. A gateway connection alone does not prove the broker is ready.
4. Connect the controller, press a button, then tap View to unlock.
5. Check the selected symbol, lot size and gateway limits. **Check BUY rules** and **Check SELL rules** show previews. Those buttons do not place orders.

If connection fails, check the gateway and token. The retry control remains available. Requests already sent keep their original IDs during automatic reconnection. Do not repeat an entry whose result is unresolved; check the positions in cTrader.

## Controller {#controller}

| Input on the demo desk | Action |
|---|---|
| View | Unlock / lock |
| Hold LT, then A | Prepare BUY |
| Hold LT, then B | Prepare SELL |
| RT after arming, with LT held | Submit the prepared action |
| Release LT before confirming | Cancel the prepared action |
| Hold LT, then X, then RT | Close the active position |
| Hold LT, then Y, then RT | Request closure of all positions |
| D-pad left / right | Select symbol |
| D-pad up / down | Change lot size |
| LB / RB | Change timeframe |
| Menu / Start | Open the navigation menu |

RT must be released and pressed again if it was already held when you armed. Holding it early cannot skip the preview.

The on-screen close buttons submit exit requests directly when connected. They do not require a controller. Check the broker response before treating a position as closed. If the connection is unavailable, manage positions in cTrader.

The navigation keyboard shortcuts do not place demo-account orders. Entries on the demo desk require the physical controller.

## Build confidence through a small routine

Before a session, choose one thing to practise: cancelling calmly, checking size, or following your written plan. You do not need a profit target or a minimum trade count.

Afterwards, note one action you handled well and one to practise next. Use **My journal** and **My process review** for gateway-backed records. A successful controls lesson does not predict trading results.

**Leave desk & review** disconnects the controls and opens the journal. It does not close positions or claim to finalize a session. Close positions and verify the result first if that is your intention.

## Every screen {#screens}

Use **Menu** or the left navigation rail:

- **Play:** start screen, controls practice, demo desk, and the existing matrix/city demo desks.
- **Review:** your journal, process review, reports and recorded trade replay. These require gateway data.
- **Settings:** preferences, data management and your principles.
- **Sample screens:** the original artwork and prototype walkthrough. A yellow notice labels their sample account status, plans, limits, trades and scores. These examples are not your results.

The sample boot and pre-session screens do not verify a broker connection or save limits. The sample session-clear screen does not end a connected account session.

## Verification limits

The browser lesson works without an account. Actual controller detection, demo fills, broker rejections, reconnect recovery and exits must also be checked with your physical controller and configured cTrader demo gateway.
