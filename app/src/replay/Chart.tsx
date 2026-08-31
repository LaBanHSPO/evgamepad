import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  createSeriesMarkers,
  LineStyle,
} from "lightweight-charts";
import type { IChartApi, ISeriesApi, Time } from "lightweight-charts";
import { excursionLines, eventMarkers, tradeMarkers } from "./Markers";
import { resample, sideForTrade, toPrice } from "./resample";
import type { ReplayBody } from "./types";

/**
 * The tape, drawn.
 *
 * The chart is imperative on purpose, the same reasoning the live HUD uses for its price nodes:
 * React owns the layout around it and never re-renders on a playhead move. Only a change of
 * timeframe or trade rebuilds the series.
 *
 * The side is chosen from the trade, not defaulted. A long is exited on the bid and a short on the
 * ask; charting a short against the bid would understate every adverse move by the spread, which
 * is exactly the asymmetry the tape stores both sides to avoid.
 */

export function Chart({ body, seconds, playheadMs, height = 320 }: {
  body: ReplayBody;
  seconds: number;
  playheadMs: number;
  height?: number;
}): JSX.Element {
  const hostRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (host === null) return;

    const chart = createChart(host, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "var(--phos-400, #8f8)",
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,.05)" },
        horzLines: { color: "rgba(255,255,255,.05)" },
      },
      timeScale: { timeVisible: true, secondsVisible: seconds < 60 },
      handleScroll: true,
      handleScale: true,
    });
    chartRef.current = chart;
    seriesRef.current = chart.addSeries(CandlestickSeries, {
      upColor: "#2fbf71", downColor: "#d9534f",
      wickUpColor: "#2fbf71", wickDownColor: "#d9534f",
      borderVisible: false,
    });

    const resize = () => chart.applyOptions({ width: host.clientWidth });
    resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [height, seconds]);

  // Series, markers and excursion lines: rebuilt only when the tape or the timeframe changes.
  useEffect(() => {
    const series = seriesRef.current;
    const tape = body.tape;
    if (series === null || tape === null) return;

    const scale = body.scale;
    const candles = resample(tape, sideForTrade(body.trade.side), seconds).map((candle) => ({
      time: candle.time as Time,
      open: toPrice(candle.open, scale),
      high: toPrice(candle.high, scale),
      low: toPrice(candle.low, scale),
      close: toPrice(candle.close, scale),
    }));
    series.setData(candles);

    createSeriesMarkers(series, [
      ...tradeMarkers(body.trade, seconds),
      ...eventMarkers(body.events, seconds),
    ].sort((a, b) => a.time - b.time).map((marker) => ({ ...marker, time: marker.time as Time })));

    const lines = excursionLines(body.trade).map((line) =>
      series.createPriceLine({
        price: line.price,
        color: line.colour,
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
        title: line.label,
      }),
    );
    chartRef.current?.timeScale().fitContent();
    return () => lines.forEach((line) => series.removePriceLine(line));
  }, [body, seconds]);

  // The playhead is a crosshair move, not a re-render — scrubbing must not cost reconciliation.
  useEffect(() => {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (chart === null || series === null) return;
    chart.setCrosshairPosition(0, (Math.floor(playheadMs / 1000 / seconds) * seconds) as Time,
                              series);
  }, [playheadMs, seconds]);

  return <div ref={hostRef} style={{ width: "100%" }} />;
}
