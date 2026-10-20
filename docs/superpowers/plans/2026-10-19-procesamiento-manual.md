# Procesamiento manual, selección de motor y visibilidad — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dashboard con botón "Procesar imágenes" + drop de motor (Gemini/Kimi), panel de actividad en vivo (incl. errores 503), y capacidad de detener un lote para cambiar de motor. Sin auto-procesado.

**Architecture:** El worker automático se reemplaza por un "batch runner" lanzado por `POST /expenses/process`, que reutiliza `claim_next_job` (FIFO + SKIP LOCKED, R008 intacto) en un bucle acotado. Un `asyncio.Lock` rechaza lotes concurrentes; `POST /expenses/stop` cancela el `asyncio.Task`. Gemini se cambia al cliente async real (`client.aio.models`) con timeout por intento, lo que además deja de congelar la app. Log de actividad = `deque` en memoria.

**Tech Stack:** FastAPI, SQLAlchemy async, Jinja/HTMX, `google-genai` 2.15.0 (`client.aio.models.generate_content` + `HttpOptions(timeout=...)`), pytest.

## Global Constraints

- Rama: `feature/procesamiento-manual-y-visibilidad` (ya creada desde `0d6970d`).
- Sin secretos en código (R001/R005): todo por env `GASTOSIA_*`. No hardcodear claves.
- `uv` exclusivo (R010). Cobertura ≥60% (R007). Un solo `ANALIZANDO` a la vez (R008).
- Tests sin invocar IA real (mockear `extract_from_image` / `_gemini_extract` / `_kimi_extract`). NUNCA llamar a Gemini ni Kimi real en tests.
- **ANTES de correr tests O commitear:** `set -a; source /tmp/gastosia-test-env.sh; set +a` (apunta al local-postgres-lab en 127.0.0.1:5434, bd gastos_ia_opencode_delete_test). El hook pre-commit hereda estos env y corre la suite completa.
- Commits solo con GATE del usuario (R002). El flujo SDD maneja la autorización.
- No desplegar a lenovosrv en esta fase. No crear dockers nuevos.

---

### Task 0: Base de rama + commit de PROGRESS.md

**Completado** por el controlador: commit `ffd37a4` en `feature/procesamiento-manual-y-visibilidad`.

---

### Task 1: Extracción async + timeout + motor preferido + eventos

**Files:**
- Modify: `app/expenses/extraction.py`
- Test: `tests/unit/test_extraction_engine.py` (create)

**Interfaces:**
- Consumes: ninguna previa.
- Produces: `extract_from_image(image_path: str, preferred_engine: str | None = None, on_event: Callable[[str], None] | None = None) -> dict` — misma forma de retorno actual (`raw_response`, `parsed_json`, `is_valid_json`, `elapsed_ms`, `error_message`, `engine`).

- [ ] **Step 1: Write failing tests** (`tests/unit/test_extraction_engine.py`):

```python
"""Tests de seleccion de motor y eventos en la extraccion."""

import pytest
from unittest.mock import AsyncMock, patch

from app.expenses import extraction


async def test_gemini_only_no_kimi_fallback(monkeypatch):
    monkeypatch.setattr(extraction, "GEMINI_API_KEYS", ["k1"])
    monkeypatch.setattr(extraction, "KIMI_API_KEY", "should-not-be-used")
    events: list[str] = []
    with patch.object(
        extraction,
        "_gemini_extract",
        AsyncMock(side_effect=Exception("503 UNAVAILABLE high demand")),
    ):
        with patch.object(extraction, "_kimi_extract", AsyncMock()) as kimi:
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
    with patch.object(extraction, "_kimi_extract", AsyncMock(return_value=ok)):
        with patch.object(extraction, "_gemini_extract", AsyncMock()) as gem:
            res = await extraction.extract_from_image("x.jpg", preferred_engine="kimi")
    gem.assert_not_called()
    assert res["engine"] == "kimi"


async def test_none_engine_keeps_fallback(monkeypatch):
    monkeypatch.setattr(extraction, "GEMINI_API_KEYS", ["k1"])
    monkeypatch.setattr(extraction, "KIMI_API_KEY", "k")
    ok_kimi = {"raw_response": '{"a":1}', "engine": "kimi", "error_message": None}
    with patch.object(
        extraction, "_gemini_extract", AsyncMock(side_effect=Exception("RESOURCE_EXHAUSTED 429"))
    ):
        with patch.object(extraction, "_kimi_extract", AsyncMock(return_value=ok_kimi)):
            res = await extraction.extract_from_image("x.jpg", preferred_engine=None)
    assert res["engine"] == "kimi"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `set -a; source /tmp/gastosia-test-env.sh; set +a; uv run pytest tests/unit/test_extraction_engine.py -v`
Expected: FAIL (TypeError: unexpected keyword argument 'preferred_engine')

- [ ] **Step 3: Implement in `extraction.py`**

  - Add near top (after `GEMINI_MODEL`):
    ```python
    from collections.abc import Callable

    GEMINI_TIMEOUT_S = int(os.environ.get("GASTOSIA_EXTRACTION_TIMEOUT", "120"))
    GEMINI_TIMEOUT_MS = GEMINI_TIMEOUT_S * 1000
    ```
  - Rewrite `_gemini_extract` to use the async client + timeout:
    ```python
    async def _gemini_extract(image_path: str, mime: str, api_key: str) -> dict[str, Any]:
        from google import genai
        from google.genai import types

        with open(image_path, "rb") as f:
            image_data = f.read()

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
        )
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=[  # type: ignore[arg-type]
                PROMPT_EXTRACCION,
                {
                    "inline_data": {
                        "mime_type": mime,
                        "data": base64.b64encode(image_data).decode("utf-8"),
                    }
                },
            ],
        )
        return {
            "raw_response": response.text or "",
            "engine": "gemini",
            "error_message": None,
        }
    ```
  - Rewrite `extract_from_image` to accept `preferred_engine` and `on_event`, and emit events per attempt. Preserve existing print logging AND call `on_event(msg)` for each notable event. Engine selection:
    - `preferred_engine == "gemini"` → only the Gemini key loop (no Kimi).
    - `preferred_engine == "kimi"` → only the Kimi block.
    - `preferred_engine is None` → current behavior (all Gemini keys, then Kimi fallback).
    - Every attempt/success/quota/503/error appends to `collected_errors` AND calls `on_event(...)`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `set -a; source /tmp/gastosia-test-env.sh; set +a; uv run pytest tests/unit/test_extraction_engine.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Lint + types**

Run: `set -a; source /tmp/gastosia-test-env.sh; set +a; uv run ruff check app/expenses/extraction.py tests/unit/test_extraction_engine.py && uv run ruff format app/expenses/extraction.py tests/unit/test_extraction_engine.py && uv run mypy app/`
Expected: clean

- [ ] **Step 6: Commit**

```bash
set -a; source /tmp/gastosia-test-env.sh; set +a
git add app/expenses/extraction.py tests/unit/test_extraction_engine.py
git commit -m "feat(extraccion): motor preferido, cliente Gemini async con timeout y eventos"
```

---

### Task 2: Módulo de actividad en memoria

**Files:**
- Create: `app/expenses/activity.py`
- Test: `tests/unit/test_activity.py` (create)

**Interfaces:**
- Consumes: ninguna.
- Produces (usado por Task 3 y 4):
  - `push_event(kind: str, msg: str) -> None`
  - `get_events() -> list[dict]` — dicts `{ts, kind, msg}`, más recientes primero, `ts` en `%H:%M:%S`.
  - `get_state() -> dict` — claves: `busy: bool`, `record_id: str|None`, `filename: str|None`, `started_at: float|None`, `engine: str|None`, `elapsed_s: int|None`.
  - `is_busy() -> bool`
  - `set_batch(record_id: str, filename: str, engine: str) -> None`
  - `clear_batch() -> None`
  - `attach_task(task) -> None`, `get_task()`, `pop_task()` (retorna y limpia la task).

- [ ] **Step 1: Write failing tests** (`tests/unit/test_activity.py`):

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `set -a; source /tmp/gastosia-test-env.sh; set +a; uv run pytest tests/unit/test_activity.py -v`
Expected: FAIL (ModuleNotFoundError / no attribute)

- [ ] **Step 3: Implement `app/expenses/activity.py`**

```python
"""Estado de actividad de extraccion en memoria (una sola app/contenedor).

Buffer circular de eventos + estado del lote en curso. No persiste: se pierde
al reiniciar la app. Suficiente para el panel de visibilidad del dashboard.
"""

import time
from collections import deque

_MAX_EVENTS = 200
_events: deque[dict] = deque(maxlen=_MAX_EVENTS)
_state: dict = {
    "busy": False,
    "record_id": None,
    "filename": None,
    "started_at": None,
    "engine": None,
}
_task = None


def push_event(kind: str, msg: str) -> None:
    _events.appendleft({"ts": time.strftime("%H:%M:%S"), "kind": kind, "msg": msg})


def get_events() -> list[dict]:
    return list(_events)


def is_busy() -> bool:
    return _state["busy"]


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


def get_state() -> dict:
    st = dict(_state)
    if st["busy"] and st["started_at"] is not None:
        st["elapsed_s"] = int(time.monotonic() - st["started_at"])
    else:
        st["elapsed_s"] = None
    return st


def attach_task(task) -> None:
    global _task
    _task = task


def get_task():
    return _task


def pop_task():
    global _task
    t = _task
    _task = None
    return t
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `set -a; source /tmp/gastosia-test-env.sh; set +a; uv run pytest tests/unit/test_activity.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Lint + types** — `ruff check/format` + `mypy app/` clean.

- [ ] **Step 6: Commit**

```bash
set -a; source /tmp/gastosia-test-env.sh; set +a
git add app/expenses/activity.py tests/unit/test_activity.py
git commit -m "feat(activity): buffer en memoria de eventos y estado de lote"
```

---

### Task 3: Cola — filtro por dueño, batch runner, reset

**Files:**
- Modify: `app/expenses/queue.py`
- Test: `tests/unit/test_queue_batch.py` (create)

**Interfaces:**
- Consumes (Task 1): `extract_from_image(image_path, preferred_engine, on_event)`. (Task 1 ya cambió la firma; `process_job` debe pasar `preferred_engine` y `on_event`.)
- Consumes (Task 2): `activity.push_event`, `activity.set_batch`, `activity.clear_batch`.
- Produces:
  - `claim_next_job(db, owner_id: uuid.UUID | None = None) -> ProcessingQueue | None` (nuevo param opcional).
  - `reset_job_to_en_cola(db, job: ProcessingQueue) -> None`
  - `process_batch(engine: str, owner_id: uuid.UUID | None, on_event) -> int` — devuelve # de jobs procesados con éxito.

- [ ] **Step 1: Write failing tests** (`tests/unit/test_queue_batch.py`):

```python
"""Tests del filtro por dueno y del batch runner."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.database.models import ExpenseRecord, ProcessingQueue
from app.expenses import queue


async def _mk_record(db, owner_id):
    r = ExpenseRecord(
        owner_id=owner_id,
        image_hash=f"h{uuid.uuid4().hex[:10]}",
        status="EN_COLA",
        source_filename=f"f{uuid.uuid4().hex[:6]}.jpg",
    )
    db.add(r)
    await db.flush()
    q = ProcessingQueue(record_id=r.id, status="EN_COLA")
    db.add(q)
    await db.commit()
    return r, q


async def test_claim_respects_owner(db_session, test_admin_user, test_standard_user):
    await _mk_record(db_session, test_standard_user.id)
    # admin no debe reclamar el job de standard
    job = await queue.claim_next_job(db_session, owner_id=test_admin_user.id)
    assert job is None
    # el dueno si
    job = await queue.claim_next_job(db_session, owner_id=test_standard_user.id)
    assert job is not None


async def test_reset_job_returns_to_en_cola(db_session, test_standard_user):
    r, q = await _mk_record(db_session, test_standard_user.id)
    job = await queue.claim_next_job(db_session, owner_id=test_standard_user.id)
    assert job.status == "ANALIZANDO"
    await queue.reset_job_to_en_cola(db_session, job)
    await db_session.refresh(job)
    assert job.status == "EN_COLA"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `set -a; source /tmp/gastosia-test-env.sh; set +a; uv run pytest tests/unit/test_queue_batch.py -v`
Expected: FAIL (`claim_next_job` sin param `owner_id`; `reset_job_to_en_cola` no existe)

- [ ] **Step 3: Implement in `queue.py`**

  - `claim_next_job(db, owner_id=None)`: si `owner_id` dado, filtrar jobs cuyo `ExpenseRecord.owner_id == owner_id` (subquery sobre `ExpenseRecord.id == ProcessingQueue.record_id`).
  - `reset_job_to_en_cola(db, job)`: `job.status="EN_COLA"; job.claimed_at=None; job.worker_id=None` + record del job a `EN_COLA`; commit.
  - `process_job(db, job, engine=None, on_event=None)`: pasar `preferred_engine=engine` y `on_event` a `extract_from_image`. (Firma actual: `process_job(db, job)` — ampliar.)
  - `process_batch(engine, owner_id, on_event)`:
    ```python
    async def process_batch(engine, owner_id, on_event) -> int:
        from app.expenses import activity

        processed = 0
        while True:
            async with async_session() as db:
                job = await claim_next_job(db, owner_id=owner_id)
                if not job:
                    break
                # filename para el estado
                rec = await db.get(ExpenseRecord, job.record_id)
                fname = rec.source_filename if rec else str(job.record_id)
                activity.set_batch(str(job.record_id), fname, engine)
                on_event("info", f"Reclamado: {fname} (intento {job.attempts})")
                ok = await process_job(db, job, engine=engine, on_event=on_event)
                await complete_job(db, job, ok, None if ok else "Error de procesamiento")
                if ok:
                    processed += 1
        activity.clear_batch()
        return processed
    ```
    (Nota: `extract_from_image` espera `on_event(str)` de UN solo arg; `process_batch` recibe `on_event(kind,msg)` del route y debe adaptar — ver Task 4. Para Task 3, `process_job` puede envolver: `lambda msg: on_event("extraccion", msg)`.)
  - `worker_loop` sin cambios (usa `preferred_engine=None`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `set -a; source /tmp/gastosia-test-env.sh; set +a; uv run pytest tests/unit/test_queue_batch.py -v`
Expected: PASS

- [ ] **Step 5: Lint + types** + run full unit subset: `uv run pytest tests/unit -q`

- [ ] **Step 6: Commit**

```bash
set -a; source /tmp/gastosia-test-env.sh; set +a
git add app/expenses/queue.py tests/unit/test_queue_batch.py
git commit -m "feat(queue): filtro por dueno, process_batch y reset para cancelar"
```

---

### Task 4: Rutas — process / stop / activity

**Files:**
- Modify: `app/expenses/routes.py`
- Create: `templates/activity_panel.html`
- Test: `tests/integration/test_process_routes.py` (create)

**Interfaces:**
- Consumes (Task 2): `activity.*`. (Task 3): `process_batch`, `reset_job_to_en_cola`.
- Produces:
  - `POST /expenses/process` (form field `engine`) → fragmento HTML; 409 si `activity.is_busy()`.
  - `POST /expenses/stop` → cancela task + reset; mensaje si no hay lote.
  - `GET /dashboard/activity` → `activity_panel.html`.

- [ ] **Step 1: Write failing integration tests** (`tests/integration/test_process_routes.py`):

```python
"""Tests de las rutas de procesamiento manual."""

from unittest.mock import patch, AsyncMock

from app.expenses import activity


async def _login(client, username, password):
    r = await client.post("/login", data={"username": username, "password": password})
    return r


async def test_process_rejects_when_busy(client, test_admin_user, test_standard_user):
    await _login(client, "test_admin_...", "admin-test-password-12345")
    activity.set_batch("x", "y.jpg", "gemini")
    r = await client.post("/expenses/process", data={"engine": "gemini"})
    assert r.status_code == 409
    activity.clear_batch()


async def test_stop_without_batch_shows_notice(client, test_admin_user):
    await _login(client, "test_admin_...", "admin-test-password-12345")
    activity.clear_batch()
    r = await client.post("/expenses/stop")
    assert r.status_code == 200


async def test_activity_panel_renders(client, test_admin_user):
    await _login(client, "test_admin_...", "admin-test-password-12345")
    r = await client.get("/dashboard/activity")
    assert r.status_code == 200
    assert "cola" in r.text.lower() or "actividad" in r.text.lower()
```

(Nota: el fixture `client` y el login real deben ajustarse al patrón de `tests/integration/test_authenticated_routes.py` existente — usar el mismo helper de login y credenciales de `test_admin_user`/`test_standard_user` que ese archivo.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `set -a; source /tmp/gastosia-test-env.sh; set +a; uv run pytest tests/integration/test_process_routes.py -v`
Expected: FAIL (404 en las rutas nuevas)

- [ ] **Step 3: Implement routes in `routes.py`**

  - `POST /expenses/process`: leer `engine` del form (`gemini`|`kimi`, validar). `owner_id = None if user.role=="admin" else user.id`. Si `activity.is_busy()` → `HTMLResponse("Proceso en curso", status_code=409)`. Si no: crear `asyncio.Task` de `process_batch(engine, owner_id, on_event)` donde `on_event(kind,msg)=activity.push_event(kind,msg)`; `activity.attach_task(task)`; emitir evento "lote iniciado"; responder fragmento `activity_panel.html` o mensaje "Procesamiento iniciado".
  - `POST /expenses/stop`: si no busy → mensaje "No hay proceso en curso". Si busy: `task = activity.pop_task(); task.cancel()`; obtener el job actual (via `activity.get_state()["record_id"]`) y `reset_job_to_en_cola`; `activity.push_event("stop","Lote detenido")`; `activity.clear_batch()`; responder "Lote detenido".
  - `GET /dashboard/activity`: auth (redirect/vacío si no user). Contar `EN_COLA` (filtrado por owner si no admin). Render `activity_panel.html` con `state=activity.get_state()`, `events=activity.get_events()`, `queued=count`.

- [ ] **Step 4: Create `templates/activity_panel.html`**

```html
<div class="activity-panel" style="border:1px solid var(--border,#ddd);border-radius:8px;padding:12px;margin-bottom:12px;">
  <div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;">
    <span><strong>En cola:</strong> {{ queued }}</span>
    <span><strong>Estado:</strong> {% if state.busy %}Procesando…{% else %}Libre{% endif %}</span>
    {% if state.busy %}
    <span><strong>Imagen:</strong> {{ state.filename }}</span>
    <span><strong>Motor:</strong> {{ state.engine }}</span>
    <span><strong>Transcurrido:</strong> {{ state.elapsed_s }}s</span>
    {% endif %}
  </div>
  <h4 style="margin:12px 0 4px;">Actividad</h4>
  <div style="max-height:220px;overflow-y:auto;font-family:monospace;font-size:12px;">
    {% for e in events %}
    <div><span style="color:#888;">{{ e.ts }}</span> [{{ e.kind }}] {{ e.msg }}</div>
    {% else %}<div>Sin actividad reciente.</div>{% endfor %}
  </div>
</div>
```

- [ ] **Step 5: Run tests to verify they pass** + full integration subset.

- [ ] **Step 6: Lint + types**

- [ ] **Step 7: Commit**

```bash
set -a; source /tmp/gastosia-test-env.sh; set +a
git add app/expenses/routes.py templates/activity_panel.html tests/integration/test_process_routes.py
git commit -m "feat(routes): process/stop/activity para procesamiento manual"
```

---

### Task 5: main.py — gate del worker + recuperación al arranque

**Files:**
- Modify: `app/main.py`
- Test: `tests/unit/test_lifespan_gate.py` (create)

- [ ] **Step 1: Write failing test**:

```python
"""El worker auto solo arranca con GASTOSIA_AUTO_PROCESS."""

import os
from unittest.mock import patch

from app import main


def test_worker_gated_by_env(monkeypatch):
    monkeypatch.delenv("GASTOSIA_AUTO_PROCESS", raising=False)
    with (
        patch("app.images.monitor.monitor_loop", AsyncMock()),
        patch("app.expenses.queue.worker_loop", AsyncMock()),
    ):
        # sin GASTOSIA_TEST para entrar al bloque real
        monkeypatch.delenv("GASTOSIA_TEST", raising=False)
        # inspeccionar la condicion directamente
        assert os.environ.get("GASTOSIA_AUTO_PROCESS", "").lower() not in ("1", "true", "yes")
```

(Nota: probar la condición de arranque de forma aislada es tricky por el lifespan; aceptable extraer una helper `_auto_process_enabled() -> bool` y testearla directamente.)

- [ ] **Step 2: Run test to verify it fails** — `uv run pytest tests/unit/test_lifespan_gate.py -v`

- [ ] **Step 3: Implement**

  - Agregar helper:
    ```python
    def _auto_process_enabled() -> bool:
        return os.environ.get("GASTOSIA_AUTO_PROCESS", "").strip().lower() in ("1", "true", "yes")
    ```
  - En `lifespan`: crear `_worker_task` solo si `_auto_process_enabled()`. Siempre llamar `recover_stale_jobs` al arranque (aunque no haya worker) dentro de un `async with async_session()`.
  - Ajustar el mensaje de log.

- [ ] **Step 4: Run test to verify it passes** + `uv run pytest tests/unit -q`

- [ ] **Step 5: Lint + types**

- [ ] **Step 6: Commit**

```bash
set -a; source /tmp/gastosia-test-env.sh; set +a
git add app/main.py tests/unit/test_lifespan_gate.py
git commit -m "feat(main): gate del worker auto tras GASTOSIA_AUTO_PROCESS + recover al arranque"
```

---

### Task 6: UI — barra de control + panel de actividad

**Files:**
- Modify: `templates/dashboard.html`
- (activity_panel.html ya creado en Task 4)

- [ ] **Step 1: Insertar barra de control + panel** en `dashboard.html`, debajo del header (línea ~31, antes de `#expense-list`):

```html
<div style="display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap;">
    <label for="engine-select">Motor:</label>
    <select id="engine-select">
        <option value="gemini">Gemini</option>
        <option value="kimi">Kimi</option>
    </select>
    <button class="btn btn-primary"
            hx-post="/expenses/process"
            hx-include="#engine-select"
            hx-target="#bulk-result" hx-swap="innerHTML">Procesar imágenes</button>
    <button class="btn btn-danger"
            hx-post="/expenses/stop"
            hx-target="#bulk-result" hx-swap="innerHTML">Detener lote</button>
</div>
<div id="activity-panel" hx-get="/dashboard/activity" hx-trigger="every 3s" hx-swap="innerHTML">
    <p>Cargando actividad...</p>
</div>
```

- [ ] **Step 2: Verificar manualmente** levantando la app local contra el lab (ver Tarea 8) — el panel hace polling y los botones responden.

- [ ] **Step 3: Lint** — `ruff` no aplica a HTML; verificar que no rompe build de templates.

- [ ] **Step 4: Commit**

```bash
set -a; source /tmp/gastosia-test-env.sh; set +a
git add templates/dashboard.html
git commit -m "feat(ui): barra de motor + boton procesar/detener + panel de actividad"
```

---

### Task 7: env de ejemplo + docs

**Files:**
- Modify: `.env.example`

- [ ] Agregar:

```
# Timeout por intento de extraccion (segundos). Protege contra Gemini colgado.
GASTOSIA_EXTRACTION_TIMEOUT=120
# Si true, el worker automatico arranca y procesa solo (modo antiguo). Default false = solo manual.
GASTOSIA_AUTO_PROCESS=false
# Motor por defecto al elegir "Gemini"/"Kimi" en el dashboard:
GASTOSIA_GEMINI_MODEL=gemini-2.0-flash
GASTOSIA_KIMI_MODEL=kimi-k2.6
```

- [ ] Commit:

```bash
set -a; source /tmp/gastosia-test-env.sh; set +a
git add .env.example
git commit -m "docs(env): documentar GASTOSIA_EXTRACTION_TIMEOUT y GASTOSIA_AUTO_PROCESS"
```

---

### Task 8: Validación local + portal + gate de calidad

- [ ] `uv sync --frozen --extra dev`
- [ ] `uv run ruff check . && uv run ruff format --check .`
- [ ] `uv run mypy app/`
- [ ] `uv run pytest tests/ --cov=app --cov-fail-under=60`
- [ ] `uv run pip-audit`
- [ ] **Portal local:** levantar la app contra el lab en `127.0.0.1:8010`, crear/seed un usuario admin, poner 1-2 imágenes sintéticas en `pendientes`, y con chrome-devtools MCP validar: login → panel de actividad → elegir motor → Procesar → el log refleja el progreso → Detener → la imagen vuelve a EN_COLA. **Motor: usar solo `gemini` (free) o mock; NUNCA `kimi` (de pago).**
- [ ] Presentar diff + resultados; esperar GATE del usuario antes de desplegar a lenovosrv (etapa posterior, fuera de este plan).
