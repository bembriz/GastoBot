"""Aplicacion principal FastAPI — Gastos IA."""

import asyncio
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth.routes import router as auth_router
from app.expenses.routes import router as expenses_router
from app.catalogs.routes import router as catalogs_router
from app.history.routes import router as history_router

_monitor_task = None
_worker_task = None


async def _start_monitor():
    from app.images.monitor import monitor_loop
    await monitor_loop()


async def _start_worker():
    from app.expenses.queue import worker_loop
    await worker_loop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _monitor_task, _worker_task
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

app.include_router(auth_router)
app.include_router(expenses_router)
app.include_router(catalogs_router)
app.include_router(history_router)
