---
title: "Phase 8: Voice — capture, upload, whisper.cpp, coach TTS"
status: deferred
phase: 8
priority: P1
effort: 14h
dependencies: [1, 3, 4, 5]
---

# Phase 8: Voice — capture, upload, whisper.cpp, coach TTS

> **Deferred by the player, 2026-08-31.** Skipped in the build order, to be picked up later.
> The runtime this phase needs — `ffmpeg` and `whisper-cli` — exists only in the Docker image, not
> in the build environment, so its transcription path would be as unverifiable here as the broker
> link. Nothing downstream is blocked: phase 9's voice-arousal input is an optional 5% component
> that redistributes when absent, and phase 3 already ships the LB+RB chord as an inert control
> event. Phase 11's memo evidence degrades the same way.
>
> Still owed when it resumes: the `voice` channel messages are already in the frozen catalog, the
> config blocks and their boot-fails already exist, and the image already carries the `tiny.en`
> floor — so this phase starts at its step 4, not at zero.
>
> Phase 9 shipped after this and added two items to that list. Both are built and tested; only their
> feeds are missing, and both feeds are memo-shaped:
>
> - `TiltTracker.observe_memo()` and `.acknowledge()` halve the recency terms, which is the way out
>   of a tilt cooldown. Nothing calls either one yet, so today the only way out is to wait the 300 s.
>   Wire them from the memo pipeline and the scorched-band prompt.
> - `arousal.ts` — the `AnalyserNode` RMS on the PTT stream — plus the `speechRate_z` / `loudness_z`
>   feed into `TiltInputs`. The component and its 5% weight already exist and renormalise away while
>   absent; only the measurement is missing.
> - Phase 11's Preparation and Review axes ask for memo evidence. `VOICE_CAPTURE_BUILT` in
>   `score/repository.py` is `False`, so those sub-items drop out and the axes renormalise rather
>   than scoring the install. Flip it to `True` when capture lands and they become live evidence —
>   and a skipped memo becomes a genuine miss, which is the intended behaviour.
>
> Phase 10 (replay) added one more, on the same terms — built, tested, unfed:
>
> - `GET /api/replay/:cid` serves `memos: []`, and the replay transport's audio sync is complete
>   (offset from the stored `durMs`, silent outside the span, held while scrubbing, muted above 2x).
>   Populate the memo index and add `GET /api/voice/:id/audio`, which the surface already points at,
>   and memo pins appear on the rail with no change to the replay code.
>
> Phase 12 (journal) adds the last of them: `TradeFacts.has_memo` is `None` (not captured) and the
> trade detail's `memos` is empty, so the after-stage execution score drops the item and
> renormalises. Populate the memo index and the item becomes live evidence.

## Overview

You cannot type a journal while trading. You can talk. Hold `LB + RB`, say why you took it, let go —
the memo is transcribed on the VPS by whisper.cpp and attached to the trade. Point the desk at an AI
tab first and the same gesture asks the coach a question instead.

**Voice is never on the order path.** It cannot place, close, modify, or navigate. That is enforced
by a config boot-fail and by the push-to-talk state machine being enterable only from order-FSM
`IDLE` or `LOCKED` — not by convention.

Audio never leaves the box: capture in Chrome, transcribe locally, no cloud STT.

## Context Links

- [plan.md](./plan.md)
- [Phase 1 — `voice` channel, HTTP surfaces, boot-fails, image packages](./phase-01-repo-protocol-docker-config.md)
- [Phase 3 — pad FSM, desk tabs, Settings overlay](./phase-03-web-game-and-8bitdo-client-agent.md)
- [Phase 4 — `ai.ask`, copilot loops, `speak` field](./phase-04-ai-desk-sentinel-news-volman.md)
- [Phase 5 — target VPS probe and verified model files](./phase-05-ubuntu-docker-deploy.md)
- https://github.com/ggml-org/whisper.cpp

## Requirements

### Capture

- Functional: `MediaRecorder` mime probe in this order, winner logged on first run like the pad
  mapping probe: `audio/webm;codecs=opus` -> `audio/webm` -> `audio/mp4` -> `''` (UA default).
  All fail -> PTT disabled, HUD reads "mic unsupported". No WAV-encoder polyfill in v1
- Functional: `getUserMedia({audio:{channelCount:1, echoCancellation:true, noiseSuppression:true, autoGainControl:true}})`
  behind an explicit **"enable mic"** button in Settings reached through GameOverlay, then held for the
  session. `voice.hold_stream: false` releases between presses for anyone who dislikes the persistent
  tab recording indicator, at the cost of 200-400 ms acquisition per press
- Functional: one `MediaRecorder` per press, `audioBitsPerSecond: 24000`, mono, one blob on `stop`.
  **No `timeslice` chunking** — whisper.cpp is a batch binary and partial chunks would need VAD
  segmentation to avoid word-boundary corruption. Stated non-goal
- Functional: the client measures `durMs = stopTs - startTs` and sends it. Chrome's MediaRecorder
  WebM carries no header duration, so `audio.duration` is `Infinity` and must never be trusted
- Non-functional: `voice.max_seconds: 60`, client stops with a visible countdown

### Push-to-talk binding and routing

- Functional: **`LB + RB` chord**. Both down inside a 120 ms window -> suppress both timeframe
  actions for that press and enter PTT. A single-bumper timeframe change fires **on release** when
  the other bumper was never down during the press
- Functional: keyboard `V` hold is an equal-status fallback (voice is not an order path, and this is
  what keeps the feature alive when the dongle is out)
- Functional: PTT is a **parallel** 3-state machine `VOICE_IDLE -> VOICE_REC -> VOICE_UPLOAD` that
  emits no order-FSM transition of its own. Enterable only from order-FSM `IDLE` or `LOCKED`.
  Entering `CLUTCH` while recording performs a **graceful stop-and-submit**, never a discard, and
  blocks new PTT until back to `IDLE`
- Functional: routing needs **zero new bindings** — GameOverlay owns desk-tab selection, and the
  transcript goes wherever the active tab points, which is on screen before you speak:

  | active desk tab | transcript becomes |
  |---|---|
  | `[Memo]` or desk closed | `voice_memo` row, linked to the open position's `cid`, else to the session and the last closed trade |
  | `[Advise]` / `[Research]` / `[News]` | the question text of `ai.ask {kind}` — the existing phase 4 path |

- Non-functional: boot-fail if `voice.bindings` resolves to LT/RT/A/B/X/Y (phase 1). Structural
  guarantee that voice cannot reach the order path

### Transport

- Functional: `POST /api/voice/memo` multipart, same origin, `EV_WS_TOKEN` bearer + Origin allowlist
- Functional: returns **`202 {voiceId}` immediately** — the request never waits on whisper. The
  result arrives on the `voice` channel as `voice.transcript`, so a dropped socket does not lose it
  (it replays on `resync`) and the HUD shows a "transcribing…" pill, not a hung request
- Functional: caps — `voice.max_bytes: 262144` -> 413; `voice.max_uploads_per_hour: 60` -> 429
- Non-functional: audio **never** rides the WS. Base64 in a 64 KiB envelope is ~16 s per frame plus
  chunking and reordering, on the socket whose whole job is prioritising order acks

### Transcription

- Functional: whisper.cpp runs as a **`child_process.spawn` of `ev-gateway`**. Compose stays at two
  services. Containment is `nice -n 19` + `taskset` pinning off core 0 + **concurrency 1** (queue
  depth 1; a third request is rejected, not queued) + `voice.stt_timeout_s: 60` SIGKILL
- Functional: one ffmpeg invocation produces both outputs — 16 kHz mono PCM WAV for whisper (deleted
  after) and a **seekable `.ogg` remux** archived for replay, which fixes the WebM seek bug for free
- Functional: boot benchmark on the shipped 11 s sample; record the real-time factor. VPS is 4+ vCPU
  / 4 GB+, so `small.en` is the target tier. If RTF > 1.5, downgrade one tier and **log it**; ladder
  is `small.en -> base.en -> tiny.en -> voice.enabled=false`. Never silently slow
- Functional: `ggml-tiny.en` (~75 MB) is baked into the gateway image as the guaranteed floor;
  `deploy/fetch-models.sh` pulls checksum-verified `small.en` into the journal volume
- Non-functional: expected end-to-end for a 10 s memo on `small.en` — finalize <100 ms + upload
  100-300 ms + warm spawn 100-400 ms + decode 6-10 s = **7-11 s to transcript**. Ask-the-coach adds
  the existing 1-5 s copilot budget. The HUD sets that expectation with a pill, never a blocking spinner
- Non-functional: `voice.stt.mode` boot-fails on anything but `local | off` — there is no cloud path,
  so audio cannot leave the box by configuration error

### Failure degradation

- Functional: mic denied / no device / no supported mime -> PTT disabled, desk still takes typed
  text, nothing else affected
- Functional: upload fails (offline / 413 / 429) -> one retry, then offer the raw blob as a download
  link so the memo is not lost; HUD says "not uploaded"
- Functional: **whisper missing / timeout / nonzero exit -> the audio is still stored and still
  linked to the trade.** `voice.transcript {ok:false, reason}`, row carries
  `transcript: null, stt_status: 'failed'`, replay still plays it. The coaching value survives total
  STT failure — this is the most important row in this table
- Functional: transcript routed to `ai.ask` while the coach is offline -> degrades to a memo with a
  HUD note, never dropped
- Functional: `voice.enabled: false` removes the feature; nothing else depends on it

### Coach TTS

- Functional: `voice.tts: 'browser' | 'off'`, **default `off`**, HUD toggle. Browser
  `speechSynthesis` only — Piper would cost another binary, a ~60 MB model, and VPS CPU we just
  spent on whisper, to speak text already on screen. Documented as a drop-in behind the same enum
- Functional: speak only the copilot's `speak` field (<=240 chars, phase 4), chunked by sentence to
  dodge Chrome's ~15 s utterance truncation, `cancel()` on new advice
- Non-functional: **auto-mute while `ARMED` or `FIRE`**; never speak a dollar figure, consistent with
  the existing rule that no notification carries one

## Architecture

```
Chrome  LB+RB hold -> MediaRecorder(opus) -> blob
   |  POST /api/voice/memo (multipart, 202 {voiceId})
   v
ev-gateway
   ffmpeg -> 16k mono wav (whisper)  +  .ogg remux (archive, seekable)
   spawn: nice -19 taskset -c N whisper-cli -m small.en   [concurrency 1, 60s kill]
   -> voice_memo row (audio always; transcript maybe)
   -> WS `voice.transcript` on the `voice` channel
   -> if routed to a desk AI tab: existing phase 4 ai.ask {kind:'coach'}
```

## Related Code Files

- Create: `apps/web/src/voice/ptt.ts` (chord detection, parallel FSM, mime probe)
- Create: `apps/web/src/voice/recorder.ts` (getUserMedia, MediaRecorder, durMs)
- Create: `apps/web/src/voice/upload.ts` (multipart POST, retry, download fallback)
- Create: `apps/web/src/voice/tts.ts` (speechSynthesis, sentence chunking, arm-mute)
- Create: `apps/web/src/voice/ptt.test.ts` (chord vs single bumper; CLUTCH stop-and-submit; never emits an order transition)
- Create: `apps/web/src/hud/MemoTab.tsx` (desk `[Memo]` tab, transcript list)
- Create: `apps/gateway/voice/routes.py` (`POST /api/voice/memo`, `GET /api/voice/:id/audio`)
- Create: `apps/gateway/voice/stt.py` (ffmpeg + whisper spawn, queue of 1, timeout, tier ladder)
- Create: `apps/gateway/voice/test_stt.py` (timeout path, nonzero exit, audio survives)
- Create: `apps/gateway/voice/bench.py` (boot benchmark + tier selection + log line)
- Create: `apps/gateway/db/migrations/006-voice.sql`
- Modify: `deploy/fetch-models.sh` (consume/verify the phase 5 model candidate)
- Modify: `apps/gateway/journal/writer.py` (`voice_memo` writes)
- Modify: `apps/web/src/hud/CopilotDesk.tsx` (5th tab; routing by active tab)
- Modify: `apps/web/src/pad/fsm.ts` (bumper fire-on-release when the chord did not engage)
- Modify: `config/default.yaml` (`voice.*`)
- Modify: `README.md` (enable mic, PTT gesture, what voice cannot do, model tiers)

## Implementation Steps

1. Apply `006-voice.sql`; add the MIME probe and Settings mic enable through GameOverlay; log the winner.
2. PTT chord in `ptt.ts` with the bumper fire-on-release change; unit tests first — the invariant
   that PTT emits no order transition is the test that matters.
3. Upload route with caps, 202, and the download fallback.
4. ffmpeg dual-output; `.ogg` archived under `<vol>/voice/<date>/<ulid>.ogg`.
5. whisper spawn with `nice`/`taskset`/concurrency 1/timeout; boot benchmark and tier ladder.
6. `voice_memo` rows; `voice.transcript` on the `voice` channel; `resync` replay.
7. Desk `[Memo]` tab and tab-based routing into the existing `ai.ask`.
8. TTS behind the toggle, default off, arm-muted.
9. Load test: fire 20 orders during a `small.en` transcode and measure order-ack p99 delta.

## Todo

- [ ] `006-voice.sql` + mime probe + mic enable in Settings
- [ ] LB+RB chord PTT; bumpers fire on release
- [ ] PTT provably cannot emit an order transition
- [ ] `POST /api/voice/memo` 202 + caps + fallback
- [ ] ffmpeg wav + seekable ogg
- [ ] whisper spawn, concurrency 1, timeout, tier ladder
- [ ] Audio survives STT failure, still linked to the trade
- [ ] `[Memo]` tab + routing by active tab
- [ ] TTS toggle, default off, arm-muted
- [ ] Order-ack p99 delta measured under transcode load

## Success Criteria

- [ ] Holding `LB + RB` in `IDLE` records; releasing produces a transcript on the HUD in under ~12 s
      for a 10 s memo
- [ ] The same gesture with `[Advise]` active asks the coach instead, via the existing `ai.ask` path
- [ ] Tapping `LB` alone still changes timeframe, and does not start a recording
- [ ] Entering `CLUTCH` mid-recording submits the memo and does not cancel the arm or fire anything
- [ ] Killing `whisper-cli` mid-run leaves the audio stored, linked to the trade, and playable in replay
- [ ] `voice.stt.mode: cloud` refuses to boot; `voice.bindings: [RT]` refuses to boot
- [ ] Firing 20 orders during a transcode moves order-ack p99 by less than 10 ms
- [ ] `voice.enabled: false` leaves the rest of the game untouched

## Risk Assessment

- **whisper steals CPU from the order path** — signal: ack p99 rises under transcode. Response:
  `taskset` reserves core 0 via the kernel, not `nice` alone; concurrency 1; the load test above is
  the gate. If it still regresses, drop a tier before reaching for a second service.
- **`LB + RB` is uncomfortable to hold for 30 s** — signal: the player stops recording memos.
  Response: keyboard `V` is equal-status; L4/R4 paddles are the alternative if the phase 3 probe
  found them.
- **Chord misfires as a timeframe change** — signal: chart jumps when starting a memo. Response:
  120 ms window plus fire-on-release; unit-tested both ways.
- **Recording indicator all evening** — signal: the player finds it creepy. Response:
  `voice.hold_stream: false`, at 200-400 ms latency per press. Pick before this phase ships.
- **Transcript quality on trading jargon** — signal: "XAUUSD" comes back as "exhaust". Response:
  `small.en` tier plus whisper's prompt-bias list seeded with the symbol basket and method
  vocabulary. Accept imperfection: the audio is retained and is the real record.
- **Model download fails on a fresh box** — signal: gateway boots on `tiny.en` forever. Response:
  the baked floor means voice always works; the tier is logged at boot so the degradation is visible.

## Security Considerations

- Transcripts are player-authored **untrusted text**: escape, never `{@html}`; they reach the LLM as
  **user** messages only, never as system prompt or instructions (phase 4 amendment).
- `GET /api/voice/:id/audio` builds its path from the DB row's ULID, **never** from a client-supplied
  string — no path traversal.
- Audio never leaves the VPS; there is no cloud STT code path to misconfigure.
- `voice.audio_retention_days: 365` drops audio and keeps transcripts; retention is hygiene, not a
  size constraint (~12 MB/month).

## Next Steps

Phase 10 plays these memos back at their recorded timestamp inside the trade replay.
