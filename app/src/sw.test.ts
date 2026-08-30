import { describe, expect, it } from "vitest";
import { PRECACHE, isCacheable, isDataRoute, isShellRoute, shouldHandle } from "./sw-policy";

describe("no data route is ever cacheable", () => {
  it.each([
    "/ws",
    "/api/voice/memo",
    "/api/replay/index",
    "/api/deck/summary",
    "/api/journal/today",
    "/api/settings/lot",
    "/api/reports/session",
    "/api/export/trades.csv",
    "/api/data/backup",
    "/healthz",
  ])("refuses %s", (path) => {
    expect(isDataRoute(path)).toBe(true);
    expect(isCacheable(path)).toBe(false);
    expect(shouldHandle("GET", path)).toBe(false);
  });

  it("means an offline app can never show a stale price or position", () => {
    // The whole point: with the network cut the shell opens and the data
    // requests fail, so the HUD renders disconnected rather than confident.
    const dataRoutes = ["/ws", "/api/deck/pnl", "/api/journal/today"];
    expect(dataRoutes.every((p) => !isCacheable(p))).toBe(true);
  });
});

describe("the shell is cacheable", () => {
  it.each([
    "/",
    "/index.html",
    "/manifest.webmanifest",
    "/assets/index-a1b2c3.js",
    "/assets/index-a1b2c3.css",
    "/assets/inter-latin.woff2",
    "/sprites/hero-fire.png",
    "/icons/icon-512.png",
    "/fonts/_faces.css",
    "/fonts/vt323-400.woff2",
  ])("caches %s", (path) => {
    expect(isShellRoute(path)).toBe(true);
    expect(isCacheable(path)).toBe(true);
  });

  it("precaches enough to open offline", () => {
    expect(PRECACHE).toContain("/");
    expect(PRECACHE.every((p) => isCacheable(p))).toBe(true);
  });
});

describe("method and origin", () => {
  it("never caches a non-GET, even on a shell path", () => {
    expect(shouldHandle("POST", "/")).toBe(false);
    expect(shouldHandle("PUT", "/index.html")).toBe(false);
  });
});

describe("ordering is a safety property", () => {
  it("a data route that also looks like a shell asset still loses", () => {
    // If the patterns are ever reordered so shell wins, this fails.
    expect(isCacheable("/api/../assets/x.js")).toBe(false);
    expect(isCacheable("/ws")).toBe(false);
  });
});
