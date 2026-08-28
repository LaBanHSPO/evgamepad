# story.md — the talk track

A twelve-minute walkthrough of the evgamepad mockups, written to be spoken.
Screen ids in brackets are the option badges on the canvas — click them or use the `#` links.

Before you start: open `evgamepad Mockups.dc.html`, zoom out until you can see a full turn,
and park on `5a`. Say the demo line once at the top and once at the end. Never in between —
it lands harder as bookends than as a disclaimer you keep repeating.

---

## 0 · Cold open — 30 seconds

> This is a game you play with a controller.
> It trades gold and forex on a broker demo account.
> And the thing it grades is not the money.

Pause there. Let the second and third sentences sit apart.

> Everything you are about to see is planning, not a shipped product. The repository is fourteen
> phase specifications and no application code yet. These twenty-three screens are what the
> specifications look like when you draw them.

Say that early. It buys you honesty credit for the whole rest of the talk, and it is the same
move the product makes on every one of its own screens.

---

## 1 · The problem it treats — 1 minute

Show **`1i`** — the HUD.

> Look at what is biggest on this screen after the price.

Wait for someone to find it.

> It is the number of trades this player refused. Four arms cancelled. Green, and it counts upward.
> Open profit is over here, in risk units, and dollars are behind a deliberate toggle.

> The reason is not modesty. Watching the money while a position is open pulls your attention off
> the decision you are in the middle of making. So the interface makes the decision loud and the
> money quiet.

Land on:

> Most trading software is built to make you look at the money. This one is built to make you
> look at what you did.

---

## 2 · The one boundary — 90 seconds

Show **`5a`** — the evening as one flow.

> Six stages, and one rule that holds through all of them.

Point at the amber lane.

> Exactly one component in this system is allowed to approve an order: the gateway. The controller
> prepares an intent. The AI coach can read everything and place nothing. Voice can record a memo
> and cannot navigate a menu, let alone fire.

> That is not a policy in a document. A config that puts the AI on the order path exits at boot.
> So does a live account, a live broker endpoint, and cloud transcription.

> Border style carries it visually, straight from the architecture diagram — solid amber can
> approve or block an order, dashed can never place one. You will see dashed borders all evening
> on the AI desk and the journal.

Land on:

> Every dangerous thing in this product is prevented by something that refuses to start,
> not by someone remembering.

---

## 3 · One evening, end to end — 3 minutes

Stay on `5a` and walk the six rows. Jump into a screen only where it earns the detour.

**First run — `2a`.**
> Paste the token, wake the pad, verify the account is a demo, optionally turn on the mic.
> Then look at the right-hand column: the boot log tells you what the machine actually found.
> That amber line is the calibration probe reporting that the paddles never moved, so the pad
> legend stays on the triggers all evening. It is not an error. It is the system being specific.

**Prepare — `4a`.**
> Four market clocks on real timezone data, five readiness questions, a position-size calculator,
> and your own written analysis. One readiness item is left unanswered on purpose — unanswered is
> not the same as no, and the score counts what you actually recorded.

**Play — `1i`, then `1d`.**
> Clutch with the left trigger, arm with A or B, confirm with the right trigger. Two hands, always.
> Menu opens one safe overlay — and opening it cancels your arm and locks new opens, because
> navigating and trading should never be the same gesture.

**The checklist — `3a`.**
> Three taps after the trade. One yes, one no in amber, one skipped. Look at the bottom right:
> the skip shrank the denominator to two of three. A skipped question does not score zero.

**Close — `2b`.**
> This is my favourite screen. The evening is over and the score slot does not contain a number.
> It says review processing, lists which two inputs are still landing, and refuses to write a
> partial score as final. Click the chip and it settles to ninety-eight.

**Review — `1a`.**
> The replay. Scrub your own trade back through the tape with the left stick. And look at the
> decision ledger: the second row is an arm you cancelled forty seconds before you fired.
> Standing down is in the record as an event, not as a gap in it.

---

## 4 · The score that rewards standing down — 2 minutes

Show **`1j`** — the deck on a stood-down evening.

> Read the line first.

> "You watched a dead tape for three hours and did not trade it."

> That evening scores a hundred. A busy, well-executed evening scores ninety-eight.

Let that be uncomfortable for a second, then explain it.

> Five axes, all process: adherence, selectivity, risk discipline, preparation, review. No win rate.
> No profit factor. With zero trades, two of those axes have no denominator at all — so instead of
> scoring them zero, which would punish discipline, or a hundred, which would be free points,
> they are dropped and the remaining weights renormalise. The radar shows them as a dashed
> not-applicable ring.

> And it is not a free lunch. Freezing in a rich tape scores seventy. Overtrading a dead tape
> scores sixty-five. Timidity is treated as a smaller mistake than recklessness, which is a
> deliberate opinion the system is willing to hold.

Land on:

> There are no streaks, no levels, no badges, and nothing that accumulates across sessions.
> Every mechanic that would create pressure to trade a dead evening is deliberately absent.

---

## 5 · Where the trust comes from — 90 seconds

Show **`2c`** — the honesty matrix.

> Twelve ways this thing can fail, and the exact words it prints for each one.

Read two aloud, no more.

> Transcription dies: "transcript failed — audio kept." The recording is still stored, still linked
> to the trade, still plays in the replay. The record survives the transcription.

> Fewer than five sessions: "not enough sessions yet." It will not print a confident number from
> three samples.

> Notice what is not on this board. Nothing is styled as a red error, because none of it is the
> player's fault. Amber is information. Green is a refusal working as designed.

Land on:

> A tool you are using to judge your own decisions has to be honest about its own. Otherwise you
> are calibrating against a flatterer.

---

## 6 · What it is actually for — 1 minute

Show **`1c`** — mistake trends and principles.

> The headline is a sentence, not a score. "Set the stop before the fire, not after it."
> Underneath, how many times it happened, with the sample size, going down from seven to one.

> On the right, principles the player wrote themselves — and each one carries its evidence.
> The first one quotes their own voice memo back at them: "I armed because it moved, not because
> it set up."

> That is the product. Not signals. Not a win rate. A record honest enough that you start trusting
> your own judgement, with the receipts to justify it.

---

## 7 · Close — 30 seconds

> Demo only. Not advice. Process over outcome.

> The stated goal in the repository is confidence and enjoyment — improving decision quality,
> not the money. Every screen you have seen is that sentence, enforced.

Stop talking there. Do not add a summary.

---

## If they ask

**"Does it make money?"**
> That is deliberately not the claim, and there is no page in the product that would let me answer
> it well. The Outcome tab has return, profit factor and drawdown, and it is behind a click you
> have to make on purpose. Sharpe currently prints "not enough sessions yet" at twenty-one sessions.

**"Why a controller?"**
> Two reasons. It forces two-handed intent — clutch and confirm, so nothing fires from one twitch.
> And the pad is already telling us how the player is doing: clutch cycles, arm flips, lot
> escalation, how fast they re-entered after a loss. That is measured behaviour, not a mood survey
> filled in afterwards.

**"So it detects tilt?"**
> It measures behaviour and names it — "re-entered forty seconds after a loss." Two rules keep it
> honest. Tilt is never an input to the score, because taxing the evening would reintroduce the
> punishment the whole design exists to avoid. And tilt can only ever slow down an opening trade.
> It can never delay a close, a panic flatten, or a session lock. That is a boot-fail too.

**"Is the AI trading?"**
> No, and it cannot be made to. It has eleven read-only tools and no place, close, modify or write
> tool exists in the schema. Show them `3c`.

**"Can I see the code?"**
> Not yet — that is the honest answer. The repository is planning complete and implementation has
> not started. These are the specifications drawn.

---

## Do not say

- Do not call it a trading system, a strategy, or an edge.
- Do not say any number here is real performance. It is fixture data on a demo account.
- Do not promise a date. The plan is 203 hours across fourteen phases and phase one has not landed.
- Do not describe tilt detection as reading emotion. It reads button behaviour.
- Do not use the word "just" about any safety mechanism.

---

## Timing

| Beat | Minutes |
|---|---|
| Cold open | 0.5 |
| The problem | 1.0 |
| The boundary | 1.5 |
| One evening | 3.0 |
| The score | 2.0 |
| Honesty | 1.5 |
| What it is for | 1.0 |
| Close | 0.5 |
| **Total** | **11.0** |

Leaves four minutes for questions in a fifteen-minute slot.

If you only get five minutes: `1i` for the refusal counter, `1j` for the hundred-point flat
evening, `2c` for the honesty. That is the whole argument in three screens.
