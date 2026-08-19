# Multi-Platform Publishing — Chess Content OS

> Status: Architecture specification
> Updated: 2026-08-19
> Scope: YouTube Shorts, Instagram Reels, Facebook Reels, TikTok

## Purpose

Chess Content OS should produce **one verified master Short** and distribute it to all supported social platforms with **platform-specific copy, one human approval gate, independent publisher adapters, idempotent retries, and per-platform analytics**.

The system must not treat publishing as a YouTube-only problem.

## Core release model

```text
verified moves.json
      ↓
analysis.json
      ↓
script + voice + render plan
      ↓
professional 9:16 master video
      ↓
platform-metadata skill
      ↓
release bundle
      ↓
content evaluator
      ↓
HUMAN APPROVAL
      ↓
social-publishing orchestrator
  ├── YouTube adapter
  ├── Instagram adapter
  ├── Facebook adapter
  └── TikTok adapter
      ↓
publication records
      ↓
analytics snapshots
      ↓
Idea Engine
```

## One video, different platform copy

The creative master should normally be reused across platforms.

Do not copy one caption everywhere.

Generate platform-specific copy from the same verified story:

```text
verified chess facts
+ learner-not-guru positioning
+ core hook / lesson / CTA
        ↓
platform-metadata
        ├── YouTube title + description + tags
        ├── Instagram caption + hashtags
        ├── Facebook caption
        └── TikTok caption + hashtags
```

Platform wording may change. Chess facts may not.

## Example release bundle

```json
{
  "content_id": "2026-08-19-game-001",
  "media": {
    "master_path": "output/2026-08-19-game-001/final.mp4",
    "validation_status": "passed"
  },
  "chess_truth": {
    "moves_verified": true,
    "analysis_verified": true
  },
  "approval": {
    "status": "approved",
    "approved_by": "owner"
  },
  "platforms": {
    "youtube": {
      "enabled": true,
      "title": "2 Mistakes and I Got Checkmated",
      "description": "...",
      "hashtags": ["chess", "chessshorts", "learnchess"]
    },
    "instagram": {
      "enabled": true,
      "caption": "...",
      "hashtags": ["chess", "learnchess", "chesscommunity"]
    },
    "facebook": {
      "enabled": true,
      "caption": "..."
    },
    "tiktok": {
      "enabled": true,
      "caption": "...",
      "hashtags": ["chess", "chesstok", "learnchess"]
    }
  }
}
```

## Approval model

The owner should not normally approve the same final render four separate times.

Recommended release approval:

```text
Final video preview
+ verification summary
+ YouTube metadata
+ Instagram metadata
+ Facebook metadata
+ TikTok metadata
+ enabled platform list

[APPROVE ALL]
[REVISE]
[REJECT]
[PLATFORMS]
```

The owner must be able to disable an individual platform before approval.

Public publishing remains a high-risk action under `skills/approval-gate/SKILL.md`.

## Publisher architecture

Recommended implementation seam:

```text
src/publishers/
├── base.py
├── models.py
├── registry.py
├── youtube.py
├── instagram.py
├── facebook.py
└── tiktok.py
```

A common publisher contract should isolate platform-specific APIs from orchestration.

Conceptual interface:

```python
class Publisher:
    def publish(self, media_path, metadata, approval, content_id):
        ...
```

Each adapter owns its own authentication, metadata mapping, upload protocol, status checks, and remote identifiers.

## Idempotency

Every platform publish attempt must be tied to:

```text
content_id + platform
```

Publishing state should be stored independently:

```json
{
  "youtube": {"status": "published", "remote_id": "..."},
  "instagram": {"status": "published", "remote_id": "..."},
  "facebook": {"status": "published", "remote_id": "..."},
  "tiktok": {"status": "failed", "remote_id": null}
}
```

If TikTok fails after the other three succeed, retry TikTok only.

Never republish successful platforms during a retry.

If an upload response is ambiguous, verify remote state before retrying.

## Hard pre-publish gates

Publishing must stop when any of these is true:

- final render missing;
- content validator failed;
- move truth unresolved;
- engine claim unverified;
- human approval absent;
- platform disabled;
- duplicate `content_id + platform` already published;
- required credentials/permissions unavailable.

## Platform-specific copy rules

### YouTube Shorts

Use a strong short title, concise description, learner framing, community question, and relevant tags/hashtags.

Example tone:

```text
Title: 2 Mistakes and I Got Checkmated

I thought this move was safe.
It wasn't.

This is what I missed while learning this position.
What would you have played?
```

### Instagram Reels

Use a more conversational caption with a relatable learning moment and community CTA.

### Facebook Reels

Allow slightly more context and story while keeping the learner voice.

### TikTok

Use a compact hook-first caption and a direct viewer challenge.

No platform may claim a chess fact that is not supported by verified move and engine data.

## Current API implementation notes

### YouTube

Current official Google documentation supports video upload with the YouTube Data API `videos.insert` method and OAuth 2.0 authorization. The API can set metadata such as title, description, tags, category, and privacy status. Resumable upload and post-upload status checks should be used in production.

Unverified API projects may have uploads restricted to private viewing until the required audit is completed. Therefore the system should support private-first operation from the beginning.

### TikTok

Current TikTok Content Posting APIs support Direct Post and Upload-to-Draft workflows. Direct Post requires the creator's authorization/consent and platform-specific posting settings. Unaudited clients may have direct posts restricted to private visibility until audit requirements are satisfied.

### Instagram and Facebook

Implement as separate Meta publisher adapters even if authentication/account setup shares infrastructure.

Exact current Meta publishing endpoints, account requirements, permissions, review requirements, media-hosting rules, and Reel constraints must be verified against Meta's official developer documentation at implementation time. Do not hard-code stale assumptions into the skill.

## Reuse from previous repository research

The earlier `sahansbandara/youtube-automation-agent` project contains useful patterns that may be adapted:

- OAuth setup flow;
- publishing queue;
- private-by-default upload behavior;
- invalid/simulated-output rejection;
- scheduling concepts;
- analytics feedback;
- provider fallback patterns.

Do not copy its entire architecture. Chess Content OS has stronger truth, validation, and approval requirements.

## Skill composition

```text
platform-metadata
      ↓
content-release
      ↓
approval-gate
      ↓
social-publishing
      ├── youtube-publishing
      ├── meta-publishing
      └── tiktok-publishing
      ↓
analytics-feedback
```

## Implementation sequencing

Define these contracts and skills now.

Implement live OAuth/upload after the first professional Short is manually publishable and the content format is proven.

Recommended order:

```text
1. platform metadata schema
2. release bundle schema
3. publisher base contract
4. publication state/idempotency model
5. YouTube adapter
6. Instagram adapter
7. Facebook adapter
8. TikTok adapter
9. Telegram release approval
10. analytics collectors
11. scheduler/orchestrator
```

## Kill criteria

Stop publishing automation work if the project still cannot produce one professional Short worth posting manually.

Stop a publish run immediately if chess truth, validation, approval, or idempotency checks fail.
