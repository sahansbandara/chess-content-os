# Chess Content OS — TODO

> Last updated: 2026-08-19
> This file replaces the generic template task list with the actual Chess Content OS roadmap.

## Current milestone

**Milestone: produce one postable short from the existing recording, by hand.**

The truth layer is ~70% built and accounts for all 10,233 lines of code so far. Nothing the audience would see exists. This milestone inverts that.

The blocker changed on 2026-08-19. Bridges 16-19 are no longer a research problem: they are resolved by the owner confirming the move list, and they sit in a drawn endgame shuffle a 35-second short cuts anyway.

Full phased plan: `docs/PLAN.md`. Review it before starting implementation.

## Current — Phase 0 prerequisites

- [ ] Install Stockfish; pin the version in `MEMORY.md`.
- [ ] Choose chess piece artwork licensed for commercial use; rasterise to PNG sprites in `assets/renderer/pieces/`; record source and licence in `design.md`. Popular sets are GPL artwork and are not suitable for monetised video.
- [ ] Choose a commercially-licensed font; embed locally in `assets/renderer/fonts/`.
- [ ] **BLOCKED — mascot identity.** All ten `assets/Character/` concepts are derivative of Sherman (DreamWorks, *Mr. Peabody & Sherman*) and are not cleared for output. Decide the replacement direction: a chess-piece character (preferred — no human-character IP surface, and a simple silhouette stays legible at any size) or a human redesign changing at least three identifiers at once.
- [ ] Once the character is settled: matte **two** sprites (`intro_peek`, `facepalm`) to transparent PNG and prove the popup component in a real 1080×1920 render before touching the other eight. Requirements are in `design.md` — alpha channel, no baked decorations, gripped surfaces included in the sprite.
- [ ] Clear the outstanding Bridge 10 validation debt: repeat the constrained Gemini control 3-5 times and once with shuffled/reversed frame order. Not a Phase 1 blocker, since Phase 1 uses human confirmation.

## Open — repository and licensing

- [ ] **Decide repository visibility and licence.** It is public with no `LICENSE` file while importing GPL-3.0 `python-chess`. Staying public means the combined work must be GPL-3.0-compatible, which lets anyone legally take and run the whole system. Recommended: return to private until settled — `gh repo edit sahansbandara/chess-content-os --visibility private --accept-visibility-change-consequences`. Not a legal opinion; proper advice warranted before choosing to stay public.
- [ ] Blocked Set 2 concept art is in public git history from commit `b75abc1`. Deleting from `HEAD` does not remove it from history — going private is the only action that reduces the exposure.
- [ ] Replace the 7 absolute `/Users/sahansandaruwan/...` paths in `Agent/BRIEF.md`, `Agent/MEMORY.md` and `docs/PROJECT_MASTER_CONTEXT.md` with repository-relative paths. They publish the owner's real name.

## Open — documentation reconciliation

Known contradictions between committed files. Resolve before implementation starts, or a future session will build the wrong thing.

- [ ] `PROJECT_MASTER_CONTEXT.md` §2.2 uses `mascot_intro_peek` naming, §2.7 uses `intro_peek.png`. `design.md` now reconciles this (file on disk, logical id in `scene.json`) — mirror it back into the master context doc.
- [ ] `PROJECT_MASTER_CONTEXT.md` §2.4 budgets five mascot popups per short. Cut to three — each popup costs ~1.2s of slide-in/settle/exit, so five spend ~6s of a 36s video on the character moving and never let the board hold attention beyond 8s.
- [ ] Add to `PROJECT_MASTER_CONTEXT.md` §2.7: the Set 2 wall is load-bearing (hands grip it, so removing it leaves hands gripping nothing), and the source images have no alpha channel at all — the hoodie reads lighter than the background wall, so naive keying destroys the character before it clears the background.

## Next — Phase 1, recording to finished mp4

- [ ] Hand-write `moves.json` for the prototype game and freeze the schema (`docs/PLAN.md` 1.1).
- [ ] Build the schema validator; reject illegal sequences, same-side consecutive moves, and any `unresolved` move reaching the renderer.
- [ ] Make the extraction workers emit `moves.json`.
- [ ] Build the CLI human move-confirmation step; write `human_confirmed` status.
- [ ] Install and wire Stockfish analysis to `analysis.json`, kept separate from move truth.
- [ ] Implement win-percentage-delta move classification; unit-test the threshold boundaries.
- [ ] Build the moment selector, targeting the owner's largest win-% drop.
- [ ] Build the script generator on the fixed four-beat structure, constrained to `analysis.json` facts.
- [ ] Add a positioning lint that rejects authority-voiced copy.
- [ ] Record the owner's voice for the first script; build the audio-driven timeline.
- [ ] Wire Kokoro-82M as the non-personal-content voice path.
- [ ] Build the renderer: board and piece tweening, then text, then eval bar, then badges and effects, then mascot and bubble.
- [ ] Prove renderer determinism: identical inputs produce a byte-identical PNG sequence across two runs.
- [ ] Prove the renderer does not alter the move sequence.
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

## Last session summary

2026-08-19 — Pulled the 8 publishing files added on `main` and adopted their architecture: one verified master short, platform-specific copy, one approval, four independent adapters with per-platform idempotency. The skills are well-built and deliberately conservative about stale API assumptions; they are specifications only, and `src/publishers/` is still empty.

Two corrections landed. The supplied "original character" reference is Sherman from DreamWorks' *Mr. Peabody & Sherman*, so all ten mascot concepts are derivative works and the Set 2 selection is reversed — new pixels from a copyrighted character do not make an original. And the repository was set public while importing GPL-3.0 `python-chess` with no `LICENSE` file, which is now an open owner decision rather than a footnote.

`design.md` was rewritten around the character-agnostic popup mechanism so the work survives whichever replacement character is chosen.

Next: settle the mascot direction (a chess-piece character is the recommendation) and the repository visibility/licence question. Then Phase 0 — Stockfish, piece and font licensing, and the popup component.

## Update rule

Update this file at:

- task start when the current objective changes;
- meaningful milestone;
- architecture decision that changes the roadmap;
- session end.

Do not update for every tiny command or temporary debug print.
