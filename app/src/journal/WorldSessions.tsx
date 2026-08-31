import type { CSSProperties } from "react";
import { useEffect, useState } from "react";

/**
 * The four market clocks.
 *
 * IANA zone names, never fixed UTC offsets. London and New York change twice a year and Tokyo
 * never does — a hard-coded `+1` is correct for about seven months and quietly wrong for the rest,
 * and the evening you notice is the evening you mistimed the open.
 *
 * `Intl.DateTimeFormat` does the whole job: it holds the tzdata, so DST is the browser's problem
 * rather than arithmetic of ours.
 */

export interface MarketZone {
  city: string;
  zone: string;
  /** Local trading hours, used only to shade the chip. */
  opens: number;
  closes: number;
}

export const ZONES: MarketZone[] = [
  { city: "Sydney", zone: "Australia/Sydney", opens: 7, closes: 16 },
  { city: "Tokyo", zone: "Asia/Tokyo", opens: 9, closes: 18 },
  { city: "London", zone: "Europe/London", opens: 8, closes: 17 },
  { city: "New York", zone: "America/New_York", opens: 8, closes: 17 },
];

/** Wall-clock time in a zone. Returns `null` if the browser cannot resolve it, never a guess. */
export function timeIn(zone: string, at: Date): string | null {
  try {
    return new Intl.DateTimeFormat([], {
      timeZone: zone, hour: "2-digit", minute: "2-digit", hour12: false,
    }).format(at);
  } catch {
    return null;
  }
}

/** The zone's UTC offset in minutes, derived from the zone itself rather than assumed. */
export function offsetMinutes(zone: string, at: Date): number | null {
  try {
    const parts = new Intl.DateTimeFormat([], {
      timeZone: zone, year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
    }).formatToParts(at);
    const get = (type: string) => Number(parts.find((p) => p.type === type)?.value);
    const asUtc = Date.UTC(get("year"), get("month") - 1, get("day"),
                           get("hour") % 24, get("minute"), get("second"));
    return Math.round((asUtc - at.getTime()) / 60_000);
  } catch {
    return null;
  }
}

export function isOpen(market: MarketZone, at: Date): boolean {
  const local = timeIn(market.zone, at);
  if (local === null) return false;
  const hour = Number(local.slice(0, 2));
  return hour >= market.opens && hour < market.closes;
}

export function WorldSessions({ now }: { now?: Date }): JSX.Element {
  const [tick, setTick] = useState(() => now ?? new Date());
  useEffect(() => {
    if (now !== undefined) return;
    const timer = setInterval(() => setTick(new Date()), 30_000);
    return () => clearInterval(timer);
  }, [now]);

  const at = now ?? tick;
  return (
    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
      {ZONES.map((market) => {
        const open = isOpen(market, at);
        return (
          <div key={market.zone} style={{ ...chip, opacity: open ? 1 : 0.55 }}>
            <span style={{ fontSize: 11, letterSpacing: "0.06em" }}>{market.city}</span>
            <span style={{ fontFamily: "var(--font-data)", fontSize: 18 }}>
              {timeIn(market.zone, at) ?? "—"}
            </span>
            <span style={{ fontSize: 10, color: open ? "var(--phos-300)" : "var(--grey-300, #999)" }}>
              {open ? "open" : "closed"}
            </span>
          </div>
        );
      })}
    </div>
  );
}

const chip: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 2,
  padding: "8px 12px",
  border: "var(--border-hairline)",
  background: "var(--black-2)",
  minWidth: 88,
};
