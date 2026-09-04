/**
 * Arcade art HUDs: catalog URLs, honest blanks, and a token that never touches storage.
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { fetchHud, fetchSkins, pickSkin } from "./fetch";
import {
  DASH,
  eventClock,
  formatPrice,
  padScore,
  pickSymbol,
  planStop,
  resolveArt,
  resolveSprite,
  threatOf,
} from "./format";
import { FALLBACK_SKINS } from "./types";
import type { ArcadeHud, ArcadeSymbol } from "./types";

const here = dirname(fileURLToPath(import.meta.url));

function code(file: string): string {
  return readFileSync(resolve(here, file), "utf8")
    .replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, "")
    .toLowerCase();
}

const gold: ArcadeSymbol = {
  name: "XAUUSD",
  maxLots: 0.1,
  defaultLots: 0.01,
  lotStep: 0.01,
  stop: 2,
  bid: 2461.38,
  ask: 2461.62,
  mid: 2461.5,
  spread: 0.24,
  ts: 1,
};

describe("formatters", () => {
  it("renders a missing price as an em dash, never a zero tick", () => {
    expect(formatPrice(null)).toBe(DASH);
    expect(formatPrice(undefined)).toBe(DASH);
    expect(formatPrice(Number.NaN)).toBe(DASH);
    expect(formatPrice(2461.38)).toBe("2461.38");
  });

  it("pads stand-down scores the way the cabinet paints them", () => {
    expect(padScore(7)).toBe("07");
    expect(padScore(0)).toBe("00");
    expect(padScore(null)).toBe("00");
  });

  it("plans a stop from the configured distance and will not invent one without a quote", () => {
    expect(planStop(gold, 2461.5)).toBeCloseTo(2459.5);
    expect(planStop(gold, null)).toBeNull();
    expect(planStop({ ...gold, stop: null }, 2461.5)).toBeNull();
  });

  it("treats a print inside the 15-minute guard as high threat", () => {
    expect(threatOf({ sym: "XAUUSD", spread: 0.2, state: "tight", nextEventTMinusS: 120 })).toBe(
      "high",
    );
    expect(threatOf({ sym: "XAUUSD", spread: 0.2, state: "tight", qualityBand: "live" })).toBe("low");
    expect(eventClock({ sym: "XAUUSD", spread: 0, state: "tight", nextEventTMinusS: 72 })).toBe(
      "1:12",
    );
  });

  it("picks the preferred symbol when the snapshot has it", () => {
    const hud = { symbols: [gold, { ...gold, name: "EURUSD", bid: null, ask: null, mid: null }] } as ArcadeHud;
    expect(pickSymbol(hud, "EURUSD")?.name).toBe("EURUSD");
    expect(pickSymbol(null)?.name).toBeUndefined();
  });
});

describe("artwork resolution", () => {
  it("uses the catalog URL when the file is ready, else the public fallback", () => {
    expect(resolveArt(FALLBACK_SKINS.matrix, "/nope")).toBe("/uploads/matrix-like-bg-fullhd.png");
    expect(
      resolveArt(
        { ...FALLBACK_SKINS.matrix, ready: false, background: "/api/arcade/assets/matrix" },
        "/nope",
      ),
    ).toBe("/uploads/matrix-like-bg-fullhd.png");
    expect(resolveSprite(FALLBACK_SKINS.city, "heroFire", "/missing.png")).toBe(
      "/sprites/hero-fire.png",
    );
  });

  it("falls back to the built-in city/matrix skins when the catalog is empty", () => {
    expect(pickSkin([], "city").id).toBe("city");
    expect(pickSkin([FALLBACK_SKINS.matrix], "city").id).toBe("city");
  });
});

describe("the art screens never invent a gold print", () => {
  it("matrix and city no longer hard-code 2461.38", () => {
    expect(code("../screens/MatrixHudScreen.tsx")).not.toContain("2461.38");
    expect(code("../screens/CityFireScreen.tsx")).not.toContain("2461.38");
    expect(code("../screens/MatrixHudScreen.tsx")).toContain("usearcaderuntime");
    expect(code("../screens/CityFireScreen.tsx")).toContain("usearcaderuntime");
  });

  it("keeps the session token in memory", () => {
    const hook = code("useArcadeRuntime.ts");
    const fetchSource = code("fetch.ts");
    expect(fetchSource).toContain("/api/arcade/hud");
    expect(hook).not.toContain("localstorage");
    expect(hook).not.toContain("sessionstorage");
    expect(code("ConnectStrip.tsx")).toContain("never stored");
  });
});

describe("fetch fallbacks", () => {
  it("returns the public skins when the catalog is down", async () => {
    const original = globalThis.fetch;
    globalThis.fetch = async () => {
      throw new Error("offline");
    };
    try {
      const skins = await fetchSkins();
      expect(skins.map((row) => row.id)).toEqual(["matrix", "city"]);
      expect(await fetchHud()).toBeNull();
    } finally {
      globalThis.fetch = original;
    }
  });
});
