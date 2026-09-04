/** Display helpers for the art HUDs. A missing figure is an em dash, never a made-up tick. */

import type { ArcadeHud, ArcadePosition, ArcadeSkin, ArcadeSymbol } from "./types";
import { FALLBACK_SKINS } from "./types";

export const DASH = "—";

export function dash(value: number | string | null | undefined): string {
  if (value == null || value === "") return DASH;
  return String(value);
}

export function formatPrice(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(Number(value))) return DASH;
  return Number(value).toFixed(digits);
}

export function padScore(value: number | null | undefined): string {
  return String(Math.max(0, Math.floor(Number(value) || 0))).padStart(2, "0");
}

export function midOf(symbol: ArcadeSymbol | undefined | null): number | null {
  if (!symbol) return null;
  if (symbol.mid != null) return symbol.mid;
  if (symbol.bid != null && symbol.ask != null) return (symbol.bid + symbol.ask) / 2;
  return symbol.bid ?? symbol.ask ?? null;
}

export function pickSymbol(
  hud: ArcadeHud | null,
  preferred?: string | null,
): ArcadeSymbol | undefined {
  if (!hud?.symbols.length) return undefined;
  if (preferred) {
    return hud.symbols.find((row) => row.name === preferred) ?? hud.symbols[0];
  }
  return hud.symbols[0];
}

export function resolveArt(skin: ArcadeSkin | null | undefined, fallback: string): string {
  if (!skin) return fallback;
  if (skin.ready) return skin.background;
  return skin.fallback || fallback;
}

export function resolveSprite(
  skin: ArcadeSkin | null | undefined,
  key: string,
  fallback: string,
): string {
  if (!skin) return fallback;
  return skin.sprites[key] || skin.spriteFallbacks?.[key] || fallback;
}

export function fallbackSkin(id: "matrix" | "city"): ArcadeSkin {
  return FALLBACK_SKINS[id];
}

/** Default stop below last, when there is a quote. Not a live order. */
export function planStop(symbol: ArcadeSymbol | undefined | null, now: number | null): number | null {
  if (now == null || symbol?.stop == null) return null;
  return now - symbol.stop;
}

export function lotsLabel(symbol: ArcadeSymbol | undefined, positions: ArcadePosition[]): string {
  if (!symbol) return DASH;
  const open = positions.filter((row) => row.symbol === symbol.name);
  if (open.length === 0) return DASH;
  const lots = open.reduce((sum, row) => sum + (row.lots ?? 0), 0);
  if (lots > 0) return lots.toFixed(2);
  return "open";
}

export function progressToTarget(position: ArcadePosition | undefined, now: number | null): number | null {
  if (!position || now == null || position.entry == null || position.tp == null) return null;
  const span = position.tp - position.entry;
  if (span === 0) return null;
  return Math.max(0, Math.min(100, ((now - position.entry) / span) * 100));
}

export function rAtStop(symbol: ArcadeSymbol | undefined | null): number | null {
  // The configured default stop *is* 1R. Do not invent a second R from a missing fill.
  if (symbol?.stop == null) return null;
  return 1;
}

const NEWS_GUARD_S = 900;

export type Threat = "low" | "mid" | "high";

export function threatOf(sentinel: ArcadeHud["sentinel"]): Threat {
  if (!sentinel) return "low";
  const tMinus = sentinel.nextEventTMinusS;
  if (tMinus != null && tMinus >= 0 && tMinus <= NEWS_GUARD_S) return "high";
  if (sentinel.qualityBand === "dead") return "high";
  if (sentinel.qualityBand === "thin") return "mid";
  return "low";
}

export function eventClock(sentinel: ArcadeHud["sentinel"]): string {
  if (!sentinel?.nextEventTMinusS && sentinel?.nextEventTMinusS !== 0) return DASH;
  const total = Math.max(0, Math.floor(sentinel.nextEventTMinusS ?? 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (hours > 0) return `${hours}:${String(minutes).padStart(2, "0")}`;
  const seconds = total % 60;
  if (total < 60) return `0:${String(seconds).padStart(2, "0")}`;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function shortSymbol(name: string | null | undefined): string {
  if (!name) return DASH;
  if (name.endsWith("USD") && name.length > 3) return name.slice(0, -3);
  return name;
}
