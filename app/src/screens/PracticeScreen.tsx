import { useCallback, useEffect, useRef, useState } from "react";
import { useCabinetOrThrow } from "../journey/Cabinet";
import { isTypingTarget } from "../journey/graph";
import { PadPoller } from "../pad/poll";
import { initialState, type PadInput } from "../pad/fsm";
import { advanceLesson, initialLesson, LESSONS, practiceInput, sitOut } from "../practice/lesson";
import "../practice/practice.css";

export function PracticeScreen() {
  const cabinet = useCabinetOrThrow();
  const [lesson, setLesson] = useState(initialLesson);
  const [controller, setController] = useState(false);
  const [padPresent, setPadPresent] = useState(false);
  const [reflection, setReflection] = useState("");
  const clutch = useRef(false);
  const paused = useRef(false);
  paused.current = cabinet.state.overlayOpen;
  const done = lesson.stage === LESSONS.length;

  const send = useCallback((overrides: Partial<PadInput>) => {
    if (paused.current) return;
    setLesson((state) => advanceLesson(state, practiceInput({ clutch: clutch.current ? 1 : 0, nowMs: performance.now(), ...overrides })));
  }, []);

  const tap = useCallback((key: "a" | "b" | "x" | "y" | "view" | "confirm") => {
    send({ [key]: true });
    send({ [key]: false });
  }, [send]);

  const pause = useCallback(() => {
    clutch.current = false;
    setLesson((state) => state.stage === LESSONS.length ? state : ({ ...state, fsm: { ...initialState }, feedback: "Paused. Your progress is kept here. Tap View to unlock and continue." }));
  }, []);

  useEffect(() => { if (cabinet.state.overlayOpen) pause(); }, [cabinet.state.overlayOpen, pause]);

  useEffect(() => {
    const onBlur = () => pause();
    window.addEventListener("blur", onBlur);
    return () => window.removeEventListener("blur", onBlur);
  }, [pause]);

  useEffect(() => {
    if (controller) {
      const poller = new PadPoller({
        onFrame: ({ input }) => {
          setPadPresent(true);
          if (!paused.current) setLesson((state) => advanceLesson(state, { ...input, menu: false }));
        },
        onAbsent: (input) => {
          setPadPresent(false);
          setLesson((state) => advanceLesson(state, input));
        },
      });
      poller.start();
      return () => poller.stop();
    }
    const keydown = (event: KeyboardEvent) => {
      if (event.repeat || isTypingTarget(event.target) || paused.current) return;
      // Leave native button activation to the browser.
      if ((event.code === "Enter" || event.code === "Space") && (event.target as HTMLElement)?.closest("button")) return;
      if (event.code === "ShiftLeft" || event.code === "ShiftRight") {
        event.preventDefault(); clutch.current = true; send({}); return;
      }
      const keys: Record<string, "view" | "a" | "b" | "x" | "y" | "confirm"> = { KeyV: "view", KeyA: "a", KeyB: "b", KeyX: "x", KeyY: "y", Enter: "confirm" };
      const key = keys[event.code];
      if (key) { event.preventDefault(); tap(key); }
    };
    const keyup = (event: KeyboardEvent) => {
      if (event.code === "ShiftLeft" || event.code === "ShiftRight") {
        clutch.current = false; send({});
      }
    };
    window.addEventListener("keydown", keydown);
    window.addEventListener("keyup", keyup);
    return () => { window.removeEventListener("keydown", keydown); window.removeEventListener("keyup", keyup); };
  }, [controller, send, tap]);

  return (
    <section className="play-shell" aria-labelledby="practice-title">
      <header className="play-topline"><span>CONTROLS PRACTICE</span><span>LOCAL SIMULATION · NO ACCOUNT CONNECTED</span></header>
      <div className="play-actions">
        <button onClick={() => cabinet.dispatch({ type: "warp", screen: "title" })}>Back to start</button>
        <button onClick={() => cabinet.emit("menu")}>Menu</button>
        <span className="play-muted">No timer. Repeat as often as you like.</span>
      </div>
      <ol className="practice-steps" aria-label="Lesson progress">
        {LESSONS.map((item, index) => <li key={item.title} aria-current={lesson.stage === index ? "step" : undefined} data-complete={lesson.stage > index}><span>{lesson.stage > index ? "✓" : `0${index + 1}`}</span>{item.title}</li>)}
      </ol>
      <div className="practice-grid">
        <section className="play-panel play-feature">
          <p className="play-eyebrow">{done ? "LESSON COMPLETE" : `STEP ${lesson.stage + 1} OF ${LESSONS.length}`}</p>
          <h1 id="practice-title">{done ? "You know the control sequence." : LESSONS[lesson.stage].title}</h1>
          <p>{done ? "You cancelled an entry, confirmed one, closed it, and chose to wait. These are control skills, not a trading score." : LESSONS[lesson.stage].detail}</p>
          <div className="practice-feedback" role="status" aria-live="polite">{lesson.feedback}</div>
          {lesson.stage === 4 && <><button className="play-primary" onClick={() => setLesson(sitOut)}>Sit out this setup</button><p className="play-muted">Or release LT and tap A to sit out.</p></>}
          {done && <>
            <label className="practice-reflection">What feels clearer? What will you practise next?
              <textarea value={reflection} onChange={(event) => setReflection(event.target.value)} placeholder="Example: I can release LT to cancel. Next I will practise closing calmly." />
            </label>
            <small>This note stays on this screen and clears when you leave.</small>
            <div className="play-actions">
              <button className="play-primary" onClick={() => cabinet.dispatch({ type: "warp", screen: "live" })}>Open demo desk</button>
              <button onClick={() => { clutch.current = false; setLesson(initialLesson()); }}>Repeat lesson</button>
            </div>
            <p className="play-muted">It is fine to stop here. You do not need to place a demo trade to finish.</p>
          </>}
        </section>
        <section className="play-panel" aria-label="Practice controls">
          <div className="play-actions">
            <button aria-pressed={!controller} onClick={() => { setController(false); pause(); }}>Mouse / keyboard</button>
            <button aria-pressed={controller} onClick={() => { setController(true); pause(); }}>Controller</button>
          </div>
          <dl className="practice-status">
            <div><dt>Control state</dt><dd>{lesson.fsm.phase}{lesson.fsm.side ? ` · ${lesson.fsm.side.toUpperCase()}` : ""}</dd></div>
            <div><dt>Practice position</dt><dd>{lesson.position ? `${lesson.position.toUpperCase()} · simulated` : "None"}</dd></div>
          </dl>
          {controller ? <>
            <p role="status">{padPresent ? "Controller detected." : "Press a button on your controller to detect it. Use XInput mode or a USB cable."}</p>
            <p>View: unlock / lock<br />Hold LT: prepare<br />A / B: BUY / SELL<br />RT: confirm after arming<br />Release LT: cancel<br />X / Y, then RT: close / close all</p>
          </> : <>
            <div className="practice-controls">
              <button disabled={done} onClick={() => tap("view")}>View <small>Unlock / lock · V</small></button>
              <button disabled={done} aria-pressed={lesson.fsm.clutchHeld} onClick={() => { clutch.current = !clutch.current; send({}); }}>LT {lesson.fsm.clutchHeld ? "held" : "released"}<small>Click to toggle · hold Shift</small></button>
              <button disabled={done} onClick={() => tap("a")}>A · BUY<small>Prepare only</small></button>
              <button disabled={done} onClick={() => tap("b")}>B · SELL<small>Prepare only</small></button>
              <button disabled={done} onClick={() => tap("x")}>X · Close<small>Prepare exit</small></button>
              <button disabled={done} onClick={() => tap("y")}>Y · Close all<small>Prepare exit</small></button>
              <button className="practice-confirm" disabled={done} onClick={() => tap("confirm")}>RT · Confirm <small>Keyboard Enter, with focus outside buttons</small></button>
            </div>
            <p className="play-muted">Clicking LT toggles it for this lesson only. On the demo desk, physically hold LT on your controller.</p>
          </>}
          <button disabled={done} onClick={pause}>Pause and lock</button>
        </section>
      </div>
    </section>
  );
}
