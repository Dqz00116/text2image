# TextToImage CLI

CLI tool for image generation and visual description powered by OpenRouter API and Kimi-Code.

## Quick Start

```bash
# Install
git clone https://github.com/Dqz00116/text2image.git
cd text2image
uv sync

# Configure
cp .env.example .env
# Edit .env with your OpenRouter API key

# Generate an image
uv run python cli.py generate -p "a sunset over mountains" -o sunset.png

# Describe an image
uv run python cli.py describe sunset.png
```

## Commands

### `generate` — Image Generation

```bash
# Text-to-image
uv run python cli.py generate -p "a cat in watercolor style" -o cat.png

# Image+text-to-image (style reference)
uv run python cli.py generate -p "make it nighttime" -i ref.png

# Multiple reference images
uv run python cli.py generate -p "combine these styles" -i char.png -i style.png

# Custom params
uv run python cli.py generate -p "..." --aspect-ratio 16:9 --image-size 2K --model openai/gpt-5.4-image-2
```

### `describe` — Visual Description

Get text descriptions of images using a vision-capable backend.

```bash
# Describe with Kimi-Code (default, local)
uv run python cli.py describe cat.png

# Ask a specific question
uv run python cli.py describe cat.png "How many people in this image?"

# Use OpenRouter vision model
uv run python cli.py describe cat.png --backend openrouter

# JSON output for scripting
uv run python cli.py describe cat.png --json
```

### Backend Options

| Backend | Type | Requirements |
|---------|------|-------------|
| `kimi` (default) | Local CLI via `kimi --print` | [Kimi-Code CLI](https://www.kimi-cli.com/) installed |
| `openrouter` | API via OpenRouter | `OPENROUTER_API_KEY` set in `.env` |

> **Python 3.14 note**: Set `KIMI_PYTHON=3.13` in `.env` to run Kimi via `uv` with a compatible Python version.

## Configuration

All settings can be configured via `.env` file, environment variables, or CLI flags.
Priority: **CLI flag > env var > .env > hardcoded default**.

| Variable | Purpose | Default |
|----------|---------|---------|
| `DESCRIBE_BACKEND` | `describe --backend` | `kimi` |
| `DESCRIBE_VISION_MODEL` | `describe --vision-model` | `openai/gpt-4o` |
| `OPENROUTER_API_BASE` | `generate --api-base` + `describe` (shared) | `https://openrouter.ai/api/v1` |
| `TEXT2IMAGE_ASPECT_RATIO` | `generate --aspect-ratio` | `1:1` |
| `TEXT2IMAGE_IMAGE_SIZE` | `generate --image-size` | `1K` |
| `TEXT2IMAGE_MODEL` | `generate --model` | `openai/gpt-5.4-image-2` |
| `TEXT2IMAGE_OUTPUT` | `generate --output` | `output.png` |

## Architecture

```
cli.py (Click group)
├── generate  →  TextToImageClient  →  OpenAI SDK  →  OpenRouter API
│                  (src/text2image/client.py)
│
└── describe  →  ImageDescriber (ABC)
                   (src/text2image/describer.py)
    ├── KimiCodeDescriber      →  subprocess: kimi --print
    └── OpenRouterVisionDescriber  →  OpenAI SDK → OpenRouter API
```

```
src/text2image/
├── client.py       # Image generation via OpenRouter
├── describer.py    # Visual description adapter layer
└── image_utils.py  # Base64 encode/decode utilities
```

## Feature History

- **2026-04-27** — OpenRouter GPT-5.4 Image 2 CLI: CLI wrapper for OpenRouter `openai/gpt-5.4-image-2` image generation
- **2026-04-28** — .env Configuration for All CLI Defaults: All CLI default values now support `.env` / environment variable configuration. Priority: CLI flag > env var > .env > hardcoded default.
- **2026-04-28** — Visual Description Backend: Added `describe` subcommand with adapter layer supporting two vision backends — Kimi-Code CLI (`--print` mode) and OpenRouter vision models.
- **2026-04-27** — Multi-Image Support: `--image` / `-i` now accepts multiple values. Use `-i` multiple times for character reference + style references.

> Auto-generated from `docs/completion/` on 2026-04-28.
> Run `uv run python scripts/generate_readme.py` to regenerate.
