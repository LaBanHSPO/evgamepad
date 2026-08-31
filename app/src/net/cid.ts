/**
 * ULIDs for intent idempotency.
 *
 * The gateway reserves a cid UNIQUE before it sends anything, so the cid *is* the guarantee that
 * a retry cannot become a second position. It has to be a real ULID — the gateway's envelope
 * validator rejects anything else — and it has to be unique even for two fires in the same
 * millisecond, which is why the random tail increments rather than being redrawn.
 */

const CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
const TIME_CHARS = 10;
const RANDOM_CHARS = 16;

let lastTime = 0;
let lastRandom: number[] = [];

function randomBytes(count: number): number[] {
  const out = new Uint8Array(count);
  if (typeof crypto !== "undefined" && crypto.getRandomValues) {
    crypto.getRandomValues(out);
  } else {
    for (let i = 0; i < count; i += 1) out[i] = Math.floor(Math.random() * 256);
  }
  return Array.from(out, (byte) => byte % 32);
}

function encodeTime(now: number): string {
  let time = now;
  let out = "";
  for (let i = TIME_CHARS - 1; i >= 0; i -= 1) {
    out = CROCKFORD[time % 32] + out;
    time = Math.floor(time / 32);
  }
  return out;
}

/** Increment the random tail in place, so same-millisecond ULIDs stay ordered and distinct. */
function bumpRandom(values: number[]): number[] {
  const next = [...values];
  for (let i = next.length - 1; i >= 0; i -= 1) {
    if (next[i] < 31) {
      next[i] += 1;
      return next;
    }
    next[i] = 0;
  }
  return randomBytes(RANDOM_CHARS);
}

export function newCid(now: number = Date.now()): string {
  if (now === lastTime && lastRandom.length > 0) {
    lastRandom = bumpRandom(lastRandom);
  } else {
    lastTime = now;
    lastRandom = randomBytes(RANDOM_CHARS);
  }
  return encodeTime(now) + lastRandom.map((value) => CROCKFORD[value]).join("");
}

/** Same shape the gateway's envelope validator accepts. */
export function isCid(value: string): boolean {
  return value.length === 26 && [...value].every((char) => CROCKFORD.includes(char));
}
