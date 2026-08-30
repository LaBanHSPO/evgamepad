import type { CSSProperties, HTMLAttributes, ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

/** Port of components/core/StatTile.jsx. */

export interface StatTileProps extends HTMLAttributes<HTMLDivElement> {
  label?: ReactNode;
  value?: ReactNode;
  delta?: ReactNode;
  tone?: "neutral" | "up" | "down";
  icon?: IconName;
  sub?: ReactNode;
  style?: CSSProperties;
}

export function StatTile({
  label,
  value,
  delta,
  tone = "neutral",
  icon,
  sub,
  style,
  ...rest
}: StatTileProps) {
  const c =
    tone === "up" ? "var(--pnl-up)" : tone === "down" ? "var(--pnl-down)" : "var(--text-primary)";
  return (
    <div
      style={{
        background: "var(--surface-panel)",
        border: "var(--border-hairline)",
        padding: "var(--space-12)",
        display: "grid",
        gap: "var(--space-6)",
        fontFamily: "var(--font-core)",
        minWidth: 0,
        overflow: "hidden",
        ...style,
      }}
      {...rest}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-6)",
          color: "var(--text-muted)",
          fontSize: "var(--text-2xs)",
          letterSpacing: "var(--tracking-caps)",
          textTransform: "uppercase",
        }}
      >
        {icon ? <Icon name={icon} size="xs" /> : null}
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {label}
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: "var(--space-8)" }}>
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: "clamp(15px, 2.1vw, 20px)",
            fontWeight: "var(--weight-bold)" as CSSProperties["fontWeight"],
            color: c,
            fontVariantNumeric: "tabular-nums",
            whiteSpace: "nowrap",
            textShadow: tone === "up" ? "var(--glow-text)" : "none",
          }}
        >
          {value}
        </span>
        {delta ? (
          <span
            style={{
              fontSize: "var(--text-xs)",
              color: tone === "down" ? "var(--pnl-down)" : "var(--phos-500)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {delta}
          </span>
        ) : null}
      </div>
      {sub ? (
        <div style={{ fontSize: "var(--text-2xs)", color: "var(--text-muted)" }}>{sub}</div>
      ) : null}
    </div>
  );
}
