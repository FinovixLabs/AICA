-- Destructive manual uninstall for GSTR-2B Reconciliation and IMS Management.
-- This file is intentionally outside the ordered migrations directory so an
-- automated migrations/*.sql glob cannot execute it.

DROP SCHEMA IF EXISTS recon CASCADE;
