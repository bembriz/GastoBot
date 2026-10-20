"""Tests de seleccion de motor y eventos en la extraccion."""

from unittest.mock import AsyncMock, patch

from app.expenses import extraction


async def test_gemini_only_no_kimi_fallback(monkeypatch):
    monkeypatch.setattr(extraction, "GEMINI_API_KEYS", ["k1"])
    monkeypatch.setattr(extraction, "KIMI_API_KEY", "should-not-be-used")
    events: list[str] = []
    gemini_error = Exception("503 UNAVAILABLE high demand")
    with (
        patch.object(extraction, "_gemini_extract", AsyncMock(side_effect=gemini_error)),
        patch.object(extraction, "_kimi_extract", AsyncMock()) as kimi,
    ):
        res = await extraction.extract_from_image(
            "x.jpg", preferred_engine="gemini", on_event=events.append
        )
    kimi.assert_not_called()
    assert res["engine"] is None
    assert res["error_message"]
    assert any("503" in e for e in events)


async def test_kimi_only(monkeypatch):
    monkeypatch.setattr(extraction, "KIMI_API_KEY", "k")
    monkeypatch.setattr(extraction, "KIMI_MODEL", "kimi-k2.6")
    ok = {"raw_response": "{}", "engine": "kimi", "error_message": None}
    with (
        patch.object(extraction, "_kimi_extract", AsyncMock(return_value=ok)),
        patch.object(extraction, "_gemini_extract", AsyncMock()) as gem,
    ):
        res = await extraction.extract_from_image("x.jpg", preferred_engine="kimi")
    gem.assert_not_called()
    assert res["engine"] == "kimi"


async def test_none_engine_keeps_fallback(monkeypatch):
    monkeypatch.setattr(extraction, "GEMINI_API_KEYS", ["k1"])
    monkeypatch.setattr(extraction, "KIMI_API_KEY", "k")
    ok_kimi = {"raw_response": '{"a":1}', "engine": "kimi", "error_message": None}
    quota_error = Exception("RESOURCE_EXHAUSTED 429")
    with (
        patch.object(extraction, "_gemini_extract", AsyncMock(side_effect=quota_error)),
        patch.object(extraction, "_kimi_extract", AsyncMock(return_value=ok_kimi)),
    ):
        res = await extraction.extract_from_image("x.jpg", preferred_engine=None)
    assert res["engine"] == "kimi"
