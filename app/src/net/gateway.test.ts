import { expect, it } from "vitest";
import { joinGateway, toWsUrl } from "./gateway";

it("leaves paths relative when no gateway origin is configured", () => {
  expect(joinGateway("", "/api/arcade/hud")).toBe("/api/arcade/hud");
  expect(joinGateway("  ", "/ws")).toBe("/ws");
});

it("prefixes gateway paths and strips a trailing slash on the origin", () => {
  expect(joinGateway("https://gw.bobvolman.com/", "/api/playbooks")).toBe(
    "https://gw.bobvolman.com/api/playbooks",
  );
  expect(joinGateway("https://gw.bobvolman.com", "api/playbooks")).toBe(
    "https://gw.bobvolman.com/api/playbooks",
  );
});

it("does not double-prefix an already-absolute URL", () => {
  expect(joinGateway("https://gw.bobvolman.com", "https://gw.bobvolman.com/api/x")).toBe(
    "https://gw.bobvolman.com/api/x",
  );
});

it("turns the page or gateway http(s) origin into a websocket URL", () => {
  expect(toWsUrl("https://hud.example")).toBe("wss://hud.example/ws");
  expect(toWsUrl("http://localhost:5173")).toBe("ws://localhost:5173/ws");
});
