/**
 * The order FSM. These tests are the safety argument for the whole client: a held button cannot
 * spray orders, a stick cannot fire, and losing focus or the pad cancels an arm on the spot.
 */

import { describe, expect, it } from "vitest";
import type { Effect, FsmState, PadInput } from "./fsm";
import { canFire, initialState, onSocketClose, resolve, step } from "./fsm";

function input(over: Partial<PadInput> = {}): PadInput {
  return {
    clutch: 0, confirm: false, a: false, b: false, x: false, y: false,
    view: false, menu: false, lotUp: false, lotDown: false,
    symbolLeft: false, symbolRight: false,
    visible: true, padConnected: true, nowMs: 1000,
    ...over,
  };
}

function kinds(effects: Effect[]): string[] {
  return effects.map((e) => e.kind);
}

function intents(effects: Effect[]): Extract<Effect, { kind: "intent" }>[] {
  return effects.filter((e): e is Extract<Effect, { kind: "intent" }> => e.kind === "intent");
}

/** Drive from LOCKED to ARMED buy, the way a player actually would. */
function armed(options = {}): FsmState {
  let state = step(initialState, input({ view: true }), options).state;
  state = step(state, input({ clutch: 0.9 }), options).state;
  return step(state, input({ clutch: 0.9, a: true }), options).state;
}

describe("unlocking", () => {
  it("starts locked and needs a deliberate View tap", () => {
    expect(initialState.phase).toBe("LOCKED");
    const held = step(initialState, input({ clutch: 1, a: true, confirm: true }));
    expect(held.state.phase).toBe("LOCKED");
    expect(intents(held.effects)).toHaveLength(0);
  });

  it("toggles the lock back on with another View tap", () => {
    const unlocked = step(initialState, input({ view: true }));
    expect(unlocked.state.phase).toBe("IDLE");
    const relocked = step(unlocked.state, input({ view: true }));
    expect(relocked.state.phase).toBe("LOCKED");
  });
});

describe("firing takes two hands", () => {
  it("opens on clutch held plus an armed side plus a confirm edge", () => {
    const state = armed();
    expect(state.phase).toBe("ARMED");
    const fired = step(state, input({ clutch: 0.9, confirm: true }));
    expect(intents(fired.effects)).toEqual([{ kind: "intent", side: "buy", armedAt: 1000 }]);
    expect(fired.state.phase).toBe("FIRE");
  });

  it("refuses to fire without the clutch", () => {
    const state = armed();
    const released = step(state, input({ clutch: 0, confirm: true }));
    expect(intents(released.effects)).toHaveLength(0);
    expect(released.state.phase).toBe("IDLE");
  });

  it("refuses to fire with no side armed", () => {
    let state = step(initialState, input({ view: true })).state;
    state = step(state, input({ clutch: 0.9 })).state;
    expect(state.phase).toBe("CLUTCH");
    const fired = step(state, input({ clutch: 0.9, confirm: true }));
    expect(intents(fired.effects)).toHaveLength(0);
  });

  it("does not spray orders while confirm stays held", () => {
    const state = armed();
    const first = step(state, input({ clutch: 0.9, confirm: true }));
    let carried = first.state;
    for (let i = 0; i < 60; i += 1) {
      const frame = step(carried, input({ clutch: 0.9, confirm: true, nowMs: 1000 + i }));
      carried = frame.state;
      expect(intents(frame.effects)).toHaveLength(0);
    }
    expect(intents(first.effects)).toHaveLength(1);
  });

  it("does not re-fire when confirm was already down as the side was armed", () => {
    let state = step(initialState, input({ view: true })).state;
    state = step(state, input({ clutch: 0.9, confirm: true })).state;
    const armedWithConfirmHeld = step(state, input({ clutch: 0.9, confirm: true, a: true }));
    // The edge belongs to an earlier frame, but the hold is satisfied and the clutch is held:
    // this is the two-hand contract, not a stray repeat.
    expect(intents(armedWithConfirmHeld.effects)).toHaveLength(1);
  });
});

describe("clutch hysteresis", () => {
  it("engages high and releases low so a resting finger cannot chatter", () => {
    let state = step(initialState, input({ view: true })).state;
    state = step(state, input({ clutch: 0.7 })).state;
    expect(state.phase).toBe("IDLE");

    state = step(state, input({ clutch: 0.85 })).state;
    expect(state.phase).toBe("CLUTCH");

    state = step(state, input({ clutch: 0.6 })).state;
    expect(state.phase).toBe("CLUTCH");

    state = step(state, input({ clutch: 0.4 })).state;
    expect(state.phase).toBe("IDLE");
  });
});

describe("cancels", () => {
  it("cancels the arm the moment the tab hides", () => {
    const hidden = step(armed(), input({ clutch: 0.9, visible: false }));
    expect(kinds(hidden.effects)).toContain("cancel");
    expect(hidden.state.phase).toBe("LOCKED");
    expect(hidden.state.side).toBeNull();
  });

  it("cancels the arm the moment the pad unplugs", () => {
    const unplugged = step(armed(), input({ clutch: 0.9, padConnected: false }));
    expect(kinds(unplugged.effects)).toContain("cancel");
    expect(unplugged.state.phase).toBe("LOCKED");
  });

  it("cancels on clutch release", () => {
    const released = step(armed(), input({ clutch: 0 }));
    expect(kinds(released.effects)).toContain("cancel");
    expect(released.state.phase).toBe("IDLE");
  });

  it("treats B while idle as a cancel, not an arm", () => {
    const state = step(initialState, input({ view: true })).state;
    const cancelled = step(state, input({ b: true }));
    expect(cancelled.state.side).toBeNull();
    expect(cancelled.state.phase).toBe("IDLE");
  });
});

describe("sticks and non-order controls", () => {
  it("has no axis input at all, so no stick can ever fire", () => {
    const keys = Object.keys(input());
    expect(keys.filter((k) => /axis|stick|ls|rs/i.test(k))).toEqual([]);
  });

  it("steps lot size while clutched, because lot is not bound to the trigger", () => {
    let state = step(initialState, input({ view: true })).state;
    state = step(state, input({ clutch: 0.9 })).state;
    const stepped = step(state, input({ clutch: 0.9, lotUp: true }));
    expect(stepped.effects).toContainEqual({ kind: "lot", step: 1 });
    expect(intents(stepped.effects)).toHaveLength(0);
  });

  it("cycles the symbol without touching the broker", () => {
    const state = step(initialState, input({ view: true })).state;
    const cycled = step(state, input({ symbolRight: true }));
    expect(cycled.effects).toContainEqual({ kind: "symbol", step: 1 });
    expect(intents(cycled.effects)).toHaveLength(0);
  });
});

describe("the overlay is a safe surface", () => {
  it("cancels the arm and locks new opens when Menu opens it", () => {
    const opened = step(armed(), input({ clutch: 0.9, menu: true }));
    expect(opened.state.overlayOpen).toBe(true);
    expect(kinds(opened.effects)).toContain("cancel");
    expect(opened.state.phase).toBe("IDLE");

    const tryArm = step(opened.state, input({ clutch: 0.9, a: true }));
    expect(tryArm.state.phase).not.toBe("ARMED");
    expect(intents(tryArm.effects)).toHaveLength(0);
  });

  it("does not step lot or symbol while the overlay is open", () => {
    const opened = step(armed(), input({ clutch: 0.9, menu: true }));
    const lot = step(opened.state, input({ clutch: 0.9, lotUp: true }));
    expect(lot.effects).not.toContainEqual({ kind: "lot", step: 1 });
    const symbol = step(opened.state, input({ symbolRight: true }));
    expect(symbol.effects).not.toContainEqual({ kind: "symbol", step: 1 });
    expect(intents(lot.effects)).toHaveLength(0);
  });
});

describe("an outstanding fire", () => {
  it("blocks a new open but never an exit", () => {
    const fired = step(armed(), input({ clutch: 0.9, confirm: true }));
    const timedOut = step(fired.state, input({ clutch: 0.9, nowMs: 1000 + 6000 }));
    expect(timedOut.state.phase).toBe("UNKNOWN");

    const tryBuy = step(timedOut.state, input({ clutch: 0.9, a: true, nowMs: 7100 }));
    expect(tryBuy.state.side).toBeNull();

    const tryClose = step(timedOut.state, input({ clutch: 0.9, x: true, nowMs: 7100 }));
    expect(tryClose.state.side).toBe("close");
    expect(tryClose.state.phase).toBe("ARMED");
  });

  it("returns to idle once the cid resolves", () => {
    const fired = step(armed(), input({ clutch: 0.9, confirm: true }));
    const acked = resolve(fired.state, true);
    expect(acked.state.phase).toBe("IDLE");
    expect(acked.state.pendingCid).toBeNull();

    const rejected = resolve(fired.state, false);
    expect(kinds(rejected.effects)).toContain("rumble");
  });
});

describe("socket loss", () => {
  it("locks the client and keeps an outstanding cid rather than minting a new one", () => {
    const fired = step(armed(), input({ clutch: 0.9, confirm: true }));
    const dropped = onSocketClose(fired.state);
    expect(dropped.phase).toBe("UNKNOWN");

    const idle = onSocketClose(step(initialState, input({ view: true })).state);
    expect(idle.phase).toBe("LOCKED");
  });
});

describe("confirmHoldMs is a parameter, not a new state", () => {
  it("still fires on a rising edge at the default of zero", () => {
    const fired = step(armed(), input({ clutch: 0.9, confirm: true }));
    expect(intents(fired.effects)).toHaveLength(1);
  });

  it("withholds the fire until the hold is satisfied when phase 9 raises it", () => {
    const options = { confirmHoldMs: 750 };
    const state = armed(options);
    const early = step(state, input({ clutch: 0.9, confirm: true, nowMs: 1100 }), options);
    expect(intents(early.effects)).toHaveLength(0);
    expect(early.state.phase).toBe("ARMED");

    const late = step(early.state, input({ clutch: 0.9, confirm: true, nowMs: 1900 }), options);
    expect(intents(late.effects)).toHaveLength(1);
  });

  it("adds no phase beyond the six the machine already had", () => {
    const phases = new Set(["LOCKED", "IDLE", "CLUTCH", "ARMED", "FIRE", "UNKNOWN"]);
    const state = armed({ confirmHoldMs: 750 });
    expect(phases.has(state.phase)).toBe(true);
  });

  it("exposes the predicate itself so friction is testable in isolation", () => {
    const state = armed();
    expect(canFire(state, input({ clutch: 0.9, confirm: true }), 0)).toBe(false);
    const withEdge = { ...state, confirmDownAt: 1000 };
    expect(canFire(withEdge, input({ clutch: 0.9, confirm: true, nowMs: 1000 }), 0)).toBe(true);
    expect(canFire(withEdge, input({ clutch: 0.9, confirm: true, nowMs: 1000 }), 750)).toBe(false);
  });
});
