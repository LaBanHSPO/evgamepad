import { describe, expect, it } from "vitest";
import { CHANNEL_OF } from "../protocol/types";
import { FIRE_TIMEOUT_MS, Gateway, newCid, type PendingFire } from "./ws";

describe("cid", () => {
  it("is a 26-char Crockford ULID the gateway will accept", () => {
    const cid = newCid();
    expect(cid).toMatch(/^[0-9A-HJKMNP-TV-Z]{26}$/);
  });

  it("is monotonic in its time prefix", () => {
    const a = newCid(1_700_000_000_000);
    const b = newCid(1_700_000_001_000);
    expect(a.slice(0, 10) < b.slice(0, 10)).toBe(true);
  });
});

describe("unresolved fires", () => {
  function gatewayWithPending(): { gw: Gateway; unknown: PendingFire[] } {
    const unknown: PendingFire[] = [];
    const gw = new Gateway("ws://localhost/ws", { onUnknown: (p) => unknown.push(p) });
    gw.pending.set("01ABC", { cid: "01ABC", sentAt: 0, kind: "open" });
    return { gw, unknown };
  }

  it("block further fires until they resolve", () => {
    const { gw } = gatewayWithPending();
    expect(gw.blocked).toBe(true);
    gw.clearPending("01ABC");
    expect(gw.blocked).toBe(false);
  });

  it("a timeout reports unknown rather than failed", () => {
    const { gw, unknown } = gatewayWithPending();
    const stale = gw.sweepTimeouts(FIRE_TIMEOUT_MS + 1);
    expect(stale).toHaveLength(1);
    expect(unknown).toHaveLength(1);
    // Still pending: the order may well have reached the broker, so it is not
    // silently dropped.
    expect(gw.blocked).toBe(true);
  });

  it("survive a reconnect with the same cid", () => {
    const { gw } = gatewayWithPending();
    const before = [...gw.pending.keys()];
    // A close does not mint a new cid, which is what stops a retry from
    // becoming a second position.
    gw.disconnect();
    expect([...gw.pending.keys()]).toEqual(before);
  });
});

describe("token handling", () => {
  it("refuses to connect without one", () => {
    const states: string[] = [];
    const gw = new Gateway("ws://localhost/ws", { onState: (s) => states.push(s) });
    gw.connect();
    expect(states).toContain("refused");
  });

  it("keeps the token out of anything serialisable", () => {
    const gw = new Gateway("ws://localhost/ws");
    gw.setToken("super-secret-token");
    expect(gw.hasToken).toBe(true);

    // A TypeScript `private` is erased at runtime, so the token would survive
    // into an error report, a debug dump, or React devtools. A `#private`
    // field does not.
    expect(JSON.stringify(gw)).not.toContain("super-secret-token");
    expect(Object.values(gw).join("|")).not.toContain("super-secret-token");
    expect(Object.keys(gw)).not.toContain("token");
  });

  it("never writes the token to persistent storage", () => {
    const gw = new Gateway("ws://localhost/ws");
    gw.setToken("super-secret-token");
    const dump = [
      ...Object.keys(globalThis.localStorage ?? {}),
      ...Object.keys(globalThis.sessionStorage ?? {}),
    ].join("|");
    expect(dump).not.toContain("super-secret-token");
    expect(globalThis.localStorage?.length ?? 0).toBe(0);
  });
});

describe("the envelope channel", () => {
  it("comes from the catalog, not the caller", () => {
    // `sub` rides `session` while subscribing *to* `quotes`. Sending it on
    // `quotes` gets it rejected as wrong_channel — and a rejection arrives as
    // an `error` frame, not an exception, so it fails silently.
    expect(CHANNEL_OF["sub"]).toBe("session");
    expect(CHANNEL_OF["intent.open"]).toBe("orders");
    expect(CHANNEL_OF["pad.telemetry"]).toBe("session");
    expect(CHANNEL_OF["voice.begin"]).toBe("voice");
  });

  it("refuses a message type the catalog does not know", () => {
    const gw = new Gateway("ws://localhost/ws");
    expect(() => gw.send("intent.teleport", {})).toThrow(/unknown message type/);
  });

  it("covers every type the client sends", () => {
    for (const t of ["hello", "ping", "sub", "resync", "snap", "pad.telemetry",
                     "intent.open", "intent.close", "intent.modify", "intent.panic"]) {
      expect(CHANNEL_OF[t]).toBeTruthy();
    }
  });
});
