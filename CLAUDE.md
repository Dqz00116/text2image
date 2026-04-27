# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv run pytest                    # All tests (25)
uv run pytest tests/unit -v      # Unit tests (18)
uv run pytest tests/integration -v # Integration tests (7)
uv run python cli.py --help      # Show CLI usage
```

No build or lint step configured yet.

## Architecture

CLI wrapper for OpenRouter's `openai/gpt-5.4-image-2` image generation model, using the OpenAI Python SDK pointed at OpenRouter's API base.

**Data flow:**

```
cli.py (click) → TextToImageClient → OpenAI SDK → OpenRouter API
                      ↑
              image_utils.py (encode/decode base64)
```

- `cli.py` — Entry point. Click command with all options. Loads `.env` via `python-dotenv`, resolves API key priority (`--api-key` > `OPENROUTER_API_KEY` env > `.env`), calls `TextToImageClient.generate()`, saves the base64 result to disk.
- `src/text2image/client.py` — `TextToImageClient` wraps `openai.OpenAI`. `generate()` returns a `GenerationResult` TypedDict with keys: `images`, `text`, `model`, `usage`. `_build_messages()` handles two paths: text-only (plain string content) and text+image (content array with `image_url` part). Local images are converted to base64 data URLs; HTTP URLs pass through.
- `src/text2image/image_utils.py` — Two pure functions: `encode_image_to_data_url(path)` reads a local file → base64 data URL; `decode_data_url_to_bytes(data_url)` extracts base64 from a data URL → raw bytes.

**API details:**
- Endpoint: `POST https://openrouter.ai/api/v1/chat/completions`
- Auth: `Authorization: Bearer <key>`
- Image generation requires `extra_body={"modalities": ["image", "text"]}` on the chat completions call
- `image_config` (with `aspect_ratio` and `image_size`) only included when non-default
- Generated images arrive as `choices[0].message.images[0].image_url.url` (base64 data URL)
- Input images use OpenAI vision format: `{"type": "image_url", "image_url": {"url": "..."}}`

**Testing:**
- Unit tests mock `_api_call()` — no real network calls
- Integration tests use `click.testing.CliRunner` with mocked `TextToImageClient.generate`
- Tests use module-level patches on `cli.<name>` (where imported), not original module paths
