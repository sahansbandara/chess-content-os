# Chess Content OS — Build Plan

> Created: 2026-08-19
> Status: awaiting owner review
> Owner constraint: ~2 years of university remaining. Target steady-state cost is
> ~10 min/day approving content, plus ~30 min/week recording voice.

## Where the project actually stands

| Layer | State |
|---|---|
| Board calibration, crop, evidence extraction | working |
| 64-square perception → piece-placement FEN | working |
| Temporal state sequence extraction | working |
| Legal bridge reconstruction (`python-chess`) | working |
| Ambiguity audit | working — 14 unique, 5 ambiguous |
| Local visual disambiguation | working — Bridge 10 resolved |
| Constrained VLM evidence comparison | control passed once; needs repeat + shuffle validation |
| Provider fallback client | working |
| **`moves.json` contract** | **does not exist** |
| **Stockfish analysis** | **not installed** |
| **Moment selection** | **does not exist** |
| **Renderer** | **does not exist** |
| **Script, voice, captions** | **does not exist** |
| **Validators, approval, publishing, analytics** | **do not exist** |

10,233 lines of Python exist. All of it is the truth layer. Nothing the audience
would ever see has been built. The plan below deliberately inverts that.

`src/agents/`, `src/approval/`, `src/database/`, `src/publishers/` and
`src/validators/` are empty directories.

## Sequencing principle

Build the half that reaches an audience, using the truth layer that already
works, and let a human answer what perception cannot. Do not resolve Bridges
16–19 algorithmically — they sit in a drawn endgame shuffle that a 35-second
short cuts anyway.

Automate only after one video has been made by hand end to end.

---

## Phase 0 — Prerequisites

Small, unblocking, no dependencies between them.

| # | Task | Done when |
|---|---|---|
| 0.1 | Install Stockfish, pin the version in `MEMORY.md` | `stockfish` responds to `uci` from `uv run` |
| 0.2 | Choose piece artwork licensed for commercial use; rasterise to PNG sprites; record the source and licence in `design.md` | sprite set in `assets/renderer/pieces/`, licence recorded |
| 0.3 | Choose a commercially-licensed font; embed locally | font in `assets/renderer/fonts/`, licence recorded |
| 0.4 | Build the geometric mascot sprite set — idle, happy, shocked, thinking, wincing, celebrating, plus a mouth-shape strip | `assets/renderer/mascot/` populated, swappable by folder |
| 0.5 | Repeat the Bridge 10 Gemini control 3–5× and once with shuffled/reversed frames | result recorded in `MEMORY.md`; constrained Gemini either cleared for use on unresolved bridges or dropped from disambiguation |

0.5 is validation debt, not a blocker for Phase 1 — Phase 1 relies on human
confirmation, not on the VLM.

---

## Phase 1 — Recording → finished mp4

**Goal: one postable 9:16 short, produced from the existing prototype recording,
posted by hand.** No Telegram, no OAuth, no cron.

### 1.1 Freeze the `moves.json` contract

The keystone. Write it by hand first from the known 36-move sequence, then make
the extractor emit it. Everything downstream reads only this file.

```jsonc
{
  "schema_version": "1.0",
  "content_id": "2026-08-19-duolingo-001",
  "source": {
    "path": "assets/raw/material-3cc02343.mov",
    "kind": "duolingo_screen_recording",
    "duration_s": 41.40,
    "fps": 60,
    "board": { "x": 0, "y": 962, "size_px": 1320, "square_px": 165,
               "orientation": "black_perspective_180" }
  },
  "start_position": {
    "piece_placement": "r1bqr1k1/pp3ppp/2n2n2/3pN3/3P4/1BB5/PPPQ1PPP/R3K2R",
    "side_to_move": "w",
    "castling": "KQ-",
    "note": "side_to_move and castling are inferred, not observed"
  },
  "owner_side": "black",
  "moves": [
    {
      "ply": 1,
      "san": "Bxd5",
      "uci": "b3d5",
      "side": "w",
      "t_start_s": 13.75,
      "t_end_s": 13.92,
      "verification": "unique",
      "bridge_id": 1,
      "candidates_considered": 1,
      "evidence": []
    }
  ],
  "pgn": "...",
  "verification_summary": {
    "unique": 0, "visual_resolved": 0, "model_supported": 0,
    "human_confirmed": 0, "unresolved": 0
  }
}
```

`verification` is one of `unique`, `visual_resolved`, `model_supported`,
`human_confirmed`, `unresolved`. A `moves.json` containing any `unresolved` move
must not reach the renderer.

**Done when:** a hand-written `moves.json` for the prototype game validates
against a schema validator, and `src/validators/` rejects an illegal sequence,
a same-side consecutive pair, and an `unresolved` entry.

### 1.2 Human move confirmation (CLI)

Print the reconstructed sequence, mark uncertain bridges, show candidate paths
and evidence frame paths, accept confirm-or-correct input, write
`verification: "human_confirmed"` on the answers.

**Done when:** Bridges 16–19 are confirmed by hand in under a minute and the
resulting `moves.json` has zero `unresolved` entries.

### 1.3 Stockfish analysis

Replay `moves.json` into a legal board, evaluate every position, classify each
move by **win-percentage delta** (Lichess-style), not raw centipawns.

| Label | Win-% drop |
|---|---|
| Blunder | > 20 |
| Mistake | 10–20 |
| Inaccuracy | 5–10 |
| Good / Best | < 5 |

Also capture: best move, refutation line, eval before and after. Written to a
separate `analysis.json` — engine output never mutates move truth.

**Done when:** every move carries a label and a best-move alternative, and the
thresholds are unit-tested at their boundaries.

### 1.4 Moment selection

Pick the **owner's** largest win-% drop. Pad with two moves of setup and the
punishment. Emit a scene list.

**Done when:** the selector picks a defensible teaching moment from the
prototype game and the output fits a 30–40 s narration.

### 1.5 Script generation

Fixed four-beat structure: the mistake → what it cost → what to play instead →
the pattern to avoid. Generated from `analysis.json` facts only. Must satisfy
the positioning rules in `BRIEF.md` — no claimed expertise, avoidance framing,
a question as CTA.

**Done when:** a generated script passes a positioning lint (no
authority-voiced phrasing) and every chess claim traces to `analysis.json`.

### 1.6 Voice + alignment

Owner records the script; the pipeline measures segment durations and builds an
audio-driven timeline. Kokoro-82M is wired as the non-personal-content path.

**Done when:** an audio file plus a segment timing map exists, and video length
follows narration length rather than a fixed constant.

### 1.7 Renderer

HTML/CSS scene system per `design.md`. Driven by `renderFrame(n)` — no
wall-clock animation. Headless screenshot per frame → PNG sequence.

Order of work: board and piece tweening → hook and caption text → eval bar →
move-quality badges and board effects → mascot and speech bubble. A complete,
postable video exists after the eval bar; the mascot lands on top.

**Done when:** identical `moves.json` plus identical assets produce a
byte-identical PNG sequence across two runs, and a renderer test proves the move
sequence is unaltered.

### 1.8 Mux

FFmpeg: PNG sequence + audio + burned captions → 1080×1920 H.264 mp4.

**Done when:** the file plays correctly on a phone, captions are legible muted,
and nothing readable sits in a platform dead zone.

### Phase 1 acceptance

One mp4, from the existing prototype recording, that the owner is willing to
post publicly. Posted by hand. Nothing automated yet.

---

## Phase 2 — Hands-off loop

Only after Phase 1 has produced a video worth posting, and ideally after ~10
have been posted by hand so the format is proven.

| # | Task |
|---|---|
| 2.1 | Content evaluator — rejects illegal positions, unreadable text, wrong duration, missing CTA, positioning violations |
| 2.2 | Run/content ID threaded through every stage; workflow status model (`ingested` → `published`) |
| 2.3 | SQLite results store |
| 2.4 | Telegram bot: move-list confirmation message |
| 2.5 | Telegram bot: final approval message — video, caption, verification summary, approve/reject/revise |
| 2.6 | Publishing kill switch — single config flag, no credentials needed for local generation |
| 2.7 | YouTube Shorts publisher with idempotency (no duplicate posts on retry) |
| 2.8 | Orchestrator + cron: nightly batch, drafts waiting by morning |

**Phase 2 acceptance:** drop a recording in `inbox/`, receive two Telegram
messages, tap twice, video is live. ~10 min/day.

---

## Phase 3 — Volume and feedback

| # | Task |
|---|---|
| 3.1 | Lichess puzzle-database lane feeding `moves.json` directly (skips stages 1–4 entirely — Phase 1's renderer works unchanged) |
| 3.2 | Analytics snapshots per publication |
| 3.3 | Idea engine — proposes content from measured performance, not generic trends |
| 3.4 | Promote high-performing examples into skill benchmark libraries |
| 3.5 | Second platform (Instagram Reels via Graph API, or TikTok after app review) |

---

## Non-goals

- Resolving Bridges 16–19 algorithmically
- Autonomous publishing without human approval
- A web dashboard
- Migrating to a large agent framework
- MCP servers built to look agentic rather than to remove work
- Reading Duolingo's own coach graphics by computer vision — Stockfish gives the
  same labels deterministically, plus the refutation line, on any source
- Any third-party character, mascot, branding, or app UI in published output

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Mascot art quality caps perceived professionalism | Content looks amateur despite correct pipeline | Sprite-swappable interface; commission a character sheet when traction justifies it |
| Templates break on a second recording (different theme, device, resolution) | Perception layer needs recalibration per source | Regression fixtures before further scanner changes; recalibration is a documented procedure, not a rebuild |
| One game ≈ one short — insufficient volume for daily posting | Slow audience growth | Phase 3 puzzle lane reuses the whole renderer; playing volume becomes production |
| Positioning requires real improvement | Arc goes stale in ~6 months if rating is flat | Rating journey is the spine; playing regularly is production, not hobby |
| Voice recording competes with degree | Pipeline stalls in exam periods | Batch-record weekly; keep a buffer of approved drafts; Kokoro lane can carry non-personal content through a crunch |
| Automatic push to `main` with no review gate | A bad commit reaches the remote instantly | Private repo, fast-forward only, no force-push, secrets check in the wrap-up checklist, full history for reverts |
| Recording another company's app at monetised volume | Platform or legal exposure | Own original assets everywhere in output; positioning is commentary on own play; a Lichess/PGN input path stays available and needs no CV at all |

---

## Honest estimate

Phase 0: a few evenings, mostly waiting on asset decisions.
Phase 1: the substantial one. The renderer is the bulk of it.
Phase 2: smaller than it looks — the pieces are well-understood, but OAuth and
bot setup always take longer than expected.

No calendar dates. University load makes them fiction.

## What is needed from the owner

1. Review this plan and the `moves.json` schema in 1.1 — the schema is expensive to change once consumers exist.
2. Decide the mascot art path (geometric now vs commission first).
3. Confirm willingness to record voice weekly, since the positioning depends on it.
4. Confirm the target chess platform stays Duolingo, given a Lichess/PGN path would remove the entire perception layer.
