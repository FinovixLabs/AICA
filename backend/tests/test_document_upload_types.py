from pathlib import Path

from app.api.routes.documents import _database_accepts_document_type


class _EnumCursor:
    def __init__(self, supported: bool):
        self.supported = supported
        self.params = None

    def execute(self, _query, params):
        self.params = params

    def fetchone(self):
        return (self.supported,)


def test_database_document_type_check_uses_requested_enum_label():
    cursor = _EnumCursor(True)
    assert _database_accepts_document_type(cursor, "ims_inward") is True
    assert cursor.params == ("ims_inward",)


def test_database_document_type_check_reports_missing_value():
    assert _database_accepts_document_type(_EnumCursor(False), "ims_outward") is False


def test_recon_document_type_migration_targets_the_documents_enum():
    migration = (
        Path(__file__).resolve().parents[1] / "migrations" / "005_add_recon_doc_types.sql"
    ).read_text(encoding="utf-8")
    assert "ALTER TYPE public.document_type" in migration
    assert "'ims_inward'" in migration
    assert "'ims_outward'" in migration
    assert "ALTER TYPE doc_type " not in migration
