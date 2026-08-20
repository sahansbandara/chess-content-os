# Chess Content OS — Architecture Decisions

> Last updated: 2026-08-20
> This file now records Chess Content OS decisions. Generic template decisions are not treated as project facts unless explicitly re-validated in this repository.

## Decision format

### YYYY-MM-DD — Decision title

**Decision:**  
What was decided.

**Reason:**  
Why this decision was made.

**Alternatives considered:**  
Other options.

**Risk:**  
Downside or tradeoff.

**Status:**  
Proposed / accepted / changed / rejected / experimental

---

### 2026-08-20 — Mascot moves to a right-edge peek; the blocked character stays blocked

**Decision:**
Adopt the owner's mockup layout — hook top-left, character peeking from the
right with a speech bubble, board framed with coordinates, move chips and an
evaluation row beneath — and render it with the **pawn**. The human character in
`assets/Character/2/` remains blocked.

**Reason:**
The layout is better than the bottom band it replaces: the bubble reads as
speech rather than as a second caption, and the chips put the engine's verdict
on screen as a fact rather than a sentence. Adopting it costs nothing.

The character does not come with it. `assets/Character/` was blocked on
2026-08-19 as derivative of Sherman (DreamWorks, *Mr. Peabody & Sherman*), and
the mockup's pose — peek around a right-hand edge — is itself named in that
decision as part of the identifying combination, being the composition of the
reference promo still. A pawn peeking around an edge is not that character: what
made the earlier set recognisable was ginger hair plus round glasses plus child
proportions plus the pose, not the pose alone.

**Alternatives considered:**
Keeping the bottom band (loses the speech read); using the blocked art (a
derivative work in monetised output, which Non-negotiable 7 forbids regardless
of who generated the pixels).

**Risk:**
The mascot now sits above the board rather than below it, so the geometric
occlusion guarantee holds for a different reason — 170..580 against a board
starting at 620. It is still a property of the layout rather than of the
renderer, so a future layout change can silently remove it.

**Status:**
accepted

---

### 2026-08-20 — A recorded review screen is not a recorded game

**Decision:**
Treat any return to an already-observed board placement as a review rewind, cut
the states observed while the review sits behind the newest position it has
shown, and never bridge across the gap. Implemented in
`src/validators/review_rewind.py` and wired into `extract_game.clean()`.

**Reason:**
The prototype source is Duolingo's *"Review your game"* screen for its entire
41s, not live play. The review steps backwards to demonstrate a better move and
then forwards again to the move actually played. The reconstructor assumed board
states only ever advance, so it bridged each rewind with invented plies — eight
of them, including a position with a black king standing in check, and two
"ambiguous bridges" that were asking which rook moved in a line nobody played.

Independent corroboration arrived from two directions afterwards. The coach's
speech bubble at t=22.4s reads "Next time, there's a better move for that king",
and Stockfish at depth 20 names the owner's worst moment as exactly that ply —
`Kg6`, a 35.04% blunder, best move `Ke6`, which is the move the review was
demonstrating.

**Alternatives considered:**
Reading the review UI header (eval label, coach text, progress bar) to mark
demonstrations explicitly — more robust, since it also catches a demonstration
that wanders off and never returns, but it needs a new OCR/template surface.
Re-recording live gameplay instead — the cleanest source fix, and still the right
answer for future recordings.

**Risk:**
A genuine threefold repetition in a recording of *live* play would be discarded
the same way. Safe for review recordings, wrong for live ones. Every rewind is
reported rather than silently applied, and the limitation is documented in the
module.

**Status:**
accepted

---

### 2026-08-20 — Frame observation is a basis; a printed candidate never is

**Decision:**
`confirm_bridges` settles a bridge only on an explicit answer, and records how:
`human_confirmed` when the owner answers, `local_visual` when the frames were
read. An unanswered bridge, an out-of-range index, and a line that does not
replay to the observed final board all refuse to write a file.

**Reason:**
Bridge 1's four candidates differed in the recapture order on e5. Reading the
frames settled it — the f6 pawn is mid-flight to e5 at t=16.20, the d5 rook
follows across t=16.30-16.42 while the e1 rook never leaves home. The answer is
`fxe5 Rdxe5 Rxe5 Rxe5`, candidate index 2. The first-listed candidate, which a
default would have taken, was **wrong**.

**Risk:**
`local_visual` is weaker than the owner's own answer and is recorded as such, so
a later pass can upgrade it rather than having to rediscover that it was a guess.

**Status:**
accepted

---

## Project decisions

### 2026-08-20 — Use an original teenage learner mascot in published shorts

**Decision:**
Use the original dark-curly-haired teenage chess learner in the active social
format. Expressions follow engine labels: regretful for an inaccuracy, mistake,
or blunder; confident for a good or best move. Keep the blocked red-haired,
round-glasses character concepts out of published output.

**Reason:**
A human learner gives the channel a stronger on-screen host while preserving
the learner-not-guru positioning. Changing hair, eyewear, facial proportions,
clothing, pose, palette, and illustration style avoids the identifying
combination documented in the earlier IP block.

**Risk:**
Generated expression variants can drift in identity. New states must use the
accepted mascot as their reference and receive a visual consistency check.

**Status:**
accepted

---

### 2026-08-18 — Use chess as the first automated social-content vertical

**Decision:**  
Build the first Chess Content OS workflow around real chess gameplay and learning content, starting with Duolingo Chess recordings.

**Reason:**  
The source activity already exists naturally, which reduces the burden of inventing a new content-production routine. It also creates a clear truth domain where moves can be validated deterministically.

**Alternatives considered:**  
Generic AI-generated social videos, travel content, affiliate content, and other unrelated automation verticals.

**Risk:**  
Chess content may not produce a large audience. The MVP therefore focuses on proving a repeatable low-workflow content engine before investing in monetization infrastructure.

**Status:**  
Accepted

### 2026-08-18 — Position the content as learning in public, not expert instruction

**Decision:**  
Use the positioning: "learning chess in public — solve, learn, improve with me."

**Reason:**  
It is compatible with gameplay mistakes, puzzles, tactics, and visible improvement without requiring the creator to claim expert status.

**Alternatives considered:**  
Expert coaching positioning and purely entertainment/meme chess content.

**Risk:**  
The content must still be accurate. All chess claims must be based on verified moves and later Stockfish analysis where appropriate.

**Status:**  
Accepted

### 2026-08-18 — Keep MoneyPrinterTurbo as a specialist creative worker only

**Decision:**  
Use MoneyPrinterTurbo only for AI-generated creative video tasks where exact chess-game timing is not the truth source. Do not use it as the gameplay editor or move-reconstruction engine.

**Reason:**  
The first local test shortened/chopped the gameplay and demonstrated that generic clip-selection logic does not preserve exact chess replay timing.

**Alternatives considered:**  
Make MoneyPrinterTurbo the primary video-editing pipeline.

**Risk:**  
This creates two video paths: deterministic chess rendering and optional AI creative generation. The separation is intentional because they have different correctness requirements.

**Status:**  
Accepted

### 2026-08-18 — Separate chess truth from AI generation

**Decision:**  
Chess state and move legality are determined by local evidence plus `python-chess`. AI may assist with ambiguous visual evidence and content language but cannot independently certify the move sequence.

**Reason:**  
Chess provides deterministic legality constraints. Using them makes the system more reliable than trusting an LLM/VLM to reconstruct a game from pixels.

**Alternatives considered:**  
Ask a video-capable model to read the entire recording and return moves directly.

**Risk:**  
Local perception errors can still create wrong candidate states. The system therefore keeps ambiguity explicit and validates across temporal evidence.

**Status:**  
Accepted

### 2026-08-18 — Use piece-placement FEN when full FEN metadata is unavailable

**Decision:**  
The visual board scanner outputs `board.board_fen()` / piece-placement FEN rather than pretending a screenshot provides full FEN metadata.

**Reason:**  
A screenshot does not reliably reveal side-to-move, castling rights, en-passant state, or move counters.

**Alternatives considered:**  
Invent or infer a complete FEN for every frame.

**Risk:**  
Legal reconstruction requires additional assumptions/context for turn order. Those assumptions must stay separate from the visual board observation.

**Status:**  
Accepted

### 2026-08-18 — Use V2 color templates and full 64-square scanning

**Decision:**  
Use RGB + mask piece templates in `assets/templates/duolingo_v2/` and scan all 64 board squares.

**Reason:**  
The V2 calibration provided clear white/black visual separation and reconstructed the calibration board correctly during visual inspection.

**Alternatives considered:**  
The earlier mask-only profile and immediate training of a new object detector.

**Risk:**  
Template matching may not generalize to different themes, devices, animations, or future Duolingo visual changes.

**Status:**  
Accepted for MVP

### 2026-08-18 — Legal path coverage is not treated as proof of exact visual path

**Decision:**  
A shortest legal bridge that reaches the target board state is a candidate, not automatically the observed truth when multiple legal paths exist.

**Reason:**  
Multiple legal move sequences can lead to the same piece-placement board state.

**Alternatives considered:**  
Take the first BFS path returned.

**Risk:**  
Ambiguity handling increases implementation complexity, but silent false certainty is unacceptable for the content truth layer.

**Status:**  
Accepted

### 2026-08-18 — Use Bridge 10 as a visual-method control

**Decision:**  
Treat the State 12 → State 14 transition as a control case for new visual disambiguation methods.

Known candidates:

```text
A: Rdxe5 → Rxe5 → Rxe5
B: Rexe5 → Rxe5 → Rxe5
```

Local temporal evidence selected candidate A, where the rook on d5 departs first.

**Reason:**  
A method that cannot reproduce a known visual distinction should not be trusted on the unresolved bridges.

**Alternatives considered:**  
Test new methods only on unresolved bridges where no reference outcome exists.

**Risk:**  
One control does not prove general accuracy; more controls will be required later.

**Status:**  
Accepted

### 2026-08-18 — Borrow VISIONE's temporal-evidence concept without installing VISIONE

**Decision:**  
Adopt scene/shot/keyframe ideas as a Chess Micro-Shot evidence pipeline implemented locally with FFmpeg/OpenCV. Do not install the full VISIONE stack for the MVP.

**Reason:**  
The useful idea is preprocessing video into manageable temporal evidence. The full repository is oriented toward a larger retrieval stack and GPU-based analysis that is unnecessary for the current MacBook-first prototype.

**Alternatives considered:**  
Install and adapt the full VISIONE system.

**Risk:**  
A simplified local implementation may miss useful advanced retrieval components, but those are not required to solve the current move-reconstruction problem.

**Status:**  
Accepted

### 2026-08-18 — Follow the deterministic perception → LLM pattern from blind_navigation

**Decision:**  
Use local frame perception/event detection before invoking an LLM/VLM, and keep a provider abstraction around AI services.

**Reason:**  
The reviewed `blind_navigation` repository demonstrates the architecture of deterministic CV producing an event before calling a text model. That separation maps well to chess evidence handling.

**Alternatives considered:**  
Send every raw recording directly to a model.

**Risk:**  
The local perception layer still requires careful calibration and testing.

**Status:**  
Accepted as architecture principle

### 2026-08-18 — Use DeepSeek Harness as an architecture reference, not a migration target

**Decision:**  
Borrow the plugin/provider-seam idea from `deepseek-ai/deepseek-harness` but keep the current Python pipeline independent.

**Reason:**  
A swappable `VideoUnderstandingProvider` is valuable, while migrating a working prototype into a new harness would add complexity before the core workflow is validated.

**Alternatives considered:**  
Rebuild the Chess Content OS directly inside DeepSeek Harness.

**Risk:**  
Some future agent features may need to be reimplemented. This is preferable to premature framework lock-in.

**Status:**  
Accepted

### 2026-08-18 — Reuse provider/publishing concepts from youtube-automation-agent later

**Decision:**  
Use `sahansbandara/youtube-automation-agent` as a reference for provider fallback, scheduling, YouTube publishing, and analytics, but not as the chess-vision engine.

**Reason:**  
Its architecture solves later pipeline stages that Chess Content OS will need after content generation is reliable.

**Alternatives considered:**  
Merge the two projects now.

**Risk:**  
Duplicated concepts may temporarily exist across repositories.

**Status:**  
Accepted for later integration

### 2026-08-18 — Treat free-llm-api-resources as discovery only

**Decision:**  
Use `jtig37/free-llm-api-resources` only to discover providers; verify models, quotas, pricing, and API details from current provider documentation before implementation.

**Reason:**  
Fast-moving API lists become stale quickly.

**Alternatives considered:**  
Treat the repository as the source of truth for free-tier limits.

**Risk:**  
Provider research requires an extra verification step.

**Status:**  
Accepted

### 2026-08-19 — Use two Gemini key slots behind a provider client

**Decision:**  
Configure separate environment variables for primary and backup Gemini credentials and access them through a fallback client. Never commit key values.

**Reason:**  
Credential redundancy and a provider seam make failures easier to isolate and later support multiple providers.

**Alternatives considered:**  
One hardcoded key or one comma-separated environment variable.

**Risk:**  
Two keys from the same provider/project may still share project-level service limits. Key fallback is not equivalent to independent-provider redundancy.

**Status:**  
Accepted

### 2026-08-19 — Prefer the currently proven working Gemini key first

**Decision:**  
The key labeled `BACKUP` is attempted first because it passed the live `OK` test. The key labeled `PRIMARY` remains the second attempt after its live test produced a server-side failure.

**Reason:**  
Runtime should prefer the credential already proven in the current environment.

**Alternatives considered:**  
Keep the original primary-first order regardless of observed status.

**Risk:**  
The earlier primary failure may have been transient. The ordering can be revisited after health-check data is collected.

**Status:**  
Accepted for current development

### 2026-08-19 — Reject open-ended whole-video Gemini move extraction as chess authority

**Decision:**  
Do not use the result of the full-video Gemini chess probe as the verified move sequence.

**Reason:**  
The model returned 25 moves marked high confidence, but many conflicted with the legal reconstruction and the output included consecutive same-side moves, which cannot represent a legal alternating chess game.

**Alternatives considered:**  
Accept the VLM output, prompt it again more strongly, or replace the local move reconstruction with the VLM.

**Risk:**  
Rejecting open-ended VLM extraction means the local chess pipeline remains necessary. This is the correct tradeoff for accuracy.

**Status:**  
Rejected as authority

### 2026-08-19 — Narrow Gemini to candidate-constrained visual evidence

**Decision:**  
The next Gemini test will provide a small chronological image/evidence pack for a known ambiguous transition and ask the model to distinguish constrained alternatives, beginning with Bridge 10.

**Reason:**  
The model performs poorly when asked to reconstruct the entire rapid game, but it may still add value as a local visual discriminator when the legal candidate set is already known.

**Alternatives considered:**  
Stop using Gemini entirely or continue whole-video prompt tuning.

**Risk:**  
The model may still fail the control. If it cannot select the known d5-rook path on Bridge 10, Gemini should be removed from chess move disambiguation and retained only for language/content tasks.

**Status:**  
Experimental / next test

### 2026-08-19 — MCP and skills are supporting infrastructure, not MVP prerequisites

**Decision:**  
Build reusable project skills and direct API integrations first. Add MCP only where a standardized reusable tool interface materially improves an existing workflow.

**Reason:**  
The agent-system guide emphasizes that tools, skills, evaluation, permissions, and approval create the useful system. MCP itself does not solve chess perception or content quality.

**Alternatives considered:**  
Start by building a custom MCP server or adopting a large agent framework before the content pipeline works.

**Risk:**  
Some integrations may later require refactoring into MCP tools. This is cheaper than premature infrastructure.

**Status:**  
Accepted

---

### 2026-08-19 — Bridge 10 candidate-constrained Gemini control passed

**Decision:**
The candidate-constrained multi-image Gemini control on Bridge 10 passed. Gemini selected candidate A, `d5 → e5` first, matching the local departure-timing result. Gemini therefore remains eligible for move disambiguation, constrained to candidate comparison on small evidence packs.

**Reason:**
Falsification rule #1 required this control before trusting the method on Bridges 16–19. Logged in `logs/gemini_bridge10_image_probe.json`: model `gemini-3.6-flash`, key label `BACKUP`, 7 frames from 16.250s–16.750s, confidence `medium`, reasoning consistent with the known d5-first departure.

**Alternatives considered:**
Removing Gemini from disambiguation entirely; continuing whole-video prompt tuning.

**Risk:**
One passing trial on a control whose answer was already known, with hand-picked frames and only `medium` self-reported confidence. Before applying this to Bridges 16–19 it must be repeated 3–5 times and tested with shuffled/reversed frame order — a model that answers A regardless of frame order has proved nothing.

**Status:**
Accepted, pending repeat-and-shuffle validation

### 2026-08-19 — Human confirmation is the ambiguity backstop

**Decision:**
Ambiguous bridges that local evidence and constrained VLM comparison cannot resolve are settled by the owner confirming the move list, not by further research. The reconstructed sequence is presented with uncertain bridges marked; the owner confirms or corrects.

**Reason:**
The owner played the game and knows what happened. Bridges 16–19 had become an open-ended research blocker holding up the entire content pipeline. A human answer costs ~30 seconds and is more reliable than any current automated method.

**Alternatives considered:**
Strengthening local temporal piece tracking; training a motion model; leaving the bridges permanently unresolved.

**Risk:**
Human memory of a fast replay section is imperfect. Mitigation: the confirmation UI shows the candidate paths and the evidence frames, and every move retains its verification status — `human_confirmed` is distinct from `unique`.

**Status:**
Accepted

### 2026-08-19 — `moves.json` is the contract seam

**Decision:**
A single `moves.json` file is the boundary between move extraction and everything downstream. It carries PGN, SAN, UCI, source video timestamps, and a per-move verification status: `unique`, `visual_resolved`, `model_supported`, `human_confirmed`, or `unresolved`. No stage after it touches pixels.

**Reason:**
24 workers currently communicate through ad-hoc JSON in `logs/`. Without a frozen contract every new stage becomes another one-off script. It also makes the input source swappable — a Duolingo recording and a PGN file converge here.

**Alternatives considered:**
Continuing with per-worker ad-hoc formats; passing a PGN string alone (loses timestamps and verification status).

**Risk:**
Schema churn early on. Mitigation: freeze it from a real hand-written example before writing consumers.

**Status:**
Accepted

### 2026-08-19 — Position as a learner sharing mistakes, not a teacher

**Decision:**
Sharpen the earlier "learning in public" positioning into an explicit content rule: every piece leads with the owner's own mistake and what it cost, framed as avoidance rather than instruction. Copy must never claim expertise the owner does not have.

```text
Everyone else:  "The best move here is Nf6, and this gambit refutes it."
This channel:   "2 mistakes and I got mated in 11. Don't do what I did."
```

**Reason:**
The chess niche is saturated with authority-voiced instruction from strong players. A visibly improving beginner documenting real mistakes is under-served, and beginners relate to a beginner's blunders more than to a titled player's analysis. It is also the one thing stronger channels cannot copy.

**Alternatives considered:**
Standard "best move / best gambit" instructional framing; pure entertainment framing.

**Risk:**
The positioning has a shelf life — it requires the owner to actually improve, or the arc goes stale. Low-rated content also attracts condescending comments. Both accepted; playing regularly becomes part of production, not a hobby beside it.

**Status:**
Accepted

### 2026-08-19 — Owner's recorded voice for first-person content; TTS only where no personal claim is made

**Decision:**
Reverses the earlier decision to use Kokoro TTS for all narration. Content asserting personal experience uses the owner's real recorded voice, batch-recorded weekly. Kokoro-82M remains for content that makes no first-person claim, such as pure puzzle shorts.

**Reason:**
A synthetic voice saying "I made this mistake" is hollow and audibly so. The entire value of the positioning is that a real person is being honest about being bad at something; outsourcing that to a robot voice removes the only defensible differentiator.

**Alternatives considered:**
Kokoro for everything (cheaper, ~0 recurring time); ElevenLabs (paid, still not a real person).

**Risk:**
~30 minutes per week of recording time against a demanding degree. Accepted as the cost of the differentiator. Rough phone audio in a quiet room is acceptable and arguably on-brand.

**Status:**
Accepted, supersedes the TTS-for-everything choice made earlier the same day

### 2026-08-19 — Clip selection targets the owner's mistakes, not the best chess

**Decision:**
The moment selector picks the owner's own largest evaluation swings, not the objectively most interesting position. Story shape is fixed: the mistake → what it cost → what should have been played → the pattern to avoid.

**Reason:**
Follows directly from the positioning. It also has a useful side effect: the interesting moments cluster in the middle game, while the currently unresolved ambiguous bridges sit in a drawn endgame shuffle that would be cut from a 35-second short anyway.

**Alternatives considered:**
Largest swing by either side; engine-rated brilliancies.

**Risk:**
A game with no clear mistake yields no content. Mitigation: fall back to the puzzle-from-my-own-blunder format, or skip the game.

**Status:**
Accepted

### 2026-08-19 — House format: the owner's blunder becomes the audience's puzzle

**Decision:**
Primary content format is "I played this position. It's losing. Can you see why?" — the owner's real mistake presented as a puzzle for the audience.

**Reason:**
It is simultaneously authentic (a real game), participatory (answers go in comments, which is what actually builds community rather than an audience), and gives a "can you find it?" hook without claiming expertise. It merges the personality lane and the volume lane into one format.

**Alternatives considered:**
Separate lanes for own-game recaps and Lichess-database puzzles.

**Risk:**
Requires a supply of the owner's own instructive mistakes, so playing volume gates content volume.

**Status:**
Accepted

### 2026-08-19 — Deterministic HTML/CSS renderer, driven by explicit frame numbers

**Decision:**
The renderer is an HTML/CSS scene system screenshotted frame by frame and muxed with FFmpeg, driven by an explicit `renderFrame(n)` call rather than wall-clock CSS animation.

**Reason:**
The product requirement moved from "clean board animation" to "professional, with a character, speech bubble, and move-quality effects". CSS reaches that polish far faster than hand-positioned Pillow drawing. Driving by frame number rather than wall clock preserves the determinism requirement — identical `moves.json` plus identical assets must produce an identical video.

**Alternatives considered:**
Pillow frame compositor (recommended earlier the same day, then reversed — faster to render, much slower to make look good); MoviePy; Manim.

**Risk:**
~1–2 minutes render time per video instead of seconds, and a headless-browser dependency in an unattended pipeline. Both acceptable for an overnight batch.

**Status:**
Accepted, supersedes the Pillow-compositor choice made earlier the same day

### 2026-08-19 — Original mascot only; no third-party IP in output

**Decision:**
The on-screen character is an original mascot owned by the project, shipped as a swappable sprite set (expression PNGs plus a mouth-shape strip). No third-party characters, mascots, branding, or app UI appear in published video. Piece and mascot art must be original or verifiably licensed for commercial use.

**Reason:**
Duolingo's characters are trademarked and copyrighted; using them in monetised daily content invites takedowns and worse, and "it's educational" is a defence to be argued rather than a shield. An owned mascot is also the better business asset — it becomes the thing the channel is recognised by, which rented IP can never do. Several popular chess piece sets are GPL-licensed artwork and are unsuitable for monetised video.

**Alternatives considered:**
Using Duolingo's characters; using popular GPL-licensed chess piece sets.

**Risk:**
Good character art is a real dependency that code cannot substitute for. Mitigation: ship a clean geometric mascot behind the sprite interface, commission a proper character sheet when traction justifies it — swapping is a file copy.

**Status:**
Accepted

### 2026-08-19 — "Presenter" layout selected

**Decision:**
9:16 layout with the hook at top, board at ~70% width centred, and a wide speech bubble above a bottom-centred mascot. The speech bubble and the subtitle are the same element.

**Reason:**
Narration needs real caption real estate that never overlaps the board, and merging the bubble with the caption avoids two competing text elements. Platform UI dead zones — top ~7%, right ~13%, bottom ~14% — are hard constraints.

**Alternatives considered:**
Board-dominant with a thin caption line (too little room for narration); mascot peeking from the right edge (collides with platform action buttons).

**Risk:**
A smaller board than the board-dominant option. Acceptable at 70% width on a 1080-wide frame.

**Status:**
Accepted

### 2026-08-19 — YouTube Shorts is the first automated publishing target

**Decision:**
Automate YouTube Shorts first. Instagram Reels, TikTok, and Facebook come later.

**Reason:**
It is the only target with an open official upload API usable today. Instagram Reels requires a Business account through the Graph API; TikTok's content posting API requires app review.

**Alternatives considered:**
Instagram Reels first; manual posting everywhere indefinitely.

**Risk:**
Single-platform concentration early on. Accepted — a second platform is additive once the first works.

**Status:**
Accepted

### 2026-08-19 — Adopted the template's session-wrap automation, with the deploy step removed

**Decision:**
Copied and adopted the project template's `Stop` hook (`.claude/hooks/session-wrap.sh`), the `main` fast-forward script (`.claude/hooks/git-sync-main.sh`), and the wrap-up checklist (`.claude/commands/wrap-session.md`). Every coding session now ends with the agent files updated, a conventional commit, and `main` pushed — automatically, without the owner asking. The template's deploy step and `deploy.sh` were deliberately not copied.

This supersedes the earlier note that these were unvalidated template assumptions. They have now been inspected, adapted to this repository (`Agent/` paths, Python/uv permissions), and adopted.

**Reason:**
The owner asked for agent files to be updated and pushed automatically at the end of every session. The template already implemented exactly that, and the scripts are safe by construction: `git-sync-main.sh` never commits, never rewrites history, never force-pushes, and refuses any non-fast-forward update to `main`.

**Alternatives considered:**
Writing a new hook from scratch; a manual end-of-session routine; a `post-commit` git hook.

**Risk:**
Automatic pushes to `main` with no review gate mean a bad commit reaches the remote immediately. Mitigated by the private repository, the secrets check in the checklist, fast-forward-only enforcement, and full git history for reverts. There is no deploy step, so nothing reaches an audience without the separate human approval gate.

**Status:**
Accepted

### 2026-08-19 — Selective template adoption, not wholesale copy

**Decision:**
Copied a relevant subset of `~/Documents/Github/Templates/Project-Template` into this repository — automation hooks, 20 skills, Python and cross-cutting rules, 14 workflows, 12 docs, and the doc templates. Originals were copied, never moved.

Deliberately excluded: the stale `.claude/worktrees/` snapshot, the duplicate `.agents/` and `claude/` skill trees, `.codex/` and `.gemini/`, bootstrap and setup prompts, `deploy/`, `benchmarks/`, `examples/`, the `trading-content` skill, language rules for TypeScript/Go/Rust/Swift/Vue/React/React Native, and the LLM provider matrix docs — which this project's own decisions already say not to treat as authoritative.

**Reason:**
The template carries ~180 files, most of which describe stacks and workflows this project does not use. Copying all of it would bury the project's own documentation in generic scaffolding.

**Risk:**
A later stack change may require pulling in more rule sets. Cheap to do on demand.

**Status:**
Accepted

### 2026-08-19 — Adopt the `PROJECT_MASTER_CONTEXT` truth model; split truth from presentation

**Decision:**
Replace the `moves.json` schema drafted in `docs/PLAN.md` with the stricter model from `docs/PROJECT_MASTER_CONTEXT.md` §8, and split the contract into three files:

```text
moves.json     truth - what happened, and how well it is known
analysis.json  engine evaluation
scene.json     presentation - derived from the two above
```

Key changes from the earlier draft:

- `verification_status` (`verified` | `human_confirmed` | `unresolved`) is separate from `verification_basis` (`unique_path`, `legal_path`, `local_visual`, `human_confirmed`).
- `model_support` is an annotation and is explicitly **not** a valid basis value. A VLM cannot make a move verified.
- UCI is canonical; SAN is derived from the board and asserted against it. A mismatch is a hard failure.
- Observed board facts and inferred metadata each carry a `provenance` field.
- Mascot cues are anchored to a `ply` plus an offset and resolved at render time, never hand-authored at absolute timestamps.
- Mascot occlusion of the discussed move's from/to squares is a hard validator failure, not a guideline.

**Reason:**
The earlier draft used a single enum containing `model_supported`, which implied a model could constitute a verification status. That contradicts the project's first non-negotiable. Storing UCI and SAN without a reconciliation rule invited silent disagreement. Putting mascot cues in `moves.json` would have put presentation data in the truth file.

**Alternatives considered:**
Keeping the single-enum draft; one combined contract file; absolute-time mascot cues.

**Risk:**
More schema surface to validate. Accepted — each addition closes a specific failure mode rather than adding generality.

**Status:**
Accepted, supersedes the schema drafted earlier the same day

### 2026-08-19 — Mascot Set 2 selected (red-haired, edge-peek); Set 1 rejected

**Decision:**
The mascot is the Set 2 character — red/ginger hair, round black glasses, white hoodie with a navy knight emblem, navy striped cuffs — in its edge-peek framing. Set 1 (brown hair, square glasses, teal palette, full body) is rejected. Edge-peek becomes the signature move; variety comes from which edge, lean depth, scale and reaction rather than from new poses.

**Reason:**
The two sets are different characters, not variants, and mixing them would violate the visual-consistency rule in `PROJECT_MASTER_CONTEXT.md` §2.1. Set 2 wins on the metric that decides the mascot's usefulness: at a mascot footprint of ~30% of a 1920-tall frame, Set 2's face renders ~260px tall versus ~75px for Set 1's full-body framing. Expression legibility is the mascot's entire function.

**Alternatives considered:**
Set 1 (freely placeable, supports more entry directions, but unreadable expressions at scale); regenerating a fresh consistent set (delays Phase 0 and re-runs the consistency risk).

**Risk:**
Every Set 2 pose is anchored to a wall with the hands gripping it, so the five entry directions in §2.6 are not achievable without regenerating poses. Accepted: a single recognisable move is branding, not a defect. Consequences to handle in production: keep a sliver of wall in the sprite, crop the baked-in decorations (the thought bubble, `?`, `!`, toppling king) so the renderer owns all overlays, and expect the fine ginger hair to need manual cleanup after matting.

Open item: `PROJECT_MASTER_CONTEXT.md` §2.1 states the red-haired Pinterest character was inspiration only. Since Set 2 is a red-haired boy in round black glasses, confirm deliberately that it clears that rule before monetising.

**Status:**
Accepted

### 2026-08-19 — Mascot Set 2 blocked: derivative of a copyrighted character

**Decision:**
Reverse the Set 2 selection made earlier the same day. None of the ten generated concepts in `assets/Character/` are cleared for published output.

The reference image supplied as "the original character" is Sherman from DreamWorks' *Mr. Peabody & Sherman* (2014) — a registered, actively enforced character, not a public-domain or free one. Set 2 retains its identifying combination: ginger swept-up hair, large round black-rimmed glasses, amber eyes, child proportions, and the peek-around-a-white-edge pose, which is the composition of the reference promo still.

**Reason:**
Copyright covers derivative works. Generating new pixels from a copyrighted character produces a derivative, not an original — the test is whether a viewer would recognise the source, not whether the output is a pixel-level copy. That an image generator produced it is not a defence and arguably evidences the derivation. Any single element here would be unremarkable; the combination is what makes it recognisable.

This is the failure mode the project's own rule in `PROJECT_MASTER_CONTEXT.md` §2.1 exists to prevent.

**Alternatives considered:**
Publishing Set 2 as-is; changing one identifier such as hair colour only (insufficient — recognisability survives a single change).

**Risk of the decision:**
Delays Phase 0 mascot work. Accepted — the alternative risks takedowns, channel strikes, and legal exposure on a monetised channel, against an asset the project does not own.

**Resolution direction, preferred order:**

1. **Non-human mascot — a chess-piece character** (knight or pawn with eyes and expressions). No human-character IP surface, thematically native, unmistakably owned, cheaper to animate, and a simple silhouette stays legible at any on-screen size — which also solves the expression-legibility problem that drove the Set 2 choice.
2. **A redesigned human character** changing at least three identifiers simultaneously: hair colour *and* silhouette, glasses shape, and a different signature pose.

Everything character-agnostic from the Set 2 decision survives: the popup lifecycle, the three-popup budget, the swappable sprite contract, edge-peek as a signature move, the no-baked-decorations rule, and the occlusion validator.

**Status:**
Accepted, supersedes the Set 2 selection made earlier the same day

### 2026-08-19 — Repository made public; licensing is now unresolved

**Decision:**
The owner set the repository to public. Record the two consequences and treat the licence question as an open decision requiring the owner's choice, not an implementation detail.

**Reason:**

1. `python-chess` is GPL-3.0 and this project imports it. A public repository distributes the code, so the combined work must be GPL-3.0-compatible. There is currently **no `LICENSE` file**, which grants no one permission while the obligation still applies. Publishing under GPL-3.0 means anyone — including someone starting a competing channel — may legally take and run the whole system.
2. Git history is permanent and world-readable. The blocked Set 2 concept art was committed in `b75abc1` before the block was known, so it is now in public history. Deleting it from `HEAD` does not remove it from history.

**Alternatives considered:**
Add GPL-3.0 and stay public (gives the system away); return to private (closes both issues, since GPL obligations attach to distribution); replace `python-chess` with a permissively licensed alternative (substantial rework, and it is the best tool for the job).

**Risk:**
Remaining public with no licence leaves both the IP exposure and the licence obligation unresolved. Not a legal opinion — proper advice is warranted before choosing to stay public.

**Recommendation:**
Return the repository to private until the licence and mascot-IP questions are settled. It is one reversible command and preserves the business option.

**Status:**
Open — requires an owner decision

### 2026-08-19 — Multi-platform publishing: one release, four adapters

**Decision:**
Adopt the architecture in `docs/MULTI_PLATFORM_PUBLISHING.md` and the seven skills added with it. One verified master short produces platform-specific copy, passes one approval, then fans out to four independent publisher adapters. Idempotency is keyed on `content_id + platform`; a single platform failure retries only that platform.

**Reason:**
A YouTube-only pipeline would not meet the reach goal, and four unrelated upload systems would duplicate approval, validation, and state logic. The shared-release-plus-adapters shape keeps one approval gate and one audit trail while letting per-platform API differences live in adapter code.

The skills are also correctly conservative in ways worth preserving: `meta-publishing` deliberately refuses to hard-code endpoints and requires checking current official documentation first; `platform-metadata` returns `FACT_GAP` rather than inventing an unsupported chess claim; `analytics-feedback` treats `null` as unavailable rather than zero and records observations rather than causal claims; `tiktok-publishing` will not label a draft upload as published.

**Alternatives considered:**
YouTube-only; four independent systems; identical copy on every platform.

**Risk:**
Implementing four APIs before one postable short exists is the main scheduling hazard — the skills are specifications, not working publishers, and `src/publishers/` is still empty. Publishing code stays sequenced after the first manual post, per `docs/PLAN.md`.

**Status:**
Accepted as architecture; implementation deferred to Phase 2

### 2026-08-19 — Mascot is an original pawn, drawn by the renderer

**Decision:**
The mascot is a **pawn** with eyes, eyebrows, stub arms and whole-body squash/stretch/tilt, drawn as vector shapes by the renderer rather than shipped as image assets. Replaces the blocked human concepts.

**Reason:**

- It is the learner's piece — weakest, most numerous, the one beginners throw away carelessly. That is the channel's subject matter in one object.
- It is the only piece whose own rules contain an improvement arc, which matches the rating-journey spine already in `BRIEF.md`.
- Simplest silhouette in chess, so it stays legible at any on-screen size. That was the exact problem that eliminated the full-body human concept.
- Zero human-character IP surface — a pawn cannot be a derivative of someone else's character.
- Drawn by the renderer means no illustrator, no image generation, no background matting, no font/art licence question, and deterministic output. Phase 0 mascot work is unblocked with no external dependency.

Palette: cream body `#F2EDDF`, deep navy outline and features `#1E2A44`, single warm amber accent `#E0A33E`. Deliberately avoids green/yellow/orange/red/gold, which are owned by the move-quality treatments, so a badge firing beside the mascot never reads as part of it.

Ten expression states. `facepalm` is replaced by `deflated` (drooping body, shut eyes) since a pawn has no real hands.

Documented as a later mechanic: the mascot **promotes** as the owner's rating climbs — pawn → knight → bishop → rook → queen — keeping the same eyes, outline and palette. A visible reward structure derived from the owner's own progress, which no competitor's mascot can copy.

**Alternatives considered:**
A knight (more visually distinctive, but reads as clever/tricky, which is closer to the guru posture the positioning rejects); a redesigned human character (still carries human-character IP risk and needs an artist); commissioning raster art now (delays Phase 0).

**Risk:**
A vector mascot has a lower ceiling on visual richness than commissioned illustration. Mitigated by keeping a swappable sprite interface in the renderer, so raster art can drop in later without touching scene logic. The board pieces are also switched to original vector glyphs for the same reason, which removes the piece-art licensing problem rather than solving it.

**Status:**
Accepted

### 2026-08-19 — Repository stays public under GPL-3.0-or-later

**Decision:**
Keep the repository public, as the owner intends to publish ideas there. Add a `LICENSE` containing the verbatim GNU GPL v3 text and license the project GPL-3.0-or-later. Supersedes the earlier recommendation to return to private.

**Reason:**
`python-chess` is GPL-3.0-or-later (confirmed: `chess` 1.11.2, `License: GPL-3.0+`) and this project imports it. A public repository distributes the code, so the combined work must be GPL-3.0-compatible — GPL-3.0-or-later is the only correct choice, not a preference.

The constraint is also the best available outcome for staying public: GPL is copyleft, so anyone who takes this system and distributes their version must open-source their changes too. A permissive licence would let a competitor take it and close it.

**Alternatives considered:**
Return to private (closes the licence and IP exposure, but blocks the owner's stated reason for the repository); staying public with no licence (grants nobody permission while the obligation still applies — the worst combination); replacing `python-chess` with a permissively licensed alternative (substantial rework, and it is the right tool).

**Risk:**
Anyone may legally run this content OS. Accepted deliberately — the owner's moat is the channel, the voice, and the audience, none of which are in the repository.

**Consequences handled in this change:**

- `LICENSE` added (verbatim GPL v3, 674 lines).
- The blocked mascot concept art is untracked and gitignored. It remains in public history from commit `b75abc1`; removing it from `HEAD` does not remove it from history, and a history rewrite would require a force-push, which `git-sync-main.sh` deliberately refuses. Flagged as an outstanding item rather than actioned unilaterally.
- All 7 absolute `/Users/<name>/...` paths replaced with `<repo root>` / `<MoneyPrinterTurbo>` placeholders across `BRIEF.md`, `MEMORY.md`, `TODO.md` and `PROJECT_MASTER_CONTEXT.md`, so the repository no longer publishes the owner's real name in file paths.

**Status:**
Accepted, supersedes the return-to-private recommendation

---

## Superseded and resolved

- **Inherited template automation** — previously recorded as unvalidated template assumptions (`Stop` hook, session wrap-up, `main` fast-forwarding, config-driven deployment). Now inspected and adopted, except deployment, which was dropped. See the 2026-08-19 adoption decision above.
- **TTS for all narration** — superseded 2026-08-19 by the owner's-voice decision.
- **Pillow frame compositor** — superseded 2026-08-19 by the HTML/CSS renderer decision.
