---
name: platform-metadata
description: Generate platform-specific social copy from verified chess facts without changing chess truth or learner-community positioning.
user-invocable: true
---

# Platform Metadata

## Purpose

Turn one verified chess story into platform-specific titles, captions, descriptions, hashtags, and CTAs for YouTube Shorts, Instagram Reels, Facebook Reels, and TikTok.

This skill changes presentation, never chess facts.

## When to use

Use after:

- `moves.json` is verified;
- engine-backed claims are available in `analysis.json` when needed;
- the selected content moment is fixed;
- the core learner-story is known.

Do not use this skill to decide what actually happened in the game.

## Required inputs

```text
content_id
core_hook
verified mistake / lesson
owner move or moment
engine-backed alternative if used
creator positioning
CTA intent
platform list
```

## Hard positioning rules

The creator is a learner, not a guru.

Prefer:

```text
"I thought this was safe."
"I completely missed this."
"This is what I learned from the game."
"What would you have played?"
```

Reject:

```text
"You must always play this."
"This opening is unbeatable."
"Only bad players miss this."
"I will teach you the perfect move."
```

## Platform behavior

### YouTube Shorts

Generate:

```text
title
description
tags / hashtags
optional playlist/category hints
```

Tone: concise, searchable, strong hook, honest lesson.

### Instagram Reels

Generate:

```text
caption
hashtags
community CTA
```

Tone: conversational, relatable, learning-journey focused.

### Facebook Reels

Generate:

```text
caption
optional slightly longer context
community question
```

Tone: clear story and lesson without pretending authority.

### TikTok

Generate:

```text
compact caption
hashtags
short viewer challenge
```

Tone: hook-first and direct.

## Fact boundary

AI may rewrite:

- hook wording;
- emotional framing;
- CTA;
- platform tone;
- title;
- description;
- hashtags.

AI may not change:

- move order;
- SAN/UCI;
- whose move it was;
- check/checkmate status;
- tactic result;
- engine evaluation;
- move-quality classification;
- outcome of the game.

If a requested caption requires an unsupported chess claim, stop and return `FACT_GAP`.

## Output schema

```json
{
  "youtube": {
    "title": "...",
    "description": "...",
    "hashtags": []
  },
  "instagram": {
    "caption": "...",
    "hashtags": []
  },
  "facebook": {
    "caption": "..."
  },
  "tiktok": {
    "caption": "...",
    "hashtags": []
  }
}
```

## Quality checklist

- [ ] Learner-not-guru voice preserved
- [ ] Real mistake or learning moment remains central
- [ ] No fabricated statistics
- [ ] No unsupported chess claim
- [ ] Platform copy differs where useful
- [ ] CTA invites participation rather than lectures
- [ ] No spammy or irrelevant hashtags
- [ ] No secrets or internal implementation details

## Stop conditions

Stop if:

- chess facts are unresolved;
- selected lesson is unsupported by analysis;
- required platform metadata cannot be generated without inventing facts.

## Evaluation examples

Good:

```text
"2 mistakes and I got mated. I thought this pawn push was safe. Can you find what I missed?"
```

Bad:

```text
"The ultimate winning system every chess player must know."
```
