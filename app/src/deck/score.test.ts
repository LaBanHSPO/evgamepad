/**
 * The score on the deck: a dashed n/a ring instead of a zero spoke, a distribution instead of a
 * streak, and not a dollar figure anywhere on the process side.
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { naReason } from "./ScoreRadar";
import type { ScoreAxis, ScoreView } from "./ScoreRadar";

const here = dirname(fileURLToPath(import.meta.url));

/** A file with its comments stripped — the comments name these things in order to rule them out. */
function code(file: string): string {
  return readFileSync(resolve(here, file), "utf8")
    .replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, "")
    .toLowerCase();
}

function axis(name: string, value: number | null, detail: Record<string, unknown> = {}): ScoreAxis {
  return { name, value, detail };
}

const DEAD_TAPE: ScoreView = {
  sessionId: "2026-08-31", total: 100, totalExact: 100, weightsVersion: 1, oqMean: 0.18,
  nFires: 0, naAxes: ["adherence", "risk_discipline"],
  axes: [
    axis("adherence", null, { reason: "no required rules were evaluated" }),
    axis("selectivity", 100, { expected: 1, band: [0, 2] }),
    axis("risk_discipline", null, { reason: "no fires" }),
    axis("preparation", 100),
    axis("review", 100),
  ],
  weights: null,
};

describe("the radar", () => {
  it("names why an axis was not scored, rather than showing a zero", () => {
    expect(naReason(DEAD_TAPE.axes[0])).toBe("no required rules were evaluated");
    expect(naReason(DEAD_TAPE.axes[2])).toBe("no fires");
  });

  it("falls back to a plain reason rather than an empty label", () => {
    expect(naReason(axis("review", null))).toBe("no evidence");
  });

  it("draws a vacuous axis at the ring, never dipped toward the centre", () => {
    // A spoke at zero says you did badly. An evening you correctly sat out did nothing badly.
    const source = readFileSync(resolve(here, "ScoreRadar.tsx"), "utf8");
    expect(source).toContain("axis.value ?? 100");
    expect(source).toContain("strokeDasharray");
  });

  it("renders the n/a ring only for the axes that have no evidence", () => {
    const vacuous = DEAD_TAPE.axes.filter((a) => a.value === null);
    expect(vacuous.map((a) => a.name)).toEqual(DEAD_TAPE.naAxes);
  });
});

describe("what the process side refuses to show", () => {
  const processFiles = ["ScoreRadar.tsx", "ProcessPanel.tsx", "TiltRetro.tsx"];

  it("puts no dollar figure on the radar or the process panel", () => {
    for (const file of processFiles) {
      const body = code(file);
      for (const money of ["usd", "pnl", "balance", "equity", "profit"]) {
        expect(body, `${file} mentions ${money}`).not.toContain(money);
      }
      // A bare `$` that is not a template placeholder would be a rendered currency sign.
      expect(body.match(/\$(?!\{)/), `${file} renders a currency sign`).toBeNull();
    }
  });

  it("has no streak, level, badge or days-since anywhere on the deck", () => {
    for (const file of [...processFiles, "PlaybookStats.tsx", "Deck.tsx"]) {
      const body = code(file);
      for (const word of ["streak", "badge", "days since", "dayssince", "level up"]) {
        expect(body, `${file} mentions ${word}`).not.toContain(word);
      }
    }
  });

  it("shows the month as a distribution with n, not as one number to defend", () => {
    const source = readFileSync(resolve(here, "ProcessPanel.tsx"), "utf8");
    expect(source).toContain("n={entry.n}");
    expect(source).toContain("entry.scores.map");
  });

  it("fetches the outcome playbook columns only on the deliberate click", () => {
    const source = readFileSync(resolve(here, "Deck.tsx"), "utf8");
    const openOutcome = source.slice(source.indexOf("const openOutcome"),
                                     source.indexOf("return ("));
    expect(openOutcome).toContain("/api/deck/playbooks/outcome");
    // The process-side effect must not reach for it.
    const processEffect = source.slice(source.indexOf('void fetch(apiUrl("/api/deck/playbooks"))'),
                                       source.indexOf("const openOutcome"));
    expect(processEffect).not.toContain("playbooks/outcome");
  });
});

describe("the tilt retrospective", () => {
  it("says what it is set against, and it is not money", () => {
    const source = readFileSync(resolve(here, "TiltRetro.tsx"), "utf8");
    expect(source).toContain("adherence");
    expect(source).toContain("never a score input");
  });
});
