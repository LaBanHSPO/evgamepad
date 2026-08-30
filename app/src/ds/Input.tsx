import { useId, useState } from "react";
import type { ChangeEventHandler, CSSProperties, ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

/** Port of components/forms/Input.jsx. */

export interface InputProps {
  label?: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  icon?: IconName;
  suffix?: ReactNode;
  size?: "sm" | "md" | "lg";
  align?: CSSProperties["textAlign"];
  value?: string;
  onChange?: ChangeEventHandler<HTMLInputElement>;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  type?: string;
  style?: CSSProperties;
  id?: string;
}

export function Input({
  label,
  hint,
  error,
  icon,
  suffix,
  size = "md",
  align = "left",
  value,
  onChange,
  placeholder,
  disabled,
  readOnly,
  type = "text",
  style,
  id,
}: InputProps) {
  const [focus, setFocus] = useState(false);
  const h =
    size === "sm"
      ? "var(--control-h-sm)"
      : size === "lg"
        ? "var(--control-h-lg)"
        : "var(--control-h-md)";
  const generatedId = useId();
  const inputId = id || generatedId;
  const borderColor = error
    ? "var(--arcade-red)"
    : focus
      ? "var(--phos-400)"
      : "var(--line-hairline)";
  return (
    <div
      style={{
        display: "grid",
        gap: "var(--space-6)",
        fontFamily: "var(--font-core)",
        minWidth: 0,
        ...style,
      }}
    >
      {label ? (
        <label
          htmlFor={inputId}
          style={{
            fontSize: "var(--text-2xs)",
            letterSpacing: "var(--tracking-caps)",
            textTransform: "uppercase",
            color: "var(--text-muted)",
          }}
        >
          {label}
        </label>
      ) : null}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-8)",
          height: h,
          minWidth: 0,
          padding: "0 var(--space-8)",
          background: "var(--surface-well)",
          border: `1px solid ${borderColor}`,
          borderRadius: "var(--radius-none)",
          boxShadow: focus ? "var(--glow-sm)" : "var(--inset-well)",
          opacity: disabled ? 0.5 : 1,
          transition: "var(--transition-control)",
        }}
      >
        {icon ? (
          <Icon
            name={icon}
            size="sm"
            style={{ color: focus ? "var(--phos-400)" : "var(--text-muted)" }}
          />
        ) : null}
        <input
          id={inputId}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          // Screens render fixed values, so the field has no handler.
          readOnly={readOnly ?? !onChange}
          size={1}
          onFocus={() => setFocus(true)}
          onBlur={() => setFocus(false)}
          style={{
            flex: 1,
            minWidth: 0,
            width: "100%",
            background: "transparent",
            border: 0,
            outline: "none",
            color: "var(--text-body)",
            fontFamily: "var(--font-data)",
            fontSize: size === "sm" ? "var(--text-xs)" : "var(--text-sm)",
            textAlign: align,
            fontVariantNumeric: "tabular-nums",
          }}
        />
        {suffix ? (
          <span
            style={{
              fontSize: "var(--text-2xs)",
              color: "var(--text-muted)",
              letterSpacing: "var(--tracking-wide)",
              textTransform: "uppercase",
            }}
          >
            {suffix}
          </span>
        ) : null}
      </div>
      {error || hint ? (
        <span
          style={{
            fontSize: "var(--text-2xs)",
            color: error ? "var(--arcade-red)" : "var(--text-muted)",
          }}
        >
          {error || hint}
        </span>
      ) : null}
    </div>
  );
}
