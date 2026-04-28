---
id: COMPLETION-649886f1
req: REQ-649886f1
date: 2026-04-28
---

# Completion: .env Configuration for All CLI Defaults

## Summary

All CLI default values now support `.env` / environment variable configuration. Priority: CLI flag > env var > .env > hardcoded default.

## New env vars

| Variable | Affects | Default |
|----------|---------|---------|
| `TEXT2IMAGE_MODEL` | `generate --model` | `openai/gpt-5.4-image-2` |
| `TEXT2IMAGE_OUTPUT` | `generate --output` | `output.png` |
| `TEXT2IMAGE_ASPECT_RATIO` | `generate --aspect-ratio` | `1:1` |
| `TEXT2IMAGE_IMAGE_SIZE` | `generate --image-size` | `1K` |
| `OPENROUTER_API_BASE` | `generate --api-base` + `describe` (shared) | `https://openrouter.ai/api/v1` |
| `DESCRIBE_VISION_MODEL` | `describe --vision-model` | `openai/gpt-4o` |
| `DESCRIBE_BACKEND` | `describe --backend` | `kimi` |
| `DESCRIBE_DEFAULT_PROMPT` | `describe` default prompt | built-in text |

## Tests
57/57 passing (33 unit + 24 integration), 0 regressions.
