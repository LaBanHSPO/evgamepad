import type { CSSProperties, HTMLAttributes } from "react";
import { useGlyphAction } from "../journey/Cabinet";
import { Icon } from "./Icon";

/** Port of components/gamepad/GamepadKey.jsx. */

const FACE: Record<string, string> = {
  a: "var(--pad-a)",
  b: "var(--pad-b)",
  x: "var(--pad-x)",
  y: "var(--pad-y)",
};

const DIR: Record<string, string> = {
  up: "chevron-up",
  down: "chevron-down",
  left: "chevron-left",
  right: "chevron-right",
};

export interface GamepadKeyProps extends HTMLAttributes<HTMLSpanElement> {
  button?: string;
  label?: string;
  size?: "sm" | "md" | "lg";
  pressed?: boolean;
  /** Painted inside a PadHint that already handles the click. */
  passive?: boolean;
  style?: CSSProperties;
}

export function GamepadKey({
  button = "a",
  label,
  size = "md",
  pressed,
  passive,
  style,
  onClick,
  ...rest
}: GamepadKeyProps) {
  const { action, fire } = useGlyphAction(button);
  const clickable = !passive && Boolean(action) && !onClick;
  const key = String(button).toLowerCase();
  const px = size === "sm" ? 18 : size === "lg" ? 28 : 22;
  const face = FACE[key];
  const dir = DIR[key];
  const color = face || "var(--pad-shoulder)";
  return (
    <span
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
      {...rest}
      onClick={onClick ?? (clickable ? fire : undefined)}
      onKeyDown={
        clickable
          ? (event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                fire();
              }
            }
          : rest.onKeyDown
      }
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-6)",
        fontFamily: "var(--font-core)",
        cursor: clickable ? "pointer" : undefined,
        ...style,
      }}
    >
      <span
        style={{
          width: face || dir ? px : "auto",
          height: px,
          minWidth: px,
          padding: face || dir ? 0 : "0 6px",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: face ? "var(--radius-pill)" : "var(--radius-sm)",
          border: `1px solid ${color}`,
          color: pressed ? "var(--black-1)" : color,
          background: pressed ? color : "var(--black-3)",
          boxShadow: pressed ? `0 0 8px ${color}` : "var(--sprite-shadow)",
          fontSize: size === "sm" ? "var(--text-2xs)" : "var(--text-xs)",
          fontWeight: "var(--weight-bold)" as CSSProperties["fontWeight"],
          letterSpacing: "var(--tracking-wide)",
          textTransform: "uppercase",
          transform: pressed ? "translate(1px,1px)" : "none",
          transition: "var(--transition-control)",
        }}
      >
        {dir ? <Icon name={dir} size={size === "sm" ? "xs" : "sm"} /> : String(button).toUpperCase()}
      </span>
      {label ? (
        <span
          style={{
            fontSize: "var(--text-2xs)",
            letterSpacing: "var(--tracking-caps)",
            textTransform: "uppercase",
            color: "var(--text-secondary)",
          }}
        >
          {label}
        </span>
      ) : null}
    </span>
  );
}
