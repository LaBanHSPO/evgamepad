import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  type Dispatch,
  type ReactNode,
} from "react";
import { BUTTON } from "../pad/map";
import { actionForButton, isTypingTarget, normalizeButton } from "./graph";
import type { CabinetAction, JourneyEvent, JourneyState } from "./types";

export interface CabinetValue {
  state: JourneyState;
  dispatch: Dispatch<JourneyEvent>;
  emit: (action: CabinetAction) => void;
  pressBootKey: (key: string) => void;
}

const CabinetContext = createContext<CabinetValue | null>(null);

export function CabinetProvider({
  state,
  dispatch,
  children,
}: {
  state: JourneyState;
  dispatch: Dispatch<JourneyEvent>;
  children: ReactNode;
}): JSX.Element {
  const emit = useCallback(
    (action: CabinetAction) => dispatch({ type: "input", action }),
    [dispatch],
  );
  const pressBootKey = useCallback(
    (key: string) => dispatch({ type: "boot-key", key: normalizeButton(key) }),
    [dispatch],
  );
  const value = useMemo(
    () => ({ state, dispatch, emit, pressBootKey }),
    [state, dispatch, emit, pressBootKey],
  );
  return <CabinetContext.Provider value={value}>{children}</CabinetContext.Provider>;
}

export function useCabinet(): CabinetValue | null {
  return useContext(CabinetContext);
}

export function useCabinetOrThrow(): CabinetValue {
  const value = useContext(CabinetContext);
  if (!value) throw new Error("CabinetProvider is required");
  return value;
}

/** Resolve a painted pad glyph to a cabinet verb on the current screen. */
export function useGlyphAction(button: string): {
  action: CabinetAction | "boot-key" | null;
  fire: () => void;
} {
  const cabinet = useCabinet();
  const key = normalizeButton(button);
  if (!cabinet) return { action: null, fire: () => undefined };
  const action = actionForButton(key, cabinet.state.screen, cabinet.state.overlayOpen);
  return {
    action,
    fire: () => {
      if (action === "boot-key") cabinet.pressBootKey(key);
      else if (action) cabinet.emit(action);
    },
  };
}

function keyToButton(event: KeyboardEvent): string | null {
  switch (event.code) {
    case "Enter":
    case "NumpadEnter":
      return "start";
    case "Space":
      return event.repeat ? null : "start";
    case "Escape":
    case "Backspace":
      return "b";
    case "KeyM":
      return "menu";
    case "KeyV":
      return "view";
    case "KeyY":
      return "y";
    case "KeyA":
      return "a";
    case "KeyB":
      return "b";
    case "ArrowUp":
      return "up";
    case "ArrowDown":
      return "down";
    case "ArrowLeft":
      return "left";
    case "ArrowRight":
      return "right";
    default:
      return null;
  }
}

const PAD_BUTTONS: { index: number; button: string }[] = [
  { index: BUTTON.A, button: "a" },
  { index: BUTTON.B, button: "b" },
  { index: BUTTON.Y, button: "y" },
  { index: BUTTON.VIEW, button: "view" },
  { index: BUTTON.MENU, button: "start" },
  { index: BUTTON.DPAD_UP, button: "up" },
  { index: BUTTON.DPAD_DOWN, button: "down" },
  { index: BUTTON.DPAD_LEFT, button: "left" },
  { index: BUTTON.DPAD_RIGHT, button: "right" },
  { index: BUTTON.LT, button: "lt" },
  { index: BUTTON.RT, button: "rt" },
  { index: BUTTON.X, button: "x" },
];

/**
 * Keyboard + pad → journey. Ignores typing targets so the live HUD token field still works.
 * Rising edges only: a held Start cannot spray screen changes.
 */
export function useCabinetInput(): void {
  const cabinet = useCabinet();
  const cabinetRef = useRef(cabinet);
  cabinetRef.current = cabinet;

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const current = cabinetRef.current;
      if (!current) return;
      if (isTypingTarget(event.target)) return;
      const button = keyToButton(event);
      if (!button) return;
      const resolved = actionForButton(button, current.state.screen, current.state.overlayOpen);
      if (!resolved) return;
      event.preventDefault();
      if (resolved === "boot-key") current.pressBootKey(button);
      else current.emit(resolved);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    const previous: boolean[] = [];
    let raf = 0;
    const poll = () => {
      const current = cabinetRef.current;
      const pads = navigator.getGamepads?.() ?? [];
      const pad = pads.find((item) => item);
      if (current && pad) {
        for (const { index, button } of PAD_BUTTONS) {
          const down = Boolean(pad.buttons[index]?.pressed);
          const was = previous[index] === true;
          previous[index] = down;
          if (!down || was) continue;
          const resolved = actionForButton(button, current.state.screen, current.state.overlayOpen);
          if (resolved === "boot-key") current.pressBootKey(button);
          else if (resolved) current.emit(resolved);
        }
      }
      raf = window.requestAnimationFrame(poll);
    };
    raf = window.requestAnimationFrame(poll);
    return () => window.cancelAnimationFrame(raf);
  }, []);
}
