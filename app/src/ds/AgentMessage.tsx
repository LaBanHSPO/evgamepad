import type { CSSProperties, HTMLAttributes, ReactNode } from "react";
import { Badge } from "./Badge";
import { Icon } from "./Icon";

/** Port of components/agents/AgentMessage.jsx. */

export interface AgentMessageProps extends HTMLAttributes<HTMLDivElement> {
  author?: "agent" | "user";
  name?: string;
  model?: string;
  time?: string;
  confidence?: number | string | null;
  streaming?: boolean;
  children?: ReactNode;
  style?: CSSProperties;
}

export function AgentMessage({
  author = "agent",
  name,
  model,
  time,
  confidence,
  streaming,
  children,
  style,
  ...rest
}: AgentMessageProps) {
  const isUser = author === "user";
  const accent = isUser ? "var(--phos-400)" : "var(--status-agent)";
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "22px 1fr",
        gap: "var(--space-8)",
        padding: "var(--space-12)",
        background: isUser ? "transparent" : "var(--black-2)",
        borderLeft: `2px solid ${accent}`,
        fontFamily: "var(--font-core)",
        minWidth: 0,
        ...style,
      }}
      {...rest}
    >
      <span
        style={{
          width: 22,
          height: 22,
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          border: `1px solid ${accent}`,
          color: accent,
          background: "var(--black-1)",
        }}
      >
        <Icon name={isUser ? "user" : "bot"} size="sm" />
      </span>
      <div style={{ display: "grid", gap: "var(--space-6)", minWidth: 0 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-8)",
            fontSize: "var(--text-2xs)",
            letterSpacing: "var(--tracking-caps)",
            textTransform: "uppercase",
          }}
        >
          <span style={{ color: accent, fontWeight: "var(--weight-bold)" as CSSProperties["fontWeight"] }}>
            {name || (isUser ? "you" : "agent")}
          </span>
          {model ? <span style={{ color: "var(--text-muted)" }}>{model}</span> : null}
          {confidence != null ? <Badge tone="agent">conf {confidence}</Badge> : null}
          {time ? (
            <span style={{ color: "var(--text-disabled)", marginLeft: "auto" }}>{time}</span>
          ) : null}
        </div>
        <div
          style={{
            fontFamily: isUser ? "var(--font-core)" : "var(--font-terminal)",
            fontSize: isUser ? "var(--text-sm)" : "var(--text-lg)",
            lineHeight: isUser ? "var(--leading-normal)" : "var(--leading-snug)",
            overflowWrap: "anywhere",
            color: isUser ? "var(--text-body)" : "var(--text-terminal)",
          }}
        >
          {children}
          {streaming ? (
            <span
              style={{
                display: "inline-block",
                width: 7,
                height: "1em",
                marginLeft: 3,
                background: "var(--phos-400)",
                verticalAlign: "text-bottom",
                animation: "ev-blink 1s steps(1,end) infinite",
              }}
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}
