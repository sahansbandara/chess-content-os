---
name: meta-publishing
description: Safely publish approved Chess Content OS releases to Instagram Reels and Facebook Reels through separate Meta platform adapters with shared safety and approval rules.
user-invocable: true
---

# Meta Publishing

## Purpose

Define the publishing procedure for:

```text
Instagram Reels
Facebook Reels
```

Instagram and Facebook may share Meta authentication/account infrastructure, but they must remain separate publisher targets with independent publication state and remote IDs.

The actual API implementations should live in:

```text
src/publishers/instagram.py
src/publishers/facebook.py
```

## Important implementation rule

Meta platform requirements change.

Before implementing or changing live publishing code, verify the current official Meta developer documentation for:

- supported account/page types;
- required permissions;
- app review requirements;
- access-token lifecycle;
- media upload/hosting requirements;
- Reel publishing flow;
- caption/metadata fields;
- status/result verification;
- current media constraints.

Do not copy stale endpoint assumptions from old tutorials, blogs, or another repository.

## Required inputs

```text
approved release bundle
content_id
video path
Instagram metadata when Instagram is enabled
Facebook metadata when Facebook is enabled
enabled target list
```

## Common preflight

Require:

- release approved;
- final render validator passed;
- chess truth verified;
- target platform enabled;
- target account/page authorized;
- required permissions available;
- publication kill switch off;
- no confirmed duplicate publication for the same content ID and platform.

## Instagram workflow

Conceptual flow:

```text
approved release
→ validate Instagram metadata
→ validate account/permissions
→ transfer/create Reel media according to current official API
→ publish/complete container flow according to current official API
→ verify remote result
→ store Instagram publication ID/state
```

## Facebook workflow

Conceptual flow:

```text
approved release
→ validate Facebook metadata
→ validate Page/account/permissions
→ transfer/create Reel media according to current official API
→ publish according to current official API
→ verify remote result
→ store Facebook publication ID/state
```

## Platform independence

Instagram and Facebook are not one publication record.

Example:

```json
{
  "instagram": {"status": "published", "remote_id": "..."},
  "facebook": {"status": "failed", "remote_id": null}
}
```

A Facebook retry must not recreate the Instagram Reel.

## Metadata boundary

Use copy produced by `platform-metadata`.

The publisher may map fields to Meta API payloads but may not rewrite factual chess claims.

## Idempotency

Use independent keys:

```text
content_id + instagram
content_id + facebook
```

Never treat successful Instagram publishing as proof that Facebook publishing succeeded or vice versa.

## Result records

Store per platform:

```text
content_id
platform
remote media/post ID
status
published timestamp
attempt count
metadata version/hash
```

Do not store access tokens or secrets in publication records.

## Retry policy

Retry only temporary/retriable provider or network failures.

Do not retry permission, account-type, app-review, invalid-media, invalid-metadata, or authentication failures until the underlying issue is corrected.

If an API response is ambiguous, verify remote state before retrying.

## Quality checklist

- [ ] Release approved
- [ ] Correct Meta target enabled
- [ ] Current official API requirements verified during implementation
- [ ] Account/page permissions validated
- [ ] Metadata validated
- [ ] Duplicate check complete
- [ ] Result verified
- [ ] Per-platform publication state stored
- [ ] No secrets logged

## Stop conditions

Stop the target platform publish before transfer when approval, truth, media, permissions, metadata, or idempotency checks fail.
