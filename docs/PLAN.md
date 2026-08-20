# Chess Content OS — Build Plan

> Created: 2026-08-19
> Status: awaiting owner review
> Owner constraint: ~2 years of university remaining. Target steady-state cost is
> ~10 min/day approving content, plus ~30 min/week recording voice.

## Where the project actually stands

> Updated 2026-08-19 after the extraction work. Verify against the repo before
> trusting any row — this table has been stale before.

| Layer | State |
|---|---|
| Board calibration, crop, evidence extraction | working |
| Dense per-square tracking + temporal smoothing | working — `src/workers/dense_board_track.py` |
| Material sanity (position + transition) | working — `src/validators/material_sanity.py` |
| Misread repair + transient dropping | working — `src/validators/constrained_reclassify.py` |
| Difference-guided bridge search | working — `src/perception/bridge_search.py` |
| **End-to-end extraction** | **working — full 96-ply game, `complete=True`** |
| `moves.json` contract + validator | working — 6 hard-fail rules, `src/validators/moves_contract.py` |
| Stockfish analysis | working — Stockfish 18, depth 20, `src/analysis/` |
| Moment selection | partial — owner's worst moment only |
| Renderer | working — 1080×1920, board + eval bar + captions |
| Mascot, script, voice, burned captions | not built |
| Approval, publishing, analytics | not built — `src/approval/`, `src/publishers/`, `src/database/` are empty |

Two shorts have been rendered from real verified moves. The extraction layer is
no longer the blocker; presentation quality is.

Known gaps: three ambiguous bridges need human confirmation, the renderer's
piece glyphs are crude, there is no mascot, and no video has voice or captions.

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
| 0.2 | Draw original vector piece glyphs in the renderer, matching the mascot's outline weight and palette | all 12 glyphs render legibly at board scale; nothing to license, nothing to attribute |
| 0.3 | Choose a commercially-licensed font; embed locally | font in `assets/renderer/fonts/`, licence recorded |
| 0.4 | Draw the pawn mascot as renderer vector shapes and build the popup component around **two** states (`intro_peek`, `deflated`) | popup proven in a real 1080×1920 test render, slide-in/settle/exit timing per `design.md`, before the other eight states are drawn |
| 0.5 | Repeat the Bridge 10 Gemini control 3–5× and once with shuffled/reversed frames | result recorded in `MEMORY.md`; constrained Gemini either cleared for use on unresolved bridges or dropped from disambiguation |

0.5 is validation debt, not a blocker for Phase 1 — Phase 1 relies on human
confirmation, not on the VLM.

---

## Phase 1 — Recording → finished mp4

**Goal: one postable 9:16 short, produced from the existing prototype recording,
posted by hand.** No Telegram, no OAuth, no cron.

### 1.1 Freeze the contracts

Two files, and the split matters: **`moves.json` carries truth only. Presentation
never touches it.**

```text
moves.json     what happened on the board, and how well we know it
analysis.json  what the engine thinks of it
scene.json     how it gets presented (derived from the two above)
```

Write each by hand first from the known prototype game, then make the pipeline
emit them.

#### `moves.json` — truth

Schema follows the model in `PROJECT_MASTER_CONTEXT.md` §8, which is stricter
than the first draft of this plan and replaces it.

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

  // Observed board facts and inferred metadata are never mixed without provenance.
  "start_position": {
    "piece_placement": { "value": "r1bqr1k1/pp3ppp/2n2n2/3pN3/3P4/1BB5/PPPQ1PPP/R3K2R",
                         "provenance": "observed" },
    "side_to_move":    { "value": "w",  "provenance": "inferred" },
    "castling_rights": { "value": null, "provenance": "unknown"  },
    "en_passant":      { "value": null, "provenance": "unknown"  }
  },

  "owner_side": "black",

  "moves": [
    {
      "ply": 13,
      "uci": "d5e5",            // canonical representation
      "san": "Rdxe5",           // derived from the board, asserted against uci
      "side": "w",
      "t_start_s": 16.37,
      "t_end_s": 16.55,

      "verification_status": "verified",           // verified | human_confirmed | unresolved
      "verification_basis": ["legal_path", "local_visual"],

      // Model support is an annotation, never a basis. It cannot make a move verified.
      "model_support": {
        "provider": "gemini",
        "model": "gemini-3.6-flash",
        "supported": true,
        "confidence": "medium"
      },

      "bridge_id": 10,
      "candidates_considered": 2,
      "evidence": ["output/evidence_test/bridge10_control/frame_034_t016.333.jpg"]
    }
  ],

  "pgn": "...",
  "verification_summary": { "verified": 0, "human_confirmed": 0, "unresolved": 0 }
}
```

`verification_basis` values: `unique_path`, `legal_path`, `local_visual`,
`human_confirmed`. `model_support` is deliberately not among them.

#### Renderer gate

```text
verification_status ∈ {verified, human_confirmed}   →  renderer allowed
verification_status == unresolved                    →  renderer blocked
model_support.supported == true, basis insufficient  →  renderer blocked
```

A VLM agreeing with a candidate is evidence *about* the world, not authority over
it. It can raise confidence in a move that already has deterministic or human
backing; it can never carry a move on its own.

#### Validator rules (all hard failures)

1. The full sequence must be legal from `start_position`.
2. No same-side consecutive moves.
3. For every move, `san` must equal the SAN `python-chess` derives for `uci` on the
   reconstructed board. A mismatch is a hard failure, not a warning — this is what
   prevents UCI and SAN drifting apart silently.
4. No `unresolved` move may reach any downstream consumer.
5. `model_support.supported == true` with an empty or model-only
   `verification_basis` is a hard failure.
6. Every `start_position` field must carry a `provenance`.

#### `scene.json` — presentation, derived

Mascot cues must **not** be hand-authored at absolute timestamps. Anchor them to
plies and derive the time at render, or every cue goes stale the moment the
selected moment shifts by a few frames.

```jsonc
{
  "schema_version": "1.0",
  "content_id": "2026-08-19-duolingo-001",
  "mascot_events": [
    {
      "id": "ev_hook",
      "anchor": { "kind": "video_start" },
      "offset_s": 0.0,
      "asset": "intro_peek",
      "edge": "right",
      "duration_s": 3.0,
      "bubble": "2 mistakes and I got mated."
    },
    {
      "id": "ev_blunder",
      "anchor": { "kind": "ply", "ply": 18 },   // time resolved from moves.json
      "offset_s": 0.4,
      "asset": "facepalm",
      "edge": "left",
      "duration_s": 2.5,
      "bubble": "I completely missed this."
    }
  ]
}
```

Budget: **three mascot popups per short** — hook, mistake reaction, outro CTA.
Each popup costs roughly 1.2s of slide-in, settle and exit; five popups spend ~6s
of a 36s video on the character moving and never let the board hold attention for
longer than 8s. The explain beat works as voice over board.

#### Occlusion validator

`PROJECT_MASTER_CONTEXT.md` §2.6 says not to cover tactically important squares.
Make that a mechanism rather than an intention: the renderer knows the discussed
move's from/to squares from the anchored ply. If the mascot's settled bounding box
intersects either square, fail the scene — then reposition to the opposite edge or
drop the cue. An unenforced rule will be broken on the first busy position.

**Done when:** hand-written `moves.json`, `analysis.json` and `scene.json` exist
for the prototype game and validate; and `src/validators/` demonstrably rejects
each of an illegal sequence, a same-side consecutive pair, a UCI/SAN mismatch, an
`unresolved` move reaching the renderer, a model-only verification basis, a
missing provenance field, and an occluding mascot cue.

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
