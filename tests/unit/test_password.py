from app.auth.password import hash_password, needs_rehash, verify_password

_CORRECT_PASSWORD = "correct-horse-battery-staple"
_CORRECT_HASH = hash_password("correct-horse-battery-staple")
_WRONG_PASSWORD = "wrong-password-xyz"


class TestHashPassword:
    def test_hash_password_returns_valid_hash(self):
        result = hash_password("my-secret-password")
        assert result.startswith("$argon2id$")
        assert len(result) > 20

    def test_hash_password_different_passwords_produce_different_hashes(self):
        h1 = hash_password("password-one")
        h2 = hash_password("password-two")
        assert h1 != h2

    def test_hash_password_same_password_produces_different_hashes(self):
        """Argon2id uses random salt so each hash is unique even for the same password."""
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2


class TestVerifyPassword:
    def test_verify_password_correct(self):
        assert verify_password(_CORRECT_PASSWORD, _CORRECT_HASH) is True

    def test_verify_password_incorrect(self):
        assert verify_password(_WRONG_PASSWORD, _CORRECT_HASH) is False

    def test_verify_password_invalid_hash_format(self):
        assert verify_password("anything", "not-a-valid-argon2-hash") is False

    def test_verify_password_empty_strings(self):
        assert verify_password("", "") is False


class TestNeedsRehash:
    def test_needs_rehash_returns_bool(self):
        h = hash_password("some-password")
        result = needs_rehash(h)
        assert isinstance(result, bool)
