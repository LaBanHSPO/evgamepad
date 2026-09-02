import { BgmControl } from "../components/bgm";
import { CodeRain } from "../components/CodeRain";
import { Artboard, Caps, DemoNotice, PadHint, Term } from "../components/primitives";
import { GamepadKey, MeterBar, PnLValue } from "../ds";
import { CITY_ART } from "./art";

/**
 * Fire on city art — the prototype's `is_artcontra` artboard.
 *
 * Layout notes carried over from the design chat, since they are the point of
 * the screen rather than incidental: every order figure lives in one 298px left
 * rail so the right of the frame stays clear to read the citadel and the aim
 * point; the framing plate sits in its own top-right HUD strip at z-index 4,
 * above the sprite band, because at z-index 1 the hero sprite always covered it.
 */
export function CityFireScreen() {
  return (
    <Artboard
      label="Fire on city art"
      frameStyle={{
        width: 1440,
        height: 810,
        position: "relative",
        background: `#040604 url('${CITY_ART}') center/cover no-repeat`,
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

      {/* ── battle layer: tracers, bursts, muzzle flash ───────── */}
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
          src="/sprites/boom-big.png"
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
          src="/sprites/boom-mid.png"
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
          src="/sprites/boom-small.png"
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

      {/* red alert pulse inside the frame edge */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          boxShadow: "inset 0 0 90px rgba(232,32,42,.55)",
          animation: "ev-alert 1.6s steps(1,end) infinite",
        }}
      />

      {/* ── arcade HUD strip ──────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 0,
          height: 56,
          display: "flex",
          alignItems: "center",
          gap: 26,
          padding: "0 20px",
          background: "rgba(4,6,4,.9)",
          borderBottom: "1px solid var(--line-strong)",
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
          1P 07
        </span>
        <span style={{ fontFamily: "var(--font-display)", fontSize: 12, color: "var(--grey-300)" }}>
          HI 12
        </span>
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: 14,
            fontWeight: 700,
            color: "var(--arcade-yellow)",
          }}
        >
          1:12:04
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Caps color="var(--text-muted)">Arms left</Caps>
          <div style={{ display: "flex", gap: 5, alignItems: "center" }}>
            <img
              src="/sprites/heart-full.png"
              alt=""
              style={{ width: 18, imageRendering: "pixelated" }}
            />
            <img
              src="/sprites/heart-full.png"
              alt=""
              style={{ width: 18, imageRendering: "pixelated" }}
            />
            <img
              src="/sprites/heart-empty.png"
              alt=""
              style={{ width: 18, imageRendering: "pixelated" }}
            />
          </div>
        </div>
        <Caps size={10} color="var(--arcade-yellow)" style={{ marginLeft: "auto" }}>
          Armed · nothing sent yet
        </Caps>
      </div>

      {/* ── boss bar: the citadel ─────────────────────────────── */}
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
            animation: "ev-blink 1s steps(1,end) infinite",
          }}
        >
          !! CITADEL !!
        </span>
        <Caps color="var(--text-muted)">dxy print · 18:04 · impact xauusd</Caps>
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
              width: "64%",
              background:
                "repeating-linear-gradient(90deg,var(--arcade-red) 0 10px,rgba(4,6,4,.6) 10px 12px)",
              animation: "ev-hpdrain 6s linear infinite",
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
          64%
        </span>
        <Caps color="var(--arcade-yellow)">Threat high</Caps>
        <span
          style={{
            marginLeft: "auto",
            fontFamily: "var(--font-terminal)",
            fontSize: 15,
            color: "var(--arcade-yellow)",
          }}
        >
          &gt; your news guard is 15 minutes. you are inside it.
        </span>
      </div>

      {/* hazard tape */}
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

      {/* ── order rail: every figure, one column ──────────────── */}
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
        {/* stage card */}
        <div
          style={{
            position: "relative",
            background: "rgba(4,6,4,.84)",
            border: "1px solid var(--line-strong)",
            boxShadow: "var(--sprite-shadow-lg)",
            display: "grid",
            animation: "ev-shake 2.4s steps(5,end) infinite",
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
              STAGE 04
            </span>
            <Caps color="var(--text-muted)">The fill</Caps>
            {/* ammo */}
            <div style={{ display: "flex", gap: 3, marginLeft: "auto" }}>
              {["var(--phos-400)", "var(--phos-400)", "var(--phos-500)", null, null].map((c, i) => (
                <i
                  key={i}
                  style={{
                    width: 7,
                    height: 13,
                    background: c ?? "var(--black-5)",
                    border: c ? undefined : "1px solid var(--line-neutral)",
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
                BUY
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
                  XAUUSD · 0.20 lots
                </span>
                <Caps color="var(--text-muted)" style={{ whiteSpace: "nowrap" }}>
                  Market · entry ~2461.38
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
                21:07:12
              </span>
            </div>
            <Term size={15} color="var(--phos-500)">
              41s since the signal bar closed
            </Term>
          </div>
        </div>

        {/* damage if wrong */}
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
          <PnLValue value={-1} size="lg" />
          <MeterBar
            value={10}
            max={30}
            segments={10}
            tone="danger"
            label="Loss meter after a stop"
          />
          <span style={{ fontFamily: "var(--font-data)", fontSize: 11, color: "var(--text-muted)" }}>
            stop 2455.60 · -1.10R already spent
          </span>
        </div>

        {/* reward if right */}
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
          <PnLValue value={2.4} size="lg" />
          <MeterBar value={24} max={30} segments={10} label="Target 2473.00" />
          <span style={{ fontFamily: "var(--font-data)", fontSize: 11, color: "var(--text-muted)" }}>
            2.4 : 1 · inside rule 4
          </span>
        </div>

        {/* risk-warden */}
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
            risk-warden: 0.20 on a 2.4R setup — rule 4 allows it.
          </Term>
          <Term size={15} color="var(--status-agent)">
            dxy prints in 18 minutes. your guard is 15.
          </Term>
        </div>

        {/* price ladder */}
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
          {[
            {
              tick: "var(--phos-400)",
              glow: true,
              text: "2473.00 target · +2.40R",
              color: "var(--phos-300)",
            },
            { tick: "var(--phos-200)", glow: false, text: "2461.38 now", color: "var(--text-body)" },
            {
              tick: "var(--arcade-red)",
              glow: false,
              text: "2455.60 stop · -1.00R",
              color: "var(--arcade-red)",
            },
          ].map((row) => (
            <div key={row.text} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <i
                style={{
                  width: 16,
                  height: 2,
                  background: row.tick,
                  boxShadow: row.glow ? "var(--glow-xs)" : undefined,
                }}
              />
              <span
                style={{ fontFamily: "var(--font-data)", fontSize: 11, color: row.color }}
              >
                {row.text}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ── framing plate, lifted clear of the sprite band ────── */}
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
          range 2461.38 → 2473.00
        </span>
        <Caps color="var(--arcade-red)">Danger · event inside guard</Caps>
        <Caps color="var(--status-agent)">2P · desk</Caps>
      </div>

      {/* ── target lock over the citadel ──────────────────────── */}
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
            <Caps color="var(--arcade-yellow)">Target locked</Caps>
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

      {/* ── the two players ──────────────────────────────────── */}
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
          src="/sprites/hero-fire.png"
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
          src="/sprites/hero-kneel.png"
          alt="2P"
          style={{
            display: "block",
            width: "100%",
            imageRendering: "pixelated",
            filter: "drop-shadow(4px 4px 0 rgba(0,0,0,.85))",
          }}
        />
      </div>

      {/* ── the two-hand confirm ──────────────────────────────── */}
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
          <GamepadKey button="LT" size="lg" pressed label="Held" />
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
              animation: "ev-blink 1s steps(1,end) infinite",
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
            release the clutch and your score goes to 08. nothing reaches the broker.
          </Term>
        </div>
      </div>

      {/* ── pad legend + BGM ──────────────────────────────────── */}
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
