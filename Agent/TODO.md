# Chess Content OS — TODO

> Last updated: 2026-08-20
> This file replaces the generic template task list with the actual Chess Content OS roadmap.

## Current milestone

**Milestone: confirm the three ambiguous bridges, then make the video look good.**

Extraction is solved. `src/workers/extract_game.py` reconstructs the complete
96-ply game from the recording with `complete=True`, 0 impossible positions and
0 impossible transitions. Two shorts have been rendered from verified moves.

The blocker is no longer truth. It is presentation: crude piece glyphs, no
mascot, no voice, no captions — and three bridges the board genuinely cannot
disambiguate.

Full phased plan: `docs/PLAN.md`.

## Current — next three tasks, in order

- [x] **Human confirmation CLI** — `src/workers/confirm_bridges.py`, 11 tests
  (`tests/test_confirm_bridges.py`). Shows each candidate line with its
  timestamp, accepts a choice interactively or via repeatable `--choose T=INDEX`,
  and writes `verification_status: human_confirmed` /
  `verification_basis: ["human_confirmed"]` for the plies inside the bridge.
  It refuses rather than guesses: an unanswered bridge, an out-of-range index,
  or a chosen line that does not replay to the observed final board all raise
  instead of writing a file. Candidate #1 never becomes truth by default.

- [x] **The recording is a review session, not a game — handled.** Every frame
  from 0.2s to 40s is Duolingo's *"Review your game"* screen, and the review
  steps **backwards** to demonstrate better moves. The reconstructor assumed
  states only move forward, so it bridged each rewind by inventing plies.

  `src/validators/review_rewind.py` splits observed states into the replayed
  game and the demonstrations: the game advances only while the review sits on
  the newest position it has ever shown, and anything observed behind that tip
  is a demonstration. Wired into `extract_game.clean()`, 6 tests.

  Result on the prototype recording: 2 rewinds found (t=21.83 back to t=20.30,
  t=24.80 back to t=20.83), 2 demonstrated states dropped, and **plies 57-64 of
  the old 96-ply sequence deleted** — `Re5 Kf7 Rf5+ Ke6 Re5+ Kf7 Rf5+ Kg6` was
  the review rewinding, showing the coach's suggested `Ke6` ("Next time, there's
  a better move for that king", t=22.4s, eval flips `BIG DISADVANTAGE` →
  `EQUAL CHANCES`), then rewinding again to what was actually played. One of
  those fabricated positions had a black king standing in check.

  **The real game is 88 plies**, `complete=True`, 0 impossible positions, 0
  impossible transitions. Ambiguous bridges 2 and 3 disappeared with the
  fabricated plies — they were never ambiguities.

  Known limitation, documented in the module: any return to a previous placement
  is treated as a rewind, so a genuine threefold repetition in a recording of
  *live* play would be discarded the same way. Safe for review recordings, wrong
  for live ones. Every rewind is reported rather than silently applied.

- [x] **Bridge 1 (t=16.73) resolved from the frames**, basis `local_visual`.
  The four candidates differed in the recapture order on e5. Frame evidence:
  the f6 pawn is mid-flight to e5 at t=16.20 (so `fxe5` came first, not
  `Rxe5`), the d5 rook slides to e5 across t=16.30-16.42 while the e1 rook never
  leaves home (so `Rdxe5`), then e5 empties and the e1 rook departs at t=16.64.
  The line is **`fxe5 Rdxe5 Rxe5 Rxe5`** — candidate index 2, *not* the
  first-listed candidate a default would have taken.

- [x] **Full game emitted as `moves.json`** — `tests/fixtures/full_game_moves.json`,
  88 plies, `validate_moves` clean, `sha256` pinning the source recording (it
  matches `opening_moves.json`, confirming the same file). Built with:

  ```bash
  uv run python src/workers/confirm_bridges.py logs/extracted_game_v2.json --visual 16.733=2 --content-id 2026-08-20-duolingo-003-full --out tests/fixtures/full_game_moves.json
  ```

- [x] **Contract validator bug found and fixed.** `moves_contract._start_board`
  ignored `start_position.castling_rights`, so `O-O` read as illegal and every
  game where either side castles would have been rejected. It never surfaced
  because the opening fixture has no castling. 2 tests added.

- [x] **Stockfish depth 20 over all 88 plies** —
  `output/content/2026-08-20-duolingo-003-full/analysis.json`.
  **The owner's worst moment is ply 56 `Kg6`, a blunder at -35.04% win; best was
  `Ke6`** — the exact move the app's coach was demonstrating at t=22.4s, which is
  independent corroboration that the rewind detector cut the right states.
  White blundered first with 55 `Rf5+` (-35.41%), then 71 `c4` (-47.24%) and
  77 `c5` (-38.57%). The owner's earlier errors: 6 `c6` (-11.20%), 8 `Bc5`
  (-10.61%), 24 `Nxe5` (-10.37%).
  Fixing this run also exposed a bug: `analyze_moves` built its own start board
  and dropped the document's castling rights, so every position before a castle
  went to Stockfish with castling unavailable to both sides. Validator and
  analyser now share one `start_board` helper.

- [x] **`tests/fixtures/prototype_moves.json` marked superseded** — carries a
  `superseded_by` note; its builder's docstring says so too. Kept, not deleted:
  the contract tests use its unresolved plies to prove the renderer gate blocks
  them, and prior probes are not deleted.

- [x] **Piece glyphs redrawn.** Every piece now shares one baseline and one
  foot, height carries the hierarchy, and the outline pass paints under the fill
  pass so overlapping parts union into a single contour. Two interior marks earn
  their place: the knight's eye and the bishop's mitre slit. The set went from
  under half a square wide to a proper footprint. Verified at true board scale in
  a real 1080x1920 scene frame, not just on a swatch sheet.

## Current — next three tasks, in order

- [x] **Moment selector** — `src/analysis/select_moment.py`, 13 tests. Picks the
  **owner's** largest win-% drop, never the biggest number on the board (the
  prototype game's largest is White's 71.`c4` at -47.24%, which a channel built
  on the owner's own mistakes cannot lead with). Raises `NoMoment` rather than
  promoting the least-good move when the owner played cleanly. Ties break to the
  earlier ply so the same analysis always yields the same short.

  `slice_moves` cuts the window into a document that still validates on its own
  terms — replayed start position, castling rights and en-passant square carried
  across the boundary, and ply numbers deliberately **not** renumbered, since
  they are the join key into `analysis.json` and drive the on-screen move number.

  On the prototype game it selects **plies 52-58 around ply 56 `Kg6`**:

  ```text
   52 b Kf7    best        -0.00%
   53 w g5     inaccuracy  -5.07%
   54 b h6     good        -3.30%
   55 w Rf5+   blunder    -35.41%
   56 b Kg6    blunder    -35.04%   <-- the moment
   57 w Rd5    good        -1.94%
   58 b hxg5   good        -1.42%
  ```

  White throws the game away and the owner hands it straight back. Rendered to
  `output/content/2026-08-20-duolingo-003-full/short.mp4` — 307 frames,
  1080x1920 @30fps, 10.2s. The eval bar settles at 53% after `Rf5+` and 87%
  after `Kg6`, matching the engine.

- [x] **Third validator gap closed.** `start_board` ignored the recorded
  en-passant square, the same class of bug as the castling one. It bites exactly
  here: a window that opens on the move after a double pawn push contains a
  capture the validator would reject as illegal. 2 tests.

- [ ] **Runtime is 10.2s, not ~35s.** `step_s` is a fixed 0.95s per ply. Length
  should follow narration (`docs/PLAN.md` 1.6), so this closes when voice lands,
  not by padding the constant.

- [x] **Custom board and piece art — landed.**

  **Board:** `src/renderer/board.html`, accepted as sent. 720x720, 64 explicit
  `<rect>`s on exact 90px boundaries, ids `a1`-`h8`, a1 dark and bottom-left.

  **Pieces:** owner's AI-generated Staunton set,
  `assets/renderer/pieces/chess_piece_sprite_sheet.png` (1536x1024 RGBA, real
  alpha). Licence cleared: Staunton is public domain from 1849 and nothing in it
  is recognisable as Duolingo's or Chess.com's artwork.

  Measured on arrival: baselines aligned within each row (+-1px) and the
  hierarchy correct in both rows — but **white and black did not match each
  other**, worst on the rook at +11.6% (303px white against 338px black). A
  black rook visibly taller than the white one is the kind of thing viewers
  notice without being able to name.

  `src/workers/build_piece_sprites.py` normalises it, 8 tests. Pieces are found
  by their own alpha rather than by assuming a grid, because the sheet is drawn
  by an illustrator and the columns are unevenly spaced. Twins are averaged
  rather than one side copied onto the other — neither half is more correct —
  and the artist's own hierarchy is preserved instead of being replaced with
  numbers from a spec, since this set already reads king > queen > bishop >
  knight > rook > pawn.

  One bug worth remembering: sprites were first written as `K.png` / `k.png`,
  and **macOS is case-insensitive by default**, so every black piece silently
  overwrote its white twin and the whole board came out black. Filenames are now
  `wK` / `bK`, and a test asserts the twelve names stay distinct when case is
  folded.

  **Wiring:** art is inlined as data URIs and injected through
  `add_init_script` alongside `window.__SCENE__`. Not referenced by path — the
  page loads over `file://`, where a relative image request is a separate load
  the screenshot can race. Missing art is not an error: the scene falls back to
  its own vector glyphs, which stay in the tree.

  **Layout Option A applied.** Board 820 -> 720 (90px squares) at y=330, eval bar
  and text moved to y=1088/1118, freeing **880x354 at y=1146-1500** for the
  mascot. Verified in a real render, not a mock.

  `tests/test_renderer.py` now identifies pieces through `data-piece` rather than
  by reading paint, since `<img>` backgrounds produce no `<g>`; every page setup
  in the tests goes through one `init_page` helper so the determinism test
  exercises the data-URI path too. All four renderer tests green, including
  byte-identical frames across runs.

- [x] **Mascot: art in, popups working.**
  `assets/renderer/mascot/pawn_neutral.png`, normalised from the owner's
  generated art into the 880x354 band with the feet on the bottom edge. Passes
  every check: pawn silhouette with stub arms and no legs, eyes and eyebrows and
  no mouth, exact palette match with the pieces (cream body, navy outline, amber
  accent), flat vector with no shadow or gradient, clean alpha, legible on the
  dark background and on a light square, and not recognisable as anyone's
  existing character.

  `src/renderer/mascot.py` schedules the popups, 8 tests. Cues anchor to a
  **ply**, never a timestamp — the moment selector can shift the window and the
  pacing constant changes again when narration drives it, and an absolute
  timestamp goes stale silently the first time either happens. The reaction
  waits for the move to land, because reacting mid-slide reads as reacting to
  nothing. Text is never written by the mascot: the reaction quotes the caption
  `analysis.json` already produced, so it cannot claim something the engine does
  not support.

  On this short: hook 0.00-3.50s, reaction 6.33-8.27s anchored to ply 56,
  outro 8.27-10.27s.

  **Occlusion is now satisfied by geometry rather than by a check.** design.md
  makes a mascot covering the discussed move's squares a hard scene failure;
  with the Option A band sitting entirely below the board, the overlap cannot
  occur. The validator is still worth writing if the layout ever changes.

- [ ] **Two mascot nits, deliberately left.**
  - The reaction and the outro are back-to-back (both at frame 248), so the pawn
    dips out and straight back in. Reads as a bounce; may want a gap.
  - The mascot is on screen for ~7.7s of a 10.2s short (75%). design.md warns
    against exactly that. It resolves itself at the ~35s target runtime, where
    the same three popups cover ~22% — so fix the runtime first, not the cues.

- [ ] **Remaining expressions.** Only the neutral pose exists. `design.md`
  specifies ten states; the reaction beat in particular wants a dismayed one
  rather than the resting face.

The hook writes itself now and it is true: the app told the owner there was a
better king move, and Stockfish independently names the same move.

## Deferred — Phase 0 leftovers

- [ ] Choose a commercially-licensed font; embed in `assets/renderer/fonts/`. Inter (SIL OFL 1.1) was the recommendation.
- [ ] Clear the Bridge 10 Gemini validation debt: repeat the control 3-5 times and once with shuffled frame order. Lower priority now — extraction no longer depends on the VLM at all.

## Open — repository and licensing

- [x] Repository stays **public**, licensed **GPL-3.0-or-later** (`LICENSE` added, verbatim GPL v3). Required, not chosen: `python-chess` is GPL-3.0+ and public distribution triggers it. Copyleft also means anyone redistributing a modified version must open-source their changes.
- [x] Absolute `/Users/<name>/...` paths replaced with placeholders across `BRIEF.md`, `MEMORY.md`, `TODO.md`, `PROJECT_MASTER_CONTEXT.md`.
- [x] Blocked mascot concept art untracked and gitignored; files kept on disk for reference.
- [ ] **Blocked concept art remains in public git history from `b75abc1`.** Untracking removes it from `HEAD` only. Fully removing it requires a history rewrite and a force-push, which `git-sync-main.sh` deliberately refuses — needs an explicit decision. Low urgency: it is unpublished concept art in a small repository, and nothing derivative reaches output.
- [ ] Add a short licence + attribution note to `README.md` once the first third-party asset (font, audio) is actually introduced.

## Open — documentation reconciliation

Known contradictions between committed files. Resolve before implementation starts, or a future session will build the wrong thing.

- [ ] `PROJECT_MASTER_CONTEXT.md` §2.2 uses `mascot_intro_peek` naming, §2.7 uses `intro_peek.png`. `design.md` now reconciles this (file on disk, logical id in `scene.json`) — mirror it back into the master context doc.
- [ ] `PROJECT_MASTER_CONTEXT.md` §2.4 budgets five mascot popups per short. Cut to three — each popup costs ~1.2s of slide-in/settle/exit, so five spend ~6s of a 36s video on the character moving and never let the board hold attention beyond 8s.
- [ ] Add to `PROJECT_MASTER_CONTEXT.md` §2.7: the Set 2 wall is load-bearing (hands grip it, so removing it leaves hands gripping nothing), and the source images have no alpha channel at all — the hoodie reads lighter than the background wall, so naive keying destroys the character before it clears the background.

## Next — Phase 1, recording to finished mp4

- [x] Hand-write `moves.json` for the prototype game and freeze the schema (`docs/PLAN.md` 1.1) — `tests/fixtures/prototype_moves.json`, built by `src/workers/build_prototype_moves_json.py`.
- [x] Build the schema validator — `src/validators/moves_contract.py`, all six hard-fail rules, 10 tests, TDD.
- [ ] Narrow the `unresolved` range: re-run `duolingo_path_ambiguity_probe.py` and record bridge → ply boundaries so plies 16-36 are not blanket-marked. Currently everything after ply 15 is conservatively unresolved because the mapping is not stored anywhere machine-readable.
- [ ] Make the extraction workers emit `moves.json`.
- [ ] Build the CLI human move-confirmation step; write `human_confirmed` status.
- [x] Stockfish analysis wired to `analysis.json`, separate from move truth — `src/analysis/analyze_moves.py`.
- [x] Win-percentage-delta classification with boundary tests — `src/analysis/move_quality.py`.
- [ ] Build the moment selector, targeting the owner's largest win-% drop.
- [ ] Build the script generator on the fixed four-beat structure, constrained to `analysis.json` facts.
- [ ] Add a positioning lint that rejects authority-voiced copy.
- [ ] Record the owner's voice for the first script; build the audio-driven timeline.
- [ ] Wire Kokoro-82M as the non-personal-content voice path.
- [x] Renderer first pass: board, original vector piece glyphs, eased tweening, capture fade, last-move highlight, hook, live eval bar, caption band, board flipped to the owner's side. Renders 1080x1920 @30fps, muxed by FFmpeg.
- [ ] Renderer second pass: move-quality badges and board effects, the freeze beat, then the pawn mascot popup.
- [x] **Found the real mistake.** The recording contains the *whole game from move 1* — only a 6-second slice had ever been reconstructed. Scanned 0-13.5s: the opening reconstructs cleanly to 5.25s with zero ambiguity as `1.e4 e5 2.Nf3 Nf6 3.Nc3 c6 4.Bc4 Bc5 5.Nxe5`. Stockfish depth 20: `c6` inaccuracy -8.03%, **`Bc5` mistake -10.42%** (`Qe7` better), then White simply wins the e5 pawn. Rendered as `2026-08-19-duolingo-002-opening`.
- [ ] Scan window 5.5s-13.5s reliably. Reconstruction degrades there: transient frames (a piece mid-flight reads as absent) plus at least one misclassification (a bishop read as a queen at t=6.25). Needs denser sampling and better transient rejection before that span can be trusted.
- [ ] Old blocker, now lower priority: Stockfish over plies 1-15 found no blunder and no mistake — one inaccuracy at ply 4 (`Be6`, -6.67%). White is already +243cp at ply 1 and +452 by ply 15, so the decisive error happened *before* 13.50s, outside the reconstructed window. Extend the truth layer backwards, or use a different game.
- [x] Renderer determinism proven and regression-tested. Required a warm-up pass: Chromium's first screenshot after load antialiases the SVG pieces differently from every later one.
- [x] Renderer proven not to alter the move sequence (`tests/test_renderer.py`).
- [ ] Mux to 1080x1920 H.264 with burned captions; verify legibility muted and no content in platform dead zones.

## Next — chess truth layer

- [ ] If Bridge 10 control passes, create a reusable `GeminiEvidenceReader` behind the provider interface.
- [ ] Define a strict structured visual-observation schema such as `side`, `from`, `to`, `capture_if_visible`, `uncertain`, and evidence timestamps.
- [ ] Apply candidate-constrained evidence comparison to Bridge 16.
- [ ] Apply candidate-constrained evidence comparison to Bridge 17.
- [ ] Apply candidate-constrained evidence comparison to Bridge 18.
- [ ] Apply candidate-constrained evidence comparison to Bridge 19.
- [ ] If Gemini fails the Bridge 10 control, remove it from move-disambiguation duties and keep it only for content-language tasks.
- [ ] Consolidate the final move sequence into a stable `moves.json` contract.
- [ ] Mark each move/bridge with verification status: `unique`, `visual_resolved`, `model_supported`, or `unresolved`.
- [ ] Add a validator that rejects impossible same-side consecutive moves and illegal move sequences before any downstream content stage.
- [ ] Add regression fixtures for the current Duolingo recording so future scanner changes cannot silently break this sequence.

## Next — chess analysis layer

- [ ] Install/configure Stockfish only after the move sequence contract is stable.
- [ ] Reconstruct a legal board with correct move order from the verified sequence.
- [ ] Produce engine analysis for mistakes, better moves, tactics, evaluation swings, and teaching moments.
- [ ] Store engine results separately from visual move truth.
- [ ] Define a simple content-event schema: `mistake`, `tactic`, `best_move`, `missed_move`, `turning_point`, `puzzle_candidate`.

## Next — deterministic video renderer

- [ ] Choose the board-rendering implementation.
- [ ] Render verified moves with deterministic pacing.
- [ ] Add configurable move highlights.
- [ ] Add arrows/circles only from verified/engine data.
- [ ] Add vertical 9:16 layout.
- [ ] Add hook area and subtitle-safe zones.
- [ ] Add loop-friendly ending option for short-form content.
- [ ] Ensure the renderer never changes the move sequence.
- [ ] Create visual regression examples for at least one verified game segment.

## Next — reusable agent skills

The existing `skills/chess-content/` and `skills/chess-video-editing/` directories are placeholders until their operating procedures are documented and tested.

- [ ] Write `skills/chess-content/SKILL.md`.
- [ ] Add approved hook examples and rejection examples.
- [ ] Define explanation rules for beginner audiences.
- [ ] Define CTA rules.
- [ ] Write `skills/chess-video-editing/SKILL.md`.
- [ ] Define board layout, pacing, highlight, subtitle, and loop rules.
- [ ] Create `skills/chess-video-reading/`.
- [ ] Add `SKILL.md`, `evidence-rules.md`, and `ambiguity-policy.md`.
- [ ] Add Bridge 10 as the first evaluation fixture for the video-reading skill.
- [ ] Create `skills/content-evaluator/` with explicit pass/fail rubric.
- [ ] Create `skills/platform-metadata/` only after the first publishing platform is selected.

A mature skill should use the reusable layout documented in `AI_Agent_Systems_Complete_Guide.md`:

```text
skill-name/
├── SKILL.md
├── examples/
├── templates/
├── scripts/
├── validation-rules.md
└── evaluation-rubric.md
```

## Next — orchestrator

- [ ] Define one content-item/run ID used across source, moves, render, copy, approval, publish, and analytics.
- [ ] Create a small Python orchestrator after the individual workers have stable contracts.
- [ ] Keep workers independently runnable from CLI for debugging.
- [ ] Add retry policy for provider/network failures.
- [ ] Do not retry deterministic validation failures; surface them.
- [ ] Add a workflow status model: `ingested`, `evidence_ready`, `moves_pending`, `moves_verified`, `rendered`, `evaluated`, `awaiting_approval`, `approved`, `published`, `failed`.

## Next — approval

- [ ] Build Telegram approval preview after the content generator produces a reliable draft.
- [ ] Approval buttons: approve, reject, revise.
- [ ] Show source ID, verified move summary, rendered preview, title/caption, and validation status.
- [ ] Do not expose API keys or internal secrets in approval messages.
- [ ] Add an emergency publish kill switch.

## Next — publishing

- [ ] Select first automated platform based on official API feasibility.
- [ ] Reuse relevant publishing/provider patterns from `sahansbandara/youtube-automation-agent` where appropriate.
- [ ] Keep publishing behind human approval during MVP.
- [ ] Store platform post ID / URL / timestamp / status.
- [ ] Add safe retry logic that prevents duplicate posts.
- [ ] Add manual-publish fallback.

## Next — analytics and Idea Engine

- [ ] Define metrics actually available from the first selected platform.
- [ ] Save analytics snapshots by content item.
- [ ] Compare topics, hooks, length, pacing, and CTA performance.
- [ ] Build an Idea Engine that proposes future content from verified performance data instead of generic trends alone.
- [ ] Add approved high-performing examples to skill benchmark libraries.

## MCP / integration roadmap

MCP is **not** a prerequisite for the MVP. Direct APIs/local libraries remain preferred while the workflow is still changing.

Potential MCP additions after the direct workflow is stable:

- [ ] GitHub MCP for repo/issue/PR operations if it reduces repeated coding-agent integration work.
- [ ] Custom content-library MCP for searching approved source/evidence/content records if a database/dashboard is added.
- [ ] Telegram MCP only if it provides a cleaner reusable agent interface than direct Bot API calls.
- [ ] Publishing MCP only where official APIs are insufficient or where a standardized multi-platform tool provides measurable value.
- [ ] Deployment MCP/Vercel integration only if/when a web dashboard is introduced.

Do not create an MCP server simply to make the architecture look more agentic.

## External repository reference tasks

### DeepSeek Harness

URL: https://github.com/deepseek-ai/deepseek-harness

- [ ] Revisit only when the local orchestrator/provider contracts are stable.
- [ ] Compare its plugin/service seam with the project's provider interfaces before adopting anything.
- [ ] Do not migrate the MVP solely for framework consistency.

### YouTube Automation Agent

URL: https://github.com/sahansbandara/youtube-automation-agent

- [ ] Reuse/port provider fallback patterns where useful.
- [ ] Reuse YouTube OAuth/publishing concepts after content approval is ready.
- [ ] Reuse analytics/scheduling ideas after first manual publish validation.

### Free LLM API Resources

URL: https://github.com/jtig37/free-llm-api-resources

- [ ] Use only for provider discovery.
- [ ] Verify any selected provider against its current official docs before implementation.

### VISIONE

URL: https://github.com/aimh-lab/visione

- [x] Extracted useful idea: preprocess long video into temporal evidence / shots.
- [x] Adapted into the Chess Micro-Shot concept.
- [ ] Do not install the full stack unless a future requirement cannot be solved by the local evidence builder.

### blind_navigation

URL: https://github.com/wink-wink-wink555/blind_navigation

- [x] Extracted useful idea: deterministic perception → event → LLM.
- [x] Extracted useful idea: provider abstraction.
- [ ] Do not use its domain-specific YOLO model for chess.

### MoneyPrinterTurbo

URL: https://github.com/harry0703/MoneyPrinterTurbo

- [x] Local WebUI tested.
- [x] Determined unsuitable as exact chess gameplay editor for the current source.
- [ ] Reintroduce later only for creative/generated content tasks where exact move timing is not the source of truth.

## Testing roadmap

- [ ] Create unit tests for board-coordinate mapping in Black orientation.
- [ ] Test piece-placement FEN construction.
- [ ] Test legal bridge enumeration.
- [ ] Test ambiguity detection.
- [ ] Test provider fallback without exposing secrets.
- [ ] Test malformed/empty model response handling.
- [ ] Test Gemini candidate-control rejection path.
- [ ] Test `moves.json` schema.
- [ ] Test renderer against known move sequence.
- [ ] Test publisher idempotency before enabling automated posts.

## Documentation roadmap

- [x] Replace generic `BRIEF.md` with Chess Content OS project brief.
- [x] Replace generic `DECISIONS.md` with current architecture decisions.
- [x] Replace generic `MEMORY.md` with current durable project state.
- [x] Replace generic `TODO.md` with the real roadmap.
- [ ] Update `README.md` after the truth-layer contract is stable.
- [ ] Add `docs/architecture.md` only if the README becomes too large.
- [ ] Add a machine-readable configuration reference for provider/model/publishing settings.
- [ ] Document environment-variable names without secret values.

## Blocked

### Exact move verification for Bridges 16–19

Current local visual scorers do not uniquely distinguish all remaining candidate paths.

Blocker-clearing experiment:

```text
Bridge 10 known control
→ candidate-constrained multi-image Gemini
→ pass or fail
```

If it passes, apply the same method to Bridges 16–19. If it fails, abandon Gemini as a move discriminator and strengthen local temporal piece tracking instead.

## Done

### Pawn mascot and public licensing (2026-08-19)

- [x] Designed the replacement mascot: an original **pawn** with eyes, eyebrows, stub arms and whole-body squash/stretch, drawn as renderer vector shapes rather than shipped assets. Chosen because it is the learner's piece, it is the only piece whose own rules contain an improvement arc, it has the simplest silhouette in chess so it stays legible at any size, and it carries no human-character IP surface.
- [x] Built and verified a working visual prototype of all ten expression states, the in-frame popup, and the promotion sequence.
- [x] Documented mascot promotion (pawn → knight → bishop → rook → queen) as a channel milestone mechanic tied to the rating spine.
- [x] Switched board pieces to original vector glyphs, removing the piece-art licensing problem instead of solving it.
- [x] Rewrote the `design.md` mascot section and updated Phase 0 in `docs/PLAN.md` accordingly.
- [x] Kept the repository public and added `LICENSE` (verbatim GPL v3, 674 lines); project is GPL-3.0-or-later, which `python-chess` requires.
- [x] Removed all 7 absolute personal paths from tracked files.
- [x] Untracked and gitignored the blocked mascot concept art.

### Publishing architecture and IP correction (2026-08-19)

- [x] Pulled and reviewed the 8 files added on `main`: `docs/MULTI_PLATFORM_PUBLISHING.md` plus the `platform-metadata`, `content-release`, `social-publishing`, `youtube-publishing`, `meta-publishing`, `tiktok-publishing` and `analytics-feedback` skills (1,428 lines).
- [x] Adopted the one-release / four-adapter publishing architecture; registered all seven skills in the `CLAUDE.md` skill router.
- [x] Identified the supplied reference character as Sherman (DreamWorks, *Mr. Peabody & Sherman*) and blocked all ten `assets/Character/` concepts as derivative works. Reversed the Set 2 selection.
- [x] Rewrote `design.md` around the popup model: character identity marked blocked, persistent-Presenter layout and mouth-shape strip removed, popup lifecycle, three-popup budget, sprite contract, matting note, and enforced occlusion documented.
- [x] Updated `CLAUDE.md` and `AGENTS.md` for public-repository reality and the GPL-3.0 obligation; corrected the superseded verification-status list in both to the three-file contract.
- [x] Sharpened non-negotiable 7 in both files: generating from a copyrighted character yields a derivative work, and the test is recognisability rather than novel pixels.

### Mascot and contract decisions (2026-08-19)

- [x] Reviewed `docs/PROJECT_MASTER_CONTEXT.md` (1,442 lines) and all 20 generated character images.
- [x] Adopted the §8 truth model into `docs/PLAN.md`, superseding the weaker single-enum schema: `verification_status` / `verification_basis` / `model_support` split, `model_support` excluded from valid basis values, UCI canonical with SAN asserted, provenance on inferred metadata.
- [x] Split the contract three ways — `moves.json` (truth), `analysis.json` (engine), `scene.json` (presentation) — so presentation data never enters the truth file.
- [x] Made mascot cues ply-anchored with a resolved-at-render offset instead of hand-authored absolute timestamps.
- [x] Promoted mascot occlusion of the discussed move's squares from guideline to hard validator failure.
- [x] Established that the two character sets are different characters, not variants; selected Set 2 on expression legibility (~260px face vs ~75px at mascot scale) and rejected Set 1.
- [x] Verified the source images carry no alpha channel, and measured that naive background keying destroys the character before clearing the background — the hoodie reads lighter than the wall and the background is a gradient, not a flat colour.
- [x] Gitignored the rejected Set 1 art rather than committing 16MB of unused images into permanent history; files remain on disk per the do-not-delete-experiments rule.

### Project system setup (2026-08-19)

- [x] Confirmed the Bridge 10 candidate-constrained Gemini control passed; recorded caveats and outstanding shuffle/repeat validation.
- [x] Sharpened positioning into an explicit learner-not-guru content rule governing all generated copy.
- [x] Reversed the all-TTS decision: owner's recorded voice for first-person content, Kokoro only where no personal claim is made.
- [x] Reversed the Pillow-compositor decision: deterministic HTML/CSS renderer driven by explicit frame numbers.
- [x] Selected the Presenter layout; documented platform dead zones as hard constraints.
- [x] Established IP boundaries: original mascot only, no third-party characters/branding/UI, no GPL piece art in monetised output.
- [x] Defined `moves.json` as the contract seam with per-move verification status.
- [x] Copied the relevant subset of the project template (98 files); excluded stale worktrees, duplicate skill trees, unused language rules, deploy tooling, and the stale LLM provider matrix.
- [x] Adopted and adapted the template session-wrap automation: `Stop` hook, `git-sync-main.sh`, wrap-session checklist, project permissions. Deploy step deliberately dropped.
- [x] Authored project-specific `CLAUDE.md`, `AGENTS.md`, `README.md`, `design.md`.
- [x] Wrote the phased build plan to `docs/PLAN.md`.
- [x] Initialised the private GitHub repository and pushed `main`.


### Project setup

- [x] Created Chess Content OS directory structure.
- [x] Initialized uv project with Python 3.11.
- [x] Added `python-chess`.
- [x] Added OpenCV headless.
- [x] Added Gemini SDK and dotenv.
- [x] Installed/verified FFmpeg and ImageMagick in local environment.

### Source preprocessing

- [x] Identified prototype Duolingo ReplayKit recording.
- [x] Built full-length deterministic gameplay video worker.
- [x] Calibrated board geometry.
- [x] Created board-only rapid clip for 13.50s–19.50s.
- [x] Created dense evidence frames.
- [x] Created slowed Gemini analysis clip.

### Board recognition

- [x] Created initial templates.
- [x] Created V2 RGB + mask templates.
- [x] Built full 64-square board scanner.
- [x] Reconstructed calibration piece-placement FEN correctly by visual inspection.

### Move reconstruction

- [x] Built state sequence probe.
- [x] Built direct single-ply chain probe.
- [x] Built multi-ply legal bridge probe.
- [x] Recovered a 36-move legal candidate sequence reaching all observed states.
- [x] Built path ambiguity audit.
- [x] Identified 5 ambiguous bridges.
- [x] Built local visual/departure/frame-scoring experiments.
- [x] Resolved Bridge 10 locally to the d5-rook first path.

### Gemini/provider work

- [x] Configured two Gemini credential slots in `.env` without storing secrets in docs.
- [x] Verified one Gemini key label is currently working.
- [x] Built `GeminiFallbackClient` provider seam.
- [x] Tested full-video Gemini move extraction.
- [x] Rejected full-video VLM extraction as the move authority due to inconsistent output.

### Research / architecture

- [x] Reviewed `deepseek-ai/deepseek-harness` for plugin/provider architecture.
- [x] Reviewed `sahansbandara/youtube-automation-agent` for provider fallback/publishing/analytics patterns.
- [x] Reviewed `jtig37/free-llm-api-resources` as provider-discovery material.
- [x] Reviewed `aimh-lab/visione` for temporal video-evidence concepts.
- [x] Reviewed `wink-wink-wink555/blind_navigation` for deterministic CV → LLM architecture.
- [x] Incorporated MCP / skills / evaluator / approval principles from `AI_Agent_Systems_Complete_Guide.md` into the project plan.

## Last session summary — 2026-08-20

Extraction was not solved. The prototype recording is Duolingo's "Review your
game" screen for its whole 41.4s, and the review steps backwards to demonstrate
better moves; the reconstructor assumed states only advance and bridged each
rewind with invented plies. Eight of the 96 plies never happened, one of them a
position with a black king standing in check, and two of the three "ambiguous
bridges" were asking which rook moved in a line nobody played.

`src/validators/review_rewind.py` separates the replayed game from the
demonstrations. The real game is 88 plies, contract-clean, emitted as
`tests/fixtures/full_game_moves.json`. The third bridge was genuine and was
settled by reading the frames: `fxe5 Rdxe5 Rxe5 Rxe5`, which is *not* the
first-listed candidate a default would have taken.

Stockfish depth 20 over all 88 plies puts the owner's worst moment at ply 56
`Kg6`, a blunder at -35.04%, best move `Ke6` — the exact move the app's coach was
demonstrating at t=22.4s. Two independent sources, same answer, and the rewind
detector found it from board-state repeats alone.

Also: the human confirmation CLI (refuses rather than guesses), the moment
selector (owner's plies only, never the biggest number on the board), the piece
glyphs redrawn, and three bugs of one class — the validator ignored castling
rights, the analyser fed Stockfish positions with castling stripped, and
`start_board` ignored the recorded en-passant square. 87 tests plus 4 renderer
tests, all green.

## Previous session summary

2026-08-19 — Replaced the blocked human mascot with an original **pawn**, drawn as renderer vector shapes: no illustrator, no image generation, no matting, no licence question, and no possibility of being a derivative of someone else's character. All ten expression states, the in-frame popup and the promotion sequence were prototyped and verified. Board pieces switched to original vector glyphs for the same reason, which also removes the piece-art licence hunt from Phase 0.

Repository stays public at the owner's decision, now licensed GPL-3.0-or-later — required rather than chosen, since `python-chess` is GPL-3.0+ and publishing distributes the combined work. Copyleft is the best available outcome for staying public: anyone redistributing a modified version must open-source their changes.

Cleaned the public surface: 7 absolute personal paths replaced with placeholders, blocked concept art untracked and gitignored. One item left open — that art is still in public history from `b75abc1`, and removing it would need a force-push the tooling refuses by design.

Next: Phase 0 proper. Install Stockfish, pick a commercially-licensed font, then draw the pawn's first two states and prove the popup in a real 1080x1920 render.

## Update rule

Update this file at:

- task start when the current objective changes;
- meaningful milestone;
- architecture decision that changes the roadmap;
- session end.

Do not update for every tiny command or temporary debug print.
