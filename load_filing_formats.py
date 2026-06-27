"""
Load filing format markdown files from filing_formats/ into the filing_formats DB table.

Run once (or re-run to update):
    python load_filing_formats.py

Each .md file maps to one row:
    form_gstr_1a.md  →  form_type = 'GSTR_1A'
    form_gstr_2a.md  →  form_type = 'GSTR_2A'
    form_gstr_2b.md  →  form_type = 'GSTR_2B'
    form_gstr_3.md   →  form_type = 'GSTR_3'
"""

from pathlib import Path
import psycopg2
from config import SUPABASE_DATABASE_URL

FORMATS_DIR = Path(__file__).parent / "filing_formats"


def _form_type(filename: str) -> str:
    # form_gstr_1a.md → GSTR_1A
    return filename.removeprefix("form_").removesuffix(".md").upper()


def load() -> list[str]:
    conn = psycopg2.connect(SUPABASE_DATABASE_URL)
    cur = conn.cursor()
    loaded: list[str] = []

    for md_file in sorted(FORMATS_DIR.glob("*.md")):
        form_type = _form_type(md_file.name)
        content = md_file.read_text(encoding="utf-8")
        cur.execute(
            """
            INSERT INTO filing_formats (form_type, content)
            VALUES (%s, %s)
            ON CONFLICT (form_type) DO UPDATE SET content = EXCLUDED.content
            """,
            (form_type, content),
        )
        loaded.append(form_type)

    conn.commit()
    cur.close()
    conn.close()
    return loaded


if __name__ == "__main__":
    results = load()
    for form_type in results:
        print(f"  loaded: {form_type}")
    print(f"Done — {len(results)} format(s) loaded.")
