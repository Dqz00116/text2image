import re
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
COMPLETION_DIR = ROOT / "docs" / "completion"
README_PATH = ROOT / "README.md"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-like frontmatter from markdown, return (meta, body)."""
    meta = {}
    body = text
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', text, re.DOTALL)
    if m:
        for line in m.group(1).strip().split("\n"):
            kv = line.split(":", 1)
            if len(kv) == 2:
                meta[kv[0].strip()] = kv[1].strip()
        body = m.group(2)
    return meta, body


def parse_sections(body: str) -> dict[str, str]:
    """Extract ## sections from markdown body, skipping code blocks."""
    sections = {}
    current_heading = None
    current_content = []
    in_code_block = False

    for line in body.split("\n"):
        if line.startswith("```"):
            in_code_block = not in_code_block
            if current_heading and not in_code_block:
                current_content.append(line)
            continue

        if in_code_block:
            if current_heading:
                current_content.append(line)
            continue

        if line.startswith("## "):
            if current_heading:
                sections[current_heading] = "\n".join(current_content).strip()
            current_heading = line[3:].strip()
            current_content = []
        elif line.startswith("# ") and "_title" not in sections:
            sections["_title"] = line[2:].strip()
        elif current_heading:
            current_content.append(line)

    if current_heading:
        sections[current_heading] = "\n".join(current_content).strip()

    return sections


def extract_usage_blocks(body: str) -> list[str]:
    """Extract markdown code blocks from body."""
    blocks = []
    in_block = False
    block_lines = []
    for line in body.split("\n"):
        if line.startswith("```") and not in_block:
            in_block = True
            block_lines = []
        elif line.startswith("```") and in_block:
            in_block = False
            blocks.append("\n".join(block_lines))
        elif in_block:
            block_lines.append(line)
    return blocks


def load_completions() -> list[dict]:
    """Load and parse all completion documents."""
    completions = []
    for fpath in sorted(COMPLETION_DIR.glob("COMPLETION-*.md")):
        text = fpath.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        sections = parse_sections(body)
        usage_blocks = extract_usage_blocks(body)
        completions.append({
            "file": fpath.name,
            "id": meta.get("id", ""),
            "date": meta.get("date", ""),
            "title": sections.get("_title", ""),
            "summary": sections.get("Summary", ""),
            "what_changed": sections.get("What Changed", ""),
            "tests": sections.get("Tests", ""),
            "usage": sections.get("Usage", ""),
            "new_env_vars": sections.get("New env vars", ""),
            "deliverables": sections.get("Deliverables", ""),
            "usage_blocks": usage_blocks,
        })
    return completions


def build_env_table(completions: list[dict]) -> str:
    """Build unified env var table from all completions."""
    env_vars = {}
    for c in completions:
        if c["new_env_vars"]:
            for line in c["new_env_vars"].split("\n"):
                m = re.match(r'\| `(\w+)` \| (.+?) \| `(.+?)` \|', line)
                if m:
                    env_vars[m.group(1)] = (m.group(2), m.group(3))

    if not env_vars:
        return ""

    lines = ["| Variable | Purpose | Default |",
             "|----------|---------|---------|"]
    for var, (purpose, default) in sorted(env_vars.items()):
        lines.append(f"| `{var}` | {purpose} | `{default}` |")
    return "\n".join(lines)


def generate_readme(completions: list[dict]) -> str:
    """Generate README.md content."""
    env_table = build_env_table(completions)

    # Collect all usage blocks
    usage_blocks = []
    for c in completions:
        usage_blocks.extend(c["usage_blocks"])

    # Latest completion date
    dates = [c["date"] for c in completions if c["date"]]
    latest = max(dates) if dates else datetime.now().strftime("%Y-%m-%d")

    # Feature history
    features = []
    for c in completions:
        title = c["title"].replace("Completion: ", "")
        summary = c["summary"].split("\n")[0] if c["summary"] else ""
        summary = re.sub(r'^[-*]\s*\*\*[^*]+\*\*[:\s]*', '', summary).strip()
        features.append((c["date"], title, summary))

    lines = [
        "# TextToImage CLI",
        "",
        "CLI tool for image generation and visual description powered by OpenRouter API and Kimi-Code.",
        "",
        "## Quick Start",
        "",
        "```bash",
        "# Install",
        "git clone https://github.com/Dqz00116/text2image.git",
        "cd text2image",
        "uv sync",
        "",
        "# Configure",
        "cp .env.example .env",
        "# Edit .env with your OpenRouter API key",
        "",
        "# Generate an image",
        "uv run python cli.py generate -p \"a sunset over mountains\" -o sunset.png",
        "",
        "# Describe an image",
        "uv run python cli.py describe sunset.png",
        "```",
        "",
        "## Commands",
        "",
        "### `generate` — Image Generation",
        "",
        "```bash",
        "# Text-to-image",
        "uv run python cli.py generate -p \"a cat in watercolor style\" -o cat.png",
        "",
        "# Image+text-to-image (style reference)",
        "uv run python cli.py generate -p \"make it nighttime\" -i ref.png",
        "",
        "# Multiple reference images",
        "uv run python cli.py generate -p \"combine these styles\" -i char.png -i style.png",
        "",
        "# Custom params",
        "uv run python cli.py generate -p \"...\" --aspect-ratio 16:9 --image-size 2K --model openai/gpt-5.4-image-2",
        "```",
        "",
        "### `describe` — Visual Description",
        "",
        "Get text descriptions of images using a vision-capable backend.",
        "",
        "```bash",
        "# Describe with Kimi-Code (default, local)",
        "uv run python cli.py describe cat.png",
        "",
        "# Ask a specific question",
        "uv run python cli.py describe cat.png \"How many people in this image?\"",
        "",
        "# Use OpenRouter vision model",
        "uv run python cli.py describe cat.png --backend openrouter",
        "",
        "# JSON output for scripting",
        "uv run python cli.py describe cat.png --json",
        "```",
        "",
        "### Backend Options",
        "",
        "| Backend | Type | Requirements |",
        "|---------|------|-------------|",
        "| `kimi` (default) | Local CLI via `kimi --print` | [Kimi-Code CLI](https://www.kimi-cli.com/) installed |",
        "| `openrouter` | API via OpenRouter | `OPENROUTER_API_KEY` set in `.env` |",
        "",
        "> **Python 3.14 note**: Set `KIMI_PYTHON=3.13` in `.env` to run Kimi via `uv` with a compatible Python version.",
        "",
        "## Configuration",
        "",
        "All settings can be configured via `.env` file, environment variables, or CLI flags.",
        "Priority: **CLI flag > env var > .env > hardcoded default**.",
        "",
    ]

    if env_table:
        lines.extend([env_table, ""])

    lines.extend([
        "## Architecture",
        "",
        "```",
        "cli.py (Click group)",
        "├── generate  →  TextToImageClient  →  OpenAI SDK  →  OpenRouter API",
        "│                  (src/text2image/client.py)",
        "│",
        "└── describe  →  ImageDescriber (ABC)",
        "                   (src/text2image/describer.py)",
        "    ├── KimiCodeDescriber      →  subprocess: kimi --print",
        "    └── OpenRouterVisionDescriber  →  OpenAI SDK → OpenRouter API",
        "```",
        "",
        "```",
        "src/text2image/",
        "├── client.py       # Image generation via OpenRouter",
        "├── describer.py    # Visual description adapter layer",
        "└── image_utils.py  # Base64 encode/decode utilities",
        "```",
        "",
        "## Feature History",
        "",
    ])

    for date, title, summary in reversed(features):
        lines.append(f"- **{date}** — {title}: {summary}")

    lines.extend([
        "",
        f"> Auto-generated from `docs/completion/` on {datetime.now().strftime('%Y-%m-%d')}.",
        f"> Run `uv run python scripts/generate_readme.py` to regenerate.",
    ])

    return "\n".join(lines) + "\n"


def main():
    completions = load_completions()
    if not completions:
        print("No completion files found.")
        return

    readme = generate_readme(completions)
    README_PATH.write_text(readme, encoding="utf-8")
    print(f"Generated {README_PATH}")
    print(f"  {len(completions)} completion files processed.")
    size = README_PATH.stat().st_size
    print(f"  {size} bytes written.")


if __name__ == "__main__":
    main()
