/**
 * Replay: lossless resampling, an honest transport, and the one invariant that matters —
 * no order can be placed from this route.
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { excursionLines, eventMarkers, styleFor, tradeMarkers } from "./Markers";
import { initialBindings, stepBindings } from "./bindings";
import type { ReplayFrame } from "./bindings";
import { TIMEFRAMES, progress, resample, sideForTrade, timeframeLabel, toPrice } from "./resample";
import {
  MAX_AUDIBLE_SPEED,
  advance,
  audioCue,
  initialState,
  nearestEvent,
  seekTo,
  stepSpeed,
  togglePlay,
  windowOf,
} from "./transport";
import type { Memo, ReplayTrade, Tape } from "./types";

const here = dirname(fileURLToPath(import.meta.url));
const SCALE = 100_000;
const T0 = 1_788_000_000;

/** A tape of `n` one-second bars, rising by one scaled unit a second, with a two-unit spread. */
function tapeOf(n: number, from = T0): Tape {
  const ts: number[] = [];
  const bid: number[] = [];
  for (let i = 0; i < n; i += 1) {
    ts.push(from + i);
    bid.push(100_000 + i);
  }
  return {
    fromTs: from, toTs: from + n - 1, dtS: 1, n, mfe: 0.1, mae: 0.05, ts,
    bidO: bid.slice(), bidH: bid.map((v) => v + 3), bidL: bid.map((v) => v - 3), bidC: bid.slice(),
    askO: bid.map((v) => v + 2), askH: bid.map((v) => v + 5), askL: bid.map((v) => v - 1),
    askC: bid.map((v) => v + 2), nTicks: bid.map(() => 4), version: 1,
  };
}

const TRADE: ReplayTrade = {
  cid: "cid-1", sessionId: "2026-08-31", positionId: 7, symbol: "XAUUSD", side: "buy", lots: 0.01,
  entry: 2458.1, exit: 2473.0, openedAt: (T0 + 300) * 1000, closedAt: (T0 + 420) * 1000,
  netPnlUsd: 14.9, rUsd: 20, rMultiple: 0.745, mfe: 3.0, mae: 1.0, adherence: null,
  tiltAtEntry: 0.21, plannedSl: 2456.1,
};

function frame(over: Partial<ReplayFrame["input"]> = {}, rest: Partial<ReplayFrame> = {}): ReplayFrame {
  return {
    input: {
      clutch: 0, confirm: false, a: false, b: false, x: false, y: false, view: false, menu: false,
      lotUp: false, lotDown: false, symbolLeft: false, symbolRight: false,
      visible: true, padConnected: true, nowMs: 0, ...over,
    },
    bumpers: { lb: false, rb: false },
    rsX: 0,
    ...rest,
  };
}

// -- resampling ---------------------------------------------------------------------

describe("resampling", () => {
  it("aggregates one-second bars losslessly onto integer prices", () => {
    const tape = tapeOf(60);
    const candles = resample(tape, "bid", 5);

    expect(candles).toHaveLength(12);
    for (const candle of candles) {
      // Every value is one that was actually in the tape — nothing averaged, nothing rounded.
      expect(Number.isInteger(candle.open)).toBe(true);
      expect(candle.high).toBeGreaterThanOrEqual(candle.low);
    }
    expect(candles[0].open).toBe(tape.bidO[0]);
    expect(candles[0].close).toBe(tape.bidC[4]);
    expect(candles[0].high).toBe(Math.max(...tape.bidH.slice(0, 5)));
    expect(candles[0].low).toBe(Math.min(...tape.bidL.slice(0, 5)));
  });

  it("conserves the tick count across every timeframe", () => {
    const tape = tapeOf(300);
    const total = tape.nTicks.reduce((a, b) => a + b, 0);
    for (const seconds of TIMEFRAMES) {
      const sum = resample(tape, "bid", seconds).reduce((a, c) => a + c.ticks, 0);
      expect(sum, `timeframe ${seconds}s dropped ticks`).toBe(total);
    }
  });

  it("keeps the first open and the last close whatever the timeframe", () => {
    const tape = tapeOf(300);
    for (const seconds of TIMEFRAMES) {
      const candles = resample(tape, "bid", seconds);
      expect(candles[0].open).toBe(tape.bidO[0]);
      expect(candles[candles.length - 1].close).toBe(tape.bidC[tape.n - 1]);
    }
  });

  it("buckets on wall-clock boundaries, not on the first bar", () => {
    // A tape that starts mid-bucket must still align to the minute, or two trades on the same
    // evening would draw candles that do not line up.
    const candles = resample(tapeOf(120, T0 + 7), "bid", 60);
    for (const candle of candles) expect(candle.time % 60).toBe(0);
  });

  it("charts a buy on the bid and a sell on the ask", () => {
    // A buy is exited on the bid and a sell on the ask. Charting both off one side would put the
    // spread-sized asymmetry back into every sell's adverse move.
    expect(sideForTrade("buy")).toBe("bid");
    expect(sideForTrade("sell")).toBe("ask");

    const tape = tapeOf(10);
    expect(resample(tape, "ask", 5)[0].open).toBeGreaterThan(resample(tape, "bid", 5)[0].open);
  });

  it("refuses a zero or negative timeframe rather than looping forever", () => {
    expect(() => resample(tapeOf(10), "bid", 0)).toThrow();
  });

  it("divides by the scale once, at the point of drawing", () => {
    expect(toPrice(245_810_000, SCALE)).toBe(2458.1);
  });

  it("labels timeframes the way the player reads them", () => {
    expect(timeframeLabel(5)).toBe("5s");
    expect(timeframeLabel(300)).toBe("5m");
  });

  it("reports the playhead's progress through the window", () => {
    const tape = tapeOf(101);
    expect(progress(tape, T0 * 1000)).toBe(0);
    expect(progress(tape, (T0 + 50) * 1000)).toBeCloseTo(0.5, 2);
    expect(progress(tape, (T0 + 999) * 1000)).toBe(1);
  });
});

// -- transport ----------------------------------------------------------------------

describe("transport", () => {
  const window_ = windowOf(tapeOf(600));

  it("starts paused at the beginning of the window", () => {
    const state = initialState(window_);
    expect(state.playing).toBe(false);
    expect(state.playheadMs).toBe(window_.fromMs);
  });

  it("advances at the chosen speed", () => {
    const playing = togglePlay(initialState(window_), window_);
    const at1x = advance(playing, window_, 1000);
    expect(at1x.playheadMs - playing.playheadMs).toBe(1000);

    const at4x = advance(stepSpeed(stepSpeed(playing, 1), 1), window_, 1000);
    expect(at4x.playheadMs - playing.playheadMs).toBe(4000);
  });

  it("steps speed without wrapping past the ends", () => {
    let state = initialState(window_);
    expect(stepSpeed(state, -1).speed).toBe(0.5);
    for (let i = 0; i < 10; i += 1) state = stepSpeed(state, 1);
    expect(state.speed).toBe(4);
  });

  it("pauses at the end rather than looping", () => {
    // A replay that loops silently re-shows the same mistake instead of ending.
    const near = { ...togglePlay(initialState(window_), window_), playheadMs: window_.toMs - 100 };
    const done = advance(near, window_, 5000);
    expect(done.playheadMs).toBe(window_.toMs);
    expect(done.playing).toBe(false);
  });

  it("restarts from the top when play is pressed at the end", () => {
    const ended = { ...initialState(window_), playheadMs: window_.toMs };
    const restarted = togglePlay(ended, window_);
    expect(restarted.playing).toBe(true);
    expect(restarted.playheadMs).toBe(window_.fromMs);
  });

  it("ignores stick noise inside the deadzone", () => {
    const state = initialState(window_);
    const nudged = advance(state, window_, 100, 0.15);
    expect(nudged.playheadMs).toBe(state.playheadMs);
    expect(nudged.scrubbing).toBe(false);
  });

  it("scrubs both ways and stays inside the window", () => {
    const state = initialState(window_);
    const forward = advance(state, window_, 1000, 1);
    expect(forward.playheadMs).toBeGreaterThan(state.playheadMs);
    expect(forward.scrubbing).toBe(true);

    // Scrubbing hard left off the start clamps rather than running off the tape.
    let back = forward;
    for (let i = 0; i < 100; i += 1) back = advance(back, window_, 1000, -1);
    expect(back.playheadMs).toBe(window_.fromMs);
  });

  it("lets the stick win over playback, then resumes where it was let go", () => {
    const playing = togglePlay(initialState(window_), window_);
    const scrubbed = advance(playing, window_, 1000, 1);
    expect(scrubbed.scrubbing).toBe(true);

    const released = advance(scrubbed, window_, 1000, 0);
    expect(released.scrubbing).toBe(false);
    expect(released.playing).toBe(true);
    expect(released.playheadMs).toBeGreaterThan(scrubbed.playheadMs);
  });

  it("seeks to an exact moment, clamped", () => {
    const state = initialState(window_);
    expect(seekTo(state, window_.fromMs + 5000, window_).playheadMs).toBe(window_.fromMs + 5000);
    expect(seekTo(state, window_.toMs + 999_999, window_).playheadMs).toBe(window_.toMs);
  });

  it("names the nearest event, and nothing when there is none close", () => {
    const events = [{ ts: 1000, kind: "arm", label: "armed" },
                    { ts: 60_000, kind: "fire", label: "fired" }];
    expect(nearestEvent(events, 1200)?.label).toBe("armed");
    expect(nearestEvent(events, 30_000)).toBeNull();
  });
});

// -- memo audio ---------------------------------------------------------------------

describe("memo audio", () => {
  const window_ = windowOf(tapeOf(600));
  const memos: Memo[] = [{ id: "m1", ts: T0 * 1000 + 10_000, durMs: 4_000, transcript: null }];

  it("is silent outside the memo and in step inside it", () => {
    const before = seekTo(initialState(window_), T0 * 1000 + 5_000, window_);
    expect(audioCue(before, memos).memoId).toBeNull();

    const inside = seekTo(initialState(window_), T0 * 1000 + 12_000, window_);
    const cue = audioCue({ ...inside, playing: true }, memos);
    expect(cue.memoId).toBe("m1");
    expect(cue.offsetS).toBeCloseTo(2, 3);
    expect(cue.playing).toBe(true);
  });

  it("takes its length from durMs, never from the element", () => {
    // Chrome's MediaRecorder WebM reports `Infinity` for `audio.duration`, so the span has to come
    // from what was recorded at capture time.
    const past = seekTo(initialState(window_), T0 * 1000 + 20_000, window_);
    expect(audioCue({ ...past, playing: true }, memos).memoId).toBeNull();
  });

  it("holds the audio still while scrubbing and re-syncs on release", () => {
    const at = seekTo(initialState(window_), T0 * 1000 + 11_000, window_);
    const scrubbing = audioCue({ ...at, playing: true, scrubbing: true }, memos);
    expect(scrubbing.playing).toBe(false);
    expect(scrubbing.offsetS).toBeCloseTo(1, 3);

    const released = audioCue({ ...at, playing: true, scrubbing: false }, memos);
    expect(released.playing).toBe(true);
  });

  it("mutes above 2x rather than pitch-shifting", () => {
    const at = seekTo(initialState(window_), T0 * 1000 + 11_000, window_);
    const fast = audioCue({ ...at, playing: true, speed: 4 }, memos);
    expect(fast.muted).toBe(true);
    expect(fast.playing).toBe(false);
    expect(fast.playbackRate).toBe(1);

    const audible = audioCue({ ...at, playing: true, speed: MAX_AUDIBLE_SPEED }, memos);
    expect(audible.muted).toBe(false);
    expect(audible.playbackRate).toBe(MAX_AUDIBLE_SPEED);
  });

  it("replays a trade with no memo exactly the same, minus the audio", () => {
    const at = seekTo(initialState(window_), T0 * 1000 + 11_000, window_);
    expect(audioCue({ ...at, playing: true }, []).memoId).toBeNull();
  });
});

// -- markers ------------------------------------------------------------------------

describe("markers", () => {
  it("draws entry and exit from the fill, not from the bars", () => {
    const markers = tradeMarkers(TRADE, 60);
    expect(markers).toHaveLength(2);
    expect(markers[0].text).toContain(String(TRADE.entry));
    expect(markers[1].text).toContain(String(TRADE.exit));
    // A buy enters with an up arrow below the bar and exits with a down arrow above it.
    expect(markers[0].shape).toBe("arrowUp");
    expect(markers[1].shape).toBe("arrowDown");
  });

  it("flips the arrows for a sell", () => {
    const markers = tradeMarkers({ ...TRADE, side: "sell" }, 60);
    expect(markers[0].shape).toBe("arrowDown");
    expect(markers[1].shape).toBe("arrowUp");
  });

  it("puts the excursions on the right side of the entry", () => {
    const buy = excursionLines(TRADE);
    expect(buy[0].price).toBeGreaterThan(TRADE.entry!);
    expect(buy[1].price).toBeLessThan(TRADE.entry!);

    const sell = excursionLines({ ...TRADE, side: "sell" });
    expect(sell[0].price).toBeLessThan(TRADE.entry!);
    expect(sell[1].price).toBeGreaterThan(TRADE.entry!);
  });

  it("prints an excursion in R only when a stop makes R knowable", () => {
    // R is money and an excursion is a price distance; without a recorded stop the two do not
    // convert, and printing a made-up R would be worse than printing the distance.
    expect(excursionLines(TRADE)[0].label).toContain("R");
    expect(excursionLines({ ...TRADE, plannedSl: null })[0].label).not.toContain("R");
  });

  it("labels every event kind from a fixed table, never from player text", () => {
    const events = [
      { ts: T0 * 1000, kind: "arm", label: "armed" },
      { ts: T0 * 1000 + 1000, kind: "cancel", label: "stood down (spread)" },
      { ts: T0 * 1000 + 2000, kind: "tilt_band_change", label: "tilt hot" },
    ];
    const markers = eventMarkers(events, 5);
    expect(markers.map((m) => m.text)).toEqual(["arm", "stood down", "tilt"]);
    for (const marker of markers) expect(marker.time % 5).toBe(0);
  });

  it("falls back to the kind rather than crashing on an unknown event", () => {
    expect(styleFor("something_new").word).toBe("something_new");
  });
});

// -- the invariant ------------------------------------------------------------------

describe("no order can be placed from a replay", () => {
  it("maps every pad control to a transport action and nothing else", () => {
    const pressed = stepBindings(initialBindings, frame(
      { a: true, b: true, lotUp: true, lotDown: true },
      { bumpers: { lb: true, rb: true }, rsX: 1 },
    ));
    const kinds = pressed.actions.map((action) => action.kind).sort();
    expect(kinds).toEqual(["exit", "playPause", "speed", "speed", "step", "step", "zoom"]);
  });

  it("fires each action once per press, not once per frame", () => {
    const first = stepBindings(initialBindings, frame({ a: true }));
    expect(first.actions).toHaveLength(1);
    const held = stepBindings(first.state, frame({ a: true }));
    expect(held.actions).toEqual([]);
  });

  it("never constructs an intent, because the action type has no case for one", () => {
    const source = readFileSync(resolve(here, "bindings.ts"), "utf8");
    for (const verb of ["intent", "sendIntent", "flatten", "closePosition"]) {
      expect(source).not.toContain(`${verb}(`);
    }
  });

  it("imports neither the agent nor the socket client anywhere on the route", () => {
    // This is the real guarantee: the FSM is not merely LOCKED here, it is not mounted at all.
    for (const file of ["Replay.tsx", "Chart.tsx", "Timeline.tsx", "transport.ts", "Markers.ts",
                        "resample.ts", "bindings.ts"]) {
      const source = readFileSync(resolve(here, file), "utf8");
      expect(source, `${file} imports the agent`).not.toMatch(/from "\.\.\/agent"/);
      expect(source, `${file} imports the client`).not.toMatch(/from "\.\.\/net\/ws"/);
    }
  });

  it("reaches the gateway only through the replay reads and the review-evidence write", () => {
    // Phase 11 added one write: recording that a trade was reviewed, which its Review axis
    // credits. It goes to the score surface, so `/api/replay/*` itself stays read-only — the
    // gateway-side guard on that is `test_every_statement_replay_runs_is_a_select`.
    const source = readFileSync(resolve(here, "Replay.tsx"), "utf8");
    const targets = [...source.matchAll(/fetch\(\s*(?:apiUrl\()?\s*(`[^`]*`|"[^"]*")/g)].map((m) => m[1]);
    expect(targets.length).toBeGreaterThan(0);
    for (const target of targets) {
      expect(target).toMatch(/\/api\/(replay|score\/evidence)\//);
    }
    // Whatever it posts, it is never an order.
    for (const verb of ["intent", "order", "position", "flatten", "panic"]) {
      expect(source).not.toContain(`/api/${verb}`);
    }
  });
});
