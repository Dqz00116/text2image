import os
import subprocess
from abc import ABC, abstractmethod
from typing import TypedDict

from openai import OpenAI

from .image_utils import encode_image_to_data_url


class DescribeResult(TypedDict):
    description: str
    model: str
    backend: str
    usage: dict[str, int] | None


class ImageDescriber(ABC):
    @abstractmethod
    def describe(self, image_path: str, prompt: str) -> DescribeResult:
        ...


class KimiCodeDescriber(ImageDescriber):
    def __init__(self, kimi_path: str = "kimi", timeout: int = 60,
                 python_path: str | None = None):
        self._kimi_path = kimi_path
        self._timeout = timeout
        self._python_path = python_path

    def describe(self, image_path: str, prompt: str) -> DescribeResult:
        full_prompt = f"{prompt}\n\nImage to analyze: {image_path}"
        if self._python_path:
            cmd = ["uv", "run", "--python", self._python_path, "--no-project",
                   self._kimi_path, "--print", "--final-message-only", "-p", full_prompt]
        else:
            cmd = [self._kimi_path, "--print", "--final-message-only", "-p", full_prompt]
        env = None
        if self._python_path:
            env = os.environ.copy()
            env.pop("VIRTUAL_ENV", None)
            env.pop("PYTHONHOME", None)
            env.pop("UV_INTERNAL__PYTHONHOME", None)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                env=env,
            )
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Kimi-Code timed out after {self._timeout}s")
        except FileNotFoundError:
            raise RuntimeError("Kimi-Code not found. Install it or set KIMI_PATH env var.")

        if proc.returncode == 1:
            raise RuntimeError(f"Kimi-Code exited with code 1: {proc.stderr.strip()}")
        if proc.returncode == 75:
            raise RuntimeError(f"Kimi-Code retryable error (code 75): {proc.stderr.strip()}")

        if proc.returncode != 0:
            raise RuntimeError(f"Kimi-Code exited with code {proc.returncode}: {proc.stderr.strip()}")

        return DescribeResult(
            description=proc.stdout.strip(),
            model="kimi",
            backend="kimi",
            usage=None,
        )


class OpenRouterVisionDescriber(ImageDescriber):
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1",
                 model: str = "moonshotai/kimi-k2.5"):
        self._model = model
        self._client = OpenAI(base_url=base_url, api_key=api_key)

    def describe(self, image_path: str, prompt: str) -> DescribeResult:
        if image_path.startswith(("http://", "https://")):
            image_url = image_path
        else:
            image_url = encode_image_to_data_url(image_path)

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }]

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
        )

        choice = response.choices[0]
        return DescribeResult(
            description=choice.message.content or "",
            model=response.model or self._model,
            backend="openrouter",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            } if response.usage else None,
        )


def create_describer(backend: str, **kwargs) -> ImageDescriber:
    if backend == "kimi":
        return KimiCodeDescriber(
            kimi_path=kwargs.get("kimi_path", "kimi"),
            timeout=kwargs.get("timeout", 60),
            python_path=kwargs.get("python_path"),
        )
    elif backend == "openrouter":
        return OpenRouterVisionDescriber(
            api_key=kwargs["api_key"],
            base_url=kwargs.get("base_url", "https://openrouter.ai/api/v1"),
            model=kwargs.get("model", "moonshotai/kimi-k2.5"),
        )
    else:
        raise ValueError(f"Unknown backend: {backend}")
