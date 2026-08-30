/**
 * Push-to-talk: a machine that runs *beside* the order FSM and never inside it.
 *
 * Two structural rules, not conventions:
 *  - PTT is enterable only from IDLE or LOCKED, so a memo can never begin while
 *    a fire is being set up.
 *  - Entering CLUTCH stops the memo by submitting what exists rather than
 *    discarding it -- the player reached for the clutch, they did not ask to
 *    lose the last four seconds of thinking.
 *
 * Phase 3 owns the control event only. No microphone is acquired, nothing is
 * recorded, and no transcript is produced until phase 8.
 */

import type { FsmState } from "./fsm";

export type PttState = {
  active: boolean;
  startedAt: number | null;
  /** Set once phase 8 attaches a recorder. Phase 3 leaves it false. */
  recording: boolean;
};

export function initialPtt(): PttState {
  return { active: false, startedAt: null, recording: false };
}

export type PttEvent =
  | { kind: "none" }
  | { kind: "begin"; at: number }
  | { kind: "submit"; at: number; reason: "released" | "clutch" }
  | { kind: "refused"; from: FsmState };

export function canEnterPtt(state: FsmState): boolean {
  return state === "IDLE" || state === "LOCKED";
}

export function beginPtt(ptt: PttState, fsmState: FsmState, now: number): { ptt: PttState; event: PttEvent } {
  if (ptt.active) return { ptt, event: { kind: "none" } };
  if (!canEnterPtt(fsmState)) {
    return { ptt, event: { kind: "refused", from: fsmState } };
  }
  return { ptt: { active: true, startedAt: now, recording: false }, event: { kind: "begin", at: now } };
}

export function endPtt(
  ptt: PttState,
  now: number,
  reason: "released" | "clutch" = "released",
): { ptt: PttState; event: PttEvent } {
  if (!ptt.active) return { ptt, event: { kind: "none" } };
  return { ptt: initialPtt(), event: { kind: "submit", at: now, reason } };
}

/**
 * Reaching for the clutch during a memo is a graceful stop-and-submit, not a
 * discard. Returns the submit event so the caller can hand it to phase 8.
 */
export function onClutchDuringPtt(ptt: PttState, now: number): { ptt: PttState; event: PttEvent } {
  return endPtt(ptt, now, "clutch");
}
