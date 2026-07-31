# Ejemplo: Configuración de Google Sheets API para Fase 3
# Archivo: app/sheets/client.py

# Este ejemplo muestra el setup y cliente de Google Sheets que
# skill-google-sheets debe implementar completamente.

import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetsClient:
    """Google Sheets API client for Gastos IA."""

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self):
        self.credentials_path = os.environ.get("GASTOSIA_GOOGLE_CREDENTIALS_PATH")
        self.spreadsheet_id = os.environ.get("GASTOSIA_GOOGLE_SPREADSHEET_ID")

        if not self.credentials_path:
            raise ValueError("GASTOSIA_GOOGLE_CREDENTIALS_PATH not set")
        if not self.spreadsheet_id:
            raise ValueError("GASTOSIA_GOOGLE_SPREADSHEET_ID not set")
        if not Path(self.credentials_path).exists():
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")

        self._service = None

    @property
    def service(self):
        if self._service is None:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=self.SCOPES
            )
            self._service = build("sheets", "v4", credentials=credentials)
        return self._service

    async def verify_connectivity(self) -> bool:
        """Quick check that Google Sheets API is reachable."""
        try:
            self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id,
                fields="properties/title",
            ).execute()
            return True
        except HttpError:
            return False

    async def get_or_create_sheet(self, sheet_name: str) -> int:
        """Get sheet ID by name, or create it if it doesn't exist.
        Returns the sheet ID."""
        spreadsheet = (
            self.service.spreadsheets()
            .get(
                spreadsheetId=self.spreadsheet_id,
            )
            .execute()
        )

        for sheet in spreadsheet.get("sheets", []):
            if sheet["properties"]["title"] == sheet_name:
                return sheet["properties"]["sheetId"]

        # Create new sheet
        body = {"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
        response = (
            self.service.spreadsheets()
            .batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body,
            )
            .execute()
        )
        return response["replies"][0]["addSheet"]["properties"]["sheetId"]

    async def create_monthly_headers(self, sheet_name: str):
        """Write the 16 column headers to a monthly sheet."""
        headers = [
            "Fecha del gasto",
            "Categoría",
            "Descripción",
            "Empleado",
            "Pagado por",
            "Actividades",
            "Fecha contable",
            "Cuenta",
            "Precio unitario",
            "Cantidad",
            "Incluir impuestos",
            "Importe de impuestos",
            "Total",
            "Estado",
            "Banco",
            "Transaccion",
        ]
        range_name = f"'{sheet_name}'!A1:P1"
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": [headers]},
        ).execute()
