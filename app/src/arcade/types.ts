/** Shapes served by `GET /api/arcade/*`. Missing figures are `null`, never invented prices. */

export interface ArcadeSprites {
  boomBig?: string;
  boomMid?: string;
  boomSmall?: string;
  heartFull?: string;
  heartEmpty?: string;
  heroFire?: string;
  heroKneel?: string;
  [key: string]: string | undefined;
}

export interface ArcadeSkin {
  id: string;
  label: string;
  screen: string;
  tone: string;
  background: string;
  fallback: string;
  sprites: ArcadeSprites;
  spriteFallbacks?: ArcadeSprites;
  ready: boolean;
}

export interface ArcadeSymbol {
  name: string;
  maxLots: number;
  defaultLots: number;
  lotStep: number;
  stop: number | null;
  bid: number | null;
  ask: number | null;
  mid: number | null;
  spread: number | null;
  ts: number | null;
}

export interface ArcadePosition {
  positionId: number | null;
  symbol: string | null;
  side: string | null;
  lots: number | null;
  volume: number | null;
  entry: number | null;
  sl: number | null;
  tp: number | null;
  openedAt: number | null;
}

export interface ArcadeSentinel {
  sym: string;
  spread: number;
  state: string;
  quality?: number;
  qualityBand?: string;
  setup?: string | null;
  setupSide?: string | null;
  sessionRemainingS?: number | null;
  nextEvent?: string | null;
  nextEventTMinusS?: number | null;
  newsAgeS?: number | null;
  locked?: boolean;
}

export interface ArcadeHud {
  mode: string;
  broker: { connected: boolean; reason: string | null };
  session: {
    id: string;
    open: boolean;
    timezone: string;
    start: string;
    end: string;
    remainingS: number;
    durationS: number;
    windowBurnedPct: number;
    clock: string;
  };
  risk: {
    maxPositions: number;
    maxDayLossUsd: number;
    rUsd: number;
    positions: number;
  };
  symbols: ArcadeSymbol[];
  positions: ArcadePosition[];
  pnl: { openPnl: number | null; dayPnl: number | null };
  sentinel: ArcadeSentinel | null;
  standDowns: number;
  hiScore: number;
}

export const SPRITE_KEYS = [
  "boomBig",
  "boomMid",
  "boomSmall",
  "heartFull",
  "heartEmpty",
  "heroFire",
  "heroKneel",
] as const;

export const FALLBACK_SKINS: Record<"matrix" | "city", ArcadeSkin> = {
  matrix: {
    id: "matrix",
    label: "HUD on matrix art",
    screen: "artmatrix",
    tone: "terminal",
    background: "/uploads/matrix-like-bg-fullhd.png",
    fallback: "/uploads/matrix-like-bg-fullhd.png",
    sprites: {},
    ready: true,
  },
  city: {
    id: "city",
    label: "Fire on city art",
    screen: "artcontra",
    tone: "contra",
    background: "/uploads/contra-like-bg-full-hd.png",
    fallback: "/uploads/contra-like-bg-full-hd.png",
    sprites: {
      boomBig: "/sprites/boom-big.png",
      boomMid: "/sprites/boom-mid.png",
      boomSmall: "/sprites/boom-small.png",
      heartFull: "/sprites/heart-full.png",
      heartEmpty: "/sprites/heart-empty.png",
      heroFire: "/sprites/hero-fire.png",
      heroKneel: "/sprites/hero-kneel.png",
    },
    spriteFallbacks: {
      boomBig: "/sprites/boom-big.png",
      boomMid: "/sprites/boom-mid.png",
      boomSmall: "/sprites/boom-small.png",
      heartFull: "/sprites/heart-full.png",
      heartEmpty: "/sprites/heart-empty.png",
      heroFire: "/sprites/hero-fire.png",
      heroKneel: "/sprites/hero-kneel.png",
    },
    ready: true,
  },
};
