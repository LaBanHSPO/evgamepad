/** Shapes served by `GET /api/deck/*`. Money-free by construction on the process side. */

export interface MonthBlock<T> {
  month: string | null;
  previousMonth: string | null;
  current: T;
  previous: T | null;
  delta: Record<string, number | null>;
}

export interface ProcessMonth {
  sessions: number;
  adherence: number | null;
  adherenceByRule: Record<string, number>;
  fires: number;
  declined: number;
  declinedRate: number | null;
  checkinAverage: number | null;
  opportunityQuality: number | null;
}

export interface ProcessView {
  panel: "process";
  disclaimer: string;
  citation: string;
  allTime: {
    sessions: number;
    adherence: number | null;
    adherenceByRule: Record<string, number>;
    fires: number;
    declined: number;
  };
  months: MonthBlock<ProcessMonth>;
  latestSession: {
    sessionId: string;
    openedAt: number;
    checkinPre: number | null;
    checkinPost: number | null;
    declined: number;
    opportunityQuality: number | null;
    verdict: string;
    note: string | null;
  } | null;
}

export interface OutcomeMonth {
  sessions: number;
  returnPct: number | null;
  averageR: number | null;
  winRate: number | null;
  profitFactor: number | null;
  maxDrawdown: number | null;
  trades: number;
}

export interface OutcomeView {
  panel: "outcome";
  disclaimer: string;
  sharpe: {
    value: number | null;
    display: string;
    sessions: number;
    enough: boolean;
    note: string;
  };
  months: MonthBlock<OutcomeMonth>;
  bySetup: Record<string, {
    trades: number;
    averageR: number | null;
    winRate: number | null;
    profitFactor: number | null;
  }>;
}

/** `null` is "not measured", which is different from zero and must not render as one. */
export function show(value: number | null | undefined, digits = 2, suffix = ""): string {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(digits)}${suffix}`;
}

export function percent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

/** A delta reads as a direction, not just a number. */
export function signed(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) return "—";
  return `${value >= 0 ? "+" : ""}${value.toFixed(digits)}`;
}
