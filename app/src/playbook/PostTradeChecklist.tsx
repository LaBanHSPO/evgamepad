import { useState } from "react";
import type { Grade, RuleGrade } from "./types";
import { pendingManual } from "./types";

/**
 * The post-trade checklist: a few taps, and skipping is free.
 *
 * A skipped rule stays `unknown` — neither a pass nor a fail — and leaves the denominator
 * entirely, so declining to answer never costs the player anything. That is what stops the
 * checklist becoming a chore that gets abandoned in week two.
 */
export function PostTradeChecklist({ cid, grade, onDone }: {
  cid: string;
  grade: Grade | null;
  onDone: (answers: Record<string, boolean>) => void;
}): JSX.Element | null {
  const [answers, setAnswers] = useState<Record<string, boolean>>({});
  const pending: RuleGrade[] = pendingManual(grade);

  if (grade === null || pending.length === 0) return null;

  const answer = (code: string, value: boolean): void => {
    setAnswers((prev) => ({ ...prev, [code]: value }));
  };

  return (
    <section style={panel}>
      <div style={{ fontSize: 12, opacity: 0.75 }}>after the trade · {cid.slice(-6)}</div>
      {pending.map((rule) => (
        <div key={rule.code} style={row}>
          <span style={{ flex: 1 }}>{rule.label}</span>
          <button
            type="button"
            onClick={() => answer(rule.code, true)}
            style={answers[rule.code] === true ? chosen : choice}
          >
            yes
          </button>
          <button
            type="button"
            onClick={() => answer(rule.code, false)}
            style={answers[rule.code] === false ? chosen : choice}
          >
            no
          </button>
        </div>
      ))}
      <div style={row}>
        <button type="button" onClick={() => onDone(answers)} style={choice}>
          save
        </button>
        {/* Skipping sends nothing, so every unanswered rule stays unknown. */}
        <button type="button" onClick={() => onDone({})} style={choice}>
          skip
        </button>
        <span style={{ fontSize: 12, opacity: 0.7 }}>skipping costs nothing</span>
      </div>
    </section>
  );
}

const panel: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 8,
  padding: 12,
  border: "var(--border-hairline)",
  background: "var(--black-2)",
};
const row: React.CSSProperties = { display: "flex", gap: 8, alignItems: "center" };
const choice: React.CSSProperties = {
  background: "transparent",
  color: "inherit",
  border: "var(--border-hairline)",
  padding: "3px 10px",
  cursor: "pointer",
};
const chosen: React.CSSProperties = { ...choice, background: "var(--black-3)", color: "var(--phos-200)" };
