/**
 * The order state machine.
 *
 * Firing takes two hands: the clutch held, an armed side, and a *rising edge*
 * on confirm. Every rule that stops an accidental order lives here, so it can
 * be tested without a browser, a pad, or a socket:
 *
 *  - A held button cannot spray orders. Only a rising edge arms or fires, and
 *    FIRE leaves the armed state immediately.
 *  - An analog stick can never fire. Sticks are not inputs to this machine at
 *    all; they reach the SL/TP preview and nothing else.
 *  - Losing the tab, the pad, or the clutch cancels the arm on the spot, rather
 *    than on the next poll.
 *
 * `confirmHoldMs` is a parameter of the fire predicate, not a state. Phase 9's
 * tilt friction raises it; the machine gains no states and these tests stay
 * valid.
 */

export type FsmState = "LOCKED" | "IDLE" | "CLUTCH" | "ARMED" | "FIRE";

/** What an ARM is pointed at. CLOSE and PANIC are safety exits. */
export type ArmSide = "buy" | "sell" | "close" | "panic";

export type Inputs = {
  clutch: boolean;
  confirm: boolean;
  armBuy: boolean;
  armSell: boolean;
  armClose: boolean;
  armPanic: boolean;
  /** `View` taps toggle the session lock. */
  toggleLock: boolean;
  /** `Menu` opens the safe overlay: cancels ARM and locks new opens. */
  overlay: boolean;
  visible: boolean;
  padConnected: boolean;
};

export const NO_INPUT: Inputs = {
  clutch: false,
  confirm: false,
  armBuy: false,
  armSell: false,
  armClose: false,
  armPanic: false,
  toggleLock: false,
  overlay: false,
  visible: true,
  padConnected: true,
};

export type Fsm = {
  state: FsmState;
  side: ArmSide | null;
  /** Wall-clock ms the current ARM began, or null. Sent as `armedAt`. */
  armedAt: number | null;
  /** Wall-clock ms the confirm button went down, for `confirmHoldMs`. */
  confirmDownAt: number | null;
  /** True while the overlay is open: new opens are hard locked. */
  overlayOpen: boolean;
  /** Set when a fire is in flight and its cid is unresolved. */
  pendingCid: string | null;
};

export function initialFsm(): Fsm {
  return {
    state: "LOCKED",
    side: null,
    armedAt: null,
    confirmDownAt: null,
    overlayOpen: false,
    pendingCid: null,
  };
}

export type Transition =
  | { kind: "none" }
  | { kind: "arm"; side: ArmSide }
  | { kind: "cancel"; reason: CancelReason }
  | { kind: "fire"; side: ArmSide; armedAt: number }
  | { kind: "lock" }
  | { kind: "unlock" }
  | { kind: "overlay"; open: boolean };

export type CancelReason =
  | "clutch_released"
  | "confirm_released"
  | "hidden"
  | "pad_lost"
  | "overlay_opened"
  | "locked"
  | "b_pressed";

export type Options = {
  /**
   * How long confirm must be held before a fire counts. 0 is a rising edge,
   * which is the default and what the pad feels like. Phase 9 raises it.
   */
  confirmHoldMs?: number;
  /** A fire is refused while a previous cid is unresolved. */
  fireBlocked?: boolean;
};

export type StepResult = { fsm: Fsm; transition: Transition };

/** Rising edge helper: true only on the frame an input goes false -> true. */
function rose(prev: boolean, next: boolean): boolean {
  return !prev && next;
}

/**
 * Advance one frame. Pure: same inputs, same result, so the whole safety story
 * is a table of assertions rather than a manual test with a real pad.
 */
export function step(
  fsm: Fsm,
  prev: Inputs,
  next: Inputs,
  now: number,
  options: Options = {},
): StepResult {
  const { confirmHoldMs = 0, fireBlocked = false } = options;

  // Losing the tab or the pad cancels immediately and unconditionally. This is
  // checked before anything else so no ordering of other inputs can outrank it.
  if (!next.visible || !next.padConnected) {
    const reason: CancelReason = !next.visible ? "hidden" : "pad_lost";
    if (fsm.state === "ARMED" || fsm.state === "CLUTCH") {
      return {
        fsm: { ...fsm, state: "LOCKED", side: null, armedAt: null, confirmDownAt: null },
        transition: { kind: "cancel", reason },
      };
    }
    if (fsm.state !== "LOCKED") {
      return { fsm: { ...fsm, state: "LOCKED", side: null, armedAt: null }, transition: { kind: "lock" } };
    }
    return { fsm, transition: { kind: "none" } };
  }

  // Menu is a safe surface, but opening it must not leave a live ARM behind.
  if (rose(prev.overlay, next.overlay)) {
    const wasArmed = fsm.state === "ARMED";
    const open = !fsm.overlayOpen;
    const cleared: Fsm = {
      ...fsm,
      overlayOpen: open,
      state: open ? (fsm.state === "LOCKED" ? "LOCKED" : "IDLE") : fsm.state,
      side: null,
      armedAt: null,
      confirmDownAt: null,
    };
    if (open && wasArmed) {
      return { fsm: cleared, transition: { kind: "cancel", reason: "overlay_opened" } };
    }
    return { fsm: cleared, transition: { kind: "overlay", open } };
  }

  if (rose(prev.toggleLock, next.toggleLock)) {
    if (fsm.state === "LOCKED") {
      return { fsm: { ...fsm, state: "IDLE" }, transition: { kind: "unlock" } };
    }
    return {
      fsm: { ...fsm, state: "LOCKED", side: null, armedAt: null, confirmDownAt: null },
      transition: { kind: "lock" },
    };
  }

  if (fsm.state === "LOCKED") return { fsm, transition: { kind: "none" } };

  // Track the confirm press time so a hold threshold can be measured without
  // adding a state to the machine.
  let confirmDownAt = fsm.confirmDownAt;
  if (rose(prev.confirm, next.confirm)) confirmDownAt = now;
  if (!next.confirm) confirmDownAt = null;

  if (fsm.state === "IDLE") {
    if (next.clutch) {
      return { fsm: { ...fsm, state: "CLUTCH", confirmDownAt }, transition: { kind: "none" } };
    }
    return { fsm: { ...fsm, confirmDownAt }, transition: { kind: "none" } };
  }

  if (fsm.state === "CLUTCH") {
    if (!next.clutch) {
      return { fsm: { ...fsm, state: "IDLE", confirmDownAt }, transition: { kind: "none" } };
    }
    // Rising edges only: holding A does not re-arm every frame.
    const side = risingSide(prev, next);
    if (side) {
      return {
        fsm: { ...fsm, state: "ARMED", side, armedAt: now, confirmDownAt },
        transition: { kind: "arm", side },
      };
    }
    return { fsm: { ...fsm, confirmDownAt }, transition: { kind: "none" } };
  }

  // ARMED
  if (!next.clutch) {
    return {
      fsm: { ...fsm, state: "IDLE", side: null, armedAt: null, confirmDownAt },
      transition: { kind: "cancel", reason: "clutch_released" },
    };
  }
  if (rose(prev.armSell, next.armSell) && fsm.side !== "sell") {
    // B while already armed elsewhere is the cancel, not a flip to sell.
    return {
      fsm: { ...fsm, state: "CLUTCH", side: null, armedAt: null, confirmDownAt },
      transition: { kind: "cancel", reason: "b_pressed" },
    };
  }

  const swap = risingSide(prev, next);
  if (swap && swap !== fsm.side) {
    return {
      fsm: { ...fsm, side: swap, armedAt: now, confirmDownAt },
      transition: { kind: "arm", side: swap },
    };
  }

  if (canFire(fsm, prev, next, now, confirmDownAt, confirmHoldMs) && fsm.side) {
    if (fireBlocked) {
      // A previous fire's cid is still unresolved. Refusing is what stops a
      // timeout from turning into two positions.
      return { fsm: { ...fsm, confirmDownAt }, transition: { kind: "none" } };
    }
    const side = fsm.side;
    const armedAt = fsm.armedAt ?? now;
    return {
      fsm: { ...fsm, state: "IDLE", side: null, armedAt: null, confirmDownAt },
      transition: { kind: "fire", side, armedAt },
    };
  }

  return { fsm: { ...fsm, confirmDownAt }, transition: { kind: "none" } };
}

function risingSide(prev: Inputs, next: Inputs): ArmSide | null {
  if (rose(prev.armPanic, next.armPanic)) return "panic";
  if (rose(prev.armClose, next.armClose)) return "close";
  if (rose(prev.armBuy, next.armBuy)) return "buy";
  if (rose(prev.armSell, next.armSell)) return "sell";
  return null;
}

/**
 * The fire predicate. Held confirm cannot fire twice: with `confirmHoldMs` at 0
 * it needs the rising edge, and above 0 the press is consumed by the transition
 * out of ARMED, so the button must be released and pressed again.
 */
function canFire(
  fsm: Fsm,
  prev: Inputs,
  next: Inputs,
  now: number,
  confirmDownAt: number | null,
  confirmHoldMs: number,
): boolean {
  if (!next.clutch || !fsm.side) return false;
  if (confirmHoldMs <= 0) return rose(prev.confirm, next.confirm);
  if (!next.confirm || confirmDownAt === null) return false;
  return now - confirmDownAt >= confirmHoldMs;
}

/** Safety exits. Never gated by tilt, dead-man, or the daily loss. */
export function isSafetyExit(side: ArmSide): boolean {
  return side === "close" || side === "panic";
}
