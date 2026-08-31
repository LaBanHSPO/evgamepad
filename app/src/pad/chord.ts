/**
 * Bumper arbitration: `LB + RB` is push-to-talk, a single bumper is a timeframe change.
 *
 * Both are non-order inputs, so a misfire costs a chart zoom and never a position. The cost of
 * getting it wrong is still real — the chart jumping every time you start a memo — so a single
 * bumper fires **on release**, and only when the other bumper was never down during that press.
 *
 * PTT is a parallel machine. It emits no order transition, it is enterable only from `IDLE` or
 * `LOCKED`, and reaching `CLUTCH` stops it gracefully rather than discarding what was said.
 */

import { CHORD_WINDOW_MS } from "./map";
import type { Phase } from "./fsm";

/** The order phases in which starting to talk is allowed at all. */
const PTT_PHASES: ReadonlySet<Phase> = new Set<Phase>(["IDLE", "LOCKED"]);

export interface ChordInput {
  lb: boolean;
  rb: boolean;
  /** Keyboard `V`, an equal-status fallback for the chord. */
  key: boolean;
  phase: Phase;
  nowMs: number;
}

export interface ChordState {
  lbDownAt: number | null;
  rbDownAt: number | null;
  /** Set once a press is claimed by the chord; that press can no longer change the timeframe. */
  lbClaimed: boolean;
  rbClaimed: boolean;
  ptt: boolean;
}

export type ChordEffect =
  | { kind: "timeframe"; step: 1 | -1 }
  | { kind: "ptt"; active: true }
  /** `submit` distinguishes a graceful stop from a discard — a clutch never throws away a memo. */
  | { kind: "ptt"; active: false; submit: boolean };

export const initialChordState: ChordState = {
  lbDownAt: null,
  rbDownAt: null,
  lbClaimed: false,
  rbClaimed: false,
  ptt: false,
};

export interface ChordResult {
  state: ChordState;
  effects: ChordEffect[];
}

export function stepChord(state: ChordState, input: ChordInput): ChordResult {
  const effects: ChordEffect[] = [];
  const next: ChordState = { ...state };

  const lbEdge = input.lb && state.lbDownAt === null;
  const rbEdge = input.rb && state.rbDownAt === null;
  if (lbEdge) {
    next.lbDownAt = input.nowMs;
    next.lbClaimed = false;
  }
  if (rbEdge) {
    next.rbDownAt = input.nowMs;
    next.rbClaimed = false;
  }

  const bothDown = input.lb && input.rb;
  const withinWindow =
    next.lbDownAt !== null &&
    next.rbDownAt !== null &&
    Math.abs(next.lbDownAt - next.rbDownAt) <= CHORD_WINDOW_MS;

  const wantsPtt = (bothDown && withinWindow) || input.key;

  if (wantsPtt && !next.ptt && PTT_PHASES.has(input.phase)) {
    next.ptt = true;
    // Both presses now belong to the chord; neither may change the timeframe on release.
    next.lbClaimed = true;
    next.rbClaimed = true;
    effects.push({ kind: "ptt", active: true });
  } else if (wantsPtt && !next.ptt) {
    // Refused because the order machine is armed or mid-fire. Still claim the presses: the player
    // meant to talk, not to zoom the chart.
    next.lbClaimed = next.lbClaimed || bothDown;
    next.rbClaimed = next.rbClaimed || bothDown;
  }

  if (next.ptt && !PTT_PHASES.has(input.phase)) {
    // The clutch came down mid-memo: stop and submit what exists rather than discarding it.
    next.ptt = false;
    effects.push({ kind: "ptt", active: false, submit: true });
  } else if (next.ptt && !wantsPtt) {
    next.ptt = false;
    effects.push({ kind: "ptt", active: false, submit: true });
  }

  // Timeframe fires on release, and only for a press the chord never claimed.
  if (!input.lb && state.lbDownAt !== null) {
    if (!next.lbClaimed) effects.push({ kind: "timeframe", step: -1 });
    next.lbDownAt = null;
    next.lbClaimed = false;
  }
  if (!input.rb && state.rbDownAt !== null) {
    if (!next.rbClaimed) effects.push({ kind: "timeframe", step: 1 });
    next.rbDownAt = null;
    next.rbClaimed = false;
  }

  return { state: next, effects };
}
