/**
 * The price, written straight to the DOM.
 *
 * This component renders once. After that a rAF loop reads the quote ref and
 * writes `textContent` at 15 Hz. React never sees a tick.
 *
 * That is not a micro-optimisation: quotes arrive faster than a person can
 * read, and re-rendering the tree on each one would re-render the confirm
 * overlay under a live ARM. The framework owns layout; the price owns itself.
 */

import { useEffect, useRef } from "react";
import type { Quote } from "./useGame";

/** Matches the gateway's browser conflation. Faster is unreadable anyway. */
const WRITE_HZ = 15;

export function PriceTape({
  quotes,
  sym,
}: {
  quotes: React.MutableRefObject<Map<string, Quote>>;
  sym: string;
}) {
  const bid = useRef<HTMLSpanElement>(null);
  const ask = useRef<HTMLSpanElement>(null);
  const spread = useRef<HTMLSpanElement>(null);
  const symRef = useRef(sym);
  symRef.current = sym;

  useEffect(() => {
    let raf = 0;
    let last = 0;
    let lastBid = 0;

    const tick = (now: number) => {
      raf = requestAnimationFrame(tick);
      if (now - last < 1000 / WRITE_HZ) return;
      last = now;

      const q = quotes.current.get(symRef.current);
      if (!q) {
        if (bid.current) bid.current.textContent = "—";
        if (ask.current) ask.current.textContent = "—";
        if (spread.current) spread.current.textContent = "no feed";
        return;
      }
      const digits = q.digits;
      if (bid.current) {
        bid.current.textContent = q.bid.toFixed(digits);
        // Direction colour is the only thing a glance needs from a tick.
        if (q.bid !== lastBid) {
          bid.current.dataset.dir = q.bid > lastBid ? "up" : "down";
          lastBid = q.bid;
        }
      }
      if (ask.current) ask.current.textContent = q.ask.toFixed(digits);
      if (spread.current) spread.current.textContent = (q.ask - q.bid).toFixed(digits);
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [quotes]);

  return (
    <div className="price-tape">
      <div className="price-tape__sym">{sym}</div>
      <div className="price-tape__pair">
        <span ref={bid} className="price-tape__bid" data-dir="up">
          —
        </span>
        <span className="price-tape__sep">/</span>
        <span ref={ask} className="price-tape__ask">
          —
        </span>
      </div>
      <div className="price-tape__spread">
        spread <span ref={spread}>—</span>
      </div>
    </div>
  );
}
