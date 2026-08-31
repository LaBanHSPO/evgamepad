import { useCallback, useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { DataManagement } from "./DataManagement";
import type { SettingsView } from "./types";

/**
 * `/settings` — preferences, and nothing that could become a safety decision.
 *
 * The form is generated from the **server's** schema rather than from a list written here, which
 * is what makes the boundary real: there is no control on this page for demo/live mode, the bind
 * address, the broker credentials, or any of the three boot-fails, because the gateway does not
 * offer them and would refuse the write if it did.
 *
 * The account is a chip. Adding a second one is not a missing feature — the entire safety story is
 * "one demo account, one set of caps".
 *
 * Dark only, desktop only. Both are product boundaries, not omissions.
 */

const GROUPS: { prefix: string; title: string }[] = [
  { prefix: "symbols.", title: "Symbols" },
  { prefix: "chart.", title: "Charts" },
  { prefix: "evening.", title: "The evening" },
  { prefix: "pad.", title: "Gamepad" },
  { prefix: "voice.", title: "Voice" },
  { prefix: "coach.", title: "Coach" },
  { prefix: "journal.", title: "Journal" },
  { prefix: "report.", title: "Reports" },
];

export function Settings(): JSX.Element {
  const [view, setView] = useState<SettingsView | null>(null);
  const [draft, setDraft] = useState<Record<string, unknown>>({});
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const load = useCallback(() => {
    void fetch("/api/settings")
      .then((response) => response.json())
      .then((body: SettingsView) => {
        setView(body);
        setDraft(body.settings);
      })
      .catch(() => setError("could not load settings"));
  }, []);

  useEffect(load, [load]);

  const save = useCallback(async () => {
    setError(null);
    const response = await fetch("/api/settings", {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(draft),
    });
    if (!response.ok) {
      // The gateway's refusal is the message: it names the key and why.
      setError((await response.json().catch(() => ({}))).detail ?? "that change was refused");
      return;
    }
    setDraft((await response.json()).settings);
    setSaved(true);
  }, [draft]);

  if (view === null) return <main style={shell}><p>{error ?? "loading settings…"}</p></main>;

  const set = (key: string, value: unknown) => {
    setSaved(false);
    setDraft((existing) => ({ ...existing, [key]: value }));
  };

  return (
    <main style={shell}>
      <header style={row}>
        <strong>SETTINGS</strong>
        <span style={chip}>
          {view.account.broker} · {view.account.platform} · {view.account.mode}
        </span>
      </header>

      <p style={note}>
        One configured account, set on the server. Trading mode, the broker connection and the
        safety limits are not editable here — they are boot-fails in the gateway's own config.
      </p>

      {GROUPS.map((group) => {
        const entries = view.schema.filter((entry) => entry.key.startsWith(group.prefix));
        if (entries.length === 0) return null;
        return (
          <section key={group.prefix} style={panel}>
            <h2 style={heading}>{group.title}</h2>
            {entries.map((entry) => (
              <Field
                key={entry.key}
                label={entry.describe}
                value={draft[entry.key]}
                symbols={view.symbols}
                settingKey={entry.key}
                onChange={(value) => set(entry.key, value)}
              />
            ))}
          </section>
        );
      })}

      <section style={panel}>
        <h2 style={heading}>Elsewhere</h2>
        {/* Linked, never duplicated: two places to define a rule is one too many. */}
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
          {view.elsewhere.map((entry) => <li key={entry.where}>{entry.what}</li>)}
        </ul>
      </section>

      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <button type="button" onClick={() => void save()}>save</button>
        {saved ? <span style={{ opacity: 0.7, fontSize: 12 }}>saved</span> : null}
        {error ? <span style={{ color: "var(--arcade-red)", fontSize: 12 }}>{error}</span> : null}
      </div>

      <DataManagement />
    </main>
  );
}

function Field({ label, value, onChange, settingKey, symbols }: {
  label: string;
  value: unknown;
  onChange: (next: unknown) => void;
  settingKey: string;
  symbols: string[];
}): JSX.Element {
  if (typeof value === "boolean") {
    return (
      <label style={fieldRow}>
        <input type="checkbox" checked={value} onChange={(e) => onChange(e.target.checked)} />
        <span>{label}</span>
      </label>
    );
  }

  if (Array.isArray(value)) {
    const options = settingKey === "symbols.enabled" ? symbols : null;
    if (options) {
      return (
        <div style={fieldRow}>
          <span style={{ width: 260 }}>{label}</span>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {options.map((option) => {
              const on = (value as string[]).includes(option);
              return (
                <button
                  key={option}
                  type="button"
                  onClick={() => onChange(on
                    ? (value as string[]).filter((v) => v !== option)
                    : [...(value as string[]), option])}
                  style={on ? activeButton : plainButton}
                >
                  {option}
                </button>
              );
            })}
          </div>
        </div>
      );
    }
    return (
      <label style={fieldRow}>
        <span style={{ width: 260 }}>{label}</span>
        <input value={(value as unknown[]).join(", ")}
               onChange={(e) => onChange(parseList(e.target.value, value as unknown[]))} />
      </label>
    );
  }

  return (
    <label style={fieldRow}>
      <span style={{ width: 260 }}>{label}</span>
      <input
        value={String(value ?? "")}
        onChange={(e) => onChange(
          typeof value === "number" ? Number(e.target.value) : e.target.value,
        )}
      />
    </label>
  );
}

/** Keeps a list of numbers numeric, so weekdays do not silently become strings. */
function parseList(raw: string, previous: unknown[]): unknown[] {
  const parts = raw.split(",").map((part) => part.trim()).filter(Boolean);
  return typeof previous[0] === "number" ? parts.map(Number) : parts;
}

const shell: CSSProperties = {
  display: "flex", flexDirection: "column", gap: 14, padding: 16, minHeight: "100%",
  background: "var(--black-1)", color: "var(--phos-300)", fontFamily: "var(--font-core)",
};
const row: CSSProperties = { display: "flex", gap: 12, alignItems: "center" };
const panel: CSSProperties = {
  display: "flex", flexDirection: "column", gap: 8, padding: 14,
  border: "var(--border-hairline)", background: "var(--black-2)",
};
const heading: CSSProperties = { margin: 0, fontSize: 14, letterSpacing: "0.08em" };
const fieldRow: CSSProperties = { display: "flex", gap: 12, alignItems: "center", fontSize: 13 };
const note: CSSProperties = { margin: 0, opacity: 0.75, fontSize: 12, maxWidth: 640 };
const chip: CSSProperties = {
  marginLeft: "auto", opacity: 0.75, fontSize: 12, border: "var(--border-hairline)",
  padding: "3px 10px",
};
const plainButton: CSSProperties = {
  background: "transparent", color: "inherit", border: "var(--border-hairline)",
  padding: "3px 10px", cursor: "pointer", fontSize: 12,
};
const activeButton: CSSProperties = {
  ...plainButton, background: "var(--black-3)", color: "var(--phos-200)",
  borderColor: "var(--phos-400)",
};
