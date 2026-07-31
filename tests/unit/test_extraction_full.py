from unittest.mock import MagicMock, mock_open, patch

from app.expenses.extraction import (
    _guess_mime,
    extract_from_image,
)


class TestGuessMime:
    def test_jpg_returns_jpeg(self):
        assert _guess_mime("photo.jpg") == "image/jpeg"

    def test_jpeg_returns_jpeg(self):
        assert _guess_mime("photo.jpeg") == "image/jpeg"

    def test_png_returns_png(self):
        assert _guess_mime("photo.png") == "image/png"

    def test_webp_returns_webp(self):
        assert _guess_mime("photo.webp") == "image/webp"

    def test_unknown_returns_jpeg(self):
        assert _guess_mime("photo.bmp") == "image/jpeg"


def _build_genai_mock(response_text: str) -> MagicMock:
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    mock_genai = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_google = MagicMock()
    mock_google.genai = mock_genai
    return mock_google


class TestExtractFromImage:
    async def test_no_keys_returns_error(self, monkeypatch):
        from app.expenses import extraction

        monkeypatch.setattr(extraction, "GEMINI_API_KEYS", [])
        monkeypatch.setattr(extraction, "KIMI_API_KEY", "")

        result = await extract_from_image("/fake/path.jpg")
        assert result["is_valid_json"] is False
        assert "configurad" in result.get("error_message", "")

    async def test_file_not_found(self, monkeypatch):
        from app.expenses import extraction

        monkeypatch.setattr(extraction, "GEMINI_API_KEYS", ["fake-key"])
        monkeypatch.setattr(extraction, "KIMI_API_KEY", "")

        result = await extract_from_image("/nonexistent/path.jpg")
        assert result["error_message"] is not None

    async def test_gemini_invalid_json(self, monkeypatch):
        from app.expenses import extraction

        mock_google = _build_genai_mock("Not valid JSON here")
        fake_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        monkeypatch.setattr(extraction, "GEMINI_API_KEYS", ["fake-key"])
        monkeypatch.setattr(extraction, "KIMI_API_KEY", "")

        with (
            patch("builtins.open", mock_open(read_data=fake_data)),
            patch.dict("sys.modules", {"google": mock_google}),
        ):
            result = await extract_from_image("/fake/path.png")

        assert result["is_valid_json"] is False

    async def test_successful_extraction(self, monkeypatch):
        from app.expenses import extraction

        response_text = (
            '{"transaction_date": "2026-01-15", "amount": 1500.50, '
            '"ticket_description": "Compra super", "bank": "BBVA", '
            '"transaction_type": "Credito"}'
        )
        mock_google = _build_genai_mock(response_text)
        fake_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        monkeypatch.setattr(extraction, "GEMINI_API_KEYS", ["fake-key"])
        monkeypatch.setattr(extraction, "KIMI_API_KEY", "")

        with (
            patch("builtins.open", mock_open(read_data=fake_data)),
            patch.dict("sys.modules", {"google": mock_google}),
        ):
            result = await extract_from_image("/fake/path.jpg")

        assert result["is_valid_json"] is True
        assert result["parsed_json"]["bank"] == "BBVA"
        assert result["parsed_json"]["amount"] == 1500.50

    async def test_extraction_with_confidence(self, monkeypatch):
        from app.expenses import extraction

        response_text = (
            '{"transaction_date": "2026-03-10", "amount": 500, '
            '"ticket_description": "Gasolina", "bank": "SANTANDER", '
            '"transaction_type": "Transferencia", '
            '"confidence": {"amount": 0.9, "bank": 0.7}}'
        )
        mock_google = _build_genai_mock(response_text)
        fake_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        monkeypatch.setattr(extraction, "GEMINI_API_KEYS", ["fake-key"])
        monkeypatch.setattr(extraction, "KIMI_API_KEY", "")

        with (
            patch("builtins.open", mock_open(read_data=fake_data)),
            patch.dict("sys.modules", {"google": mock_google}),
        ):
            result = await extract_from_image("/fake/path.jpg")

        assert result["is_valid_json"] is True
        assert result["parsed_json"]["confidence"]["amount"] == 0.9
