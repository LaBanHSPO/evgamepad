import { useState } from "react";
import type { CSSProperties, HTMLAttributes, MouseEvent, ReactNode } from "react";
import { Icon } from "./Icon";

/** Port of components/core/Tag.jsx. */

export interface TagProps extends Omit<HTMLAttributes<HTMLSpanElement>, "color"> {
  children?: ReactNode;
  onRemove?: (e: MouseEvent<HTMLButtonElement>) => void;
  color?: string;
  selected?: boolean;
  style?: CSSProperties;
}

export function Tag({
  children,
  onRemove,
  color = "var(--phos-400)",
  selected,
  onClick,
  style,
  ...rest
}: TagProps) {
  const [hover, setHover] = useState(false);
  return (
    <span
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-6)",
        height: 20,
        padding: "0 6px 0 5px",
        background: selected
          ? "var(--surface-selected)"
          : hover && onClick
            ? "var(--surface-hover)"
            : "transparent",
        border: "1px solid var(--line-hairline)",
        borderLeft: `2px solid ${color}`,
        color: selected ? "var(--phos-200)" : "var(--text-secondary)",
        fontFamily: "var(--font-core)",
        fontSize: "var(--text-2xs)",
        letterSpacing: "var(--tracking-wide)",
        textTransform: "uppercase",
        whiteSpace: "nowrap",
        cursor: onClick ? "pointer" : "default",
        transition: "var(--transition-control)",
        ...style,
      }}
      {...rest}
    >
      {children}
      {onRemove ? (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove(e);
          }}
          aria-label="Remove tag"
          style={{
            display: "inline-flex",
            background: "none",
            border: 0,
            padding: 0,
            color: "inherit",
            cursor: "pointer",
            opacity: 0.7,
          }}
        >
          <Icon name="x" size="xs" />
        </button>
      ) : null}
    </span>
  );
}
