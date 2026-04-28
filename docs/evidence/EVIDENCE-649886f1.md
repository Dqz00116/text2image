---
id: EVIDENCE-649886f1
req: REQ-649886f1
date: 2026-04-28
---

# Verification Evidence: .env Configuration for All CLI Defaults

## Criterion: All 9 env vars resolve correctly

**Tests:** 11 new integration tests covering env var resolution + CLI flag override

### generate env vars

| Test | PASSED |
|------|--------|
| `test_model_from_env` — `TEXT2IMAGE_MODEL` | ✅ |
| `test_output_from_env` — `TEXT2IMAGE_OUTPUT` | ✅ |
| `test_aspect_ratio_from_env` — `TEXT2IMAGE_ASPECT_RATIO` | ✅ |
| `test_image_size_from_env` — `TEXT2IMAGE_IMAGE_SIZE` | ✅ |
| `test_api_base_from_env` — `OPENROUTER_API_BASE` | ✅ |
| `test_cli_flag_overrides_env` — `--model` overrides `TEXT2IMAGE_MODEL` | ✅ |

### describe env vars

| Test | PASSED |
|------|--------|
| `test_vision_model_from_env` — `DESCRIBE_VISION_MODEL` | ✅ |
| `test_backend_from_env` — `DESCRIBE_BACKEND` | ✅ |
| `test_default_prompt_from_env` — `DESCRIBE_DEFAULT_PROMPT` | ✅ |
| `test_cli_prompt_overrides_env_prompt` | ✅ |
| `test_api_base_shared_between_commands` — `OPENROUTER_API_BASE` shared | ✅ |

## Criterion: No regressions

**Command:** `uv run pytest`
**Result:** 57 passed (33 unit + 24 integration), 0 failures, 0 warnings.
