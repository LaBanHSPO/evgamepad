/**
 * rAF poll of the Gamepad API.
 *
 * The Gamepad object is a **snapshot**, not a live view: Chrome hands back a new
 * one each call, and caching it gives you buttons frozen at the moment you
 * cached. So `navigator.getGamepads()` is called every frame, every time.
 *
 * `visibilitychange` and `gamepaddisconnected` are handled as *events* rather
 * than as poll results, because rAF stops firing in a hidden tab -- waiting for
 * the next frame to notice the tab is gone would leave an ARM live for as long
 * as the tab stayed hidden.
 */

import { AXIS, BUTTON, CLUTCH_OFF, CLUTCH_ON, applyDeadzone, isSupportedPad } from "./map";
import type { PadProfile } from "./map";
import { DEFAULT_PROFILE } from "./map";

export type RawFrame = {
  at: number;
  connected: boolean;
  visible: boolean;
  buttons: boolean[];
  values: number[];
  axes: number[];
  id: string;
  mapping: string;
};

export type PadSnapshot = RawFrame & {
  clutch: boolean;
  confirm: boolean;
  lt: number;
  rt: number;
  ls: { x: number; y: number };
  rs: { x: number; y: number };
};

/** Hysteresis needs the previous decision, so the reader is stateful. */
export class PadReader {
  private clutchLatched = false;
  profile: PadProfile;

  constructor(profile: PadProfile = DEFAULT_PROFILE) {
    this.profile = profile;
  }

  read(frame: RawFrame): PadSnapshot {
    const lt = frame.values[BUTTON.LT] ?? 0;
    const rt = frame.values[BUTTON.RT] ?? 0;

    const aliasClutch =
      this.profile.clutchAlias !== null && (frame.buttons[this.profile.clutchAlias] ?? false);
    const aliasConfirm =
      this.profile.confirmAlias !== null && (frame.buttons[this.profile.confirmAlias] ?? false);

    // Schmitt trigger: cross 0.80 to engage, fall below 0.50 to release. A
    // single threshold chatters, and a chattering clutch cancels a live ARM.
    if (this.clutchLatched) {
      if (lt < CLUTCH_OFF && !aliasClutch) this.clutchLatched = false;
    } else if (lt >= CLUTCH_ON || aliasClutch) {
      this.clutchLatched = true;
    }

    if (!frame.connected || !frame.visible) this.clutchLatched = false;

    return {
      ...frame,
      lt,
      rt,
      clutch: this.clutchLatched,
      confirm: (frame.buttons[BUTTON.RT] ?? false) || aliasConfirm,
      ls: {
        x: applyDeadzone(frame.axes[AXIS.LS_X] ?? 0),
        y: applyDeadzone(frame.axes[AXIS.LS_Y] ?? 0),
      },
      rs: {
        x: applyDeadzone(frame.axes[AXIS.RS_X] ?? 0),
        y: applyDeadzone(frame.axes[AXIS.RS_Y] ?? 0),
      },
    };
  }
}

export function readGamepad(visible: boolean, at: number): RawFrame {
  // Never cached: see the module docstring.
  const pads = typeof navigator !== "undefined" ? navigator.getGamepads?.() ?? [] : [];
  const pad = [...pads].find((p): p is Gamepad => p !== null && isSupportedPad(p));
  if (!pad) {
    return {
      at,
      connected: false,
      visible,
      buttons: [],
      values: [],
      axes: [],
      id: "",
      mapping: "",
    };
  }
  return {
    at,
    connected: true,
    visible,
    buttons: pad.buttons.map((b) => b.pressed),
    values: pad.buttons.map((b) => b.value),
    axes: [...pad.axes],
    id: pad.id,
    mapping: pad.mapping,
  };
}

export type PollHandle = { stop: () => void };

/**
 * Drive `onFrame` from rAF, and force a frame on the events rAF cannot deliver.
 */
export function startPolling(onFrame: (frame: RawFrame) => void): PollHandle {
  let running = true;
  let raf = 0;

  const tick = () => {
    if (!running) return;
    onFrame(readGamepad(document.visibilityState === "visible", performance.now()));
    raf = requestAnimationFrame(tick);
  };

  // Synthesised immediately, not on the next frame: a hidden tab gets no frames.
  const onVisibility = () => {
    onFrame(readGamepad(document.visibilityState === "visible", performance.now()));
  };
  const onDisconnect = () => {
    onFrame({
      at: performance.now(),
      connected: false,
      visible: document.visibilityState === "visible",
      buttons: [],
      values: [],
      axes: [],
      id: "",
      mapping: "",
    });
  };

  document.addEventListener("visibilitychange", onVisibility);
  window.addEventListener("gamepaddisconnected", onDisconnect);
  window.addEventListener("blur", onVisibility);
  raf = requestAnimationFrame(tick);

  return {
    stop: () => {
      running = false;
      cancelAnimationFrame(raf);
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("gamepaddisconnected", onDisconnect);
      window.removeEventListener("blur", onVisibility);
    },
  };
}

/** Best-effort rumble. The visual confirm is canonical; this is a bonus. */
export function rumble(strength: number, ms: number): void {
  const pads = typeof navigator !== "undefined" ? navigator.getGamepads?.() ?? [] : [];
  for (const pad of pads) {
    const actuator = (pad as unknown as { vibrationActuator?: { playEffect?: Function } })
      ?.vibrationActuator;
    if (!actuator?.playEffect) continue;
    try {
      actuator.playEffect("dual-rumble", {
        duration: ms,
        strongMagnitude: strength,
        weakMagnitude: strength * 0.6,
      });
    } catch {
      // Firefox returns null, Safari throws. Neither is a problem worth showing.
    }
  }
}
