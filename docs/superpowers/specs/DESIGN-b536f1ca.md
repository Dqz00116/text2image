---
id: DESIGN-b536f1ca
req: REQ-b536f1ca
feat: FEAT-b536f1ca
status: approved
decision: Approach B
---

# Design Options for Text-to-Image CLI

## Approach A: Single-File Script with openai SDK (Recommended)

One `cli.py` file (~200 lines). All logic in one place: image encoding, API call, response decoding, file save.

**Pros:**
- Fewest files, zero internal imports — trivially hackable
- `openai` SDK handles auth, retries, streaming, error typing out of the box
- `click` decorators produce clean --help and input validation
- Matches user's stated preference (click, uv, no local install)

**Cons:**
- If future features grow (batch generation, multiple providers), single-file becomes unwieldy
- Cannot unit-test helpers without importing the CLI module

**Effort**: ~30 min

---

## Approach B: Structured Package

```
src/text2image/
  __init__.py
  cli.py        # click commands only
  client.py     # API client (auth, request, response parsing)
  image.py      # image encode/decode helpers
pyproject.toml  # with [project.scripts] console entry point
```

**Pros:**
- Clear separation of concerns, each module independently testable
- Ready for `pip install` + global `text2image` command when wanted
- Scales well if more features are added

**Cons:**
- More boilerplate for an MVP: 4 files instead of 1
- Over-engineered for "wrap an API endpoint" scope

**Effort**: ~1 hr

---

## Approach C: Zero-SDK Manual HTTP (requests)

No `openai` dependency. Raw `requests.post()` with hand-built JSON bodies.

**Pros:**
- Fewer abstraction layers — every byte of the request is visible
- Smaller dependency footprint (no `openai` SDK)

**Cons:**
- Must manually handle auth header, error response parsing, streaming edge cases
- OpenRouter is OpenAI-compatible — using the SDK is the documented happy path
- More code to maintain for zero practical benefit

**Effort**: ~1 hr

---

## Recommendation

**Approach A** — Single-file script. It matches the user's tooling choices (click + openai SDK + uv), delivers the fastest MVP, and can be refactored to Approach B later if the tool grows. The openai SDK is already a project dependency and its error types, retry logic, and authentication handling are worth the import.
