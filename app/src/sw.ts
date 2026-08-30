/// <reference lib="webworker" />
/**
 * App-shell service worker.
 *
 * Two behaviours matter beyond the caching policy in `sw-policy.ts`:
 *
 *  - `skipWaiting` + `clients.claim`: a new build runs on the **next launch**
 *    rather than waiting for every tab to close. Asking a trader to hard-reload
 *    mid-evening is not a deployment strategy.
 *  - Data requests are passed straight through with no cache read *and* no
 *    cache write, so a network failure surfaces as a failure. The HUD shows a
 *    disconnected state; it never shows a price that is no longer true.
 */

import { PRECACHE, SHELL_CACHE, shouldHandle } from "./sw-policy";

declare const self: ServiceWorkerGlobalScope;

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll([...PRECACHE])).then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== SHELL_CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Cross-origin and every data route: straight to the network, uncached.
  if (url.origin !== self.location.origin) return;
  if (!shouldHandle(event.request.method, url.pathname)) return;

  event.respondWith(
    caches.match(event.request).then((hit) => {
      if (hit) {
        // Refresh in the background so the next launch has the new build.
        event.waitUntil(
          fetch(event.request)
            .then((res) => (res.ok ? caches.open(SHELL_CACHE).then((c) => c.put(event.request, res)) : undefined))
            .catch(() => undefined),
        );
        return hit;
      }
      return fetch(event.request).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          event.waitUntil(caches.open(SHELL_CACHE).then((c) => c.put(event.request, copy)));
        }
        return res;
      });
    }),
  );
});

export {};
