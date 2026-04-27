---
id: FEAT-b536f1ca
req: REQ-b536f1ca
title: OpenRouter GPT-5.4 Image 2 CLI — Technical Implementation
status: draft
---

## Architecture

Single-file CLI script (`cli.py`) using `click` + `openai` SDK.

```
cli.py                    # CLI entry point, all logic
pyproject.toml            # Dependencies: openai, click
```

## CLI Design

```
python cli.py [OPTIONS]

Options:
  --prompt TEXT              Text prompt for image generation (required)
  --image PATH               Input image path (local file or HTTP URL)
  --output PATH              Output file path (default: output.png)
  --model TEXT               Model ID (default: openai/gpt-5.4-image-2)
  --aspect-ratio [1:1|2:3|3:2|3:4|4:3|4:5|5:4|9:16|16:9|21:9]
  --image-size [1K|2K|4K]
  --api-key TEXT             OpenRouter API key (or set OPENROUTER_API_KEY env var)
  --api-base TEXT            API base URL (default: https://openrouter.ai/api/v1)
  --help                     Show help
```

## Data Flow

### Text-to-Image
```
User prompt → build messages [{"role":"user","content":"prompt"}] 
→ POST chat/completions with modalities=["image","text"], image_config
→ response.choices[0].message.images[0].image_url.url (base64 data URL)
→ decode base64 → save to output file
```

### Image+Text-to-Image
```
User prompt + image path → 
  if local file: read bytes → base64 encode → data:image/<mime>;base64,<data>
  if URL: pass through
→ build messages [{"role":"user","content": [
     {"type":"text","text":"prompt"},
     {"type":"image_url","image_url":{"url":"<base64 or url>"}}
   ]}]
→ POST chat/completions (same as above)
→ decode base64 → save to output file
```

## Key Implementation Details

1. **API call**: Use `openai.OpenAI(base_url=..., api_key=...)` then `client.chat.completions.create()` with `extra_body={"modalities": ["image", "text"]}`
2. **image_config**: Pass `image_config` as another key in `extra_body` when aspect_ratio or image_size is non-default
3. **Local image → base64**: Read file, use `base64.b64encode()`, detect MIME type from extension
4. **Base64 save**: Parse `data:image/png;base64,...` → extract base64 portion → `base64.b64decode()` → write bytes
5. **Error handling**: Catch `openai.AuthenticationError`, `openai.APIStatusError`, network errors, file-not-found

## Dependencies

- `openai` — OpenAI SDK (compatible with OpenRouter)
- `click` — CLI framework

## Testing

Unit tests for:
- base64 encode/decode helpers
- message building (text-only vs text+image)
- CLI argument parsing (click CliRunner)
