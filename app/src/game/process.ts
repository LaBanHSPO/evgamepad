/**
 * Process cues: the adherence badge, the stand-down counter, and R-first P/L.
 *
 * The product's stated goal is confidence and decision quality, not money. Two
 * consequences show up here:
 *
 *  - **P/L is shown in R by default**, with dollars one deliberate toggle away.
 *    Watching the money mid-trade is what pulls attention off the process.
 *  - **Cancelling into a bad tape counts as a win.** The stand-down counter
 *    records the conditions that were true at the moment of the cancel, and
 *    emits a `stand_down` phase 11 will reuse for its Selectivity axis rather
 *    than adding a second counter of its own.
 */

export type AdherenceCue = {
  id: string;
  label: string;
  ok: boolean;
};

export type MarketContext = {
  insideWindow: boolean;
  setupNamed: boolean;
  /** Minutes to the next high-impact release, or null when none is near. */
  minutesToNews: number | null;
  lots: number;
  maxLots: number;
  spread: number | null;
  maxSpread: number | null;
};

export const NEWS_BLACKOUT_MIN = 15;

/**
 * The four cues the HUD shows live. They are advisory: none of them can block a
 * fire -- the gateway's risk rules are the only thing that does that.
 */
export function adherenceCues(ctx: MarketContext): AdherenceCue[] {
  return [
    { id: "window", label: "in session", ok: ctx.insideWindow },
    { id: "setup", label: "named setup", ok: ctx.setupNamed },
    {
      id: "news",
      label: `outside T-${NEWS_BLACKOUT_MIN}`,
      ok: ctx.minutesToNews === null || Math.abs(ctx.minutesToNews) > NEWS_BLACKOUT_MIN,
    },
    { id: "lots", label: "lot at cap", ok: ctx.lots <= ctx.maxLots },
  ];
}

export function adherenceScore(cues: AdherenceCue[]): number {
  if (cues.length === 0) return 1;
  return cues.filter((c) => c.ok).length / cues.length;
}

/**
 * Was standing down the right call? True when any cue was failing, which is
 * what makes the counter meaningful rather than a tally of hesitation.
 */
export function wasWorthStandingDown(ctx: MarketContext): boolean {
  const failing = adherenceCues(ctx).filter((c) => !c.ok);
  const wideSpread =
    ctx.maxSpread !== null && ctx.spread !== null && ctx.spread > ctx.maxSpread;
  return failing.length > 0 || wideSpread;
}

export type StandDown = {
  at: number;
  /** Cue ids that were failing. Phase 11's Selectivity axis reads these. */
  conditions: string[];
};

export class StandDownCounter {
  readonly events: StandDown[] = [];

  /** Returns the recorded event, or null when the cancel was not a stand-down. */
  record(at: number, ctx: MarketContext): StandDown | null {
    if (!wasWorthStandingDown(ctx)) return null;
    const conditions = adherenceCues(ctx)
      .filter((c) => !c.ok)
      .map((c) => c.id);
    if (
      ctx.maxSpread !== null &&
      ctx.spread !== null &&
      ctx.spread > ctx.maxSpread
    ) {
      conditions.push("spread");
    }
    const event: StandDown = { at, conditions };
    this.events.push(event);
    return event;
  }

  get count(): number {
    return this.events.length;
  }
}

export type PnlUnit = "R" | "USD";

/** R by default. Dollars are a deliberate toggle, never the landing state. */
export const DEFAULT_PNL_UNIT: PnlUnit = "R";

export function formatPnl(usd: number, rUsd: number | null, unit: PnlUnit): string {
  if (unit === "USD") return money(usd);
  // Zero is zero in any unit, so being flat never forces the display back to
  // dollars -- which would otherwise contradict the "in R" label.
  if (usd === 0) return "0.00R";
  if (rUsd === null || rUsd <= 0) return money(usd);
  return r(usd / rUsd);
}

function money(usd: number): string {
  return `${usd >= 0 ? "+" : "-"}$${Math.abs(usd).toFixed(2)}`;
}

function r(value: number): string {
  return `${value >= 0 ? "+" : "-"}${Math.abs(value).toFixed(2)}R`;
}

export type OpenPosition = { pnl: number; rMultiple?: number | null };

/**
 * Open P/L for the HUD.
 *
 * R comes from the gateway's own per-position `rMultiple`, never from a
 * constant divided into the dollars -- the HUD inventing its own R is exactly
 * how the HUD and the journal end up disagreeing about the same trade. If any
 * open position has no R yet, the whole figure falls back to dollars rather
 * than reporting a partial sum as if it were complete.
 */
export function formatOpenPnl(positions: OpenPosition[], unit: PnlUnit): string {
  const usd = positions.reduce((sum, p) => sum + p.pnl, 0);
  if (unit === "USD") return money(usd);
  if (positions.length === 0) return "0.00R";
  if (positions.some((p) => p.rMultiple === null || p.rMultiple === undefined)) {
    return money(usd);
  }
  return r(positions.reduce((sum, p) => sum + (p.rMultiple ?? 0), 0));
}
