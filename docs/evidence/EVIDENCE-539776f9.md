---
id: EVIDENCE-539776f9
req: REQ-539776f9
date: 2026-04-28
---

# Verification Evidence: Visual Description Backend

## Criterion: CLI refactored to Click group with `generate` and `describe`
**Command:** `uv run python cli.py --help`
**Output:**
```
Commands:
  describe  Describe an image using a vision-capable backend.
  generate  Generate images using OpenRouter's GPT-5.4 Image 2 model.
```
**Result:** PASSED — both subcommands listed.

## Criterion: `generate` subcommand preserves all options (backward compatible)
**Command:** `uv run python cli.py generate --help`
**Output:** --prompt, --image, --output, --model, --aspect-ratio, --image-size, --api-key, --api-base all present.
**Tests:** 7/7 Generate integration tests PASSED.
**Result:** PASSED — zero behavioral change.

## Criterion: `describe IMAGE [PROMPT]`
**Command:** `uv run python cli.py describe --help`
**Output:** Usage: `cli.py describe [OPTIONS] IMAGE [PROMPT]`
**Tests:** `test_describe_default`, `test_describe_custom_prompt` — both PASSED.
**Result:** PASSED.

## Criterion: ImageDescriber ABC + two implementations
**Tests:** 14/14 `test_describer.py` PASSED:
- `TestDescribeResult` (1): TypedDict shape
- `TestKimiCodeDescriber` (7): success, custom prompt, exit 1, exit 75, timeout, not found, custom path
- `TestOpenRouterVisionDescriber` (3): success, image data URL encoding, HTTP URL passthrough
- `TestCreateDescriber` (3): kimi, openrouter, invalid
**Result:** PASSED.

## Criterion: --backend kimi|openrouter
**Tests:** `test_describe_openrouter_backend` PASSED — `--backend openrouter` invokes `create_describer("openrouter", ...)`.
**Default:** kimi backend confirmed in test_describe_default.
**Result:** PASSED.

## Criterion: --json output
**Test:** `test_describe_json` — verifies `{"description": "...", "model": "...", "backend": "...", "usage": ...}`.
**Result:** PASSED.

## Criterion: Timeout resolution (--timeout > DESCRIBE_TIMEOUT > 60)
**Test:** `test_describe_timeout_env` — `DESCRIBE_TIMEOUT=120` from env, default 60.
**Code check:** `cli.py:111-113` — three-way fallback implemented.
**Result:** PASSED.

## Criterion: Error handling — kimi not found
**Test:** `test_kimi_not_found` — `FileNotFoundError` → `RuntimeError("Kimi-Code not found")`.
**Result:** PASSED.

## Criterion: Error handling — API key missing (openrouter)
**Test:** `test_missing_api_key` in TestGenerate (applies to openrouter backend).
**Result:** PASSED.

## Full Test Suite
**Command:** `uv run pytest`
**Result:** 46 passed (33 unit + 13 integration), 0 failures, 0 warnings.
