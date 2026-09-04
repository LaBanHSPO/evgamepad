/**
 * The order finite state machine.
 *
 * Firing takes two hands: the clutch held *and* a confirm rising edge *and* an armed side. There
 * is no countdown, and no analog axis reaches this machine — a stick cannot submit an order, by
 * construction rather than by threshold.
 *
 * `confirmHoldMs` is a parameter of the fire predicate, not a new state, so phase 9's friction is
 * a config change and this file's tests stay valid.
 */

import { clutchEngaged } from "./map";

export type Phase = "LOCKED" | "IDLE" | "CLUTCH" | "ARMED" | "FIRE" | "UNKNOWN";

/** What an armed side will do when confirmed. */
export type Side = "buy" | "sell" | "close" | "panic";

/** Sides that open exposure. These are the only ones any gate may ever block. */
const OPENING_SIDES: ReadonlySet<Side> = new Set<Side>(["buy", "sell"]);

export interface PadInput {
  /** Continuous clutch reading, already resolved from LT or the L4 alias. */
  clutch: number;
  /** Confirm, already resolved from RT or the R4 alias. */
  confirm: boolean;
  /** Edge-detected face buttons. */
  a: boolean;
  b: boolean;
  x: boolean;
  y: boolean;
  view: boolean;
  menu: boolean;
  lotUp: boolean;
  lotDown: boolean;
  symbolLeft: boolean;
  symbolRight: boolean;
  /** Tab focus and pad presence. Either going false cancels immediately. */
  visible: boolean;
  padConnected: boolean;
  nowMs: number;
}

export interface FsmOptions {
  /** 0 means a rising edge fires. Phase 9 raises it to add friction to opens only. */
  confirmHoldMs?: number;
  /** How long a FIRE may stay unacknowledged before the cid is treated as unknown. */
  fireTimeoutMs?: number;
}

export interface FsmState {
  phase: Phase;
  side: Side | null;
  /** Pong-corrected moment the side was armed; travels with the intent. */
  armedAt: number | null;
  clutchHeld: boolean;
  confirmDownAt: number | null;
  firedAt: number | null;
  pendingCid: string | null;
  overlayOpen: boolean;
}

export type Effect =
  | { kind: "intent"; side: Side; armedAt: number }
  | { kind: "cancel"; reason: string }
  | { kind: "rumble"; pattern: "arm" | "fire" | "reject" }
  | { kind: "lot"; step: 1 | -1 }
  | { kind: "symbol"; step: 1 | -1 }
  | { kind: "lock"; locked: boolean }
  | { kind: "transition"; from: Phase; to: Phase; reason: string };

export interface StepResult {
  state: FsmState;
  effects: Effect[];
}

export const initialState: FsmState = {
  phase: "LOCKED",
  side: null,
  armedAt: null,
  clutchHeld: false,
  confirmDownAt: null,
  firedAt: null,
  pendingCid: null,
  overlayOpen: false,
};

const DEFAULTS: Required<FsmOptions> = { confirmHoldMs: 0, fireTimeoutMs: 5000 };

function armedFrom(input: PadInput): Side | null {
  if (input.a) return "buy";
  if (input.b) return "sell";
  if (input.x) return "close";
  if (input.y) return "panic";
  return null;
}

/**
 * The fire predicate. Held long enough, clutched, and armed — all three, every time.
 *
 * With `confirmHoldMs === 0` this is a plain rising edge: `confirmDownAt` is set on the frame the
 * button goes down, so the same frame already satisfies the hold.
 */
export function canFire(state: FsmState, input: PadInput, confirmHoldMs: number): boolean {
  if (state.phase !== "ARMED" || state.side === null) return false;
  if (!state.clutchHeld || !input.confirm) return false;
  if (state.confirmDownAt === null) return false;
  return input.nowMs - state.confirmDownAt >= confirmHoldMs;
}

/** One frame. Pure: same state and input always give the same result. */
export function step(state: FsmState, input: PadInput, options: FsmOptions = {}): StepResult {
  // Spreading would let an explicit `undefined` from a caller clobber the default and disable
  // every fire, so each option falls back individually.
  const confirmHoldMs = options.confirmHoldMs ?? DEFAULTS.confirmHoldMs;
  const fireTimeoutMs = options.fireTimeoutMs ?? DEFAULTS.fireTimeoutMs;
  const effects: Effect[] = [];
  let next: FsmState = { ...state };

  const move = (phase: Phase, reason: string): void => {
    if (next.phase === phase) return;
    effects.push({ kind: "transition", from: next.phase, to: phase, reason });
    next.phase = phase;
  };

  const cancel = (reason: string): void => {
    if (next.phase === "ARMED" || next.phase === "CLUTCH") {
      effects.push({ kind: "cancel", reason });
    }
    next.side = null;
    next.armedAt = null;
  };

  // Clutch hysteresis first: everything below reads the resolved boolean.
  next.clutchHeld = clutchEngaged(input.clutch, state.clutchHeld);

  // Confirm edge tracking, so a button already down when ARMED is reached cannot fire.
  if (input.confirm && state.confirmDownAt === null) {
    next.confirmDownAt = input.nowMs;
  } else if (!input.confirm) {
    next.confirmDownAt = null;
  }

  // Losing focus or the pad cancels immediately — not on the next poll.
  if (!input.visible || !input.padConnected) {
    cancel(!input.visible ? "hidden" : "pad_disconnected");
    next.clutchHeld = false;
    if (next.phase !== "FIRE" && next.phase !== "UNKNOWN") move("LOCKED", "focus_lost");
    return { state: next, effects };
  }

  // Non-order controls work in every phase that is not mid-fire. They never touch the broker.
  // While the overlay is open the D-pad belongs to destination selection, not lot/symbol.
  if (next.phase !== "FIRE" && !next.overlayOpen) {
    if (input.lotUp) effects.push({ kind: "lot", step: 1 });
    if (input.lotDown) effects.push({ kind: "lot", step: -1 });
    if (input.symbolLeft) effects.push({ kind: "symbol", step: -1 });
    if (input.symbolRight) effects.push({ kind: "symbol", step: 1 });
  }

  // Opening the overlay cancels any arm and hard locks new opens.
  if (input.menu) {
    next.overlayOpen = !next.overlayOpen;
    if (next.overlayOpen) {
      cancel("overlay_opened");
      if (next.phase === "ARMED" || next.phase === "CLUTCH") move("IDLE", "overlay_opened");
    }
  }

  if (input.view) {
    const locked = next.phase !== "LOCKED";
    effects.push({ kind: "lock", locked });
    move(locked ? "LOCKED" : "IDLE", "view_toggle");
    cancel("view_toggle");
    return { state: next, effects };
  }

  switch (next.phase) {
    case "LOCKED":
      // Only the View tap above leaves LOCKED. Nothing else here can reach the broker.
      break;

    case "FIRE": {
      if (state.firedAt !== null && input.nowMs - state.firedAt >= fireTimeoutMs) {
        // The cid is outstanding. New opens stay blocked until it resolves; exits do not.
        move("UNKNOWN", "fire_timeout");
      }
      break;
    }

    case "UNKNOWN":
    case "IDLE":
    case "CLUTCH":
    case "ARMED": {
      if (next.phase === "IDLE" && input.b) {
        cancel("b_while_idle");
        break;
      }

      if (!next.clutchHeld) {
        cancel("clutch_up");
        if (next.phase === "CLUTCH" || next.phase === "ARMED") {
          move(state.phase === "UNKNOWN" ? "UNKNOWN" : "IDLE", "clutch_up");
        }
        break;
      }

      if (next.phase === "IDLE" || next.phase === "UNKNOWN") {
        if (!next.overlayOpen) move(next.phase === "UNKNOWN" ? "UNKNOWN" : "CLUTCH", "clutch_down");
      }

      const side = armedFrom(input);
      if (side !== null && (next.phase === "CLUTCH" || next.phase === "UNKNOWN")) {
        // An outstanding cid blocks new exposure; it never blocks an exit.
        if (next.phase === "UNKNOWN" && OPENING_SIDES.has(side)) break;
        if (next.overlayOpen) break;
        next.side = side;
        next.armedAt = input.nowMs;
        effects.push({ kind: "rumble", pattern: "arm" });
        move("ARMED", `arm_${side}`);
      }

      if (canFire(next, input, confirmHoldMs)) {
        effects.push({ kind: "intent", side: next.side as Side, armedAt: next.armedAt as number });
        effects.push({ kind: "rumble", pattern: "fire" });
        next.firedAt = input.nowMs;
        // The arm is spent the moment it fires. Leaving it set would let a stale side survive a
        // fire timeout and read as a live arm in UNKNOWN.
        next.side = null;
        next.armedAt = null;
        move("FIRE", "confirm");
      }
      break;
    }
  }

  return { state: next, effects };
}

/** The broker answered. A resolved cid clears an outstanding fire, ack or reject alike. */
export function resolve(state: FsmState, ok: boolean): StepResult {
  const effects: Effect[] = [];
  if (!ok) effects.push({ kind: "rumble", pattern: "reject" });
  effects.push({ kind: "transition", from: state.phase, to: "IDLE", reason: ok ? "ack" : "reject" });
  return {
    state: { ...state, phase: "IDLE", side: null, armedAt: null, firedAt: null, pendingCid: null },
    effects,
  };
}

/** The socket dropped. Lock the client, and keep any outstanding cid — never mint a new one. */
export function onSocketClose(state: FsmState): FsmState {
  return { ...state, phase: state.phase === "FIRE" ? "UNKNOWN" : "LOCKED", side: null, armedAt: null };
}
