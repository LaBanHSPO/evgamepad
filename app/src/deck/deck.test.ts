/**
 * The deck's layout rule, asserted in source: process is the default, and the outcome figures are
 * not even fetched until the player deliberately opens that tab.
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";
import { percent, show, signed } from "./types";

const here = dirname(fileURLToPath(import.meta.url));
const deckSource = readFileSync(resolve(here, "Deck.tsx"), "utf8");
const processSource = readFileSync(resolve(here, "ProcessPanel.tsx"), "utf8");

it("opens on the process panel", () => {
  expect(deckSource).toMatch(/useState<Tab>\("process"\)/);
});

it("does not fetch the outcome figures until the tab is opened", () => {
  // The money must not arrive on a glance; it takes a decision.
  const mount = deckSource.slice(deckSource.indexOf("useEffect"), deckSource.indexOf("openOutcome"));
  expect(mount).toContain("/api/deck/process");
  expect(mount).not.toContain("/api/deck/outcome");
  expect(deckSource).toMatch(/openOutcome[\s\S]*api\/deck\/outcome/);
});

it("renders the player's own note as text, never as markup", () => {
  expect(processSource).not.toContain("dangerouslySetInnerHTML");
  expect(processSource).toContain("{view.latestSession.note}");
});

it("shows a dash for a figure that was never measured, not a zero", () => {
  expect(show(null)).toBe("—");
  expect(percent(undefined)).toBe("—");
  expect(signed(null)).toBe("—");
  expect(show(0)).toBe("0.00");
  expect(percent(0)).toBe("0.0%");
});

it("gives a delta its direction", () => {
  expect(signed(0.25)).toBe("+0.25");
  expect(signed(-0.25)).toBe("-0.25");
});
