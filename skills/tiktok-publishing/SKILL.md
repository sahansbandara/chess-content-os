---
name: tiktok-publishing
description: Safely publish or upload an approved Chess Content OS release to TikTok using the current official Content Posting API, with explicit consent, idempotency, and publication-state tracking.
user-invocable: true
---

# TikTok Publishing

## Purpose

Define the agent procedure for sending an approved Chess Content OS Short to TikTok.

The actual API implementation belongs in `src/publishers/tiktok.py`.

## Current official capability basis

At the time of this specification, TikTok's official Content Posting API supports:

```text
Direct Post
Upload to TikTok as a draft
```

Direct Post requires the creator/user to authorize the app and provide the required posting settings/consent.

Unaudited clients may have direct-post visibility restricted to private until TikTok audit requirements are satisfied.

Always re-check current official TikTok developer documentation before implementing or changing API behavior.

## Required inputs

```text
approved release bundle
content_id
video path
TikTok caption/hashtags
posting mode
privacy/audience settings supported by current creator info
```

## Preflight

Require:

- release approval = approved;
- TikTok enabled;
- final media exists and passed validation;
- chess truth verified;
- TikTok metadata exists;
- access authorization available;
- required posting scope available;
- user/creator posting settings queried when required by the current API;
- no confirmed TikTok publication already exists for this content ID;
- global publish kill switch off.

## Direct Post workflow

Conceptual flow:

```text
preflight
→ query creator/posting information when required
→ present/use approved posting settings
→ initialize post
→ transfer media
→ capture publish identifier/status
→ verify result
→ store publication record
```

## Draft-upload workflow

Use when the release is intentionally being transferred to TikTok for manual completion/editing rather than direct public posting.

Conceptual flow:

```text
approved draft-upload intent
→ initialize upload
→ transfer media
→ record upload result
→ mark state = awaiting_manual_tiktok_post
```

Do not label draft upload as `published`.

## Consent boundary

TikTok direct posting must not bypass required user consent or creator posting options.

The social-publishing orchestrator may automate the technical sequence only after the release and posting intent have been approved.

## Metadata boundary

Use TikTok copy produced by `platform-metadata`.

The publisher may map caption/hashtags/settings into TikTok API fields but may not change chess facts.

## Idempotency

Use:

```text
content_id + tiktok
```

If a confirmed remote post ID/state already exists, do not create another post.

For timeouts or unknown results after upload initialization/transfer, reconcile remote/local state before retrying.

## Result record

Store:

```text
content_id
platform = tiktok
mode = direct_post | draft_upload
remote publish/upload identifier
status
visibility state when available
attempt count
timestamp
metadata version/hash
```

Never store access tokens in publication records.

## Retry policy

Retry only temporary network/provider failures under bounded backoff.

Do not retry deterministic validation, missing consent, permission/scope, audit-policy, authentication, or unsupported-media failures without operator action.

## Quality checklist

- [ ] Release approved
- [ ] TikTok enabled
- [ ] Posting mode explicit
- [ ] Creator authorization/consent requirements satisfied
- [ ] Metadata validated
- [ ] Duplicate check complete
- [ ] Result verified
- [ ] State saved correctly as published vs draft
- [ ] No secret logged

## Stop conditions

Stop before media transfer if approval, consent, truth, media, metadata, permissions, or idempotency checks fail.
