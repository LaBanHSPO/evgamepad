/**
 * The socket client.
 *
 * Three rules carry most of the weight:
 *
 *  - **A reconnect does not mint a new cid.** An unacked fire keeps its cid
 *    across `onclose`, so a retry collides with the gateway's cid ledger
 *    instead of opening a second position.
 *  - **A FIRE timeout is `unknown`, not `failed`.** New fires are blocked until
 *    the cid resolves, because the order may well have reached the broker.
 *  - **A protocol version we do not recognise is fatal.** The HUD refuses to
 *    run rather than mis-read a frame about money.
 *
 * The token lives in memory for this session only. Never `localStorage`, never
 * a `VITE_*` build-time constant -- both would put a trading credential
 * somewhere it outlives the evening.
 */

import { PROTOCOL_VERSION, type ServerFrame } from "../protocol/types";

export type ConnState = "idle" | "connecting" | "open" | "closed" | "refused";

export type PendingFire = {
  cid: string;
  sentAt: number;
  kind: "open" | "close" | "modify" | "panic";
};

export const FIRE_TIMEOUT_MS = 8000;

export type ClientFlags = { visible: boolean; pad: boolean; clutch: boolean };

export type GatewayEvents = {
  onFrame?: (frame: ServerFrame) => void;
  onState?: (state: ConnState, detail?: string) => void;
  /** A fire whose cid never resolved. New fires stay blocked until cleared. */
  onUnknown?: (pending: PendingFire) => void;
};

/** Crockford base32, matching the gateway's ULID. */
const B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";

export function newCid(now = Date.now(), random = Math.random): string {
  let time = now;
  const chars = new Array<string>(26);
  for (let i = 9; i >= 0; i -= 1) {
    chars[i] = B32[time % 32]!;
    time = Math.floor(time / 32);
  }
  for (let i = 10; i < 26; i += 1) chars[i] = B32[Math.floor(random() * 32)]!;
  return chars.join("");
}

export class Gateway {
  private ws: WebSocket | null = null;
  /**
   * A true `#private` field, not a TypeScript `private` one: TS privacy is
   * erased at runtime, so a `private token` still shows up in
   * `JSON.stringify`, an error report, or React devtools. A trading credential
   * must not be one accidental serialisation away from a log.
   */
  #token = "";
  private seq = 0;
  private outSeq = 0;
  private retry = 0;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private closedByUs = false;

  state: ConnState = "idle";
  flags: ClientFlags = { visible: true, pad: false, clutch: false };
  /** Unresolved fires, keyed by cid. Survives a reconnect on purpose. */
  pending = new Map<string, PendingFire>();

  constructor(
    private url: string,
    private events: GatewayEvents = {},
  ) {}

  /** Paste-once, memory-only. */
  setToken(token: string): void {
    this.#token = token;
  }

  get hasToken(): boolean {
    return this.#token.length > 0;
  }

  get blocked(): boolean {
    return this.pending.size > 0;
  }

  connect(): void {
    if (!this.#token) {
      this.setState("refused", "no token");
      return;
    }
    this.closedByUs = false;
    this.setState("connecting");
    const ws = new WebSocket(this.url);
    this.ws = ws;

    ws.onopen = () => {
      this.retry = 0;
      this.setState("open");
      this.send("hello", "session", { token: this.#token, lastSeq: this.seq, protocolVersion: PROTOCOL_VERSION });
      this.send("sub", "session", { ch: "quotes", syms: [] });
      this.resendPending();
    };

    ws.onmessage = (event) => this.receive(event.data as string);

    ws.onclose = () => {
      this.ws = null;
      // LOCKED, but the unacked cid is kept. Minting a new one on reconnect is
      // exactly how a retry becomes a second position.
      this.setState("closed");
      if (!this.closedByUs) this.scheduleReconnect();
    };

    ws.onerror = () => this.setState("closed", "socket error");
  }

  disconnect(): void {
    this.closedByUs = true;
    if (this.timer) clearTimeout(this.timer);
    this.ws?.close();
    this.ws = null;
  }

  private scheduleReconnect(): void {
    this.retry = Math.min(this.retry + 1, 6);
    const delay = Math.min(500 * 2 ** (this.retry - 1), 15000);
    this.timer = setTimeout(() => this.connect(), delay);
  }

  private setState(state: ConnState, detail?: string): void {
    this.state = state;
    this.events.onState?.(state, detail);
  }

  private receive(raw: string): void {
    let frame: ServerFrame;
    try {
      frame = JSON.parse(raw) as ServerFrame;
    } catch {
      return;
    }

    if (frame.v !== PROTOCOL_VERSION) {
      // A frame we cannot read is about money. Refuse rather than guess.
      this.setState("refused", `protocol v${frame.v}, this build speaks v${PROTOCOL_VERSION}`);
      this.disconnect();
      return;
    }

    // A gap means frames were lost. Ask for them before acting on this one.
    if (frame.seq > this.seq + 1 && this.seq > 0) {
      this.send("resync", "session", { fromSeq: this.seq });
    }
    this.seq = Math.max(this.seq, frame.seq);

    if (frame.t === "order.ack" || frame.t === "order.reject") {
      const cid = frame.cid ?? (frame.p as { cid?: string }).cid;
      if (cid) this.pending.delete(cid);
    }

    this.events.onFrame?.(frame);
  }

  private raw(payload: unknown): void {
    if (this.ws?.readyState !== WebSocket.OPEN) return;
    this.ws.send(JSON.stringify(payload));
  }

  send(t: string, ch: string, p: unknown, cid?: string): void {
    this.outSeq += 1;
    this.raw({ v: PROTOCOL_VERSION, t, seq: this.outSeq, ts: Date.now(), ch, cid: cid ?? null, p });
  }

  /**
   * The dead-man heartbeat. `clutch` here is liveness evidence only -- a fire is
   * authorised by the clutch on the intent itself, so a press 50 ms after
   * clutch-down is not refused by a stale ping.
   */
  ping(): void {
    this.send("ping", "session", { clutch: this.flags.clutch });
  }

  telemetry(batch: unknown): void {
    this.send("pad.telemetry", "session", batch);
  }

  /**
   * Send an intent, remembering its cid until the gateway resolves it.
   * Returns the cid so the HUD can show what is in flight.
   */
  fire(
    kind: PendingFire["kind"],
    payload: Record<string, unknown>,
    cid = newCid(),
  ): string {
    this.pending.set(cid, { cid, sentAt: Date.now(), kind });
    this.send(`intent.${kind}`, "orders", { ...payload, clutch: true }, cid);
    return cid;
  }

  /** Re-send nothing, but re-assert what is outstanding after a reconnect. */
  private resendPending(): void {
    for (const p of this.pending.values()) this.events.onUnknown?.(p);
  }

  /**
   * Sweep for fires that never resolved. Called on a timer; each one keeps the
   * fire path blocked until the player or a later ack clears it.
   */
  sweepTimeouts(now = Date.now(), timeoutMs = FIRE_TIMEOUT_MS): PendingFire[] {
    const stale: PendingFire[] = [];
    for (const p of this.pending.values()) {
      if (now - p.sentAt > timeoutMs) stale.push(p);
    }
    for (const p of stale) this.events.onUnknown?.(p);
    return stale;
  }

  /** Explicit operator acknowledgement that an unknown fire has been resolved. */
  clearPending(cid: string): void {
    this.pending.delete(cid);
  }
}
