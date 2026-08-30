import { describe, expect, it } from "vitest";
import {
  DEFAULT_PNL_UNIT,
  formatOpenPnl,
  StandDownCounter,
  adherenceCues,
  adherenceScore,
  formatPnl,
  wasWorthStandingDown,
  type MarketContext,
} from "./process";

const GOOD: MarketContext = {
  insideWindow: true,
  setupNamed: true,
  minutesToNews: 90,
  lots: 0.01,
  maxLots: 0.1,
  spread: 0.4,
  maxSpread: 0.8,
};

describe("P/L is shown in R by default", () => {
  it("lands on R, not dollars", () => {
    expect(DEFAULT_PNL_UNIT).toBe("R");
  });

  it("formats R from the trade's own R, not a constant", () => {
    expect(formatPnl(-3.2, 2.0, "R")).toBe("-1.60R");
    expect(formatPnl(40, 20, "R")).toBe("+2.00R");
  });

  it("shows dollars only when deliberately asked", () => {
    expect(formatPnl(-3.2, 2.0, "USD")).toBe("-$3.20");
  });

  it("falls back to dollars when there is no R to divide by", () => {
    expect(formatPnl(-3.2, null, "R")).toBe("-$3.20");
    expect(formatPnl(-3.2, 0, "R")).toBe("-$3.20");
  });

  it("shows flat as 0.00R, not as dollars", () => {
    // Otherwise the number reads "+$0.00" under a label saying "in R".
    expect(formatPnl(0, null, "R")).toBe("0.00R");
    expect(formatOpenPnl([], "R")).toBe("0.00R");
  });
});

describe("open P/L uses the gateway's R, never its own", () => {
  it("sums the per-position rMultiple", () => {
    expect(formatOpenPnl([{ pnl: -3.2, rMultiple: -1.6 }], "R")).toBe("-1.60R");
    expect(
      formatOpenPnl([{ pnl: 10, rMultiple: 0.5 }, { pnl: 20, rMultiple: 1.0 }], "R"),
    ).toBe("+1.50R");
  });

  it("falls back to dollars rather than reporting a partial sum as complete", () => {
    expect(
      formatOpenPnl([{ pnl: 10, rMultiple: 0.5 }, { pnl: 20, rMultiple: null }], "R"),
    ).toBe("+$30.00");
  });

  it("shows dollars when asked, whatever the R", () => {
    expect(formatOpenPnl([{ pnl: -3.2, rMultiple: -1.6 }], "USD")).toBe("-$3.20");
  });
});

describe("adherence cues are advisory", () => {
  it("all four pass on a clean setup", () => {
    expect(adherenceScore(adherenceCues(GOOD))).toBe(1);
  });

  it.each([
    ["outside the session window", { insideWindow: false }, "window"],
    ["no named setup", { setupNamed: false }, "setup"],
    ["inside the news blackout", { minutesToNews: 4 }, "news"],
    ["over the lot cap", { lots: 0.5 }, "lots"],
  ])("flags %s", (_label, over, id) => {
    const failing = adherenceCues({ ...GOOD, ...over }).filter((c) => !c.ok);
    expect(failing.map((c) => c.id)).toContain(id);
  });

  it("treats the blackout as symmetric around the release", () => {
    expect(adherenceCues({ ...GOOD, minutesToNews: -5 }).find((c) => c.id === "news")?.ok).toBe(false);
  });
});

describe("standing down counts as a win", () => {
  it("records a cancel that avoided a bad tape", () => {
    const counter = new StandDownCounter();
    const event = counter.record(1000, { ...GOOD, minutesToNews: 3 });
    expect(event).not.toBeNull();
    expect(event?.conditions).toContain("news");
    expect(counter.count).toBe(1);
  });

  it("does not credit a cancel when everything was fine", () => {
    const counter = new StandDownCounter();
    expect(counter.record(1000, GOOD)).toBeNull();
    expect(counter.count).toBe(0);
  });

  it("counts a wide spread even when every cue passes", () => {
    expect(wasWorthStandingDown({ ...GOOD, spread: 1.5 })).toBe(true);
    const counter = new StandDownCounter();
    expect(counter.record(1, { ...GOOD, spread: 1.5 })?.conditions).toContain("spread");
  });

  it("carries its conditions, so phase 11 reuses this counter", () => {
    const counter = new StandDownCounter();
    const event = counter.record(1, { ...GOOD, insideWindow: false, setupNamed: false });
    // Selectivity needs to know *why* the player stood down, not just how often.
    expect(event?.conditions.sort()).toEqual(["setup", "window"]);
  });
});
