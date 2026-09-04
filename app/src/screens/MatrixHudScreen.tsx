import type { ReactNode } from "react";
import { ConnectStrip } from "../arcade/ConnectStrip";
import {
  DASH,
  dash,
  formatPrice,
  padScore,
  progressToTarget,
  shortSymbol,
} from "../arcade/format";
import { useArcadeRuntime } from "../arcade/useArcadeRuntime";
import { CodeRain } from "../components/CodeRain";
import { Artboard, Caps, DemoNotice, PadHint, Term } from "../components/primitives";
import { Icon, MeterBar, PnLValue, Switch, type IconName } from "../ds";
import { MATRIX_ART } from "./art";

/** HUD on matrix art — live `/api/arcade` figures on the prototype artboard. */

function SectionLabel({
  icon,
  children,
  center,
}: {
  icon: IconName;
  children: ReactNode;
  center?: boolean;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: center ? "center" : undefined,
        gap: 7,
        color: "var(--phos-500)",
      }}
    >
      <Icon name={icon} size="xs" />
      <Caps color="inherit">{children}</Caps>
    </div>
  );
}

export function MatrixHudScreen() {
  const rt = useArcadeRuntime("matrix");
  const selected = rt.selected;
  const positions = rt.hud?.positions ?? [];
  const first = positions[0];
  const rUsd = rt.hud?.risk.rUsd ?? 20;
  const dayPnl = rt.hud?.pnl.dayPnl;
  const dayR = dayPnl == null ? null : dayPnl / rUsd;
  const sizeUsed = positions.reduce((sum, row) => sum + (row.lots ?? 0), 0);
  const sizeMax = selected?.maxLots ?? 1;
  const lossMax = rt.hud?.risk.maxDayLossUsd ?? 0;
  const lossUsed = dayPnl == null || dayPnl >= 0 ? 0 : Math.min(lossMax, -dayPnl);
  const others = (rt.hud?.symbols ?? []).filter((row) => row.name !== selected?.name);
  const readyLabel = rt.view?.phase ?? (rt.online ? "SAFE" : "OFFLINE");
  const setup = rt.hud?.sentinel?.setup ?? "waiting on tape";
  const incoming = rt.hud?.sentinel?.nextEvent;

  return (
    <Artboard
      label="HUD on matrix art"
      frameStyle={{
        width: 1440,
        height: 810,
        display: "grid",
        gridTemplateRows: "56px 1fr 64px",
        background: `#040604 url('${rt.artUrl || MATRIX_ART}') center/cover no-repeat`,
        border: "1px solid var(--line-strong)",
        boxShadow: "var(--glow-md)",
        position: "relative",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: 26,
          padding: "0 20px",
          borderBottom: "1px solid var(--line-strong)",
          background: "var(--black-2)",
          position: "relative",
          zIndex: 2,
        }}
      >
        <div style={{ display: "grid", gap: 3 }}>
          <Caps color="var(--phos-500)">1P stood down</Caps>
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 16,
              color: "var(--phos-400)",
              textShadow: "var(--glow-text)",
            }}
          >
            {padScore(rt.standDowns)}
          </span>
        </div>
        <div style={{ display: "grid", gap: 3 }}>
          <Caps color="var(--text-muted)">HI</Caps>
          <span style={{ fontFamily: "var(--font-display)", fontSize: 16, color: "var(--grey-300)" }}>
            {padScore(rt.hiScore)}
          </span>
        </div>
        <div style={{ display: "grid", gap: 5 }}>
          <Caps color="var(--text-muted)">
            Arms left · positions {rt.positionsOpen} of {rt.maxPositions}
          </Caps>
          <div style={{ display: "flex", gap: 5 }}>
            {rt.slots.map((lit, i) => (
              <i
                key={i}
                style={{
                  width: 11,
                  height: 11,
                  background: lit ? "var(--phos-400)" : "var(--black-5)",
                  boxShadow: lit ? "var(--glow-xs)" : undefined,
                  border: lit ? undefined : "1px solid var(--line-neutral)",
                }}
              />
            ))}
          </div>
        </div>
        <div style={{ display: "grid", gap: 3 }}>
          <Caps color="var(--text-muted)">Session ends</Caps>
          <span
            style={{
              fontFamily: "var(--font-data)",
              fontSize: 16,
              fontWeight: 700,
              color: "var(--arcade-yellow)",
            }}
          >
            {rt.clock}
          </span>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <ConnectStrip runtime={rt} />
        </div>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "300px 1fr 320px",
          minHeight: 0,
          position: "relative",
        }}
      >
        <div style={{ position: "absolute", inset: 0, zIndex: 0, overflow: "hidden" }}>
          <CodeRain opacity={0.12} fontSize={15} />
        </div>

        <aside
          style={{
            position: "relative",
            zIndex: 1,
            borderRight: "1px solid var(--line-strong)",
            background: "rgba(8,12,8,.92)",
            display: "grid",
            gridTemplateRows: "auto auto 1fr",
            minHeight: 0,
          }}
        >
          <div
            style={{
              padding: "16px 18px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 12,
            }}
          >
            <SectionLabel icon="shield">Player limits · gateway enforced</SectionLabel>
            <MeterBar
              label={dayPnl == null ? "Loss meter · waiting on broker" : "Loss meter"}
              value={lossUsed}
              max={lossMax || 1}
              segments={10}
              tone="warn"
              showValue={dayPnl != null}
            />
            <MeterBar
              label="Size used"
              value={sizeUsed}
              max={sizeMax || 1}
              segments={10}
            />
            <MeterBar
              label="Window burned"
              value={rt.hud?.session.windowBurnedPct ?? 0}
              max={100}
              segments={10}
              tone="info"
            />
          </div>

          <div
            style={{
              padding: "16px 18px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 10,
            }}
          >
            <SectionLabel icon="gamepad-2">Instrument · d-pad</SectionLabel>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                height: 34,
                padding: "0 12px",
                border: "1px solid var(--line-strong)",
                background: "var(--phos-a08)",
                boxShadow: "var(--glow-xs)",
              }}
            >
              <span
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: 12,
                  color: "var(--phos-400)",
                }}
              >
                {selected?.name ?? "XAUUSD"}
              </span>
              <span style={{ fontFamily: "var(--font-data)", fontSize: 12, color: "var(--phos-200)" }}>
                {rt.view ? rt.view.lots.toFixed(2) : rt.lotsText}
              </span>
            </div>
            {others.map((row) => {
              const open = positions.filter((pos) => pos.symbol === row.name);
              const size =
                open.length === 0
                  ? DASH
                  : open.some((pos) => pos.lots != null)
                    ? `${open.reduce((sum, pos) => sum + (pos.lots ?? 0), 0).toFixed(2)} open`
                    : "open";
              return (
                <div
                  key={row.name}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: open.length ? "var(--text-muted)" : "var(--text-disabled)",
                    padding: "0 2px",
                  }}
                >
                  <span>{row.name}</span>
                  <span>{size}</span>
                </div>
              );
            })}
          </div>

          <div
            style={{
              padding: "16px 18px",
              display: "grid",
              gap: 8,
              alignContent: "start",
              background: "rgba(4,6,4,.7)",
              backgroundImage: "var(--veil-scanline)",
            }}
          >
            <SectionLabel icon="terminal">Session log</SectionLabel>
            {rt.log.length === 0 ? (
              <>
                <Term color="var(--phos-400)">
                  {rt.online ? "arcade hud live · quotes from the book" : "gateway unreachable · art fallback"}
                </Term>
                <Term color="var(--phos-500)">
                  broker {rt.hud?.broker.connected ? "up" : dash(rt.hud?.broker.reason ?? "waiting")}
                </Term>
                <Term color="var(--status-agent)">
                  {rt.hud?.sentinel
                    ? `sentinel ${rt.hud.sentinel.qualityBand ?? rt.hud.sentinel.state}`
                    : "sentinel waiting on a quote"}
                </Term>
              </>
            ) : (
              rt.log.slice(0, 4).map((line) => (
                <Term key={line} color="var(--phos-400)">
                  {line}
                </Term>
              ))
            )}
          </div>
        </aside>

        <section
          style={{
            position: "relative",
            zIndex: 1,
            display: "grid",
            gridTemplateRows: "auto 1fr",
            minHeight: 0,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              gap: 20,
              padding: "16px 20px",
              background: "rgba(4,6,4,.92)",
              borderBottom: "1px solid var(--line-strong)",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-data)",
                fontSize: 64,
                fontWeight: 700,
                lineHeight: 1,
                color: "var(--phos-100)",
                textShadow: "var(--glow-text)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {formatPrice(rt.price)}
            </span>
            <div style={{ display: "grid", gap: 5, paddingBottom: 6 }}>
              <Caps size={10} color="var(--phos-500)">
                {selected?.name ?? "XAUUSD"} · {rt.view?.timeframe ?? "M5"}
              </Caps>
              <span
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: "var(--text-secondary)",
                }}
              >
                {formatPrice(first?.entry ?? selected?.bid)} → {formatPrice(rt.price)} · spread{" "}
                {formatPrice(rt.spread, 2)}
              </span>
            </div>
            <div style={{ marginLeft: "auto", display: "grid", gap: 5, justifyItems: "end" }}>
              <Caps size={10} color="var(--phos-500)">
                Session
              </Caps>
              {dayR == null ? (
                <span style={{ fontFamily: "var(--font-data)", fontSize: 18, color: "var(--text-muted)" }}>
                  {DASH}
                </span>
              ) : (
                <PnLValue value={rt.showDollars ? dayPnl ?? 0 : dayR} unit={rt.showDollars ? "USD" : "R"} size="lg" />
              )}
            </div>
          </div>

          <div
            style={{
              position: "relative",
              background: "rgba(4,6,4,.3)",
              backgroundImage: "var(--veil-grid)",
              overflow: "hidden",
            }}
          >
            {first?.tp != null ? (
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: "26%",
                  borderTop: "1px dashed rgba(0,255,65,.42)",
                }}
              >
                <span
                  style={{
                    position: "absolute",
                    right: 10,
                    top: -17,
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--phos-400)",
                  }}
                >
                  TP {formatPrice(first.tp)}
                </span>
              </div>
            ) : null}
            {first?.entry != null ? (
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: "52%",
                  borderTop: "2px solid var(--phos-400)",
                  boxShadow: "var(--glow-sm)",
                }}
              >
                <span
                  style={{
                    position: "absolute",
                    right: 10,
                    top: -18,
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--phos-200)",
                  }}
                >
                  ENTRY {formatPrice(first.entry)}
                </span>
              </div>
            ) : null}
            {(first?.sl ?? rt.planSl) != null ? (
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: "78%",
                  borderTop: "1px dashed var(--arcade-red-dim)",
                }}
              >
                <span
                  style={{
                    position: "absolute",
                    right: 10,
                    top: -17,
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--arcade-red)",
                  }}
                >
                  SL {formatPrice(first?.sl ?? rt.planSl)}
                  {first?.sl == null ? " · plan" : ""}
                </span>
              </div>
            ) : null}

            <div
              style={{
                position: "absolute",
                left: 20,
                top: 20,
                padding: "10px 12px",
                background: "rgba(4,6,4,.86)",
                border: "1px solid var(--line-strong)",
                boxShadow: "var(--sprite-shadow)",
                display: "grid",
                gap: 6,
              }}
            >
              <Caps color="var(--phos-500)">Lens · not AI</Caps>
              <span
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: "var(--text-secondary)",
                }}
              >
                {setup}
                {rt.hud?.sentinel?.setupSide ? ` · ${rt.hud.sentinel.setupSide}` : ""}
              </span>
            </div>

            <Caps style={{ position: "absolute", left: 20, bottom: 14 }} size={10}>
              Chart placeholder — the city is the backdrop, the tape renders here
            </Caps>

            <div
              style={{
                position: "absolute",
                right: 20,
                bottom: 16,
                padding: "10px 14px",
                background: "rgba(4,6,4,.9)",
                border: "1px solid rgba(255,212,0,.4)",
                boxShadow: "var(--sprite-shadow)",
                display: "flex",
                alignItems: "center",
                gap: 10,
              }}
            >
              <Caps size={10} color="var(--arcade-yellow)">
                Incoming · {incoming ?? "none"}
              </Caps>
              <span
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 14,
                  fontWeight: 700,
                  color: "var(--arcade-yellow)",
                }}
              >
                {incoming ? rt.eventEta : DASH}
              </span>
            </div>
          </div>
        </section>

        <aside
          style={{
            position: "relative",
            zIndex: 1,
            borderLeft: "1px solid var(--line-strong)",
            background: "rgba(8,12,8,.92)",
            display: "grid",
            gridTemplateRows: "auto auto 1fr auto",
            minHeight: 0,
          }}
        >
          <div
            style={{
              padding: "16px 18px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 8,
              justifyItems: "center",
              textAlign: "center",
            }}
          >
            <SectionLabel icon="target" center>
              Stand-down score
            </SectionLabel>
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 36,
                lineHeight: 1.1,
                color: "var(--phos-400)",
                textShadow: "var(--glow-text)",
              }}
            >
              {padScore(rt.standDowns)}
            </span>
            <Term color="var(--phos-500)">
              {rt.standDowns} stood down · hi {padScore(rt.hiScore)}
            </Term>
          </div>

          <div
            style={{
              padding: "16px 18px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 10,
            }}
          >
            <SectionLabel icon="chart-candlestick">
              Positions · {rt.positionsOpen} of {rt.maxPositions}
            </SectionLabel>

            {positions.length === 0 ? (
              <Term color="var(--text-muted)">no open arms</Term>
            ) : (
              positions.map((row) => {
                const pct = progressToTarget(row, rt.price);
                return (
                  <div
                    key={String(row.positionId ?? row.symbol)}
                    style={{
                      border: "1px solid var(--line-strong)",
                      background: "var(--phos-a08)",
                      boxShadow: "var(--glow-xs)",
                      padding: 10,
                      display: "grid",
                      gap: 6,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                      <span
                        style={{
                          fontFamily: "var(--font-display)",
                          fontSize: 12,
                          color: "var(--phos-300)",
                        }}
                      >
                        {shortSymbol(row.symbol)}
                      </span>
                      <Caps
                        size={10}
                        weight={700}
                        color={row.side === "sell" ? "var(--side-sell)" : "var(--side-buy)"}
                      >
                        {row.side ?? DASH}
                      </Caps>
                      <span style={{ marginLeft: "auto", fontFamily: "var(--font-data)", fontSize: 11 }}>
                        {row.lots != null ? `${row.lots.toFixed(2)} lots` : DASH}
                      </span>
                    </div>
                    {pct != null ? (
                      <>
                        <MeterBar value={pct} max={100} segments={12} />
                        <span
                          style={{ fontFamily: "var(--font-data)", fontSize: 10, color: "var(--text-muted)" }}
                        >
                          {Math.round(pct)}% of the way to target
                        </span>
                      </>
                    ) : (
                      <span
                        style={{ fontFamily: "var(--font-data)", fontSize: 10, color: "var(--text-muted)" }}
                      >
                        stop {formatPrice(row.sl)} · {row.tp == null ? "no target set" : `tp ${formatPrice(row.tp)}`}
                      </span>
                    )}
                  </div>
                );
              })
            )}
          </div>

          <div style={{ padding: "16px 18px", display: "grid", gap: 10, alignContent: "start" }}>
            <SectionLabel icon="timer">Ready state</SectionLabel>
            <div
              style={{
                padding: 14,
                border: "1px solid var(--line-strong)",
                background: "var(--black-3)",
                boxShadow: "var(--sprite-shadow)",
                display: "grid",
                gap: 10,
                justifyItems: "center",
              }}
            >
              <span
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: 16,
                  color: "var(--phos-400)",
                  textShadow: "var(--glow-text)",
                }}
              >
                {readyLabel}
              </span>
              <Term style={{ textAlign: "center" }}>hold LT to arm. sticks never fire.</Term>
            </div>
          </div>

          <div
            style={{
              borderTop: "1px solid var(--line-hairline)",
              padding: "14px 18px",
              display: "grid",
              gap: 6,
            }}
          >
            <SectionLabel icon="database">Money view</SectionLabel>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontFamily: "var(--font-data)",
                fontSize: 11,
                color: "var(--text-muted)",
              }}
            >
              <Switch
                checked={rt.showDollars}
                onChange={(event) => rt.setShowDollars(event.target.checked)}
              />
              <span>{rt.showDollars ? "on — dollars" : "off — R only"}</span>
            </div>
          </div>
        </aside>
      </div>

      <footer
        style={{
          position: "relative",
          zIndex: 2,
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: "0 20px",
          borderTop: "1px solid var(--line-strong)",
          background: "var(--black-1)",
        }}
      >
        <Caps color="var(--phos-500)">Your controller</Caps>
        <PadHint button="LT" label="Arm" />
        <PadHint button="RT" label="Fire" />
        <PadHint button="a" label="Close" />
        <PadHint button="b" label="Stand down" />
        <PadHint button="y" label="Ask desk" />
        <PadHint button="VIEW" label="Lock" />
        <DemoNotice />
      </footer>
    </Artboard>
  );
}
