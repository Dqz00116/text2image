---
id: REQ-b536f1ca
title: OpenRouter GPT-5.4 Image 2 CLI
status: done
priority: high
---

## Description

A Python CLI tool that wraps the OpenRouter API for `openai/gpt-5.4-image-2`, supporting two input modes:

1. **Text-to-Image**: Provide a text prompt, get a generated image back
2. **Image+Text-to-Image**: Provide a text prompt plus an input image, get a generated/modified image back

The user is a developer who wants quick command-line access to the image generation model without writing API calls manually.

## Acceptance Criteria

- [ ] `--prompt "description"` generates an image and saves it to disk (default: `output.png`)
- [ ] `--prompt "description" --image cat.png` sends the image along with the prompt and saves the result
- [ ] `--api-key sk-...` or `OPENROUTER_API_KEY` env var authenticates the request
- [ ] `--aspect-ratio` supports: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9 (default: 1:1)
- [ ] `--image-size` supports: 1K, 2K, 4K (default: 1K)
- [ ] `--output path/to/file.png` controls the output file path
- [ ] `--model` allows overriding the model ID (default: `openai/gpt-5.4-image-2`)
- [ ] Input images can be local file paths (auto-converted to base64 data URL) or HTTP URLs
- [ ] The CLI prints clear error messages for missing API keys, network failures, and API errors
- [ ] The CLI prints token usage info after a successful generation (prompt_tokens, completion_tokens, total_tokens)
- [ ] `--api-base` allows overriding the API base URL (default: `https://openrouter.ai/api/v1`)

## Notes

- Uses the OpenAI Python SDK (`openai`) pointed at OpenRouter's base URL
- Image output arrives as base64 data URLs in `response.choices[0].message.images[0].image_url.url`
- The `modalities: ["image", "text"]` extra_body parameter is required for image generation
- Image input uses the vision format: `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}`
- Local image files should be read and converted to base64 data URLs before sending
- Minimum Python version: 3.9

## Design Decisions

- **CLI framework**: `click` — better UX (progress output, rich help), already needed alongside `openai` SDK
- **Environment management**: `uv` (venv + `uv pip install`) — no `pip install` distribution for MVP
- **Entry point**: `python cli.py` or `uv run python cli.py` — single script, no console_scripts entry point yet
