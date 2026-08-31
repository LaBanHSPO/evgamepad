/**
 * The game socket client.
 *
 * Three rules shape this file. The token lives in **memory for the session** — never
 * `localStorage`, never a `VITE_*` constant baked at compile time, because anything baked into
 * the bundle is readable by anyone who opens it. A dropped socket **keeps its outstanding cid**
 * rather than minting a new one, so a reconnect can never turn one intent into two positions.
 * And a protocol version the HUD does not recognise stops the client dead: a stale HUD guessing
 * at a new envelope is worse than a HUD that refuses to run.
 */

import { MAX_FRAME_BYTES, PROTOCOL_VERSION } from "../protocol/types";
import type { Channel, Envelope, MessageType } from "../protocol/types";

const PING_INTERVAL_MS = 1000;
const RECONNECT_BACKOFF_MS = [500, 1000, 2000, 5000, 10000];

export interface Heartbeat {
  visible: boolean;
  pad: boolean;
  clutch: boolean;
}

export interface PendingIntent {
  cid: string;
  t: MessageType;
  ch: Channel;
  payload: Record<string, unknown>;
}

export type SocketStatus = "connecting" | "open" | "closed" | "refused";

export interface SocketHooks {
  onMessage: (envelope: Envelope) => void;
  onStatus: (status: SocketStatus) => void;
  /** Fired when the gateway speaks a protocol this bundle does not know. Fatal by design. */
  onProtocolMismatch?: (theirs: number) => void;
}

export interface SocketLike {
  send(data: string): void;
  close(): void;
  onopen: ((event: unknown) => void) | null;
  onclose: ((event: unknown) => void) | null;
  onmessage: ((event: { data: string }) => void) | null;
  onerror: ((event: unknown) => void) | null;
}

export type SocketFactory = (url: string) => SocketLike;

export class GameClient {
  private socket: SocketLike | null = null;
  private seq = 0;
  private lastServerSeq = 0;
  private attempts = 0;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private heartbeat: Heartbeat = { visible: true, pad: false, clutch: false };
  /** Intents sent but not yet answered, keyed by cid. Survives a reconnect intact. */
  private outstanding = new Map<string, PendingIntent>();
  private closedByUs = false;

  constructor(
    private url: string,
    private token: string,
    private hooks: SocketHooks,
    private factory: SocketFactory = (url) => new WebSocket(url) as unknown as SocketLike,
  ) {}

  connect(): void {
    this.closedByUs = false;
    this.hooks.onStatus("connecting");
    // The token rides the query string of a same-origin socket; it is never persisted anywhere.
    const socket = this.factory(`${this.url}?token=${encodeURIComponent(this.token)}`);
    this.socket = socket;

    socket.onopen = () => {
      this.attempts = 0;
      this.hooks.onStatus("open");
      this.send("hello", "session", {
        token: this.token,
        lastSeq: this.lastServerSeq || undefined,
      });
      // Replay outstanding intents under their original cids. The gateway's ledger collapses the
      // duplicates, so a replay costs nothing; minting new cids would cost a second position.
      for (const pending of this.outstanding.values()) {
        this.send(pending.t, pending.ch, pending.payload, pending.cid);
      }
      this.startPing();
    };

    socket.onmessage = (event) => this.receive(event.data);
    socket.onclose = () => {
      this.stopPing();
      this.hooks.onStatus("closed");
      if (!this.closedByUs) this.scheduleReconnect();
    };
    socket.onerror = () => socket.close();
  }

  disconnect(): void {
    this.closedByUs = true;
    this.stopPing();
    this.socket?.close();
    this.socket = null;
  }

  setHeartbeat(heartbeat: Heartbeat): void {
    this.heartbeat = heartbeat;
  }

  private startPing(): void {
    this.stopPing();
    this.pingTimer = setInterval(() => {
      this.send("ping", "session", { ...this.heartbeat });
    }, PING_INTERVAL_MS);
  }

  private stopPing(): void {
    if (this.pingTimer !== null) clearInterval(this.pingTimer);
    this.pingTimer = null;
  }

  private scheduleReconnect(): void {
    const delay = RECONNECT_BACKOFF_MS[Math.min(this.attempts, RECONNECT_BACKOFF_MS.length - 1)];
    this.attempts += 1;
    setTimeout(() => this.connect(), delay);
  }

  /** Send one frame. Returns the envelope actually written, for tests and for the journal. */
  send(
    t: MessageType | string,
    ch: Channel,
    payload: Record<string, unknown>,
    cid?: string,
  ): Envelope {
    this.seq += 1;
    const envelope: Envelope = {
      v: PROTOCOL_VERSION,
      t,
      seq: this.seq,
      ts: Date.now(),
      ch,
      ...(cid ? { cid } : {}),
      p: payload,
    };
    const raw = JSON.stringify(envelope);
    if (raw.length > MAX_FRAME_BYTES) {
      throw new Error(`frame ${raw.length}B exceeds the ${MAX_FRAME_BYTES}B cap (t=${t})`);
    }
    this.socket?.send(raw);
    return envelope;
  }

  /** Send an intent and remember it until the gateway answers for that cid. */
  sendIntent(intent: PendingIntent): void {
    this.outstanding.set(intent.cid, intent);
    this.send(intent.t, intent.ch, intent.payload, intent.cid);
  }

  /** How many intents are still unanswered. A non-zero count blocks a new open in the HUD. */
  get pending(): number {
    return this.outstanding.size;
  }

  private receive(raw: string): void {
    let envelope: Envelope;
    try {
      envelope = JSON.parse(raw) as Envelope;
    } catch {
      return;
    }

    if (envelope.v !== undefined && envelope.v !== PROTOCOL_VERSION) {
      // A HUD that guesses at an unknown envelope is worse than one that stops.
      this.hooks.onProtocolMismatch?.(envelope.v);
      this.hooks.onStatus("refused");
      this.disconnect();
      return;
    }

    if (envelope.seq > this.lastServerSeq + 1 && this.lastServerSeq > 0) {
      // A gap means frames were missed; ask for them rather than rendering a hole.
      this.send("resync", "session", { lastSeq: this.lastServerSeq });
    }
    this.lastServerSeq = Math.max(this.lastServerSeq, envelope.seq);

    if (
      envelope.cid &&
      (envelope.t === "order.ack" || envelope.t === "order.reject" || envelope.t === "order.upd")
    ) {
      this.outstanding.delete(envelope.cid);
    }

    this.hooks.onMessage(envelope);
  }
}
