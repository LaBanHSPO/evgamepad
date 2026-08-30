// Generates src/protocol/types.ts from the gateway's exported JSON Schema.
//
// The catalog in apps/gateway/protocol/catalog.py is the single source of
// truth. This runs in `pnpm build`, so a catalog change that was not
// regenerated fails the web build instead of drifting into a runtime surprise.
//
//   node scripts/gen-protocol-types.mjs           # write
//   node scripts/gen-protocol-types.mjs --check   # fail if stale

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SCHEMA = resolve(here, "../src/protocol/schema.json");
const OUT = resolve(here, "../src/protocol/types.ts");

if (!existsSync(SCHEMA)) {
  console.error(
    `${SCHEMA} is missing. Run:\n  uv run python -m apps.gateway.protocol.export_schema`,
  );
  process.exit(1);
}

const schema = JSON.parse(readFileSync(SCHEMA, "utf8"));
const defs = schema.$defs ?? {};

const ident = (name) => name.replace(/[^A-Za-z0-9_]/g, "_");

function tsType(node, depth = 0) {
  if (!node) return "unknown";
  if (node.$ref) return ident(node.$ref.replace("#/$defs/", ""));
  if (node.anyOf) {
    const parts = node.anyOf.map((n) => tsType(n, depth + 1));
    return [...new Set(parts)].join(" | ");
  }
  if (node.enum) return node.enum.map((v) => JSON.stringify(v)).join(" | ");
  if (node.const !== undefined) return JSON.stringify(node.const);
  switch (node.type) {
    case "string":
      return "string";
    case "integer":
    case "number":
      return "number";
    case "boolean":
      return "boolean";
    case "null":
      return "null";
    case "array":
      return `${tsType(node.items, depth + 1)}[]`;
    case "object":
      if (node.additionalProperties && node.additionalProperties !== true) {
        return `Record<string, ${tsType(node.additionalProperties, depth + 1)}>`;
      }
      return "Record<string, unknown>";
    default:
      return "unknown";
  }
}

function renderInterface(name, def) {
  const required = new Set(def.required ?? []);
  const props = Object.entries(def.properties ?? {}).map(([key, prop]) => {
    const doc = prop.description ? `  /** ${prop.description.replace(/\s+/g, " ")} */\n` : "";
    const optional = required.has(key) ? "" : "?";
    const safeKey = /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(key) ? key : JSON.stringify(key);
    return `${doc}  ${safeKey}${optional}: ${tsType(prop)};`;
  });
  return `export interface ${ident(name)} {\n${props.join("\n")}\n}`;
}

const messages = schema.messages ?? {};
const byDir = (dir) =>
  Object.entries(messages)
    .filter(([, m]) => m.direction === dir)
    .sort(([a], [b]) => a.localeCompare(b));

const payloadOf = (m) => ident(m.payload.$ref.replace("#/$defs/", ""));

const lines = [
  "// GENERATED FILE -- do not edit.",
  "// Source: apps/gateway/protocol/catalog.py",
  "// Regenerate: uv run python -m apps.gateway.protocol.export_schema",
  "//             && node scripts/gen-protocol-types.mjs",
  "",
  `export const PROTOCOL_VERSION = ${schema.protocolVersion};`,
  `export const MAX_FRAME_BYTES = ${schema.maxFrameBytes};`,
  `export type Channel = ${schema.channels.map((c) => JSON.stringify(c)).join(" | ")};`,
  "",
  "export interface Envelope<T extends string, P> {",
  "  v: typeof PROTOCOL_VERSION;",
  "  t: T;",
  "  seq: number;",
  "  /** Unix milliseconds, sender clock. */",
  "  ts: number;",
  "  ch: Channel;",
  "  /** ULID. Required on every intent. */",
  "  cid?: string | null;",
  "  p: P;",
  "}",
  "",
  ...Object.entries(defs)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([name, def]) => renderInterface(name, def)),
  "",
  "export interface ClientMessages {",
  ...byDir("c2s").map(([t, m]) => `  ${JSON.stringify(t)}: ${payloadOf(m)};`),
  "}",
  "",
  "export interface ServerMessages {",
  ...byDir("s2c").map(([t, m]) => `  ${JSON.stringify(t)}: ${payloadOf(m)};`),
  "}",
  "",
  "export type ClientFrame = {",
  "  [T in keyof ClientMessages & string]: Envelope<T, ClientMessages[T]>;",
  "}[keyof ClientMessages & string];",
  "",
  "export type ServerFrame = {",
  "  [T in keyof ServerMessages & string]: Envelope<T, ServerMessages[T]>;",
  "}[keyof ServerMessages & string];",
  "",
  "export const CHANNEL_OF: Record<string, Channel> = {",
  ...Object.entries(messages)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([t, m]) => `  ${JSON.stringify(t)}: ${JSON.stringify(m.channel)},`),
  "};",
  "",
];

const out = lines.join("\n");

if (process.argv.includes("--check")) {
  if (!existsSync(OUT) || readFileSync(OUT, "utf8") !== out) {
    console.error(
      `src/protocol/types.ts is stale.\n` +
        `The gateway catalog changed. Regenerate:\n` +
        `  uv run python -m apps.gateway.protocol.export_schema\n` +
        `  node app/scripts/gen-protocol-types.mjs`,
    );
    process.exit(1);
  }
  process.exit(0);
}

writeFileSync(OUT, out);
console.log(`wrote ${OUT}`);
