/**
 * The ARM confirm surface.
 *
 * Shows exactly what is about to be sent, the R it risks, and -- until phase 7
 * -- an honest `grading unavailable`. The placeholder is deliberate: the
 * overlay reserves the space so the layout does not jump when playbooks arrive,
 * and phase 3's acceptance does not depend on them existing.
 */

import type { ArmSide } from "../pad/fsm";
import type { GradeView, Quote } from "./useGame";

export function ConfirmOverlay({
  side,
  sym,
  lots,
  quote,
  relativeSl,
  relativeTp,
  rUsd,
  grade,
}: {
  side: ArmSide;
  sym: string;
  lots: number;
  quote: Quote | undefined;
  relativeSl: number | null;
  relativeTp: number | null;
  rUsd: number | null;
  /** From the gateway. The browser never grades a trade itself. */
  grade: GradeView | null;
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

      {grade ? (
        <div
          className="confirm__grade"
          data-state={grade.clean ? "clean" : "flagged"}
        >
          <strong>
            {grade.playbookId === "__unplanned__"
              ? "unplanned"
              : `${grade.required_pass}/${grade.required_total} rules OK`}
          </strong>
          {/* Only the failures. A list of everything that passed is noise at
              the moment of a fire. */}
          {grade.results
            .filter((r) => r.passed === false)
            .map((r) => (
              <span key={r.ruleId} className="confirm__grade-miss">
                ✗ {r.note || r.ruleId}
              </span>
            ))}
        </div>
      ) : (
        <div className="confirm__grade" data-state="unavailable">
          no playbook selected
        </div>
      )}

      <div className="confirm__hint">
        hold <kbd>LT</kbd> · press <kbd>RT</kbd> to fire · release to cancel
      </div>
    </div>
  );
}
