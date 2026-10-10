import { initialState, resolve, step, type FsmState, type PadInput } from "../pad/fsm";

export const LESSONS = [
  { title: "Unlock deliberately", detail: "Tap View to unlock. Unlocking never places an order." },
  { title: "Try an entry, then cancel", detail: "Hold LT, tap A for BUY, then release LT. You can change your mind before confirming." },
  { title: "Confirm one practice entry", detail: "Hold LT, choose A for BUY or B for SELL, then press RT. Take your time to read the armed side." },
  { title: "Close the practice position", detail: "Hold LT, tap X to prepare a close, then press RT. Y prepares a close of all positions." },
  { title: "Choose to sit out", detail: "Imagine your setup is unclear. Choose to sit out. A session does not need a trade to be worthwhile." },
] as const;

export interface LessonState {
  fsm: FsmState;
  stage: number;
  position: "buy" | "sell" | null;
  feedback: string;
}

export function initialLesson(): LessonState {
  return { fsm: { ...initialState }, stage: 0, position: null, feedback: "No account is connected. All actions stay in this lesson." };
}

export function practiceInput(overrides: Partial<PadInput> = {}): PadInput {
  return {
    clutch: 0, confirm: false, a: false, b: false, x: false, y: false,
    view: false, menu: false, lotUp: false, lotDown: false,
    symbolLeft: false, symbolRight: false, visible: true, padConnected: true,
    nowMs: 0, ...overrides,
  };
}

/** The real controller rules, with local acknowledgements and no network client. */
export function advanceLesson(state: LessonState, input: PadInput): LessonState {
  if (state.stage >= LESSONS.length) return state;
  if (state.stage === 4 && input.a && input.clutch < 0.5 && input.visible && input.padConnected) return sitOut(state);
  const result = step(state.fsm, input);
  let next = { ...state, fsm: result.state };
  if (state.stage === 0 && result.state.phase === "IDLE") {
    next.stage = 1;
    next.feedback = "Unlocked. Nothing was submitted. Now practise changing your mind.";
  }
  if (result.state.phase === "ARMED" && state.fsm.phase !== "ARMED") {
    next.feedback = `Prepared ${result.state.side?.toUpperCase()}. Nothing is submitted yet. Release LT to cancel.`;
  }
  if (result.effects.some((effect) => effect.kind === "cancel") && state.fsm.phase === "ARMED") {
    if (input.visible && input.padConnected && !input.menu && !input.view && !result.state.clutchHeld) {
      if (state.stage === 1) next.stage = 2;
      next.feedback = "Cancelled. No position opened. Checking and changing your mind is a useful skill.";
    } else {
      next.feedback = "Practice paused and the arm was cancelled. Unlock with View when you return.";
    }
  }
  for (const effect of result.effects) {
    if (effect.kind !== "intent") continue;
    next.fsm = resolve(result.state, true).state;
    if (effect.side === "buy" || effect.side === "sell") {
      if (state.stage !== 2) {
        next.feedback = state.stage === 1
          ? "Try cancelling first: hold LT, tap A, then release LT without pressing RT. No position opened."
          : "This step is about closing or sitting out. No extra position opened.";
      } else {
        next.position = effect.side;
        next.stage = 3;
        next.feedback = `Simulated ${effect.side.toUpperCase()} opened. You prepared it, checked it, then confirmed it.`;
      }
    } else if (next.position) {
      next.position = null;
      next.stage = 4;
      next.feedback = "Practice position closed. You now know how to cancel before entry and exit afterwards.";
    } else {
      next.feedback = "There is no practice position to close.";
    }
  }
  // Avoid a React render on every controller frame when nothing visible changes.
  return JSON.stringify(next) === JSON.stringify(state) ? state : next;
}

export function sitOut(state: LessonState): LessonState {
  if (state.stage !== 4 || state.position !== null) return state;
  return { ...state, stage: 5, fsm: { ...initialState }, feedback: "You chose to wait when the setup was unclear. Lesson complete." };
}
