/**
 * What the service worker is allowed to cache.
 *
 * Split out from `sw.ts` so the policy is importable and testable without a worker global. The
 * rule it encodes is the one that matters: the shell may be cached, live data may never be. A
 * stale price, position, or P/L served from a cache is worse than no app at all — an offline HUD
 * still showing last night's gold price invites a trade against a number that no longer exists.
 */

export const CACHE_NAME = "evgp-shell-v1";

/** The shell, and only the shell. Hashed asset URLs are added by the fetch handler on demand. */
export const SHELL_ASSETS = ["/", "/index.html", "/manifest.webmanifest"];

/** Anything matching one of these is live data and must never be served from a cache. */
export const NEVER_CACHE = [/^\/ws\b/, /^\/api\//, /^\/healthz\b/];

/** True when a same-origin path may be cached at all. */
export function isCacheable(pathname: string): boolean {
  return !NEVER_CACHE.some((pattern) => pattern.test(pathname));
}
