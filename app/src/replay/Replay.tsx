import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { PadPoller } from "../pad/poll";
import { Chart } from "./Chart";
import { Timeline, clock } from "./Timeline";
import { CONTROLS, initialBindings, stepBindings } from "./bindings";
import type { BindingState } from "./bindings";
import { TIMEFRAMES, timeframeLabel } from "./resample";
import {
  advance,
  audioCue,
  initialState,
  nearestEvent,
  seekTo,
  stepSpeed,
  togglePlay,
  windowOf,
} from "./transport";
import type { TransportState, Window } from "./transport";
import type { IndexRow, ReplayBody } from "./types";

/**
 * Trade replay: a closed position, scrubbed back through the tape it actually traded on.
 *
 * **No order can be placed from here.** Not because a flag says so, but because there is nothing
 * to place one with: this route imports neither the agent nor the socket client, and selecting a
 * screen unmounts the previous one, so the live HUD's agent, poller and socket are all destroyed
 * before this mounts. The pad on this route drives `bindings.ts`, whose action type has no order
 * case to construct. `replay.test.ts` asserts all of it.
 *
 * The tape is frozen, never simulated. Nothing here can reach the broker, and nothing here writes.
 */

/** Opens on 5-second candles: fine enough to see the fill, coarse enough to see the move. */
const DEFAULT_TIMEFRAME_INDEX = 1;

export function Replay({ cid, onExit }: { cid?: string; onExit?: () => void }): JSX.Element {
  const [index, setIndex] = useState<IndexRow[]>([]);
  const [current, setCurrent] = useState<string | null>(cid ?? null);
  const [body, setBody] = useState<ReplayBody | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tfIndex, setTfIndex] = useState(DEFAULT_TIMEFRAME_INDEX);
  const [transport, setTransport] = useState<TransportState>(
    () => initialState({ fromMs: 0, toMs: 0 }),
  );

  const audioRef = useRef<HTMLAudioElement>(null);
  const bindingsRef = useRef<BindingState>(initialBindings);
  const lastFrameRef = useRef(0);

  const window_: Window = useMemo(
    () => (body?.tape ? windowOf(body.tape) : { fromMs: 0, toMs: 0 }),
    [body],
  );
  const seconds = TIMEFRAMES[tfIndex];
  // The poller closure outlives any one window, so it reads the current one through a ref.
  const windowRef = useRef(window_);
  windowRef.current = window_;

  // The trade list drives LB/RB stepping. It is fetched once; a replay is not realtime.
  useEffect(() => {
    void fetch("/api/replay/index")
      .then((r) => r.json())
      .then((payload) => {
        const trades = payload.trades as IndexRow[];
        setIndex(trades);
        setCurrent((existing) => existing ?? trades[trades.length - 1]?.cid ?? null);
      })
      .catch(() => setError("could not load the trade list"));
  }, []);

  useEffect(() => {
    if (current === null) return;
    setError(null);
    void fetch(`/api/replay/${encodeURIComponent(current)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((payload: ReplayBody) => {
        setBody(payload);
        setTransport(initialState(payload.tape
          ? windowOf(payload.tape)
          : { fromMs: payload.trade.openedAt ?? 0, toMs: payload.trade.closedAt }));
      })
      .catch(() => setError("no tape for that trade"));
  }, [current]);

  const stepTrade = useCallback((step: 1 | -1) => {
    setCurrent((existing) => {
      const at = index.findIndex((row) => row.cid === existing);
      if (at < 0) return existing;
      const next = Math.max(0, Math.min(index.length - 1, at + step));
      return index[next].cid;
    });
  }, [index]);

  // One poller for the whole route. It reads the pad and produces transport actions — there is no
  // agent, no client, and no code path from here to an intent.
  useEffect(() => {
    const poller = new PadPoller({
      onFrame: (frame) => {
        const now = frame.input.nowMs;
        const elapsed = lastFrameRef.current === 0 ? 0 : now - lastFrameRef.current;
        lastFrameRef.current = now;

        const result = stepBindings(bindingsRef.current, {
          input: frame.input, bumpers: frame.bumpers, rsX: frame.sticks.rsX,
        });
        bindingsRef.current = result.state;

        for (const action of result.actions) {
          if (action.kind === "playPause") {
            setTransport((s) => togglePlay(s, windowRef.current));
          } else if (action.kind === "speed") {
            setTransport((s) => stepSpeed(s, action.step));
          } else if (action.kind === "zoom") {
            setTfIndex((i) => Math.max(0, Math.min(TIMEFRAMES.length - 1, i + action.step)));
          } else if (action.kind === "step") {
            stepTrade(action.step);
          } else if (action.kind === "exit") {
            onExit?.();
          }
        }

        // Scrub and play on the same clock, so a stick nudge during playback wins cleanly.
        setTransport((s) => advance(s, windowRef.current, elapsed, frame.sticks.lsX));
      },
      onAbsent: () => undefined,
    });
    poller.start();
    return () => poller.stop();
  }, [stepTrade, onExit]);

  // Audio follows the playhead rather than the other way round, and its length comes from the
  // stored `durMs` — Chrome's MediaRecorder WebM reports `Infinity` for `audio.duration`.
  const cue = useMemo(
    () => audioCue(transport, body?.memos ?? []),
    [transport, body],
  );
  useEffect(() => {
    const element = audioRef.current;
    if (element === null || cue.memoId === null) return;
    element.muted = cue.muted;
    element.playbackRate = cue.playbackRate;
    if (Math.abs(element.currentTime - cue.offsetS) > 0.25) element.currentTime = cue.offsetS;
    if (cue.playing) void element.play().catch(() => undefined);
    else element.pause();
  }, [cue]);

  const nearest = useMemo(
    () => (body ? nearestEvent(body.events, transport.playheadMs) : null),
    [body, transport.playheadMs],
  );

  if (error !== null && body === null) {
    return <section style={shell}><p>{error}</p></section>;
  }
  if (body === null) {
    return <section style={shell}><p>loading the tape…</p></section>;
  }

  const { trade, grade, tape } = body;
  return (
    <section style={shell}>
      <header style={{ display: "flex", gap: 16, alignItems: "baseline", flexWrap: "wrap" }}>
        <strong>
          {trade.side.toUpperCase()} {trade.lots} {trade.symbol}
        </strong>
        <span style={{ opacity: 0.8 }}>
          {trade.openedAt === null ? "" : clock(trade.openedAt)} → {clock(trade.closedAt)}
        </span>
        <span style={{ color: trade.rMultiple >= 0 ? "var(--phos-200)" : "var(--arcade-red)" }}>
          {trade.rMultiple >= 0 ? "+" : ""}{trade.rMultiple.toFixed(2)}R
        </span>
        {trade.tiltAtEntry === null ? null : (
          <span style={{ opacity: 0.7 }}>tilt at entry {trade.tiltAtEntry.toFixed(2)}</span>
        )}
      </header>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "flex-start" }}>
        <div style={{ flex: "1 1 520px", minWidth: 320, display: "flex", flexDirection: "column",
                      gap: 8 }}>
          {tape === null ? (
            // A pre-phase-2 trade has no window. It is still worth reviewing, so the markers stand
            // in for the chart rather than the screen going blank.
            <p style={{ opacity: 0.75 }}>
              no tape for this trade · entry {trade.entry} · exit {trade.exit}
            </p>
          ) : (
            <>
              <Chart body={body} seconds={seconds} playheadMs={transport.playheadMs} />
              <Timeline
                tape={tape}
                events={body.events}
                playheadMs={transport.playheadMs}
                nearest={nearest}
                onSeek={(ms) => setTransport((s) => seekTo(s, ms, window_))}
              />
            </>
          )}

          <div style={{ display: "flex", gap: 12, alignItems: "center", fontSize: 12 }}>
            <button type="button" onClick={() => setTransport((s) => togglePlay(s, window_))}>
              {transport.playing ? "pause" : "play"}
            </button>
            <span>{transport.speed}x</span>
            <span>{timeframeLabel(seconds)}</span>
            <span style={{ opacity: 0.7 }}>{clock(transport.playheadMs)}</span>
            <button type="button" onClick={() => stepTrade(-1)}>prev</button>
            <button type="button" onClick={() => stepTrade(1)}>next</button>
          </div>

          {/* The evening's trades, in the order they were taken. The same list LB/RB steps. */}
          <TradePicker rows={index} current={current} onPick={setCurrent} />

          {/* Without phase 8 there are no memos, and no audio element to show. */}
          {cue.memoId === null ? null : (
            <audio ref={audioRef} src={`/api/voice/${cue.memoId}/audio`} preload="auto" />
          )}
        </div>

        <aside style={{ flex: "0 1 300px", display: "flex", flexDirection: "column", gap: 10 }}>
          <GradePanel grade={grade} />
          <dl style={{ margin: 0, fontSize: 12, display: "grid", gridTemplateColumns: "auto 1fr",
                       gap: "4px 10px" }}>
            <dt style={{ opacity: 0.7 }}>entry</dt><dd style={dd}>{trade.entry ?? "—"}</dd>
            <dt style={{ opacity: 0.7 }}>exit</dt><dd style={dd}>{trade.exit ?? "—"}</dd>
            <dt style={{ opacity: 0.7 }}>MFE</dt><dd style={dd}>{fixed(trade.mfe)}</dd>
            <dt style={{ opacity: 0.7 }}>MAE</dt><dd style={dd}>{fixed(trade.mae)}</dd>
          </dl>
          <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 11, opacity: 0.75 }}>
            {CONTROLS.map((control) => (
              <li key={control.input}>{control.input} · {control.action}</li>
            ))}
          </ul>
        </aside>
      </div>
    </section>
  );
}

/**
 * The evening's trades.
 *
 * This lives here rather than on the deck because the deck's outcome panel aggregates by setup and
 * carries no per-trade rows — phase 6 kept per-trade money off it deliberately, and phase 10 is not
 * the place to put it back.
 */
function TradePicker({ rows, current, onPick }: {
  rows: IndexRow[];
  current: string | null;
  onPick: (cid: string) => void;
}): JSX.Element | null {
  if (rows.length === 0) return null;
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", fontSize: 11 }}>
      {rows.map((row) => (
        <button
          key={row.cid}
          type="button"
          onClick={() => onPick(row.cid)}
          title={row.hasTape ? clock(row.closedAt) : "no tape — markers only"}
          style={{
            opacity: row.hasTape ? 1 : 0.55,
            outline: row.cid === current ? "1px solid var(--phos-300)" : undefined,
          }}
        >
          {clock(row.closedAt)} {row.rMultiple >= 0 ? "+" : ""}{row.rMultiple.toFixed(1)}R
        </button>
      ))}
    </div>
  );
}

/** The phase 7 grade, beside the chart. Failing rules are information — they never blocked a fire. */
function GradePanel({ grade }: { grade: ReplayBody["grade"] }): JSX.Element {
  if (grade === null) {
    return <p style={{ fontSize: 12, opacity: 0.75 }}>no grade recorded for this fire</p>;
  }
  return (
    <div style={{ fontSize: 12, display: "flex", flexDirection: "column", gap: 4 }}>
      <strong style={{ color: grade.clean ? "var(--phos-200)" : "var(--arcade-yellow)" }}>
        {grade.requiredPass}/{grade.requiredTotal} rules OK{grade.clean ? " · clean" : ""}
      </strong>
      {grade.results.map((rule) => (
        <span key={rule.code} style={{ opacity: rule.unknown ? 0.5 : 0.9 }}>
          {rule.unknown ? "?" : rule.ok ? "✓" : "✗"} {rule.label}
          {rule.actual ? ` (${rule.actual})` : ""}
        </span>
      ))}
    </div>
  );
}

function fixed(value: number | null): string {
  return value === null ? "—" : value.toFixed(2);
}

const shell = {
  display: "flex",
  flexDirection: "column" as const,
  gap: 12,
  width: "100%",
};

const dd = { margin: 0 };
