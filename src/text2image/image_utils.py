import base64
import mimetypes
import os


def encode_image_to_data_url(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    mime, _ = mimetypes.guess_type(path)
    if mime is None:
        if ext:
            mime = f"image/{ext.lstrip('.')}"
        else:
            mime = "image/png"

    with open(path, "rb") as f:
        data = f.read()

    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


def decode_data_url_to_bytes(data_url: str) -> bytes:
    if not data_url.startswith("data:"):
        raise ValueError(f"Invalid data URL: missing 'data:' prefix")

    header, b64 = data_url.split(",", 1)
    if ";base64" not in header:
        raise ValueError("Invalid data URL: not base64 encoded")

    return base64.b64decode(b64)
