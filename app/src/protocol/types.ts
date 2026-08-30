// GENERATED FILE -- do not edit.
// Source: apps/gateway/protocol/catalog.py
// Regenerate: uv run python -m apps.gateway.protocol.export_schema
//             && node scripts/gen-protocol-types.mjs

export const PROTOCOL_VERSION = 1;
export const MAX_FRAME_BYTES = 65536;
export type Channel = "quotes" | "orders" | "session" | "ai" | "voice";

export interface Envelope<T extends string, P> {
  v: typeof PROTOCOL_VERSION;
  t: T;
  seq: number;
  /** Unix milliseconds, sender clock. */
  ts: number;
  ch: Channel;
  /** ULID. Required on every intent. */
  cid?: string | null;
  p: P;
}

export interface AiAdvice {
  disabled?: boolean;
  kind: "research" | "plan" | "advise" | "news" | "coach";
  text?: string;
  ts: number;
}
export interface AiAsk {
  kind: "research" | "plan" | "advise" | "news" | "coach";
  sym?: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY" | null;
  tf?: "M1" | "M5" | "M15" | "H1" | "H4" | "D1" | null;
}
export interface Candle {
  c: number;
  closed?: boolean;
  h: number;
  l: number;
  o: number;
  sym: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY";
  tf: "M1" | "M5" | "M15" | "H1" | "H4" | "D1";
  ts: number;
}
export interface ErrorMsg {
  detail?: string | null;
  reason: string;
}
export interface GradeAnswer {
  answer: boolean;
  cid: string;
  ruleId: string;
}
export interface GradeMsg {
  cid: string;
  clean?: boolean;
  playbookId: string;
  required_pass?: number;
  required_total?: number;
  results?: GradeResult[];
}
export interface GradeResult {
  note?: string | null;
  passed?: boolean | null;
  required: boolean;
  ruleId: string;
}
export interface Hello {
  lastSeq?: number;
  protocolVersion?: number;
  token: string;
  ua?: string | null;
}
export interface IntentClose {
  /** Unix ms the pad entered ARM */
  armedAt: number;
  clutch: true;
  positionId: number;
}
export interface IntentModify {
  /** Unix ms the pad entered ARM */
  armedAt: number;
  clutch: true;
  positionId: number;
  sl?: number | null;
  tp?: number | null;
}
export interface IntentOpen {
  /** Unix ms the pad entered ARM */
  armedAt: number;
  clutch: true;
  lots: number;
  relativeSl?: number | null;
  relativeTp?: number | null;
  side: "buy" | "sell";
  sym: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY";
  type?: "market";
}
export interface IntentPanic {
  /** Unix ms the pad entered ARM */
  armedAt: number;
  clutch: true;
}
export interface JournalMemoLink {
  cid: string;
  voiceId: string;
}
export interface Maint {
  detail?: string | null;
  reason: string;
  until?: number | null;
}
export interface NewsItem {
  currency: string;
  id: string;
  impact: "low" | "medium" | "high";
  sym?: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY" | null;
  title: string;
  ts: number;
}
export interface OrderAck {
  cid: string;
  lots: number;
  orderId?: number | null;
  positionId?: number | null;
  price: number;
  side: "buy" | "sell";
  sym: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY";
  ts: number;
}
export interface OrderReject {
  cid?: string | null;
  detail?: string | null;
  reason: "not_wired" | "no_clutch" | "stale_arm" | "duplicate_cid" | "locked" | "session_closed" | "dead_man" | "max_positions" | "max_daily_loss" | "max_lots" | "lot_step" | "unknown_symbol" | "spread_too_wide" | "rate_limited" | "cooldown" | "broker_error" | "broker_down";
}
export interface OrderUpd {
  cid?: string | null;
  detail?: string | null;
  orderId?: number | null;
  positionId?: number | null;
  status: "filled" | "closed" | "amended" | "cancelled" | "expired";
  ts: number;
}
export interface PadTelemetry {
  armFlips?: number;
  armMs?: number;
  btnRateHz?: number;
  clutchCycles?: number;
  clutchMs?: number;
  from?: string | null;
  lotStepsSince?: number;
  lots?: number | null;
  reason?: string | null;
  sym?: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY" | null;
  to?: string | null;
  ts: number;
  ttfMs?: number | null;
}
export interface Ping {
  clutch?: boolean;
  padSeq?: number | null;
}
export interface PlaybookList {
  playbooks?: PlaybookSummary[];
}
export interface PlaybookSelect {
  playbookId: string;
}
export interface PlaybookSummary {
  name: string;
  playbookId: string;
  requiredCount: number;
  ruleCount: number;
}
export interface Pnl {
  balance: number;
  dayPnl?: number;
  equity: number;
  openPnl?: number;
  ts: number;
}
export interface Pong {
  clutch?: boolean;
  serverTs: number;
}
export interface Position {
  entry: number;
  lots: number;
  openedAt: number;
  pnl?: number;
  positionId: number;
  rMultiple?: number | null;
  side: "buy" | "sell";
  sl?: number | null;
  sym: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY";
  tp?: number | null;
}
export interface PosSnap {
  positions?: Position[];
  ts: number;
}
export interface Quote {
  ask: number;
  bid: number;
  digits: number;
  sym: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY";
  ts: number;
}
export interface Resync {
  fromSeq: number;
}
export interface RiskState {
  dayLossUsd?: number;
  locked: boolean;
  maxDailyLossUsd?: number;
  maxPositions?: number;
  positions?: number;
  reasons?: "not_wired" | "no_clutch" | "stale_arm" | "duplicate_cid" | "locked" | "session_closed" | "dead_man" | "max_positions" | "max_daily_loss" | "max_lots" | "lot_step" | "unknown_symbol" | "spread_too_wide" | "rate_limited" | "cooldown" | "broker_error" | "broker_down"[];
}
export interface ScoreSession {
  axes?: Record<string, number>;
  na?: string[];
  total?: number;
  weightsVersion?: string;
}
export interface SentinelTick {
  band: "green" | "amber" | "red";
  newsOk: boolean;
  sessionOk: boolean;
  spread: number;
  spreadOk: boolean;
  sym: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY";
  ts: number;
}
export interface SessionLock {

}
export interface SessionState {
  endsAt?: number | null;
  opensAllowed: boolean;
  reason?: string | null;
  startsAt?: number | null;
  state: "closed" | "open" | "locked" | "cooldown";
  tz: string;
}
export interface SessionUnlock {

}
export interface SignalItem {
  id: string;
  source?: "tradingview";
  sym: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY";
  text: string;
  tf?: "M1" | "M5" | "M15" | "H1" | "H4" | "D1" | null;
  ts: number;
}
export interface Snap {
  what?: "pos" | "pnl" | "session" | "risk" | "playbook" | "tilt"[];
}
export interface Sub {
  ch: "quotes" | "orders" | "session" | "ai" | "voice";
  syms?: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY"[];
  tf?: "M1" | "M5" | "M15" | "H1" | "H4" | "D1" | null;
}
export interface TiltMsg {
  band: "cool" | "warm" | "hot" | "scorched";
  cooldownUntil?: number | null;
  score: number;
  top?: string[];
}
export interface VoiceBegin {
  cid?: string | null;
  voiceId: string;
}
export interface VoiceCancel {
  voiceId: string;
}
export interface VoiceStateMsg {
  busy?: boolean;
  queued?: number;
}
export interface VoiceTranscript {
  cid?: string | null;
  durMs?: number;
  ok: boolean;
  reason?: string | null;
  sttMs?: number;
  text?: string | null;
  voiceId: string;
}
export interface Welcome {
  features?: Record<string, boolean>;
  protocolVersion?: number;
  resumed?: boolean;
  seq: number;
  serverTs: number;
  sessionId: string;
  symbols: "XAUUSD" | "EURUSD" | "GBPUSD" | "USDJPY"[];
  tz: string;
}

export interface ClientMessages {
  "ai.ask": AiAsk;
  "grade.answer": GradeAnswer;
  "hello": Hello;
  "intent.close": IntentClose;
  "intent.modify": IntentModify;
  "intent.open": IntentOpen;
  "intent.panic": IntentPanic;
  "journal.memo.link": JournalMemoLink;
  "pad.telemetry": PadTelemetry;
  "ping": Ping;
  "playbook.select": PlaybookSelect;
  "resync": Resync;
  "session.lock": SessionLock;
  "session.unlock": SessionUnlock;
  "snap": Snap;
  "sub": Sub;
  "voice.begin": VoiceBegin;
  "voice.cancel": VoiceCancel;
}

export interface ServerMessages {
  "ai.advice": AiAdvice;
  "candle": Candle;
  "error": ErrorMsg;
  "grade": GradeMsg;
  "maint": Maint;
  "news.item": NewsItem;
  "order.ack": OrderAck;
  "order.reject": OrderReject;
  "order.upd": OrderUpd;
  "playbook.list": PlaybookList;
  "pnl": Pnl;
  "pong": Pong;
  "pos.snap": PosSnap;
  "quote": Quote;
  "risk": RiskState;
  "score.session": ScoreSession;
  "sentinel.tick": SentinelTick;
  "session": SessionState;
  "signal.item": SignalItem;
  "tilt": TiltMsg;
  "voice.state": VoiceStateMsg;
  "voice.transcript": VoiceTranscript;
  "welcome": Welcome;
}

export type ClientFrame = {
  [T in keyof ClientMessages & string]: Envelope<T, ClientMessages[T]>;
}[keyof ClientMessages & string];

export type ServerFrame = {
  [T in keyof ServerMessages & string]: Envelope<T, ServerMessages[T]>;
}[keyof ServerMessages & string];

export const CHANNEL_OF: Record<string, Channel> = {
  "ai.advice": "ai",
  "ai.ask": "ai",
  "candle": "quotes",
  "error": "session",
  "grade": "session",
  "grade.answer": "session",
  "hello": "session",
  "intent.close": "orders",
  "intent.modify": "orders",
  "intent.open": "orders",
  "intent.panic": "orders",
  "journal.memo.link": "voice",
  "maint": "session",
  "news.item": "ai",
  "order.ack": "orders",
  "order.reject": "orders",
  "order.upd": "orders",
  "pad.telemetry": "session",
  "ping": "session",
  "playbook.list": "session",
  "playbook.select": "session",
  "pnl": "orders",
  "pong": "session",
  "pos.snap": "orders",
  "quote": "quotes",
  "resync": "session",
  "risk": "session",
  "score.session": "session",
  "sentinel.tick": "ai",
  "session": "session",
  "session.lock": "session",
  "session.unlock": "session",
  "signal.item": "ai",
  "snap": "session",
  "sub": "session",
  "tilt": "session",
  "voice.begin": "voice",
  "voice.cancel": "voice",
  "voice.state": "voice",
  "voice.transcript": "voice",
  "welcome": "session",
};
