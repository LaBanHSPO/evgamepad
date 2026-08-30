import { describe, expect, it } from "vitest";
import {
  NO_INPUT,
  initialFsm,
  isSafetyExit,
  step,
  type Fsm,
  type Inputs,
  type Transition,
} from "./fsm";

const T0 = 1_000_000;

function inputs(over: Partial<Inputs> = {}): Inputs {
  return { ...NO_INPUT, ...over };
}

/** Drive a sequence of frames, collecting every transition. */
function run(
  frames: Partial<Inputs>[],
  start: Fsm = initialFsm(),
  options = {},
): { fsm: Fsm; transitions: Transition[] } {
  let fsm = start;
  let prev = inputs();
  const transitions: Transition[] = [];
  frames.forEach((frame, i) => {
    const next = inputs(frame);
    const result = step(fsm, prev, next, T0 + i * 16, options);
    fsm = result.fsm;
    if (result.transition.kind !== "none") transitions.push(result.transition);
    prev = next;
  });
  return { fsm, transitions };
}

/** The canonical unlock: a View tap. */
const UNLOCK: Partial<Inputs>[] = [{ toggleLock: true }, {}];

describe("locking", () => {
  it("starts locked and needs a deliberate unlock", () => {
    const { fsm } = run([{ clutch: true, armBuy: true, confirm: true }]);
    expect(fsm.state).toBe("LOCKED");
  });

  it("View toggles the lock both ways", () => {
    const a = run(UNLOCK);
    expect(a.fsm.state).toBe("IDLE");
    const b = run([{ toggleLock: true }, {}], a.fsm);
    expect(b.fsm.state).toBe("LOCKED");
  });
});

describe("firing", () => {
  it("clutch, arm, confirm opens exactly one order", () => {
    const { fsm, transitions } = run(
      [...UNLOCK, { clutch: true }, { clutch: true, armBuy: true }, { clutch: true }, { clutch: true, confirm: true }],
    );
    const fires = transitions.filter((t) => t.kind === "fire");
    expect(fires).toHaveLength(1);
    expect(fires[0]).toMatchObject({ kind: "fire", side: "buy" });
    expect(fsm.state).toBe("IDLE");
  });

  it("a held confirm does not spray orders", () => {
    // Twenty frames with confirm down the whole time.
    const held = Array.from({ length: 20 }, () => ({
      clutch: true,
      armBuy: true,
      confirm: true,
    }));
    const { transitions } = run([...UNLOCK, { clutch: true }, { clutch: true, armBuy: true }, ...held]);
    expect(transitions.filter((t) => t.kind === "fire")).toHaveLength(1);
  });

  it("a held arm button does not re-arm every frame", () => {
    const held = Array.from({ length: 30 }, () => ({ clutch: true, armBuy: true }));
    const { transitions } = run([...UNLOCK, { clutch: true }, ...held]);
    expect(transitions.filter((t) => t.kind === "arm")).toHaveLength(1);
  });

  it("confirm without an arm fires nothing", () => {
    const { transitions } = run([
      ...UNLOCK,
      { clutch: true },
      { clutch: true, confirm: true },
      { clutch: true },
      { clutch: true, confirm: true },
    ]);
    expect(transitions.filter((t) => t.kind === "fire")).toHaveLength(0);
  });

  it("an arm without the clutch fires nothing", () => {
    const { transitions } = run([...UNLOCK, { armBuy: true }, { armBuy: true, confirm: true }]);
    expect(transitions.filter((t) => t.kind === "fire")).toHaveLength(0);
  });

  it("carries armedAt so the gateway can age the press", () => {
    const { transitions } = run([
      ...UNLOCK,
      { clutch: true },
      { clutch: true, armBuy: true },
      { clutch: true },
      { clutch: true, confirm: true },
    ]);
    const fire = transitions.find((t) => t.kind === "fire");
    expect(fire).toBeDefined();
    if (fire?.kind === "fire") expect(fire.armedAt).toBeGreaterThan(0);
  });
});

describe("cancelling", () => {
  it.each([
    ["releasing the clutch", { clutch: false }, "clutch_released"],
    ["hiding the tab", { clutch: true, visible: false }, "hidden"],
    ["unplugging the pad", { clutch: true, padConnected: false }, "pad_lost"],
    ["opening the overlay", { clutch: true, overlay: true }, "overlay_opened"],
  ])("cancels an ARM on %s", (_label, frame, reason) => {
    const { transitions } = run([...UNLOCK, { clutch: true }, { clutch: true, armBuy: true }, frame]);
    expect(transitions.at(-1)).toMatchObject({ kind: "cancel", reason });
  });

  it("B while armed cancels rather than flipping to sell", () => {
    const { fsm, transitions } = run([
      ...UNLOCK,
      { clutch: true },
      { clutch: true, armBuy: true },
      { clutch: true },
      { clutch: true, armSell: true },
    ]);
    expect(transitions.at(-1)).toMatchObject({ kind: "cancel", reason: "b_pressed" });
    expect(fsm.side).toBeNull();
  });

  it("a cancelled arm cannot then fire", () => {
    const { transitions } = run([
      ...UNLOCK,
      { clutch: true },
      { clutch: true, armBuy: true },
      { visible: false },
      { clutch: true, confirm: true },
    ]);
    expect(transitions.filter((t) => t.kind === "fire")).toHaveLength(0);
  });

  it("losing the tab locks even when nothing was armed", () => {
    const { fsm } = run([...UNLOCK, { visible: false }]);
    expect(fsm.state).toBe("LOCKED");
  });
});

describe("sticks", () => {
  it("are not inputs to this machine at all", () => {
    // The Inputs type has no axis fields, so a stick cannot reach a fire even
    // by mistake. This asserts the shape rather than a behaviour.
    expect(Object.keys(NO_INPUT).sort()).toEqual(
      [
        "armBuy",
        "armClose",
        "armPanic",
        "armSell",
        "clutch",
        "confirm",
        "overlay",
        "padConnected",
        "toggleLock",
        "visible",
      ].sort(),
    );
  });
});

describe("confirmHoldMs (phase 9 friction)", () => {
  it("defaults to a rising edge, so these tests hold unchanged", () => {
    const { transitions } = run([
      ...UNLOCK,
      { clutch: true },
      { clutch: true, armBuy: true },
      { clutch: true, confirm: true },
    ]);
    expect(transitions.filter((t) => t.kind === "fire")).toHaveLength(1);
  });

  it("a hold threshold delays the fire without adding a state", () => {
    let fsm = initialFsm();
    let prev = inputs();
    const options = { confirmHoldMs: 750 };
    const seen: Transition[] = [];
    const frames: Partial<Inputs>[] = [
      { toggleLock: true },
      {},
      { clutch: true },
      { clutch: true, armBuy: true },
      { clutch: true, confirm: true }, // t = +64ms, too early
    ];
    frames.forEach((f, i) => {
      const next = inputs(f);
      const r = step(fsm, prev, next, T0 + i * 16, options);
      fsm = r.fsm;
      if (r.transition.kind !== "none") seen.push(r.transition);
      prev = next;
    });
    expect(seen.filter((t) => t.kind === "fire")).toHaveLength(0);
    expect(fsm.state).toBe("ARMED");

    // Same press, held past the threshold.
    const late = inputs({ clutch: true, confirm: true });
    const r = step(fsm, late, late, T0 + 5 * 16 + 800, options);
    expect(r.transition).toMatchObject({ kind: "fire", side: "buy" });
  });
});

describe("unresolved fires", () => {
  it("a blocked fire does not send while a cid is unknown", () => {
    const { transitions } = run(
      [...UNLOCK, { clutch: true }, { clutch: true, armBuy: true }, { clutch: true, confirm: true }],
      initialFsm(),
      { fireBlocked: true },
    );
    expect(transitions.filter((t) => t.kind === "fire")).toHaveLength(0);
  });
});

describe("tilt friction never reaches a safety exit", () => {
  it.each([
    ["close", { armClose: true }],
    ["panic", { armPanic: true }],
  ])("a %s fires on a rising edge even at 750ms friction", (_label, arm) => {
    const { transitions } = run(
      [...UNLOCK, { clutch: true }, { clutch: true, ...arm }, { clutch: true, confirm: true }],
      initialFsm(),
      { confirmHoldMs: 750 },
    );
    expect(transitions.filter((t) => t.kind === "fire")).toHaveLength(1);
  });

  it("an open at the same friction still has to be held", () => {
    const { transitions } = run(
      [...UNLOCK, { clutch: true }, { clutch: true, armBuy: true }, { clutch: true, confirm: true }],
      initialFsm(),
      { confirmHoldMs: 750 },
    );
    expect(transitions.filter((t) => t.kind === "fire")).toHaveLength(0);
  });
});

describe("safety exits", () => {
  it("close and panic are the exits", () => {
    expect(isSafetyExit("close")).toBe(true);
    expect(isSafetyExit("panic")).toBe(true);
    expect(isSafetyExit("buy")).toBe(false);
    expect(isSafetyExit("sell")).toBe(false);
  });

  it("panic still needs the clutch and the confirm", () => {
    const { transitions } = run([...UNLOCK, { armPanic: true }, { armPanic: true, confirm: true }]);
    expect(transitions.filter((t) => t.kind === "fire")).toHaveLength(0);
  });
});
