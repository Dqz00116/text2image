import pytest
from unittest.mock import MagicMock, patch
from src.text2image.describer import (
    DescribeResult,
    ImageDescriber,
    KimiCodeDescriber,
    OpenRouterVisionDescriber,
    create_describer,
)


class TestDescribeResult:
    def test_describe_result_shape(self):
        result: DescribeResult = {
            "description": "A painting of a cat",
            "model": "kimi",
            "backend": "kimi",
            "usage": None,
        }
        assert result["description"] == "A painting of a cat"
        assert result["backend"] == "kimi"


class TestKimiCodeDescriber:
    @pytest.fixture
    def describer(self):
        return KimiCodeDescriber(kimi_path="kimi", timeout=30)

    def test_describe_returns_result(self, describer):
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "A watercolor painting of a cat"
        with patch("subprocess.run", return_value=mock) as run_mock:
            result = describer.describe("/tmp/cat.png", "Describe this image")
            assert result["description"] == "A watercolor painting of a cat"
            assert result["backend"] == "kimi"
            assert result["model"] == "kimi"
            assert result["usage"] is None
            run_mock.assert_called_once()
            args = run_mock.call_args[0][0]
            assert args[:3] == ["kimi", "--print", "--final-message-only"]

    def test_describe_custom_prompt(self, describer):
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "3 people"
        with patch("subprocess.run", return_value=mock) as run_mock:
            result = describer.describe("/tmp/photo.jpg", "How many people?")
            assert result["description"] == "3 people"
            full_cmd = " ".join(run_mock.call_args[0][0])
            assert "How many people?" in full_cmd

    def test_exit_code_1_raises(self, describer):
        mock = MagicMock()
        mock.returncode = 1
        mock.stderr = "API key not configured"
        mock.stdout = ""
        with patch("subprocess.run", return_value=mock):
            with pytest.raises(RuntimeError, match="Kimi-Code exited with code 1"):
                describer.describe("/tmp/img.png", "desc")

    def test_exit_code_75_raises_retryable(self, describer):
        mock = MagicMock()
        mock.returncode = 75
        mock.stderr = "rate limited"
        mock.stdout = ""
        with patch("subprocess.run", return_value=mock):
            with pytest.raises(RuntimeError, match="retryable"):
                describer.describe("/tmp/img.png", "desc")

    def test_timeout_raises(self, describer):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="kimi", timeout=30)):
            with pytest.raises(TimeoutError, match="timed out"):
                describer.describe("/tmp/img.png", "desc")

    def test_kimi_not_found(self, describer):
        with patch("subprocess.run", side_effect=FileNotFoundError("kimi")):
            with pytest.raises(RuntimeError, match="Kimi-Code not found"):
                describer.describe("/tmp/img.png", "desc")

    def test_uses_kimi_path_env(self):
        describer = KimiCodeDescriber(kimi_path="/usr/local/bin/kimi", timeout=30)
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "ok"
        with patch("subprocess.run", return_value=mock) as run_mock:
            describer.describe("/tmp/img.png", "desc")
            assert run_mock.call_args[0][0][0] == "/usr/local/bin/kimi"

    def test_uses_python_path_via_uv(self):
        describer = KimiCodeDescriber(python_path="3.12", timeout=30)
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "ok"
        with patch("subprocess.run", return_value=mock) as run_mock:
            describer.describe("/tmp/img.png", "desc")
            cmd = run_mock.call_args[0][0]
            assert cmd[:6] == ["uv", "run", "--python", "3.12", "--no-project", "kimi"]
            assert cmd[6:] == ["--print", "--final-message-only", "-p", cmd[-1]]

    def test_python_path_with_custom_kimi_path(self):
        describer = KimiCodeDescriber(kimi_path="/custom/kimi", python_path="3.12", timeout=30)
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "ok"
        with patch("subprocess.run", return_value=mock) as run_mock:
            describer.describe("/tmp/img.png", "desc")
            cmd = run_mock.call_args[0][0]
            assert cmd[0:6] == ["uv", "run", "--python", "3.12", "--no-project", "/custom/kimi"]


class TestOpenRouterVisionDescriber:
    @pytest.fixture
    def describer(self):
        return OpenRouterVisionDescriber(
            api_key="sk-test",
            base_url="https://openrouter.ai/api/v1",
            model="openai/gpt-4o",
        )

    def test_describe_returns_result(self, describer, tmp_path):
        img = tmp_path / "cat.png"
        img.write_bytes(b"fake")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "A beautiful cat painting"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 30
        mock_response.usage.total_tokens = 80
        mock_response.model = "openai/gpt-4o"

        with patch.object(describer._client.chat.completions, "create", return_value=mock_response) as create_mock:
            result = describer.describe(str(img), "Describe this")
            assert result["description"] == "A beautiful cat painting"
            assert result["backend"] == "openrouter"
            assert result["model"] == "openai/gpt-4o"
            assert result["usage"]["prompt_tokens"] == 50
            create_mock.assert_called_once()

    def test_messages_include_image_data_url(self, describer, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"fake-image-data")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "nice"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch.object(describer._client.chat.completions, "create", return_value=mock_response) as create_mock:
            describer.describe(str(img), "What is this?")
            call_args = create_mock.call_args[1]
            messages = call_args["messages"]
            content = messages[0]["content"]
            assert content[0] == {"type": "text", "text": "What is this?"}
            assert content[1]["type"] == "image_url"
            assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")

    def test_http_url_passed_through(self, describer):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "a cat"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch.object(describer._client.chat.completions, "create", return_value=mock_response) as create_mock:
            describer.describe("https://example.com/photo.jpg", "Describe")
            call_args = create_mock.call_args[1]
            image_url = call_args["messages"][0]["content"][1]["image_url"]["url"]
            assert image_url == "https://example.com/photo.jpg"


class TestCreateDescriber:
    def test_returns_kimi_describer(self):
        d = create_describer("kimi", kimi_path="kimi", timeout=60)
        assert isinstance(d, KimiCodeDescriber)
        assert d._python_path is None

    def test_returns_kimi_describer_with_python_path(self):
        d = create_describer("kimi", kimi_path="kimi", timeout=60, python_path="3.12")
        assert isinstance(d, KimiCodeDescriber)
        assert d._python_path == "3.12"

    def test_returns_openrouter_describer(self):
        d = create_describer("openrouter", api_key="sk-test")
        assert isinstance(d, OpenRouterVisionDescriber)

    def test_invalid_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown backend"):
            create_describer("invalid")  # type: ignore
