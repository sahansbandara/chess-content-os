# Chess Content OS — Agent Memory

> Last updated: 2026-08-19
> Purpose: durable project knowledge that future coding/agent sessions should load before making changes.

## Do not store

Never store:

- passwords;
- API keys;
- private keys;
- access tokens;
- bank/card details;
- production secrets;
- unrelated sensitive personal data.

It is acceptable to store an environment-variable name or non-secret credential label such as `PRIMARY` / `BACKUP`; never store the secret value.

## Core project purpose

Chess Content OS is a reusable AI-assisted, human-approved chess social-content pipeline.

The project is not simply a video generator. Its purpose is to convert chess source material into verified move data, clean rendered content, AI-written platform copy, an approval workflow, publishing, and a future analytics feedback loop.

First source: Duolingo Chess gameplay recordings.

First public positioning:

```text
Learning chess in public — solve, learn, improve with me.
```

Long-term direction:

```text
audience
→ useful free content
→ lead magnet / puzzle resource
→ paid digital product
→ beginner course only after evidence of expertise/demand
→ optional partnerships/merch later
```

## Non-negotiable architecture rule

Chess truth and creative AI are separate layers.

```text
Visual evidence
→ local board/state perception
→ python-chess legality
→ ambiguity audit
→ optional constrained VLM evidence
→ verified moves
→ Stockfish analysis
→ deterministic renderer
→ AI language/creative layer
```

Never let an LLM/VLM invent a move merely to complete the sequence.

## Current local environment

Project root:

```text
/Users/sahansandaruwan/Dev/chess-content-os
```

Current tools/dependencies used by the project:

```text
uv-managed Python 3.11.15
FFmpeg 8.1.1
ImageMagick 7.1.2-29
python-chess
opencv-python-headless 5.0.0.93 (cv2 reports 5.0.0)
google-genai
python-dotenv
```

System Python should not be replaced for this project.

## Current repository layout

```text
assets/
  raw/
  processed/
  puzzles/
  templates/
inbox/
logs/
output/
skills/
  chess-content/
  chess-video-editing/
src/
  agents/
  approval/
  database/
  publishers/
  providers/
  validators/
  workers/
README.md
.gitignore
pyproject.toml
uv.lock
```

Git was initialized on `main`. Do not assume template session/deploy hooks are active in this repository without inspecting/testing them.

## Prototype source recording

```text
/Users/sahansandaruwan/Dev/MoneyPrinterTurbo/storage/local_videos/
material-3cc02343e1b64dbeb464b7127ad0187b.mov
```

Observed metadata during the prototype:

```text
Duration: ~41.40 s
Resolution: 1320 × 2868
Frame rate: ~60 FPS
Codec: HEVC/H.265
Source: ReplayKit
Audio: present
```

## MoneyPrinterTurbo state

Local MoneyPrinterTurbo location:

```text
/Users/sahansandaruwan/Dev/MoneyPrinterTurbo
```

The app/WebUI works locally, but its first gameplay-editing attempt shortened/chopped the source recording. The project decision is therefore:

```text
MoneyPrinterTurbo = optional AI video / creative worker
MoneyPrinterTurbo != chess gameplay truth/editor
```

## Board calibration

Known calibration geometry for the prototype recording:

```text
raw frame: 1320 × 2868
board: 1320 × 1320
board top: ~962 px
square size: 165 px
orientation: Black perspective / 180° rotated
```

Board-coordinate reminder for the rotated view:

```text
Top-left    = h1
Top-right   = a1
Bottom-left = h8
Bottom-right= a8
```

## Template profiles

Legacy profile:

```text
assets/templates/duolingo/profile.json
```

Current V2 profile:

```text
assets/templates/duolingo_v2/profile.json
```

V2 stores color-aware templates (`.npz`) using RGB + mask data.

Known calibration luma ranges from the current prototype:

```text
white pieces: ~194.26–204.89
black pieces: ~89.25–102.03
```

These are calibration observations, not universal constants. Recalibrate if theme/device visuals change.

## Current board scanner

Worker:

```text
src/workers/duolingo_board_scanner.py
```

Important behavior:

- scans all 64 squares;
- uses V2 color templates;
- constructs `chess.Board(None)`;
- outputs piece-placement FEN using `board.board_fen()`;
- does not claim full FEN metadata.

Calibration position output:

```text
r1bqr1k1/pp3ppp/2n2n2/3pN3/3P4/1BB5/PPPQ1PPP/R3K2R
```

Visual inspection matched the screenshot at the calibration point.

## Current move-extraction workers / experiments

Files created during the prototype include:

```text
src/workers/duolingo_template_bootstrap.py
src/workers/duolingo_color_template_bootstrap.py
src/workers/duolingo_board_scanner.py
src/workers/duolingo_state_sequence_probe.py
src/workers/duolingo_move_chain_probe.py
src/workers/duolingo_multi_ply_probe.py
src/workers/duolingo_path_ambiguity_probe.py
src/workers/duolingo_visual_ambiguity_probe.py
src/workers/duolingo_departure_probe.py
src/workers/duolingo_departure_audit.py
src/workers/duolingo_path_frame_score.py
src/workers/video_evidence_builder.py
src/workers/gemini_chess_video_probe.py
src/providers/gemini_client.py
```

Older experimental detector/normalizer files also exist. Do not delete or overwrite experiments without explicit approval; create new files for new approaches unless a deliberate migration is approved.

## Rapid section state

Primary difficult window:

```text
13.50s → 19.50s
```

The state-sequence probe produced 24 stable observed state runs in the current prototype window.

Important observed states include:

```text
State01 13.50 r1b1r1k1/pp3ppp/8/3rP3/4n3/1BB5/PPP2PPP/2KR3R
State02 13.75 r1b1r1k1/pp3ppp/8/3BP3/4n3/2B5/PPP2PPP/2KR3R
State04 14.25 r1b1r1k1/pp3ppp/8/3BP3/8/2n5/PPP2PPP/2KR3R
State05 14.50 r1b1r1k1/pp3ppp/8/3BP3/8/2P5/P1P2PPP/2KR3R
State06 14.75 r3r1k1/pp3ppp/4b3/3BP3/8/2P5/P1P2PPP/2KR3R
State07 15.00 r3r1k1/pB3ppp/4b3/4P3/8/2P5/P1P2PPP/2KR3R
State08 15.25 1r2r1k1/pB3ppp/4b3/4P3/8/2P5/P1P2PPP/2KR3R
State09 15.50 1r2r1k1/p4ppp/4b3/3BP3/8/2P5/P1P2PPP/2KR3R
State11 16.00 1r2r1k1/p5pp/5p2/3RP3/8/2P5/P1P2PPP/2K4R
State12 16.25 1r2r1k1/p5pp/8/3Rp3/8/2P5/P1P2PPP/2K1R3
State14 16.75 1r4k1/p5pp/8/4R3/8/2P5/P1P2PPP/2K5
State15 17.00 5rk1/p5pp/8/4R3/8/2P5/P1P2PPP/2K5
State16 17.25 6k1/p5pp/8/4R3/2P2r2/8/P1P3PP/2K5
State17 17.50 6k1/p5pp/8/2P1R3/8/8/P1P2rPP/2K5
State18 17.75 6k1/p5pp/5r2/2P1R3/8/8/P1P3PP/2K5
State20 18.25 6k1/p5pp/4r3/2P1R3/6P1/8/P1P4P/2K5
State21 18.50 6k1/p5pp/2r5/2P1R3/6P1/8/P1P4P/2K5
State22 18.75 6k1/p5pp/2r5/2P1R3/6PP/8/P1P5/2K5
State23 19.00 8/p4kpp/2r5/2P1R3/6PP/8/P1P5/2K5
State24 19.50 8/p4kpp/2r5/2P1R1P1/7P/8/P1P5/2K5
```

Some skipped/intermediate sampled states are intentionally omitted from this memory summary because they are known to be animation/noise-prone. Use the probe logs/scripts for the full raw list.

## Legal move chain recovered so far

Current 36-move candidate sequence:

```text
01  Bxd5   b3d5
02  Nxc3   e4c3
03  bxc3   b2c3
04  Be6    c8e6
05  Bxb7   d5b7
06  Rab8   a8b8
07  Bd5    b7d5
08  Bxd5   e6d5
09  Rxd5   d1d5
10  f6     f7f6
11  Re1    h1e1
12  fxe5   f6e5
13  Rdxe5  d5e5
14  Rxe5   e8e5
15  Rxe5   e1e5
16  Rf8    b8f8
17  f4     f2f4
18  Rxf4   f8f4
19  c4     c3c4
20  Rf2    f4f2
21  c5     c4c5
22  Rf6    f2f6
23  g4     g2g4
24  Re6    f6e6
25  Rh5    e5h5
26  Rc6    e6c6
27  Re5    h5e5
28  Kh8    g8h8
29  h4     h2h4
30  Kg8    h8g8
31  Re8+   e5e8
32  Kf7    g8f7
33  Re5    e8e5
34  Kg8    f7g8
35  g5     g4g5
36  Kf7    g8f7
```

Important: this sequence reaches the observed state chain but contains choices through bridges that were not uniquely determined by board states alone. Do not label all 36 moves "verified" until ambiguity is resolved.

## Ambiguity state

The path ambiguity audit found:

```text
14 unique bridges
5 ambiguous bridges
```

Ambiguous bridges:

```text
Bridge 10: State12 → State14
Bridge 16: State20 → State21
Bridge 17: State21 → State22
Bridge 18: State22 → State23
Bridge 19: State23 → State24
```

Bridge 10 candidates:

```text
A: Rdxe5 → Rxe5 → Rxe5
B: Rexe5 → Rxe5 → Rxe5
```

Local departure evidence:

```text
d5 departure ≈ 16.3667s
e1 departure ≈ 16.6333s
selected: d5 first
```

Full-path frame scoring also preferred candidate A over candidate B in the control test.

Bridges 16–19 were not reliably discriminated by the current full-path static scorer. Never accept rank #1 merely because it prints first when the top-score gap is zero.

## Evidence builder

Worker:

```text
src/workers/video_evidence_builder.py
```

Board-only rapid clip:

```text
output/evidence_test/rapid_board.mp4
```

Current prototype evidence export:

```text
Source FPS: 60
Duration: 6.00s
Evidence FPS: 12
Frames exported: 72
Manifest: output/evidence_test/dense_frames/manifest.json
```

`12 FPS` is a prototype sampling choice, not a universal truth. Increase or localize density if visual controls prove it misses transitions.

## Gemini configuration / state

Environment variable names:

```text
GEMINI_API_KEY_PRIMARY
GEMINI_API_KEY_BACKUP
GEMINI_VIDEO_MODEL
```

Never store their values here.

Provider file:

```text
src/providers/gemini_client.py
```

Current observed live test:

```text
BACKUP label: success / returned OK
PRIMARY label: ServerError in that test
```

Current provider ordering attempts the proven-working `BACKUP` label first.

## Gemini whole-video experiment — failed as chess truth source

Analysis video:

```text
output/evidence_test/rapid_board_gemini.mp4
```

Observed properties:

```text
72 frames
~71.083333 seconds
```

Worker:

```text
src/workers/gemini_chess_video_probe.py
```

Gemini returned 25 moves with high confidence, but the sequence substantially disagreed with the legal reconstruction. It also produced consecutive same-side moves. Therefore:

```text
DO NOT use open-ended Gemini whole-video extraction as the move authority.
```

Current narrowed hypothesis:

```text
local CV + python-chess candidates
→ small evidence pack
→ Gemini compares constrained alternatives
→ python-chess validates final selection
```

### Bridge 10 constrained control — PASSED 2026-08-19

Worker:

```text
src/workers/gemini_bridge10_image_probe.py
```

Log:

```text
logs/gemini_bridge10_image_probe.json
```

Result:

```text
model: gemini-3.6-flash
key label: BACKUP
input: 7 frames, t=16.250s -> 16.750s
selected_candidate: A
selected_first_source: d5  -> e5
confidence: medium
```

The model's stated reasoning matched the known local departure order: d5 rook leaves first, Black recaptures on e5, then the e1 rook follows. This agrees with the local departure timing (d5 ~16.3667s, e1 ~16.6333s).

Caveats that must be cleared before trusting this on Bridges 16-19:

- one trial only;
- frames were hand-picked around a window where the answer was already known;
- self-reported confidence was only `medium`;
- no shuffled/reversed frame-order control was run. A model that answers A regardless of frame order has proved nothing.

## Repository research memory

### DeepSeek Harness

```text
https://github.com/deepseek-ai/deepseek-harness
```

Useful concept: plugin/provider architecture and swappable service seams.

Use here: future `VideoUnderstandingProvider` / model-provider abstraction.

Do not: migrate the current Python MVP into the harness before the core workflow works.

### YouTube Automation Agent

```text
https://github.com/sahansbandara/youtube-automation-agent
```

Useful concepts: provider fallback, YouTube publishing, scheduling, analytics.

Use here: later publishing/analytics/provider abstraction.

Do not: treat it as the chess visual reader.

### Free LLM API Resources

```text
https://github.com/jtig37/free-llm-api-resources
```

Useful concept: provider discovery.

Do not: trust it as current model/quota/pricing authority without checking provider documentation.

### VISIONE

```text
https://github.com/aimh-lab/visione
```

Useful concepts: temporal preprocessing, scene/shot extraction, keyframes, evidence retrieval.

Adaptation for this project:

```text
Chess Micro-Shot
= before + transition + after around one move event
```

Do not: install the full VISIONE stack for the MVP unless later evidence shows it is necessary.

### blind_navigation

```text
https://github.com/wink-wink-wink555/blind_navigation
```

Useful concept:

```text
deterministic frame perception
→ event detection
→ LLM output
```

Use here: local CV should create the evidence/event before the model is called.

Do not: reuse its domain-specific YOLO weights for chess.

### MoneyPrinterTurbo

```text
https://github.com/harry0703/MoneyPrinterTurbo
```

Useful role: AI-generated video worker / creative material generation.

Not suitable as exact chess replay editor in current prototype.

## MCP / skills memory

Source design principles come from `AI_Agent_Systems_Complete_Guide.md`.

Preferred tool order:

```text
1. Direct API / local library
2. MCP tool
3. Browser automation
4. Computer Use
```

MCP is a standardized tool interface, not an intelligence layer. Do not add MCP simply to claim the project is "agentic".

Skills are reusable procedures. The project should progressively create:

```text
skills/chess-content/
skills/chess-video-editing/
skills/chess-video-reading/
skills/chess-puzzle-content/
skills/platform-metadata/
skills/content-evaluator/
```

A mature skill should include:

```text
SKILL.md
examples/
templates/
scripts/
validation-rules.md
evaluation-rubric.md
```

## Agent architecture memory

```text
Content Orchestrator
├── Gameplay Worker
├── Puzzle Worker
├── AI Video Worker
├── Chess Validator
├── Chess Analysis Worker
├── Script/Metadata Agent
├── Evaluator
├── Approval Bot
├── Publisher
└── Analytics / Idea Engine
```

The orchestrator should coordinate specialists. It should not contain all domain logic itself.

## Feedback-loop principle

```text
Generate
→ Evaluate
→ Find weaknesses
→ Revise
→ Test again
→ stop when threshold/kill criterion is reached
```

For Chess Content OS, there are two distinct loops:

```text
Truth loop:
visual state → candidate moves → legality → ambiguity → more evidence

Content loop:
verified chess data → script/render → evaluator → revision → human approval
```

Never mix the two. A prettier explanation cannot repair an unverified move sequence.

## Patterns that worked

- Preserve old experiments instead of repeatedly overwriting them.
- Use a known control case before trusting a new ambiguity resolver.
- Separate observed board state from inferred legal metadata.
- Use `python-chess` legality to constrain visual uncertainty.
- Use explicit provider wrappers rather than embedding keys/model calls throughout workers.
- Use board-only crop instead of sending unrelated phone UI to visual models.
- Treat model confidence text as untrusted until validated against chess legality/evidence.

## Mistakes to avoid

- Do not accept candidate #1 when multiple paths have the same score.
- Do not call a piece-placement FEN a complete FEN.
- Do not let a VLM write SAN as the first stage of visual analysis.
- Do not use AI strategic plausibility to choose between visually ambiguous paths.
- Do not install large external frameworks before proving a small workflow they would improve.
- Do not add publishing automation before the generation/evaluation pipeline is reliable.
- Do not log secrets.
- Do not assume the generic template's Claude hooks/deployment automation is active in this repo until inspected and tested.

## Product decisions locked 2026-08-19

### Positioning — governs all generated copy

Learner sharing mistakes, never a guru teaching from authority.

```text
Everyone else:  "The best move here is Nf6."
This channel:   "2 mistakes and I got mated in 11. Don't do what I did."
```

House format: the owner's own blunder becomes the audience's puzzle — "I played this. It's losing. Can you see why?" Authentic, participatory, and no expertise claimed.

Clip selection targets the **owner's** eval swings, not the objectively best chess. Story shape is fixed: mistake -> what it cost -> what should have been played -> pattern to avoid.

### Voice

```text
first-person content  -> owner's real recorded voice, batch-recorded weekly (~30 min/week)
no personal claim     -> Kokoro-82M local TTS
```

Supersedes the earlier TTS-for-everything choice. A synthetic voice saying "I made this mistake" is audibly hollow and removes the only differentiator stronger channels cannot copy.

### Renderer

HTML/CSS scene system, screenshotted frame by frame, muxed with FFmpeg. Driven by an explicit `renderFrame(n)` call, **never** wall-clock CSS animation — that is what preserves determinism.

Supersedes the earlier Pillow-compositor choice. Reason: the requirement moved from "clean board" to "professional, with character and effects", and CSS reaches polish far faster. Cost: ~1-2 min render per video instead of seconds. Fine on an overnight batch.

Layout selected: **Presenter** — hook top, board ~70% width centred, wide speech bubble above a bottom-centred mascot. The bubble and the subtitle are the same element. See `design.md`.

Platform UI dead zones are hard constraints: top ~7%, right ~13%, bottom ~14%.

Perceived polish comes mostly from easing, the freeze beat before the reveal, and a live eval bar — not from the character art.

### IP boundaries — business risk, not a style note

```text
NEVER in published output: Duolingo characters, Duolingo branding, Duolingo UI chrome
NEVER in monetised output: GPL-licensed chess piece artwork
```

Mascot is original, owned by the project, shipped as a swappable sprite set (expression PNGs + mouth-shape strip). Swapping art is a file copy, not a code change.

`python-chess` is GPL-3.0 — no practical effect while this repo is private; must be addressed before making it public.

### First publish target

YouTube Shorts. Only platform with an open official upload API today. Instagram Reels needs a Business account via Graph API; TikTok's posting API needs app review.

## Repository automation

Adopted from the project template on 2026-08-19 and adapted to this repo:

```text
.claude/hooks/session-wrap.sh      Stop hook - blocks once when work is uncommitted/unpushed
.claude/hooks/git-sync-main.sh     pushes branch, fast-forwards main, pushes main
.claude/commands/wrap-session.md   the checklist the hook injects
.claude/settings.json              permissions + Stop hook registration
```

Every session must end with agent files updated, a conventional commit, and `main` pushed. Standing policy — do not ask whether to run it.

Safety properties of `git-sync-main.sh`: never commits, never rewrites history, never force-pushes, refuses any non-fast-forward update to `main`.

The template's deploy step and `deploy.sh` were deliberately **not** copied — this project has no deployment target.

Agent files live in `Agent/` (capitalised). The template used lowercase `agent/`; macOS is case-insensitive so both resolve, but all copied references were rewritten to `Agent/` so the repo does not break on a case-sensitive filesystem.

## Current falsification rules

1. Any new visual method must pass the Bridge 10 control before being trusted on Bridges 16–19. **Constrained Gemini passed on 2026-08-19 (one trial).**
2. Constrained Gemini must also pass a shuffled/reversed frame-order control before it is used on any unresolved bridge. Not yet run.
2b. If the renderer alters, reorders, or drops verified moves, reject the renderer implementation.
2c. If generated copy claims expertise the owner does not have, reject the copy — see the positioning rules in `BRIEF.md`.
3. If the local scanner fails on new recordings/themes, recalibrate before adding more heuristics.
4. If the deterministic renderer changes verified move truth, reject the renderer implementation.
5. If platform automation cannot preserve human approval and rollback, do not enable autonomous publishing.

## Current next action

Execute Phase 1 of `docs/PLAN.md`: freeze the `moves.json` contract from a hand-written example, then build Stockfish analysis, moment selection, the renderer, and the voice/caption layer.

Bridges 16-19 are no longer a blocker. They are resolved by human confirmation of the move list, and they sit in a drawn endgame shuffle that gets cut from a 35-second short anyway.

Outstanding validation debt on the Bridge 10 control: repeat it 3-5 times and test with shuffled/reversed frame order before applying constrained Gemini to any unresolved bridge.
