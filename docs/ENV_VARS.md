# Environment Variables

Names and purposes only. **Values live in `.env`, which is gitignored and must
never be committed, pasted into documentation, logged, or included in a prompt or
an approval message.**

Logs may record a credential *label* (`PRIMARY`, `BACKUP`) so failures can be
traced. They must never record a credential value.

## Currently in use

| Variable | Purpose | Required |
|---|---|---|
| `GEMINI_API_KEY_PRIMARY` | Gemini credential slot 1 | one of the two |
| `GEMINI_API_KEY_BACKUP` | Gemini credential slot 2 | one of the two |
| `GEMINI_VIDEO_MODEL` | Gemini model id used by the evidence probes | yes, when calling Gemini |

Both key slots are read by `src/providers/gemini_client.py`, which tries them in
order and falls back on provider or network errors only — never to mask a bad
model response.

Known limitation: two keys from the same Google project share project-level
service limits. This is credential redundancy, not independent-provider
redundancy. A genuine second provider behind the same seam would be required for
quota resilience.

## Planned

Not yet implemented. Listed so the names are settled before the code is written.

| Variable | Purpose | Phase |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI provider credential; unused until the OpenAI provider adapter is implemented | 1 |
| `STOCKFISH_PATH` | Path to the local Stockfish binary | 1 |
| `PUBLISHING_ENABLED` | Master kill switch for all outward publishing. Anything other than `true` disables every publisher. | 2 |
| `TELEGRAM_BOT_TOKEN` | Approval bot credential | 2 |
| `TELEGRAM_CHAT_ID` | Destination chat for approval messages | 2 |
| `YOUTUBE_CLIENT_ID` | YouTube Data API OAuth client | 2 |
| `YOUTUBE_CLIENT_SECRET` | YouTube Data API OAuth client secret | 2 |
| `YOUTUBE_REFRESH_TOKEN` | Long-lived YouTube upload credential | 2 |

`PUBLISHING_ENABLED` must default to disabled. Local generation and rendering
must work with no publishing credentials present at all.

## Rules

- `.env` and `.env.*` are gitignored. Verify that with `git check-ignore -v .env`
  rather than assuming it.
- Never commit a real credential, even briefly, even to a private repository —
  git history is not a safe place for a secret.
- If a key is ever exposed, rotate it at the provider first, then clean up.
- Add a new variable here at the same time as the code that reads it.
- Never interpolate a secret into a URL, query string, filename, or log line.
