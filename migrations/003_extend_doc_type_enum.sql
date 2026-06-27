-- Extend the doc_type enum with all new document types needed by the filing
-- prerequisite check. Assumes the PostgreSQL type is named "doc_type".
-- If your type has a different name, replace "doc_type" below accordingly.
-- Safe to re-run: IF NOT EXISTS prevents duplicate-value errors.

ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'export_invoice';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'shipping_bill';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'sez_document';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'deemed_export_document';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'advance_receipt_register';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'advance_adjustment_register';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'ecommerce_tcs_statement';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'rcm_invoice';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'import_services_document';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'inward_debit_note';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'inward_credit_note';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'isd_credit_document';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'itc_reversal_working';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'mismatch_rectification_report';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'tds_credit_detail';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'tcs_credit_detail';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'interest_working';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'late_fee_working';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'bank_account_details';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'electronic_liability_ledger';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'electronic_cash_ledger';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'electronic_credit_ledger';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'supplier_invoice';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'supplier_debit_note';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'supplier_credit_note';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'gstr_2a';
ALTER TYPE doc_type ADD VALUE IF NOT EXISTS 'gstr_3b';
