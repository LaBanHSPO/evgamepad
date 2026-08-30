import { describe, expect, it } from "vitest";
import { EMA_PERIOD, ema, emaStep } from "./ema";

function bars(closes: number[]) {
  return closes.map((close, i) => ({ time: 1_700_000_000 + i * 300, close }));
}

describe("the 20 EMA", () => {
  it("emits nothing until it has a full period", () => {
    expect(ema(bars(Array(19).fill(100)))).toEqual([]);
    expect(ema(bars(Array(20).fill(100)))).toHaveLength(1);
  });

  it("seeds from the average of the first period, not the first close", () => {
    // Seeding from one price starts the line far from the data and lets it
    // drift into place, which reads as a signal when it is only the seed.
    const closes = [...Array(19).fill(100), 200];
    const [first] = ema(bars(closes));
    const average = closes.reduce((a, b) => a + b, 0) / 20;
    expect(first!.value).toBeCloseTo(average, 6);
    expect(first!.value).not.toBeCloseTo(100, 1);
  });

  it("is flat on flat data", () => {
    const points = ema(bars(Array(60).fill(42)));
    expect(points.every((p) => Math.abs(p.value - 42) < 1e-9)).toBe(true);
  });

  it("lags a step change without overshooting it", () => {
    const points = ema(bars([...Array(20).fill(100), ...Array(40).fill(200)]));
    const values = points.map((p) => p.value);
    expect(values[0]).toBeCloseTo(100, 6);
    expect(values.at(-1)!).toBeGreaterThan(190);
    expect(Math.max(...values)).toBeLessThanOrEqual(200);
    // Monotonic toward the new level: no overshoot, no oscillation.
    for (let i = 1; i < values.length; i += 1) {
      expect(values[i]!).toBeGreaterThanOrEqual(values[i - 1]!);
    }
  });

  it("carries one point per bar past the seed", () => {
    expect(ema(bars(Array(100).fill(1)))).toHaveLength(100 - EMA_PERIOD + 1);
  });

  it("emaStep matches the series it continues", () => {
    const closes = Array.from({ length: 40 }, (_, i) => 100 + i);
    const full = ema(bars(closes));
    const short = ema(bars(closes.slice(0, -1)));
    expect(emaStep(short.at(-1)!.value, closes.at(-1)!)).toBeCloseTo(full.at(-1)!.value, 9);
  });
});
