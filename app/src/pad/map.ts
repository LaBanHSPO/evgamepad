/**
 * 8BitDo Ultimate 2 Wireless -> intents, on Chrome's standard Xbox mapping.
 *
 * The default map uses only buttons the standard 17-button mapping guarantees.
 * L4/R4 are paddles that most browsers do not expose at all, so they are opt-in
 * aliases enabled by a first-run probe that watches the extra indices actually
 * change -- never assumed from the pad's `id`.
 *
 * Deliberately absent: any binding from an analog stick to an order. Sticks pan
 * the chart and stage an SL/TP preview. Nothing else.
 */

/** Standard mapping indices (https://w3c.github.io/gamepad/#remapping). */
export const BUTTON = {
  A: 0,
  B: 1,
  X: 2,
  Y: 3,
  LB: 4,
  RB: 5,
  LT: 6,
  RT: 7,
  VIEW: 8,
  MENU: 9,
  L3: 10,
  R3: 11,
  DPAD_UP: 12,
  DPAD_DOWN: 13,
  DPAD_LEFT: 14,
  DPAD_RIGHT: 15,
} as const;

export const AXIS = { LS_X: 0, LS_Y: 1, RS_X: 2, RS_Y: 3 } as const;

/** First index past the standard 17. A paddle, if this pad reports one at all. */
export const EXTRA_BUTTON_START = 17;

/**
 * Trigger hysteresis. One threshold would chatter the clutch around the
 * crossing point, and a clutch that flickers mid-ARM is a cancelled fire.
 */
export const CLUTCH_ON = 0.8;
export const CLUTCH_OFF = 0.5;

/** Sticks idle noisily. Anything under this is not an input. */
export const STICK_DEADZONE = 0.12;

/** Both bumpers inside this window is a chord, not two timeframe changes. */
export const CHORD_WINDOW_MS = 120;

/** L3+R3 held this long is the backup panic, for a pad with a dead face button. */
export const PANIC_CHORD_MS = 1500;

export type PadProfile = {
  /** Extra button index acting as a clutch alias, or null for LT only. */
  clutchAlias: number | null;
  /** Extra button index acting as a confirm alias, or null for RT only. */
  confirmAlias: number | null;
  /** Nintendo layout swaps the physical A/B positions. Default is Xbox. */
  swapAB: boolean;
};

export const DEFAULT_PROFILE: PadProfile = {
  clutchAlias: null,
  confirmAlias: null,
  swapAB: false,
};

/**
 * Chrome reports `mapping: "standard"` for the 2.4G dongle, which presents an
 * XInput-class device. Some builds report an empty mapping for the same pad, so
 * an 8BitDo `id` with a plausible button count is accepted too -- refusing it
 * would leave the player with a working pad and a dead HUD.
 */
export function isSupportedPad(pad: Pick<Gamepad, "id" | "mapping" | "buttons">): boolean {
  if (pad.mapping === "standard") return true;
  const looks8BitDo = /8bitdo|ultimate/i.test(pad.id);
  return looks8BitDo && pad.buttons.length >= 16;
}

export type ProbeState = {
  /** Baseline reading for each extra index, captured on the first frame. */
  baseline: Map<number, number>;
  moved: Set<number>;
};

export function beginProbe(): ProbeState {
  return { baseline: new Map(), moved: new Set() };
}

/**
 * Watch the indices past the standard 17 and record which ones actually move.
 * A paddle that never moves stays unbound, so the default LT/RT map keeps
 * working rather than silently routing the clutch to a button that does not
 * exist.
 */
export function probeFrame(state: ProbeState, buttons: readonly { value: number }[]): ProbeState {
  for (let i = EXTRA_BUTTON_START; i < buttons.length; i += 1) {
    const value = buttons[i]!.value;
    if (!state.baseline.has(i)) {
      state.baseline.set(i, value);
      continue;
    }
    if (Math.abs(value - state.baseline.get(i)!) > 0.5) state.moved.add(i);
  }
  return state;
}

/**
 * Turn probe results into a profile. The first moved extra becomes the clutch
 * alias and the second the confirm alias, matching the calibration overlay's
 * "hold L4, then RT" order.
 */
export function profileFromProbe(state: ProbeState, base = DEFAULT_PROFILE): PadProfile {
  const moved = [...state.moved].sort((a, b) => a - b);
  return {
    ...base,
    clutchAlias: moved[0] ?? null,
    confirmAlias: moved[1] ?? null,
  };
}

export function applyDeadzone(value: number, deadzone = STICK_DEADZONE): number {
  return Math.abs(value) < deadzone ? 0 : value;
}
