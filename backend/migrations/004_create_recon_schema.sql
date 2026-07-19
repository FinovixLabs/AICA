-- 004_create_recon_schema.sql
-- Storage for the GSTR-2B Reconciliation and IMS Management modules.
--
-- Source files are NOT stored here — they are uploaded through the Documents
-- workspace into the base `documents` table (tagged purchase_register / gstr_2b /
-- ims_inward / ims_outward) and reconciliation references them by id. This schema
-- only persists reconciliation runs and their result rows.
--
-- Everything lives under the `recon` Postgres schema. It references clients(id)
-- and documents(id) from the base schema. Full uninstall:
-- migrations/manual/999_drop_recon.sql.
--
-- NOTE: if an earlier version of this migration (which created recon.uploads) was
-- already applied, run manual/999_drop_recon.sql first, then re-apply this file.
--
-- gen_random_uuid() is a Postgres 13+ / Supabase built-in.

CREATE SCHEMA IF NOT EXISTS recon;

-- One reconciliation run. The counterparty side (cp) always points at a document;
-- the purchase-register side (pr) is null for IMS Outward, which has no PR.
-- `config` records exactly how the run was produced (confirmed column maps, date
-- orders, doc-type map, tolerance) so a run is reproducible and auditable.
-- `excluded` holds rows held out of matching (e.g. dated outside the period).
CREATE TABLE IF NOT EXISTS recon.runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    module          TEXT NOT NULL,          -- 'gstr2b' | 'ims_inward' | 'ims_outward'
    period          TEXT,
    pr_document_id  UUID REFERENCES documents(id) ON DELETE SET NULL,
    cp_document_id  UUID REFERENCES documents(id) ON DELETE SET NULL,
    config          JSONB NOT NULL DEFAULT '{}'::jsonb,
    totals          JSONB NOT NULL DEFAULT '{}'::jsonb,
    excluded        JSONB NOT NULL DEFAULT '[]'::jsonb,
    engine_version  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS runs_client_module_idx
    ON recon.runs (client_id, module, created_at DESC);

-- One row of the contemporary reconciliation list. Persisted per-row so the CA
-- can Ignore an item or attach a generated Take Action message to it, and so the
-- Excel download reproduces exactly what was on screen.
CREATE TABLE IF NOT EXISTS recon.results (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id      UUID NOT NULL REFERENCES recon.runs(id) ON DELETE CASCADE,
    seq         INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL,
    status_code TEXT NOT NULL,              -- backend sort key only; never reaches Excel
    match_key   TEXT,
    payload     JSONB NOT NULL DEFAULT '{}'::jsonb,
    ims_action  TEXT NOT NULL DEFAULT 'not_actioned',
    ims_action_at TIMESTAMPTZ,
    ignored     BOOLEAN NOT NULL DEFAULT FALSE,
    message     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE recon.results DROP CONSTRAINT IF EXISTS results_ims_action_check;
ALTER TABLE recon.results ADD CONSTRAINT results_ims_action_check
    CHECK (ims_action IN ('not_actioned', 'accept', 'reject', 'hold'));
CREATE INDEX IF NOT EXISTS results_run_idx
    ON recon.results (run_id, status_code, seq);
