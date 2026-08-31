import { useCallback, useEffect, useState } from "react";
import type { CSSProperties } from "react";
import type { SystemView } from "./types";

/**
 * How you trade, in your own words.
 *
 * Deliberately one document rather than a log: this is a statement you revise, not a stream you
 * accumulate. The setup library lives in `/playbooks` and is phase 7's — this page links to it
 * rather than duplicating it, so there is exactly one place a rule is defined.
 *
 * Everything on this page is player text and is rendered as a text child. Nothing here is ever
 * emitted as markup, and no model writes a word of it.
 */

export function SystemPrinciples(): JSX.Element {
  const [view, setView] = useState<SystemView | null>(null);
  const [philosophy, setPhilosophy] = useState("");
  const [principles, setPrinciples] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    void fetch("/api/journal/system")
      .then((response) => response.json())
      .then((body: SystemView) => {
        setView(body);
        setPhilosophy(body.philosophy ?? "");
        setPrinciples(body.principles.join("\n"));
      })
      .catch(() => undefined);
  }, []);

  const save = useCallback(async () => {
    const body = {
      philosophy,
      principles: principles.split("\n").map((line) => line.trim()).filter(Boolean),
      focusCode: view?.focusCode ?? null,
    };
    const response = await fetch("/api/journal/system", {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (response.ok) {
      setView((await response.json()) as SystemView);
      setSaved(true);
    }
  }, [philosophy, principles, view]);

  return (
    <section style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 720 }}>
      <h2 style={heading}>System</h2>

      <label style={field}>
        <span style={caption}>Trading philosophy</span>
        <textarea rows={5} value={philosophy}
                  onChange={(e) => { setPhilosophy(e.target.value); setSaved(false); }} />
      </label>

      <label style={field}>
        <span style={caption}>Core principles — one per line</span>
        <textarea rows={8} value={principles}
                  onChange={(e) => { setPrinciples(e.target.value); setSaved(false); }} />
      </label>

      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <button type="button" onClick={() => void save()}>save</button>
        {saved ? <span style={{ opacity: 0.7, fontSize: 12 }}>saved</span> : null}
      </div>

      {view?.principles.length ? (
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, opacity: 0.85 }}>
          {/* Text children: the player's own words, never markup. */}
          {view.principles.map((line, index) => <li key={`${line}-${index}`}>{line}</li>)}
        </ul>
      ) : null}

      <p style={note}>
        Setups live in the playbook library, not here — one place per rule.
      </p>
    </section>
  );
}

const heading: CSSProperties = { margin: 0, fontSize: 14, letterSpacing: "0.08em" };
const field: CSSProperties = { display: "flex", flexDirection: "column", gap: 4 };
const caption: CSSProperties = { opacity: 0.7, fontSize: 11 };
const note: CSSProperties = { margin: 0, opacity: 0.7, fontSize: 12 };
