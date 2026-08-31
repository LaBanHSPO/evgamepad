// Fail the web build when src/protocol/types.ts no longer matches the schema it came from.
//
// The Pydantic catalog in apps/gateway/protocol is the single source of truth. Both files here
// are generated; editing either by hand, or changing the catalog without regenerating, stops
// the build rather than shipping a HUD that disagrees with the gateway about the wire.

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const schemaPath = resolve(here, "../src/protocol/schema.json");
const typesPath = resolve(here, "../src/protocol/types.ts");

const REGENERATE = "cd apps/gateway && uv run python -m protocol.export_ts";

function fail(message) {
  console.error(`protocol types: ${message}\n  regenerate with: ${REGENERATE}`);
  process.exit(1);
}

let schema;
let types;
try {
  schema = readFileSync(schemaPath, "utf8");
  types = readFileSync(typesPath, "utf8");
} catch (err) {
  fail(`cannot read generated files (${err.message})`);
}

const expected = createHash("sha256").update(schema).digest("hex");
const declared = types.match(/^\/\/ schema-sha256: ([0-9a-f]{64})$/m)?.[1];

if (!declared) {
  fail("types.ts carries no schema-sha256 header");
}
if (declared !== expected) {
  fail(`types.ts was generated from a different schema\n  expected ${expected}\n  found    ${declared}`);
}

console.log("protocol types: up to date");
