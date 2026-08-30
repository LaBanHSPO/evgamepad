/**
 * The ARM confirm surface.
 *
 * Shows exactly what is about to be sent, the R it risks, and -- until phase 7
 * -- an honest `grading unavailable`. The placeholder is deliberate: the
 * overlay reserves the space so the layout does not jump when playbooks arrive,
 * and phase 3's acceptance does not depend on them existing.
 */

import type { ArmSide } from "../pad/fsm";
import type { Quote } from "./useGame";

export function ConfirmOverlay({
  side,
  sym,
  lots,
  quote,
  relativeSl,
  relativeTp,
  rUsd,
}: {
  side: ArmSide;
  sym: string;
  lots: number;
  quote: Quote | undefined;
  relativeSl: number | null;
  relativeTp: number | null;
  rUsd: number | null;
}) {
  const price = quote ? (side === "buy" ? quote.ask : quote.bid) : null;
  const digits = quote?.digits ?? 2;
  const slDistance = relativeSl === null ? null : relativeSl / 100_000;
  const tpDistance = relativeTp === null ? null : relativeTp / 100_000;
  const sign = side === "buy" ? 1 : -1;

  const exit = side === "close" || side === "panic";

  return (
    <div className="confirm" data-side={side} role="status" aria-live="assertive">
      <div className="confirm__headline">
        {exit ? (
          <strong>{side === "panic" ? "FLATTEN ALL + LOCK" : "CLOSE POSITION"}</strong>
        ) : (
          <strong>
            {side.toUpperCase()} {lots.toFixed(2)} {sym}
            {price !== null ? ` @ ${price.toFixed(digits)}` : ""}
          </strong>
        )}
      </div>

      {!exit && (
        <dl className="confirm__grid">
          <div>
            <dt>SL</dt>
            <dd>
              {slDistance === null || price === null
                ? "none"
                : (price - sign * slDistance).toFixed(digits)}
            </dd>
          </div>
          <div>
            <dt>TP</dt>
            <dd>
              {tpDistance === null || price === null
                ? "none"
                : (price + sign * tpDistance).toFixed(digits)}
            </dd>
          </div>
          <div>
            <dt>risk</dt>
            <dd>{rUsd === null ? "1R" : `$${rUsd.toFixed(2)} = 1R`}</dd>
          </div>
        </dl>
      )}

      {/* Reserved for phase 7. Says so rather than pretending to grade. */}
      <div className="confirm__grade" data-state="unavailable">
        grading unavailable until phase 7
      </div>

      <div className="confirm__hint">
        hold <kbd>LT</kbd> · press <kbd>RT</kbd> to fire · release to cancel
      </div>
    </div>
  );
}
