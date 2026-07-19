import pytest
from fastapi import HTTPException

from app.api.routes.filing import _normalise_period


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("2026-07", "072026"), ("072026", "072026"), ("", "")],
)
def test_normalise_period(raw, expected):
    assert _normalise_period(raw) == expected


@pytest.mark.parametrize("raw", ["2026-13", "../../secret", "072026.xlsx", "2026/07"])
def test_normalise_period_rejects_unsafe_values(raw):
    with pytest.raises(HTTPException) as raised:
        _normalise_period(raw)
    assert raised.value.status_code == 422
