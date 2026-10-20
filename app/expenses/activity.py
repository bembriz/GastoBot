"""Estado de actividad de extraccion en memoria (una sola app/contenedor).

Buffer circular de eventos + estado del lote en curso. No persiste: se pierde
al reiniciar la app. Suficiente para el panel de visibilidad del dashboard.
"""

import time
from collections import deque
from typing import Any

_MAX_EVENTS = 200
_events: deque[dict[str, Any]] = deque(maxlen=_MAX_EVENTS)
_state: dict[str, Any] = {
    "busy": False,
    "record_id": None,
    "filename": None,
    "started_at": None,
    "engine": None,
}
_task: Any = None


def push_event(kind: str, msg: str) -> None:
    _events.appendleft({"ts": time.strftime("%H:%M:%S"), "kind": kind, "msg": msg})


def get_events() -> list[dict[str, Any]]:
    return list(_events)


def is_busy() -> bool:
    return bool(_state["busy"])


def set_batch(record_id: str, filename: str, engine: str) -> None:
    _state.update(
        busy=True,
        record_id=record_id,
        filename=filename,
        started_at=time.monotonic(),
        engine=engine,
    )


def clear_batch() -> None:
    _state.update(busy=False, record_id=None, filename=None, started_at=None, engine=None)


def get_state() -> dict[str, Any]:
    st: dict[str, Any] = dict(_state)
    if st["busy"] and st["started_at"] is not None:
        st["elapsed_s"] = int(time.monotonic() - st["started_at"])
    else:
        st["elapsed_s"] = None
    return st


def attach_task(task: Any) -> None:
    global _task
    _task = task


def get_task() -> Any:
    return _task


def pop_task() -> Any:
    global _task
    t = _task
    _task = None
    return t
