"""
Crash scenario: CLI _load_image produces malformed multimodal content.
If the content list doesn't match Section 3.1 format, modules/generate()
will crash when parsing content parts.
"""
import base64
import os
import tempfile
import pytest
from cli import _load_image


class TestCliLoadImage:
    def test_load_jpeg(self):
        """_load_image returns a list with image_url content part for JPEG."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0test-jpeg-data")
            path = f.name
        try:
            result = _load_image(path)
            assert isinstance(result, list)
            assert len(result) == 1
            part = result[0]
            assert part["type"] == "image_url"
            assert part["image_url"]["url"].startswith("data:image/jpeg;base64,")
            # Verify base64 round-trip
            b64_data = part["image_url"]["url"].split(",", 1)[1]
            decoded = base64.b64decode(b64_data)
            assert decoded == b"\xff\xd8\xff\xe0test-jpeg-data"
        finally:
            os.unlink(path)

    def test_load_png(self):
        """_load_image returns correct MIME for PNG."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n")
            path = f.name
        try:
            result = _load_image(path)
            assert result[0]["image_url"]["url"].startswith("data:image/png;base64,")
        finally:
            os.unlink(path)

    def test_load_nonexistent_file_raises(self):
        """_load_image must raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            _load_image("/nonexistent/path/image.jpg")
