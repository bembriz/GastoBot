"""Aplicacion principal FastAPI — Gastos IA."""

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError

from app.auth.routes import router as auth_router
from app.catalogs.routes import router as catalogs_router
from app.expenses.routes import router as expenses_router
from app.history.routes import router as history_router

_monitor_task = None
_worker_task = None


async def _start_monitor() -> None:
    from app.images.monitor import monitor_loop

    await monitor_loop()


async def _start_worker() -> None:
    from app.expenses.queue import worker_loop

    await worker_loop()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _monitor_task, _worker_task
    if os.environ.get("GASTOSIA_TEST"):
        yield
        return
    try:
        _monitor_task = asyncio.create_task(_start_monitor())
        _worker_task = asyncio.create_task(_start_worker())
        print("[App] Monitor y worker FIFO iniciados", flush=True)
    except Exception as e:
        print(f"[App] ERROR iniciando tareas: {e}", flush=True)
    yield
    if _monitor_task:
        _monitor_task.cancel()
    if _worker_task:
        _worker_task.cancel()
    print("[App] Monitor y worker detenidos", flush=True)


app = FastAPI(
    title="Gastos IA",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(OperationalError)
async def db_connection_error(request: Request, exc: OperationalError) -> HTMLResponse:
    from app.templates import render

    db_error = "Error de conexion a la base de datos. Verifique PostgreSQL."
    if request.headers.get("HX-Request") == "true":
        return HTMLResponse(f'<p class="error">{db_error}</p>', status_code=503)

    return HTMLResponse(
        render(
            "login.html",
            request=request,
            user=None,
            error=db_error,
        ),
        status_code=503,
    )


app.include_router(auth_router)
app.include_router(expenses_router)
app.include_router(catalogs_router)
app.include_router(history_router)
