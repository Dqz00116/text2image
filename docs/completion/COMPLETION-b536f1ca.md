---
id: COMPLETION-b536f1ca
req: REQ-b536f1ca
date: 2026-04-27
---

# Completion: OpenRouter GPT-5.4 Image 2 CLI

## Summary

- **Feature**: CLI wrapper for OpenRouter `openai/gpt-5.4-image-2` image generation
- **Status**: Complete — all 11 acceptance criteria verified
- **Tests**: 24/24 passing (18 unit + 6 integration)
- **Evidence**: [EVIDENCE-b536f1ca.md](../evidence/EVIDENCE-b536f1ca.md)

## Deliverables

```
E:\Agent\TextToImage\
├── cli.py                       # Entry point
├── pyproject.toml               # Dependencies
├── src/text2image/
│   ├── __init__.py
│   ├── image_utils.py           # Base64 encode/decode
│   └── client.py                # API client
└── tests/
    ├── unit/
    │   ├── test_image_utils.py  # 7 tests
    │   └── test_client.py       # 11 tests
    └── integration/
        └── test_cli.py          # 6 tests
```

## Usage

```bash
# Text-to-image
uv run python cli.py --prompt "a sunset over mountains"

# Image+text-to-image  
uv run python cli.py --prompt "make it nighttime" --image cat.png

# Custom params
uv run python cli.py --prompt "..." --aspect-ratio 16:9 --image-size 2K --output result.png

# API key via env var
export OPENROUTER_API_KEY="sk-..."
uv run python cli.py --prompt "..."
```
