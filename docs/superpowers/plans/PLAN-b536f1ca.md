---
id: PLAN-b536f1ca
req: REQ-b536f1ca
design: DESIGN-b536f1ca
status: draft
---

# Implementation Plan: Text-to-Image CLI

## File Structure

```
E:\Agent\TextToImage\
├── pyproject.toml                 # deps: openai, click, pytest
├── cli.py                         # entry point: `python cli.py`
├── src/
│   └── text2image/
│       ├── __init__.py            # package marker
│       ├── client.py              # API client
│       └── image_utils.py         # image encode/decode helpers
└── tests/
    ├── __init__.py
    ├── test_image_utils.py
    └── test_client.py
```

## Tasks

- [ ] TASK-001: Create `pyproject.toml` with deps (openai, click, pytest)
- [ ] TASK-002: Create `src/text2image/__init__.py`
- [ ] TASK-003: Implement `src/text2image/image_utils.py` — `encode_image_to_data_url(path)` and `decode_data_url_to_bytes(data_url)`
- [ ] TASK-004: Implement `src/text2image/client.py` — `TextToImageClient` class with `generate(prompt, image_path, aspect_ratio, image_size)` method
- [ ] TASK-005: Implement `cli.py` — click command with all options, wires Client → response → save
- [ ] TASK-006: Write `tests/test_image_utils.py` — test base64 encode/decode round-trip
- [ ] TASK-007: Write `tests/test_client.py` — test message building for text-only and text+image
- [ ] TASK-008: Run `pytest` — all tests pass

## Test Strategy

| Layer | What | Tool |
|-------|------|------|
| Unit: `image_utils.py` | encode/decode round-trip, MIME detection, data URL parsing | `pytest` |
| Unit: `client.py` | Message structure correctness (text-only vs text+image), image_config assembly | `pytest` (no real API call) |
| Integration | Full `cli.py` invocation with CliRunner | `pytest` + `click.testing.CliRunner` |

## Edge Cases Covered

- Empty API key (--api-key missing and env var unset) → clear error + exit
- Local image file not found → FileNotFoundError with path
- API returns no images in response → error with usage info if available
- API returns error (401, 402, 429) → pass through status code + message
- Output path in subdirectory that doesn't exist → auto-create parent dirs
- Non-image file extension for output → determined by actual MIME from data URL
