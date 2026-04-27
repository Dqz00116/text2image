from typing import TypedDict

from openai import OpenAI

from .image_utils import encode_image_to_data_url


DEFAULT_ASPECT_RATIO = "1:1"
DEFAULT_IMAGE_SIZE = "1K"


class GenerationResult(TypedDict):
    images: list[str]
    text: str | None
    model: str
    usage: dict[str, int]


class TextToImageClient:
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1",
                 model: str = "openai/gpt-5.4-image-2"):
        self.model = model
        self._client = OpenAI(base_url=base_url, api_key=api_key)

    def _build_messages(self, prompt: str, image_path: str | None = None) -> list[dict]:
        if image_path is None:
            return [{"role": "user", "content": prompt}]

        if image_path.startswith(("http://", "https://")):
            image_url = image_path
        else:
            image_url = encode_image_to_data_url(image_path)

        return [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]}]

    def _build_extra_body(self, aspect_ratio: str, image_size: str) -> dict:
        body: dict = {"modalities": ["image", "text"]}
        config = {}
        if aspect_ratio != DEFAULT_ASPECT_RATIO:
            config["aspect_ratio"] = aspect_ratio
        if image_size != DEFAULT_IMAGE_SIZE:
            config["image_size"] = image_size
        if config:
            body["image_config"] = config
        return body

    def _api_call(self, messages: list[dict], extra_body: dict):
        return self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            extra_body=extra_body,
        )

    def generate(self, prompt: str, image_path: str | None = None,
                 aspect_ratio: str = DEFAULT_ASPECT_RATIO,
                 image_size: str = DEFAULT_IMAGE_SIZE) -> GenerationResult:
        messages = self._build_messages(prompt, image_path)
        extra_body = self._build_extra_body(aspect_ratio, image_size)
        response = self._api_call(messages, extra_body)
        choice = response.choices[0]
        def _get_url(img):
            if hasattr(img, "image_url"):
                iu = img.image_url
                return iu.url if hasattr(iu, "url") else iu["url"]
            d = img["image_url"]
            return d.url if hasattr(d, "url") else d["url"]
        images = [_get_url(img) for img in (choice.message.images or [])]

        return {
            "images": images,
            "text": choice.message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }
