import os
import sys
import click
from dotenv import load_dotenv
from src.text2image.client import TextToImageClient
from src.text2image.image_utils import decode_data_url_to_bytes


ASPECT_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
IMAGE_SIZES = ["1K", "2K", "4K"]


@click.command()
@click.option("--prompt", "-p", required=True, help="Text prompt for image generation")
@click.option("--image", "-i", default=None, help="Input image path (local file or HTTP URL)")
@click.option("--output", "-o", default="output.png", show_default=True, help="Output image file path")
@click.option("--model", default="openai/gpt-5.4-image-2", show_default=True, help="Model ID")
@click.option("--aspect-ratio", default="1:1", show_default=True,
              type=click.Choice(ASPECT_RATIOS), help="Image aspect ratio")
@click.option("--image-size", default="1K", show_default=True,
              type=click.Choice(IMAGE_SIZES), help="Image resolution")
@click.option("--api-key", default=None, help="OpenRouter API key (or set OPENROUTER_API_KEY)")
@click.option("--api-base", default="https://openrouter.ai/api/v1",
              show_default=True, help="API base URL")
def main(prompt, image, output, model, aspect_ratio, image_size, api_key, api_base):
    """Generate images using OpenRouter's GPT-5.4 Image 2 model.

    Supports text-to-image and image+text-to-image generation.

    API key priority: --api-key > OPENROUTER_API_KEY env var > .env file
    """
    load_dotenv()

    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        click.echo("Error: API key required. Use --api-key, OPENROUTER_API_KEY env var, or .env file.", err=True)
        sys.exit(1)

    click.echo(f"Generating image for prompt: {prompt}")
    if image:
        click.echo(f"Input image: {image}")

    client = TextToImageClient(api_key=api_key, base_url=api_base, model=model)

    try:
        result = client.generate(
            prompt=prompt,
            image_path=image,
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


if __name__ == "__main__":
    main()
