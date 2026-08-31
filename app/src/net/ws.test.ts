/** The socket client: memory-only token, cid survival across a reconnect, version refusal. */

import { expect, it, vi } from "vitest";
import type { SocketLike } from "./ws";
import { GameClient } from "./ws";

class FakeSocket implements SocketLike {
  sent: string[] = [];
  closed = false;
  onopen: ((e: unknown) => void) | null = null;
  onclose: ((e: unknown) => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onerror: ((e: unknown) => void) | null = null;

  send(data: string): void {
    this.sent.push(data);
  }

  close(): void {
    this.closed = true;
    this.onclose?.(null);
  }

  frames(): Record<string, any>[] {
    return this.sent.map((raw) => JSON.parse(raw));
  }

  deliver(envelope: Record<string, unknown>): void {
    this.onmessage?.({ data: JSON.stringify(envelope) });
  }
}

function harness() {
  const sockets: FakeSocket[] = [];
  const onMessage = vi.fn();
  const onStatus = vi.fn();
  const onProtocolMismatch = vi.fn();
  const game = new GameClient(
    "/ws",
    "tok",
    { onMessage, onStatus, onProtocolMismatch },
    () => {
      const socket = new FakeSocket();
      sockets.push(socket);
      return socket;
    },
  );
  return { game, sockets, onMessage, onStatus, onProtocolMismatch };
}

it("says hello with the token and keeps no persisted copy of it", () => {
  const { game, sockets } = harness();
  game.connect();
  sockets[0].onopen?.(null);

  const hello = sockets[0].frames()[0];
  expect(hello.t).toBe("hello");
  expect(hello.p.token).toBe("tok");
  // Nothing in this module reaches storage; the token exists only for this session.
  expect(String(GameClient)).not.toMatch(/localStorage|sessionStorage/);
});

it("replays an outstanding intent under its original cid after a reconnect", () => {
  const { game, sockets } = harness();
  game.connect();
  sockets[0].onopen?.(null);
  game.sendIntent({
    cid: "01ABC",
    t: "intent.open",
    ch: "orders",
    payload: { sym: "XAUUSD", side: "buy", lots: 0.01, clutch: true, armedAt: 1 },
  });
  expect(game.pending).toBe(1);

  sockets[0].onclose?.(null);
  game.connect();
  sockets[1].onopen?.(null);

  const replayed = sockets[1].frames().filter((f) => f.t === "intent.open");
  expect(replayed).toHaveLength(1);
  expect(replayed[0].cid).toBe("01ABC");
});

it("forgets an intent once the gateway answers for that cid", () => {
  const { game, sockets } = harness();
  game.connect();
  sockets[0].onopen?.(null);
  game.sendIntent({ cid: "01ABC", t: "intent.open", ch: "orders", payload: {} });

  sockets[0].deliver({ v: 1, t: "order.ack", seq: 1, ts: 1, ch: "orders", cid: "01ABC", p: {} });
  expect(game.pending).toBe(0);
});

it("does not let a rejected intent linger either", () => {
  const { game, sockets } = harness();
  game.connect();
  sockets[0].onopen?.(null);
  game.sendIntent({ cid: "01ABC", t: "intent.open", ch: "orders", payload: {} });
  sockets[0].deliver({
    v: 1, t: "order.reject", seq: 1, ts: 1, ch: "orders", cid: "01ABC",
    p: { reason: "daily_loss" },
  });
  expect(game.pending).toBe(0);
});

it("asks for a resync when the server sequence skips", () => {
  const { game, sockets } = harness();
  game.connect();
  sockets[0].onopen?.(null);
  sockets[0].deliver({ v: 1, t: "quote", seq: 1, ts: 1, ch: "quotes", p: {} });
  sockets[0].sent = [];
  sockets[0].deliver({ v: 1, t: "quote", seq: 5, ts: 1, ch: "quotes", p: {} });

  const resync = sockets[0].frames().find((f) => f.t === "resync");
  expect(resync).toBeDefined();
  expect(resync?.p.lastSeq).toBe(1);
});

it("refuses a protocol version it does not recognise instead of guessing", () => {
  const { game, sockets, onProtocolMismatch, onStatus } = harness();
  game.connect();
  sockets[0].onopen?.(null);
  sockets[0].deliver({ v: 99, t: "welcome", seq: 1, ts: 1, ch: "session", p: {} });

  expect(onProtocolMismatch).toHaveBeenCalledWith(99);
  expect(onStatus).toHaveBeenCalledWith("refused");
  expect(sockets[0].closed).toBe(true);
});

it("refuses to write a frame past the protocol cap", () => {
  const { game, sockets } = harness();
  game.connect();
  sockets[0].onopen?.(null);
  expect(() => game.send("ai.ask", "ai", { kind: "advise", text: "x".repeat(70_000) })).toThrow(
    /exceeds/,
  );
});

it("carries the dead-man flags on every heartbeat", () => {
  vi.useFakeTimers();
  const { game, sockets } = harness();
  game.connect();
  sockets[0].onopen?.(null);
  game.setHeartbeat({ visible: false, pad: true, clutch: false });
  vi.advanceTimersByTime(1000);

  const ping = sockets[0].frames().find((f) => f.t === "ping");
  expect(ping?.p).toEqual({ visible: false, pad: true, clutch: false });
  vi.useRealTimers();
});

it("stops pinging once we close the socket ourselves", () => {
  vi.useFakeTimers();
  const { game, sockets } = harness();
  game.connect();
  sockets[0].onopen?.(null);
  vi.advanceTimersByTime(1000);
  const before = sockets[0].frames().filter((f) => f.t === "ping").length;

  game.disconnect();
  vi.advanceTimersByTime(5000);
  const after = sockets[0].frames().filter((f) => f.t === "ping").length;
  expect(after).toBe(before);
  vi.useRealTimers();
});
