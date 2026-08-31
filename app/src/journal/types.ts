/** Shapes served by `GET|PUT /api/journal/*`. */

export interface ReadinessItem {
  item: string;
  ok: boolean | null;
  note?: string | null;
}

export interface DailyAnalysis {
  updatedAt: number;
  thesis: string | null;
  instruments: string[];
  keyLevels: { price: number; label: string }[];
  invalidation: string | null;
  eventRisks: string | null;
  tags: string[];
  notes: string | null;
}

export interface Attachment {
  id: string;
  mime: string;
  bytes: number;
  width: number | null;
  height: number | null;
  label: string | null;
  created_at: number;
}

export interface TodayView {
  sessionId: string;
  readiness: ReadinessItem[];
  analysis: DailyAnalysis | null;
  deskPlan: { createdAt: number; bias: string | null; setup: string | null; text: string;
              offline: boolean } | null;
  attachments: Attachment[];
  checkin: { pre: number | null; post: number | null; declined: number;
             opportunityQuality: number | null } | null;
}

export interface StageScore {
  stage: "before" | "during" | "after";
  value: number | null;
  items: Record<string, boolean>;
  dropped: string[];
}

export interface TradeRow {
  cid: string;
  sessionId: string | null;
  symbol: string;
  side: "buy" | "sell";
  lots: number;
  timeframe: string | null;
  playbookId: string | null;
  playbookName: string | null;
  intent: "planned" | "impulsive" | "revenge" | "unknown";
  intentBy: string;
  rMultiple: number | null;
  closedAt: number;
  clean: boolean | null;
  scores: Record<string, StageScore>;
  hasTape: boolean;
}

export interface DayRow {
  sessionId: string;
  openedAt: number;
  score: number | null;
  trades: number;
  declined: number;
  mistakes: number;
  hasAnalysis: boolean;
  checkinPre: number | null;
  checkinPost: number | null;
}

export interface Consistency {
  value: number | null;
  n: number;
  mean: number | null;
  meanAbsoluteDeviation: number | null;
  reason: string | null;
}

export interface MistakeTrendRow {
  code: string;
  count: number;
  trades: number;
  auto: number;
  player: number;
}

export interface Overview {
  account: { broker: string; kind: string; readOnly: boolean };
  sessions: number;
  consistency: Consistency;
  processScoreMean: number | null;
  latestTrades: TradeRow[];
  groups: { groups: Record<string, number>; unclassified: number; note: string };
  mistakes: { mistakes: MistakeTrendRow[]; focus: string | null; note: string };
}

export interface ActualVsPlan {
  plannedR: number | null;
  realisedR: number | null;
  deltaR: number | null;
  plannedSl: number | null;
  plannedTp: number | null;
  amendments: { ts: number; sl?: number | null; tp?: number | null }[];
  worsenedStops: { ts: number; from: number; to: number }[];
  label: string;
}

export interface TradeDetailView {
  plan: Record<string, unknown> & { cid: string; symbol: string; side: string;
                                    playbookName: string | null; plannedSl: number | null;
                                    plannedTp: number | null };
  execution: { entry: number | null; exit: number | null; openedAt: number | null;
               closedAt: number; lots: number; rMultiple: number; rUsd: number;
               mfe: number | null; mae: number | null;
               events: { kind: string; ts: number; payload: Record<string, unknown> }[] };
  grade: { clean: boolean; requiredPass: number; requiredTotal: number;
           results: { code: string; label?: string; ok: boolean; unknown: boolean }[] } | null;
  actualVsPlan: ActualVsPlan;
  scores: Record<string, StageScore>;
  intent: { value: string; by: string };
  review: { note: string | null; earlyExit: boolean };
  mistakes: { code: string; source: string; note: string | null; ts: number }[];
  attachments: Attachment[];
  memos: unknown[];
  hasTape: boolean;
}

export interface MistakeDefinition {
  code: string;
  label: string;
  builtin: boolean;
  active: boolean;
  derivable: boolean;
}

export interface SizeAnswer {
  symbol: string;
  requestedLots: number | null;
  roundedLots: number | null;
  volume: number | null;
  riskUsd: number | null;
  actualRiskUsd: number | null;
  stopDistance: number | null;
  rate: number | null;
  rateChain: string | null;
  cappedAt: number | null;
  reason: string | null;
}

export interface SystemView {
  philosophy: string | null;
  principles: string[];
  focusCode: string | null;
  updatedAt: number | null;
}

/** A missing figure is a gap, never a zero — the journal's rule since phase 6. */
export function show(value: number | null | undefined, digits = 2): string {
  return value === null || value === undefined ? "—" : value.toFixed(digits);
}

export function r(value: number | null | undefined): string {
  return value === null || value === undefined
    ? "—"
    : `${value >= 0 ? "+" : ""}${value.toFixed(2)}R`;
}
