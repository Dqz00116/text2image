---
id: COMPLETION-499776f9
req: REQ-499776f9
date: 2026-04-27
---

# Completion: Multi-Image Support

## Summary
`--image` / `-i` now accepts multiple values. Use `-i` multiple times for character reference + style references.

## Usage
```bash
# Single image (backward compatible)
uv run python cli.py -p "..." -i ref.png

# Multiple images
uv run python cli.py -p "..." -i char.png -i style1.jpg -i style2.jpg
```

## Tests
26/26 passing (19 unit + 7 integration).
