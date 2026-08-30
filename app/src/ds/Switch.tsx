import { useId } from "react";
import type { ChangeEventHandler, CSSProperties } from "react";

/** Port of components/forms/Switch.jsx. */

export interface SwitchProps {
  label?: string;
  checked?: boolean;
  onChange?: ChangeEventHandler<HTMLInputElement>;
  disabled?: boolean;
  size?: "sm" | "md";
  style?: CSSProperties;
  id?: string;
}

export function Switch({
  label,
  checked,
  onChange,
  disabled,
  size = "md",
  style,
  id,
}: SwitchProps) {
  const generatedId = useId();
  const swId = id || generatedId;
  const w = size === "sm" ? 26 : 34;
  const h = size === "sm" ? 14 : 18;
  const knob = h - 6;
  return (
    <label
      htmlFor={swId}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-8)",
        fontFamily: "var(--font-core)",
        fontSize: "var(--text-sm)",
        color: "var(--text-body)",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.6 : 1,
        ...style,
      }}
    >
      <input
        id={swId}
        type="checkbox"
        role="switch"
        checked={!!checked}
        onChange={onChange}
        // The arcade screens render fixed state, so the input has no handler.
        readOnly={!onChange}
        disabled={disabled}
        style={{ position: "absolute", opacity: 0, width: 0, height: 0 }}
      />
      <span
        style={{
          position: "relative",
          width: w,
          height: h,
          flex: `0 0 ${w}px`,
          background: checked ? "var(--phos-a32)" : "var(--surface-well)",
          border: `1px solid ${checked ? "var(--phos-400)" : "var(--line-strong)"}`,
          boxShadow: checked ? "var(--glow-xs)" : "none",
          transition: "var(--transition-control)",
        }}
      >
        <i
          style={{
            position: "absolute",
            top: 2,
            left: checked ? w - knob - 4 : 2,
            width: knob,
            height: knob,
            background: checked ? "var(--phos-400)" : "var(--grey-500)",
            transition:
              "left var(--dur-fast) var(--ease-step-2), background-color var(--dur-fast) linear",
          }}
        />
      </span>
      {label ? <span>{label}</span> : null}
    </label>
  );
}
