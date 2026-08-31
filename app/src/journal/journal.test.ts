/**
 * The journal cockpit: DST-correct clocks, a process-first heatmap, and the surfaces that refuse
 * to claim more than they know.
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { colourFor } from "./Heatmap";
import { FILTERS } from "./History";
import { LABELS, answered } from "./ReadinessChecklist";
import { GROUP_LABELS } from "./TradeQuality";
import { ZONES, isOpen, offsetMinutes, timeIn } from "./WorldSessions";
import { r, show } from "./types";

const here = dirname(fileURLToPath(import.meta.url));

/** A file with comments stripped — they name forbidden things in order to forbid them. */
function code(file: string): string {
  return readFileSync(resolve(here, file), "utf8")
    .replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, "")
    .toLowerCase();
}

// Two dates either side of the northern DST changes, chosen so London and New York have both
// already switched and Tokyo has not.
const JANUARY = new Date("2026-01-15T12:00:00Z");
const JULY = new Date("2026-07-15T12:00:00Z");

describe("world session clocks", () => {
  it("uses IANA zones, never a hard-coded offset", () => {
    // A fixed `+1` is right for about seven months a year and quietly wrong for the rest.
    for (const zone of ZONES) expect(zone.zone).toContain("/");
    const source = code("WorldSessions.tsx");
    expect(source).toContain("timezone");
    expect(source).not.toMatch(/utc[+-]\d/);
  });

  it("moves London and New York across DST and leaves Tokyo alone", () => {
    const london = [offsetMinutes("Europe/London", JANUARY), offsetMinutes("Europe/London", JULY)];
    const newYork = [offsetMinutes("America/New_York", JANUARY),
                     offsetMinutes("America/New_York", JULY)];
    const tokyo = [offsetMinutes("Asia/Tokyo", JANUARY), offsetMinutes("Asia/Tokyo", JULY)];

    expect(london).toEqual([0, 60]);
    expect(newYork).toEqual([-300, -240]);
    // Japan has not observed DST since 1951, so this pair must never differ.
    expect(tokyo).toEqual([540, 540]);
  });

  it("reads the same instant differently in each zone", () => {
    const times = ZONES.map((zone) => timeIn(zone.zone, JULY));
    expect(new Set(times).size).toBe(ZONES.length);
    for (const time of times) expect(time).toMatch(/^\d{2}:\d{2}$/);
  });

  it("returns nothing rather than a guess for an unresolvable zone", () => {
    expect(timeIn("Not/AZone", JULY)).toBeNull();
    expect(offsetMinutes("Not/AZone", JULY)).toBeNull();
  });

  it("marks a market open only inside its own local hours", () => {
    const tokyo = ZONES.find((z) => z.city === "Tokyo")!;
    // 12:00 UTC is 21:00 in Tokyo — after the close.
    expect(isOpen(tokyo, JULY)).toBe(false);
    // 02:00 UTC is 11:00 in Tokyo — inside it.
    expect(isOpen(tokyo, new Date("2026-07-15T02:00:00Z"))).toBe(true);
  });
});

describe("readiness", () => {
  it("labels all five items", () => {
    expect(Object.keys(LABELS)).toEqual([
      "sleep", "calm", "focus", "risk_accepted", "plan_reviewed",
    ]);
  });

  it("counts a declined item as answered, not as missing", () => {
    // Skipping is a real answer, and different from "no".
    expect(answered([
      { item: "sleep", ok: true }, { item: "calm", ok: false }, { item: "focus", ok: null },
    ])).toBe(2);
  });

  it("says out loud that it never blocks anything", () => {
    expect(code("ReadinessChecklist.tsx")).toContain("never blocks");
  });
});

describe("the heatmap", () => {
  it("colours by Process Score", () => {
    expect(colourFor(95)).not.toBe(colourFor(65));
    expect(colourFor(95)).toBe(colourFor(92));
  });

  it("draws an unscored day as an outline rather than a bad one", () => {
    expect(colourFor(null)).toBeNull();
    expect(code("Heatmap.tsx")).toContain("dashed");
  });

  it("has no access to a dollar figure at all", () => {
    const source = code("Heatmap.tsx");
    for (const money of ["pnl", "usd", "equity", "balance", "profit"]) {
      expect(source).not.toContain(money);
    }
  });
});

describe("what the journal refuses to claim", () => {
  it("never promises what the market would have done", () => {
    for (const file of ["TradeQuality.tsx", "TradeDetail.tsx", "Journal.tsx"]) {
      const source = code(file);
      for (const claim of ["would have", "theoretical profit", "could have won", "missed profit"]) {
        expect(source, `${file} claims ${claim}`).not.toContain(claim);
      }
    }
  });

  it("labels the comparison Actual vs Plan", () => {
    expect(readFileSync(resolve(here, "TradeQuality.tsx"), "utf8")).toContain("view.label");
    expect(GROUP_LABELS["planned-win"]).toBe("Planned · win");
  });

  it("charts four groups and excludes the unclassified", () => {
    expect(Object.keys(GROUP_LABELS)).toHaveLength(4);
    expect(code("TradeQuality.tsx")).toContain("excluded rather than");
  });

  it("names the inputs a stage score could not measure", () => {
    // A high score over a small denominator should look like one.
    expect(code("TradeQuality.tsx")).toContain("not measured");
  });

  it("keeps money off every process surface", () => {
    for (const file of ["Journal.tsx", "Today.tsx", "MistakeTrends.tsx"]) {
      const source = code(file);
      for (const money of ["pnl", "netpnl", "equity", "balance", "profit"]) {
        expect(source, `${file} mentions ${money}`).not.toContain(money);
      }
    }
  });

  it("has no streak, badge or penalty in the mistake trend", () => {
    const source = code("MistakeTrends.tsx");
    for (const word of ["streak", "badge", "penalty", "level up"]) {
      expect(source).not.toContain(word);
    }
  });
});

describe("history filters", () => {
  it("offers every dimension the plan asks for", () => {
    const keys = FILTERS.map((filter) => filter.key);
    for (const dimension of ["symbol", "timeframe", "playbook", "setup", "side", "market_session",
                             "intent", "mistake", "result"]) {
      expect(keys).toContain(dimension);
    }
  });

  it("offers exactly the four intents plus 'any'", () => {
    const intent = FILTERS.find((filter) => filter.key === "intent")!;
    expect(intent.options).toEqual(["", "planned", "impulsive", "revenge", "unknown"]);
  });
});

describe("the size calculator", () => {
  it("computes nothing itself — the gateway owns the arithmetic", () => {
    // A client-side copy would agree with the journal and disagree with the broker the first time
    // a volume step changed.
    const source = code("PositionSizeCalculator.tsx");
    expect(source).toContain("/api/journal/size");
    expect(source).not.toMatch(/risk\s*\/\s*\(/);
  });

  it("shows the risk asked for and the risk that will be carried, separately", () => {
    const source = readFileSync(resolve(here, "PositionSizeCalculator.tsx"), "utf8");
    expect(source).toContain("Risk you asked for");
    expect(source).toContain("Risk you will carry");
  });

  it("says applying a size only changes the preview", () => {
    expect(code("PositionSizeCalculator.tsx")).toContain("only thing that trades");
  });

  it("has no path to an order", () => {
    const source = code("PositionSizeCalculator.tsx");
    for (const path of ["/api/replay", "intent.open", "sendintent", "flatten"]) {
      expect(source).not.toContain(path);
    }
  });
});

describe("formatting", () => {
  it("prints a missing figure as a gap, never as zero", () => {
    expect(show(null)).toBe("—");
    expect(show(undefined)).toBe("—");
    expect(show(0)).toBe("0.00");
    expect(r(null)).toBe("—");
    expect(r(0)).toBe("+0.00R");
    expect(r(-1.5)).toBe("-1.50R");
  });
});

describe("attachments", () => {
  it("sends the file as a raw body and never names a path", () => {
    const source = readFileSync(resolve(here, "Today.tsx"), "utf8");
    expect(source).toContain("body: file");
    // The browser's filename rides as a label only.
    expect(source).toContain("label=");
    expect(source).not.toContain("filename=");
  });

  it("accepts only the three raster types", () => {
    expect(readFileSync(resolve(here, "Today.tsx"), "utf8"))
      .toContain('accept="image/png,image/jpeg,image/webp"');
  });
});
