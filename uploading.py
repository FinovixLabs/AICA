from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def extract_and_clean(file_path: str) -> str | None:
    """
    Extract text from an uploaded document and return text ready for documents.file_text.

    Supported now:
    - .txt
    - .csv
    - .pdf when pypdf is installed

    Pandas is used for the cleanup step: strip whitespace, drop blank lines,
    and drop duplicate lines while preserving the original order.
    """
    path = Path(file_path)
    try:
        raw = _extract_raw_text(path)
    except ValueError:
        logger.warning("Unsupported file type, skipping text extraction: %s", file_path)
        return None
    except Exception as exc:
        logger.error("Document text extraction failed for %s: %s", file_path, exc, exc_info=True)
        return None

    result = _clean_text(raw)
    if not result:
        logger.warning("Extracted text is empty for: %s", file_path)
        return None

    logger.info("Extracted %d characters from %s", len(result), file_path)
    return result


def _extract_raw_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".csv":
        return _extract_csv(path)
    if suffix == ".pdf":
        return _extract_pdf(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def _extract_csv(path: Path) -> str:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    return frame.to_csv(index=False)


def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text)
    return "\n".join(parts)


def _clean_text(raw: str) -> str:
    if not raw or not raw.strip():
        return ""

    series = pd.Series(raw.splitlines(), dtype="string").str.strip()
    series = series[series.notna() & (series != "")]
    series = series.drop_duplicates()
    series = series.reset_index(drop=True)
    return "\n".join(series.astype(str).tolist())
