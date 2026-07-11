CREATE TABLE IF NOT EXISTS filing_formats (
    form_type  TEXT PRIMARY KEY,
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
