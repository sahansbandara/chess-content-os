---
name: social-publishing
description: Orchestrate approved multi-platform publishing across YouTube, Instagram, Facebook, and TikTok with per-platform idempotency, retries, and result recording.
user-invocable: true
---

# Social Publishing

## Purpose

Publish one approved release bundle to all enabled social platforms without duplicating successful posts or allowing one platform failure to corrupt the others.

This skill orchestrates platform-specific publisher adapters. It does not contain platform API implementation details.

## Supported target platforms

```text
YouTube Shorts
Instagram Reels
Facebook Reels
TikTok
```

## Required input

An approved release bundle from `content-release`.

Required properties:

```text
content_id
media_path
validation = passed
approval = approved
enabled platforms
platform metadata
```

## Workflow

```text
approved release bundle
      ↓
load publication state for content_id
      ↓
for each enabled platform:
      ├── skip if already published
      ├── validate adapter readiness
      ├── call platform publisher
      ├── verify result
      └── store remote ID / status
      ↓
return combined publication report
```

## Per-platform independence

A platform failure must not trigger re-upload of platforms that already succeeded.

Example:

```text
YouTube   published
Instagram published
Facebook  published
TikTok    failed
```

Retry behavior:

```text
retry TikTok only
```

## Idempotency key

The logical idempotency key is:

```text
content_id + platform
```

Before publishing, load existing publication state.

If the platform already has a confirmed remote ID for that content ID, do not create another post.

## Unknown-result policy

If the client times out after sending an upload and the remote result is unknown:

1. do not immediately retry;
2. query or verify remote state when the platform supports it;
3. reconcile the publication record;
4. retry only when duplicate creation has been ruled out.

## Platform adapter mapping

```text
youtube   → youtube-publishing
instagram → meta-publishing / Instagram adapter
facebook  → meta-publishing / Facebook adapter
tiktok    → tiktok-publishing
```

## Publication result schema

```json
{
  "content_id": "...",
  "platforms": {
    "youtube": {
      "status": "published",
      "remote_id": "...",
      "attempts": 1
    },
    "instagram": {
      "status": "published",
      "remote_id": "...",
      "attempts": 1
    },
    "facebook": {
      "status": "published",
      "remote_id": "...",
      "attempts": 1
    },
    "tiktok": {
      "status": "failed",
      "remote_id": null,
      "attempts": 1,
      "error_class": "..."
    }
  }
}
```

## Retry policy

Retry only retriable failures such as temporary network/provider errors.

Do not retry:

- missing approval;
- invalid media;
- validator failure;
- invalid credentials until operator fixes them;
- permission/app-review denial;
- unsupported media constraints;
- deterministic metadata validation errors.

Use bounded retry/backoff in publisher code.

## Security rules

- Never log access tokens or refresh tokens.
- Never put credentials in release bundles.
- Publisher code loads credentials from approved secret storage/environment configuration.
- Public posting remains behind `approval-gate`.
- Keep a global outward-publishing kill switch.

## Quality checklist

- [ ] Release bundle approved
- [ ] `content_id` present
- [ ] Publication state loaded
- [ ] Already-published platforms skipped
- [ ] Failed platforms isolated
- [ ] Remote IDs stored
- [ ] No secrets logged
- [ ] Combined result returned

## Stop conditions

Stop the entire run before the first upload if release approval or validation is invalid.

After publishing begins, isolate platform-specific failures rather than rolling back unrelated successful posts.
