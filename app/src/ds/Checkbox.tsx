import { useId } from "react";
import type { ChangeEventHandler, CSSProperties, ReactNode } from "react";
import { Icon } from "./Icon";

/** Port of components/forms/Checkbox.jsx. */

export interface CheckboxProps {
  label?: ReactNode;
  checked?: boolean;
  onChange?: ChangeEventHandler<HTMLInputElement>;
  disabled?: boolean;
  description?: ReactNode;
  style?: CSSProperties;
  id?: string;
}

export function Checkbox({
  label,
  checked,
  onChange,
  disabled,
  description,
  style,
  id,
}: CheckboxProps) {
  const generatedId = useId();
  const boxId = id || generatedId;
  return (
    <label
      htmlFor={boxId}
      style={{
        display: "inline-flex",
        alignItems: description ? "flex-start" : "center",
        gap: "var(--space-8)",
        fontFamily: "var(--font-core)",
        fontSize: "var(--text-sm)",
        color: disabled ? "var(--text-disabled)" : "var(--text-body)",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.6 : 1,
        ...style,
      }}
    >
      <input
        id={boxId}
        type="checkbox"
        checked={!!checked}
        onChange={onChange}
        // Screens render fixed state, so the input has no handler.
        readOnly={!onChange}
        disabled={disabled}
        style={{ position: "absolute", opacity: 0, width: 0, height: 0 }}
      />
      <span
        style={{
          width: 14,
          height: 14,
          flex: "0 0 14px",
          marginTop: description ? 2 : 0,
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          background: checked ? "var(--phos-400)" : "var(--surface-well)",
          border: `1px solid ${checked ? "var(--phos-400)" : "var(--line-strong)"}`,
          boxShadow: checked ? "var(--glow-xs)" : "none",
          color: "var(--black-1)",
          transition: "var(--transition-control)",
        }}
      >
        {checked ? <Icon name="check" size={10} /> : null}
      </span>
      <span style={{ display: "grid", gap: 2 }}>
        <span>{label}</span>
        {description ? (
          <span style={{ fontSize: "var(--text-2xs)", color: "var(--text-muted)" }}>
            {description}
          </span>
        ) : null}
      </span>
    </label>
  );
}
