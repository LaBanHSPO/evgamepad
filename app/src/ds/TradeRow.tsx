import { useState } from "react";
import type { CSSProperties, HTMLAttributes } from "react";
import { Badge } from "./Badge";
import { Icon } from "./Icon";
import { PnLValue } from "./PnLValue";
import { Tag } from "./Tag";

/** Port of components/trading/TradeRow.jsx. */

export type TradeTag = string | { label: string; color?: string };

export interface TradeRowProps extends Omit<HTMLAttributes<HTMLDivElement>, "children"> {
  time?: string;
  symbol?: string;
  side?: "long" | "short";
  size?: string;
  entry?: string;
  exit?: string;
  result?: number | string;
  tags?: TradeTag[];
  status?: string;
  selected?: boolean;
  style?: CSSProperties;
}

export function TradeRow({
  time,
  symbol,
  side = "long",
  entry,
  exit,
  result,
  tags = [],
  status,
  selected,
  onClick,
  style,
  ...rest
}: TradeRowProps) {
  const [hover, setHover] = useState(false);
  const sideColor = side === "short" ? "var(--side-short)" : "var(--side-long)";
  const cell: CSSProperties = {
    fontFamily: "var(--font-data)",
    fontSize: "var(--text-xs)",
    color: "var(--text-secondary)",
    fontVariantNumeric: "tabular-nums",
    minWidth: 0,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  };
  return (
    <div
      role="row"
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "grid",
        gridTemplateColumns:
          "minmax(0,52px) minmax(0,74px) 40px minmax(0,84px) minmax(34px,1.2fr) minmax(58px,90px) 20px",
        alignItems: "center",
        gap: "var(--space-8)",
        minHeight: "var(--row-h)",
        padding: "4px 0",
        paddingLeft: "var(--space-12)",
        paddingRight: "var(--space-12)",
        borderBottom: "var(--border-hairline)",
        borderLeft: `2px solid ${selected ? "var(--phos-400)" : "transparent"}`,
        background: selected
          ? "var(--surface-selected)"
          : hover
            ? "var(--surface-hover)"
            : "transparent",
        cursor: onClick ? "pointer" : "default",
        transition: "var(--transition-control)",
        ...style,
      }}
      {...rest}
    >
      <span style={{ ...cell, color: "var(--text-muted)" }}>{time}</span>
      <span
        style={{
          fontFamily: "var(--font-core)",
          fontSize: "var(--text-xs)",
          fontWeight: "var(--weight-bold)" as CSSProperties["fontWeight"],
          color: "var(--text-body)",
          letterSpacing: "var(--tracking-wide)",
          minWidth: 0,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {symbol}
      </span>
      <span
        style={{
          fontFamily: "var(--font-core)",
          fontSize: "var(--text-2xs)",
          fontWeight: "var(--weight-bold)" as CSSProperties["fontWeight"],
          letterSpacing: "var(--tracking-caps)",
          textTransform: "uppercase",
          color: sideColor,
          minWidth: 0,
          overflow: "hidden",
        }}
      >
        {side}
      </span>
      <span style={{ ...cell, whiteSpace: "normal", lineHeight: 1.15, textOverflow: "clip" }}>
        {entry}
        {exit ? (
          <>
            <span style={{ color: "var(--text-disabled)" }}> → </span>
            {exit}
          </>
        ) : null}
      </span>
      <span style={{ display: "flex", gap: "var(--space-4)", minWidth: 0, overflow: "hidden" }}>
        {tags.slice(0, 3).map((t) => {
          const label = typeof t === "string" ? t : t.label;
          const color = typeof t === "string" ? undefined : t.color;
          return (
            <Tag key={label} color={color}>
              {label}
            </Tag>
          );
        })}
        {status ? (
          <Badge tone={status === "open" ? "live" : "neutral"} dot={status === "open"}>
            {status}
          </Badge>
        ) : null}
      </span>
      <span style={{ minWidth: 0, display: "flex", justifyContent: "flex-end", overflow: "hidden" }}>
        <PnLValue value={result ?? 0} size="sm" />
      </span>
      <span
        style={{
          color: hover ? "var(--phos-400)" : "var(--text-disabled)",
          display: "flex",
          justifyContent: "flex-end",
        }}
      >
        <Icon name="chevron-right" size="sm" />
      </span>
    </div>
  );
}
