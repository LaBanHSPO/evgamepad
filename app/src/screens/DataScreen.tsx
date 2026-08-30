import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { Badge, Button, GamepadKey, Input, MeterBar } from "../ds";

/**
 * Data — the prototype's `is_data` artboard.
 *
 * Restore states its preconditions before it will run, and the wipe needs a
 * typed sentence plus a two-second hold. Neither is a single click.
 */

const MANIFEST = [
  { name: "journal.sqlite", size: "412 MB", hash: "9f2a…c41d ok" },
  { name: "voice/ · 184 files", size: "1.2 GB", hash: "77be…0a19 ok" },
  { name: "tapes/ · 38 windows", size: "2.1 GB", hash: "c103…88f2 ok" },
  { name: "charts/ · 22 images", size: "96 MB", hash: "1de4…5b70 ok" },
];

const PRECONDITIONS = [
  { text: "session locked", ok: true },
  { text: "no open position", ok: true },
  { text: "1 transcription job running · finishes in 40s", ok: false },
];

const RESTORE_CHECK = [
  { label: "rows restored", value: "18 412 / 18 412" },
  { label: "attachment hashes", value: "244 / 244 match" },
];

const panel = {
  background: "var(--black-2)",
  padding: "18px 20px",
  display: "grid",
  gap: 16,
  alignContent: "start",
  minHeight: 0,
  overflow: "hidden",
} as const;

const well = {
  display: "grid",
  gap: 10,
  padding: 14,
  background: "var(--black-3)",
  border: "1px solid var(--line-hairline)",
} as const;

export function DataScreen() {
  return (
    <Artboard
      label="Data"
      frameStyle={{
        width: 1440,
        height: 860,
        display: "grid",
        gridTemplateRows: "44px 1fr 44px",
        background: "var(--surface-app)",
        border: "1px solid var(--line-hairline)",
      }}
    >
      <ScreenHeader
        title="Data"
        right={<Badge tone="neutral">One data job at a time</Badge>}
      >
        <Badge tone="warn" dot>
          Disk · 20 sessions left
        </Badge>
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: 10,
            letterSpacing: ".12em",
            color: "var(--text-muted)",
          }}
        >
          41.2 GB free · journal kept indefinitely
        </span>
      </ScreenHeader>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        {/* export + backup */}
        <div style={panel}>
          <div style={{ display: "grid", gap: 10 }}>
            <Caps size={10} weight={700} color="var(--phos-300)">
              Export
            </Caps>
            <div style={well}>
              <div style={{ display: "flex", gap: 6 }}>
                {["JSON", "CSV"].map((f) => {
                  const on = f === "JSON";
                  return (
                    <span
                      key={f}
                      style={{
                        padding: "6px 12px",
                        fontSize: 10,
                        fontWeight: 700,
                        letterSpacing: ".18em",
                        textTransform: "uppercase",
                        color: on ? "var(--phos-300)" : "var(--text-muted)",
                        border: `1px solid ${on ? "var(--line-strong)" : "var(--line-neutral)"}`,
                        background: on ? "var(--phos-a08)" : undefined,
                      }}
                    >
                      {f}
                    </span>
                  );
                })}
                <span
                  style={{
                    marginLeft: "auto",
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--text-muted)",
                    alignSelf: "center",
                  }}
                >
                  august 2026 · ~14 MB
                </span>
              </div>
              <span
                style={{
                  fontSize: 14,
                  lineHeight: 1.5,
                  color: "var(--text-body)",
                  maxWidth: "64ch",
                }}
              >
                Self-explaining: sessions, pre-session plans, per-trade grades, reviews, process
                scores, analyses, attachment metadata.
              </span>
              <div
                style={{
                  display: "grid",
                  gap: 4,
                  padding: 10,
                  background: "var(--surface-well)",
                  boxShadow: "var(--inset-well)",
                }}
              >
                <Term color="var(--phos-500)">
                  in the file: sessions · plans · grades · reviews · scores · attachment names
                </Term>
                <Term color="var(--arcade-red)">
                  never in the file: tokens · env values · server paths · raw config
                </Term>
              </div>
              <Button variant="secondary" size="md">
                Export JSON
              </Button>
            </div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
              <Caps size={10} weight={700} color="var(--phos-300)">
                Backup package
              </Caps>
              <Badge tone="info">Recent confirm required</Badge>
            </div>
            <div style={well}>
              <span style={{ fontSize: 14, lineHeight: 1.5, maxWidth: "64ch" }}>
                Last package built 2026-08-24 21:10 · 3.8 GB. Contains your voice recordings — that
                is why it does not sit behind a single click.
              </span>
              <div style={{ display: "grid", gap: 6 }}>
                <Caps>Manifest · checked without restoring</Caps>
                {MANIFEST.map((row, i) => (
                  <div
                    key={row.name}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 80px 130px",
                      gap: 8,
                      fontFamily: "var(--font-data)",
                      fontSize: 10,
                      color: "var(--text-secondary)",
                      borderBottom:
                        i === MANIFEST.length - 1 ? undefined : "1px solid var(--line-hairline)",
                      paddingBottom: i === MANIFEST.length - 1 ? undefined : 4,
                    }}
                  >
                    <span>{row.name}</span>
                    <span>{row.size}</span>
                    <span>{row.hash}</span>
                  </div>
                ))}
              </div>
              <Term color="var(--grey-500)">
                excluded on purpose: transcription models · docker images · caches · env · tokens.
              </Term>
              <div style={{ display: "flex", gap: 10 }}>
                <Button variant="secondary" size="md">
                  Build package
                </Button>
                <Button variant="ghost" size="md">
                  Verify manifest
                </Button>
              </div>
              <Term>no periodic backup reminder exists. this warning is disk space, not a streak.</Term>
            </div>
          </div>
        </div>

        {/* restore + wipe */}
        <div style={panel}>
          <div style={{ display: "grid", gap: 10 }}>
            <Caps size={10} weight={700} color="var(--phos-300)">
              Restore
            </Caps>
            <div style={well}>
              <Caps>Preconditions</Caps>
              <div style={{ display: "grid", gap: 6 }}>
                {PRECONDITIONS.map((p) => (
                  <div
                    key={p.text}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontFamily: "var(--font-data)",
                      fontSize: 11,
                      color: p.ok ? "var(--phos-300)" : "var(--arcade-yellow)",
                    }}
                  >
                    <i
                      style={{
                        width: 5,
                        height: 5,
                        borderRadius: 999,
                        background: p.ok ? "var(--phos-400)" : "var(--arcade-yellow)",
                        boxShadow: p.ok ? "0 0 6px var(--phos-400)" : undefined,
                      }}
                    />
                    {p.text}
                  </div>
                ))}
              </div>
              <Term>
                manifest, checksums, schema and archive paths are all checked before anything
                current is touched.
              </Term>
              <Term>a failure at any step leaves today&apos;s journal exactly as it is.</Term>
              <Button variant="secondary" size="md" disabled>
                Restore · waiting on 1 job
              </Button>
              <Caps size={10} color="var(--text-muted)">
                Only packages this product built are accepted
              </Caps>
            </div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <Caps size={10} weight={700} color="var(--phos-300)">
              Last restore check
            </Caps>
            <div style={{ ...well, gap: 6 }}>
              {RESTORE_CHECK.map((r) => (
                <div
                  key={r.label}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--text-secondary)",
                  }}
                >
                  <span>{r.label}</span>
                  <span style={{ color: "var(--phos-300)" }}>{r.value}</span>
                </div>
              ))}
              <Term color="var(--grey-500)">
                drill run 2026-07-02. numbers, not a &quot;success&quot; line.
              </Term>
            </div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <Caps size={10} weight={700} color="var(--arcade-red)">
              Wipe everything
            </Caps>
            <div
              style={{
                display: "grid",
                gap: 12,
                padding: 14,
                border: "1px solid var(--arcade-red-dim)",
                background: "rgba(232,32,42,.06)",
              }}
            >
              <span style={{ fontSize: 14, lineHeight: 1.5, maxWidth: "64ch" }}>
                Journal, voice, chart images and tapes are deleted and the space is reclaimed.
                Config, models, software and login remain, plus an audit row with no content in it.
              </span>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: 10,
                  background: "var(--black-3)",
                  border: "1px solid var(--line-hairline)",
                }}
              >
                <Caps size={10} color="var(--text-muted)">
                  Build a package first?
                </Caps>
                <Button variant="ghost" size="sm">
                  Build package
                </Button>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 10,
                    color: "var(--text-muted)",
                    marginLeft: "auto",
                  }}
                >
                  saves to ~/evgamepad/backups
                </span>
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                {/* typed sentence, then a two-second hold — deliberately not one click */}
                <Input
                  label="Type: delete everything permanently"
                  value="delete everything perman"
                />
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <Button variant="danger" size="md">
                    Hold 2s to wipe
                  </Button>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <MeterBar value={0} max={20} segments={10} tone="danger" />
                  </div>
                </div>
              </div>

              <Term color="var(--arcade-red)">
                after the final confirmation there is no hidden recovery copy.
              </Term>
              <Term>
                a package you already built lives outside this product — restoring an old one brings
                deleted data back.
              </Term>
            </div>
          </div>
        </div>
      </div>

      <ScreenFooter notice="no import path exists · demo only · not advice">
        <GamepadKey button="b" size="sm" label="Back" />
        <Caps size={10} color="var(--text-muted)">
          Every data action leaves a contentless audit row: action, time, counts
        </Caps>
      </ScreenFooter>
    </Artboard>
  );
}
