/** The pip always names a behaviour, and friction never reaches a close. */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";
import { BAND_FRICTION, HOT_HOLD_MS, confirmHoldMsFor } from "./TiltPip";

const here = dirname(fileURLToPath(import.meta.url));

it("adds friction only from the hot band up", () => {
  expect(confirmHoldMsFor("calm", 750)).toBe(0);
  // A warning that costs nothing is one you keep listening to.
  expect(confirmHoldMsFor("warm", 750)).toBe(0);
  expect(confirmHoldMsFor("hot", 750)).toBe(750);
  expect(confirmHoldMsFor("scorched", 750)).toBe(750);
});

it("describes friction only in terms of opens", () => {
  const text = Object.values(BAND_FRICTION).join(" ").toLowerCase();
  expect(text).toContain("fire");
  for (const exit of ["close", "panic", "flatten", "lock"]) {
    expect(text).not.toContain(exit);
  }
});

it("names the driver rather than showing a bare number", () => {
  const source = readFileSync(resolve(here, "TiltPip.tsx"), "utf8");
  expect(source).toContain("tilt.top[0]");
  expect(source).not.toMatch(/\{tilt\?\.score\}/);
});

it("changes only the fire predicate's parameter, never an FSM state", () => {
  const agent = readFileSync(resolve(here, "..", "agent.ts"), "utf8");
  expect(agent).toContain("setConfirmHoldMs");
  const fsm = readFileSync(resolve(here, "..", "pad", "fsm.ts"), "utf8");
  expect(fsm.toLowerCase()).not.toContain("tilt");
});

it("holds the same confirm window the gateway config does", () => {
  // The client enforces the UX friction and the server enforces the block, so the number is
  // written twice. This is the guard that keeps the two copies honest.
  const yaml = readFileSync(resolve(here, "..", "..", "..", "config", "default.yaml"), "utf8");
  const tilt = yaml.slice(yaml.indexOf("\ntilt:"));
  const match = /confirm_hold_ms:\s*(\d+)/.exec(tilt);
  expect(match, "tilt.confirm_hold_ms missing from config/default.yaml").not.toBeNull();
  expect(Number(match![1])).toBe(HOT_HOLD_MS);
});
