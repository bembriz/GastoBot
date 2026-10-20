"""Tests del buffer de actividad en memoria."""

import time

from app.expenses import activity


def setup_function():
    activity.clear_batch()
    activity.get_events().clear()


def test_push_event_respects_maxlen():
    for i in range(250):
        activity.push_event("info", f"msg{i}")
    events = activity.get_events()
    assert len(events) <= 200
    assert events[0]["msg"] == "msg249"  # mas reciente primero


def test_batch_state_lifecycle():
    assert activity.is_busy() is False
    activity.set_batch("rec-1", "foto.jpg", "gemini")
    assert activity.is_busy() is True
    st = activity.get_state()
    assert st["busy"] is True and st["engine"] == "gemini" and st["filename"] == "foto.jpg"
    assert st["elapsed_s"] >= 0
    activity.clear_batch()
    assert activity.is_busy() is False
    assert activity.get_state()["record_id"] is None


def test_events_order_newest_first():
    activity.push_event("a", "uno")
    time.sleep(0.01)
    activity.push_event("b", "dos")
    ev = activity.get_events()
    assert ev[0]["msg"] == "dos" and ev[1]["msg"] == "uno"
