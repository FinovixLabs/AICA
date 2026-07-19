import pytest
from fastapi import HTTPException

from app.api.routes import recon


def test_abs_path_stays_inside_upload_root(tmp_path, monkeypatch):
    stored = tmp_path / "client" / "document.xlsx"
    stored.parent.mkdir()
    stored.write_bytes(b"test")
    monkeypatch.setattr(recon, "UPLOAD_ROOT", str(tmp_path))

    assert recon._abs_path("client/document.xlsx") == str(stored.resolve())


def test_abs_path_rejects_escape(tmp_path, monkeypatch):
    monkeypatch.setattr(recon, "UPLOAD_ROOT", str(tmp_path))
    with pytest.raises(HTTPException) as raised:
        recon._abs_path("../outside.xlsx")
    assert raised.value.status_code == 400


def test_abs_path_reports_missing_persistent_file(tmp_path, monkeypatch):
    monkeypatch.setattr(recon, "UPLOAD_ROOT", str(tmp_path))
    with pytest.raises(HTTPException) as raised:
        recon._abs_path("client/missing.xlsx")
    assert raised.value.status_code == 410
