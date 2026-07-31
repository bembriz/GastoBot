from app.images.monitor import optimize_image, sha256_file


class TestSha256File:
    def test_sha256_returns_64_chars(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        h = sha256_file(f)
        assert len(h) == 64
        assert h == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    def test_sha256_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        h = sha256_file(f)
        assert len(h) == 64

    def test_sha256_permission_error(self, tmp_path):
        f = tmp_path / "noperm.txt"
        f.write_text("data")
        import os

        os.chmod(f, 0o000)
        try:
            import contextlib

            with contextlib.suppress(PermissionError):
                sha256_file(f)
        finally:
            os.chmod(f, 0o644)


class TestOptimizeImage:
    def test_small_image_not_resized(self, tmp_path):
        from PIL import Image as PILImage

        src = tmp_path / "src.jpg"
        dest = tmp_path / "dest.jpg"
        img = PILImage.new("RGB", (100, 100), color="red")
        img.save(src)

        result = optimize_image(src, dest)
        assert result == (100, 100)
        assert dest.exists()

    def test_large_image_resized(self, tmp_path):
        from PIL import Image as PILImage

        src = tmp_path / "src.jpg"
        dest = tmp_path / "dest.jpg"
        img = PILImage.new("RGB", (4000, 3000), color="blue")
        img.save(src)

        result = optimize_image(src, dest)
        assert result is not None
        w, h = result
        assert max(w, h) <= 2048
        assert dest.exists()

    def test_unidentified_image_returns_none(self, tmp_path):
        src = tmp_path / "bad.jpg"
        src.write_text("not an image")
        dest = tmp_path / "dest.jpg"
        result = optimize_image(src, dest)
        assert result is None


class TestMonitorFunctions:
    def test_allowed_extensions_set(self):
        from app.images.monitor import ALLOWED_EXTENSIONS

        assert ".jpg" in ALLOWED_EXTENSIONS
        assert ".png" in ALLOWED_EXTENSIONS

    def test_max_file_size_defined(self):
        from app.images.monitor import MAX_FILE_SIZE

        assert MAX_FILE_SIZE > 0

    def test_poll_interval_defined(self):
        from app.images.monitor import POLL_INTERVAL

        assert POLL_INTERVAL > 0
