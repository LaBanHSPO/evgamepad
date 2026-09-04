/**
 * The evening as one playable cabinet, not a gallery of disconnected artboards.
 *
 * Screen ids match the click-through shell so the rail can still warp. The reducer is the only
 * place a pad, key, or click may change which screen is showing — and it cannot construct an order.
 */

import type { HudState } from "../screens/SessionHudScreen";

export type { HudState };

export type ScreenId =
  | "settingslive"
  | "reportlive"
  | "journallive"
  | "systemlive"
  | "replaylive"
  | "title"
  | "boot"
  | "pre"
  | "session"
  | "live"
  | "deck"
  | "artmatrix"
  | "artcontra"
  | "desk"
  | "detail"
  | "calc"
  | "clear"
  | "over"
  | "report"
  | "journal"
  | "replay"
  | "history"
  | "score"
  | "pad"
  | "data"
  | "settings"
  | "philosophy";

/** Cabinet verbs. None of these is an order: the live HUD's FSM still owns fire. */
export type CabinetAction =
  | "start"
  | "confirm"
  | "back"
  | "alt"
  | "view"
  | "menu"
  | "end"
  | "up"
  | "down"
  | "left"
  | "right";

export type OverlayGroup = "Play" | "Review" | "Close" | "Setup" | "Cabinet" | "Art" | "Gallery";

export interface OverlayDestination {
  id: ScreenId;
  label: string;
  group: OverlayGroup;
  hint: string;
}

export interface JourneyState {
  screen: ScreenId;
  overlayOpen: boolean;
  overlayIndex: number;
  hud: HudState;
  /** Where B returns after a detour. Attract until the session starts, then the live desk. */
  hub: ScreenId;
  handshake: string[];
  replayCid: string | null;
  sessionStarted: boolean;
  locked: boolean;
}

export type JourneyEvent =
  | { type: "input"; action: CabinetAction }
  | { type: "warp"; screen: ScreenId; hud?: HudState }
  | { type: "boot-key"; key: string }
  | { type: "replay"; cid: string }
  | { type: "sync-overlay"; open: boolean }
  | { type: "hover"; index: number }
  | { type: "choose"; index: number };
