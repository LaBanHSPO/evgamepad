/**
 * The rAF poll.
 *
 * `navigator.getGamepads()` returns a fresh snapshot every call and the objects it hands back go
 * stale immediately, so nothing here holds one across a frame. The Gamepad API also stays silent
 * until the page has seen a button press (the spec's privacy gesture), which is why the HUD asks
 * for one before it will call the pad connected.
 *
 * Losing focus or the pad does not wait for the next frame: `visibilitychange` and
 * `gamepaddisconnected` push straight through.
 */

import type { PadInput } from "./fsm";
import type { PadProfile } from "./map";
import { AXIS, BUTTON, applyDeadzone, clutchValue, confirmPressed, profileFor } from "./map";

/** Previous frame's pressed state, so every face button is a rising edge. */
export type ButtonSnapshot = Record<number, boolean>;

export interface RawFrame {
  input: PadInput;
  snapshot: ButtonSnapshot;
  sticks: { lsX: number; lsY: number; rsX: number; rsY: number };
  bumpers: { lb: boolean; rb: boolean };
}

function rising(pad: Gamepad, previous: ButtonSnapshot, index: number): boolean {
  return Boolean(pad.buttons[index]?.pressed) && !previous[index];
}

/**
 * One frame, as a pure function of the pad and the previous snapshot.
 *
 * Face buttons are rising edges — a held A arms once, not sixty times a second. The clutch and
 * confirm stay continuous because the FSM applies its own hysteresis and edge rules to them.
 */
export function readFrame(
  pad: Gamepad,
  previous: ButtonSnapshot,
  profile: PadProfile,
  context: { visible: boolean; nowMs: number },
): RawFrame {
  const snapshot: ButtonSnapshot = {};
  pad.buttons.forEach((button, index) => {
    snapshot[index] = button.pressed;
  });

  return {
    input: {
      clutch: clutchValue(pad, profile),
      confirm: confirmPressed(pad, profile),
      a: rising(pad, previous, BUTTON.A),
      b: rising(pad, previous, BUTTON.B),
      x: rising(pad, previous, BUTTON.X),
      y: rising(pad, previous, BUTTON.Y),
      view: rising(pad, previous, BUTTON.VIEW),
      menu: rising(pad, previous, BUTTON.MENU),
      lotUp: rising(pad, previous, BUTTON.DPAD_UP),
      lotDown: rising(pad, previous, BUTTON.DPAD_DOWN),
      symbolLeft: rising(pad, previous, BUTTON.DPAD_LEFT),
      symbolRight: rising(pad, previous, BUTTON.DPAD_RIGHT),
      visible: context.visible,
      padConnected: true,
      nowMs: context.nowMs,
    },
    snapshot,
    sticks: {
      lsX: applyDeadzone(pad.axes[AXIS.LS_X] ?? 0),
      lsY: applyDeadzone(pad.axes[AXIS.LS_Y] ?? 0),
      rsX: applyDeadzone(pad.axes[AXIS.RS_X] ?? 0),
      rsY: applyDeadzone(pad.axes[AXIS.RS_Y] ?? 0),
    },
    bumpers: {
      lb: Boolean(pad.buttons[BUTTON.LB]?.pressed),
      rb: Boolean(pad.buttons[BUTTON.RB]?.pressed),
    },
  };
}

/** The disconnected frame. Sent immediately on unplug or hide, not on the next poll. */
export function absentFrame(nowMs: number, visible: boolean): PadInput {
  return {
    clutch: 0, confirm: false, a: false, b: false, x: false, y: false,
    view: false, menu: false, lotUp: false, lotDown: false,
    symbolLeft: false, symbolRight: false,
    visible, padConnected: false, nowMs,
  };
}

/** First standard-mapping pad in the live snapshot. Never held across frames. */
export function firstPad(): Gamepad | null {
  const pads = navigator.getGamepads?.() ?? [];
  for (const pad of pads) {
    if (pad && profileFor(pad).supported) return pad;
  }
  return null;
}

export interface PollerOptions {
  onFrame: (frame: RawFrame) => void;
  onAbsent: (input: PadInput) => void;
  onProfile?: (profile: PadProfile) => void;
}

export class PadPoller {
  private running = false;
  private snapshot: ButtonSnapshot = {};
  private profile: PadProfile | null = null;
  private paddlesSeen = false;
  private raf = 0;

  constructor(private options: PollerOptions) {}

  start(): void {
    if (this.running) return;
    this.running = true;
    window.addEventListener("gamepaddisconnected", this.handleDisconnect);
    document.addEventListener("visibilitychange", this.handleVisibility);
    this.raf = requestAnimationFrame(this.tick);
  }

  stop(): void {
    this.running = false;
    cancelAnimationFrame(this.raf);
    window.removeEventListener("gamepaddisconnected", this.handleDisconnect);
    document.removeEventListener("visibilitychange", this.handleVisibility);
  }

  private handleDisconnect = (): void => {
    this.profile = null;
    this.snapshot = {};
    this.options.onAbsent(absentFrame(performance.now(), !document.hidden));
  };

  private handleVisibility = (): void => {
    if (document.hidden) this.options.onAbsent(absentFrame(performance.now(), false));
  };

  private tick = (): void => {
    if (!this.running) return;
    // Re-read every frame: a cached Gamepad object is stale the moment the frame ends.
    const pad = firstPad();
    if (pad === null) {
      this.options.onAbsent(absentFrame(performance.now(), !document.hidden));
    } else {
      if (!this.paddlesSeen && pad.buttons.length > 16) {
        this.paddlesSeen = Boolean(pad.buttons[16]?.pressed || pad.buttons[17]?.pressed);
      }
      const profile = profileFor(pad, this.paddlesSeen);
      if (this.profile?.hasPaddles !== profile.hasPaddles || this.profile === null) {
        this.profile = profile;
        this.options.onProfile?.(profile);
      }
      const frame = readFrame(pad, this.snapshot, profile, {
        visible: !document.hidden,
        nowMs: performance.now(),
      });
      this.snapshot = frame.snapshot;
      this.options.onFrame(frame);
    }
    this.raf = requestAnimationFrame(this.tick);
  };
}
