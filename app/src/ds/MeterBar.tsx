import type { CSSProperties, HTMLAttributes } from "react";

/** Port of components/feedback/MeterBar.jsx. */

export type MeterTone = "phos" | "danger" | "warn" | "info";

export interface MeterBarProps extends HTMLAttributes<HTMLDivElement> {
  value?: number;
  max?: number;
  label?: string;
  segments?: number;
  tone?: MeterTone;
  showValue?: boolean;
  style?: CSSProperties;
}

export function MeterBar({
  value = 0,
  max = 100,
  label,
  segments = 20,
  tone = "phos",
  showValue,
  style,
  ...rest
}: MeterBarProps) {
  const pct = Math.max(0, Math.min(1, max ? value / max : 0));
  const filled = Math.round(pct * segments);
  const color =
    tone === "danger"
      ? "var(--arcade-red)"
      : tone === "warn"
        ? "var(--arcade-yellow)"
        : tone === "info"
          ? "var(--arcade-cyan)"
          : "var(--phos-400)";
  return (
    <div
      style={{
        display: "grid",
        gap: "var(--space-4)",
        fontFamily: "var(--font-core)",
        minWidth: 0,
        ...style,
      }}
      {...rest}
    >
      {label || showValue ? (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "var(--text-2xs)",
            letterSpacing: "var(--tracking-caps)",
            textTransform: "uppercase",
            color: "var(--text-muted)",
          }}
        >
          <span>{label}</span>
          {showValue ? (
            <span style={{ color, fontVariantNumeric: "tabular-nums" }}>
              {value}/{max}
            </span>
          ) : null}
        </div>
      ) : null}
      <div
        role="meter"
        aria-valuenow={value}
        aria-valuemax={max}
        style={{
          display: "flex",
          gap: 2,
          height: 8,
          background: "var(--surface-well)",
          border: "1px solid var(--line-hairline)",
          padding: 1,
        }}
      >
        {Array.from({ length: segments }).map((_, i) => (
          <span
            key={i}
            style={{
              flex: 1,
              background: i < filled ? color : "var(--black-5)",
              boxShadow: i < filled ? `0 0 4px ${color}` : "none",
              transition: "background-color var(--dur-fast) var(--ease-step-2)",
            }}
          />
        ))}
      </div>
    </div>
  );
}
