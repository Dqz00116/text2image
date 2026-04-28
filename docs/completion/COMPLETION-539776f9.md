---
id: COMPLETION-539776f9
req: REQ-539776f9
date: 2026-04-28
---

# Completion: Visual Description Backend

## Summary

Added `describe` subcommand with adapter layer supporting two vision backends — Kimi-Code CLI (`--print` mode) and OpenRouter vision models.

## What Changed

| File | Change |
|------|--------|
| `src/text2image/describer.py` | NEW — `DescribeResult`, `ImageDescriber` ABC, `KimiCodeDescriber`, `OpenRouterVisionDescriber`, `create_describer` factory |
| `cli.py` | REFACTOR — flat command → Click group with `generate` + `describe` subcommands |
| `tests/unit/test_describer.py` | NEW — 14 tests covering both backends, factory, error paths |
| `tests/integration/test_cli.py` | UPDATE — all invocations updated to group syntax, +6 describe tests |

## Usage

```bash
# Generate (backward compatible)
uv run python cli.py generate -p "a cat in watercolor" -o cat.png

# Describe with Kimi (default)
uv run python cli.py describe cat.png

# Describe with custom question
uv run python cli.py describe cat.png "How many people in this image?"

# Describe with OpenRouter vision
uv run python cli.py describe cat.png --backend openrouter

# JSON output for scripting
uv run python cli.py describe cat.png --json
```

## Tests
46/46 passing (33 unit + 13 integration). Zero regressions.
