# Chess Content OS — Project Brief

> Status: Active development
> Last updated: 2026-08-19
> Repository root: `/Users/sahansandaruwan/Dev/chess-content-os`
> This file replaces the generic project-template content with the current Chess Content OS project context.

## Project type

AI-assisted, human-approved social content automation system for chess gameplay, puzzles, educational shorts, and future chess media workflows.

## Goal

Build a reusable system that can turn raw chess inputs into accurate, polished, platform-ready social content with minimal manual editing.

The first input source is Duolingo Chess screen recordings. The system should recover the actual chess moves, validate them deterministically, rebuild a clean chess animation, add an AI-written language layer, send the result for human approval, publish it to social platforms, record performance, and use those results to improve future content.

The long-term goal is not a single video generator. It is a small content operating system with reusable agents, skills, validators, provider fallbacks, approval gates, publishing tools, and feedback loops.

## Business / content purpose

The content positioning is:

> Learning chess in public — these are the mistakes I made, so you don't have to.

The creator is explicitly a **learner, not a teacher**. This is the project's differentiator and it governs every generated caption:

```text
Everyone else:  "The best move here is Nf6, and this gambit refutes it."
This channel:   "2 mistakes and I got mated in 11. Don't do what I did."
```

Copy rules that follow from it:

- Never claim expertise the creator does not have.
- Lead with the creator's own mistake and what it cost.
- Frame the lesson as avoidance ("don't do this"), not instruction ("you should").
- Ask rather than lecture: "what would you have played?" beats "here is the answer".
- Number the series so viewers follow an improvement arc, not a one-off tip.
- Make the rating journey the spine of the channel.
- Every chess claim traces to verified moves plus engine output, never to model opinion.

**House format:** the creator's own blunder becomes the audience's puzzle — *"I played this position. It's losing. Can you see why?"* This is authentic (a real game), participatory (answers go in the comments, which is what builds a community rather than an audience), and delivers a "can you find it?" hook without claiming authority.

The target is a **learning community** with the creator inside it as a student, not an audience being lectured. Community is built by replying to comments personally; that part is deliberately not automated.

Known constraint on this positioning: it requires the creator to actually keep improving, or the arc goes stale. Playing regularly is therefore part of production, not a hobby alongside it.

Long-term monetization path:

```text
Audience
→ useful free chess content
→ free lead magnet / puzzle resource
→ paid puzzle workbook or digital product
→ beginner course only after sufficient expertise and audience demand
→ optional merch or partnerships later
```

The system is intended to reduce recurring editing workload and make content production sustainable alongside other work and university responsibilities.

## Target users

- Primary: project owner / content operator creating chess content.
- Secondary: future editor, collaborator, or automation operator.
- Admin/operator: project owner with final approval authority.
- Audience: global English-speaking beginner and improving chess players.

## Main problem

A phone screen recording is not directly usable as reliable chess content automation input.

Problems include:

- fast replay sections where several moves happen within a fraction of a second;
- UI elements and phone framing around the chessboard;
- chess-piece recognition errors;
- multiple legal move sequences that can produce the same observed piece-placement state;
- AI vision models producing confident but incorrect chess moves;
- generated-video tools treating gameplay as generic footage rather than preserving exact chess truth;
- repeated manual work for cropping, editing, captions, publishing, and analytics.

The project therefore separates **chess truth** from **creative generation**.

## Main purpose of the architecture

The core rule is:

> Deterministic systems establish chess state and legality. AI helps interpret ambiguous visual evidence and generate language/creative assets, but AI does not become the final authority on move truth.

## Main workflow

```text
RAW INPUT
Duolingo recording / puzzle / future chess source
        ↓
Chess Video Preprocessor
FFmpeg / OpenCV
board crop + timing + evidence extraction
        ↓
Board / Event Perception
local templates + visual state scanner
        ↓
Candidate Move Reconstruction
python-chess legality + shortest legal bridges
        ↓
Ambiguity Detection
unique path vs multiple legal paths
        ↓
Visual Reconciliation
local temporal evidence
+ constrained VLM evidence when useful
        ↓
Verified move sequence
SAN / PGN derived deterministically
        ↓
Chess Analysis
Stockfish later for evaluation, tactics, mistakes, best moves
        ↓
Clean Chess Renderer
fixed board, pacing, arrows, captions, highlights
        ↓
AI Language Layer
hook + explanation + CTA + platform metadata
        ↓
Evaluator
chess validity + format + content quality
        ↓
Human approval
        ↓
Publisher
YouTube Shorts / Instagram Reels / TikTok / Facebook
        ↓
Results database
        ↓
Analytics + Idea Engine
        ↓
future content improvements
```

## Agent-system architecture

The project follows the reusable-agent model documented in `AI_Agent_Systems_Complete_Guide.md`:

```text
Model
+ instructions
+ context
+ tools
+ memory
+ workflow
+ evaluation
+ permissions
```

Recommended project-level orchestration:

```text
Content Orchestrator
├── Gameplay Worker
├── Puzzle Worker
├── AI Video Worker
├── Chess State / Move Validator
├── Chess Analysis Worker
├── Script / Caption Agent
├── Quality Evaluator
├── Approval Bot
├── Publisher
└── Analytics / Idea Engine
```

## MVP

### Included

- Duolingo Chess screen-recording ingestion.
- Board crop and evidence preparation.
- Piece-placement state scanning.
- Legal move reconstruction with `python-chess`.
- Explicit ambiguity detection instead of silently picking candidate path #1.
- Local visual reconciliation for ambiguous transitions.
- Constrained Gemini visual experiments as a secondary evidence source.
- Verified move output in structured JSON.
- Deterministic clean chess-video rendering.
- AI-generated hook, explanation, CTA, title, caption, hashtags, and platform metadata.
- Human approval before publishing.
- At least one social-platform publishing path after the content pipeline is stable.
- Logging of generated content, approval status, publishing status, and later performance.

### Excluded from the first MVP

- Fully autonomous publishing without human approval.
- Allowing Gemini or another VLM to invent the chess move sequence.
- Full installation of VISIONE.
- Training a new computer-vision model unless template-based recognition proves inadequate across multiple recordings.
- Building a large web dashboard before the core content pipeline is proven.
- Merchandise, course platform, or advanced monetization automation.
- Migrating the project to a large agent framework before the local Python workflow works end-to-end.

## Current technical state

### Local environment

- macOS on Apple Silicon MacBook M4.
- Project: `/Users/sahansandaruwan/Dev/chess-content-os`.
- Project Python: uv-managed Python 3.11.15.
- System Python is intentionally not replaced.
- FFmpeg 8.1.1 installed.
- ImageMagick installed.
- `python-chess` installed.
- `opencv-python-headless` installed and `cv2` verified.
- `google-genai` installed.
- `python-dotenv` installed.

### Existing project structure

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

### Source recording used for the prototype

```text
/Users/sahansandaruwan/Dev/MoneyPrinterTurbo/storage/local_videos/
material-3cc02343e1b64dbeb464b7127ad0187b.mov
```

Observed recording properties during the current project session:

- approximately 41.40 seconds;
- 1320 × 2868;
- approximately 60 FPS;
- HEVC/H.265;
- ReplayKit recording;
- audio present.

### Board calibration

At the calibration point around 10 seconds:

- board width: 1320 px;
- board height: 1320 px;
- square size: 165 px;
- board top: approximately 962 px;
- orientation: Black perspective / board rotated 180 degrees.

The V2 template system stores RGB and mask information in:

```text
assets/templates/duolingo_v2/
```

### Calibrated board scan

The V2 full-board scanner produced the following piece-placement FEN at the calibration position:

```text
r1bqr1k1/pp3ppp/2n2n2/3pN3/3P4/1BB5/PPPQ1PPP/R3K2R
```

This is **piece placement only**, not a complete FEN. Side-to-move, castling rights, en-passant square, halfmove clock, and fullmove number are not available from a single screenshot.

### Rapid replay state reconstruction

The difficult replay section is approximately:

```text
13.50s → 19.50s
```

A state-sequence probe sampled observed board states and a legal bridge search recovered a complete path through the observed sequence.

The current 36-move candidate chain is:

```text
01  White  Bxd5    b3d5
02  Black  Nxc3    e4c3
03  White  bxc3    b2c3
04  Black  Be6     c8e6
05  White  Bxb7    d5b7
06  Black  Rab8    a8b8
07  White  Bd5     b7d5
08  Black  Bxd5    e6d5
09  White  Rxd5    d1d5
10  Black  f6      f7f6
11  White  Re1     h1e1
12  Black  fxe5    f6e5
13  White  Rdxe5   d5e5
14  Black  Rxe5    e8e5
15  White  Rxe5    e1e5
16  Black  Rf8     b8f8
17  White  f4      f2f4
18  Black  Rxf4    f8f4
19  White  c4      c3c4
20  Black  Rf2     f4f2
21  White  c5      c4c5
22  Black  Rf6     f2f6
23  White  g4      g2g4
24  Black  Re6     f6e6
25  White  Rh5     e5h5
26  Black  Rc6     e6c6
27  White  Re5     h5e5
28  Black  Kh8     g8h8
29  White  h4      h2h4
30  Black  Kg8     h8g8
31  White  Re8+    e5e8
32  Black  Kf7     g8f7
33  White  Re5     e8e5
34  Black  Kg8     f7g8
35  White  g5      g4g5
36  Black  Kf7     g8f7
```

This chain reaches all currently observed piece-placement states, but coverage does not prove that every ambiguous bridge uses the exact visual path shown by the replay.

### Ambiguity audit

The current ambiguity model found:

- 14 unique bridges;
- 5 ambiguous bridges;
- Bridge 10 was resolved locally;
- Bridges 16–19 remain partially or fully ambiguous under the current local visual scorers.

Bridge 10 control candidates were:

```text
A: Rdxe5 → Rxe5 → Rxe5
B: Rexe5 → Rxe5 → Rxe5
```

Local temporal evidence selected candidate A. This bridge is now used as a falsification/control case for any new visual method.

### Gemini experiment

A board-only rapid clip was created:

```text
output/evidence_test/rapid_board.mp4
```

A dense evidence builder exported 72 timestamped frames at the prototype sampling rate of 12 FPS.

A slowed analysis video was created from those frames:

```text
output/evidence_test/rapid_board_gemini.mp4
```

Observed output properties:

- 72 frames;
- approximately 71.083333 seconds.

Two Gemini API keys are configured in `.env` under separate variable names. Secrets must never be committed or copied into project documentation.

A provider fallback client exists at:

```text
src/providers/gemini_client.py
```

During the live key test:

- the key labeled `BACKUP` successfully returned `OK`;
- the key labeled `PRIMARY` produced a server-side failure in that test;
- the working key is currently attempted first by the fallback client.

A full-video Gemini chess-reading probe was then tested. Gemini returned 25 high-confidence moves, but the sequence conflicted heavily with the legal reconstruction and even contained same-side consecutive moves. Therefore the project explicitly rejects open-ended whole-video Gemini extraction as a source of chess truth.

Current Gemini use case is narrowed to **candidate-constrained visual comparison** on small evidence packs, beginning with Bridge 10 as the known control.

## Core features

1. Chess source ingestion.
2. Board ROI extraction and calibration.
3. Piece template management.
4. Full-board state recognition.
5. Temporal state sequence extraction.
6. Legal move / path search with `python-chess`.
7. Ambiguity detection.
8. Local visual scoring and evidence packs.
9. Optional VLM candidate comparison.
10. Stockfish analysis.
11. Clean deterministic chess animation.
12. AI copywriting and platform metadata.
13. Quality evaluation.
14. Human approval.
15. Publishing.
16. Analytics and content feedback loop.

## Pages / screens / flows

The MVP is CLI-first. A web UI is not required yet.

| Page or flow | Purpose | User role |
|---|---|---|
| Inbox / CLI ingestion | Add a recording or puzzle | Operator |
| Evidence review | Inspect board crop / ambiguous transitions | Operator |
| Generated preview | Review final short before publishing | Operator |
| Telegram approval flow | Approve / reject / request revision | Admin/operator |
| Analytics dashboard | Later: compare performance across posts | Operator |

## Data model

| Entity | Fields | Relationships | Sensitivity |
|---|---|---|---|
| SourceAsset | id, path, source_type, created_at, metadata | one-to-many EvidenceEvent / ContentItem | Low to medium |
| BoardState | timestamp, piece_placement_fen, confidence, scanner_version | belongs to SourceAsset | Low |
| MoveCandidate | bridge_id, UCI sequence, SAN sequence, path_length, score | belongs to transition | Low |
| EvidenceEvent | timestamps, before/transition/after frames, candidate paths | belongs to SourceAsset | Low |
| VerifiedMove | sequence, UCI, SAN, evidence status | belongs to ContentItem/game | Low |
| ContentItem | hook, script, rendered_path, status, platform metadata | uses SourceAsset / moves | Low |
| Approval | content_id, status, timestamp, reviewer | belongs to ContentItem | Medium |
| Publication | platform, post_id, URL/id, published_at, status | belongs to ContentItem | Medium |
| PerformanceSnapshot | views, likes, comments, shares, retention when available | belongs to Publication | Medium |
| ProviderAttempt | provider, key label only, model, status, error class, latency | belongs to workflow run | Do not log secrets |

## APIs and integrations

| Requirement | Preferred interface | Candidate tool | Fallback | Permission level |
|---|---|---|---|---|
| Chess legality | Local library | python-chess | none | local only |
| Chess engine analysis | Local process | Stockfish | cloud chess API only if needed | local only |
| Video processing | Local CLI | FFmpeg | OpenCV where frame-level work is required | local only |
| Frame/image processing | Python library | OpenCV | Pillow/ImageMagick | local only |
| VLM visual evidence | Direct API | Gemini | another VLM via provider interface later | outbound API |
| AI video generation | Local app/worker | MoneyPrinterTurbo | another generator later | local / provider-dependent |
| Approval | Direct API | Telegram Bot API | local CLI review | outward message |
| Publishing | Official platform APIs | YouTube / Meta / TikTok where available | manual publish | outward-facing; approval required |
| Repository operations | Git CLI / GitHub API | GitHub MCP can be added later | manual Git | code-write permissions |
| Scheduling | local scheduler / automation layer | cron/launchd or agent scheduler | manual trigger | controlled |

## LLM requirements

- LLM required: yes, but not for core chess legality.
- Tasks: visual candidate comparison, hook writing, concise chess explanation after truth is established, CTA, title, description, platform metadata, content evaluation.
- Modality: text + images; video only for experiments where justified.
- Expected requests/day: not fixed yet; measure after MVP.
- Expected tokens/day: not fixed yet; log during pilot.
- Context requirement: source metadata + verified move data + content skill + approved examples.
- Structured output: required for machine-readable stages.
- Tool calling: optional; do not require it for simple generation.
- Languages: English for public content; project files/code in English.
- Latency target: not fixed; reliability is more important than low latency for offline content creation.
- Privacy level: no secrets in prompts/logs; only required source content is sent to external models.
- Free-only policy: prefer free/local during development; paid fallback can be evaluated only after usage/value is measured.
- Reliability target: chess validation must be deterministic; creative text can tolerate model variation.

## MCP and reusable skills strategy

The project uses the concepts from `AI_Agent_Systems_Complete_Guide.md` rather than treating MCP or agent frameworks as goals by themselves.

### Preferred integration order

```text
1. Direct API or local library
2. MCP integration when it provides a reusable standardized tool interface
3. Browser automation
4. Computer Use only when no stable API/tool exists
```

### Why MCP is useful here

Potential future MCP servers can expose:

- GitHub repository operations;
- analytics database queries;
- publishing actions;
- content library search;
- Telegram approval / channel tools;
- Vercel or future dashboard deployment;
- asset storage.

MCP is not required for the first chess-video MVP. The current Python workers should remain directly testable without an agent runtime.

### Skills to build

A skill is a reusable operating procedure, not just a prompt. Each important workflow should eventually have a structure similar to:

```text
skill-name/
├── SKILL.md
├── examples/
├── templates/
├── scripts/
├── validation-rules.md
└── evaluation-rubric.md
```

Recommended project skills:

```text
skills/
├── chess-content/
│   ├── SKILL.md
│   ├── hook-rules.md
│   ├── explanation-rules.md
│   ├── cta-rules.md
│   └── examples/
├── chess-video-editing/
│   ├── SKILL.md
│   ├── pacing-rules.md
│   ├── board-layout.md
│   └── examples/
├── chess-video-reading/
│   ├── SKILL.md
│   ├── evidence-rules.md
│   ├── ambiguity-policy.md
│   └── evaluation-rubric.md
├── chess-puzzle-content/
│   ├── SKILL.md
│   └── examples/
├── platform-metadata/
│   ├── SKILL.md
│   ├── youtube-shorts.md
│   ├── instagram-reels.md
│   ├── tiktok.md
│   └── facebook-reels.md
└── content-evaluator/
    ├── SKILL.md
    └── evaluation-rubric.md
```

The purpose of skills is to prevent the agent from rediscovering the workflow every run and to make successful formats reusable.

## GitHub repositories reviewed for this project

These repositories are references, not dependencies unless explicitly adopted later.

### `deepseek-ai/deepseek-harness`

URL: https://github.com/deepseek-ai/deepseek-harness

How it helps this project:

- demonstrates a plugin-oriented agent harness;
- supports the idea of a swappable provider seam;
- informs a future `VideoUnderstandingProvider` / model-provider interface;
- useful as an architecture reference, not a reason to migrate the current project.

Current decision: borrow the provider/plugin design concept only. Do not replace the working Python pipeline with this harness during the MVP.

### `sahansbandara/youtube-automation-agent`

URL: https://github.com/sahansbandara/youtube-automation-agent

How it helps this project:

- provider fallback patterns;
- publishing and scheduling ideas;
- YouTube OAuth / upload concepts;
- analytics feedback-loop ideas;
- multi-provider configuration patterns.

Current decision: reuse architectural patterns later for publishing/provider abstraction. It is not the chess-video reader.

### `jtig37/free-llm-api-resources`

URL: https://github.com/jtig37/free-llm-api-resources

How it helps this project:

- provider discovery checklist;
- useful for finding candidate low-cost APIs for experiments.

Current decision: discovery only. Do not use the repository as current authority for model names, limits, quotas, or pricing; verify those with provider documentation when needed.

### `aimh-lab/visione`

URL: https://github.com/aimh-lab/visione

How it helps this project:

- video preprocessing before semantic analysis;
- scene/shot thinking;
- keyframe and temporal evidence extraction;
- inspired the project-specific **Chess Micro-Shot** concept.

Adapted concept:

```text
game
↓
move event
↓
chess micro-shot
↓
before / transition / after evidence
```

Current decision: do not install full VISIONE on the MacBook for the MVP. Reimplement only the useful evidence-preparation concepts using FFmpeg/OpenCV.

### `wink-wink-wink555/blind_navigation`

URL: https://github.com/wink-wink-wink555/blind_navigation

How it helps this project:

- demonstrates deterministic frame perception before an LLM;
- demonstrates triggering LLM reasoning only after a local event is detected;
- demonstrates a unified AI-provider seam.

Current decision: adopt the architecture principle, not its YOLO model or domain-specific navigation code.

### `harry0703/MoneyPrinterTurbo`

URL: https://github.com/harry0703/MoneyPrinterTurbo

How it helps this project:

- AI-generated video worker;
- script-to-video experimentation;
- asset-generation ideas.

Current decision: keep as a specialized AI-content/video-generation worker. Do not use it to edit or reconstruct exact chess gameplay because its clip logic does not preserve the required move timing/truth.

## Planned provider architecture

```text
VideoUnderstandingProvider
        │
        ├── GeminiEvidenceReader
        ├── FutureProviderB
        └── FutureLocalModel
```

Provider output should describe **visual observations**, not authoritative chess notation.

Example:

```json
{
  "side": "white",
  "from": "d5",
  "to": "e5",
  "captured_piece_if_visible": null,
  "uncertain": false
}
```

Then `python-chess` validates the observation and derives SAN.

## Auth

- Required for local MVP: no user-account system.
- Gemini credentials: environment variables only.
- Publishing / Telegram credentials: environment variables or secret manager only.
- Roles later: operator and admin/approver.
- Permission rules: generation can be automated; outward publishing and destructive operations require explicit approval until the workflow has a proven safety record.

## Payments

- Required for MVP: no.
- Provider: none.
- Future digital product payments: to be selected only after audience validation.

## Deployment

- Current platform: local MacBook development.
- Production worker target: not selected.
- Domain: none required for CLI MVP.
- Environments: local development first; production only after end-to-end pipeline stabilizes.
- CI/CD: GitHub-based CI can be added after tests exist.
- Environment variables: `.env`; never commit secrets.

## Design direction

- Brand: not finalized.
- Audience: global English-speaking beginner/improving chess players.
- Visual tone: clean, modern, high-contrast, readable on mobile, chessboard-first.
- Colors: not locked.
- Typography: not locked; must prioritize mobile readability.
- Accessibility: captions/subtitles, readable contrast, avoid overloading small screens.

## Evaluation

### Chess truth evaluator

Hard failures:

- illegal move;
- impossible turn order;
- board state does not reconcile with observed state;
- ambiguous transition silently accepted as unique;
- AI-generated move accepted without deterministic validation.

### Content evaluator

Evaluate:

- hook clarity;
- factual/chess correctness;
- beginner readability;
- pacing;
- visual legibility;
- CTA quality;
- originality;
- platform formatting.

### Human approval

Required before publishing during MVP.

## Approval model

| Action | Risk level | Approval required | Rollback |
|---|---|---|---|
| Generate local evidence | Low | No | Delete generated outputs |
| Run local chess validation | Low | No | Re-run |
| Call external VLM with non-sensitive evidence | Low/medium | No per call after provider is configured | Stop provider / remove upload |
| Modify code | Medium | Review via Git | Revert commit |
| Publish social content | Medium/high | Yes during MVP | Delete/unpublish where platform permits |
| Change production credentials | High | Yes | Rotate / restore |
| Delete source assets / database records | High | Yes | Backup required |
| Fully autonomous publishing | High | Not permitted in MVP | N/A |

## Sandbox

- Required: yes for unfamiliar code/repositories and risky automation experiments.
- Reason: isolate dependency and execution risk from the main development environment.
- Selected method: current local project environment for trusted code; consider disposable sandbox/worktree for external repos or major experiments.
- Forbidden access: production secrets, unrelated personal files, live databases unless explicitly required and approved.

## Logging

Log:

- workflow run ID;
- source asset identifier/path;
- scanner version;
- observed board states;
- legal candidates;
- ambiguity status;
- provider/model name;
- key label only, never key value;
- provider error class;
- chosen evidence path and reason;
- rendered output path;
- approval state;
- publication IDs/status;
- later analytics snapshots.

Exclude:

- API keys;
- access tokens;
- private keys;
- passwords;
- unrelated personal data.

## Automation

### Manual workflow tested so far

```text
recording
→ board crop
→ board calibration
→ template scan
→ state sequence
→ legal path reconstruction
→ ambiguity audit
→ local visual scoring
→ Gemini whole-video experiment
```

The last Gemini stage demonstrated why open-ended VLM output must not be trusted as move authority.

### Proposed automated trigger

Initial automation should remain manual/CLI until one end-to-end content item passes all validators.

Later:

```text
new approved source asset in inbox/
→ orchestrator run
→ evidence + moves
→ render + copy
→ evaluator
→ Telegram approval
→ publish
→ analytics
```

### Failure handling

- stop on invalid chess state;
- preserve intermediate evidence;
- mark ambiguous transitions explicitly;
- use provider fallback only for provider/network errors, not to hide bad outputs;
- require human review when validation cannot resolve a conflict;
- never publish partial or failed output.

### Notification

Telegram approval bot is the preferred operator notification/approval surface after the core pipeline is stable.

### Kill switch

A single configuration flag should disable all outward publishing. Publishing credentials should not be required for local generation/testing.

## Acceptance criteria

- [ ] One raw Duolingo recording can be processed end-to-end.
- [x] Board-only crop generated correctly for the current prototype recording.
- [x] V2 board scanner reconstructs the calibration position visually correctly.
- [x] Legal bridge search can reconcile the current rapid sequence to all observed states.
- [x] Ambiguity is surfaced instead of silently hidden.
- [x] Bridge 10 local visual control is resolved to the d5-rook path.
- [x] Gemini provider credentials/fallback plumbing has been tested with one working key.
- [x] Whole-video Gemini extraction has been tested and rejected as chess authority.
- [x] Candidate-constrained multi-image Gemini passes the Bridge 10 control (2026-08-19; single trial, needs repeat + shuffled-frame validation).
- [ ] Remaining ambiguous bridges are resolved or explicitly marked unresolved.
- [ ] Verified move sequence is exported to stable `moves.json` format.
- [ ] Stockfish analysis is added after move truth is established.
- [ ] Clean deterministic chess renderer works from verified moves.
- [ ] Chess content skill produces hook/explanation/CTA from verified chess data.
- [ ] Evaluator rejects illegal/inconsistent content.
- [ ] Human approval flow works.
- [ ] At least one platform publishing workflow works.
- [ ] Analytics are stored after publish.
- [ ] No secrets exposed in Git or logs.
- [ ] Fallback behavior is defined and tested.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Template classifier misreads a piece | Wrong move reconstruction | legality checks + calibration controls + ambiguity flagging |
| Same piece-placement state can have multiple legal paths | False certainty | enumerate shortest legal paths and require temporal evidence |
| VLM confidently hallucinates moves | Incorrect public chess content | VLM never becomes final authority; constrain to candidate comparison |
| Fast replay hides transitions | Missing evidence | dense local sampling / micro-shot evidence packs |
| MoneyPrinterTurbo changes exact gameplay | Incorrect chess sequence | use only as separate creative video worker |
| API quota/provider failure | Workflow interruption | provider seam + fallback key/provider + local validators |
| Same-project API keys share quota | Backup does not solve quota exhaustion | treat keys as credential redundancy; add provider-level fallback later |
| Overbuilding agent infrastructure | Delays content MVP | keep CLI-first and adopt frameworks only after end-to-end proof |
| Automated publishing sends bad content | Reputation damage | human approval and kill switch |
| Copyright/platform-policy issues | Account risk | use own gameplay or properly licensed/allowed source material |

## Open questions

1. ~~Can candidate-constrained multi-image Gemini correctly select the known Bridge 10 path?~~ **Answered 2026-08-19: yes, on one trial.** Open follow-up: does it still pass when frames are shuffled or reversed, and across repeat runs?
2. Can the remaining ambiguous bridges be resolved reliably with local evidence + constrained VLM, or is a stronger piece/motion model required?
3. What stable `moves.json` schema should become the contract between move extraction, Stockfish analysis, rendering, and content generation?
4. Which deterministic board renderer should be used for the final social video style?
5. Which platform should be automated first after human approval: YouTube Shorts, Instagram Reels, TikTok, or Facebook Reels?
6. What analytics fields are actually available from the selected platform APIs?
7. When should a custom MCP server become worth building instead of direct APIs?

## Evidence / research notes

Project design also incorporates the principles documented in `AI_Agent_Systems_Complete_Guide.md`: reusable skills, direct APIs before UI automation, evaluator loops, permission boundaries, human approval, and a clear separation between tools and agent reasoning.

Repository observations in this brief were gathered during the project research session and should be re-verified against current upstream documentation before adding any repository as a production dependency.
