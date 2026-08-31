/**
 * The service worker's one hard rule: no data route is cacheable.
 *
 * A stale price, position, or P/L served from a cache is worse than no app at all, so this is
 * asserted rather than reviewed.
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";
import { NEVER_CACHE, SHELL_ASSETS, isCacheable } from "./sw-policy";

const here = dirname(fileURLToPath(import.meta.url));

it("refuses to cache the socket, the API, or the health probe", () => {
  expect(isCacheable("/ws")).toBe(false);
  expect(isCacheable("/api/replay/index")).toBe(false);
  expect(isCacheable("/api/voice/01ABC/audio")).toBe(false);
  expect(isCacheable("/healthz")).toBe(false);
});

it("caches the shell and its assets", () => {
  expect(isCacheable("/")).toBe(true);
  expect(isCacheable("/index.html")).toBe(true);
  expect(isCacheable("/assets/index-abc123.js")).toBe(true);
  expect(isCacheable("/manifest.webmanifest")).toBe(true);
});

it("precaches nothing that could hold market or journal data", () => {
  for (const asset of SHELL_ASSETS) {
    expect(isCacheable(asset)).toBe(true);
    expect(asset).not.toMatch(/api|ws|quote|position|pnl|journal/i);
  }
});

it("keeps the never-cache list anchored, so /apixyz cannot slip past /api/", () => {
  expect(NEVER_CACHE.every((pattern) => pattern.source.startsWith("^"))).toBe(true);
  expect(isCacheable("/apidocs")).toBe(true);
  expect(isCacheable("/api/")).toBe(false);
});

it("activates a new deploy immediately instead of waiting for tabs to close", () => {
  const source = readFileSync(resolve(here, "sw.ts"), "utf8");
  expect(source).toMatch(/skipWaiting\(\)/);
  expect(source).toMatch(/clients\.claim\(\)/);
});

it("goes to the network first, so a cached shell never outranks a live response", () => {
  const source = readFileSync(resolve(here, "sw.ts"), "utf8");
  const fetchIndex = source.indexOf("await fetch(request)");
  const matchIndex = source.indexOf("caches.match(request)");
  expect(fetchIndex).toBeGreaterThan(-1);
  expect(fetchIndex).toBeLessThan(matchIndex);
});
