"""Cliente de Google Sheets API via gspread (cuenta de servicio)."""

import os
import time
from pathlib import Path

import gspread

CREDENTIALS_PATH = os.environ["GASTOSIA_GOOGLE_CREDENTIALS_PATH"]
SPREADSHEET_ID = os.environ["GASTOSIA_GOOGLE_SPREADSHEET_ID"]

_client: gspread.Client | None = None
_spreadsheet: gspread.Spreadsheet | None = None
_last_connectivity_check = 0.0
_is_online = True


def _get_client() -> gspread.Client:
    global _client
    if _client is None:
        if not Path(CREDENTIALS_PATH).exists():
            raise FileNotFoundError(f"Credencial no encontrada: {CREDENTIALS_PATH}")
        _client = gspread.service_account(filename=CREDENTIALS_PATH)
    return _client


def get_spreadsheet() -> gspread.Spreadsheet:
    global _spreadsheet
    if _spreadsheet is None:
        gc = _get_client()
        _spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    return _spreadsheet


def verify_connectivity() -> bool:
    global _last_connectivity_check, _is_online
    now = time.monotonic()
    if now - _last_connectivity_check < 30:
        return _is_online
    _last_connectivity_check = now
    try:
        _ = get_spreadsheet().title
        _is_online = True
        return True
    except Exception:
        _is_online = False
        return False
