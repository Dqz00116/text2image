import base64
import pytest
from unittest.mock import MagicMock, patch
from src.text2image.client import TextToImageClient


@pytest.fixture
def client():
    return TextToImageClient(api_key="sk-test", base_url="https://openrouter.ai/api/v1")


class TestBuildMessages:
    def test_text_only(self, client):
        msg = client._build_messages("a beautiful sunset")
        assert isinstance(msg, list)
        assert len(msg) == 1
        assert msg[0]["role"] == "user"
        assert msg[0]["content"] == "a beautiful sunset"

    def test_text_with_image_url(self, client):
        msg = client._build_messages("make it darker", "https://example.com/cat.png")
        content = msg[0]["content"]
        assert isinstance(content, list)
        assert content[0] == {"type": "text", "text": "make it darker"}
        assert content[1] == {"type": "image_url", "image_url": {"url": "https://example.com/cat.png"}}

    def test_text_with_local_image(self, client, tmp_path):
        img = tmp_path / "cat.jpg"
        img.write_bytes(b"x")
        msg = client._build_messages("make it darker", str(img))
        assert msg[0]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")

    def test_text_with_local_image_not_found(self, client):
        with pytest.raises(FileNotFoundError):
            client._build_messages("make it darker", "/nonexistent/img.png")


class TestExtraBody:
    def test_default_no_image_config(self, client):
        body = client._build_extra_body("1:1", "1K")
        assert body == {"modalities": ["image", "text"]}

    def test_aspect_ratio_added(self, client):
        body = client._build_extra_body("16:9", "1K")
        assert body["image_config"] == {"aspect_ratio": "16:9"}

    def test_image_size_added(self, client):
        body = client._build_extra_body("1:1", "2K")
        assert body["image_config"] == {"image_size": "2K"}

    def test_both_added(self, client):
        body = client._build_extra_body("16:9", "4K")
        assert body["image_config"] == {"aspect_ratio": "16:9", "image_size": "4K"}

    def test_non_default_only(self, client):
        body = client._build_extra_body("1:1", "1K")
        assert "image_config" not in body


class TestGenerate:
    def test_extracts_image_and_usage(self, client):
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_image = MagicMock()
        mock_image.image_url.url = "data:image/png;base64,Zm9v"
        mock_choice.message.images = [mock_image]
        mock_choice.message.content = "Here is your image"
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 200
        mock_response.usage.total_tokens = 300
        mock_response.model = "openai/gpt-5.4-image-2"

        with patch.object(client, "_api_call", return_value=mock_response):
            result = client.generate("a sunset")
            assert len(result["images"]) == 1
            assert result["images"][0] == "data:image/png;base64,Zm9v"
            assert result["usage"]["prompt_tokens"] == 100
            assert result["usage"]["completion_tokens"] == 200
            assert result["usage"]["total_tokens"] == 300
            assert result["model"] == "openai/gpt-5.4-image-2"
            assert result["text"] == "Here is your image"

    def test_no_images_in_response(self, client):
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.images = []
        mock_choice.message.content = "I cannot generate that"
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch.object(client, "_api_call", return_value=mock_response):
            result = client.generate("something prohibited")
            assert result["images"] == []
            assert result["text"] == "I cannot generate that"
