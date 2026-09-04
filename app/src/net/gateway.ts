/**
 * Where the HUD talks to the Python gateway.
 *
 * Local `npm run dev` leaves this empty: Vite proxies `/ws` and `/api` to 127.0.0.1:8444,
 * so the page stays same-origin. A production HUD hosted on another domain sets
 * `VITE_GATEWAY_ORIGIN` at **build** time (see `app/.env.production`). That value is a
 * hostname, not a secret — the session token is still pasted into memory and never baked in.
 */

export function gatewayOrigin(): string {
  const raw = (import.meta.env.VITE_GATEWAY_ORIGIN as string | undefined) ?? "";
  return raw.trim().replace(/\/$/, "");
}

/** Prefix a gateway path with the configured origin, or leave it relative (same-origin). */
export function apiUrl(path: string): string {
  return joinGateway(gatewayOrigin(), path);
}

export function joinGateway(origin: string, path: string): string {
  const base = origin.trim().replace(/\/$/, "");
  if (/^https?:\/\//i.test(path) || /^wss?:\/\//i.test(path)) return path;
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${suffix}` : suffix;
}

/** Game socket URL. `pageOrigin` is `location.origin` in the browser. */
export function toWsUrl(httpOrigin: string): string {
  return `${httpOrigin.replace(/^http/i, "ws")}/ws`;
}

export function wsUrl(pageOrigin: string = typeof location !== "undefined" ? location.origin : ""): string {
  return toWsUrl(gatewayOrigin() || pageOrigin);
}
