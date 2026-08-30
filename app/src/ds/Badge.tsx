import type { CSSProperties, HTMLAttributes, ReactNode } from "react";

/** Port of components/core/Badge.jsx. */

export type BadgeTone = "neutral" | "live" | "up" | "down" | "warn" | "info" | "agent";

const TONES: Record<BadgeTone, { fg: string; bg: string; bd: string }> = {
  neutral: { fg: "var(--text-secondary)", bg: "var(--black-4)", bd: "var(--line-neutral)" },
  live: { fg: "var(--phos-300)", bg: "var(--phos-a16)", bd: "var(--line-strong)" },
  up: { fg: "var(--pnl-up)", bg: "var(--pnl-up-bg)", bd: "var(--line-strong)" },
  down: { fg: "var(--pnl-down)", bg: "var(--pnl-down-bg)", bd: "var(--arcade-red-dim)" },
  warn: { fg: "var(--arcade-yellow)", bg: "rgba(255,212,0,.14)", bd: "rgba(255,212,0,.4)" },
  info: { fg: "var(--arcade-cyan)", bg: "rgba(34,224,255,.14)", bd: "rgba(34,224,255,.4)" },
  agent: { fg: "var(--status-agent)", bg: "rgba(255,61,166,.14)", bd: "rgba(255,61,166,.4)" },
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
  dot?: boolean;
  children?: ReactNode;
  style?: CSSProperties;
}

export function Badge({ tone = "neutral", dot, children, style, ...rest }: BadgeProps) {
  const t = TONES[tone] || TONES.neutral;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-6)",
        height: 18,
        padding: "0 6px",
        background: t.bg,
        color: t.fg,
        border: `1px solid ${t.bd}`,
        borderRadius: "var(--radius-none)",
        fontFamily: "var(--font-core)",
        fontSize: "var(--text-2xs)",
        fontWeight: "var(--weight-bold)" as CSSProperties["fontWeight"],
        letterSpacing: "var(--tracking-caps)",
        textTransform: "uppercase",
        whiteSpace: "nowrap",
        ...style,
      }}
      {...rest}
    >
      {dot ? (
        <i
          style={{
            width: 5,
            height: 5,
            borderRadius: "var(--radius-pill)",
            background: t.fg,
            boxShadow: `0 0 6px ${t.fg}`,
          }}
        />
      ) : null}
      {children}
    </span>
  );
}
