import { BOOT_KEYS, OVERLAY_DESTINATIONS } from "./graph";
import type { CabinetAction, HudState, JourneyEvent, JourneyState, ScreenId } from "./types";

export const initialJourney = (): JourneyState => ({
  screen: "title",
  overlayOpen: false,
  overlayIndex: 0,
  hud: "live",
  hub: "title",
  handshake: [],
  replayCid: null,
  sessionStarted: false,
  locked: false,
});

const DEST_COUNT = OVERLAY_DESTINATIONS.length;

function wrap(index: number, step: number): number {
  return (index + step + DEST_COUNT) % DEST_COUNT;
}

function clampIndex(index: number): number {
  if (DEST_COUNT === 0) return 0;
  return ((index % DEST_COUNT) + DEST_COUNT) % DEST_COUNT;
}

function resetCabinet(partial: Partial<JourneyState> = {}): JourneyState {
  return {
    ...initialJourney(),
    ...partial,
  };
}

function closeOverlay(state: JourneyState): JourneyState {
  return { ...state, overlayOpen: false };
}

function go(state: JourneyState, screen: ScreenId, extra: Partial<JourneyState> = {}): JourneyState {
  const next: JourneyState = { ...state, screen, overlayOpen: false, ...extra };
  if (screen === "title") {
    return resetCabinet({ overlayIndex: state.overlayIndex });
  }
  if (screen === "session" || screen === "live") {
    next.sessionStarted = true;
    next.hub = screen;
  }
  if (screen === "journallive" || screen === "journal") {
    next.hub = screen;
  }
  return next;
}

function applyOverlay(state: JourneyState): JourneyState {
  const dest = OVERLAY_DESTINATIONS[state.overlayIndex];
  if (!dest) return closeOverlay(state);
  return go(state, dest.id);
}

function applyInput(state: JourneyState, action: CabinetAction): JourneyState {
  if (state.overlayOpen) {
    switch (action) {
      case "up":
      case "left":
        return { ...state, overlayIndex: wrap(state.overlayIndex, -1) };
      case "down":
      case "right":
        return { ...state, overlayIndex: wrap(state.overlayIndex, 1) };
      case "confirm":
        return applyOverlay(state);
      case "back":
      case "menu":
      case "view":
        return closeOverlay(state);
      default:
        return state;
    }
  }

  switch (action) {
    case "menu":
      return { ...state, overlayOpen: true };
    case "end":
      return go(state, "clear");
    case "up":
    case "down":
    case "left":
    case "right":
      return state;
    default:
      break;
  }

  switch (state.screen) {
    case "title":
      if (action === "start") return go(state, "boot");
      if (action === "alt") return go(state, "journallive");
      if (action === "view") return go(state, "pad");
      return state;
    case "boot":
      if (action === "start") return go(state, "pre");
      if (action === "view" || action === "back") return go(state, "title");
      return state;
    case "pre":
      if (action === "start") {
        return go(state, "session", { sessionStarted: true, hub: "session", locked: false, hud: "live" });
      }
      if (action === "back") return go(state, "boot");
      return state;
    case "session":
    case "artmatrix":
    case "artcontra":
      if (action === "start") return { ...state, overlayOpen: true };
      if (action === "view") {
        const locked = !state.locked;
        const hud: HudState = locked ? "locked" : "live";
        return { ...state, locked, hud };
      }
      if (action === "alt") return go(state, "desk");
      if (action === "back") return go(state, state.hub === state.screen ? "title" : state.hub);
      return state;
    case "live":
      if (action === "start") return { ...state, overlayOpen: true };
      if (action === "view") {
        const locked = !state.locked;
        return { ...state, locked, hud: locked ? "locked" : "live" };
      }
      if (action === "back") return go(state, "session");
      return state;
    case "clear":
      if (action === "confirm") return go(state, "journallive", { hub: "journallive" });
      if (action === "alt") return go(state, "desk");
      if (action === "view" || action === "back") return go(state, "title");
      return state;
    case "over":
      if (action === "confirm") return go(state, "journal", { hub: "journallive" });
      if (action === "view" || action === "back") return go(state, "title");
      return state;
    default:
      if (action === "start" || action === "back") {
        if (state.screen === state.hub) {
          return go(state, state.sessionStarted ? "session" : "title");
        }
        return go(state, state.hub);
      }
      return state;
  }
}

export function reduceJourney(state: JourneyState, event: JourneyEvent): JourneyState {
  switch (event.type) {
    case "input":
      return applyInput(state, event.action);
    case "warp":
      return go(state, event.screen, {
        ...(event.hud ? { hud: event.hud, locked: event.hud === "locked" } : {}),
      });
    case "boot-key": {
      const key = event.key.trim().toLowerCase();
      if (state.screen !== "boot") return state;
      if (!(BOOT_KEYS as readonly string[]).includes(key)) return state;
      if (state.handshake.includes(key)) return state;
      return { ...state, handshake: [...state.handshake, key] };
    }
    case "replay":
      return go(state, "replaylive", { replayCid: event.cid, hub: "journallive" });
    case "sync-overlay":
      if (state.overlayOpen === event.open) return state;
      return { ...state, overlayOpen: event.open };
    case "hover":
      if (!state.overlayOpen) return state;
      return { ...state, overlayIndex: clampIndex(event.index) };
    case "choose":
      if (!state.overlayOpen) return state;
      return applyOverlay({ ...state, overlayIndex: clampIndex(event.index) });
    default:
      return state;
  }
}

/** Pure helper for tests: overlay apply never carries an order field. */
export function overlayApplyPayload(state: JourneyState): { screen: ScreenId } {
  const dest = OVERLAY_DESTINATIONS[state.overlayIndex];
  return { screen: dest?.id ?? state.screen };
}
