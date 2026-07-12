"""
Exact-template regeneration assets for GSTR-1.

`template_capsule.json` is an AICA_EXACT_XLSX_CAPSULE: a base64 image of the
official GSTR1_Excel_Workbook_Template_V2.0.xlsx plus a SHA-256 integrity hash.
`recreate_workbook.recreate()` decodes it into a byte-for-byte identical workbook.
"""
from __future__ import annotations
from pathlib import Path

from app.filing.gstr1_recreate.recreate_workbook import recreate

CAPSULE_PATH: Path = Path(__file__).resolve().parent / "template_capsule.json"

__all__ = ["recreate", "CAPSULE_PATH"]
