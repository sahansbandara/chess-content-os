---
name: analytics-feedback
description: Collect and compare per-platform performance snapshots for published Chess Content OS posts, then turn measured results into content experiments without fabricating causal claims.
user-invocable: true
---

# Analytics Feedback

## Purpose

Close the loop after publication.

Collect available metrics from YouTube, Instagram, Facebook, and TikTok, store time-stamped snapshots by content ID, compare content variables, and propose the next experiment.

This skill does not invent performance data and does not treat correlation as proven causation.

## When to use

Use only after a content item has a confirmed publication record on at least one platform.

## Inputs

```text
content_id
publication records
platform remote IDs
content metadata
hook type
mistake/tactic type
video duration
CTA type
mascot events used
render/style version
```

## Core workflow

```text
publication records
      ↓
collect platform metrics currently available
      ↓
store timestamped snapshots
      ↓
normalize only where comparison is defensible
      ↓
compare content variables
      ↓
identify patterns / uncertainties
      ↓
propose next content experiment
      ↓
Idea Engine / skill benchmark updates
```

## Possible metrics

Collect only metrics actually exposed by each platform/API and account type.

Possible examples:

```text
views / plays
likes
comments
shares
saves when available
watch time / retention when available
completion metrics when available
followers/subscribers attributed when available
publication age
```

Do not assume every platform exposes the same metric or defines it identically.

## Snapshot model

Example:

```json
{
  "content_id": "...",
  "platform": "youtube",
  "captured_at": "...",
  "age_hours": 24,
  "metrics": {
    "views": 0,
    "likes": 0,
    "comments": 0,
    "shares": null,
    "retention": null
  }
}
```

`null` means unavailable/unknown, not zero.

## Content variables to track

Useful experiment dimensions:

```text
hook wording
mistake category
puzzle vs straight explanation
video duration
freeze-beat duration
mascot appearance count
mascot mood used
speech-bubble style
CTA wording
voice style
caption style
platform-specific metadata version
```

## Analysis rules

- Never fabricate missing metrics.
- Never compare metrics with different platform definitions as if they are identical.
- Flag small samples.
- Separate observed result from inference.
- Treat one viral/failed post as weak evidence.
- Prefer repeated patterns across multiple posts.
- Record what would falsify a content hypothesis.

## Example output

```text
OBSERVED:
Videos using a puzzle pause have higher median completion in the current sample.

UNCERTAINTY:
The sample is small and those videos were also shorter.

NEXT EXPERIMENT:
Keep duration within the same range and vary only puzzle pause on/off across the next matched set.
```

## Idea Engine handoff

The skill may propose:

- repeat a strong mistake type;
- test a different hook for the same lesson type;
- adjust mascot frequency;
- test shorter/longer explanation;
- promote high-performing examples into skill benchmark libraries.

It may not claim a strategy is proven from inadequate evidence.

## Platform API rule

Before implementing analytics collectors, verify current official APIs, permissions, metric definitions, and availability for each platform.

Do not copy stale metric assumptions from old repositories or tutorials.

## Quality checklist

- [ ] Publication IDs verified
- [ ] Metrics sourced from platform/API
- [ ] Missing metrics represented as unknown
- [ ] Snapshot timestamp stored
- [ ] Platform definitions not silently conflated
- [ ] Sample-size limitation stated
- [ ] Observation separated from inference
- [ ] Next experiment changes as few variables as practical

## Stop conditions

Stop and report `INSUFFICIENT_DATA` when no reliable measurement supports a useful conclusion.
