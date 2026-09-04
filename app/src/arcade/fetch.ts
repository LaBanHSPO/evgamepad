/** Token-free REST for the art HUDs. Failures become fallbacks, never invented prices. */

import type { ArcadeHud, ArcadeSkin } from "./types";
import { FALLBACK_SKINS } from "./types";
import { apiUrl } from "../net/gateway";

function qualifySkin(skin: ArcadeSkin): ArcadeSkin {
  const sprites: ArcadeSkin["sprites"] = {};
  for (const [key, value] of Object.entries(skin.sprites)) {
    sprites[key] = value ? apiUrl(value) : value;
  }
  return {
    ...skin,
    background: apiUrl(skin.background),
    sprites,
  };
}

export async function fetchSkins(): Promise<ArcadeSkin[]> {
  try {
    const response = await fetch(apiUrl("/api/arcade/skins"));
    if (!response.ok) throw new Error("skins");
    const body = (await response.json()) as { skins?: ArcadeSkin[] };
    if (!body.skins?.length) throw new Error("empty");
    return body.skins.map(qualifySkin);
  } catch {
    return [FALLBACK_SKINS.matrix, FALLBACK_SKINS.city];
  }
}

export async function fetchHud(): Promise<ArcadeHud | null> {
  try {
    const response = await fetch(apiUrl("/api/arcade/hud"), { cache: "no-store" });
    if (!response.ok) throw new Error("hud");
    return (await response.json()) as ArcadeHud;
  } catch {
    return null;
  }
}

export function pickSkin(skins: ArcadeSkin[], id: "matrix" | "city"): ArcadeSkin {
  return skins.find((row) => row.id === id) ?? FALLBACK_SKINS[id];
}
