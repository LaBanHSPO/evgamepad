import type { CSSProperties } from "react";
import { Button } from "../ds";
import type { ArcadeRuntime } from "./useArcadeRuntime";

/**
 * Compact connect / flatten strip for the art HUDs.
 *
 * The token is an `<input>` so the cabinet keyboard map ignores it. It is never written to
 * storage — same contract as the live HUD.
 */
export function ConnectStrip({
  runtime,
  flattenLabel = "Flatten all",
}: {
  runtime: ArcadeRuntime;
  flattenLabel?: string;
}) {
  const live = runtime.socketStatus === "open" || runtime.socketStatus === "connecting";
  return (
    <div style={row}>
      <span style={statusMark(runtime)}>
        {runtime.socketStatus === "open"
          ? "LIVE"
          : runtime.online
            ? runtime.socketStatus === "idle"
              ? "PRESS START"
              : runtime.socketStatus
            : "OFFLINE"}
      </span>
      {!live ? (
        <>
          <input
            type="password"
            autoComplete="off"
            placeholder="session token"
            value={runtime.token}
            onChange={(event) => runtime.setToken(event.target.value)}
            style={tokenField}
            aria-label="Session token — pasted once, kept in memory, never stored"
          />
          <Button
            variant="secondary"
            size="sm"
            onClick={runtime.connect}
            disabled={!runtime.token}
          >
            Connect
          </Button>
        </>
      ) : (
        <span style={{ fontFamily: "var(--font-data)", fontSize: 11, color: "var(--text-muted)" }}>
          {runtime.hud?.broker.connected ? "broker up" : "broker waiting"}
        </span>
      )}
      <Button
        variant="danger"
        size="sm"
        onClick={runtime.flatten}
        disabled={runtime.socketStatus !== "open"}
      >
        {flattenLabel}
      </Button>
    </div>
  );
}

const row: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
};

function statusMark(runtime: ArcadeRuntime): CSSProperties {
  const live = runtime.socketStatus === "open";
  return {
    fontFamily: "var(--font-display)",
    fontSize: 12,
    color: live ? "var(--phos-400)" : runtime.online ? "var(--arcade-red)" : "var(--text-muted)",
    textShadow: live ? "var(--glow-text)" : undefined,
    animation: live ? undefined : "ev-blink 1s steps(1,end) infinite",
    whiteSpace: "nowrap",
  };
}

const tokenField: CSSProperties = {
  width: 140,
  height: 28,
  background: "var(--black-2)",
  color: "inherit",
  border: "1px solid var(--line-hairline)",
  padding: "0 8px",
  fontFamily: "var(--font-data)",
  fontSize: 11,
};
