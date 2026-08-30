import { describe, expect, it } from "vitest";
import { initialChord, stepChord, type Bumpers, type ChordEvent } from "./chord";
import { beginPtt, canEnterPtt, initialPtt, onClutchDuringPtt } from "./ptt";

const T0 = 500_000;

function run(frames: Bumpers[], startAt = T0, stepMs = 16) {
  let state = initialChord();
  let prev: Bumpers = { lb: false, rb: false };
  const events: ChordEvent[] = [];
  frames.forEach((next, i) => {
    const r = stepChord(state, prev, next, startAt + i * stepMs);
    state = r.state;
    if (r.event.kind !== "none") events.push(r.event);
    prev = next;
  });
  return { state, events };
}

const UP: Bumpers = { lb: false, rb: false };

describe("single bumper", () => {
  it("changes timeframe on release, not on press", () => {
    const pressOnly = run([{ lb: true, rb: false }]);
    expect(pressOnly.events).toEqual([]);

    const full = run([{ lb: true, rb: false }, { lb: true, rb: false }, UP]);
    expect(full.events).toEqual([{ kind: "timeframe", direction: -1 }]);
  });

  it("RB steps the other way", () => {
    const { events } = run([{ lb: false, rb: true }, UP]);
    expect(events).toEqual([{ kind: "timeframe", direction: 1 }]);
  });

  it("a long single-bumper hold is still one timeframe change", () => {
    const held = Array.from({ length: 60 }, () => ({ lb: true, rb: false }));
    const { events } = run([...held, UP]);
    expect(events).toEqual([{ kind: "timeframe", direction: -1 }]);
  });
});

describe("the LB+RB chord", () => {
  it("enters push-to-talk when both land inside the window", () => {
    const { events } = run([
      { lb: true, rb: false },
      { lb: true, rb: true }, // +16ms, well inside 120ms
    ]);
    expect(events).toEqual([{ kind: "ptt", phase: "begin" }]);
  });

  it("suppresses BOTH timeframe changes", () => {
    const { events } = run([
      { lb: true, rb: false },
      { lb: true, rb: true },
      { lb: true, rb: true },
      { lb: false, rb: true },
      UP,
    ]);
    expect(events.filter((e) => e.kind === "timeframe")).toEqual([]);
    expect(events.map((e) => e.kind)).toEqual(["ptt", "ptt"]);
  });

  it("ends when either bumper comes up", () => {
    const { events } = run([
      { lb: true, rb: true },
      { lb: true, rb: true },
      { lb: true, rb: false },
    ]);
    expect(events).toEqual([
      { kind: "ptt", phase: "begin" },
      { kind: "ptt", phase: "end" },
    ]);
  });

  it("a second bumper arriving too late is two timeframe changes, not a chord", () => {
    // LB down, then RB 200ms later: outside the 120ms window.
    let state = initialChord();
    let prev: Bumpers = UP;
    const events: ChordEvent[] = [];
    const script: [Bumpers, number][] = [
      [{ lb: true, rb: false }, 0],
      [{ lb: true, rb: true }, 200],
      [{ lb: false, rb: true }, 216],
      [UP, 232],
    ];
    for (const [next, offset] of script) {
      const r = stepChord(state, prev, next, T0 + offset);
      state = r.state;
      if (r.event.kind !== "none") events.push(r.event);
      prev = next;
    }
    expect(events.filter((e) => e.kind === "ptt")).toEqual([]);
    expect(events.filter((e) => e.kind === "timeframe")).toHaveLength(2);
  });
});

describe("push-to-talk is not on the order path", () => {
  it("emits no order transition of its own", () => {
    const { events } = run([{ lb: true, rb: true }, UP]);
    // The union has exactly two shapes and neither is an order.
    for (const event of events) {
      expect(["timeframe", "ptt"]).toContain(event.kind);
    }
  });

  it("is enterable only from IDLE or LOCKED", () => {
    expect(canEnterPtt("IDLE")).toBe(true);
    expect(canEnterPtt("LOCKED")).toBe(true);
    expect(canEnterPtt("CLUTCH")).toBe(false);
    expect(canEnterPtt("ARMED")).toBe(false);
    expect(canEnterPtt("FIRE")).toBe(false);
  });

  it("refuses to begin while a fire is being set up", () => {
    const { ptt, event } = beginPtt(initialPtt(), "ARMED", T0);
    expect(event).toEqual({ kind: "refused", from: "ARMED" });
    expect(ptt.active).toBe(false);
  });

  it("reaching for the clutch submits the memo instead of discarding it", () => {
    const started = beginPtt(initialPtt(), "IDLE", T0);
    expect(started.ptt.active).toBe(true);
    const { ptt, event } = onClutchDuringPtt(started.ptt, T0 + 4000);
    expect(event).toEqual({ kind: "submit", at: T0 + 4000, reason: "clutch" });
    expect(ptt.active).toBe(false);
  });

  it("acquires no microphone in phase 3", () => {
    const { ptt } = beginPtt(initialPtt(), "IDLE", T0);
    // recording stays false: phase 3 owns the control event only.
    expect(ptt.recording).toBe(false);
  });
});
