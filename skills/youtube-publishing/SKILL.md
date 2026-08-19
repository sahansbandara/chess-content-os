---
name: youtube-publishing
description: Safely publish an approved Chess Content OS release to YouTube Shorts using the official YouTube Data API, preserving idempotency and publication state.
user-invocable: true
---

# YouTube Publishing

## Purpose

Define the agent procedure for publishing an approved Short to YouTube.

The actual API implementation belongs in `src/publishers/youtube.py`.

## Current official capability basis

At the time of this specification, Google's official YouTube Data API documentation supports video upload through `videos.insert`, with OAuth 2.0 authorization and metadata such as title, description, tags, category, and privacy status.

Production code should use resumable upload behavior and verify processing status after upload.

Unverified API projects may have uploaded videos restricted to private viewing until the required audit is completed. Design private-first operation as a normal supported state.

Always re-check current official Google documentation before implementing or changing API behavior.

## Required inputs

```text
approved release bundle
content_id
master/derived video path
YouTube title
description
tags/hashtags
privacy/schedule intent
```

## Preflight

Require:

- release approval = approved;
- YouTube enabled;
- video file exists;
- validator passed;
- no unresolved chess truth;
- metadata exists;
- no confirmed YouTube publication already exists for this content ID;
- OAuth credentials/token available;
- global publish kill switch off.

## Workflow

```text
preflight
→ authenticate
→ prepare metadata
→ upload video
→ capture returned video ID
→ verify processing/upload status
→ store publication record
→ return success
```

## Private-first behavior

During development and API verification, prefer private uploads.

The system must support:

```text
private test upload
→ verify rendered video and metadata
→ later public/scheduled release only under approved production flow
```

## Metadata boundary

Use metadata produced by `platform-metadata`.

Do not rewrite chess claims inside the publisher.

The publisher may map metadata field names to YouTube API fields but may not create new factual claims.

## Idempotency

Before upload, query local publication state for:

```text
content_id + youtube
```

If a confirmed remote YouTube video ID exists, return `already_published` rather than uploading again.

For ambiguous network failures after request submission, verify remote/local state before retrying.

## Result record

Store at minimum:

```text
content_id
platform = youtube
remote_video_id
status
privacy state
published/uploaded timestamp
attempt count
metadata version/hash
```

Never store OAuth secrets in publication records.

## Retry policy

Use bounded retry/backoff only for temporary network/server failures.

Do not retry deterministic validation, permission, credential, quota-policy, or app-audit failures without operator action.

## Quality checklist

- [ ] Approved release
- [ ] YouTube enabled
- [ ] Metadata validated
- [ ] Duplicate check complete
- [ ] OAuth available
- [ ] Upload result captured
- [ ] Processing/status verified
- [ ] Publication state saved
- [ ] No secret logged

## Stop conditions

Stop before upload if approval, truth, media, metadata, credentials, or idempotency checks fail.
