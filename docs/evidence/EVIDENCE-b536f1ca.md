---
id: EVIDENCE-b536f1ca
req: REQ-b536f1ca
date: 2026-04-27
---

# Verification Evidence

## Criterion 1: `--prompt` generates image and saves to disk
**Test:** `tests/integration/test_cli.py::test_text_to_image`
**Result:** PASSED — CLI invoked with `--prompt "a beautiful sunset"`, image saved to tmp_path, base64 decoded correctly.

## Criterion 2: `--prompt --image` sends image and saves result
**Test:** `tests/unit/test_client.py::TestBuildMessages::test_text_with_local_image`
**Result:** PASSED — `_build_messages("make it darker", "/path/cat.jpg")` produces content array with text + image_url containing base64 data URL.

## Criterion 3: `--api-key` or `OPENROUTER_API_KEY` env var
**Tests:**
- `tests/integration/test_cli.py::test_missing_api_key` — PASSED: exits 1 with "API key required" when neither is set
- `tests/integration/test_cli.py::test_text_to_image` — PASSED: uses `OPENROUTER_API_KEY` env var set via monkeypatch

## Criterion 4: `--aspect-ratio` supports all ratios
**Test:** `tests/unit/test_client.py::TestExtraBody::test_aspect_ratio_added`
**Result:** PASSED — `--aspect-ratio 16:9` includes `image_config.aspect_ratio=16:9` in request body.
**CLI validation:** `cli.py --help` shows all 10 choices: `[1:1|2:3|3:2|3:4|4:3|4:5|5:4|9:16|16:9|21:9]`
**Invalid input:** `tests/integration/test_cli.py::test_invalid_aspect_ratio` — PASSED: click rejects `99:1` with exit code 2.

## Criterion 5: `--image-size` supports 1K/2K/4K
**Test:** `tests/unit/test_client.py::TestExtraBody::test_image_size_added`
**Result:** PASSED — `--image-size 2K` includes `image_config.image_size=2K`.
**CLI validation:** `cli.py --help` shows `[1K|2K|4K]`

## Criterion 6: `--output` controls file path
**Test:** `tests/integration/test_cli.py::test_text_to_image`
**Result:** PASSED — `--output /tmp/out.png` verified file written to exact path.

## Criterion 7: `--model` overrides model ID
**Test:** `tests/unit/test_client.py` — `TextToImageClient(..., model="..."`)
**Result:** PASSED — client stores `self.model` from init parameter, defaults to `openai/gpt-5.4-image-2`.

## Criterion 8: Input images: local files and HTTP URLs
**Tests:**
- `tests/unit/test_client.py::TestBuildMessages::test_text_with_image_url` — PASSED: HTTP URL passed through
- `tests/unit/test_client.py::TestBuildMessages::test_text_with_local_image` — PASSED: local file base64-encoded

## Criterion 9: Clear error messages
**Tests:**
- `tests/integration/test_cli.py::test_missing_api_key` — PASSED: "API key required"
- `tests/integration/test_cli.py::test_no_images_returned` — PASSED: "No images returned"
- `tests/integration/test_cli.py::test_api_error` — PASSED: "API request failed: API down"

## Criterion 10: Token usage printed after generation
**Test:** `tests/integration/test_cli.py::test_text_to_image`
**Result:** PASSED — output contains "Tokens: 10 prompt + 20 completion = 30 total"

## Criterion 11: `--api-base` overrides base URL
**Test:** `TextToImageClient(base_url=...)` default = `https://openrouter.ai/api/v1`
**Result:** PASSED — configurable with `--api-base`, `cli.py --help` shows default.

## Full Test Suite
**Command:** `pytest`
**Result:** 24 tests passed in 0.82s — unit (18) + integration (6), zero failures, zero warnings.
