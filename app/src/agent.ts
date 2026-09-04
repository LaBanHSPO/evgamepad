/**
 * The client agent: pad frames in, protocol intents out.
 *
 * Everything the pad can cause happens here, which is why nothing here decides whether an order
 * is *allowed*. The gateway owns that. The agent's job is to turn a two-handed physical gesture
 * into exactly one intent with a stable cid, and to keep the dead-man flags honest so the server
 * can lock opens the instant the tab loses focus.
 *
 * Two safety exits deliberately bypass the pad entirely: `flatten()` and `closePosition()` are
 * callable from a button or the keyboard, so a dead pad never traps an open position.
 */

import { stepChord, initialChordState } from "./pad/chord";
import type { ChordState } from "./pad/chord";
import { initialState as initialFsmState, onSocketClose, resolve, step } from "./pad/fsm";
import type { Effect, FsmState, PadInput, Side } from "./pad/fsm";
import type { RawFrame } from "./pad/poll";
import { TelemetryBatcher } from "./pad/telemetry";
import { newCid } from "./net/cid";
import type { GameClient } from "./net/ws";
import type { Envelope } from "./protocol/types";

/** What the HUD needs from the agent, refreshed per frame but rendered at its own rate. */
export interface AgentView {
  phase: FsmState["phase"];
  side: Side | null;
  symbol: string;
  lots: number;
  timeframe: string;
  ptt: boolean;
  padConnected: boolean;
  stoodDown: number;
  pendingIntents: number;
  overlayOpen: boolean;
}

export interface AgentOptions {
  client: GameClient;
  symbols: string[];
  timeframes?: string[];
  lotSteps?: number[];
  confirmHoldMs?: number;
  /** Live conditions that make not firing the better trade. Phase 4 and 9 will supply real ones. */
  standDownConditions?: () => string[];
  onView?: (view: AgentView) => void;
  onStandDown?: (conditions: string[]) => void;
}

const DEFAULT_TIMEFRAMES = ["M1", "M5", "M15", "H1"];
const DEFAULT_LOT_STEPS = [0.01, 0.02, 0.05, 0.1];

export class GameAgent {
  private fsm: FsmState = initialFsmState;
  private chord: ChordState = initialChordState;
  private telemetry = new TelemetryBatcher(Date.now());
  private symbolIndex = 0;
  private lotIndex = 0;
  private timeframeIndex = 1;
  private stoodDown = 0;
  private padConnected = false;
  private positionId: number | null = null;

  constructor(private options: AgentOptions) {}

  get view(): AgentView {
    return {
      phase: this.fsm.phase,
      side: this.fsm.side,
      symbol: this.options.symbols[this.symbolIndex],
      lots: this.lotSteps[this.lotIndex],
      timeframe: this.timeframes[this.timeframeIndex],
      ptt: this.chord.ptt,
      padConnected: this.padConnected,
      stoodDown: this.stoodDown,
      pendingIntents: this.options.client.pending,
      overlayOpen: this.fsm.overlayOpen,
    };
  }

  private get timeframes(): string[] {
    return this.options.timeframes ?? DEFAULT_TIMEFRAMES;
  }

  private get lotSteps(): number[] {
    return this.options.lotSteps ?? DEFAULT_LOT_STEPS;
  }

  /**
   * Phase 9's friction, as a parameter of the fire predicate.
   *
   * Tilt changes exactly this and whether the server accepts an open. The FSM gains no state, so
   * `fsm.test.ts` stays valid unchanged.
   */
  setConfirmHoldMs(ms: number): void {
    this.options.confirmHoldMs = ms;
  }

  /**
   * The GameOverlay is a safe surface. Opening it from a click must cancel an arm the same way
   * the Menu rising edge does inside the FSM, or the two sources of truth would drift.
   */
  setOverlayOpen(open: boolean): void {
    if (this.fsm.overlayOpen === open) return;
    let next = { ...this.fsm, overlayOpen: open };
    if (open) {
      next = { ...next, side: null, armedAt: null };
      if (next.phase === "ARMED" || next.phase === "CLUTCH") next = { ...next, phase: "IDLE" };
    }
    this.fsm = next;
    this.options.onView?.(this.view);
  }

  /** One pad frame. Called from the rAF poller; it never renders anything itself. */
  onFrame(frame: RawFrame): void {
    this.padConnected = frame.input.padConnected;
    const { state, effects } = step(this.fsm, frame.input, {
      confirmHoldMs: this.options.confirmHoldMs,
    });
    this.fsm = state;

    const chordResult = stepChord(this.chord, {
      lb: frame.bumpers.lb,
      rb: frame.bumpers.rb,
      key: false,
      phase: this.fsm.phase,
      nowMs: frame.input.nowMs,
    });
    this.chord = chordResult.state;

    this.telemetry.observe(effects, frame.input.nowMs);
    this.applyEffects(effects, frame.input);
    this.applyChordEffects(chordResult.effects);

    // The dead-man flags travel on the heartbeat, so the gateway can lock opens on its own clock.
    this.options.client.setHeartbeat({
      visible: frame.input.visible,
      pad: frame.input.padConnected,
      clutch: this.fsm.clutchHeld,
    });

    const sample = this.telemetry.drain(Date.now());
    if (sample !== null) {
      this.options.client.send("pad.telemetry", "session", { ...sample });
    }

    this.options.onView?.(this.view);
  }

  /** A frame with no pad at all — unplugged, or the tab went away. */
  onAbsent(input: PadInput): void {
    this.onFrame({
      input,
      snapshot: {},
      sticks: { lsX: 0, lsY: 0, rsX: 0, rsY: 0 },
      bumpers: { lb: false, rb: false },
    });
  }

  private applyEffects(effects: Effect[], input: PadInput): void {
    for (const effect of effects) {
      switch (effect.kind) {
        case "intent":
          this.emitIntent(effect.side, effect.armedAt);
          break;
        case "lot":
          this.lotIndex = clamp(this.lotIndex + effect.step, 0, this.lotSteps.length - 1);
          break;
        case "symbol":
          this.symbolIndex = wrap(this.symbolIndex + effect.step, this.options.symbols.length);
          break;
        case "cancel":
          this.recordStandDown(input);
          break;
        default:
          break;
      }
    }
  }

  private applyChordEffects(effects: ReturnType<typeof stepChord>["effects"]): void {
    for (const effect of effects) {
      if (effect.kind === "timeframe") {
        this.timeframeIndex = clamp(
          this.timeframeIndex + effect.step, 0, this.timeframes.length - 1,
        );
      }
      // A `ptt` effect is deliberately inert here. Phase 3 owns the control event and the
      // fire-on-release arbitration; nothing acquires a microphone until phase 8.
    }
  }

  /**
   * A cancelled arm while a stand-down condition was live is the counter's whole point: choosing
   * not to fire on a bad tape is a result worth recording, not an absence of one.
   */
  private recordStandDown(input: PadInput): void {
    if (!input.visible || !input.padConnected) return;
    const conditions = this.options.standDownConditions?.() ?? [];
    if (conditions.length === 0) return;
    this.stoodDown += 1;
    this.options.onStandDown?.(conditions);
  }

  private emitIntent(side: Side, armedAt: number): void {
    const cid = newCid();
    if (side === "buy" || side === "sell") {
      this.options.client.sendIntent({
        cid,
        t: "intent.open",
        ch: "orders",
        payload: {
          sym: this.view.symbol,
          side,
          type: "market",
          lots: this.view.lots,
          clutch: true,
          armedAt,
        },
      });
      return;
    }
    if (side === "close") {
      this.closePosition(cid);
      return;
    }
    this.flatten(cid);
  }

  /** Full close. Reachable from the pad, a button, or the keyboard — never gated. */
  closePosition(cid: string = newCid()): void {
    if (this.positionId === null) return;
    this.options.client.sendIntent({
      cid,
      t: "intent.close",
      ch: "orders",
      payload: { positionId: this.positionId, clutch: true, armedAt: Date.now() },
    });
  }

  /** Panic flatten. The one control that must work with no pad, no focus, and a dead session. */
  flatten(cid: string = newCid()): void {
    this.options.client.sendIntent({
      cid,
      t: "intent.panic",
      ch: "orders",
      payload: { clutch: true, armedAt: Date.now() },
    });
  }

  /** Gateway traffic the agent itself cares about. The HUD gets everything via its own handler. */
  onMessage(envelope: Envelope): void {
    if (envelope.t === "order.ack" || envelope.t === "order.upd") {
      this.fsm = resolve(this.fsm, true).state;
      const positionId = (envelope.p as { positionId?: number }).positionId;
      if (typeof positionId === "number") this.positionId = positionId;
    } else if (envelope.t === "order.reject") {
      this.fsm = resolve(this.fsm, false).state;
    } else if (envelope.t === "pos.snap") {
      const positions = (envelope.p as { positions?: { positionId: number }[] }).positions ?? [];
      this.positionId = positions.length > 0 ? positions[0].positionId : null;
    }
    this.options.onView?.(this.view);
  }

  /** The socket dropped. Lock the client and keep any outstanding cid exactly as it was. */
  onSocketClosed(): void {
    this.fsm = onSocketClose(this.fsm);
    this.options.onView?.(this.view);
  }
}

function clamp(value: number, low: number, high: number): number {
  return Math.min(high, Math.max(low, value));
}

function wrap(value: number, length: number): number {
  return ((value % length) + length) % length;
}
