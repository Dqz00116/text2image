import os
import base64
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from cli import main


MINIMAL_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYPgPAAEDAQAIicLsAAAAAElFTkSuQmCC"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-integration")


def test_missing_api_key(runner, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with patch("cli.load_dotenv"):
        result = runner.invoke(main, ["--prompt", "a sunset"])
    assert result.exit_code == 1
    assert "API key required" in result.output


def test_help(runner, mock_api_key):
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "--prompt" in result.output
    assert "--image" in result.output


def test_text_to_image(runner, mock_api_key, tmp_path):
    output_file = tmp_path / "out.png"

    mock_result = {
        "images": [f"data:image/png;base64,{MINIMAL_PNG_B64}"],
        "text": "Here is your sunset",
        "model": "openai/gpt-5.4-image-2",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }

    with patch("cli.TextToImageClient.generate", return_value=mock_result):
        result = runner.invoke(main, [
            "--prompt", "a beautiful sunset",
            "--output", str(output_file),
        ])
        assert result.exit_code == 0
        assert "Saved:" in result.output
        assert "Tokens:" in result.output
        assert output_file.read_bytes() == base64.b64decode(MINIMAL_PNG_B64)


def test_no_images_returned(runner, mock_api_key):
    mock_result = {
        "images": [],
        "text": "Cannot generate that",
        "model": "openai/gpt-5.4-image-2",
        "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
    }

    with patch("cli.TextToImageClient.generate", return_value=mock_result):
        result = runner.invoke(main, ["--prompt", "something bad"])
        assert result.exit_code == 1
        assert "No images returned" in result.output


def test_api_error(runner, mock_api_key):
    with patch("cli.TextToImageClient.generate", side_effect=RuntimeError("API down")):
        result = runner.invoke(main, ["--prompt", "a sunset"])
        assert result.exit_code == 1
        assert "API request failed" in result.output


def test_api_key_from_dotenv(runner, tmp_path, monkeypatch):
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
        result = runner.invoke(main, ["--prompt", "from env"])
        assert result.exit_code == 0


def test_invalid_aspect_ratio(runner, mock_api_key):
    result = runner.invoke(main, ["--prompt", "test", "--aspect-ratio", "99:1"])
    assert result.exit_code == 2  # click exits with 2 for invalid choice
