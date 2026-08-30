/**
 * The one hook that owns the evening: pad -> FSM -> socket, and back.
 *
 * The division of labour matters for the hot path. **React owns layout and the
 * overlay; it does not re-render on quotes.** Prices land in refs and are
 * written to the DOM by `PriceTape` at 15 Hz. A 60 Hz `setState` per tick would
 * re-render the tree under the player's hands while they are trying to fire.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { Gateway, type ConnState, type PendingFire } from "../net/ws";
import {
  initialChord,
  stepChord,
  type ChordState,
} from "../pad/chord";
import {
  NO_INPUT,
  initialFsm,
  step,
  type ArmSide,
  type Fsm,
  type Inputs,
} from "../pad/fsm";
import { BUTTON, DEFAULT_PROFILE, beginProbe, probeFrame, profileFromProbe } from "../pad/map";
import { PadReader, rumble, startPolling, type RawFrame } from "../pad/poll";
import { beginPtt, endPtt, initialPtt, onClutchDuringPtt, type PttState } from "../pad/ptt";
import { TelemetryCollector } from "../pad/telemetry";
import type { ServerFrame } from "../protocol/types";
import type { CandleFrame } from "./Chart";
import { StandDownCounter, type MarketContext, type PnlUnit } from "./process";

export const SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"] as const;
export type Sym = (typeof SYMBOLS)[number];
export const TIMEFRAMES = ["M1", "M5", "M15", "H1"] as const;

export type Quote = { bid: number; ask: number; ts: number; digits: number };

export type Position = {
  positionId: number;
  sym: string;
  side: string;
  lots: number;
  entry: number;
  sl: number | null;
  tp: number | null;
  pnl: number;
  /** From the gateway's own R definition. Null until a plan exists. */
  rMultiple?: number | null;
};

/** What React renders. Deliberately excludes anything that ticks at quote rate. */
export type GameView = {
  conn: ConnState;
  connDetail: string;
  padConnected: boolean;
  padId: string;
  fsm: Fsm["state"];
  armed: ArmSide | null;
  clutch: number;
  sym: Sym;
  lots: number;
  timeframe: string;
  positions: Position[];
  sessionOpen: boolean;
  locked: boolean;
  standDowns: number;
  pnlUnit: PnlUnit;
  unknownFires: PendingFire[];
  lastReject: string | null;
  pttActive: boolean;
  overlayOpen: boolean;
};

export type GameApi = {
  view: GameView;
  quotes: React.MutableRefObject<Map<string, Quote>>;
  /** Chart frames, drained by the chart's own rAF loop. */
  candles: React.MutableRefObject<CandleFrame[]>;
  connect: (token: string) => void;
  setPnlUnit: (unit: PnlUnit) => void;
  /** Keyboard/click Flatten. Works with no pad, and bypasses the dead-man. */
  flatten: () => void;
  closePosition: (positionId: number) => void;
  clearUnknown: (cid: string) => void;
  marketContext: () => MarketContext;
};

const WS_URL = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;

export function useGame(): GameApi {
  const gatewayRef = useRef<Gateway | null>(null);
  const quotes = useRef<Map<string, Quote>>(new Map());
  const candles = useRef<CandleFrame[]>([]);
  const fsmRef = useRef<Fsm>(initialFsm());
  const prevInputs = useRef<Inputs>(NO_INPUT);
  const chordRef = useRef<ChordState>(initialChord());
  const prevBumpers = useRef({ lb: false, rb: false });
  const pttRef = useRef<PttState>(initialPtt());
  const readerRef = useRef(new PadReader(DEFAULT_PROFILE));
  const probeRef = useRef(beginProbe());
  const telemetryRef = useRef(new TelemetryCollector(performance.now()));
  const standDownRef = useRef(new StandDownCounter());
  const lastFrameAt = useRef(performance.now());
  const prevDpad = useRef({ up: false, down: false, left: false, right: false });

  const [view, setView] = useState<GameView>({
    conn: "idle",
    connDetail: "",
    padConnected: false,
    padId: "",
    fsm: "LOCKED",
    armed: null,
    clutch: 0,
    sym: "XAUUSD",
    lots: 0.01,
    timeframe: "M5",
    positions: [],
    sessionOpen: false,
    locked: true,
    standDowns: 0,
    pnlUnit: "R",
    unknownFires: [],
    lastReject: null,
    pttActive: false,
    overlayOpen: false,
  });
  const viewRef = useRef(view);
  const patch = useCallback((next: Partial<GameView>) => {
    viewRef.current = { ...viewRef.current, ...next };
    setView(viewRef.current);
  }, []);

  const marketContext = useCallback((): MarketContext => {
    const q = quotes.current.get(viewRef.current.sym);
    return {
      insideWindow: viewRef.current.sessionOpen,
      setupNamed: false, // phase 7 fills this from the playbook
      minutesToNews: null, // phase 4 fills this from the calendar
      lots: viewRef.current.lots,
      maxLots: viewRef.current.sym === "XAUUSD" ? 0.1 : 0.5,
      spread: q ? q.ask - q.bid : null,
      maxSpread: viewRef.current.sym === "XAUUSD" ? 0.8 : null,
    };
  }, []);

  const onFrame = useCallback(
    (frame: ServerFrame) => {
      switch (frame.t) {
        case "quote": {
          const p = frame.p as Quote & { sym: string };
          // Straight into a ref. No setState: this arrives many times a second
          // and React must not re-render the tree under a live ARM.
          quotes.current.set(p.sym, { bid: p.bid, ask: p.ask, ts: p.ts, digits: p.digits });
          break;
        }
        case "candle":
          // Into a ref, like quotes. The chart drains it on its own frame.
          candles.current.push(frame.p as CandleFrame);
          break;
        case "welcome":
          patch({ connDetail: "" });
          break;
        case "session": {
          const p = frame.p as { opensAllowed: boolean; state: string };
          patch({ sessionOpen: p.opensAllowed, locked: p.state === "locked" });
          break;
        }
        case "pos.snap":
          patch({ positions: (frame.p as { positions: Position[] }).positions });
          break;
        case "order.ack":
          rumble(0.9, 180);
          patch({ lastReject: null, unknownFires: [...(gatewayRef.current?.pending.values() ?? [])] });
          break;
        case "order.reject": {
          rumble(0.35, 90);
          const p = frame.p as { reason: string; detail?: string };
          patch({
            lastReject: p.detail ? `${p.reason}: ${p.detail}` : p.reason,
            unknownFires: [...(gatewayRef.current?.pending.values() ?? [])],
          });
          break;
        }
        case "order.upd":
          patch({ unknownFires: [...(gatewayRef.current?.pending.values() ?? [])] });
          break;
        default:
          break;
      }
    },
    [patch],
  );

  const connect = useCallback(
    (token: string) => {
      const gw = new Gateway(WS_URL, {
        onFrame,
        onState: (state, detail) => patch({ conn: state, connDetail: detail ?? "" }),
        onUnknown: () => patch({ unknownFires: [...(gatewayRef.current?.pending.values() ?? [])] }),
      });
      gw.setToken(token);
      gatewayRef.current = gw;
      gw.connect();
    },
    [onFrame, patch],
  );

  // -- the pad loop -------------------------------------------------------
  useEffect(() => {
    const handle = startPolling((raw: RawFrame) => {
      const now = raw.at;
      const dt = now - lastFrameAt.current;
      lastFrameAt.current = now;

      if (raw.connected && probeRef.current.moved.size === 0) {
        probeFrame(probeRef.current, raw.values.map((v) => ({ value: v })));
        readerRef.current.profile = profileFromProbe(probeRef.current, readerRef.current.profile);
      }

      const pad = readerRef.current.read(raw);
      const gw = gatewayRef.current;

      const next: Inputs = {
        clutch: pad.clutch,
        confirm: pad.confirm,
        armBuy: raw.buttons[BUTTON.A] ?? false,
        armSell: raw.buttons[BUTTON.B] ?? false,
        armClose: raw.buttons[BUTTON.X] ?? false,
        armPanic: raw.buttons[BUTTON.Y] ?? false,
        toggleLock: raw.buttons[BUTTON.VIEW] ?? false,
        overlay: raw.buttons[BUTTON.MENU] ?? false,
        visible: raw.visible,
        padConnected: raw.connected,
      };

      // Bumpers: timeframe on release, or the PTT chord. Neither is on the
      // order path, so this runs beside the FSM rather than inside it.
      const bumpers = {
        lb: raw.buttons[BUTTON.LB] ?? false,
        rb: raw.buttons[BUTTON.RB] ?? false,
      };
      const chord = stepChord(chordRef.current, prevBumpers.current, bumpers, now);
      chordRef.current = chord.state;
      prevBumpers.current = bumpers;
      if (chord.event.kind === "timeframe") {
        const i = TIMEFRAMES.indexOf(viewRef.current.timeframe as (typeof TIMEFRAMES)[number]);
        const nextTf = TIMEFRAMES[Math.min(Math.max(i + chord.event.direction, 0), TIMEFRAMES.length - 1)]!;
        patch({ timeframe: nextTf });
      } else if (chord.event.kind === "ptt") {
        if (chord.event.phase === "begin") {
          const r = beginPtt(pttRef.current, fsmRef.current.state, now);
          pttRef.current = r.ptt;
          patch({ pttActive: r.ptt.active });
        } else {
          pttRef.current = endPtt(pttRef.current, now).ptt;
          patch({ pttActive: false });
        }
      }

      // Reaching for the clutch mid-memo submits it rather than discarding it.
      if (pttRef.current.active && next.clutch) {
        pttRef.current = onClutchDuringPtt(pttRef.current, now).ptt;
        patch({ pttActive: false });
      }

      // Lot and symbol live on the D-pad, deliberately never on the clutch:
      // binding size to the trigger you hold to fire is how a lot changes
      // during an ARM.
      handleDpad(raw, prevDpad.current, viewRef.current, patch, telemetryRef.current);
      prevDpad.current = {
        up: raw.buttons[BUTTON.DPAD_UP] ?? false,
        down: raw.buttons[BUTTON.DPAD_DOWN] ?? false,
        left: raw.buttons[BUTTON.DPAD_LEFT] ?? false,
        right: raw.buttons[BUTTON.DPAD_RIGHT] ?? false,
      };

      const blocked = gw?.blocked ?? false;
      const result = step(fsmRef.current, prevInputs.current, next, now, { fireBlocked: blocked });
      const before = fsmRef.current.state;
      fsmRef.current = result.fsm;
      prevInputs.current = next;

      telemetryRef.current.frame(dt, next.clutch, result.fsm.state === "ARMED");
      if (result.transition.kind !== "none") {
        telemetryRef.current.transition({
          at: now,
          from: before,
          to: result.fsm.state,
          side: result.fsm.side,
          reason: result.transition.kind === "cancel" ? result.transition.reason : null,
        });
      }

      switch (result.transition.kind) {
        case "arm":
          rumble(0.25, 60);
          break;
        case "cancel": {
          // A cancel into a bad tape is a win, and is counted as one.
          const event = standDownRef.current.record(Date.now(), marketContext());
          if (event) patch({ standDowns: standDownRef.current.count });
          break;
        }
        case "fire": {
          telemetryRef.current.fired(result.transition.armedAt, now);
          sendIntent(gw, result.transition.side, viewRef.current, result.transition.armedAt);
          break;
        }
        default:
          break;
      }

      if (gw) {
        gw.flags = { visible: raw.visible, pad: raw.connected, clutch: pad.clutch };
        const batch = telemetryRef.current.maybeFlush(now, {
          sym: viewRef.current.sym,
          lots: viewRef.current.lots,
        });
        if (batch) gw.telemetry(batch);
      }

      if (
        result.fsm.state !== viewRef.current.fsm ||
        result.fsm.side !== viewRef.current.armed ||
        raw.connected !== viewRef.current.padConnected ||
        result.fsm.overlayOpen !== viewRef.current.overlayOpen
      ) {
        patch({
          fsm: result.fsm.state,
          armed: result.fsm.side,
          padConnected: raw.connected,
          padId: raw.id,
          clutch: pad.lt,
          overlayOpen: result.fsm.overlayOpen,
        });
      }
    });
    return () => handle.stop();
  }, [marketContext, patch]);

  // Heartbeat and the unresolved-fire sweep.
  useEffect(() => {
    const id = setInterval(() => {
      const gw = gatewayRef.current;
      if (!gw) return;
      gw.ping();
      const stale = gw.sweepTimeouts();
      if (stale.length) patch({ unknownFires: [...gw.pending.values()] });
    }, 1000);
    return () => clearInterval(id);
  }, [patch]);

  // Re-subscribe whenever the chart series changes: the gateway replays that
  // series' history on `sub`, so the chart fills in one frame rather than one
  // bar at a time.
  useEffect(() => {
    const gw = gatewayRef.current;
    if (!gw || gw.state !== "open") return;
    candles.current.length = 0;
    gw.send("sub", { ch: "quotes", syms: [view.sym], tf: view.timeframe });
  }, [view.sym, view.timeframe, view.conn]);

  const flatten = useCallback(() => {
    // Available with no pad and never gated: a safety exit must not depend on
    // hardware the player may have just unplugged.
    gatewayRef.current?.fire("panic", { armedAt: Date.now() });
  }, []);

  const closePosition = useCallback((positionId: number) => {
    gatewayRef.current?.fire("close", { positionId, armedAt: Date.now() });
  }, []);

  return {
    view,
    quotes,
    candles,
    connect,
    setPnlUnit: (pnlUnit) => patch({ pnlUnit }),
    flatten,
    closePosition,
    clearUnknown: (cid) => {
      gatewayRef.current?.clearPending(cid);
      patch({ unknownFires: [...(gatewayRef.current?.pending.values() ?? [])] });
    },
    marketContext,
  };
}

const LOT_STEP = 0.01;
const MAX_LOTS: Record<string, number> = { XAUUSD: 0.1, EURUSD: 0.5, GBPUSD: 0.5, USDJPY: 0.5 };

type Dpad = { up: boolean; down: boolean; left: boolean; right: boolean };

function handleDpad(
  raw: RawFrame,
  prev: Dpad,
  view: GameView,
  patch: (next: Partial<GameView>) => void,
  telemetry: TelemetryCollector,
): void {
  const now: Dpad = {
    up: raw.buttons[BUTTON.DPAD_UP] ?? false,
    down: raw.buttons[BUTTON.DPAD_DOWN] ?? false,
    left: raw.buttons[BUTTON.DPAD_LEFT] ?? false,
    right: raw.buttons[BUTTON.DPAD_RIGHT] ?? false,
  };

  const step = (delta: number) => {
    const max = MAX_LOTS[view.sym] ?? 0.5;
    const lots = Math.min(Math.max(Number((view.lots + delta).toFixed(2)), LOT_STEP), max);
    if (lots !== view.lots) {
      telemetry.lotStep();
      patch({ lots });
    }
  };
  if (!prev.up && now.up) step(LOT_STEP);
  if (!prev.down && now.down) step(-LOT_STEP);

  const cycle = (direction: number) => {
    const i = SYMBOLS.indexOf(view.sym);
    const sym = SYMBOLS[(i + direction + SYMBOLS.length) % SYMBOLS.length]!;
    const max = MAX_LOTS[sym] ?? 0.5;
    patch({ sym, lots: Math.min(view.lots, max) });
  };
  if (!prev.left && now.left) cycle(-1);
  if (!prev.right && now.right) cycle(1);
}

function sendIntent(gw: Gateway | null, side: ArmSide, view: GameView, armedAt: number): void {
  if (!gw) return;
  if (side === "panic") {
    gw.fire("panic", { armedAt });
    return;
  }
  if (side === "close") {
    const open = view.positions[0];
    if (open) gw.fire("close", { positionId: open.positionId, armedAt });
    return;
  }
  gw.fire("open", { sym: view.sym, side, type: "market", lots: view.lots, armedAt });
}
