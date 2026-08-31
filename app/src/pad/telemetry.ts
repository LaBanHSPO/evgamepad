/**
 * Pad telemetry: the only source phase 9's tilt score will ever have.
 *
 * Cheap to design in now, expensive to retrofit — so every FSM transition contributes here from
 * day one, even though nothing reads it until phase 9.
 *
 * The hard rule is the batching. This rides the `session` channel at **1 Hz**, never per frame:
 * at 60 Hz it would be the loudest thing on a socket whose entire job is prioritising order acks.
 */

import type { Effect, Phase } from "./fsm";

/** One batched sample, matching the frozen `pad.telemetry` payload. */
export interface PadTelemetry {
  ts: number;
  from: string;
  to: string;
  sym?: string;
  lots?: number;
  reason?: string;
  clutchMs: number;
  armMs: number;
  clutchCycles: number;
  armFlips: number;
  btnRateHz: number;
  lotStepsSince: number;
  ttfMs?: number;
}

const BATCH_INTERVAL_MS = 1000;

export class TelemetryBatcher {
  private clutchMs = 0;
  private armMs = 0;
  private clutchCycles = 0;
  private armFlips = 0;
  private buttonPresses = 0;
  private lotSteps = 0;
  private clutchSince: number | null = null;
  private armSince: number | null = null;
  private ttfMs: number | undefined;
  private from: Phase = "LOCKED";
  private to: Phase = "LOCKED";
  private reason: string | undefined;
  private lastEmit: number;

  constructor(startMs: number) {
    this.lastEmit = startMs;
  }

  /** Fold one frame's effects in. Called every frame; emits nothing. */
  observe(effects: Effect[], nowMs: number): void {
    for (const effect of effects) {
      switch (effect.kind) {
        case "transition":
          this.onTransition(effect.from, effect.to, effect.reason, nowMs);
          break;
        case "lot":
          this.lotSteps += 1;
          this.buttonPresses += 1;
          break;
        case "symbol":
          this.buttonPresses += 1;
          break;
        case "intent":
          // Time to fire: how long the armed side sat before the player committed.
          this.ttfMs = nowMs - effect.armedAt;
          this.buttonPresses += 1;
          break;
        default:
          break;
      }
    }
  }

  private onTransition(from: Phase, to: Phase, reason: string, nowMs: number): void {
    this.from = from;
    this.to = to;
    this.reason = reason;

    const enteringClutch = to === "CLUTCH" && from !== "ARMED";
    const leavingClutch = from === "CLUTCH" || from === "ARMED";
    if (enteringClutch) {
      this.clutchSince = nowMs;
      this.clutchCycles += 1;
    } else if (leavingClutch && to !== "ARMED" && to !== "CLUTCH" && this.clutchSince !== null) {
      this.clutchMs += nowMs - this.clutchSince;
      this.clutchSince = null;
    }

    if (to === "ARMED") {
      this.armSince = nowMs;
      this.armFlips += 1;
    } else if (from === "ARMED" && this.armSince !== null) {
      this.armMs += nowMs - this.armSince;
      this.armSince = null;
    }

    this.buttonPresses += 1;
  }

  /**
   * At most one sample per second, including an idle heartbeat when nothing happened —
   * phase 9 needs to tell a quiet evening from a disconnected one.
   */
  drain(nowMs: number): PadTelemetry | null {
    if (nowMs - this.lastEmit < BATCH_INTERVAL_MS) return null;
    const elapsedS = (nowMs - this.lastEmit) / 1000;

    const sample: PadTelemetry = {
      ts: nowMs,
      from: this.from,
      to: this.to,
      reason: this.reason,
      clutchMs: Math.round(this.clutchMs + (this.clutchSince !== null ? nowMs - this.clutchSince : 0)),
      armMs: Math.round(this.armMs + (this.armSince !== null ? nowMs - this.armSince : 0)),
      clutchCycles: this.clutchCycles,
      armFlips: this.armFlips,
      btnRateHz: Number((this.buttonPresses / elapsedS).toFixed(2)),
      lotStepsSince: this.lotSteps,
      ttfMs: this.ttfMs,
    };

    this.lastEmit = nowMs;
    this.clutchMs = 0;
    this.armMs = 0;
    this.clutchCycles = 0;
    this.armFlips = 0;
    this.buttonPresses = 0;
    this.lotSteps = 0;
    this.reason = undefined;
    this.ttfMs = undefined;
    if (this.clutchSince !== null) this.clutchSince = nowMs;
    if (this.armSince !== null) this.armSince = nowMs;
    return sample;
  }
}
