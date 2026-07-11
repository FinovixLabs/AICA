from __future__ import annotations
import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


def extract_and_clean(file_path: str) -> str | None:
    path = Path(file_path)
    try:
        raw = _extract_raw_text(path)
    except ValueError:
        logger.warning("Unsupported file type: %s", file_path)
        return None
    except Exception as exc:
        logger.error("Extraction failed for %s: %s", file_path, exc, exc_info=True)
        return None

    result = _clean_text(raw)
    if not result:
        logger.warning("Empty extraction: %s", file_path)
        return None

    logger.info("Extracted %d chars from %s", len(result), file_path)
    return result


def _extract_raw_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".csv":
        return _extract_csv(path)
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix in (".xlsx", ".xls"):
        return _extract_excel(path)
    raise ValueError(f"Unsupported: {suffix}")


def _extract_csv(path: Path) -> str:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    return frame.to_csv(index=False)


def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    parts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(p for p in parts if p.strip())


def _extract_excel(path: Path) -> str:
    frame = pd.read_excel(path, dtype=str)
    frame = frame.fillna("")
    return frame.to_csv(index=False)


def _clean_text(raw: str) -> str:
    if not raw or not raw.strip():
        return ""
    series = pd.Series(raw.splitlines(), dtype="string").str.strip()
    series = series[series.notna() & (series != "")]
    series = series.drop_duplicates().reset_index(drop=True)
    return "\n".join(series.astype(str).tolist())
