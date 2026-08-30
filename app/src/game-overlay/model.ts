/**
 * The GameOverlay navigation contract, as data.
 *
 * One rule shapes this whole module: **navigation and apply can never emit
 * `intent.open` or `intent.modify`.** It is enforced structurally rather than by
 * review -- the reducer's action type has no order-emitting variant, and an
 * SL/TP edit produces a *staged preview* that still needs LT+RT back in the
 * game. A test asserts the emitted-action union, so adding an order action here
 * would fail the build rather than ship a fire behind a menu.
 *
 * Full close, HUD Flatten, and panic stay reachable while the overlay is open:
 * a safe surface must not become a trap with a position open.
 */

export type Destination = "desk" | "playbook" | "journal" | "system" | "reports" | "settings";

export const DESTINATIONS: readonly Destination[] = [
  "desk",
  "playbook",
  "journal",
  "system",
  "reports",
  "settings",
];

/** The copilot desk's tabs. `memo` is phase 8 and renders disabled. */
export type DeskTab = "sentinel" | "news" | "setups" | "coach" | "memo";

export const DESK_TABS: readonly DeskTab[] = ["sentinel", "news", "setups", "coach", "memo"];

/** Tabs with nothing behind them yet, so the shell renders honestly. */
export const DISABLED_TABS: ReadonlySet<DeskTab> = new Set<DeskTab>(["memo"]);

export type StagedModify = {
  positionId: number;
  sl: number | null;
  tp: number | null;
};

export type OverlayState = {
  open: boolean;
  destination: Destination;
  tab: DeskTab;
  /**
   * An SL/TP edit that has been *staged*, not sent. It reaches the broker only
   * after the player returns to the game and confirms with LT+RT.
   */
  staged: StagedModify | null;
};

export function initialOverlay(): OverlayState {
  return { open: false, destination: "desk", tab: "sentinel", staged: null };
}

export type OverlayAction =
  | { kind: "open" }
  | { kind: "close" }
  | { kind: "nav"; direction: -1 | 1 }
  | { kind: "goto"; destination: Destination }
  | { kind: "tab"; direction: -1 | 1 }
  | { kind: "enter" }
  | { kind: "back" }
  | { kind: "stageModify"; value: StagedModify }
  | { kind: "clearStaged" };

/**
 * Everything the overlay is allowed to emit. There is deliberately no
 * `intent.open` or `intent.modify` here, and `overlay.test.ts` asserts it.
 */
export type OverlayEffect =
  | { kind: "none" }
  | { kind: "opened" }
  | { kind: "closed" }
  | { kind: "navigated"; destination: Destination }
  | { kind: "tabChanged"; tab: DeskTab }
  | { kind: "stagedModify"; value: StagedModify }
  | { kind: "refused"; why: "tab_disabled" };

export const EMITTABLE_EFFECTS: readonly OverlayEffect["kind"][] = [
  "none",
  "opened",
  "closed",
  "navigated",
  "tabChanged",
  "stagedModify",
  "refused",
];

function cycle<T>(items: readonly T[], current: T, direction: -1 | 1): T {
  const index = items.indexOf(current);
  const next = (index + direction + items.length) % items.length;
  return items[next]!;
}

export function reduce(
  state: OverlayState,
  action: OverlayAction,
): { state: OverlayState; effect: OverlayEffect } {
  switch (action.kind) {
    case "open":
      return { state: { ...state, open: true }, effect: { kind: "opened" } };
    case "close":
      return { state: { ...state, open: false }, effect: { kind: "closed" } };
    case "nav": {
      if (!state.open) return { state, effect: { kind: "none" } };
      const destination = cycle(DESTINATIONS, state.destination, action.direction);
      return { state: { ...state, destination }, effect: { kind: "navigated", destination } };
    }
    case "goto": {
      // Mouse and keyboard reach a destination directly; the D-pad cycles.
      // Both go through the same reducer, so neither can emit an order.
      if (!state.open) return { state, effect: { kind: "none" } };
      return {
        state: { ...state, destination: action.destination },
        effect: { kind: "navigated", destination: action.destination },
      };
    }
    case "tab": {
      if (!state.open || state.destination !== "desk") return { state, effect: { kind: "none" } };
      const tab = cycle(DESK_TABS, state.tab, action.direction);
      // A disabled tab is still selectable so the player can see it exists and
      // why -- it just cannot be entered.
      return { state: { ...state, tab }, effect: { kind: "tabChanged", tab } };
    }
    case "enter": {
      if (!state.open) return { state, effect: { kind: "none" } };
      if (state.destination === "desk" && DISABLED_TABS.has(state.tab)) {
        return { state, effect: { kind: "refused", why: "tab_disabled" } };
      }
      return { state, effect: { kind: "none" } };
    }
    case "back":
      return { state, effect: { kind: "none" } };
    case "stageModify":
      // Staged only. Reaching the broker still needs LT+RT in the game.
      return {
        state: { ...state, staged: action.value },
        effect: { kind: "stagedModify", value: action.value },
      };
    case "clearStaged":
      return { state: { ...state, staged: null }, effect: { kind: "none" } };
  }
}

/** Opening the overlay hard-locks new opens. Exits stay available. */
export function opensLocked(state: OverlayState): boolean {
  return state.open;
}

export function safetyExitsAvailable(_state: OverlayState): boolean {
  // Always. A menu that traps the player with a live position is worse than no
  // menu, so this is a function rather than a constant to make it greppable.
  return true;
}
