/**
 * The agent: a two-handed gesture becomes exactly one intent, and the safety exits never need
 * the pad.
 */

import { expect, it, vi } from "vitest";
import { GameAgent } from "./agent";
import type { AgentOptions } from "./agent";
import { isCid, newCid } from "./net/cid";
import type { GameClient } from "./net/ws";
import type { PadInput } from "./pad/fsm";
import type { RawFrame } from "./pad/poll";

function fakeClient() {
  const sent: { t: string; payload: Record<string, unknown>; cid?: string }[] = [];
  const heartbeats: unknown[] = [];
  const client = {
    pending: 0,
    sendIntent: (intent: { cid: string; t: string; payload: Record<string, unknown> }) =>
      sent.push({ t: intent.t, payload: intent.payload, cid: intent.cid }),
    send: (t: string, _ch: string, payload: Record<string, unknown>) => {
      sent.push({ t, payload });
      return {} as never;
    },
    setHeartbeat: (beat: unknown) => heartbeats.push(beat),
  } as unknown as GameClient;
  return { client, sent, heartbeats };
}

function frame(over: Partial<PadInput> = {}, bumpers = { lb: false, rb: false }): RawFrame {
  return {
    input: {
      clutch: 0, confirm: false, a: false, b: false, x: false, y: false,
      view: false, menu: false, lotUp: false, lotDown: false,
      symbolLeft: false, symbolRight: false,
      visible: true, padConnected: true, nowMs: 1000,
      ...over,
    },
    snapshot: {},
    sticks: { lsX: 0, lsY: 0, rsX: 0, rsY: 0 },
    bumpers,
  };
}

function agentAt(options: Partial<Omit<AgentOptions, "client" | "symbols">> = {}) {
  const { client, sent, heartbeats } = fakeClient();
  const agent = new GameAgent({ client, symbols: ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"], ...options });
  return { agent, client, sent, heartbeats };
}

it("turns a clutch-arm-confirm gesture into exactly one open intent", () => {
  const { agent, sent } = agentAt();
  agent.onFrame(frame({ view: true }));
  agent.onFrame(frame({ clutch: 0.9 }));
  agent.onFrame(frame({ clutch: 0.9, a: true }));
  agent.onFrame(frame({ clutch: 0.9, confirm: true }));

  const opens = sent.filter((f) => f.t === "intent.open");
  expect(opens).toHaveLength(1);
  expect(opens[0].payload).toMatchObject({
    sym: "XAUUSD", side: "buy", type: "market", lots: 0.01, clutch: true,
  });
  expect(isCid(opens[0].cid as string)).toBe(true);
});

it("gives every intent a distinct cid, even inside one millisecond", () => {
  const cids = new Set(Array.from({ length: 50 }, () => newCid(1_700_000_000_000)));
  expect(cids.size).toBe(50);
  expect([...cids].every(isCid)).toBe(true);
});

it("carries the dead-man flags on the heartbeat every frame", () => {
  const { agent, heartbeats } = agentAt();
  agent.onFrame(frame({ view: true }));
  agent.onFrame(frame({ clutch: 0.9 }));
  expect(heartbeats.at(-1)).toEqual({ visible: true, pad: true, clutch: true });

  agent.onAbsent({ ...frame().input, padConnected: false, visible: false });
  expect(heartbeats.at(-1)).toEqual({ visible: false, pad: false, clutch: false });
});

it("flattens without a pad, because a dead pad must never trap a position", () => {
  const { agent, sent } = agentAt();
  agent.onAbsent({ ...frame().input, padConnected: false });
  agent.flatten();

  const panics = sent.filter((f) => f.t === "intent.panic");
  expect(panics).toHaveLength(1);
  expect(panics[0].payload).toMatchObject({ clutch: true });
});

it("cycles symbol and lot without sending anything to the broker", () => {
  const { agent, sent } = agentAt();
  agent.onFrame(frame({ view: true }));
  agent.onFrame(frame({ symbolRight: true }));
  expect(agent.view.symbol).toBe("EURUSD");

  agent.onFrame(frame({ lotUp: true }));
  expect(agent.view.lots).toBe(0.02);
  expect(sent.filter((f) => f.t.startsWith("intent."))).toHaveLength(0);
});

it("wraps the symbol ring but clamps the lot ladder", () => {
  const { agent } = agentAt();
  agent.onFrame(frame({ view: true }));
  for (let i = 0; i < 4; i += 1) agent.onFrame(frame({ symbolRight: true }));
  expect(agent.view.symbol).toBe("XAUUSD");

  for (let i = 0; i < 10; i += 1) agent.onFrame(frame({ lotDown: true }));
  expect(agent.view.lots).toBe(0.01);
});

it("batches telemetry onto the socket at 1 Hz, not per frame", () => {
  vi.useFakeTimers();
  vi.setSystemTime(0);
  const { agent, sent } = agentAt();
  for (let i = 0; i < 120; i += 1) {
    vi.setSystemTime(i * 16);
    agent.onFrame(frame({ nowMs: i * 16 }));
  }
  const samples = sent.filter((f) => f.t === "pad.telemetry");
  expect(samples.length).toBeLessThanOrEqual(2);
  expect(samples.length).toBeGreaterThan(0);
  vi.useRealTimers();
});

it("counts a stand-down only when a condition was actually live", () => {
  const conditions: string[] = [];
  const { agent } = agentAt({ standDownConditions: () => conditions });
  agent.onFrame(frame({ view: true }));
  agent.onFrame(frame({ clutch: 0.9 }));
  agent.onFrame(frame({ clutch: 0.9, a: true }));

  agent.onFrame(frame({ clutch: 0 }));
  expect(agent.view.stoodDown).toBe(0);

  conditions.push("spread_wide");
  agent.onFrame(frame({ clutch: 0.9 }));
  agent.onFrame(frame({ clutch: 0.9, a: true }));
  agent.onFrame(frame({ clutch: 0 }));
  expect(agent.view.stoodDown).toBe(1);
});

it("does not count an unplug as a stand-down", () => {
  const { agent } = agentAt({ standDownConditions: () => ["spread_wide"] });
  agent.onFrame(frame({ view: true }));
  agent.onFrame(frame({ clutch: 0.9 }));
  agent.onFrame(frame({ clutch: 0.9, a: true }));
  agent.onAbsent({ ...frame().input, padConnected: false });
  expect(agent.view.stoodDown).toBe(0);
});

it("changes the timeframe on a single bumper release and not on the chord", () => {
  const { agent } = agentAt();
  agent.onFrame(frame({ view: true }));
  agent.onFrame(frame({ nowMs: 1000 }, { lb: false, rb: true }));
  agent.onFrame(frame({ nowMs: 1100 }, { lb: false, rb: false }));
  expect(agent.view.timeframe).toBe("M15");

  agent.onFrame(frame({ nowMs: 2000 }, { lb: true, rb: true }));
  agent.onFrame(frame({ nowMs: 2300 }, { lb: false, rb: false }));
  expect(agent.view.timeframe).toBe("M15");
});

it("clears the arm and stays quiet when the socket drops mid-fire", () => {
  const { agent, sent } = agentAt();
  agent.onFrame(frame({ view: true }));
  agent.onFrame(frame({ clutch: 0.9 }));
  agent.onFrame(frame({ clutch: 0.9, a: true }));
  agent.onFrame(frame({ clutch: 0.9, confirm: true }));
  const before = sent.length;

  agent.onSocketClosed();
  expect(agent.view.phase).toBe("UNKNOWN");
  expect(sent).toHaveLength(before);
});

it("returns to idle once the gateway answers", () => {
  const { agent } = agentAt();
  agent.onFrame(frame({ view: true }));
  agent.onFrame(frame({ clutch: 0.9 }));
  agent.onFrame(frame({ clutch: 0.9, a: true }));
  agent.onFrame(frame({ clutch: 0.9, confirm: true }));

  agent.onMessage({ v: 1, t: "order.ack", seq: 1, ts: 1, ch: "orders", cid: "x",
                    p: { positionId: 9 } });
  expect(agent.view.phase).toBe("IDLE");
});

it("closes the position the gateway last reported, and nothing when there is none", () => {
  const { agent, sent } = agentAt();
  agent.closePosition();
  expect(sent).toHaveLength(0);

  agent.onMessage({ v: 1, t: "pos.snap", seq: 1, ts: 1, ch: "orders",
                    p: { positions: [{ positionId: 42 }] } });
  agent.closePosition();
  expect(sent.at(-1)?.payload).toMatchObject({ positionId: 42, clutch: true });
});

it("never requests a microphone in phase 3", async () => {
  const source = await import("./agent");
  expect(String(Object.values(source).map(String).join(""))).not.toMatch(
    /getUserMedia|MediaRecorder/,
  );
});
