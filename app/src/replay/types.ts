/** Shapes served by `GET /api/replay/*`. Prices are scaled integers; divide once, when drawing. */

export type EventKind =
  | "arm"
  | "cancel"
  | "fire"
  | "ack"
  | "sl_move"
  | "memo"
  | "volman_tag"
  | "tv_signal"
  | "tilt_band_change";

export interface ReplayEvent {
  ts: number;
  kind: EventKind | string;
  label: string;
  price?: number | null;
  band?: string;
}

/** Columnar because the client reads whole series; 600 JSON objects would be ~3x the bytes. */
export interface Tape {
  fromTs: number;
  toTs: number;
  dtS: number;
  n: number;
  mfe: number | null;
  mae: number | null;
  ts: number[];
  bidO: number[];
  bidH: number[];
  bidL: number[];
  bidC: number[];
  askO: number[];
  askH: number[];
  askL: number[];
  askC: number[];
  nTicks: number[];
  version: number;
}

export interface ReplayTrade {
  cid: string;
  sessionId: string | null;
  positionId: number;
  symbol: string;
  side: "buy" | "sell";
  lots: number;
  entry: number | null;
  exit: number | null;
  openedAt: number | null;
  closedAt: number;
  netPnlUsd: number | null;
  rUsd: number;
  rMultiple: number;
  mfe: number | null;
  mae: number | null;
  adherence: number | null;
  tiltAtEntry: number | null;
  plannedSl?: number | null;
  timeframe?: string | null;
  playbookId?: string | null;
  armedAt?: number | null;
}

export interface ReplayGrade {
  playbookId: string | null;
  stage: string;
  results: {
    code: string;
    label: string;
    kind: "auto" | "manual";
    required: boolean;
    ok: boolean;
    unknown: boolean;
    actual: string | null;
    expected: string | null;
  }[];
  requiredPass: number;
  requiredTotal: number;
  clean: boolean;
}

/** Phase 8 fills `memos`. An empty array is what "no memo" looks like — not an error. */
export interface Memo {
  id: string;
  ts: number;
  durMs: number;
  transcript: string | null;
}

export interface ReplayBody {
  trade: ReplayTrade;
  grade: ReplayGrade | null;
  tape: Tape | null;
  events: ReplayEvent[];
  memos: Memo[];
  scale: number;
}

export interface IndexRow {
  cid: string;
  sessionId: string | null;
  symbol: string;
  side: "buy" | "sell";
  lots: number;
  openedAt: number | null;
  closedAt: number;
  rMultiple: number;
  netPnlUsd: number | null;
  clean: boolean | null;
  hasTape: boolean;
}
