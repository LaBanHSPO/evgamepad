/**
 * What gets drawn on top of the tape.
 *
 * Entry, exit, MFE and MAE come from `trade_closed`, never from the bars. At 1 Hz the entry candle
 * is context — the fill is truth — so the marker sits at the recorded price and time even when the
 * bar around it says something slightly different.
 *
 * Every label comes from this module's own strings or from a fixed event table. Nothing here
 * renders player text, so nothing untrusted reaches the chart through this path.
 */

import type { ReplayEvent, ReplayTrade } from "./types";

export type MarkerShape = "arrowUp" | "arrowDown" | "circle" | "square";
export type MarkerPosition = "aboveBar" | "belowBar" | "inBar";

export interface ChartMarker {
  time: number;
  position: MarkerPosition;
  shape: MarkerShape;
  color: string;
  text: string;
}

export const COLOURS = {
  entry: "var(--phos-300)",
  exit: "var(--phos-200)",
  mfe: "var(--phos-400)",
  mae: "var(--arcade-red)",
} as const;

/** One colour and one short word per event kind. The rail never invents a label. */
export const EVENT_STYLE: Record<string, { colour: string; word: string }> = {
  arm: { colour: "var(--arcade-cyan)", word: "arm" },
  cancel: { colour: "var(--phos-400)", word: "stood down" },
  fire: { colour: "var(--phos-200)", word: "fire" },
  ack: { colour: "var(--grey-300)", word: "ack" },
  sl_move: { colour: "var(--arcade-yellow)", word: "sl move" },
  memo: { colour: "var(--status-agent)", word: "memo" },
  volman_tag: { colour: "var(--arcade-cyan)", word: "tag" },
  tv_signal: { colour: "var(--arcade-cyan)", word: "tv" },
  tilt_band_change: { colour: "var(--arcade-orange)", word: "tilt" },
};

export function styleFor(kind: string): { colour: string; word: string } {
  return EVENT_STYLE[kind] ?? { colour: "var(--grey-300)", word: kind };
}

/**
 * Entry and exit, in the timeframe's own bucket.
 *
 * The marker snaps to the bucket the chart draws, but its *label* carries the real fill price, so
 * a coarse timeframe never quietly changes what you paid.
 */
export function tradeMarkers(trade: ReplayTrade, seconds: number): ChartMarker[] {
  const out: ChartMarker[] = [];
  const long = trade.side === "buy";

  if (trade.openedAt !== null && trade.entry !== null) {
    out.push({
      time: bucket(trade.openedAt, seconds),
      position: long ? "belowBar" : "aboveBar",
      shape: long ? "arrowUp" : "arrowDown",
      color: COLOURS.entry,
      text: `entry ${trade.entry}`,
    });
  }
  if (trade.exit !== null) {
    out.push({
      time: bucket(trade.closedAt, seconds),
      position: long ? "aboveBar" : "belowBar",
      shape: long ? "arrowDown" : "arrowUp",
      color: COLOURS.exit,
      text: `exit ${trade.exit}`,
    });
  }
  return out;
}

/**
 * MFE and MAE as price lines rather than dots.
 *
 * Their *time* was never recorded — the freeze stores the extremes, not when they happened — so
 * drawing them at a guessed timestamp would be a fabrication. A horizontal line at the price is
 * exactly what is known.
 */
export function excursionLines(trade: ReplayTrade): { price: number; colour: string; label: string }[] {
  if (trade.entry === null) return [];
  const long = trade.side === "buy";
  const lines: { price: number; colour: string; label: string }[] = [];

  if (trade.mfe !== null && trade.mfe > 0) {
    lines.push({
      price: long ? trade.entry + trade.mfe : trade.entry - trade.mfe,
      colour: COLOURS.mfe,
      label: `MFE ${inR(trade.mfe, trade)}`,
    });
  }
  if (trade.mae !== null && trade.mae > 0) {
    lines.push({
      price: long ? trade.entry - trade.mae : trade.entry + trade.mae,
      colour: COLOURS.mae,
      label: `MAE ${inR(trade.mae, trade)}`,
    });
  }
  return lines;
}

/**
 * An excursion in R, when R is knowable.
 *
 * R is a money figure and the excursion is a price distance, so the two only convert through a
 * recorded stop. Without one the price distance is printed as itself rather than as a made-up R.
 */
function inR(distance: number, trade: ReplayTrade): string {
  const stop = trade.plannedSl;
  if (stop === null || stop === undefined || trade.entry === null) return distance.toFixed(2);
  const risk = Math.abs(trade.entry - stop);
  if (risk <= 0) return distance.toFixed(2);
  return `${(distance / risk).toFixed(2)}R`;
}

/** Events as ticks on the time axis, in the displayed timeframe's buckets. */
export function eventMarkers(events: ReplayEvent[], seconds: number): ChartMarker[] {
  return events.map((event) => ({
    time: bucket(event.ts, seconds),
    position: "aboveBar" as const,
    shape: "circle" as const,
    color: styleFor(event.kind).colour,
    text: styleFor(event.kind).word,
  }));
}

function bucket(ms: number, seconds: number): number {
  return Math.floor(ms / 1000 / seconds) * seconds;
}
