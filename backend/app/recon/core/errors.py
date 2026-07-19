from __future__ import annotations


class ReconError(Exception):
    """Base for every error raised inside app/recon."""


class ParseError(ReconError):
    """A source file could not be read into a grid."""


class MappingIncomplete(ReconError):
    """A run was requested before every required system field was mapped."""

    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__(f"Unmapped required fields: {', '.join(missing)}")


class AmbiguousDateOrder(ReconError):
    """A file's dates cannot be read under any single day/month order."""
