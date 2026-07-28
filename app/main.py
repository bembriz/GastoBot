"""Aplicacion principal FastAPI — Gastos IA."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth.routes import router as auth_router
from app.expenses.routes import router as expenses_router
from app.catalogs.routes import router as catalogs_router
from app.history.routes import router as history_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


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
