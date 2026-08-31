/**
 * 1 Hz bars into whatever timeframe is on screen.
 *
 * The tape is stored once, at one second, and every displayed timeframe is folded out of it here.
 * There is deliberately no second series to fetch: a 5-minute view of a stored 5-minute series and
 * a 5-minute view folded from seconds would eventually disagree, and then the review would be
 * arguing with itself.
 *
 * Aggregation stays on the **scaled integers**. Open is the first open, close the last close, high
 * and low the extremes — all of which are values that were actually in the tape, so nothing is
 * invented and nothing is rounded. The divide by `scale` happens once, at the point of drawing.
 */

import type { Tape } from "./types";

export type Side = "bid" | "ask";

export interface Candle {
  /** Bucket start, in seconds — what Lightweight Charts calls the time. */
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  ticks: number;
}

/** The timeframes the right stick steps through, in seconds. */
export const TIMEFRAMES = [1, 5, 15, 60, 300] as const;
export type Timeframe = (typeof TIMEFRAMES)[number];

export function timeframeLabel(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  return `${seconds / 60}m`;
}

/**
 * Fold the tape into `seconds`-wide candles on one side of the book.
 *
 * A long is exited on the bid and a short on the ask, so the side is the caller's choice and never
 * a default — showing a short against the bid understates every adverse move by the spread.
 */
export function resample(tape: Tape, side: Side, seconds: number): Candle[] {
  if (seconds <= 0) throw new Error("timeframe must be positive");

  const opens = side === "bid" ? tape.bidO : tape.askO;
  const highs = side === "bid" ? tape.bidH : tape.askH;
  const lows = side === "bid" ? tape.bidL : tape.askL;
  const closes = side === "bid" ? tape.bidC : tape.askC;

  const out: Candle[] = [];
  let current: Candle | null = null;

  for (let i = 0; i < tape.n; i += 1) {
    const bucket = Math.floor(tape.ts[i] / seconds) * seconds;
    if (current === null || current.time !== bucket) {
      if (current !== null) out.push(current);
      current = {
        time: bucket,
        open: opens[i],
        high: highs[i],
        low: lows[i],
        close: closes[i],
        ticks: tape.nTicks[i],
      };
      continue;
    }
    current.high = Math.max(current.high, highs[i]);
    current.low = Math.min(current.low, lows[i]);
    current.close = closes[i];
    current.ticks += tape.nTicks[i];
  }
  if (current !== null) out.push(current);
  return out;
}

/** The side a position's excursions are measured on, and therefore the side to chart it against. */
export function sideForTrade(tradeSide: "buy" | "sell"): Side {
  return tradeSide === "buy" ? "bid" : "ask";
}

/** Scaled integer to a price the axis can print. One divide, at the last possible moment. */
export function toPrice(scaled: number, scale: number): number {
  return scaled / scale;
}

/** Where the playhead sits within the window, 0 to 1. Used by the timeline and the scrubber. */
export function progress(tape: Tape, playheadMs: number): number {
  const span = tape.toTs - tape.fromTs;
  if (span <= 0) return 0;
  return clamp01((playheadMs / 1000 - tape.fromTs) / span);
}

export function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}
