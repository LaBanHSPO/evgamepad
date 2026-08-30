/**
 * Pad telemetry for phase 9's tilt meter.
 *
 * Phase 9 has no other source for this, and retrofitting it would mean
 * replaying an evening that no longer exists -- so it is collected now, even
 * though nothing consumes it yet.
 *
 * The batching is a requirement, not an optimisation. Transitions are recorded
 * per frame and flushed **once a second**; putting them on the socket at frame
 * rate would compete with the order acks that socket exists to deliver.
 */

import type { ArmSide, CancelReason, FsmState } from "./fsm";

export const BATCH_MS = 1000;

export type TransitionRecord = {
  at: number;
  from: FsmState;
  to: FsmState;
  side: ArmSide | null;
  reason: CancelReason | null;
};

export type TelemetryBatch = {
  ts: number;
  from: string | null;
  to: string | null;
  sym: string | null;
  lots: number | null;
  reason: string | null;
  /** Total ms the clutch was held this second. */
  clutchMs: number;
  /** Total ms spent in ARMED this second. */
  armMs: number;
  /** Clutch presses this second. */
  clutchCycles: number;
  /** ARM side changes this second -- the strongest tilt signal in the set. */
  armFlips: number;
  /** Button presses per second across the pad. */
  btnRateHz: number;
  /** Lot steps since the last flush. */
  lotStepsSince: number;
  /** Time from ARM to FIRE, when one happened this second. */
  ttfMs: number | null;
};

export class TelemetryCollector {
  private clutchMs = 0;
  private armMs = 0;
  private clutchCycles = 0;
  private armFlips = 0;
  private buttonPresses = 0;
  private lotSteps = 0;
  private ttfMs: number | null = null;
  private lastFlush: number;
  private last: TransitionRecord | null = null;

  constructor(now: number) {
    this.lastFlush = now;
  }

  /** Called every frame with the elapsed ms since the previous frame. */
  frame(dtMs: number, clutchHeld: boolean, armed: boolean): void {
    if (clutchHeld) this.clutchMs += dtMs;
    if (armed) this.armMs += dtMs;
  }

  transition(record: TransitionRecord): void {
    this.last = record;
    if (record.to === "CLUTCH" && record.from === "IDLE") this.clutchCycles += 1;
    if (record.to === "ARMED" && record.from === "ARMED") this.armFlips += 1;
    if (record.to === "FIRE" || record.side) this.buttonPresses += 1;
  }

  buttonPress(count = 1): void {
    this.buttonPresses += count;
  }

  lotStep(): void {
    this.lotSteps += 1;
  }

  fired(armedAt: number, at: number): void {
    this.ttfMs = at - armedAt;
  }

  /**
   * Flush if a second has passed. Returns null otherwise, so the caller can
   * call this every frame without gating on the clock itself.
   *
   * A batch is emitted even when nothing happened: the idle heartbeat is what
   * lets phase 9 tell "calm" apart from "went to make tea".
   */
  maybeFlush(
    now: number,
    context: { sym: string | null; lots: number | null },
    force = false,
  ): TelemetryBatch | null {
    const elapsed = now - this.lastFlush;
    // `force` is used on an ARM transition and nowhere else. The confirm
    // overlay's grade comes from the gateway, the protocol has no `arm`
    // message, and waiting up to a second for the next batch would show the
    // player a grade for a decision they already made. Still not per-frame:
    // one flush per ARM, not one per tick.
    if (!force && elapsed < BATCH_MS) return null;

    const batch: TelemetryBatch = {
      ts: Math.round(now),
      from: this.last?.from ?? null,
      to: this.last?.to ?? null,
      sym: context.sym,
      lots: context.lots,
      reason: this.last?.reason ?? null,
      clutchMs: Math.round(this.clutchMs),
      armMs: Math.round(this.armMs),
      clutchCycles: this.clutchCycles,
      armFlips: this.armFlips,
      btnRateHz: Number((this.buttonPresses / (elapsed / 1000)).toFixed(2)),
      lotStepsSince: this.lotSteps,
      ttfMs: this.ttfMs,
    };

    this.clutchMs = 0;
    this.armMs = 0;
    this.clutchCycles = 0;
    this.armFlips = 0;
    this.buttonPresses = 0;
    this.lotSteps = 0;
    this.ttfMs = null;
    this.last = null;
    this.lastFlush = now;
    return batch;
  }
}
