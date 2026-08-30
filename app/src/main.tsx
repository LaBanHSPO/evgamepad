import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { Game } from "./game/Game";
import "./styles/global.css";
import "./game/game.css";

/**
 * Two entries share one bundle.
 *
 * `/` is the game -- the thing the evening runs on. `?prototype` is the
 * click-through screen deck the design work produced, kept because it is the
 * reference the HUD is built against, not because it is live.
 */
const isPrototype = new URLSearchParams(location.search).has("prototype");

createRoot(document.getElementById("root")!).render(
  <StrictMode>{isPrototype ? <App /> : <Game />}</StrictMode>,
);

/**
 * The shell-only service worker. `updateViaCache: "none"` plus the worker's own
 * `skipWaiting` is what makes a new build run on the next launch instead of
 * asking the player to hard-reload mid-evening.
 */
if ("serviceWorker" in navigator && import.meta.env.PROD) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js", { type: "module", updateViaCache: "none" })
      .catch(() => {
        // No service worker just means no offline shell. The game still runs.
      });
  });
}
