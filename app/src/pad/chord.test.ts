/** LB+RB is a memo; one bumper is a timeframe change. Both directions, both tested. */

import { expect, it } from "vitest";
import type { ChordEffect, ChordInput, ChordState } from "./chord";
import { initialChordState, stepChord } from "./chord";

function input(over: Partial<ChordInput> = {}): ChordInput {
  return { lb: false, rb: false, key: false, phase: "IDLE", nowMs: 1000, ...over };
}

function run(frames: Partial<ChordInput>[], start: ChordState = initialChordState) {
  let state = start;
  const effects: ChordEffect[] = [];
  for (const frame of frames) {
    const result = stepChord(state, input(frame));
    state = result.state;
    effects.push(...result.effects);
  }
  return { state, effects };
}

it("a single bumper changes the timeframe, on release", () => {
  const held = run([{ lb: true, nowMs: 1000 }, { lb: true, nowMs: 1050 }]);
  expect(held.effects).toEqual([]);

  const released = run([{ lb: true, nowMs: 1000 }, { lb: false, nowMs: 1100 }]);
  expect(released.effects).toEqual([{ kind: "timeframe", step: -1 }]);
});

it("the other bumper steps the other way", () => {
  const { effects } = run([{ rb: true }, { rb: false, nowMs: 1100 }]);
  expect(effects).toEqual([{ kind: "timeframe", step: 1 }]);
});

it("both bumpers inside the window is push-to-talk, not two timeframe changes", () => {
  const { effects } = run([
    { lb: true, nowMs: 1000 },
    { lb: true, rb: true, nowMs: 1080 },
    { lb: false, rb: false, nowMs: 1500 },
  ]);
  expect(effects.filter((e) => e.kind === "timeframe")).toEqual([]);
  expect(effects[0]).toEqual({ kind: "ptt", active: true });
});

it("bumpers pressed far apart are two separate timeframe changes", () => {
  const { effects } = run([
    { lb: true, nowMs: 1000 },
    { lb: false, nowMs: 1100 },
    { rb: true, nowMs: 2000 },
    { rb: false, nowMs: 2100 },
  ]);
  expect(effects).toEqual([
    { kind: "timeframe", step: -1 },
    { kind: "timeframe", step: 1 },
  ]);
});

it("releasing the chord submits the memo rather than discarding it", () => {
  const { effects } = run([
    { lb: true, rb: true, nowMs: 1000 },
    { lb: false, rb: false, nowMs: 3000 },
  ]);
  expect(effects).toContainEqual({ kind: "ptt", active: false, submit: true });
});

it("the keyboard fallback has equal status", () => {
  const { effects } = run([{ key: true }, { key: false, nowMs: 2000 }]);
  expect(effects[0]).toEqual({ kind: "ptt", active: true });
  expect(effects[1]).toEqual({ kind: "ptt", active: false, submit: true });
});

it("talking cannot start while the order machine is armed or firing", () => {
  for (const phase of ["CLUTCH", "ARMED", "FIRE", "UNKNOWN"] as const) {
    const { state, effects } = run([{ lb: true, rb: true, phase }]);
    expect(state.ptt).toBe(false);
    expect(effects.filter((e) => e.kind === "ptt")).toEqual([]);
  }
});

it("a refused chord still does not zoom the chart", () => {
  const { effects } = run([
    { lb: true, rb: true, phase: "ARMED", nowMs: 1000 },
    { lb: false, rb: false, phase: "ARMED", nowMs: 1200 },
  ]);
  expect(effects).toEqual([]);
});

it("clutching mid-memo stops and submits instead of discarding", () => {
  const started = run([{ lb: true, rb: true, nowMs: 1000 }]);
  expect(started.state.ptt).toBe(true);

  const clutched = stepChord(started.state, input({ lb: true, rb: true, phase: "CLUTCH", nowMs: 1400 }));
  expect(clutched.state.ptt).toBe(false);
  expect(clutched.effects).toContainEqual({ kind: "ptt", active: false, submit: true });
});

it("emits no order transition of its own, ever", () => {
  const { effects } = run([
    { lb: true, rb: true, nowMs: 1000 },
    { lb: false, rb: false, nowMs: 2000 },
  ]);
  const kinds = new Set(effects.map((e) => e.kind));
  expect(kinds).toEqual(new Set(["ptt"]));
  expect([...kinds]).not.toContain("intent");
});
