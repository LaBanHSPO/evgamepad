/**
 * The replay transport: a playhead, a speed, and where the memo audio should be.
 *
 * Pure on purpose. `advance` takes the elapsed wall time and returns the next state, so the whole
 * scrub-and-play behaviour is testable without a chart, a pad, or an `<audio>` element. The React
 * layer's only job is to call `advance` once a frame and push the result at the DOM.
 *
 * Two rules the audio obeys, both from the plan and both about not lying to the player:
 *
 * - Duration comes from the stored `durMs`, **never** `audio.duration`. Chrome's MediaRecorder
 *   WebM reports `Infinity`, and a memo that claims to be infinitely long desynchronises the
 *   moment you scrub.
 * - Above 2x the memo is muted rather than pitch-shifted. A chipmunk voice is not a review.
 */

import type { Memo, Tape } from "./types";

export const SPEEDS = [0.5, 1, 2, 4] as const;
export type Speed = (typeof SPEEDS)[number];

/** Past this, the memo is muted instead of played faster. */
export const MAX_AUDIBLE_SPEED = 2;

/** How far past a memo's end the playhead may sit and still count as inside it. */
const AUDIO_EPSILON_MS = 50;

/** Left stick deadzone, and how much window a full deflection covers per second. */
export const SCRUB_DEADZONE = 0.2;
export const SCRUB_SPAN_PER_S = 0.25;

export interface TransportState {
  /** Playhead in unix ms. Always inside the tape window. */
  playheadMs: number;
  playing: boolean;
  speed: Speed;
  /** Set while the stick is off-centre; play resumes from wherever it is let go. */
  scrubbing: boolean;
}

export interface Window {
  fromMs: number;
  toMs: number;
}

/** What the `<audio>` element should be doing right now. The React layer just applies it. */
export interface AudioCue {
  memoId: string | null;
  /** Seconds into the memo the playhead sits at. Meaningless when `memoId` is null. */
  offsetS: number;
  playing: boolean;
  muted: boolean;
  playbackRate: number;
}

export const SILENT: AudioCue = {
  memoId: null, offsetS: 0, playing: false, muted: false, playbackRate: 1,
};

export function windowOf(tape: Tape): Window {
  return { fromMs: tape.fromTs * 1000, toMs: tape.toTs * 1000 };
}

export function initialState(window: Window): TransportState {
  return { playheadMs: window.fromMs, playing: false, speed: 1, scrubbing: false };
}

function clampToWindow(ms: number, window: Window): number {
  return Math.max(window.fromMs, Math.min(window.toMs, ms));
}

/**
 * One frame of playback.
 *
 * Scrubbing wins over playing: the stick is a direct instruction, so while it is off-centre the
 * clock does not also advance. Reaching the end pauses rather than looping — a replay that loops
 * silently re-shows you the same mistake instead of ending.
 */
export function advance(
  state: TransportState, window: Window, elapsedMs: number, axis = 0,
): TransportState {
  const deflection = Math.abs(axis) < SCRUB_DEADZONE ? 0 : axis;
  if (deflection !== 0) {
    const span = window.toMs - window.fromMs;
    const delta = deflection * span * SCRUB_SPAN_PER_S * (elapsedMs / 1000);
    return {
      ...state,
      scrubbing: true,
      playheadMs: clampToWindow(state.playheadMs + delta, window),
    };
  }

  const settled = state.scrubbing ? { ...state, scrubbing: false } : state;
  if (!settled.playing) return settled;

  const next = settled.playheadMs + elapsedMs * settled.speed;
  if (next >= window.toMs) {
    return { ...settled, playheadMs: window.toMs, playing: false };
  }
  return { ...settled, playheadMs: next };
}

export function togglePlay(state: TransportState, window: Window): TransportState {
  // Pressing play at the very end restarts rather than doing nothing at all.
  if (!state.playing && state.playheadMs >= window.toMs) {
    return { ...state, playing: true, playheadMs: window.fromMs };
  }
  return { ...state, playing: !state.playing };
}

/** D-pad up and down step through the speeds; the ends hold rather than wrapping. */
export function stepSpeed(state: TransportState, step: 1 | -1): TransportState {
  const index = SPEEDS.indexOf(state.speed);
  const next = Math.max(0, Math.min(SPEEDS.length - 1, index + step));
  return { ...state, speed: SPEEDS[next] };
}

export function seekTo(state: TransportState, ms: number, window: Window): TransportState {
  return { ...state, playheadMs: clampToWindow(ms, window), scrubbing: false };
}

/**
 * The memo the playhead is inside, if any, and how it should be playing.
 *
 * Spans are computed from `durMs`, so scrubbing away silences the memo and scrubbing back in
 * resumes it at the right offset rather than from wherever the element happened to be.
 */
export function audioCue(state: TransportState, memos: Memo[]): AudioCue {
  const active = memos.find(
    (memo) => state.playheadMs >= memo.ts
      && state.playheadMs < memo.ts + memo.durMs + AUDIO_EPSILON_MS,
  );
  if (!active) return SILENT;

  const muted = state.speed > MAX_AUDIBLE_SPEED;
  return {
    memoId: active.id,
    offsetS: Math.max(0, (state.playheadMs - active.ts) / 1000),
    // A paused or scrubbing playhead holds the audio still; only real playback plays it.
    playing: state.playing && !state.scrubbing && !muted,
    muted,
    playbackRate: muted ? 1 : state.speed,
  };
}

/** The event nearest the playhead, for the label the rail shows while scrubbing. */
export function nearestEvent<T extends { ts: number }>(
  events: T[], playheadMs: number, withinMs = 5_000,
): T | null {
  let best: T | null = null;
  let bestGap = Infinity;
  for (const event of events) {
    const gap = Math.abs(event.ts - playheadMs);
    if (gap < bestGap) {
      best = event;
      bestGap = gap;
    }
  }
  return best !== null && bestGap <= withinMs ? best : null;
}
