import json

from app.expenses.extraction import _normalize_extraction, _parse_json_response


class TestParseJsonResponse:
    def test_parse_valid_json(self):
        data = {
            "transaction_date": "2026-07-15",
            "amount": 450.50,
            "ticket_description": "Compra en supermercado",
            "bank": "NU",
            "transaction_type": "Transferencia",
        }
        text = json.dumps(data)
        result, valid = _parse_json_response(text)
        assert valid is True
        assert result["transaction_date"] == "2026-07-15"
        assert result["amount"] == 450.50
        assert result["bank"] == "NU"

    def test_parse_json_with_markdown_wrapper(self):
        data = {
            "transaction_date": "2026-01-01",
            "amount": 100.00,
            "ticket_description": "Cena restaurante",
            "bank": "BBVA",
            "transaction_type": "Credito",
        }
        text = f"```json\n{json.dumps(data)}\n```"
        result, valid = _parse_json_response(text)
        assert valid is True
        assert result["amount"] == 100.00

    def test_parse_json_with_plain_markdown_block(self):
        data = {
            "transaction_date": "2026-06-01",
            "amount": 50.75,
            "ticket_description": "Gasolina",
            "bank": "SANTANDER",
            "transaction_type": "Transferencia",
        }
        text = f"```\n{json.dumps(data)}\n```"
        result, valid = _parse_json_response(text)
        assert valid is True

    def test_parse_json_with_explanatory_text_before(self):
        data = {
            "transaction_date": "2026-03-10",
            "amount": 2000.00,
            "ticket_description": "Pago renta",
            "bank": "BANORTE",
            "transaction_type": "Transferencia",
        }
        text = f"Aqui esta el resultado:\n{json.dumps(data)}"
        result, valid = _parse_json_response(text)
        assert valid is True

    def test_parse_json_with_text_after(self):
        data = {
            "transaction_date": "2026-03-10",
            "amount": 2000.00,
            "ticket_description": "Pago renta",
            "bank": "BANORTE",
            "transaction_type": "Transferencia",
        }
        text = f"{json.dumps(data)}\nEspero que sirva."
        result, valid = _parse_json_response(text)
        assert valid is True

    def test_parse_invalid_json_returns_false(self):
        result, valid = _parse_json_response("esto no es json para nada")
        assert result is None
        assert valid is False

    def test_parse_json_missing_required_fields(self):
        text = json.dumps({"transaction_date": "2026-01-01", "amount": 100.0})
        result, valid = _parse_json_response(text)
        assert result is not None
        assert valid is False

    def test_parse_json_with_extra_whitespace(self):
        data = {
            "transaction_date": "2026-08-20",
            "amount": 75.00,
            "ticket_description": "Farmacia",
            "bank": "HSBC",
            "transaction_type": "Credito",
        }
        text = f"  \n  {json.dumps(data)}  \n  "
        result, valid = _parse_json_response(text)
        assert valid is True

    def test_parse_json_with_null_values(self):
        data = {
            "transaction_date": None,
            "amount": None,
            "ticket_description": None,
            "bank": None,
            "transaction_type": None,
        }
        text = json.dumps(data)
        result, valid = _parse_json_response(text)
        assert valid is True
        assert result["transaction_date"] is None


class TestNormalizeExtraction:
    def test_normalize_amount_string(self):
        data = {"amount": "$1,234.56", "transaction_type": "Transferencia"}
        result = _normalize_extraction(data)
        assert result["amount"] == 1234.56

    def test_normalize_amount_already_float(self):
        data = {"amount": 500.00, "transaction_type": "Credito"}
        result = _normalize_extraction(data)
        assert result["amount"] == 500.00

    def test_normalize_amount_with_currency_symbols(self):
        data = {"amount": "  $  1,000.50  "}
        result = _normalize_extraction(data)
        assert result["amount"] == 1000.50

    def test_normalize_amount_invalid_string(self):
        data = {"amount": "no-es-numero"}
        result = _normalize_extraction(data)
        assert result["amount"] == 0.0

    def test_normalize_transaction_type_credito(self):
        data = {"transaction_type": "credito"}
        result = _normalize_extraction(data)
        assert result["transaction_type"] == "Credito"

    def test_normalize_transaction_type_credito_with_accent(self):
        data = {"transaction_type": "Crédito"}
        result = _normalize_extraction(data)
        assert result["transaction_type"] == "Credito"

    def test_normalize_transaction_type_transferencia(self):
        data = {"transaction_type": "transferencia"}
        result = _normalize_extraction(data)
        assert result["transaction_type"] == "Transferencia"

    def test_normalize_transaction_type_unknown(self):
        data = {"transaction_type": "algo-raro"}
        result = _normalize_extraction(data)
        assert result["transaction_type"] == "Transferencia"

    def test_normalize_bank_uppercase(self):
        data = {"bank": "bbva"}
        result = _normalize_extraction(data)
        assert result["bank"] == "BBVA"

    def test_normalize_bank_with_whitespace(self):
        data = {"bank": "  Nu  "}
        result = _normalize_extraction(data)
        assert result["bank"] == "NU"

    def test_normalize_adds_confidence_defaults(self):
        data = {
            "transaction_date": "2026-01-01",
            "amount": 50.0,
            "ticket_description": "test",
            "bank": "NU",
            "transaction_type": "Transferencia",
        }
        result = _normalize_extraction(data)
        assert "confidence" in result
        for k in ["transaction_date", "amount", "ticket_description", "bank", "transaction_type"]:
            assert result["confidence"][k] == 0.8

    def test_normalize_preserves_existing_confidence(self):
        data = {
            "transaction_date": "2026-01-01",
            "amount": 50.0,
            "ticket_description": "test",
            "bank": "NU",
            "transaction_type": "Transferencia",
            "confidence": {"amount": 0.95},
        }
        result = _normalize_extraction(data)
        assert result["confidence"]["amount"] == 0.95

    def test_normalize_handles_empty_dict(self):
        result = _normalize_extraction({})
        assert isinstance(result, dict)
