/**
 * The pre/post session check-in: two pad taps, 1-5, skippable.
 *
 * Skippable is the important word. It is rendered as a dismissable panel over
 * the HUD rather than a gate in front of it, so a session can start while it is
 * still on screen. A journal prompt that stands between the player and their
 * evening is a prompt they will learn to resent.
 */

import { useState } from "react";
import { Button } from "../ds";

export type CheckInPhase = "pre" | "post";

export function CheckIn({
  phase,
  onDone,
}: {
  phase: CheckInPhase;
  onDone: (rating: number | null) => void;
}) {
  const [sent, setSent] = useState(false);
  if (sent) return null;

  const submit = async (rating: number | null) => {
    setSent(true);
    onDone(rating);
    try {
      await fetch("/api/session/checkin", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ phase, rating }),
      });
    } catch {
      // Never blocks the evening. A lost check-in is a reporting gap, not a
      // reason to stop the player trading.
    }
  };

  return (
    <aside className="checkin" role="note">
      <p className="checkin__ask">
        {phase === "pre" ? "How ready do you feel?" : "How did you trade that?"}
      </p>
      <div className="checkin__scale">
        {[1, 2, 3, 4, 5].map((n) => (
          <Button key={n} size="sm" variant="secondary" onClick={() => submit(n)}>
            {n}
          </Button>
        ))}
      </div>
      <button type="button" className="checkin__skip" onClick={() => submit(null)}>
        skip
      </button>
    </aside>
  );
}
