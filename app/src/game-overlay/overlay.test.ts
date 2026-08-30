import { describe, expect, it } from "vitest";
import {
  DESK_TABS,
  DESTINATIONS,
  DISABLED_TABS,
  EMITTABLE_EFFECTS,
  initialOverlay,
  opensLocked,
  reduce,
  safetyExitsAvailable,
  type OverlayAction,
  type OverlayEffect,
} from "./model";

function drive(actions: OverlayAction[]) {
  let state = initialOverlay();
  const effects: OverlayEffect[] = [];
  for (const action of actions) {
    const r = reduce(state, action);
    state = r.state;
    effects.push(r.effect);
  }
  return { state, effects };
}

describe("the overlay can never place an order", () => {
  it("has no order-emitting effect in its union", () => {
    // This is the guarantee. Adding an `intent.open` effect to the overlay
    // would fail here rather than ship a fire behind a menu.
    expect(EMITTABLE_EFFECTS).not.toContain("intent.open");
    expect(EMITTABLE_EFFECTS).not.toContain("intent.modify");
    expect(EMITTABLE_EFFECTS).not.toContain("fire");
  });

  it("emits nothing order-shaped across an exhaustive action sweep", () => {
    const every: OverlayAction[] = [
      { kind: "open" },
      ...DESTINATIONS.map(() => ({ kind: "nav", direction: 1 }) as OverlayAction),
      ...DESK_TABS.map(() => ({ kind: "tab", direction: 1 }) as OverlayAction),
      { kind: "enter" },
      { kind: "back" },
      ...DESTINATIONS.map((destination) => ({ kind: "goto", destination }) as OverlayAction),
      { kind: "stageModify", value: { positionId: 1, sl: 2338, tp: null } },
      { kind: "clearStaged" },
      { kind: "close" },
    ];
    const { effects } = drive(every);
    for (const effect of effects) {
      expect(EMITTABLE_EFFECTS).toContain(effect.kind);
    }
  });
});

describe("navigation", () => {
  it("D-pad cycles destinations in both directions", () => {
    const forward = drive([{ kind: "open" }, { kind: "nav", direction: 1 }]);
    expect(forward.state.destination).toBe(DESTINATIONS[1]);
    const back = drive([{ kind: "open" }, { kind: "nav", direction: -1 }]);
    expect(back.state.destination).toBe(DESTINATIONS.at(-1));
  });

  it("ignores navigation while closed", () => {
    const { effects } = drive([{ kind: "nav", direction: 1 }]);
    expect(effects).toEqual([{ kind: "none" }]);
  });

  it("LB/RB changes desk tabs only on the desk", () => {
    const onDesk = drive([{ kind: "open" }, { kind: "tab", direction: 1 }]);
    expect(onDesk.state.tab).toBe(DESK_TABS[1]);

    const elsewhere = drive([
      { kind: "open" },
      { kind: "nav", direction: 1 },
      { kind: "tab", direction: 1 },
    ]);
    expect(elsewhere.effects.at(-1)).toEqual({ kind: "none" });
  });

  it("goto reaches a destination directly", () => {
    const { state, effects } = drive([{ kind: "open" }, { kind: "goto", destination: "settings" }]);
    expect(state.destination).toBe("settings");
    expect(effects.at(-1)).toEqual({ kind: "navigated", destination: "settings" });
  });

  it("goto is ignored while closed", () => {
    const { effects } = drive([{ kind: "goto", destination: "settings" }]);
    expect(effects).toEqual([{ kind: "none" }]);
  });

  it("every destination is reachable", () => {
    let state = initialOverlay();
    state = reduce(state, { kind: "open" }).state;
    const seen = new Set([state.destination]);
    for (let i = 0; i < DESTINATIONS.length; i += 1) {
      state = reduce(state, { kind: "nav", direction: 1 }).state;
      seen.add(state.destination);
    }
    expect([...seen].sort()).toEqual([...DESTINATIONS].sort());
  });
});

describe("the Memo tab", () => {
  it("exists but refuses to be entered before phase 8", () => {
    expect(DESK_TABS).toContain("memo");
    expect(DISABLED_TABS.has("memo")).toBe(true);

    let state = initialOverlay();
    state = reduce(state, { kind: "open" }).state;
    while (state.tab !== "memo") state = reduce(state, { kind: "tab", direction: 1 }).state;
    expect(reduce(state, { kind: "enter" }).effect).toEqual({
      kind: "refused",
      why: "tab_disabled",
    });
  });
});

describe("an SL/TP edit", () => {
  it("stages a preview and does not reach the broker", () => {
    const { state, effects } = drive([
      { kind: "open" },
      { kind: "stageModify", value: { positionId: 42, sl: 2338.5, tp: null } },
    ]);
    expect(state.staged).toEqual({ positionId: 42, sl: 2338.5, tp: null });
    expect(effects.at(-1)).toEqual({
      kind: "stagedModify",
      value: { positionId: 42, sl: 2338.5, tp: null },
    });
    // Staged is not sent: the LT+RT confirmation happens back in the game.
    expect(EMITTABLE_EFFECTS).not.toContain("intent.modify");
  });
});

describe("lock semantics", () => {
  it("an open overlay hard locks new opens", () => {
    const { state } = drive([{ kind: "open" }]);
    expect(opensLocked(state)).toBe(true);
  });

  it("closing releases the lock", () => {
    const { state } = drive([{ kind: "open" }, { kind: "close" }]);
    expect(opensLocked(state)).toBe(false);
  });

  it("safety exits stay available with the overlay open", () => {
    const { state } = drive([{ kind: "open" }]);
    // A menu that traps the player with a live position is worse than no menu.
    expect(safetyExitsAvailable(state)).toBe(true);
  });
});
