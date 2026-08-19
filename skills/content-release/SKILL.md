---
name: content-release
description: Build and validate a release bundle before any social platform upload, requiring verified chess truth, a passed final render, platform metadata, and explicit human approval.
user-invocable: true
---

# Content Release

## Purpose

Convert a finished Chess Content OS draft into one auditable release bundle that can be approved once and then distributed safely to enabled platforms.

This skill is the boundary between content generation and outward publishing.

## Required inputs

```text
content_id
final video path
render validation result
moves verification summary
analysis verification summary
platform metadata bundle
enabled platform list
approval state
```

## Release pipeline

```text
final.mp4
+ verified chess truth
+ verified analysis
+ platform metadata
      ↓
release validation
      ↓
approval-gate
      ↓
APPROVED release bundle
      ↓
social-publishing
```

## Pre-release checks

The release must fail if any of these is true:

- final video file does not exist;
- final video validator failed;
- any required chess move is unresolved;
- an engine-backed claim is unsupported;
- platform metadata is missing for an enabled platform;
- `content_id` is missing;
- approval is missing or rejected;
- outward publishing kill switch is active.

## One approval, platform controls

Normal behavior:

```text
preview final video
preview verification summary
preview all platform copy
preview enabled platforms
        ↓
APPROVE ALL / REVISE / REJECT / PLATFORMS
```

The owner may disable one or more platforms before approval without rebuilding the video.

## Release bundle schema

```json
{
  "content_id": "...",
  "media_path": "...",
  "validation": "passed",
  "truth": {
    "moves_verified": true,
    "analysis_verified": true
  },
  "approval": {
    "status": "approved",
    "approved_by": "owner",
    "approved_at": "..."
  },
  "platforms": {
    "youtube": {"enabled": true, "metadata": {}},
    "instagram": {"enabled": true, "metadata": {}},
    "facebook": {"enabled": true, "metadata": {}},
    "tiktok": {"enabled": true, "metadata": {}}
  }
}
```

## Audit requirements

Record:

- content ID;
- final media hash/path;
- validator result;
- verification summary;
- approved metadata version;
- approved platform list;
- approval timestamp;
- approval actor;
- publishing kill-switch state.

Do not record secrets.

## Relationship to approval-gate

Public posting is a high-risk action.

This skill must invoke or respect `skills/approval-gate/SKILL.md` before the release can become publishable.

## Quality checklist

- [ ] Final media exists
- [ ] Chess truth verified
- [ ] Engine claims verified
- [ ] Render passed validation
- [ ] All enabled platforms have metadata
- [ ] Human approval recorded
- [ ] Platform list is explicit
- [ ] Kill switch is off
- [ ] No secrets stored in bundle

## Stop conditions

Stop immediately on any failed pre-release gate.

Never downgrade a failed validator to a warning in order to publish.
