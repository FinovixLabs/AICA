-- Persistent local IMS Inward action selected by the CA.
-- This is deliberately separate from reconciliation status and from any status
-- contained in an uploaded file. It does not claim transmission to the GST IMS.

ALTER TABLE recon.results
    ADD COLUMN IF NOT EXISTS ims_action TEXT NOT NULL DEFAULT 'not_actioned';

ALTER TABLE recon.results
    ADD COLUMN IF NOT EXISTS ims_action_at TIMESTAMPTZ;

ALTER TABLE recon.results DROP CONSTRAINT IF EXISTS results_ims_action_check;
ALTER TABLE recon.results ADD CONSTRAINT results_ims_action_check
    CHECK (ims_action IN ('not_actioned', 'accept', 'reject', 'hold'));
