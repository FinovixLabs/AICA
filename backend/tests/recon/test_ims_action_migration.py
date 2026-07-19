from pathlib import Path


def test_ims_action_migration_creates_persisted_status_and_allowed_values():
    migration = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "006_add_ims_inward_action_status.sql"
    ).read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS ims_action" in migration
    assert "ADD COLUMN IF NOT EXISTS ims_action_at" in migration
    for value in ("not_actioned", "accept", "reject", "hold"):
        assert f"'{value}'" in migration
