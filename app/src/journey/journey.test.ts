import { describe, expect, it } from "vitest";
import { OVERLAY_DESTINATIONS } from "./graph";
import { initialJourney, overlayApplyPayload, reduceJourney } from "./reducer";
import type { JourneyState, ScreenId } from "./types";

function play(events: Parameters<typeof reduceJourney>[1][], from: JourneyState = initialJourney()) {
  return events.reduce(reduceJourney, from);
}

describe("the evening path", () => {
  it("walks attract → boot → pre → session → clear → journal", () => {
    const evening = play([
      { type: "input", action: "start" },
      { type: "input", action: "start" },
      { type: "input", action: "start" },
      { type: "input", action: "end" },
      { type: "input", action: "confirm" },
    ]);
    expect(evening.screen).toBe("journallive");
    expect(evening.sessionStarted).toBe(true);
    expect(evening.overlayOpen).toBe(false);
  });

  it("lets Y on attract open last night's journal without starting a session", () => {
    const state = play([{ type: "input", action: "alt" }]);
    expect(state.screen).toBe("journallive");
    expect(state.sessionStarted).toBe(false);
  });

  it("lets VIEW on attract open rebind", () => {
    expect(play([{ type: "input", action: "view" }]).screen).toBe("pad");
  });

  it("returns from boot VIEW to the cabinet", () => {
    const state = play([
      { type: "input", action: "start" },
      { type: "input", action: "view" },
    ]);
    expect(state.screen).toBe("title");
    expect(state.sessionStarted).toBe(false);
  });

  it("returns from pre B to boot", () => {
    const state = play([
      { type: "input", action: "start" },
      { type: "input", action: "start" },
      { type: "input", action: "back" },
    ]);
    expect(state.screen).toBe("boot");
  });
});

describe("session lock and close", () => {
  it("VIEW toggles the designed HUD into locked, then live", () => {
    const session = play([
      { type: "input", action: "start" },
      { type: "input", action: "start" },
      { type: "input", action: "start" },
    ]);
    expect(session.screen).toBe("session");
    expect(session.hud).toBe("live");
    const locked = reduceJourney(session, { type: "input", action: "view" });
    expect(locked.locked).toBe(true);
    expect(locked.hud).toBe("locked");
    const unlocked = reduceJourney(locked, { type: "input", action: "view" });
    expect(unlocked.locked).toBe(false);
    expect(unlocked.hud).toBe("live");
  });

  it("loss-cap close lands on session over, then the journal note", () => {
    const session = play([
      { type: "input", action: "start" },
      { type: "input", action: "start" },
      { type: "input", action: "start" },
      { type: "input", action: "menu" },
    ]);
    const overIndex = OVERLAY_DESTINATIONS.findIndex((d) => d.id === "over");
    let state = session;
    while (state.overlayIndex !== overIndex) {
      state = reduceJourney(state, { type: "input", action: "down" });
    }
    state = reduceJourney(state, { type: "input", action: "confirm" });
    expect(state.screen).toBe("over");
    state = reduceJourney(state, { type: "input", action: "confirm" });
    expect(state.screen).toBe("journal");
  });
});

describe("the overlay is a complete map", () => {
  it("lists every screen id exactly once", () => {
    const ids = OVERLAY_DESTINATIONS.map((d) => d.id);
    expect(new Set(ids).size).toBe(ids.length);
    const expected: ScreenId[] = [
      "settingslive", "reportlive", "journallive", "systemlive", "replaylive",
      "title", "boot", "pre", "session", "live", "deck", "artmatrix", "artcontra",
      "desk", "detail", "calc", "clear", "over", "report", "journal", "replay",
      "history", "score", "pad", "data", "settings", "philosophy",
    ];
    expect(ids.sort()).toEqual([...expected].sort());
  });

  it("reaches every destination from attract without starting a session", () => {
    const reached = new Set<ScreenId>();
    for (let i = 0; i < OVERLAY_DESTINATIONS.length; i += 1) {
      let state = initialJourney();
      state = reduceJourney(state, { type: "input", action: "menu" });
      expect(state.overlayOpen).toBe(true);
      while (state.overlayIndex !== i) {
        state = reduceJourney(state, { type: "input", action: "down" });
      }
      const before = overlayApplyPayload(state);
      expect(before).toEqual({ screen: OVERLAY_DESTINATIONS[i].id });
      expect(Object.keys(before)).toEqual(["screen"]);
      state = reduceJourney(state, { type: "input", action: "confirm" });
      reached.add(state.screen);
      expect(state.overlayOpen).toBe(false);
    }
    expect(reached.size).toBe(OVERLAY_DESTINATIONS.length);
  });

  it("B and Menu close the overlay without changing room", () => {
    const open = play([{ type: "input", action: "menu" }]);
    expect(reduceJourney(open, { type: "input", action: "back" })).toMatchObject({
      screen: "title",
      overlayOpen: false,
    });
    expect(reduceJourney(open, { type: "input", action: "menu" })).toMatchObject({
      screen: "title",
      overlayOpen: false,
    });
  });

  it("opening the overlay is not an order", () => {
    const payload = overlayApplyPayload(play([{ type: "input", action: "menu" }]));
    expect("side" in payload).toBe(false);
    expect("lots" in payload).toBe(false);
    expect("intent" in payload).toBe(false);
  });
});

describe("boot handshake", () => {
  it("records each key once and ignores keys off the boot screen", () => {
    const boot = play([{ type: "input", action: "start" }]);
    const first = reduceJourney(boot, { type: "boot-key", key: "LT" });
    const again = reduceJourney(first, { type: "boot-key", key: "lt" });
    expect(again.handshake).toEqual(["lt"]);
    const off = reduceJourney(initialJourney(), { type: "boot-key", key: "a" });
    expect(off.handshake).toEqual([]);
  });

  it("START still writes limits even if the handshake is short", () => {
    const boot = play([{ type: "input", action: "start" }]);
    const next = reduceJourney(boot, { type: "input", action: "start" });
    expect(next.screen).toBe("pre");
  });
});

describe("review loop", () => {
  it("hands a cid from the journal to replay and B returns to the journal", () => {
    const replay = play([{ type: "replay", cid: "01TESTCID0000000000000000" }]);
    expect(replay.screen).toBe("replaylive");
    expect(replay.replayCid).toBe("01TESTCID0000000000000000");
    const back = reduceJourney(replay, { type: "input", action: "back" });
    expect(back.screen).toBe("journallive");
  });
});

describe("warp from the gallery rail", () => {
  it("jumps without inventing an order and can still open the overlay", () => {
    const warped = reduceJourney(initialJourney(), { type: "warp", screen: "philosophy" });
    expect(warped.screen).toBe("philosophy");
    const open = reduceJourney(warped, { type: "input", action: "menu" });
    expect(open.overlayOpen).toBe(true);
  });

  it("clicking a destination sets the index and enters in one step", () => {
    const open = play([{ type: "input", action: "menu" }]);
    const desk = OVERLAY_DESTINATIONS.findIndex((d) => d.id === "desk");
    const hovered = reduceJourney(open, { type: "hover", index: desk });
    expect(hovered.overlayIndex).toBe(desk);
    const chosen = reduceJourney(hovered, { type: "choose", index: desk });
    expect(chosen.screen).toBe("desk");
    expect(chosen.overlayOpen).toBe(false);
  });
});
