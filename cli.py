import os
import json
import sys
import click
from dotenv import load_dotenv
from src.text2image.client import TextToImageClient
from src.text2image.describer import create_describer
from src.text2image.image_utils import decode_data_url_to_bytes


ASPECT_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
IMAGE_SIZES = ["1K", "2K", "4K"]


@click.group()
def cli():
    """Text-to-image generation and image description using OpenRouter API."""
    pass


@cli.command("generate")
@click.option("--prompt", "-p", required=True, help="Text prompt for image generation")
@click.option("--image", "-i", multiple=True, help="Input image path (local file or HTTP URL). Repeat for multiple images.")
@click.option("--output", "-o", default=None, help="Output image file path (env: TEXT2IMAGE_OUTPUT)")
@click.option("--model", default=None, help="Model ID (env: TEXT2IMAGE_MODEL)")
@click.option("--aspect-ratio", default=None,
              type=click.Choice(ASPECT_RATIOS), help="Image aspect ratio (env: TEXT2IMAGE_ASPECT_RATIO)")
@click.option("--image-size", default=None,
              type=click.Choice(IMAGE_SIZES), help="Image resolution (env: TEXT2IMAGE_IMAGE_SIZE)")
@click.option("--api-key", default=None, help="OpenRouter API key (env: OPENROUTER_API_KEY)")
@click.option("--api-base", default=None, help="API base URL (env: OPENROUTER_API_BASE)")
def generate(prompt, image, output, model, aspect_ratio, image_size, api_key, api_base):
    """Generate images using OpenRouter's GPT-5.4 Image 2 model.

    Supports text-to-image and image+text-to-image generation.
    Use -i multiple times for multiple input images.

    All options with defaults can be configured via environment variables or .env file.
    """
    load_dotenv()

    output = output or os.environ.get("TEXT2IMAGE_OUTPUT", "output.png")
    model = model or os.environ.get("TEXT2IMAGE_MODEL", "openai/gpt-5.4-image-2")
    aspect_ratio = aspect_ratio or os.environ.get("TEXT2IMAGE_ASPECT_RATIO", "1:1")
    image_size = image_size or os.environ.get("TEXT2IMAGE_IMAGE_SIZE", "1K")
    api_base = api_base or os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        click.echo("Error: API key required. Use --api-key, OPENROUTER_API_KEY env var, or .env file.", err=True)
        sys.exit(1)

    image_paths = list(image) if image else None

    click.echo(f"Generating image for prompt: {prompt}")
    if image_paths:
        click.echo(f"Input images: {len(image_paths)}")

    client = TextToImageClient(api_key=api_key, base_url=api_base, model=model)

    try:
        result = client.generate(
            prompt=prompt,
            image_paths=image_paths,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )
    except Exception as e:
        click.echo(f"Error: API request failed: {e}", err=True)
        sys.exit(1)

    if not result["images"]:
        click.echo("Error: No images returned in response.", err=True)
        if result["text"]:
            click.echo(f"Model response: {result['text']}", err=True)
        sys.exit(1)

    image_data_url = result["images"][0]
    image_bytes = decode_data_url_to_bytes(image_data_url)

    output_dir = os.path.dirname(output) or "."
    os.makedirs(output_dir, exist_ok=True)

    with open(output, "wb") as f:
        f.write(image_bytes)

    click.echo(f"Saved: {output}")
    click.echo(f"Model: {result['model']}")
    usage = result["usage"]
    click.echo(f"Tokens: {usage['prompt_tokens']} prompt + {usage['completion_tokens']} completion "
               f"= {usage['total_tokens']} total")

    if result["text"]:
        click.echo(f"Response text: {result['text']}")


@cli.command("describe")
@click.argument("image")
@click.argument("prompt", required=False)
@click.option("--backend", type=click.Choice(["kimi", "openrouter"]), default=None,
              help="Vision backend (env: DESCRIBE_BACKEND)")
@click.option("--timeout", type=int, default=None, help="Timeout in seconds (env: DESCRIBE_TIMEOUT)")
@click.option("--json", "json_output", is_flag=True, help="Output as structured JSON")
@click.option("--api-key", default=None, help="OpenRouter API key (openrouter backend, env: OPENROUTER_API_KEY)")
@click.option("--vision-model", default=None, help="Vision model (openrouter backend, env: DESCRIBE_VISION_MODEL)")
@click.option("--api-base", default=None, help="API base URL (env: OPENROUTER_API_BASE)")
@click.option("--kimi-path", default=None, help="Path to kimi executable (env: KIMI_PATH)")
@click.option("--kimi-python", default=None, help="Python version for kimi via uv (env: KIMI_PYTHON)")
def describe(image, prompt, backend, timeout, json_output, api_key, vision_model, api_base, kimi_path, kimi_python):
    """Describe an image using a vision-capable backend.

    IMAGE is the path to the image file (local or HTTP URL).
    PROMPT is an optional question about the image.

    All options with defaults can be configured via environment variables or .env file.
    """
    load_dotenv()

    backend = backend or os.environ.get("DESCRIBE_BACKEND", "kimi")
    api_base = api_base or os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")

    if timeout is None:
        timeout_str = os.environ.get("DESCRIBE_TIMEOUT")
        timeout = int(timeout_str) if timeout_str else 60

    if kimi_path is None:
        kimi_path = os.environ.get("KIMI_PATH", "kimi")

    if kimi_python is None:
        kimi_python = os.environ.get("KIMI_PYTHON")

    if vision_model is None:
        vision_model = os.environ.get("DESCRIBE_VISION_MODEL", "moonshotai/kimi-k2.5")

    if prompt is None:
        prompt = os.environ.get("DESCRIBE_DEFAULT_PROMPT",
                                "Please describe this image in detail, focusing on style, composition, colors, subjects, and mood.")

    try:
        if backend == "kimi":
            describer = create_describer("kimi", kimi_path=kimi_path, timeout=timeout, python_path=kimi_python)
        else:
            api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
            if not api_key:
                click.echo("Error: API key required for openrouter backend. Use --api-key or OPENROUTER_API_KEY.", err=True)
                sys.exit(1)
            describer = create_describer("openrouter", api_key=api_key, model=vision_model, base_url=api_base)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    try:
        result = describer.describe(image, prompt)
    except TimeoutError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(result, ensure_ascii=False))
    else:
        click.echo(result["description"])


if __name__ == "__main__":
    cli()
