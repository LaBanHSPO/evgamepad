import { describe, expect, it } from "vitest";
import { BATCH_MS, TelemetryCollector } from "./telemetry";

const T0 = 100_000;
const CTX = { sym: "XAUUSD", lots: 0.01 };

describe("batching is a requirement, not an optimisation", () => {
  it("emits nothing before a second has passed", () => {
    const c = new TelemetryCollector(T0);
    for (let i = 1; i <= 59; i += 1) {
      c.frame(16, true, false);
      expect(c.maybeFlush(T0 + i * 16, CTX)).toBeNull();
    }
  });

  it("emits at most one batch per second under a 60fps flood", () => {
    const c = new TelemetryCollector(T0);
    let batches = 0;
    // Five seconds of frames at 60fps.
    for (let i = 1; i <= 300; i += 1) {
      const now = T0 + i * 16.67;
      c.frame(16.67, true, true);
      c.buttonPress();
      if (c.maybeFlush(now, CTX)) batches += 1;
    }
    // Five seconds of pad input must not become 300 socket frames.
    expect(batches).toBeLessThanOrEqual(5);
    expect(batches).toBeGreaterThanOrEqual(4);
  });
});

describe("what a batch carries", () => {
  it("accumulates the fields phase 9 has no other source for", () => {
    const c = new TelemetryCollector(T0);
    c.frame(400, true, false);
    c.frame(600, true, true);
    c.transition({ at: T0, from: "IDLE", to: "CLUTCH", side: null, reason: null });
    c.transition({ at: T0, from: "ARMED", to: "ARMED", side: "sell", reason: null });
    c.lotStep();
    c.lotStep();
    c.fired(T0, T0 + 820);

    const batch = c.maybeFlush(T0 + BATCH_MS, CTX);
    expect(batch).not.toBeNull();
    expect(batch).toMatchObject({
      clutchMs: 1000,
      armMs: 600,
      clutchCycles: 1,
      armFlips: 1,
      lotStepsSince: 2,
      ttfMs: 820,
      sym: "XAUUSD",
    });
  });

  it("emits an idle heartbeat, so calm reads differently from absent", () => {
    const c = new TelemetryCollector(T0);
    const batch = c.maybeFlush(T0 + BATCH_MS, { sym: null, lots: null });
    expect(batch).not.toBeNull();
    expect(batch).toMatchObject({ clutchMs: 0, armFlips: 0, btnRateHz: 0 });
  });

  it("resets counters after a flush", () => {
    const c = new TelemetryCollector(T0);
    c.lotStep();
    c.maybeFlush(T0 + BATCH_MS, CTX);
    const second = c.maybeFlush(T0 + BATCH_MS * 2, CTX);
    expect(second?.lotStepsSince).toBe(0);
  });
});
