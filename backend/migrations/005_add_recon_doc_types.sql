-- 005_add_recon_doc_types.sql
-- Document types used by the reconciliation modules, uploaded through the
-- Documents workspace into the base `documents` table.
--
-- The base schema names the enum `public.document_type` (the column is named
-- `doc_type`). Do not alter a type called `doc_type`: that type does not exist in
-- the current database. purchase_register already exists; all additions remain
-- defensive and idempotent.
--
-- Postgres note: ALTER TYPE ... ADD VALUE must run OUTSIDE a transaction block and
-- a newly added value cannot be used in the same transaction. Run this file on its
-- own (psql runs each statement in its own transaction by default) before inserting
-- documents with these types.

ALTER TYPE public.document_type ADD VALUE IF NOT EXISTS 'gstr_2b';
ALTER TYPE public.document_type ADD VALUE IF NOT EXISTS 'ims_inward';
ALTER TYPE public.document_type ADD VALUE IF NOT EXISTS 'ims_outward';
