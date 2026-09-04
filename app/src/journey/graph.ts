import type { CabinetAction, OverlayDestination, ScreenId } from "./types";

/**
 * Every screen the cabinet can show. Menu from attract (or anywhere) lists the full set, so a
 * first-run player can reach a destination without knowing the evening order — and the sequential
 * START path still teaches that order.
 */
export const OVERLAY_DESTINATIONS: readonly OverlayDestination[] = [
  { id: "session", label: "Session HUD", group: "Play", hint: "the designed evening desk" },
  { id: "live", label: "Live HUD", group: "Play", hint: "real gateway · paste the token" },
  { id: "desk", label: "Agent desk", group: "Play", hint: "reads, never fires" },
  { id: "deck", label: "Deck", group: "Play", hint: "process first, money behind a click" },
  { id: "calc", label: "Size calculator", group: "Play", hint: "lots from the plan, not the mood" },
  { id: "detail", label: "Trade detail", group: "Play", hint: "one fill, the rules it met" },
  { id: "journallive", label: "Journal", group: "Review", hint: "today, heatmap, history" },
  { id: "replaylive", label: "Replay", group: "Review", hint: "scrub the frozen tape" },
  { id: "history", label: "History", group: "Review", hint: "sessions, not dollars" },
  { id: "score", label: "Process score", group: "Review", hint: "five axes, stand-down is 100" },
  { id: "reportlive", label: "Reports", group: "Review", hint: "print from the browser" },
  { id: "clear", label: "End session", group: "Close", hint: "tally and freeze the evening" },
  { id: "over", label: "Loss cap", group: "Close", hint: "the cap did its job" },
  { id: "pad", label: "Gamepad", group: "Setup", hint: "bindings and handshake" },
  { id: "settingslive", label: "Settings", group: "Setup", hint: "safe preferences only" },
  { id: "systemlive", label: "System", group: "Setup", hint: "principles you wrote down" },
  { id: "data", label: "Data", group: "Setup", hint: "export, backup, wipe" },
  { id: "philosophy", label: "Philosophy", group: "Setup", hint: "why the money stays quiet" },
  { id: "title", label: "Attract", group: "Cabinet", hint: "insert coin" },
  { id: "boot", label: "Boot", group: "Cabinet", hint: "pad handshake" },
  { id: "pre", label: "Pre-session", group: "Cabinet", hint: "write limits while calm" },
  { id: "artmatrix", label: "HUD on matrix art", group: "Art", hint: "attract-era skin" },
  { id: "artcontra", label: "Fire on city art", group: "Art", hint: "contra-era skin" },
  { id: "journal", label: "Journal (prototype)", group: "Gallery", hint: "fixed data walkthrough" },
  { id: "replay", label: "Replay (prototype)", group: "Gallery", hint: "fixed tape" },
  { id: "report", label: "Report (prototype)", group: "Gallery", hint: "fixed print" },
  { id: "settings", label: "Settings (prototype)", group: "Gallery", hint: "fixed prefs" },
] as const;

export const BOOT_KEYS = ["lt", "rt", "a", "b", "x", "y", "start"] as const;

/** Physical Start and Menu are the same Xbox button (index 9). Screen graph decides what it does. */
const START_OPENS_OVERLAY = new Set<ScreenId>([
  "session",
  "live",
  "desk",
  "deck",
  "artmatrix",
  "artcontra",
  "detail",
  "calc",
  "pad",
  "data",
  "settings",
  "settingslive",
  "systemlive",
  "philosophy",
  "report",
  "reportlive",
  "replay",
  "replaylive",
]);

const START_RETURNS_TO_HUB = new Set<ScreenId>([
  "journal",
  "journallive",
  "history",
  "score",
]);

/**
 * Bindings while the overlay is closed. A/B/X/Y/LT/RT on the session HUD stay with the order FSM;
 * the cabinet only claims the buttons that change rooms.
 */
export function bindingsFor(screen: ScreenId): Readonly<Record<string, CabinetAction>> {
  const menu = { menu: "menu" as const };
  switch (screen) {
    case "title":
      return { ...menu, start: "start", y: "alt", view: "view" };
    case "boot":
      return { ...menu, start: "start", view: "view" };
    case "pre":
      return { ...menu, start: "start", b: "back" };
    case "session":
    case "artmatrix":
    case "artcontra":
      return { ...menu, start: "menu", view: "view", y: "alt" };
    case "live":
      return { ...menu, start: "menu", view: "view" };
    case "clear":
      return { ...menu, a: "confirm", y: "alt", view: "view" };
    case "over":
      return { ...menu, a: "confirm", view: "view" };
    default:
      if (START_OPENS_OVERLAY.has(screen)) {
        return { ...menu, start: "menu", b: "back" };
      }
      if (START_RETURNS_TO_HUB.has(screen)) {
        return { ...menu, start: "back", b: "back" };
      }
      return { ...menu, b: "back" };
  }
}

export function overlayBindings(): Readonly<Record<string, CabinetAction>> {
  return {
    a: "confirm",
    start: "confirm",
    b: "back",
    menu: "menu",
    up: "up",
    down: "down",
    left: "left",
    right: "right",
    view: "back",
  };
}

export function normalizeButton(button: string): string {
  return button.trim().toLowerCase();
}

export function actionForButton(
  button: string,
  screen: ScreenId,
  overlayOpen: boolean,
): CabinetAction | "boot-key" | null {
  const key = normalizeButton(button);
  if (overlayOpen) return overlayBindings()[key] ?? null;
  if (screen === "boot" && (BOOT_KEYS as readonly string[]).includes(key) && key !== "start") {
    return "boot-key";
  }
  return bindingsFor(screen)[key] ?? null;
}

export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}
