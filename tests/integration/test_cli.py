import os
import base64
import json
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from cli import cli


MINIMAL_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYPgPAAEDAQAIicLsAAAAAElFTkSuQmCC"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-integration")


class TestGenerate:
    def test_missing_api_key(self, runner, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with patch("cli.load_dotenv"):
            result = runner.invoke(cli, ["generate", "--prompt", "a sunset"])
        assert result.exit_code == 1
        assert "API key required" in result.output

    def test_help(self, runner, mock_api_key):
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--prompt" in result.output
        assert "--image" in result.output

    def test_text_to_image(self, runner, mock_api_key, tmp_path):
        output_file = tmp_path / "out.png"

        mock_result = {
            "images": [f"data:image/png;base64,{MINIMAL_PNG_B64}"],
            "text": "Here is your sunset",
            "model": "openai/gpt-5.4-image-2",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }

        with patch("cli.TextToImageClient.generate", return_value=mock_result):
            result = runner.invoke(cli, [
                "generate",
                "--prompt", "a beautiful sunset",
                "--output", str(output_file),
            ])
            assert result.exit_code == 0
            assert "Saved:" in result.output
            assert "Tokens:" in result.output
            assert output_file.read_bytes() == base64.b64decode(MINIMAL_PNG_B64)

    def test_no_images_returned(self, runner, mock_api_key):
        mock_result = {
            "images": [],
            "text": "Cannot generate that",
            "model": "openai/gpt-5.4-image-2",
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        }

        with patch("cli.TextToImageClient.generate", return_value=mock_result):
            result = runner.invoke(cli, ["generate", "--prompt", "something bad"])
            assert result.exit_code == 1
            assert "No images returned" in result.output

    def test_api_error(self, runner, mock_api_key):
        with patch("cli.TextToImageClient.generate", side_effect=RuntimeError("API down")):
            result = runner.invoke(cli, ["generate", "--prompt", "a sunset"])
            assert result.exit_code == 1
            assert "API request failed" in result.output

    def test_api_key_from_dotenv(self, runner, tmp_path, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text("OPENROUTER_API_KEY=sk-from-dotenv")

        mock_result = {
            "images": [f"data:image/png;base64,{MINIMAL_PNG_B64}"],
            "text": "",
            "model": "openai/gpt-5.4-image-2",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

        with patch("cli.TextToImageClient.generate", return_value=mock_result), \
             patch("cli.load_dotenv") as mock_load:
            def fake_load():
                monkeypatch.setenv("OPENROUTER_API_KEY", "sk-from-dotenv")
            mock_load.side_effect = fake_load
            result = runner.invoke(cli, ["generate", "--prompt", "from env"])
            assert result.exit_code == 0

    def test_invalid_aspect_ratio(self, runner, mock_api_key):
        result = runner.invoke(cli, ["generate", "--prompt", "test", "--aspect-ratio", "99:1"])
        assert result.exit_code == 2

    def test_model_from_env(self, runner, mock_api_key, monkeypatch):
        monkeypatch.setenv("TEXT2IMAGE_MODEL", "env-model-id")
        mock_result = {
            "images": [f"data:image/png;base64,{MINIMAL_PNG_B64}"],
            "text": "",
            "model": "env-model-id",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        with patch("cli.TextToImageClient") as mock_client_cls:
            mock_client_cls.return_value.generate.return_value = mock_result
            runner.invoke(cli, ["generate", "--prompt", "test"])
            mock_client_cls.assert_called_once_with(
                api_key="sk-test-integration",
                base_url="https://openrouter.ai/api/v1",
                model="env-model-id",
            )

    def test_output_from_env(self, runner, mock_api_key, monkeypatch, tmp_path):
        monkeypatch.setenv("TEXT2IMAGE_OUTPUT", str(tmp_path / "env_out.png"))
        mock_result = {
            "images": [f"data:image/png;base64,{MINIMAL_PNG_B64}"],
            "text": "",
            "model": "test",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        with patch("cli.TextToImageClient.generate", return_value=mock_result):
            result = runner.invoke(cli, ["generate", "--prompt", "test"])
            assert result.exit_code == 0
            assert (tmp_path / "env_out.png").exists()

    def test_aspect_ratio_from_env(self, runner, mock_api_key, monkeypatch):
        monkeypatch.setenv("TEXT2IMAGE_ASPECT_RATIO", "16:9")
        mock_result = {
            "images": [f"data:image/png;base64,{MINIMAL_PNG_B64}"],
            "text": "",
            "model": "test",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        with patch("cli.TextToImageClient.generate", return_value=mock_result) as mock_gen:
            runner.invoke(cli, ["generate", "--prompt", "test"])
            call_kwargs = mock_gen.call_args[1]
            assert call_kwargs["aspect_ratio"] == "16:9"

    def test_image_size_from_env(self, runner, mock_api_key, monkeypatch):
        monkeypatch.setenv("TEXT2IMAGE_IMAGE_SIZE", "4K")
        mock_result = {
            "images": [f"data:image/png;base64,{MINIMAL_PNG_B64}"],
            "text": "",
            "model": "test",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        with patch("cli.TextToImageClient.generate", return_value=mock_result) as mock_gen:
            runner.invoke(cli, ["generate", "--prompt", "test"])
            call_kwargs = mock_gen.call_args[1]
            assert call_kwargs["image_size"] == "4K"

    def test_api_base_from_env(self, runner, mock_api_key, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_BASE", "https://custom.api/v1")
        mock_result = {
            "images": [f"data:image/png;base64,{MINIMAL_PNG_B64}"],
            "text": "",
            "model": "test",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        with patch("cli.TextToImageClient") as mock_client_cls:
            mock_client_cls.return_value.generate.return_value = mock_result
            runner.invoke(cli, ["generate", "--prompt", "test"])
            mock_client_cls.assert_called_once_with(
                api_key="sk-test-integration",
                base_url="https://custom.api/v1",
                model="openai/gpt-5.4-image-2",
            )

    def test_cli_flag_overrides_env(self, runner, mock_api_key, monkeypatch):
        monkeypatch.setenv("TEXT2IMAGE_MODEL", "env-model")
        mock_result = {
            "images": [f"data:image/png;base64,{MINIMAL_PNG_B64}"],
            "text": "",
            "model": "cli-model",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        with patch("cli.TextToImageClient") as mock_client_cls:
            mock_client_cls.return_value.generate.return_value = mock_result
            runner.invoke(cli, ["generate", "--prompt", "test", "--model", "cli-model"])
            mock_client_cls.assert_called_once_with(
                api_key="sk-test-integration",
                base_url="https://openrouter.ai/api/v1",
                model="cli-model",
            )


class TestDescribe:
    @pytest.fixture(autouse=True)
    def mock_kimi(self):
        with patch("cli.create_describer") as mock:
            yield mock

    def test_describe_default(self, runner, mock_api_key, mock_kimi, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "A watercolor painting of a cat",
            "model": "kimi",
            "backend": "kimi",
            "usage": None,
        }

        result = runner.invoke(cli, ["describe", str(img)])
        assert result.exit_code == 0
        assert "A watercolor painting of a cat" in result.output

    def test_describe_custom_prompt(self, runner, mock_api_key, mock_kimi, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "3 people",
            "model": "kimi",
            "backend": "kimi",
            "usage": None,
        }

        result = runner.invoke(cli, ["describe", str(img), "How many people?"])
        assert result.exit_code == 0
        assert "3 people" in result.output

    def test_describe_json(self, runner, mock_api_key, mock_kimi, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "Nice image",
            "model": "kimi",
            "backend": "kimi",
            "usage": None,
        }

        result = runner.invoke(cli, ["describe", str(img), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["description"] == "Nice image"
        assert data["backend"] == "kimi"

    def test_describe_openrouter_backend(self, runner, mock_api_key, mock_kimi, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "A cat",
            "model": "openai/gpt-4o",
            "backend": "openrouter",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        result = runner.invoke(cli, ["describe", str(img), "--backend", "openrouter"])
        assert result.exit_code == 0
        assert "A cat" in result.output

    def test_describe_timeout_env(self, runner, mock_api_key, mock_kimi, tmp_path, monkeypatch):
        monkeypatch.setenv("DESCRIBE_TIMEOUT", "120")
        img = tmp_path / "test.png"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "ok",
            "model": "kimi",
            "backend": "kimi",
            "usage": None,
        }

        result = runner.invoke(cli, ["describe", str(img)])
        assert result.exit_code == 0

    def test_top_level_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "generate" in result.output
        assert "describe" in result.output

    def test_vision_model_from_env(self, runner, mock_api_key, mock_kimi, tmp_path, monkeypatch):
        monkeypatch.setenv("DESCRIBE_VISION_MODEL", "anthropic/claude-sonnet-4")
        monkeypatch.setenv("DESCRIBE_BACKEND", "openrouter")
        img = tmp_path / "test.png"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "ok",
            "model": "anthropic/claude-sonnet-4",
            "backend": "openrouter",
            "usage": None,
        }

        runner.invoke(cli, ["describe", str(img)])
        mock_kimi.assert_called_once()
        call_kwargs = mock_kimi.call_args[1]
        assert call_kwargs["model"] == "anthropic/claude-sonnet-4"

    def test_backend_from_env(self, runner, mock_api_key, mock_kimi, tmp_path, monkeypatch):
        monkeypatch.setenv("DESCRIBE_BACKEND", "openrouter")
        img = tmp_path / "test.png"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "ok",
            "model": "moonshotai/kimi-k2.5",
            "backend": "openrouter",
            "usage": None,
        }

        runner.invoke(cli, ["describe", str(img)])
        mock_kimi.assert_called_with("openrouter", api_key="sk-test-integration",
                                     model="moonshotai/kimi-k2.5",
                                     base_url="https://openrouter.ai/api/v1")

    def test_default_prompt_from_env(self, runner, mock_api_key, mock_kimi, tmp_path, monkeypatch):
        monkeypatch.setenv("DESCRIBE_DEFAULT_PROMPT", "Custom default question?")
        img = tmp_path / "test.png"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "answer",
            "model": "kimi",
            "backend": "kimi",
            "usage": None,
        }

        runner.invoke(cli, ["describe", str(img)])
        call_args = mock_describer.describe.call_args[0]
        assert call_args[1] == "Custom default question?"

    def test_cli_prompt_overrides_env_prompt(self, runner, mock_api_key, mock_kimi, tmp_path, monkeypatch):
        monkeypatch.setenv("DESCRIBE_DEFAULT_PROMPT", "Env prompt")
        img = tmp_path / "test.png"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "ok",
            "model": "kimi",
            "backend": "kimi",
            "usage": None,
        }

        runner.invoke(cli, ["describe", str(img), "CLI prompt"])
        call_args = mock_describer.describe.call_args[0]
        assert call_args[1] == "CLI prompt"

    def test_api_base_shared_between_commands(self, runner, mock_api_key, mock_kimi, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_BASE", "https://shared.api/v1")
        monkeypatch.setenv("DESCRIBE_BACKEND", "openrouter")
        img = tmp_path / "test.png"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "ok",
            "model": "moonshotai/kimi-k2.5",
            "backend": "openrouter",
            "usage": None,
        }

        runner.invoke(cli, ["describe", str(img)])
        mock_kimi.assert_called_with("openrouter", api_key="sk-test-integration",
                                     model="moonshotai/kimi-k2.5",
                                     base_url="https://shared.api/v1")

    def test_kimi_python_from_env(self, runner, mock_api_key, mock_kimi, tmp_path, monkeypatch):
        monkeypatch.setenv("KIMI_PYTHON", "3.12")
        img = tmp_path / "test.png"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "ok",
            "model": "kimi",
            "backend": "kimi",
            "usage": None,
        }

        runner.invoke(cli, ["describe", str(img)])
        mock_kimi.assert_called_with("kimi", kimi_path="kimi", timeout=120, python_path="3.12")

    def test_kimi_python_cli_flag(self, runner, mock_api_key, mock_kimi, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"fake")

        mock_describer = mock_kimi.return_value
        mock_describer.describe.return_value = {
            "description": "ok",
            "model": "kimi",
            "backend": "kimi",
            "usage": None,
        }

        runner.invoke(cli, ["describe", str(img), "--kimi-python", "3.12"])
        mock_kimi.assert_called_with("kimi", kimi_path="kimi", timeout=120, python_path="3.12")
