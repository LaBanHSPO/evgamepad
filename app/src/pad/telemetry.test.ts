/** Telemetry must reach the socket at 1 Hz — batching is a requirement, not an optimisation. */

import { expect, it } from "vitest";
import type { Effect } from "./fsm";
import { TelemetryBatcher } from "./telemetry";

const transition = (from: any, to: any, reason: string): Effect => ({ kind: "transition", from, to, reason });

it("never emits more than once a second, even at frame rate", () => {
  const batcher = new TelemetryBatcher(0);
  let emitted = 0;
  // 60 Hz for ten seconds: 600 frames in, at most 10 samples out.
  for (let frame = 1; frame <= 600; frame += 1) {
    const nowMs = frame * (1000 / 60);
    batcher.observe([transition("IDLE", "CLUTCH", "clutch_down")], nowMs);
    if (batcher.drain(nowMs) !== null) emitted += 1;
  }
  expect(emitted).toBeLessThanOrEqual(10);
  expect(emitted).toBeGreaterThan(8);
});

it("emits an idle heartbeat so a quiet evening is distinguishable from a dead one", () => {
  const batcher = new TelemetryBatcher(0);
  const sample = batcher.drain(1000);
  expect(sample).not.toBeNull();
  expect(sample?.clutchCycles).toBe(0);
  expect(sample?.btnRateHz).toBe(0);
  expect(sample?.from).toBe("LOCKED");
});

it("counts clutch cycles and arm flips across a batch", () => {
  const batcher = new TelemetryBatcher(0);
  batcher.observe([transition("IDLE", "CLUTCH", "clutch_down")], 100);
  batcher.observe([transition("CLUTCH", "ARMED", "arm_buy")], 200);
  batcher.observe([transition("ARMED", "IDLE", "clutch_up")], 400);
  batcher.observe([transition("IDLE", "CLUTCH", "clutch_down")], 500);
  batcher.observe([transition("CLUTCH", "IDLE", "clutch_up")], 700);

  const sample = batcher.drain(1000);
  expect(sample?.clutchCycles).toBe(2);
  expect(sample?.armFlips).toBe(1);
  expect(sample?.armMs).toBe(200);
});

it("measures time to fire from the arm, not from the frame", () => {
  const batcher = new TelemetryBatcher(0);
  batcher.observe([{ kind: "intent", side: "buy", armedAt: 400 }], 1200);
  expect(batcher.drain(1200)?.ttfMs).toBe(800);
});

it("counts lot steps since the last sample", () => {
  const batcher = new TelemetryBatcher(0);
  batcher.observe([{ kind: "lot", step: 1 }, { kind: "lot", step: -1 }], 500);
  expect(batcher.drain(1000)?.lotStepsSince).toBe(2);
  batcher.observe([], 1500);
  expect(batcher.drain(2000)?.lotStepsSince).toBe(0);
});

it("carries an in-progress clutch across the batch boundary without double counting", () => {
  const batcher = new TelemetryBatcher(0);
  batcher.observe([transition("IDLE", "CLUTCH", "clutch_down")], 500);
  const first = batcher.drain(1000);
  const second = batcher.drain(2000);
  expect(first?.clutchMs).toBe(500);
  expect(second?.clutchMs).toBe(1000);
});

it("reports a button rate rather than raw counts", () => {
  const batcher = new TelemetryBatcher(0);
  for (let i = 0; i < 6; i += 1) batcher.observe([{ kind: "lot", step: 1 }], 100 * i);
  const sample = batcher.drain(2000);
  expect(sample?.btnRateHz).toBeCloseTo(3.0, 1);
});
