/**
 * Runtime for the matrix and city artboards.
 *
 * REST paints the cabinet without a token. Flatten / fire still need the memory-only socket,
 * same rule as the live HUD: the token is pasted once and never written to storage.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { GameAgent } from "../agent";
import type { AgentView } from "../agent";
import { useCabinet } from "../journey/Cabinet";
import { GameClient } from "../net/ws";
import type { SocketStatus } from "../net/ws";
import { PadPoller } from "../pad/poll";
import type { Envelope } from "../protocol/types";
import { fetchHud, fetchSkins, pickSkin } from "./fetch";
import {
  DASH,
  eventClock,
  lotsLabel,
  midOf,
  pickSymbol,
  planStop,
  resolveArt,
  resolveSprite,
  threatOf,
} from "./format";
import type { ArcadeHud, ArcadeSkin, ArcadeSymbol } from "./types";
import { FALLBACK_SKINS } from "./types";

const POLL_MS = 1000;
const DEFAULT_SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"];

export interface LiveQuote {
  sym: string;
  bid: number;
  ask: number;
}

export interface ArcadeRuntime {
  skinId: "matrix" | "city";
  skin: ArcadeSkin;
  artUrl: string;
  sprite: (key: string, fallback: string) => string;
  hud: ArcadeHud | null;
  online: boolean;
  selected: ArcadeSymbol | undefined;
  price: number | null;
  spread: number | null;
  clock: string;
  standDowns: number;
  hiScore: number;
  maxPositions: number;
  positionsOpen: number;
  slots: boolean[];
  flatten: () => void;
  token: string;
  setToken: (value: string) => void;
  connect: () => void;
  socketStatus: SocketStatus | "idle";
  view: AgentView | null;
  showDollars: boolean;
  setShowDollars: (value: boolean) => void;
  log: string[];
  liveQuote: LiveQuote | null;
  threat: ReturnType<typeof threatOf>;
  eventEta: string;
  lotsText: string;
  planSl: number | null;
}

export function useArcadeRuntime(skinId: "matrix" | "city"): ArcadeRuntime {
  const cabinet = useCabinet();
  const [skins, setSkins] = useState<ArcadeSkin[]>([FALLBACK_SKINS.matrix, FALLBACK_SKINS.city]);
  const [hud, setHud] = useState<ArcadeHud | null>(null);
  const [online, setOnline] = useState(false);
  const [token, setToken] = useState("");
  const [status, setStatus] = useState<SocketStatus | "idle">("idle");
  const [view, setView] = useState<AgentView | null>(null);
  const [showDollars, setShowDollars] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const [liveQuote, setLiveQuote] = useState<LiveQuote | null>(null);

  const clientRef = useRef<GameClient | null>(null);
  const agentRef = useRef<GameAgent | null>(null);
  const pollerRef = useRef<PadPoller | null>(null);

  const note = useCallback((line: string) => {
    setLog((prev) => [`${new Date().toLocaleTimeString()} ${line}`, ...prev].slice(0, 6));
  }, []);

  useEffect(() => {
    let cancelled = false;
    void fetchSkins().then((rows) => {
      if (!cancelled) setSkins(rows);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const tick = () => {
      void fetchHud().then((body) => {
        if (cancelled) return;
        setHud(body);
        setOnline(body != null);
      });
    };
    tick();
    const id = window.setInterval(tick, POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  const onMessage = useCallback((envelope: Envelope) => {
    agentRef.current?.onMessage(envelope);
    const payload = envelope.p as Record<string, number | string>;
    if (envelope.t === "quote" && typeof payload.bid === "number" && typeof payload.ask === "number") {
      setLiveQuote({
        sym: String(payload.sym ?? ""),
        bid: Number(payload.bid),
        ask: Number(payload.ask),
      });
    }
    if (envelope.t === "order.reject") note(`reject: ${payload.reason}`);
    if (envelope.t === "order.ack") note(`ack ${payload.side} ${payload.lots} ${payload.sym}`);
  }, [note]);

  const connect = useCallback(() => {
    if (!token) return;
    pollerRef.current?.stop();
    clientRef.current?.disconnect();

    const symbols = hud?.symbols.map((row) => row.name) ?? DEFAULT_SYMBOLS;
    const client = new GameClient(`${location.origin.replace(/^http/, "ws")}/ws`, token, {
      onMessage,
      onStatus: (next) => {
        setStatus(next);
        if (next === "closed") agentRef.current?.onSocketClosed();
      },
    });
    const first = hud?.symbols[0];
    const lotSteps = first
      ? [first.lotStep, first.defaultLots, first.maxLots].filter((n, i, all) => all.indexOf(n) === i)
      : undefined;
    const agent = new GameAgent({
      client,
      symbols,
      lotSteps: lotSteps?.length ? lotSteps : undefined,
      onView: setView,
      onStandDown: (conditions) => {
        note(`stood down (${conditions.join(", ")})`);
        void fetch("/api/journal/stand-down", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ conditions }),
        });
      },
    });
    const poller = new PadPoller({
      onFrame: (frame) => agent.onFrame(frame),
      onAbsent: (input) => agent.onAbsent(input),
      onProfile: (profile) => note(`pad: ${profile.id}`),
    });
    clientRef.current = client;
    agentRef.current = agent;
    pollerRef.current = poller;
    client.connect();
    poller.start();
    client.send("sub", "session", { ch: "quotes", syms: symbols });
    note("socket connecting");
  }, [hud, note, onMessage, token]);

  useEffect(() => () => {
    pollerRef.current?.stop();
    clientRef.current?.disconnect();
  }, []);

  useEffect(() => {
    agentRef.current?.setOverlayOpen(Boolean(cabinet?.state.overlayOpen));
  }, [cabinet?.state.overlayOpen]);

  const flatten = useCallback(() => {
    agentRef.current?.flatten();
    note("flatten sent");
  }, [note]);

  const skin = useMemo(() => pickSkin(skins, skinId), [skins, skinId]);
  const selected = pickSymbol(hud, view?.symbol);
  const restPrice = midOf(selected);
  const liveForSelected =
    liveQuote && selected && liveQuote.sym === selected.name
      ? (liveQuote.bid + liveQuote.ask) / 2
      : null;
  const price = liveForSelected ?? restPrice;
  const spread =
    liveQuote && selected && liveQuote.sym === selected.name
      ? liveQuote.ask - liveQuote.bid
      : selected?.spread ?? null;
  const maxPositions = hud?.risk.maxPositions ?? 1;
  const positionsOpen = hud?.positions.length ?? 0;
  const remainingSlots = Math.max(0, maxPositions - positionsOpen);
  const slots = Array.from({ length: Math.max(maxPositions, 1) }, (_, i) => i < remainingSlots);

  return {
    skinId,
    skin,
    artUrl: resolveArt(skin, FALLBACK_SKINS[skinId].fallback),
    sprite: (key, fallback) => resolveSprite(skin, key, fallback),
    hud,
    online,
    selected,
    price,
    spread,
    clock: hud?.session.clock ?? DASH,
    standDowns: view?.stoodDown ?? hud?.standDowns ?? 0,
    hiScore: hud?.hiScore ?? 0,
    maxPositions,
    positionsOpen,
    slots,
    flatten,
    token,
    setToken,
    connect,
    socketStatus: status,
    view,
    showDollars,
    setShowDollars,
    log,
    liveQuote,
    threat: threatOf(hud?.sentinel ?? null),
    eventEta: eventClock(hud?.sentinel ?? null),
    lotsText: lotsLabel(selected, hud?.positions ?? []),
    planSl: planStop(selected, price),
  };
}
