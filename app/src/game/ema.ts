/**
 * The 20 EMA the plan asks for on the chart.
 *
 * Seeded with a simple average of the first `period` bars rather than with the
 * first close: seeding from a single price makes the line start far from the
 * data and drift into place over the next few dozen bars, which reads as a
 * signal when it is only an artefact of the seed.
 */

export const EMA_PERIOD = 20;

export type Point = { time: number; value: number };

export function ema(closes: { time: number; close: number }[], period = EMA_PERIOD): Point[] {
  if (closes.length < period) return [];

  const k = 2 / (period + 1);
  const out: Point[] = [];

  let acc = 0;
  for (let i = 0; i < period; i += 1) acc += closes[i]!.close;
  let value = acc / period;
  out.push({ time: closes[period - 1]!.time, value });

  for (let i = period; i < closes.length; i += 1) {
    value = closes[i]!.close * k + value * (1 - k);
    out.push({ time: closes[i]!.time, value });
  }
  return out;
}

/** One step, for updating the line as the right-hand bar moves. */
export function emaStep(previous: number, close: number, period = EMA_PERIOD): number {
  const k = 2 / (period + 1);
  return close * k + previous * (1 - k);
}
