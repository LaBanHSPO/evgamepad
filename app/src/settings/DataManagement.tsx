import { useCallback, useEffect, useState } from "react";
import type { CSSProperties } from "react";
import type { ArchiveSummary, BackupRow } from "./types";
import { bytes } from "./types";
import { apiUrl } from "../net/gateway";

/**
 * Backup, restore, export, and the one that cannot be undone.
 *
 * The delete gate is four separate conditions — the exact phrase, a two-second hold, a locked
 * session, and no open position — and the gateway enforces every one of them again. This panel is
 * the *first* of two checks, never the only one.
 *
 * A backup is offered before the delete and never taken after it. A hidden recovery copy made
 * after the final confirmation would not be a safety net; it would be a lie about what the word
 * means.
 */

const PHRASE = "DELETE EVERYTHING";
const HOLD_MS = 2000;

export function DataManagement(): JSX.Element {
  const [backups, setBackups] = useState<BackupRow[]>([]);
  const [summary, setSummary] = useState<ArchiveSummary | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [phrase, setPhrase] = useState("");
  const [heldSince, setHeldSince] = useState<number | null>(null);
  const [held, setHeld] = useState(0);

  const load = useCallback(() => {
    void fetch(apiUrl("/api/data/backups"))
      .then((response) => response.json())
      .then((body) => setBackups(body.backups as BackupRow[]))
      .catch(() => undefined);
  }, []);

  useEffect(load, [load]);

  // The hold is a real elapsed measurement, not a timer that fires once — letting go resets it.
  useEffect(() => {
    if (heldSince === null) return;
    const timer = setInterval(() => setHeld(Date.now() - heldSince), 50);
    return () => clearInterval(timer);
  }, [heldSince]);

  const call = useCallback(async (path: string, init?: RequestInit) => {
    setBusy(true);
    setStatus(null);
    try {
      const response = await fetch(apiUrl(path), init);
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        setStatus(body.detail ?? `that was refused (${response.status})`);
        return null;
      }
      return body;
    } finally {
      setBusy(false);
    }
  }, []);

  const makeBackup = useCallback(async () => {
    const body = await call("/api/data/backup", { method: "POST" });
    if (body) {
      setStatus(`backed up ${body.files} files · ${bytes(body.bytes)}`);
      load();
    }
  }, [call, load]);

  const inspect = useCallback(async (name: string) => {
    setSelected(name);
    const body = await call("/api/data/restore/inspect", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ name }),
    });
    setSummary(body as ArchiveSummary | null);
  }, [call]);

  const doRestore = useCallback(async () => {
    if (selected === null) return;
    const body = await call("/api/data/restore", {
      method: "POST", headers: { "content-type": "application/json" },
      // The gateway checks these again; sending them is a declaration, not the authority.
      body: JSON.stringify({ name: selected, locked: true, positionsOpen: 0, jobsRunning: 0 }),
    });
    if (body) setStatus(`restored ${body.files} files from ${new Date(body.restoredFrom).toLocaleString()}`);
  }, [call, selected]);

  const doDelete = useCallback(async () => {
    const body = await call("/api/data/all", {
      method: "DELETE", headers: { "content-type": "application/json" },
      body: JSON.stringify({ phrase, heldMs: held, locked: true, positionsOpen: 0 }),
    });
    if (body) {
      setStatus(`deleted ${body.rows} rows and ${body.files} files`);
      setPhrase("");
      setHeldSince(null);
      setHeld(0);
      load();
    }
  }, [call, phrase, held, load]);

  const armed = phrase === PHRASE && held >= HOLD_MS;

  return (
    <>
      <section style={panel}>
        <h2 style={heading}>Export</h2>
        <div style={{ display: "flex", gap: 10 }}>
          <a href={apiUrl("/api/export/trades.csv")} download style={link}>trades.csv</a>
          <a href={apiUrl("/api/export/journal.json")} download style={link}>journal.json</a>
        </div>
        <p style={note}>
          Your trades and your own words. No credentials, no server paths, and no import path back
          in — this journal describes what this gateway executed.
        </p>
      </section>

      <section style={panel}>
        <h2 style={heading}>Backup</h2>
        <div>
          <button type="button" disabled={busy} onClick={() => void makeBackup()}>
            back up now
          </button>
        </div>
        <p style={note}>
          The journal, your screenshots, your memos and the trade tapes. Not the broker tokens and
          not the speech models — one is a secret, the other is replaceable.
        </p>

        {backups.length === 0 ? <p style={note}>no backups yet</p> : (
          <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12 }}>
            {backups.map((backup) => (
              <li key={backup.name} style={{ display: "flex", gap: 10, alignItems: "center",
                                             padding: "3px 0" }}>
                <span style={{ flex: 1 }}>{backup.name}</span>
                <span style={{ opacity: 0.7 }}>{bytes(backup.bytes)}</span>
                <a href={apiUrl(`/api/data/backups/${encodeURIComponent(backup.name)}`)} download
                   style={link}>download</a>
                <button type="button" onClick={() => void inspect(backup.name)}>inspect</button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {summary ? (
        <section style={panel}>
          <h2 style={heading}>Restore</h2>
          <p style={{ margin: 0, fontSize: 13 }}>
            {selected} · {summary.files} files · taken{" "}
            {new Date(summary.createdAt).toLocaleString()}
          </p>
          <p style={note}>
            Every checksum is verified and the copy is staged before anything is swapped. A failure
            leaves your current journal exactly as it is. Lock the session first.
          </p>
          <div>
            <button type="button" disabled={busy} onClick={() => void doRestore()}>
              restore this backup
            </button>
          </div>
        </section>
      ) : null}

      <section style={{ ...panel, borderColor: "var(--arcade-red)" }}>
        <h2 style={heading}>Delete everything</h2>
        <p style={note}>
          Every trade, memo, screenshot, tape and note. Your settings, the app and the broker
          connection stay. This cannot be undone, and nothing is copied aside afterwards — take a
          backup first if you want one.
        </p>
        <label style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13 }}>
          <span style={{ opacity: 0.7, fontSize: 11 }}>type {PHRASE}</span>
          <input value={phrase} onChange={(e) => setPhrase(e.target.value)} />
        </label>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <button
            type="button"
            disabled={busy || phrase !== PHRASE}
            onMouseDown={() => setHeldSince(Date.now())}
            onMouseUp={() => { if (armed) void doDelete(); setHeldSince(null); setHeld(0); }}
            onMouseLeave={() => { setHeldSince(null); setHeld(0); }}
            style={{ ...plainButton, borderColor: armed ? "var(--arcade-red)" : undefined }}
          >
            hold to delete
          </button>
          <span style={{ fontSize: 12, opacity: 0.7 }}>
            {heldSince === null ? `hold for ${HOLD_MS / 1000}s`
                                : `${Math.min(HOLD_MS, held) / 1000}s`}
          </span>
        </div>
      </section>

      {status ? <p style={{ margin: 0, fontSize: 13 }}>{status}</p> : null}
    </>
  );
}

const panel: CSSProperties = {
  display: "flex", flexDirection: "column", gap: 10, padding: 14,
  border: "var(--border-hairline)", background: "var(--black-2)",
};
const heading: CSSProperties = { margin: 0, fontSize: 14, letterSpacing: "0.08em" };
const note: CSSProperties = { margin: 0, opacity: 0.75, fontSize: 12, maxWidth: 640 };
const link: CSSProperties = { color: "var(--phos-200)" };
const plainButton: CSSProperties = {
  background: "transparent", color: "inherit", border: "var(--border-hairline)",
  padding: "4px 12px", cursor: "pointer",
};
