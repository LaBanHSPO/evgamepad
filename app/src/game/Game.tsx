/**
 * The evening. Token gate, HUD, overlay, check-in.
 *
 * The token is asked for once and kept in memory for this session only --
 * never `localStorage`, never a `VITE_*` build constant. Both would leave a
 * trading credential somewhere it outlives the evening.
 */

import { useCallback, useState } from "react";
import { Button, Input } from "../ds";
import { GameOverlay } from "../game-overlay/GameOverlay";
import { initialOverlay, reduce, type OverlayState } from "../game-overlay/model";
import { CheckIn } from "../session/CheckIn";
import { Hud } from "./Hud";
import { useGame } from "./useGame";

export function Game() {
  const game = useGame();
  const [token, setToken] = useState("");
  const [connected, setConnected] = useState(false);
  const [overlay, setOverlay] = useState<OverlayState>(initialOverlay());
  const [checkedIn, setCheckedIn] = useState(false);

  const open = useCallback(() => setOverlay((s) => reduce(s, { kind: "open" }).state), []);
  const close = useCallback(() => setOverlay((s) => reduce(s, { kind: "close" }).state), []);

  if (!connected) {
    return (
      <form
        className="gate"
        onSubmit={(e) => {
          e.preventDefault();
          if (!token) return;
          game.connect(token);
          setConnected(true);
          setToken(""); // out of React state the moment the socket has it
        }}
      >
        <h1>Evening Forex Gold Gamepad</h1>
        <p>
          Paste the session token. It is held in memory for this session only and is never written
          to storage.
        </p>
        <Input
          type="password"
          value={token}
          onChange={(e) => setToken(e.currentTarget.value)}
          placeholder="EV_WS_TOKEN"
        />
        <Button type="submit" variant="primary">
          Connect
        </Button>
        <small>cTrader demo · not advice · keep this tab focused</small>
      </form>
    );
  }

  return (
    <>
      <Hud game={game} onOpenOverlay={open} />
      <GameOverlay
        state={overlay}
        onState={setOverlay}
        onClose={close}
        onFlatten={game.flatten}
        padId={game.view.padId}
        conn={game.view.conn}
      />
      {/* Rendered over the HUD, never in front of it: the session can start
          while this is still on screen. */}
      {!checkedIn && <CheckIn phase="pre" onDone={() => setCheckedIn(true)} />}
    </>
  );
}
