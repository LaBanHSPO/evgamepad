import { useState } from "react";
import type { ButtonHTMLAttributes, CSSProperties, ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

/** Port of components/core/Button.jsx. */

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "arcade";
export type ControlSize = "sm" | "md" | "lg";

const HEIGHTS: Record<ControlSize, string> = {
  sm: "var(--control-h-sm)",
  md: "var(--control-h-md)",
  lg: "var(--control-h-lg)",
};

const FONTS: Record<ControlSize, string> = {
  sm: "var(--text-xs)",
  md: "var(--text-sm)",
  lg: "var(--text-md)",
};

const VARIANTS: Record<ButtonVariant, { base: CSSProperties; hover: CSSProperties }> = {
  primary: {
    base: {
      background: "var(--phos-400)",
      color: "var(--text-inverse)",
      border: "1px solid var(--phos-400)",
      boxShadow: "var(--glow-sm)",
    },
    hover: {
      background: "var(--phos-300)",
      borderColor: "var(--phos-300)",
      boxShadow: "var(--glow-md)",
    },
  },
  secondary: {
    base: {
      background: "transparent",
      color: "var(--phos-300)",
      border: "1px solid var(--line-strong)",
    },
    hover: {
      background: "var(--phos-a16)",
      borderColor: "var(--phos-400)",
      color: "var(--phos-200)",
    },
  },
  ghost: {
    base: {
      background: "transparent",
      color: "var(--text-secondary)",
      border: "1px solid transparent",
    },
    hover: { background: "var(--surface-hover)", color: "var(--phos-300)" },
  },
  danger: {
    base: {
      background: "transparent",
      color: "var(--arcade-red)",
      border: "1px solid var(--arcade-red-dim)",
    },
    hover: {
      background: "rgba(232,32,42,.16)",
      borderColor: "var(--arcade-red)",
      boxShadow: "var(--glow-red)",
    },
  },
  arcade: {
    base: {
      background: "var(--arcade-red)",
      color: "#fff",
      border: "1px solid var(--black-0)",
      boxShadow: "var(--sprite-shadow)",
      fontFamily: "var(--font-display)",
      letterSpacing: 0,
    },
    hover: { background: "var(--arcade-orange)" },
  },
};

export interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "type"> {
  variant?: ButtonVariant;
  size?: ControlSize;
  icon?: IconName;
  iconAfter?: IconName;
  fullWidth?: boolean;
  children?: ReactNode;
  type?: "button" | "submit" | "reset";
}

export function Button({
  variant = "primary",
  size = "md",
  icon,
  iconAfter,
  disabled,
  fullWidth,
  children,
  style,
  onClick,
  type = "button",
  ...rest
}: ButtonProps) {
  const [hover, setHover] = useState(false);
  const [down, setDown] = useState(false);
  const v = VARIANTS[variant] || VARIANTS.primary;
  const s: CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "var(--space-8)",
    height: HEIGHTS[size],
    padding: `0 ${size === "sm" ? 8 : 14}px`,
    width: fullWidth ? "100%" : undefined,
    fontFamily: variant === "arcade" ? "var(--font-display)" : "var(--font-core)",
    fontSize: variant === "arcade" ? "var(--display-sm)" : FONTS[size],
    fontWeight: (variant === "arcade" ? 400 : "var(--weight-bold)") as CSSProperties["fontWeight"],
    letterSpacing: variant === "arcade" ? 0 : "var(--tracking-wide)",
    textTransform: "uppercase",
    borderRadius: "var(--radius-none)",
    cursor: disabled ? "not-allowed" : "pointer",
    whiteSpace: "nowrap",
    transition: "var(--transition-control)",
    transform: down && !disabled ? "translate(1px,1px)" : "none",
    ...v.base,
    ...(hover && !disabled ? v.hover : null),
    ...(disabled
      ? {
          background: "var(--black-3)",
          color: "var(--text-disabled)",
          borderColor: "var(--line-neutral)",
          boxShadow: "none",
        }
      : null),
    ...style,
  };
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      style={s}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => {
        setHover(false);
        setDown(false);
      }}
      onMouseDown={() => setDown(true)}
      onMouseUp={() => setDown(false)}
      {...rest}
    >
      {icon ? <Icon name={icon} size={size === "lg" ? "md" : "sm"} /> : null}
      {children}
      {iconAfter ? <Icon name={iconAfter} size={size === "lg" ? "md" : "sm"} /> : null}
    </button>
  );
}
