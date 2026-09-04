import { ConnectStrip } from "../arcade/ConnectStrip";
import { DASH, dash, formatPrice, padScore, rAtStop } from "../arcade/format";
import { useArcadeRuntime } from "../arcade/useArcadeRuntime";
import { BgmControl } from "../components/bgm";
import { CodeRain } from "../components/CodeRain";
import { Artboard, Caps, DemoNotice, PadHint, Term } from "../components/primitives";
import { GamepadKey, MeterBar, PnLValue } from "../ds";
import { CITY_ART } from "./art";

/**
 * Fire on city art — live `/api/arcade` figures on the prototype `is_artcontra` artboard.
 *
 * Layout notes carried over from the design chat, since they are the point of
 * the screen rather than incidental: every order figure lives in one 298px left
 * rail so the right of the frame stays clear to read the citadel and the aim
 * point; the framing plate sits in its own top-right HUD strip at z-index 4,
 * above the sprite band, because at z-index 1 the hero sprite always covered it.
 */
export function CityFireScreen() {
  const rt = useArcadeRuntime("city");
  const selected = rt.selected;
  const first = rt.hud?.positions[0];
  const side = (rt.view?.side === "buy" || rt.view?.side === "sell"
    ? rt.view.side
    : first?.side) ?? null;
  const lots = rt.view?.lots ?? selected?.defaultLots ?? null;
  const now = rt.price;
  const stopPx = first?.sl ?? rt.planSl;
  const targetPx = first?.tp ?? null;
  const damageR = rAtStop(selected);
  const phase = rt.view?.phase ?? (rt.online ? "IDLE" : "OFFLINE");
  const armed = phase === "ARMED" || phase === "FIRE" || phase === "CLUTCH";
  const qualityPct =
    rt.hud?.sentinel?.quality != null ? Math.round(rt.hud.sentinel.quality * 100) : null;
  const threatHigh = rt.threat === "high";
  const nextEvent = rt.hud?.sentinel?.nextEvent;
  const tMinus = rt.hud?.sentinel?.nextEventTMinusS;
  const insideGuard = tMinus != null && tMinus >= 0 && tMinus <= 900;
  const heartFull = rt.sprite("heartFull", "/sprites/heart-full.png");
  const heartEmpty = rt.sprite("heartEmpty", "/sprites/heart-empty.png");
  const stageLabel =
    phase === "FIRE" ? "THE FILL" : phase === "ARMED" ? "ARMED" : phase === "CLUTCH" ? "CLUTCH" : "WAIT";

  const ladder = [
    targetPx != null
      ? {
          tick: "var(--phos-400)",
          glow: true,
          text: `${formatPrice(targetPx)} target`,
          color: "var(--phos-300)",
        }
      : null,
    {
      tick: "var(--phos-200)",
      glow: false,
      text: `${formatPrice(now)} now`,
      color: "var(--text-body)",
    },
    stopPx != null
      ? {
          tick: "var(--arcade-red)",
          glow: false,
          text: `${formatPrice(stopPx)} stop${first?.sl == null ? " · plan" : ""}`,
          color: "var(--arcade-red)",
        }
      : null,
  ].filter((row): row is { tick: string; glow: boolean; text: string; color: string } => row != null);

  return (
    <Artboard
      label="Fire on city art"
      frameStyle={{
        width: 1440,
        height: 810,
        position: "relative",
        background: `#040604 url('${rt.artUrl || CITY_ART}') center/cover no-repeat`,
        border: "1px solid var(--line-strong)",
        boxShadow: "var(--glow-md)",
      }}
    >
      <div style={{ position: "absolute", inset: 0, background: "var(--veil-vignette)" }} />
      <div style={{ position: "absolute", inset: 0, opacity: 0.5, pointerEvents: "none" }}>
        <CodeRain opacity={0.3} fontSize={17} />
      </div>
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "var(--veil-scanline)",
          opacity: 0.45,
          pointerEvents: "none",
        }}
      />

      <div style={{ position: "absolute", inset: 0, pointerEvents: "none", overflow: "hidden" }}>
        <i
          style={{
            position: "absolute",
            left: "6%",
            top: "62%",
            width: 180,
            height: 2,
            background: "linear-gradient(90deg,transparent,var(--arcade-yellow))",
            boxShadow: "0 0 6px var(--arcade-yellow)",
            transform: "rotate(-38deg)",
            animation: "ev-tracer 1.1s linear infinite",
          }}
        />
        <i
          style={{
            position: "absolute",
            left: "22%",
            top: "78%",
            width: 140,
            height: 2,
            background: "linear-gradient(90deg,transparent,var(--arcade-orange))",
            boxShadow: "0 0 6px var(--arcade-orange)",
            transform: "rotate(-42deg)",
            animation: "ev-tracer 1.4s linear .35s infinite",
          }}
        />
        <i
          style={{
            position: "absolute",
            right: "12%",
            top: "70%",
            width: 160,
            height: 2,
            background: "linear-gradient(270deg,transparent,var(--arcade-red))",
            boxShadow: "0 0 6px var(--arcade-red)",
            transform: "rotate(38deg)",
            animation: "ev-tracer 1.25s linear .7s infinite",
          }}
        />

        <img
          src={rt.sprite("boomBig", "/sprites/boom-big.png")}
          alt=""
          style={{
            position: "absolute",
            left: "30%",
            top: "24%",
            width: 120,
            imageRendering: "pixelated",
            animation: "ev-burst 1.6s steps(6,end) infinite",
          }}
        />
        <img
          src={rt.sprite("boomMid", "/sprites/boom-mid.png")}
          alt=""
          style={{
            position: "absolute",
            left: "36%",
            bottom: "52%",
            width: 140,
            imageRendering: "pixelated",
            animation: "ev-burst 2.1s steps(6,end) .5s infinite",
          }}
        />
        <img
          src={rt.sprite("boomSmall", "/sprites/boom-small.png")}
          alt=""
          style={{
            position: "absolute",
            left: "44%",
            top: "34%",
            width: 70,
            imageRendering: "pixelated",
            animation: "ev-burst 1.3s steps(5,end) .9s infinite",
          }}
        />

        <i
          style={{
            position: "absolute",
            left: "4%",
            top: "52%",
            width: 120,
            height: 120,
            background: "radial-gradient(circle,rgba(255,138,0,.55),transparent 68%)",
            animation: "ev-muzzle 1.1s steps(1,end) infinite",
          }}
        />
        <i
          style={{
            position: "absolute",
            right: "4%",
            top: "40%",
            width: 150,
            height: 150,
            background: "radial-gradient(circle,rgba(255,212,0,.45),transparent 68%)",
            animation: "ev-muzzle 1.7s steps(1,end) .4s infinite",
          }}
        />
      </div>

      {threatHigh ? (
        <div
          style={{
            position: "absolute",
            inset: 0,
            pointerEvents: "none",
            boxShadow: "inset 0 0 90px rgba(232,32,42,.55)",
            animation: "ev-alert 1.6s steps(1,end) infinite",
          }}
        />
      ) : null}

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 0,
          height: 56,
          display: "flex",
          alignItems: "center",
          gap: 18,
          padding: "0 20px",
          background: "rgba(4,6,4,.9)",
          borderBottom: "1px solid var(--line-strong)",
          zIndex: 5,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 12,
            color: "var(--phos-400)",
            textShadow: "var(--glow-text)",
          }}
        >
          1P {padScore(rt.standDowns)}
        </span>
        <span style={{ fontFamily: "var(--font-display)", fontSize: 12, color: "var(--grey-300)" }}>
          HI {padScore(rt.hiScore)}
        </span>
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: 14,
            fontWeight: 700,
            color: "var(--arcade-yellow)",
          }}
        >
          {rt.clock}
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Caps color="var(--text-muted)">Arms left</Caps>
          <div style={{ display: "flex", gap: 5, alignItems: "center" }}>
            {rt.slots.map((lit, i) => (
              <img
                key={i}
                src={lit ? heartFull : heartEmpty}
                alt=""
                style={{ width: 18, imageRendering: "pixelated" }}
              />
            ))}
          </div>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <ConnectStrip runtime={rt} flattenLabel="Flatten" />
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 56,
          height: 34,
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: "0 20px",
          background: "rgba(4,6,4,.9)",
          borderBottom: "1px solid var(--arcade-red-dim)",
          zIndex: 4,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 10,
            color: "var(--arcade-red)",
            textShadow: "2px 2px 0 #000",
            animation: threatHigh ? "ev-blink 1s steps(1,end) infinite" : undefined,
          }}
        >
          {threatHigh ? "!! CITADEL !!" : "CITADEL"}
        </span>
        <Caps color="var(--text-muted)">
          {nextEvent ? `${nextEvent} · ${rt.eventEta}` : "no print on the tape"}
          {selected ? ` · ${selected.name.toLowerCase()}` : ""}
        </Caps>
        <div
          style={{
            flex: 1,
            maxWidth: 380,
            height: 12,
            background: "var(--black-4)",
            border: "1px solid var(--arcade-red-dim)",
            padding: 2,
          }}
        >
          <i
            style={{
              display: "block",
              height: "100%",
              width: `${qualityPct ?? 0}%`,
              background:
                "repeating-linear-gradient(90deg,var(--arcade-red) 0 10px,rgba(4,6,4,.6) 10px 12px)",
            }}
          />
        </div>
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: 11,
            fontWeight: 700,
            color: "var(--arcade-red)",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {qualityPct == null ? DASH : `${qualityPct}%`}
        </span>
        <Caps color="var(--arcade-yellow)">
          {rt.threat === "high" ? "Threat high" : rt.threat === "mid" ? "Threat mid" : "Threat low"}
        </Caps>
        <span
          style={{
            marginLeft: "auto",
            fontFamily: "var(--font-terminal)",
            fontSize: 15,
            color: "var(--arcade-yellow)",
          }}
        >
          {insideGuard
            ? `> your news guard is 15 minutes. you are inside it.`
            : tMinus != null
              ? `> next print in ${rt.eventEta}. guard is 15.`
              : "> news guard quiet."}
        </span>
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 90,
          height: 6,
          zIndex: 4,
          background:
            "repeating-linear-gradient(135deg,var(--arcade-yellow) 0 14px,#040604 14px 28px)",
          opacity: 0.65,
          animation: "ev-hazard 1.2s linear infinite",
        }}
      />

      <div
        style={{
          position: "absolute",
          left: 20,
          top: 104,
          bottom: 78,
          width: 298,
          display: "flex",
          flexDirection: "column",
          gap: 6,
          zIndex: 3,
        }}
      >
        <div
          style={{
            position: "relative",
            background: "rgba(4,6,4,.84)",
            border: "1px solid var(--line-strong)",
            boxShadow: "var(--sprite-shadow-lg)",
            display: "grid",
            animation: armed ? "ev-shake 2.4s steps(5,end) infinite" : undefined,
          }}
        >
          <i
            style={{
              position: "absolute",
              left: -1,
              top: -1,
              width: 16,
              height: 16,
              borderLeft: "3px solid var(--arcade-red)",
              borderTop: "3px solid var(--arcade-red)",
            }}
          />
          <i
            style={{
              position: "absolute",
              right: -1,
              bottom: -1,
              width: 16,
              height: 16,
              borderRight: "3px solid var(--phos-400)",
              borderBottom: "3px solid var(--phos-400)",
            }}
          />
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              height: 28,
              padding: "0 12px",
              background: "var(--black-1)",
              borderBottom: "1px solid var(--line-strong)",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 9,
                color: "var(--arcade-yellow)",
                textShadow: "2px 2px 0 #000",
              }}
            >
              {phase}
            </span>
            <Caps color="var(--text-muted)">{stageLabel}</Caps>
            <div style={{ display: "flex", gap: 3, marginLeft: "auto" }}>
              {rt.slots.map((lit, i) => (
                <i
                  key={i}
                  style={{
                    width: 7,
                    height: 13,
                    background: lit ? "var(--phos-400)" : "var(--black-5)",
                    border: lit ? undefined : "1px solid var(--line-neutral)",
                  }}
                />
              ))}
            </div>
          </div>
          <div style={{ padding: 14, display: "grid", gap: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: 26,
                  lineHeight: 1,
                  color: "var(--phos-400)",
                  textShadow: "var(--glow-text),3px 3px 0 #000",
                }}
              >
                {side ? side.toUpperCase() : DASH}
              </span>
              <div style={{ display: "grid", gap: 3 }}>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 13,
                    fontWeight: 700,
                    whiteSpace: "nowrap",
                    color: "var(--text-body)",
                  }}
                >
                  {selected?.name ?? "XAUUSD"} · {lots != null ? lots.toFixed(2) : DASH} lots
                </span>
                <Caps color="var(--text-muted)" style={{ whiteSpace: "nowrap" }}>
                  Market · entry ~{formatPrice(now)}
                </Caps>
              </div>
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                paddingTop: 2,
                borderTop: "1px solid var(--line-hairline)",
              }}
            >
              <Caps>Weapon</Caps>
              <span
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: 9,
                  color: "var(--phos-300)",
                  textShadow: "2px 2px 0 #000",
                }}
              >
                M · MARKET
              </span>
              <span
                style={{
                  marginLeft: "auto",
                  fontFamily: "var(--font-data)",
                  fontSize: 12,
                  color: "var(--arcade-yellow)",
                }}
              >
                {rt.hud?.session.id ?? DASH}
              </span>
            </div>
            <Term size={15} color="var(--phos-500)">
              {rt.hud?.sentinel?.setup
                ? `${rt.hud.sentinel.setup}${rt.hud.sentinel.setupSide ? ` · ${rt.hud.sentinel.setupSide}` : ""}`
                : "waiting on a quote before the sentinel can speak"}
            </Term>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gap: 6,
            padding: 12,
            border: "1px solid var(--arcade-red-dim)",
            background: "rgba(4,6,4,.84)",
            boxShadow: "var(--sprite-shadow)",
          }}
        >
          <Caps color="var(--arcade-red)">Damage if wrong</Caps>
          {damageR == null ? (
            <span style={{ fontFamily: "var(--font-data)", fontSize: 22, color: "var(--text-muted)" }}>
              {DASH}
            </span>
          ) : (
            <PnLValue value={-damageR} size="lg" />
          )}
          <MeterBar
            value={0}
            max={rt.hud?.risk.maxDayLossUsd || 1}
            segments={10}
            tone="danger"
            label="Loss meter · waiting on broker"
          />
          <span style={{ fontFamily: "var(--font-data)", fontSize: 11, color: "var(--text-muted)" }}>
            stop {formatPrice(stopPx)} · default stop is 1R
          </span>
        </div>

        <div
          style={{
            display: "grid",
            gap: 6,
            padding: 12,
            border: "1px solid var(--line-strong)",
            background: "rgba(4,6,4,.84)",
            boxShadow: "var(--sprite-shadow)",
          }}
        >
          <Caps color="var(--phos-300)">Reward if right</Caps>
          {targetPx == null ? (
            <span style={{ fontFamily: "var(--font-data)", fontSize: 18, color: "var(--text-muted)" }}>
              no target set
            </span>
          ) : (
            <MeterBar value={0} max={1} segments={10} label={`Target ${formatPrice(targetPx)}`} />
          )}
          <span style={{ fontFamily: "var(--font-data)", fontSize: 11, color: "var(--text-muted)" }}>
            {targetPx == null ? "a fill with a TP would paint R here" : `tp ${formatPrice(targetPx)}`}
          </span>
        </div>

        <div
          style={{
            padding: "10px 12px",
            borderLeft: "2px solid var(--status-agent)",
            borderTop: "1px solid var(--line-hairline)",
            borderRight: "1px solid var(--line-hairline)",
            borderBottom: "1px solid var(--line-hairline)",
            background: "rgba(4,6,4,.84)",
            display: "grid",
            gap: 3,
          }}
        >
          <Term size={15} color="var(--status-agent)">
            risk-warden: {lots != null ? lots.toFixed(2) : DASH} on {selected?.name ?? "—"} — max{" "}
            {selected?.maxLots ?? DASH}.
          </Term>
          <Term size={15} color="var(--status-agent)">
            {insideGuard
              ? `print in ${rt.eventEta}. your guard is 15.`
              : rt.online
                ? "inside the window's rules, or waiting on a quote."
                : "gateway offline — figures are blank on purpose."}
          </Term>
        </div>

        <div
          style={{
            display: "grid",
            gap: 4,
            padding: "10px 12px",
            background: "rgba(4,6,4,.82)",
            border: "1px solid var(--line-hairline)",
          }}
        >
          <Caps>Price ladder</Caps>
          {ladder.map((row) => (
            <div key={row.text} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <i
                style={{
                  width: 16,
                  height: 2,
                  background: row.tick,
                  boxShadow: row.glow ? "var(--glow-xs)" : undefined,
                }}
              />
              <span style={{ fontFamily: "var(--font-data)", fontSize: 11, color: row.color }}>
                {row.text}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          right: 20,
          top: 104,
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "5px 12px",
          background: "rgba(4,6,4,.88)",
          border: "1px solid var(--line-hairline)",
          boxShadow: "var(--sprite-shadow)",
          zIndex: 4,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: 11,
            color: "var(--arcade-yellow)",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {formatPrice(now)}
          {targetPx != null ? ` → ${formatPrice(targetPx)}` : ""}
        </span>
        <Caps color={threatHigh ? "var(--arcade-red)" : "var(--text-muted)"}>
          {insideGuard ? "Danger · event inside guard" : dash(rt.hud?.sentinel?.qualityBand ?? "quiet")}
        </Caps>
        <Caps color="var(--status-agent)">2P · desk</Caps>
      </div>

      <div
        style={{
          position: "absolute",
          left: 330,
          right: 200,
          bottom: 64,
          top: 104,
          zIndex: 1,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: 36,
            transform: "translateX(-50%)",
            width: 500,
            height: 280,
            pointerEvents: "none",
          }}
        >
          <i
            style={{
              position: "absolute",
              left: 0,
              top: 0,
              width: 44,
              height: 44,
              borderLeft: "3px solid var(--arcade-red)",
              borderTop: "3px solid var(--arcade-red)",
              boxShadow: "2px 2px 0 #000",
            }}
          />
          <i
            style={{
              position: "absolute",
              right: 0,
              top: 0,
              width: 44,
              height: 44,
              borderRight: "3px solid var(--arcade-red)",
              borderTop: "3px solid var(--arcade-red)",
              boxShadow: "-2px 2px 0 #000",
            }}
          />
          <i
            style={{
              position: "absolute",
              left: 0,
              bottom: 0,
              width: 44,
              height: 44,
              borderLeft: "3px solid var(--arcade-red)",
              borderBottom: "3px solid var(--arcade-red)",
              boxShadow: "2px -2px 0 #000",
            }}
          />
          <i
            style={{
              position: "absolute",
              right: 0,
              bottom: 0,
              width: 44,
              height: 44,
              borderRight: "3px solid var(--arcade-red)",
              borderBottom: "3px solid var(--arcade-red)",
              boxShadow: "-2px -2px 0 #000",
            }}
          />
          <i
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: 0,
              height: 2,
              background: "var(--arcade-red)",
              boxShadow: "0 0 8px var(--arcade-red)",
              animation: "ev-scanv 2.6s linear infinite",
            }}
          />
          <i
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              width: 2,
              height: 26,
              margin: "-13px 0 0 -1px",
              background: "rgba(232,32,42,.8)",
            }}
          />
          <i
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              width: 26,
              height: 2,
              margin: "-1px 0 0 -13px",
              background: "rgba(232,32,42,.8)",
            }}
          />
          <div
            style={{
              position: "absolute",
              left: 0,
              top: -26,
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 10,
                color: "var(--arcade-red)",
                textShadow: "2px 2px 0 #000",
              }}
            >
              CITADEL
            </span>
            <Caps color="var(--arcade-yellow)">{now == null ? "No lock" : "Target locked"}</Caps>
          </div>
        </div>
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: 0,
            height: 220,
            background: "var(--protect-bottom)",
          }}
        />
      </div>

      <div
        style={{
          position: "absolute",
          left: 380,
          bottom: 200,
          width: 300,
          zIndex: 2,
          pointerEvents: "none",
        }}
      >
        <img
          src={rt.sprite("heroFire", "/sprites/hero-fire.png")}
          alt="1P"
          style={{
            display: "block",
            width: "100%",
            imageRendering: "pixelated",
            filter: "drop-shadow(4px 4px 0 rgba(0,0,0,.85))",
          }}
        />
        <span
          style={{
            position: "absolute",
            left: 8,
            top: -18,
            fontSize: 9,
            letterSpacing: ".18em",
            textTransform: "uppercase",
            color: "var(--phos-400)",
            textShadow: "2px 2px 0 #000",
          }}
        >
          1P
        </span>
      </div>
      <div
        style={{
          position: "absolute",
          left: 710,
          bottom: 200,
          width: 165,
          zIndex: 2,
          pointerEvents: "none",
        }}
      >
        <img
          src={rt.sprite("heroKneel", "/sprites/hero-kneel.png")}
          alt="2P"
          style={{
            display: "block",
            width: "100%",
            imageRendering: "pixelated",
            filter: "drop-shadow(4px 4px 0 rgba(0,0,0,.85))",
          }}
        />
      </div>

      <div
        style={{
          position: "absolute",
          left: 330,
          right: 350,
          bottom: 78,
          display: "grid",
          gap: 8,
          zIndex: 3,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            padding: "14px 16px",
            background: "rgba(4,6,4,.88)",
            border: "1px solid var(--line-strong)",
            boxShadow: "var(--glow-sm),var(--sprite-shadow)",
          }}
        >
          <GamepadKey button="LT" size="lg" pressed={armed} label={armed ? "Held" : undefined} />
          <span
            style={{ fontFamily: "var(--font-display)", fontSize: 14, color: "var(--text-disabled)" }}
          >
            +
          </span>
          <GamepadKey button="RT" size="lg" />
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 16,
              color: "var(--phos-400)",
              textShadow: "var(--glow-text)",
              animation: phase === "ARMED" ? "ev-blink 1s steps(1,end) infinite" : undefined,
            }}
          >
            FIRE
          </span>
          <Caps size={10} color="var(--text-muted)" style={{ marginLeft: "auto" }}>
            Two hands · one order · one confirm
          </Caps>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "10px 14px",
            background: "rgba(4,6,4,.72)",
            border: "1px dashed var(--line-strong)",
          }}
        >
          <GamepadKey button="b" size="md" />
          <span
            style={{ fontFamily: "var(--font-display)", fontSize: 11, color: "var(--phos-300)" }}
          >
            STAND DOWN +1
          </span>
          <Term size={15}>
            release the clutch and your score goes to {padScore(rt.standDowns + 1)}. nothing reaches
            the broker.
          </Term>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 0,
          height: 64,
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: "0 20px",
          background: "var(--black-1)",
          borderTop: "1px solid var(--line-strong)",
        }}
      >
        <Caps color="var(--phos-500)">Your controller</Caps>
        <PadHint button="RT" label="Fire" />
        <PadHint button="b" label="Stand down" />
        <PadHint button="y" label="Ask desk" />
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "6px 12px",
            border: "1px solid var(--line-hairline)",
          }}
        >
          <BgmControl />
        </div>
        <DemoNotice />
      </div>
    </Artboard>
  );
}
