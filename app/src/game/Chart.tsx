/**
 * The candle chart.
 *
 * Lightweight Charts owns its own canvas and its own update path: bars arrive
 * as `candle` frames and go straight to `series.update()`. React renders the
 * container once and never re-renders on a bar, for the same reason it never
 * re-renders on a quote -- a chart redraw under a live ARM is a redraw the
 * player did not ask for.
 *
 * The 20 EMA is recomputed only when a bar *closes*. Recomputing it on the
 * forming bar would make the line twitch on every tick against a value that is
 * not yet real.
 */

import { createChart, CandlestickSeries, LineSeries, type IChartApi, type ISeriesApi } from "lightweight-charts";
import { useEffect, useRef } from "react";
import { EMA_PERIOD, ema } from "./ema";

export type CandleFrame = {
  sym: string;
  tf: string;
  ts: number;
  o: number;
  h: number;
  l: number;
  c: number;
  closed?: boolean;
};

/** Project tokens, so the chart is part of the HUD rather than a widget in it. */
const INK = {
  up: "#00FF41",
  down: "#E8202A",
  grid: "#131B13",
  text: "#6E7C6E",
  ema: "#FFD400",
  ground: "#040604",
};

export function Chart({
  candles,
  sym,
  tf,
}: {
  /** Frames arrive here from the socket; the chart drains without React. */
  candles: React.MutableRefObject<CandleFrame[]>;
  sym: string;
  tf: string;
}) {
  const host = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const price = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const line = useRef<ISeriesApi<"Line"> | null>(null);
  /**
   * Bars by open time. Lightweight Charts refuses an `update()` older than the
   * last one it received, and a history replay legitimately arrives after live
   * bars (a reconnect, a re-subscribe). Keeping the series here lets an
   * out-of-order batch rebuild with `setData` instead of throwing.
   */
  const bars = useRef<Map<number, CandleFrame>>(new Map());
  const latest = useRef(0);
  const series = useRef(`${sym}:${tf}`);

  useEffect(() => {
    if (!host.current) return;

    const api = createChart(host.current, {
      layout: {
        background: { color: INK.ground },
        textColor: INK.text,
        fontFamily: '"JetBrains Mono", ui-monospace, monospace',
        fontSize: 11,
        attributionLogo: false,
      },
      grid: { vertLines: { color: INK.grid }, horzLines: { color: INK.grid } },
      rightPriceScale: { borderColor: INK.grid },
      timeScale: { borderColor: INK.grid, timeVisible: true, secondsVisible: false },
      crosshair: { mode: 0 },
      handleScroll: true,
      handleScale: true,
    });

    price.current = api.addSeries(CandlestickSeries, {
      upColor: INK.up,
      downColor: INK.down,
      borderUpColor: INK.up,
      borderDownColor: INK.down,
      wickUpColor: INK.up,
      wickDownColor: INK.down,
    });
    line.current = api.addSeries(LineSeries, {
      color: INK.ema,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    chart.current = api;

    const resize = new ResizeObserver(([entry]) => {
      if (entry) api.applyOptions({ width: entry.contentRect.width, height: entry.contentRect.height });
    });
    resize.observe(host.current);

    let raf = 0;
    const drain = () => {
      raf = requestAnimationFrame(drain);
      if (candles.current.length === 0) return;

      const batch = candles.current.splice(0, candles.current.length);
      let closedAny = false;
      let rewind = false;

      for (const bar of batch) {
        if (`${bar.sym}:${bar.tf}` !== series.current) {
          // A frame for a series we are no longer showing. Dropping it is
          // right: the switch already replayed the new series' history.
          continue;
        }
        const time = Math.floor(bar.ts / 1000);
        if (time < latest.current) rewind = true;
        latest.current = Math.max(latest.current, time);
        bars.current.set(time, bar);
        if (bar.closed) closedAny = true;
      }
      if (batch.length === 0) return;

      const ordered = [...bars.current.entries()].sort((a, b) => a[0] - b[0]);

      if (rewind) {
        // A replay landed behind the live edge. Rebuilding is the only correct
        // move; updating would be refused and would leave a hole in the chart.
        price.current?.setData(
          ordered.map(([time, b]) => ({
            time: time as never, open: b.o, high: b.h, low: b.l, close: b.c,
          })),
        );
      } else {
        for (const bar of batch) {
          if (`${bar.sym}:${bar.tf}` !== series.current) continue;
          price.current?.update({
            time: Math.floor(bar.ts / 1000) as never,
            open: bar.o, high: bar.h, low: bar.l, close: bar.c,
          });
        }
      }

      // Only on a close, or a rebuild: a line recomputed against the forming
      // bar twitches every tick against a value that is not final.
      if (closedAny || rewind) {
        const closes = ordered
          .filter(([, b]) => b.closed)
          .map(([time, b]) => ({ time, close: b.c }));
        if (closes.length >= EMA_PERIOD) {
          line.current?.setData(
            ema(closes).map((p) => ({ time: p.time as never, value: p.value })),
          );
        }
      }
    };
    raf = requestAnimationFrame(drain);

    return () => {
      cancelAnimationFrame(raf);
      resize.disconnect();
      api.remove();
      chart.current = null;
      price.current = null;
      line.current = null;
    };
  }, [candles]);

  // Switching symbol or timeframe clears the series; the gateway replays the
  // new one's history on `sub`.
  useEffect(() => {
    series.current = `${sym}:${tf}`;
    bars.current = new Map();
    latest.current = 0;
    candles.current.length = 0;
    price.current?.setData([]);
    line.current?.setData([]);
  }, [sym, tf, candles]);

  return (
    <div className="chart">
      <div className="chart__label">
        {sym} · {tf} · <span style={{ color: INK.ema }}>EMA {EMA_PERIOD}</span>
      </div>
      <div ref={host} className="chart__canvas" />
    </div>
  );
}
