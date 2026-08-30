/**
 * What the service worker may cache, as a pure function.
 *
 * A stale price, position, or P/L is worse than no app at all -- an offline HUD
 * showing yesterday's gold print is actively dangerous in a way a blank screen
 * is not. So the shell is precached and **every data route is refused**.
 *
 * This lives apart from `sw.ts` so it can be unit-tested without a
 * ServiceWorker environment. `sw.ts` is the thin wiring around it.
 */

export const SHELL_CACHE = "ev-shell-v1";

/** Never cached, under any circumstance. */
const DATA_PATTERNS: readonly RegExp[] = [
  /^\/ws$/,
  /^\/ws\//,
  /^\/api\//,
  /^\/healthz$/,
];

/** The app shell: markup, code, styles, fonts, icons. */
const SHELL_PATTERNS: readonly RegExp[] = [
  /^\/$/,
  /^\/index\.html$/,
  /^\/manifest\.webmanifest$/,
  /^\/assets\/.+\.(js|css|woff2?|png|svg|webp)$/,
  /^\/fonts\/.+\.(css|woff2?)$/,
  /^\/sprites\/.+\.(png|svg|webp)$/,
  /^\/icons\/.+\.(png|svg)$/,
];

export function isDataRoute(pathname: string): boolean {
  return DATA_PATTERNS.some((re) => re.test(pathname));
}

export function isShellRoute(pathname: string): boolean {
  return SHELL_PATTERNS.some((re) => re.test(pathname));
}

/**
 * The single decision. Data always loses, even when it also matches a shell
 * pattern -- ordering here is a safety property, not a preference.
 */
export function isCacheable(pathname: string): boolean {
  if (isDataRoute(pathname)) return false;
  return isShellRoute(pathname);
}

/** Non-GET is never cached: a POST is an action, not a document. */
export function shouldHandle(method: string, pathname: string): boolean {
  return method === "GET" && isCacheable(pathname);
}

export const PRECACHE: readonly string[] = ["/", "/index.html", "/manifest.webmanifest"];
