from pathlib import Path
from types import SimpleNamespace

from app.images.files import move_image_to_sent


def test_move_image_to_sent(tmp_path, monkeypatch):
    source = tmp_path / "procesados" / "ticket.jpeg"
    source.parent.mkdir()
    source.write_bytes(b"image-content")
    monkeypatch.setenv("GASTOSIA_SENT_IMAGES_DIR", str(tmp_path / "enviadas"))

    image = SimpleNamespace(original_path=str(source))
    moved = move_image_to_sent(image, "Julio-2026")

    expected = tmp_path / "enviadas" / "Julio-2026" / "ticket.jpeg"
    assert moved == str(expected)
    assert expected.exists()
    assert not source.exists()
    assert image.original_path == str(expected)


def test_move_image_is_idempotent_when_destination_exists(tmp_path, monkeypatch):
    source = tmp_path / "procesados" / "ticket.jpeg"
    source.parent.mkdir()
    source.write_bytes(b"same-content")
    dest_dir = tmp_path / "enviadas" / "Julio-2026"
    dest_dir.mkdir(parents=True)
    dest = dest_dir / "ticket.jpeg"
    dest.write_bytes(b"same-content")
    monkeypatch.setenv("GASTOSIA_SENT_IMAGES_DIR", str(tmp_path / "enviadas"))

    image = SimpleNamespace(original_path=str(source))
    moved = move_image_to_sent(image, "Julio-2026")

    assert moved == str(dest)
    assert dest.exists()
    assert not source.exists()


def test_move_image_keeps_both_when_name_collides_with_other_content(tmp_path, monkeypatch):
    source = tmp_path / "procesados" / "ticket.jpeg"
    source.parent.mkdir()
    source.write_bytes(b"new-content")
    dest_dir = tmp_path / "enviadas" / "Julio-2026"
    dest_dir.mkdir(parents=True)
    (dest_dir / "ticket.jpeg").write_bytes(b"old-content")
    monkeypatch.setenv("GASTOSIA_SENT_IMAGES_DIR", str(tmp_path / "enviadas"))

    image = SimpleNamespace(original_path=str(source))
    moved = move_image_to_sent(image, "Julio-2026")

    assert moved is not None
    assert Path(moved).exists()
    assert Path(moved).name != "ticket.jpeg"
    assert (dest_dir / "ticket.jpeg").read_bytes() == b"old-content"
    assert not source.exists()


def test_move_image_missing_source_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("GASTOSIA_SENT_IMAGES_DIR", str(tmp_path / "enviadas"))
    image = SimpleNamespace(original_path=str(tmp_path / "missing.jpeg"))

    assert move_image_to_sent(image, "Julio-2026") is None


def test_move_image_without_base_returns_none(tmp_path, monkeypatch):
    source = tmp_path / "ticket.jpeg"
    source.write_bytes(b"x")
    monkeypatch.delenv("GASTOSIA_SENT_IMAGES_DIR", raising=False)

    image = SimpleNamespace(original_path=str(source))
    assert move_image_to_sent(image, "Julio-2026") is None
    assert source.exists()
