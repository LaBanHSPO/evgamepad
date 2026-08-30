/**
 * LB/RB arbitration: a timeframe change, or a push-to-talk chord.
 *
 * The two cannot be told apart at press time -- the second bumper may be a few
 * frames behind the first -- so a single bumper fires its timeframe change **on
 * release**, and only if the other bumper was never down during that press.
 * Both bumpers inside CHORD_WINDOW_MS is push-to-talk, and suppresses both
 * timeframe actions.
 *
 * Getting this wrong costs a chart zoom, never a position: neither bumper is on
 * the order path, and PTT is a parallel machine that emits no order transition
 * (see `ptt.ts`).
 */

import { CHORD_WINDOW_MS } from "./map";

export type ChordState = {
  lbDownAt: number | null;
  rbDownAt: number | null;
  /** Set when a press has been claimed by the chord and must not fire on release. */
  lbConsumed: boolean;
  rbConsumed: boolean;
  pttActive: boolean;
};

export function initialChord(): ChordState {
  return {
    lbDownAt: null,
    rbDownAt: null,
    lbConsumed: false,
    rbConsumed: false,
    pttActive: false,
  };
}

export type ChordEvent =
  | { kind: "none" }
  | { kind: "timeframe"; direction: -1 | 1 }
  | { kind: "ptt"; phase: "begin" | "end" };

export type Bumpers = { lb: boolean; rb: boolean };

export function stepChord(
  state: ChordState,
  prev: Bumpers,
  next: Bumpers,
  now: number,
  windowMs = CHORD_WINDOW_MS,
): { state: ChordState; event: ChordEvent } {
  const s: ChordState = { ...state };

  if (!prev.lb && next.lb) {
    s.lbDownAt = now;
    s.lbConsumed = false;
  }
  if (!prev.rb && next.rb) {
    s.rbDownAt = now;
    s.rbConsumed = false;
  }

  // Both down close together -> chord. Marking both consumed is what stops the
  // releases from also emitting two timeframe changes.
  if (
    !s.pttActive &&
    next.lb &&
    next.rb &&
    s.lbDownAt !== null &&
    s.rbDownAt !== null &&
    Math.abs(s.lbDownAt - s.rbDownAt) <= windowMs
  ) {
    s.pttActive = true;
    s.lbConsumed = true;
    s.rbConsumed = true;
    return { state: s, event: { kind: "ptt", phase: "begin" } };
  }

  // PTT ends when either bumper comes up: a chord is held with both.
  if (s.pttActive && (!next.lb || !next.rb)) {
    s.pttActive = false;
    if (!next.lb) s.lbDownAt = null;
    if (!next.rb) s.rbDownAt = null;
    return { state: s, event: { kind: "ptt", phase: "end" } };
  }

  if (prev.lb && !next.lb) {
    const consumed = s.lbConsumed;
    s.lbDownAt = null;
    s.lbConsumed = false;
    if (!consumed && !s.pttActive) return { state: s, event: { kind: "timeframe", direction: -1 } };
  }
  if (prev.rb && !next.rb) {
    const consumed = s.rbConsumed;
    s.rbDownAt = null;
    s.rbConsumed = false;
    if (!consumed && !s.pttActive) return { state: s, event: { kind: "timeframe", direction: 1 } };
  }

  return { state: s, event: { kind: "none" } };
}
