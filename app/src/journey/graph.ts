import type { CabinetAction, OverlayDestination, ScreenId } from "./types";

/**
 * Every screen the cabinet can show. Menu from attract (or anywhere) lists the full set, so a
 * first-run player can reach a destination without knowing the evening order — and the sequential
 * START path still teaches that order.
 */
const DESTINATIONS: readonly OverlayDestination[] = [
  { id: "practice", label: "Controls practice", group: "Play", hint: "guided lesson · no account needed" },
  { id: "live", label: "Demo desk", group: "Play", hint: "connect your cTrader demo account" },
  { id: "session", label: "Session HUD sample", group: "Gallery", hint: "sample data · no orders" },
  { id: "desk", label: "Agent desk sample", group: "Gallery", hint: "sample coaching messages" },
  { id: "deck", label: "Deck", group: "Play", hint: "process first, money behind a click" },
  { id: "calc", label: "Size calculator sample", group: "Gallery", hint: "example values" },
  { id: "detail", label: "Trade detail sample", group: "Gallery", hint: "example fill" },
  { id: "journallive", label: "Journal", group: "Review", hint: "today, heatmap, history" },
  { id: "replaylive", label: "Replay", group: "Review", hint: "scrub the frozen tape" },
  { id: "history", label: "History sample", group: "Gallery", hint: "example sessions" },
  { id: "score", label: "Process score sample", group: "Gallery", hint: "example scores" },
  { id: "reportlive", label: "Reports", group: "Review", hint: "print from the browser" },
  { id: "clear", label: "Session clear sample", group: "Gallery", hint: "example summary · does not end a session" },
  { id: "over", label: "Loss cap sample", group: "Gallery", hint: "example summary" },
  { id: "pad", label: "Gamepad sample", group: "Gallery", hint: "example controller settings" },
  { id: "settingslive", label: "Settings", group: "Setup", hint: "safe preferences only" },
  { id: "systemlive", label: "System", group: "Setup", hint: "principles you wrote down" },
  { id: "data", label: "Data sample", group: "Gallery", hint: "example data controls" },
  { id: "philosophy", label: "Philosophy", group: "Setup", hint: "why the money stays quiet" },
  { id: "title", label: "Start here", group: "Play", hint: "practice, connect, review" },
  { id: "attract", label: "Attract sample", group: "Gallery", hint: "original artwork · sample data" },
  { id: "boot", label: "Boot sample", group: "Gallery", hint: "example connection checks" },
  { id: "pre", label: "Pre-session sample", group: "Gallery", hint: "example limits and plan" },
  { id: "artmatrix", label: "HUD on matrix art", group: "Art", hint: "attract-era skin" },
  { id: "artcontra", label: "Fire on city art", group: "Art", hint: "contra-era skin" },
  { id: "journal", label: "Journal (prototype)", group: "Gallery", hint: "fixed data walkthrough" },
  { id: "replay", label: "Replay (prototype)", group: "Gallery", hint: "fixed tape" },
  { id: "report", label: "Report (prototype)", group: "Gallery", hint: "fixed print" },
  { id: "settings", label: "Settings (prototype)", group: "Gallery", hint: "fixed prefs" },
] as const;

export const OVERLAY_DESTINATIONS: readonly OverlayDestination[] = [...DESTINATIONS].sort((a, b) => {
  const groups = ["Play", "Review", "Close", "Setup", "Cabinet", "Art", "Gallery"];
  return groups.indexOf(a.group) - groups.indexOf(b.group);
});

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
    case "attract":
      return { ...menu, start: "start", b: "back" };
    case "practice":
      // Face buttons, View and confirm belong to the isolated practice lesson.
      return { ...menu, start: "menu" };
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
