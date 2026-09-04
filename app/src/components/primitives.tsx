import type { CSSProperties, ReactNode } from "react";
import { GamepadKey } from "../ds";
import { useGlyphAction } from "../journey/Cabinet";

/**
 * Small repeated shapes lifted out of the prototype markup. Each one reproduces
 * an inline-styled pattern that recurs verbatim across the arcade screens.
 */

/** The artboard: a screen label above a fixed-size frame. */
export function Artboard({
  label,
  frameStyle,
  children,
}: {
  label: string;
  frameStyle: CSSProperties;
  children: ReactNode;
}) {
  return (
    <div style={{ display: "grid", gap: 12, justifyItems: "start" }}>
      <span
        style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: ".18em",
          textTransform: "uppercase",
          color: "var(--phos-300)",
        }}
      >
        {label}
      </span>
      <div
        style={{
          fontFamily: "var(--font-core)",
          color: "var(--text-body)",
          overflow: "hidden",
          ...frameStyle,
        }}
      >
        {children}
      </div>
    </div>
  );
}

/** A boxed pad hint in a screen footer: key glyph + what it does. Clickable when the cabinet binds it. */
export function PadHint({
  button,
  label,
  size = "md",
  pressed,
  dim,
}: {
  button: string;
  label: string;
  size?: "sm" | "md" | "lg";
  pressed?: boolean;
  /** "Fire · disabled" on the session-over footer. */
  dim?: boolean;
}) {
  const { action, fire } = useGlyphAction(button);
  const clickable = Boolean(action) && !dim;
  return (
    <div
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
      onClick={clickable ? fire : undefined}
      onKeyDown={
        clickable
          ? (event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                fire();
              }
            }
          : undefined
      }
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "6px 10px",
        border: "1px solid var(--line-hairline)",
        cursor: clickable ? "pointer" : undefined,
        ...(dim ? { opacity: 0.4 } : null),
      }}
    >
      <GamepadKey button={button} size={size} pressed={pressed} passive />
      <span
        style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: ".18em",
          textTransform: "uppercase",
          color: dim ? "var(--text-disabled)" : "var(--text-secondary)",
        }}
      >
        {label}
      </span>
    </div>
  );
}

/** An uppercase tracked label — the system's one casing rule. */
export function Caps({
  children,
  size = 9,
  color = "var(--text-disabled)",
  weight,
  style,
}: {
  children: ReactNode;
  size?: number;
  color?: string;
  weight?: number;
  style?: CSSProperties;
}) {
  return (
    <span
      style={{
        fontSize: size,
        fontWeight: weight,
        letterSpacing: ".18em",
        textTransform: "uppercase",
        color,
        ...style,
      }}
    >
      {children}
    </span>
  );
}

/** A terminal line in the agent voice: VT323, one clause, `> ` prefixed. */
export function Term({
  children,
  size = 16,
  color = "var(--grey-300)",
  style,
}: {
  children: ReactNode;
  size?: number;
  color?: string;
  style?: CSSProperties;
}) {
  return (
    <span style={{ fontFamily: "var(--font-terminal)", fontSize: size, color, ...style }}>
      &gt; {children}
    </span>
  );
}

/** The EVGAMEPAD type lockup — `EV` phosphor, `GAMEPAD` arcade red. */
export function Wordmark({ size = 11 }: { size?: number }) {
  return (
    <span
      style={{
        fontFamily: "var(--font-display)",
        fontSize: size,
        color: "var(--phos-400)",
        textShadow: "var(--glow-text)",
      }}
    >
      EV<span style={{ color: "var(--arcade-red)" }}>GAMEPAD</span>
    </span>
  );
}

/** The 44px app header the data screens share: wordmark, title, meta, extras. */
export function ScreenHeader({
  title,
  meta,
  children,
  right,
}: {
  title: string;
  meta?: string;
  /** Badges and the like, sitting after the meta line. */
  children?: ReactNode;
  /** Pushed to the right edge. */
  right?: ReactNode;
}) {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        padding: "0 16px",
        borderBottom: "1px solid var(--line-hairline)",
        background: "var(--black-2)",
      }}
    >
      <Wordmark />
      <Caps size={11} weight={700} color="var(--text-body)">
        {title}
      </Caps>
      {meta ? (
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: 10,
            letterSpacing: ".12em",
            color: "var(--text-muted)",
          }}
        >
          {meta}
        </span>
      ) : null}
      {children}
      {right ? (
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
          {right}
        </div>
      ) : null}
    </header>
  );
}

/** The 44px footer the data screens share: pad hints, then the legal line. */
export function ScreenFooter({
  children,
  notice,
  height,
}: {
  children?: ReactNode;
  notice?: ReactNode;
  /**
   * Set only where the frame's last grid row is `auto` — the prototype gives
   * the footer an explicit content height there, so it occupies height + 1px
   * of border. In a fixed 44px row the footer stretches and this stays unset.
   */
  height?: number;
}) {
  return (
    <footer
      style={{
        display: "flex",
        alignItems: "center",
        gap: 18,
        height,
        padding: "0 16px",
        borderTop: "1px solid var(--line-hairline)",
        background: "var(--black-1)",
      }}
    >
      {children}
      <DemoNotice>{notice}</DemoNotice>
    </footer>
  );
}

/** The legal line every screen footer ends with. */
export function DemoNotice({ children }: { children?: ReactNode }) {
  return (
    <span
      style={{
        marginLeft: "auto",
        fontFamily: "var(--font-terminal)",
        fontSize: 15,
        color: "var(--phos-600)",
      }}
    >
      &gt; {children ?? "demo only · not advice · entertainment, not alpha"}
    </span>
  );
}
