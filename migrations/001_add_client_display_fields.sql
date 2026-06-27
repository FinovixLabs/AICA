-- Add free-text display fields entered from the "Add Client" form.
-- reg_type   -> GST registration type (Regular / Composition / Exporter / ...)
-- reg_scheme -> filing scheme label as entered (Monthly / QRMP / CMP-08 / ...)
-- The native filing_frequency enum is still populated (normalized) from reg_scheme.
ALTER TABLE clients ADD COLUMN IF NOT EXISTS reg_type text;
ALTER TABLE clients ADD COLUMN IF NOT EXISTS reg_scheme text;
