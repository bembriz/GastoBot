from unittest.mock import AsyncMock, MagicMock

import pytest

from app.database.locking import _group_lock_id, get_next_consecutive


class TestGroupLockId:
    def test_same_code_produces_same_id(self):
        a = _group_lock_id("BORAMAR")
        b = _group_lock_id("BORAMAR")
        assert a == b

    def test_case_insensitive(self):
        a = _group_lock_id("boramar")
        b = _group_lock_id("BORAMAR")
        assert a == b

    def test_different_codes_produce_different_ids(self):
        a = _group_lock_id("BORAMAR")
        b = _group_lock_id("BUNG")
        assert a != b

    def test_returns_int(self):
        val = _group_lock_id("TEST")
        assert isinstance(val, int)

    def test_fits_64_bits(self):
        val = _group_lock_id("ANYCODE")
        assert -(2**63) <= val < 2**63

    def test_problematic_code_fits_signed_64(self):
        val = _group_lock_id("PSAV-260730")
        assert -(2**63) <= val < 2**63


class TestGetNextConsecutive:
    @pytest.mark.asyncio
    async def test_returns_next_number(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        db.execute.return_value = mock_result

        val = await get_next_consecutive(db, "BORAMAR")
        assert val == 5

    @pytest.mark.asyncio
    async def test_no_existing_records_returns_one(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 1
        db.execute.return_value = mock_result

        val = await get_next_consecutive(db, "NEWGROUP")
        assert val == 1
