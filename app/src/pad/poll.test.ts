/** Frame reading: rising edges, deadzones, and the disconnected frame. */

import { expect, it } from "vitest";
import { BUTTON, EXTRA_BUTTON, profileFor } from "./map";
import { absentFrame, readFrame } from "./poll";

function gamepad(over: { buttons?: Record<number, number>; axes?: number[]; id?: string; mapping?: string } = {}): Gamepad {
  const buttons = Array.from({ length: 18 }, (_, index) => {
    const value = over.buttons?.[index] ?? 0;
    return { pressed: value >= 0.5, touched: value > 0, value } as GamepadButton;
  });
  return {
    id: over.id ?? "8BitDo Ultimate 2 Wireless (STANDARD GAMEPAD)",
    index: 0,
    connected: true,
    mapping: (over.mapping ?? "standard") as GamepadMappingType,
    timestamp: 0,
    axes: over.axes ?? [0, 0, 0, 0],
    buttons,
    vibrationActuator: null,
  } as unknown as Gamepad;
}

const profile = profileFor(gamepad());

it("reads a held face button as an edge exactly once", () => {
  const pad = gamepad({ buttons: { [BUTTON.A]: 1 } });
  const first = readFrame(pad, {}, profile, { visible: true, nowMs: 1 });
  expect(first.input.a).toBe(true);

  const second = readFrame(pad, first.snapshot, profile, { visible: true, nowMs: 2 });
  expect(second.input.a).toBe(false);
});

it("passes the clutch through as a continuous value for the FSM's hysteresis", () => {
  const frame = readFrame(gamepad({ buttons: { [BUTTON.LT]: 0.62 } }), {}, profile,
    { visible: true, nowMs: 1 });
  expect(frame.input.clutch).toBeCloseTo(0.62);
});

it("silences stick drift below the deadzone", () => {
  const frame = readFrame(gamepad({ axes: [0.05, -0.09, 0.4, 0] }), {}, profile,
    { visible: true, nowMs: 1 });
  expect(frame.sticks.lsX).toBe(0);
  expect(frame.sticks.lsY).toBe(0);
  expect(frame.sticks.rsX).toBeCloseTo(0.4);
});

it("ignores the paddles until a probe has actually seen one move", () => {
  const pad = gamepad({ buttons: { [EXTRA_BUTTON.L4]: 1 } });
  const unprobed = readFrame(pad, {}, profileFor(pad, false), { visible: true, nowMs: 1 });
  expect(unprobed.input.clutch).toBe(0);

  const probed = readFrame(pad, {}, profileFor(pad, true), { visible: true, nowMs: 1 });
  expect(probed.input.clutch).toBe(1);
});

it("accepts an 8BitDo whose mapping Chrome has not filled in yet", () => {
  const late = profileFor(gamepad({ mapping: "", id: "8BitDo Ultimate 2 Wireless" }));
  expect(late.supported).toBe(true);

  const stranger = profileFor(gamepad({ mapping: "", id: "Some Other Device" }));
  expect(stranger.supported).toBe(false);
});

it("reports the bumpers raw, because the chord machine owns their arbitration", () => {
  const frame = readFrame(gamepad({ buttons: { [BUTTON.LB]: 1, [BUTTON.RB]: 1 } }), {}, profile,
    { visible: true, nowMs: 1 });
  expect(frame.bumpers).toEqual({ lb: true, rb: true });
});

it("builds an absent frame that cancels everything downstream", () => {
  const absent = absentFrame(500, false);
  expect(absent.padConnected).toBe(false);
  expect(absent.visible).toBe(false);
  expect(absent.clutch).toBe(0);
  expect(absent.confirm).toBe(false);
});
