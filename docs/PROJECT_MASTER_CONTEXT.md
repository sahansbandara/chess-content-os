# Chess Content OS — Project Master Context

> Status: Canonical handoff and strategy document
> Updated: 2026-08-19
> Repository: `sahansbandara/chess-content-os`
> Purpose: Preserve the full product vision, content positioning, mascot/video system, technical architecture, research findings, agent rules, and implementation direction in one place.

---

# 1. End Goal and Brand Positioning

Chess Content OS is an AI-assisted, human-approved content operating system that turns the owner's real chess activity into accurate, polished, short-form social content.

It is **not** a generic video generator and it is **not** a guru-style chess teaching channel.

The core idea is:

> **I am learning chess too. These are the mistakes I made, what I learned from them, and what you should avoid repeating when you play.**

The creator is deliberately presented as another student in the community, not as a master speaking down to beginners.

## 1.1 The differentiation

Most chess social content speaks from authority:

```text
"The best move here is Nf6."
"This gambit is winning."
"Never play this opening."
```

This project should sound different:

```text
"2 mistakes and I got checkmated."
"I thought this move was safe. It wasn't."
"I completely missed this attack."
"This is what I learned from this game."
"If you reach this position, don't repeat what I did."
"What would you have played here?"
```

## 1.2 Community identity

The intended community identity is:

```text
I play.
I make mistakes.
We analyze them.
We learn together.
Next game, we try not to repeat them.
```

The creator should be visibly inside the learning journey.

The audience should feel like a group improving together, not like students watching another guru.

## 1.3 Copy rules

Every hook, caption, voice script, description, CTA, and comment prompt should follow these rules:

- Never claim expertise the creator does not have.
- Lead with a real mistake, discovery, confusion, or learning moment.
- Frame lessons as shared learning or avoidance, not authority.
- Prefer "I missed this" over "you should know this".
- Prefer "what would you play?" over "here is the answer".
- Explain what the move cost the creator.
- Use first-person language for personal gameplay.
- Every chess claim must trace to verified moves plus engine output.
- AI wording may explain facts, but AI opinion may never become a chess fact.

## 1.4 House content format

The strongest recurring format is:

```text
my real game
→ my mistake
→ viewer gets the position as a puzzle
→ "can you see what I missed?"
→ reveal
→ show the better move
→ explain what I learned
→ ask the community what they would play
```

This turns the creator's own mistake into the viewer's puzzle.

## 1.5 Example hooks

```text
"2 mistakes and I got mated."
"I thought this move was completely safe."
"This one move ruined my position."
"I saw the attack too late."
"I learned this the hard way today."
"I missed this move. Can you find it?"
"I was fine here... then I played this."
"The engine showed me what I completely missed."
```

## 1.6 Business direction

The goal is to build an original chess media brand that can eventually become a business.

Possible long-term path:

```text
real learning journey
→ consistent short-form content
→ learning community
→ free puzzle / mistake resource
→ email, Telegram, or Discord community
→ paid puzzle workbook / digital product
→ beginner resources
→ course only after genuine experience and audience demand
→ sponsorships / affiliates / merchandise later
```

The project should not build monetization infrastructure before proving that people want the content format.

---

# 2. Mascot System — The 10 Generated Images and How to Use Them

The mascot is a **fellow chess student**, not a chess teacher.

The character should react with the creator and viewer: confused when a tactic is missed, shocked by a blunder, happy when a good move appears, thoughtful before a puzzle reveal, and welcoming when asking the community to participate.

The generated mascot concepts are intended as a **reusable reaction library**, not as ten unrelated images.

## 2.1 Important commercial rule

Do not publish a copied third-party cartoon character.

The original Pinterest-style red-haired character was used only as visual inspiration for energy, glasses, expressiveness, and peeking poses.

Published output must use an original, commercially safe mascot identity.

The chosen mascot should stay visually consistent across every asset:

- same face proportions;
- same hair design;
- same glasses;
- same eye color;
- same hoodie/outfit;
- same chess emblem;
- same rendering style;
- only pose/expression changes.

## 2.2 The ten mascot states

The ten generated concepts should be standardized into these production assets:

| # | Asset name | Mood / role | Typical use |
|---|---|---|---|
| 01 | `mascot_intro_peek` | curious / friendly | hook, opening, "look at this" |
| 02 | `mascot_confused` | confused / uncertain | "what did I miss?" / questionable move |
| 03 | `mascot_good_move` | happy / thumbs-up | good move, recovery, correct idea |
| 04 | `mascot_shocked` | shocked / surprised | blunder, mate threat, sudden tactic |
| 05 | `mascot_thinking` | analytical / thoughtful | puzzle pause, candidate move, "can you see it?" |
| 06 | `mascot_explain` | pointing / speech bubble | short lesson or explanation |
| 07 | `mascot_celebrate` | fist-up / excited | best move, tactic found, successful recovery |
| 08 | `mascot_shh` | secret / hidden trick | small tactical trick, "watch this square" |
| 09 | `mascot_facepalm` | embarrassed / regret | personal mistake, missed tactic, blunder review |
| 10 | `mascot_outro_wave` | friendly goodbye | CTA, comments prompt, outro / vanish |

## 2.3 Do not leave the mascot on screen for the entire video

The mascot should appear only when it adds meaning.

Recommended pattern:

```text
chess continues
→ important event happens
→ mascot pops in
→ reacts / speaks
→ speech bubble appears
→ mascot exits
→ board becomes primary again
```

The board remains the main information surface.

The mascot is a reaction and narration layer.

## 2.4 Recommended use in one Short

Example structure:

```text
0–2s
mascot_intro_peek
"2 mistakes and I got mated."

2–8s
board only
show setup

8–11s
mascot_facepalm or mascot_shocked
"Yeah... I missed that."

11–18s
board explanation

18–21s
mascot_good_move
"This was the move I needed."

21–29s
board continuation / tactical reveal

29–33s
mascot_explain
"Next game, I'm watching this square."

33–36s
mascot_outro_wave
"What would you have played?"
```

This is an example scene design, not a fixed duration rule. Actual timing should follow narration and analytics.

## 2.5 How to animate the still images

Do **not** simply place the PNG on the screen and leave it static.

Each mascot state should be animated by the deterministic renderer.

Example popup animation:

```text
0.00s   character fully outside frame
0.15s   starts sliding into frame
0.30s   reaches target with slight overshoot
0.40s   settles
0.40–2.80s
        gentle idle bob
        optional blink
        speech bubble / narration
        tiny scale breathing motion
2.80s   speech bubble closes
3.00s   mascot begins exit
3.25s   fully outside frame
```

All animation should be driven by renderer frame number, not wall-clock randomness.

## 2.6 Popup directions

Use more than one entry direction so the format does not become repetitive:

```text
right-edge peek
left-edge peek
bottom pop-up
small corner slide
short centered presenter moment
```

Avoid placing the mascot where platform UI covers it or where it hides tactically important squares.

## 2.7 Transparent production assets

The generated concept images currently use normal backgrounds.

For production, the preferred mascot assets are transparent-background PNG/WebP images or cleanly masked sprites.

Target structure:

```text
assets/renderer/mascot/
├── intro_peek.png
├── confused.png
├── good_move.png
├── shocked.png
├── thinking.png
├── explain.png
├── celebrate.png
├── shh.png
├── facepalm.png
└── outro_wave.png
```

Later versions may add alternate left/right variants and mouth shapes.

## 2.8 PNG animation vs 5-second AI video clips

The project should use a hybrid approach.

### Primary method — renderer-animated transparent sprites

Use transparent mascot images and animate them locally:

- slide in/out;
- overshoot;
- bounce;
- blink;
- subtle scale changes;
- speech bubbles;
- mouth swaps;
- motion blur during entry/exit.

This is preferred because it is deterministic, reusable, cheap, fast, and visually consistent.

### Secondary method — short premium mascot clips

For a few high-value reactions, create reusable 2–5 second transparent/alpha video clips later:

```text
blunder_reaction.mov
celebrate_best.mov
thinking_loop.mov
outro_wave.mov
```

These should be reusable across many posts.

Do not generate a completely new AI mascot video for every Short. That would increase inconsistency and production time.

### Recommended creative mix

Use mostly deterministic sprite animation, with a smaller library of pre-rendered premium reaction clips for important moments.

## 2.9 Mascot event data

Mascot appearances should be data-driven, not manually edited into each export.

Example `render_plan.json` / `script.json` representation:

```json
{
  "mascot_events": [
    {
      "time": 0.0,
      "asset": "intro_peek",
      "side": "right",
      "duration": 3.0,
      "bubble": "2 mistakes and I got mated."
    },
    {
      "time": 8.4,
      "asset": "facepalm",
      "side": "left",
      "duration": 2.5,
      "bubble": "I completely missed this."
    },
    {
      "time": 19.2,
      "asset": "good_move",
      "side": "right",
      "duration": 2.8,
      "bubble": "This was the move I needed."
    },
    {
      "time": 31.0,
      "asset": "outro_wave",
      "side": "right",
      "duration": 3.0,
      "bubble": "What would you play?"
    }
  ]
}
```

The renderer should read these events and automatically load the correct mascot state, animate it, add the bubble, and remove it.

## 2.10 Speech bubble is also the subtitle

The mascot's speech bubble and the narration caption should normally be the same UI element.

Do not place a separate subtitle block that competes with the character and board unless accessibility testing requires it.

Example:

```text
        ┌────────────────────────┐
        │ I thought this was safe │
        │ ...it was not.          │
        └────────────┬───────────┘
                     mascot

               CHESS BOARD
```

This gives the mascot a narrator role without presenting him as an expert.

---

# 3. Professional Video Direction

The videos must not look like static screenshots placed one after another.

The renderer should behave like a small motion-design engine.

## 3.1 Professional layer stack

```text
Layer 6 — speech bubbles / captions
Layer 5 — mascot
Layer 4 — particles / mistake / blunder effects
Layer 3 — arrows / circles / square highlights
Layer 2 — animated chess pieces
Layer 1 — chessboard
Layer 0 — background / framing
```

Audio layers:

```text
owner voice
+ subtle music
+ piece movement sound
+ capture sound
+ blunder impact
+ good-move chime
+ mascot popup sound
```

## 3.2 Chess-piece animation

Pieces should never teleport.

Required motion language:

- slide square-to-square;
- easing in/out;
- subtle settle at destination;
- captured piece shrinks/fades;
- last move squares highlighted;
- optional motion trail for fast tactical sequences;
- deterministic timing from verified move data.

## 3.3 Good move / mistake / blunder effects

### Good move

```text
small green-style pulse
check badge
soft success sound
mascot_good_move if useful
```

### Best move / brilliant moment

```text
stronger pulse
animated arrow
sparkle / glow
positive eval movement
mascot_celebrate
```

### Mistake

```text
warning flash
small camera punch-in
negative eval movement
mascot_confused or mascot_facepalm
```

### Blunder

```text
strong warning flash
board shake
impact sound
eval bar collapses
mascot_shocked
```

Colors and exact thresholds belong to the renderer/analysis design files and must remain configurable.

## 3.4 Tactical freeze beat

Before revealing a key tactic:

```text
board freezes
screen slightly dims
important square may glow
mascot_thinking appears briefly
bubble: "Can you see what I missed?"
short pause
→ reveal move
```

The pause creates a participation moment instead of turning the video into passive explanation.

## 3.5 Original identity only

Duolingo can inspire interaction patterns such as:

```text
character reaction
speech bubble
small gamified effect
clear mistake / success feedback
```

But published output must not copy Duolingo's character, exact interface, copyrighted art, or app UI.

Chess Content OS needs its own board, pieces, mascot, motion language, and visual identity.

---

# 4. Recommended Short Structure

A common structure may look like this:

```text
HOOK
→ position setup
→ my move
→ freeze / viewer challenge
→ opponent punishment
→ better alternative
→ what I learned
→ community CTA
```

Example narrative:

```text
"2 mistakes and I got mated."

"I thought this was safe."

"Can you see what I missed?"

[reveal]

"This was the move I needed instead."

"The lesson for me: watch this diagonal before pushing the pawn."

"What would you have played here?"
```

Do not hard-code one duration for every Short. Narration and measured retention should determine pacing.

---

# 5. System Architecture

The project intentionally separates chess truth from creative generation.

```text
INPUTS
screen recording / PGN / puzzle source
        ↓
Chess Video Preprocessor
FFmpeg / OpenCV
board crop + evidence
        ↓
Board Perception
local templates / scanner
        ↓
Observed piece-placement states
        ↓
Move Candidate Reconstruction
python-chess legality / legal bridge search
        ↓
Ambiguity Audit
unique vs multiple legal paths
        ↓
Visual Evidence
local temporal scoring
+ constrained VLM support where useful
        ↓
Human confirmation when required
        ↓
VERIFIED moves.json
        ↓
Stockfish analysis
        ↓
analysis.json
        ↓
Moment Selector
        ↓
Script Generator
        ↓
Voice / alignment
        ↓
Professional Motion Renderer
board + effects + mascot + bubble
        ↓
Validators
        ↓
Human approval
        ↓
Publisher
        ↓
Analytics
        ↓
Idea Engine
```

Two loops must remain separate:

```text
TRUTH LOOP
pixels → observed state → candidate paths → legality → ambiguity → evidence → human confirmation

CONTENT LOOP
verified data → engine facts → scene → script → render → evaluate → approve → publish
```

A better script cannot repair an unverified chess sequence.

---

# 6. Truth Layer — Current Technical State

## 6.1 Local environment

Current prototype environment:

- macOS on Apple Silicon / MacBook M4;
- uv-managed Python 3.11.15;
- FFmpeg 8.1.1;
- ImageMagick;
- `python-chess`;
- `opencv-python-headless`;
- `google-genai`;
- `python-dotenv`.

The system Python should not be replaced.

## 6.2 Prototype source recording

Prototype recording:

```text
<MoneyPrinterTurbo>/storage/local_videos/
material-3cc02343e1b64dbeb464b7127ad0187b.mov
```

Observed properties during development:

```text
duration ≈ 41.40 s
resolution = 1320 × 2868
frame rate ≈ 60 FPS
codec = HEVC/H.265
ReplayKit recording
audio present
```

## 6.3 Board calibration

At the calibration position around 10 seconds:

```text
board width = 1320 px
board height = 1320 px
square = 165 px
board top ≈ 962 px
orientation = Black perspective / 180° rotation
```

V2 RGB + mask templates live under:

```text
assets/templates/duolingo_v2/
```

The calibrated piece-placement FEN was:

```text
r1bqr1k1/pp3ppp/2n2n2/3pN3/3P4/1BB5/PPPQ1PPP/R3K2R
```

This is piece placement only, not complete FEN metadata.

## 6.4 Rapid replay region

The difficult rapid replay section is approximately:

```text
13.50s → 19.50s
```

The state scanner successfully produced observed piece-placement states through this section.

## 6.5 Legal move reconstruction

The multi-ply legal bridge search found a 36-ply candidate chain that reaches all observed states.

Current candidate chain:

```text
01 White Bxd5  b3d5
02 Black Nxc3  e4c3
03 White bxc3  b2c3
04 Black Be6   c8e6
05 White Bxb7  d5b7
06 Black Rab8  a8b8
07 White Bd5   b7d5
08 Black Bxd5  e6d5
09 White Rxd5  d1d5
10 Black f6    f7f6
11 White Re1   h1e1
12 Black fxe5  f6e5
13 White Rdxe5 d5e5
14 Black Rxe5  e8e5
15 White Rxe5  e1e5
16 Black Rf8   b8f8
17 White f4    f2f4
18 Black Rxf4  f8f4
19 White c4    c3c4
20 Black Rf2   f4f2
21 White c5    c4c5
22 Black Rf6   f2f6
23 White g4    g2g4
24 Black Re6   f6e6
25 White Rh5   e5h5
26 Black Rc6   e6c6
27 White Re5   h5e5
28 Black Kh8   g8h8
29 White h4    h2h4
30 Black Kg8   h8g8
31 White Re8+  e5e8
32 Black Kf7   g8f7
33 White Re5   e8e5
34 Black Kg8   f7g8
35 White g5    g4g5
36 Black Kf7   g8f7
```

Coverage of observed states does **not** prove every ambiguous path is the actual path shown in the recording.

## 6.6 Ambiguity audit

The existing audit found:

```text
14 unique bridges
5 ambiguous bridges
Bridge 10 locally resolved
Bridges 16–19 partially or fully ambiguous under current local scorers
```

Bridge 10 became the control case.

Its competing paths were:

```text
A: Rdxe5 → Rxe5 → Rxe5
B: Rexe5 → Rxe5 → Rxe5
```

Local departure evidence selected the rook from `d5` first.

## 6.7 Local visual probes

Several experimental workers were created and intentionally preserved:

```text
duolingo_state_sequence_probe.py
duolingo_move_chain_probe.py
duolingo_multi_ply_probe.py
duolingo_path_ambiguity_probe.py
duolingo_visual_ambiguity_probe.py
duolingo_departure_probe.py
duolingo_departure_audit.py
duolingo_path_frame_score.py
video_evidence_builder.py
```

Experiments should not be silently overwritten or deleted.

---

# 7. Gemini / VLM Findings

## 7.1 Two-key fallback

Two Gemini key labels are configured through environment variables.

Secrets must never appear in documentation, source code, logs, commits, or prompts.

A provider fallback client exists so a second credential can be attempted after a failed provider request.

## 7.2 Whole-video experiment failed as chess truth

A board-only rapid clip was created and then slowed for Gemini analysis.

The whole-video Gemini probe returned many confident moves, but the result contained major conflicts with the legal reconstruction and even same-side consecutive moves.

Therefore:

> Open-ended Gemini video reading is rejected as an authority on chess move truth.

## 7.3 Evidence-image approach

The architecture was narrowed to small chronological evidence packs.

Instead of asking:

```text
"What moves happened in this video?"
```

ask narrow visual questions such as:

```text
"Which rook visibly leaves first: d5 or e1?"
```

`python-chess` still owns legality.

## 7.4 Bridge 10 control

A seven-image chronological Bridge 10 control pack was created.

An unlabeled inline-image Gemini probe identified:

```text
first source square: d5
confidence: high
```

This agreed with the independently resolved local evidence.

This proves constrained VLM evidence can be useful as **secondary visual evidence on at least one control case**.

It does not make Gemini a certifier of chess truth.

## 7.5 Current recommendation

Do not spend unlimited development time algorithmically resolving the late ambiguous endgame bridges if they are not needed in the first publishable Short.

For the MVP:

```text
unique deterministic result
→ accept

ambiguous but locally resolved with adequate evidence
→ record evidence

ambiguous and still uncertain
→ human confirmation

VLM support
→ optional evidence only
```

---

# 8. `moves.json` — The Contract Seam

Everything downstream should consume a verified structured move file.

The renderer, Stockfish analyzer, script generator, and publisher must never need to inspect raw phone pixels.

## 8.1 Recommended truth model

A model-supported candidate alone must not count as final verification.

Prefer separate status and provenance concepts.

Example:

```json
{
  "uci": "d5e5",
  "san": "Rdxe5",
  "verification_status": "verified",
  "verification_basis": [
    "legal_path",
    "local_visual",
    "human_confirmed"
  ],
  "model_support": {
    "provider": "gemini",
    "supported": true
  }
}
```

Recommended renderer gate:

```text
verified by deterministic evidence
OR human_confirmed
        ↓
renderer allowed

VLM support alone
        ↓
renderer not allowed
```

## 8.2 UCI should be canonical

Store UCI as the canonical move representation.

Derive SAN from the legal board with `python-chess` and assert any stored SAN matches the derived value.

This prevents silent disagreement between UCI and SAN.

## 8.3 Provenance for inferred metadata

Do not mix observed board facts with inferred metadata without provenance.

Example:

```json
{
  "piece_placement": {
    "value": "...",
    "provenance": "observed"
  },
  "side_to_move": {
    "value": "w",
    "provenance": "inferred"
  },
  "castling_rights": {
    "value": null,
    "provenance": "unknown"
  }
}
```

---

# 9. Stockfish and Analysis Layer

Stockfish should analyze verified `moves.json` only.

Output should go to a separate `analysis.json`.

Engine analysis must never mutate move truth.

Useful output per move:

```text
evaluation before
evaluation after
best move
principal variation / refutation
move-quality label
owner mistake severity
```

Any move-quality thresholds should be explicitly sourced or labelled as project heuristics and configurable.

Do not present unsourced thresholds as an official Lichess methodology.

---

# 10. Moment Selection

The first content selector should prefer the owner's most useful learning moment, not simply the flashiest tactic.

Strong candidates:

- largest owner evaluation drop;
- move that causes a clear tactical punishment;
- mistake with a simple reusable pattern;
- moment that can be explained honestly in a short narration;
- position that can become a viewer puzzle.

Scene output should include a small amount of setup, the mistake, punishment, alternative, and lesson.

---

# 11. Script and Voice

## 11.1 Script structure

A useful four-beat learner script:

```text
1. what I played / thought
2. what it cost me
3. what I should have noticed or played instead
4. what I learned / viewer question
```

## 11.2 Personal voice

First-person personal-game content should use the owner's real recorded voice when practical.

Synthetic voice is more appropriate for non-personal content lanes such as general puzzle content.

The renderer timeline should follow actual narration length rather than forcing narration into a fixed-duration template.

---

# 12. Professional Motion Renderer

The deterministic renderer should be understood as a **professional motion-design engine**, not a plain chess simulation.

Deterministic means the same verified data and assets produce the same frames.

It does not mean the video must look simple.

Supported visual polish can include:

- piece easing;
- captures;
- arrows;
- circles;
- square glows;
- camera push-ins;
- screen dimming;
- board shake;
- particles;
- eval-bar movement;
- move-quality badges;
- mascot entry/exit;
- speech bubbles;
- audio-reactive mouth swaps;
- subtitles;
- sound effects.

---

# 13. Repositories Researched and What to Reuse

## 13.1 `deepseek-ai/deepseek-harness`

Use as an architecture reference for swappable providers and plugin/capability seams.

Do not migrate Chess Content OS into it just to use an agent framework.

Project lesson:

```text
VideoUnderstandingProvider
→ Gemini implementation now
→ another provider later without changing callers
```

## 13.2 `sahansbandara/youtube-automation-agent`

Useful patterns:

- provider fallback;
- publishing;
- scheduling;
- YouTube OAuth;
- analytics.

It is not a chess video-understanding solution.

## 13.3 `jtig37/free-llm-api-resources`

Use only for provider discovery.

Do not use it as current pricing, model, or quota truth because provider information changes quickly.

## 13.4 `aimh-lab/visione`

Useful architectural idea:

```text
video
→ temporal preprocessing
→ scene / shot evidence
→ keyframes / visual features
```

Chess Content OS adapts this idea into chess micro-shots / evidence windows.

Do not install the full VISIONE stack for the MacBook MVP.

## 13.5 `wink-wink-wink555/blind_navigation`

Useful lesson:

```text
deterministic frame perception
→ event detection
→ LLM explanation
```

The LLM should not replace deterministic visual/geometry logic.

## 13.6 MoneyPrinterTurbo

MoneyPrinterTurbo can be a future creative-video worker.

It should not edit or reconstruct exact chess gameplay because its generic clip logic already proved unsuitable for preserving move truth.

---

# 14. MCP, Skills, and Agent Strategy

The project uses the following agent-system model:

```text
model
+ instructions
+ context
+ tools
+ memory
+ workflow
+ evaluation
+ permissions
```

## 14.1 Tool priority

Prefer:

```text
direct local library / API
→ MCP when it removes repeated integration work
→ browser automation only when no stable API exists
→ computer-use style interaction only as a last resort
```

Do not build MCP servers merely to make the project look agentic.

## 14.2 Skills

Skills should encode workflows that have already been proven.

Potential skill structure:

```text
skills/
├── chess-content/
├── chess-video-editing/
├── chess-video-reading/
├── chess-puzzle-content/
├── motion/
├── platform-metadata/
└── content-evaluator/
```

A skill should define:

- when to use it;
- inputs;
- exact procedure;
- validations;
- expected output;
- stop conditions;
- examples;
- failure modes.

Do not formalize a workflow as a skill while its steps are still changing every experiment.

---

# 15. Agent Memory and End-of-Session Workflow

The repo already treats agent files as project memory.

Agents should read the project rules and current state before coding.

Canonical context includes:

```text
AGENTS.md
CLAUDE.md
Agent/BRIEF.md
Agent/TODO.md
Agent/MEMORY.md
Agent/DECISIONS.md
design.md
docs/PLAN.md
docs/PROJECT_MASTER_CONTEXT.md
```

## 15.1 End of every meaningful coding session

The coding agent should:

```text
1. review what changed
2. update Agent/TODO.md
3. update Agent/MEMORY.md if durable knowledge changed
4. update Agent/DECISIONS.md if an architecture decision changed
5. update design/plan/docs if the implementation changes them
6. update changelog when appropriate
7. run tests / validation
8. check that no secret is staged
9. review diff
10. commit using a conventional commit
11. use the repository's safe git-sync workflow to push and fast-forward main
```

No force-push.

No secrets.

No silent destructive cleanup of experiments.

Automatic documentation sync should describe what actually happened, not fabricate progress.

---

# 16. Human Approval and Publishing

Publishing remains human-approved.

Target future workflow:

```text
recording enters inbox
→ pipeline builds draft
→ move uncertainty confirmation if needed
→ final render
→ Telegram approval message
→ approve / reject / revise
→ publisher
```

A kill switch must disable all outward publishing while leaving local generation usable.

The first videos should be posted manually before OAuth/cron automation is built.

---

# 17. Analytics and Idea Engine

The system eventually records performance and uses it to propose future content.

Possible stored metrics:

```text
views
likes
comments
shares
retention / completion when available
hook type
mistake type
video length
CTA type
content source
```

The idea engine should propose future posts from measured performance rather than generic trend claims.

High-performing examples may later become benchmark examples inside reusable skills/evaluators.

---

# 18. Future Content Lanes

The renderer should not depend permanently on Duolingo screen recordings.

Possible sources:

```text
own gameplay recordings
PGN files
Lichess games
puzzle databases
manually entered positions
future original chess source integrations
```

A puzzle/PGN lane can feed verified move data directly and skip the entire phone-screen perception layer.

That is important for scaling content volume.

---

# 19. What Not to Do

Do not:

- pretend the creator is a chess master;
- copy a third-party mascot;
- copy Duolingo's UI into monetized output;
- let Gemini invent the move sequence;
- choose the first BFS candidate because it appears first;
- treat model confidence as verification;
- render unresolved moves as if they were certain;
- build a static chess slideshow and call it the final product;
- keep the mascot permanently on screen;
- generate a completely new inconsistent mascot animation for every post;
- build Telegram/publishing before one good manual video exists;
- build MCP/framework infrastructure just to look sophisticated;
- delete failed experiments without approval;
- commit `.env`, API keys, credentials, or private tokens;
- automate public posting without human approval.

---

# 20. Recommended Build Order From Here

The shortest path to a real product is now:

```text
1. Freeze moves.json v1 contract
2. Build moves validator
3. Add quick human confirmation for unresolved bridges
4. Install / wire Stockfish
5. Produce analysis.json
6. Select one strong learning moment
7. Write/generate learner-style script
8. Record first voice
9. Build professional board renderer
10. Build first mascot popup component
11. Add speech bubble / subtitle
12. Add move-quality effects + sound
13. Mux final 1080×1920 video
14. Review on phone
15. Publish manually
16. Repeat manually until format is proven
17. Build evaluator
18. Build Telegram approval
19. Build official publisher
20. Add analytics / idea engine
```

The first mascot implementation should be only one reusable component:

```text
right-side intro peek
→ slide in
→ speech bubble
→ stay briefly
→ bubble closes
→ slide out
```

Once that works inside a real Short, reuse the same component for the other nine mascot states.

---

# 21. Phase Acceptance Criteria

## Phase A — Truth contract

Done when:

- verified `moves.json` exists;
- sequence is legal;
- no unresolved move reaches downstream consumers;
- UCI/SAN consistency is validated;
- uncertain metadata has provenance.

## Phase B — First finished Short

Done when:

- one useful owner mistake is selected;
- board animation looks professional;
- voice and speech bubbles are readable;
- at least one mascot popup works naturally;
- move-quality visual treatment works;
- final output is 1080×1920;
- the owner is willing to publish it manually.

## Phase C — Repeatable content

Done when several posts can be created without redesigning the system each time.

## Phase D — Automation

Done when human approval can trigger publishing safely and idempotently.

---

# 22. Risks and Kill Criteria

## 22.1 Perception research rabbit hole

Risk: endless CV/VLM experiments delay the audience-facing product.

Kill criterion:

> If a late ambiguous bridge is not needed for the selected Short, use human confirmation and move on.

## 22.2 Mascot polish rabbit hole

Risk: spending weeks on character art before proving the video format.

Kill criterion:

> Build one popup asset and one final video before expanding the entire mascot animation library.

## 22.3 Visual clutter

Risk: mascot/effects hide the board.

Kill criterion:

> If a viewer cannot immediately understand the chess position, reduce character size, duration, or visual effects.

## 22.4 AI truth failure

Risk: confident but wrong chess claims.

Kill criterion:

> No move or engine claim reaches copy/rendering without deterministic validation or explicit human confirmation.

## 22.5 Automation before product validation

Risk: automating a format nobody wants.

Kill criterion:

> Do not build the full publishing loop until at least one manual video is genuinely worth posting.

---

# 23. Definition of the Product

Chess Content OS succeeds when the system can repeatedly turn a real chess learning moment into content that feels like this:

```text
"I made this mistake.
I didn't see the tactic.
Here's what happened.
Here's what I learned.
Can you find the better move before I reveal it?
Let's improve together."
```

And visually feels like this:

```text
professional animated chessboard
+ verified move truth
+ meaningful highlights and effects
+ original student mascot
+ speech-bubble narration
+ personal voice
+ viewer participation
+ human approval
```

The competitive advantage is not that the system knows more chess than every guru.

The advantage is that it turns a real learner's journey into a consistent, trustworthy, interactive media product.
