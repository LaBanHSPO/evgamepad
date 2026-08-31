/**
 * 8BitDo Ultimate 2 mapping, on Chrome's standard 17-button Xbox layout.
 *
 * The default map uses only indices every standard pad has, so the game works on the 2.4G dongle
 * with no calibration. L4/R4 are extras that exist on this pad but not in the standard mapping —
 * they are adopted only after a probe actually sees them move, never assumed.
 *
 * Lot size is deliberately not bound to a trigger: LT is the clutch, and a control that changes
 * size must not share a finger with the one that authorises a fire.
 */

/** Standard-mapping button indices (Chrome, `mapping === "standard"`). */
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

/** Paddles, present on the Ultimate 2 but outside the standard mapping. */
export const EXTRA_BUTTON = { L4: 16, R4: 17 } as const;

export const AXIS = { LS_X: 0, LS_Y: 1, RS_X: 2, RS_Y: 3 } as const;

/** Clutch hysteresis: engage high, release low, so a resting finger cannot chatter. */
export const CLUTCH_ON = 0.8;
export const CLUTCH_OFF = 0.5;

/** Stick drift must never reach a control. */
export const STICK_DEADZONE = 0.12;

/** Both bumpers inside this window is a chord, not two timeframe changes. */
export const CHORD_WINDOW_MS = 120;

export interface PadProfile {
  /** True when Chrome reports the standard layout, or the id is a recognisable 8BitDo. */
  supported: boolean;
  /** Extras adopted only after the probe saw them change. */
  hasPaddles: boolean;
  id: string;
  mapping: string;
  buttons: number;
}

const EIGHTBITDO = /8bitdo|ultimate\s*2/i;

export function profileFor(pad: Gamepad, paddlesSeen = false): PadProfile {
  // An empty `mapping` with an 8BitDo id still gets in: the dongle presents an XInput-class pad
  // and some Chrome builds report the layout late.
  const supported = pad.mapping === "standard" || EIGHTBITDO.test(pad.id);
  return {
    supported,
    hasPaddles: paddlesSeen && pad.buttons.length > EXTRA_BUTTON.R4,
    id: pad.id,
    mapping: pad.mapping,
    buttons: pad.buttons.length,
  };
}

/** Clutch value, reading the paddle alias only once the probe has proven it exists. */
export function clutchValue(pad: Gamepad, profile: PadProfile): number {
  const trigger = pad.buttons[BUTTON.LT]?.value ?? 0;
  if (!profile.hasPaddles) return trigger;
  return Math.max(trigger, pad.buttons[EXTRA_BUTTON.L4]?.pressed ? 1 : 0);
}

export function confirmPressed(pad: Gamepad, profile: PadProfile): boolean {
  const trigger = (pad.buttons[BUTTON.RT]?.value ?? 0) >= CLUTCH_ON;
  if (!profile.hasPaddles) return trigger;
  return trigger || Boolean(pad.buttons[EXTRA_BUTTON.R4]?.pressed);
}

/** Hysteresis applied to a continuous clutch reading. */
export function clutchEngaged(value: number, wasEngaged: boolean): boolean {
  return wasEngaged ? value > CLUTCH_OFF : value >= CLUTCH_ON;
}

export function applyDeadzone(value: number): number {
  return Math.abs(value) < STICK_DEADZONE ? 0 : value;
}

/**
 * Did the probe see a paddle move? Called during the first-run calibration overlay
 * ("hold L4, then RT"). If L4 never moves, the game stays on LT/RT forever.
 */
export function probePaddles(pad: Gamepad): boolean {
  const l4 = pad.buttons[EXTRA_BUTTON.L4];
  const r4 = pad.buttons[EXTRA_BUTTON.R4];
  return Boolean(l4?.pressed || r4?.pressed);
}
