/**
 * Service worker: app shell only.
 *
 * The shell is cached so the installed window opens instantly and, with the network down, can say
 * so. **No data route is ever cached** — not `/ws`, not `/api/*`, not a quote, a position, or a
 * P/L. A stale price is worse than no app: an offline HUD that still shows last night's gold
 * price is an invitation to trade against a number that no longer exists.
 *
 * A new deploy takes effect on the next launch. The worker activates immediately rather than
 * waiting for every tab to close, because "hard-reload to get the fix" is not a thing to ask of
 * someone mid-session.
 */

/// <reference lib="webworker" />

import { CACHE_NAME, SHELL_ASSETS, isCacheable } from "./sw-policy";

declare const self: ServiceWorkerGlobalScope;

self.addEventListener("install", (event) => {
  // Take over as soon as the new worker is ready; do not wait for old tabs to close.
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS)));
  void self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const names = await caches.keys();
      await Promise.all(names.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name)));
      await self.clients.claim();
    })(),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Cross-origin and every data route go straight to the network, every time.
  if (url.origin !== self.location.origin || !isCacheable(url.pathname) || request.method !== "GET") {
    return;
  }

  event.respondWith(
    (async () => {
      try {
        // Network first, so a new deploy is picked up without asking for a reload.
        const response = await fetch(request);
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, response.clone());
        return response;
      } catch {
        // Offline: the shell, or an honest failure. Never a stale price.
        const cached = await caches.match(request);
        if (cached) return cached;
        const shell = await caches.match("/index.html");
        if (shell && request.mode === "navigate") return shell;
        throw new Error("offline and not in the shell cache");
      }
    })(),
  );
});
