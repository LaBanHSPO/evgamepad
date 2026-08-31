/**
 * The pad, on the replay route.
 *
 * This table is the whole reason no order can be placed from a replay: it maps pad input to
 * **transport actions only**, and there is no branch, anywhere, from a replay action to an intent.
 * The order FSM is not merely `LOCKED` here — it is not mounted at all, because selecting a screen
 * unmounts the previous one, taking the agent, its poller and its socket with it.
 *
 * `replay.test.ts` asserts both halves of that: this table contains no order action, and the
 * replay surface imports neither the agent nor the client.
 */

import type { PadInput } from "../pad/fsm";

export type ReplayAction =
  | { kind: "playPause" }
  | { kind: "speed"; step: 1 | -1 }
  | { kind: "zoom"; step: 1 | -1 }
  | { kind: "step"; step: 1 | -1 }
  | { kind: "exit" };

/** What the HUD prints under the chart, and the only actions the route can produce. */
export const CONTROLS: { input: string; action: string }[] = [
  { input: "LS ←→", action: "scrub" },
  { input: "RS ←→", action: "zoom the window" },
  { input: "A", action: "play / pause" },
  { input: "D-pad ↑↓", action: "speed 0.5x - 4x" },
  { input: "LB / RB", action: "previous / next trade" },
  { input: "B", action: "exit" },
];

/** Held buttons the previous frame, so every action fires on a rising edge exactly once. */
export interface BindingState {
  a: boolean;
  b: boolean;
  up: boolean;
  down: boolean;
  lb: boolean;
  rb: boolean;
  zoomIn: boolean;
  zoomOut: boolean;
}

export const initialBindings: BindingState = {
  a: false, b: false, up: false, down: false, lb: false, rb: false, zoomIn: false, zoomOut: false,
};

export interface ReplayFrame {
  input: PadInput;
  bumpers: { lb: boolean; rb: boolean };
  /** Right stick X, for zoom. Left stick X is read by the transport for scrubbing. */
  rsX: number;
}

const ZOOM_DEADZONE = 0.5;

/** One frame in, the actions it newly asks for out. Pure, so the tests need no pad. */
export function stepBindings(
  state: BindingState, frame: ReplayFrame,
): { state: BindingState; actions: ReplayAction[] } {
  const next: BindingState = {
    a: frame.input.a,
    b: frame.input.b,
    // The same physical D-pad the HUD uses for lot steps. Nothing on this route sizes an order,
    // so the buttons are free to mean speed here.
    up: frame.input.lotUp,
    down: frame.input.lotDown,
    lb: frame.bumpers.lb,
    rb: frame.bumpers.rb,
    zoomIn: frame.rsX > ZOOM_DEADZONE,
    zoomOut: frame.rsX < -ZOOM_DEADZONE,
  };

  const actions: ReplayAction[] = [];
  if (rising(state.a, next.a)) actions.push({ kind: "playPause" });
  if (rising(state.up, next.up)) actions.push({ kind: "speed", step: 1 });
  if (rising(state.down, next.down)) actions.push({ kind: "speed", step: -1 });
  if (rising(state.zoomIn, next.zoomIn)) actions.push({ kind: "zoom", step: -1 });
  if (rising(state.zoomOut, next.zoomOut)) actions.push({ kind: "zoom", step: 1 });
  if (rising(state.lb, next.lb)) actions.push({ kind: "step", step: -1 });
  if (rising(state.rb, next.rb)) actions.push({ kind: "step", step: 1 });
  if (rising(state.b, next.b)) actions.push({ kind: "exit" });

  return { state: next, actions };
}

function rising(before: boolean, after: boolean): boolean {
  return after && !before;
}
