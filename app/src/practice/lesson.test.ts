import { describe, expect, it } from "vitest";
import { advanceLesson, initialLesson, practiceInput, sitOut, type LessonState } from "./lesson";
import type { PadInput } from "../pad/fsm";

function frame(state: LessonState, input: Partial<PadInput>) {
  return advanceLesson(state, practiceInput(input));
}

function throughCancellation() {
  let state = frame(initialLesson(), { view: true });
  state = frame(state, { clutch: 1, a: true });
  return frame(state, { clutch: 0 });
}

describe("guided practice", () => {
  it("completes from actual cancel, entry, exit, and sit-out actions", () => {
    let state = throughCancellation();
    expect(state.stage).toBe(2);
    expect(state.position).toBeNull();
    state = frame(state, { clutch: 1, b: true });
    state = frame(state, { clutch: 1, confirm: true });
    expect(state.stage).toBe(3);
    expect(state.position).toBe("sell");
    state = frame(state, { clutch: 0 });
    state = frame(state, { clutch: 1, x: true });
    state = frame(state, { clutch: 1, confirm: true });
    expect(state.stage).toBe(4);
    expect(state.position).toBeNull();
    state = sitOut(state);
    expect(state.stage).toBe(5);
    expect(state.fsm.phase).toBe("LOCKED");
  });

  it("does not pass cancellation when the player confirms instead", () => {
    let state = frame(initialLesson(), { view: true });
    state = frame(state, { clutch: 1, a: true });
    state = frame(state, { clutch: 1, confirm: true });
    expect(state.stage).toBe(1);
    expect(state.position).toBeNull();
    expect(state.feedback).toContain("Try cancelling first");
  });

  it("does not award a deliberate cancellation for unplugging or hiding the tab", () => {
    for (const input of [{ visible: false }, { padConnected: false }, { menu: true }]) {
      let state = frame(initialLesson(), { view: true });
      state = frame(state, { clutch: 1, a: true });
      state = frame(state, { clutch: 1, ...input });
      expect(state.stage).toBe(1);
      expect(state.fsm.side).toBeNull();
    }
  });

  it("does not complete the lesson while a practice position is open", () => {
    let state = throughCancellation();
    state = frame(state, { clutch: 1, a: true });
    state = frame(state, { clutch: 1, confirm: true });
    expect(sitOut(state)).toBe(state);
  });

  it("keeps completion locked when more buttons are pressed", () => {
    const complete = { ...initialLesson(), stage: 5 };
    expect(frame(complete, { view: true, clutch: 1, a: true, confirm: true })).toBe(complete);
  });
});
