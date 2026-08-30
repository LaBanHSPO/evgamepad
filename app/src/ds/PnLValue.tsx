import type { CSSProperties, HTMLAttributes } from "react";
import { Icon } from "./Icon";

/** Port of components/trading/PnLValue.jsx. */

export interface PnLValueProps extends HTMLAttributes<HTMLSpanElement> {
  value: number | string;
  unit?: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl" | (string & {});
  showSign?: boolean;
  showArrow?: boolean;
  precision?: number;
  style?: CSSProperties;
}

const FONT_SIZES: Record<string, string> = {
  xs: "var(--text-xs)",
  sm: "var(--text-sm)",
  md: "var(--text-lg)",
  lg: "var(--text-2xl)",
  xl: "var(--text-4xl)",
};

export function PnLValue({
  value,
  unit = "R",
  size = "md",
  showSign = true,
  showArrow,
  precision = 2,
  style,
  ...rest
}: PnLValueProps) {
  const n = typeof value === "number" ? value : parseFloat(value);
  const dir = n > 0 ? "up" : n < 0 ? "down" : "flat";
  const color =
    dir === "up" ? "var(--pnl-up)" : dir === "down" ? "var(--pnl-down)" : "var(--pnl-flat)";
  const fs = FONT_SIZES[size] || size;
  const text = (showSign && n > 0 ? "+" : "") + (isNaN(n) ? String(value) : n.toFixed(precision));
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-4)",
        fontFamily: "var(--font-data)",
        fontSize: fs,
        fontWeight: "var(--weight-bold)" as CSSProperties["fontWeight"],
        color,
        fontVariantNumeric: "tabular-nums",
        letterSpacing: "var(--tracking-tight)",
        textShadow:
          dir === "up"
            ? "var(--glow-text)"
            : dir === "down"
              ? "0 0 6px rgba(232,32,42,.5)"
              : "none",
        ...style,
      }}
      {...rest}
    >
      {showArrow && dir !== "flat" ? (
        <Icon name={dir === "up" ? "arrow-up-right" : "arrow-down-right"} size="sm" />
      ) : null}
      {text}
      <span style={{ fontSize: "0.7em", opacity: 0.8 }}>{unit}</span>
    </span>
  );
}
