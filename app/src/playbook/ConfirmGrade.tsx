import type { TiltState } from "../hud/TiltPip";
import type { GradePreview } from "./types";
import { gradeLine } from "./types";

/**
 * The grade in the confirm overlay — the line that makes this feature worth having.
 *
 * It appears **before** the fire, names the active playbook, and says how many of its rules the
 * trade in front of you satisfies. A failing playbook rule is information, never a block: the
 * fire goes through either way, and the number is there so you can decide not to.
 *
 * From the hot band up it also carries the tilt driver and the evening's realised R, because those
 * are the two facts most worth seeing at the moment you are least likely to look them up. Both are
 * shown here and nowhere near a close — this overlay stands in front of an open only.
 */
export function ConfirmGrade({ preview, tilt = null, dayR = null }: {
  preview: GradePreview | null;
  tilt?: TiltState | null;
  dayR?: number | null;
}): JSX.Element {
  const clean = preview?.grade.clean ?? false;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ color: clean ? "var(--phos-200)" : "var(--arcade-yellow)" }}>
        {gradeLine(preview)}
      </div>
      {preview ? (
        <div style={{ fontSize: 12, opacity: 0.75 }}>
          {preview.grade.results
            .filter((r) => r.unknown)
            .map((r) => r.label)
            .join(" · ") || "every rule had the data it needed"}
        </div>
      ) : (
        <div style={{ fontSize: 12, opacity: 0.75 }}>grading lands with a selected playbook</div>
      )}
      {tilt && (tilt.band === "hot" || tilt.band === "scorched") ? (
        <div style={{ fontSize: 12, color: "var(--arcade-red)" }}>
          {tilt.top[0] ?? tilt.band}
          {dayR === null ? "" : ` · tonight ${dayR >= 0 ? "+" : ""}${dayR.toFixed(2)}R`}
        </div>
      ) : null}
    </div>
  );
}
