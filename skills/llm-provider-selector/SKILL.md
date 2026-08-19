---
name: llm-provider-selector
description: Select and benchmark suitable free or low-cost LLM APIs for each project using current provider data, project requirements, privacy, quotas, and fallback planning.
user-invocable: true
---

# LLM Provider Selector

## Purpose

Select a project-appropriate provider and model. The answer may differ for each project.

Use this repository as a candidate-discovery source:

```text
https://github.com/cheahjs/free-llm-api-resources
```

It tracks legitimate providers, models, quotas, verification requirements, and some warnings. It is not a model-quality benchmark.

## When to use

Use when a project requires chat, coding, extraction, classification, embeddings, RAG, vision, speech, tool calling, structured output, or agent reasoning.

Skip when the project does not need an LLM API.

## Inputs to check

- Task type and modalities
- Requests and tokens per day
- Context length
- Structured-output and tool-calling needs
- Language requirements
- Latency target
- Data sensitivity and region restrictions
- Deployment platform
- Free-only or paid-fallback policy
- Reliability and commercial-use requirements

## Source policy

1. Read the latest repository README.
2. Record the repository update date.
3. Verify shortlisted providers against official documentation.
4. Treat quotas and free tiers as temporary.
5. Record verification date.
6. Do not send sensitive production data to an unacceptable free tier.
7. Never store API keys in Markdown.

## Hard filters

Reject a candidate if it lacks a required modality, quota, context, structured output, tool calling, privacy standard, region, commercial permission, deployment compatibility, or reliable fallback.

## Scoring model

| Criterion | Weight |
|---|---:|
| Task quality | 25 |
| API feature compatibility | 15 |
| Free quota suitability | 15 |
| Structured output/tool calling | 10 |
| Context suitability | 10 |
| Latency | 10 |
| Privacy/data handling | 10 |
| Provider stability | 5 |

Projects may change weights in `docs/LLM_PROVIDER_MATRIX.md`.

## Workflow

1. Read `agent/BRIEF.md`.
2. Decide whether an LLM is required.
3. Define project requirements.
4. Refresh free-provider candidates from the source repository.
5. Verify current details using official provider documentation.
6. Apply hard filters.
7. Shortlist 2–5 candidates.
8. Score candidates.
9. Benchmark the top 2–3 with real project cases.
10. Select primary, fallback, and optional paid migration path.
11. Update the LLM provider documents and `agent/DECISIONS.md`.
12. Add environment-variable names to `docs/ENV_VARS.md`.

## Benchmark requirements

Test correctness, instruction following, output format, latency, token usage, failures, multilingual/Sinhala performance when relevant, tool calling, JSON validity, and refusal behavior.

Do not declare a winner from one prompt.

## Architecture rule

```text
Application
→ LLM service/router
   ├── Primary provider
   ├── Fallback provider
   └── Optional paid provider
```

Suggested environment-variable names:

```text
LLM_PRIMARY_PROVIDER
LLM_PRIMARY_MODEL
LLM_FALLBACK_PROVIDER
LLM_FALLBACK_MODEL
LLM_TIMEOUT_MS
LLM_MAX_RETRIES
LLM_DAILY_REQUEST_LIMIT
```

## Migration triggers

Move away from the free tier when quota usage exceeds 70%, fallback usage exceeds 10%, error rate exceeds 2%, latency becomes unacceptable, sensitive data is introduced, revenue depends on it, uptime becomes critical, or terms change.

## Output format

```text
LLM SELECTION:

PROJECT REQUIREMENTS:
- Task:
- Modality:
- Traffic:
- Context:
- Structured output/tool calling:
- Privacy:
- Latency:
- Deployment:

PRIMARY:
- Provider:
- Model:
- Score:
- Free quota:
- Reason:
- Limitations:

FALLBACK:
- Provider:
- Model:
- Score:
- Activation condition:

BENCHMARK:
- Cases tested:
- Results:
- Known failures:

PRODUCTION DECISION:
- Prototype only / acceptable for production / paid migration required
- Migration triggers:
- Verification date:
```

## Quality checklist

- [ ] Current source checked
- [ ] Official documentation verified
- [ ] Requirements documented
- [ ] Privacy checked
- [ ] Quota checked
- [ ] Top candidates benchmarked
- [ ] Primary and fallback selected
- [ ] Migration triggers defined
- [ ] No secrets stored
- [ ] No unsupported “best model” claim

## Stop conditions

Stop if terms cannot be verified, privacy is unacceptable, required capabilities are missing, or production depends entirely on an unstable free tier.
