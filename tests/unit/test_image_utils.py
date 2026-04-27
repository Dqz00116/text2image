import base64
import os
import pytest
from src.text2image.image_utils import encode_image_to_data_url, decode_data_url_to_bytes


# Minimal valid PNG — 1x1 red pixel
MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYPgPAAEDAQAIicLsAAAAAElFTkSuQmCC"
)


@pytest.fixture
def test_image_path(tmp_path):
    img = tmp_path / "test.png"
    img.write_bytes(MINIMAL_PNG)
    return str(img)


def test_encode_image_to_data_url_png(test_image_path):
    url = encode_image_to_data_url(test_image_path)
    assert url.startswith("data:image/png;base64,")
    decoded = base64.b64decode(url.split(",", 1)[1])
    assert decoded == MINIMAL_PNG


def test_encode_image_jpeg(tmp_path):
    img = tmp_path / "test.jpg"
    img.write_bytes(MINIMAL_PNG)  # content doesn't matter for MIME
    url = encode_image_to_data_url(str(img))
    assert url.startswith("data:image/jpeg;base64,")


def test_encode_image_not_found():
    with pytest.raises(FileNotFoundError):
        encode_image_to_data_url("nonexistent.png")


def test_encode_image_unknown_extension(tmp_path):
    img = tmp_path / "test.bmp"
    img.write_bytes(MINIMAL_PNG)
    url = encode_image_to_data_url(str(img))
    assert url.startswith("data:image/bmp;base64,")


def test_decode_data_url_to_bytes():
    b64 = base64.b64encode(MINIMAL_PNG).decode("ascii")
    url = f"data:image/png;base64,{b64}"
    result = decode_data_url_to_bytes(url)
    assert result == MINIMAL_PNG


def test_decode_data_url_missing_header():
    with pytest.raises(ValueError, match="Invalid data URL"):
        decode_data_url_to_bytes("not-a-data-url")


def test_round_trip(test_image_path):
    url = encode_image_to_data_url(test_image_path)
    result = decode_data_url_to_bytes(url)
    assert result == MINIMAL_PNG
