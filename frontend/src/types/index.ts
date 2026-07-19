export interface User {
  name: string
  frn: string
  initials: string
  firm: string
}

export interface Client {
  gstin: string
  name: string
  state?: string
  type?: string
  scheme?: string
  status?: string
  init?: string
  score?: number
  filing?: string
  risk?: string
}

export interface Document {
  name: string
  type: string
  route: string
  extracted: string
  status: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface DashboardStats {
  clientCount: number
  filings: { done: number; total: number; delta: number }
  openNotices: number
  approved: number
  itcReconciled: string
}

export interface Deadline {
  day: string
  mon: string
  title: string
  sub: string
  overdue?: boolean
  daysLeft?: number
}

export interface ActivityItem {
  kind: 'approved' | 'draft' | 'upload' | 'notice'
  title: string
  sub: string
  time: string
}

export interface BucketSummary {
  count: number
  taxable_value?: number
  igst?: number
  cgst?: number
  sgst?: number
  cess?: number
}

export interface GstrSummary {
  B2B: BucketSummary
  B2CL: BucketSummary
  B2CS: BucketSummary
  'Nil-rated': BucketSummary
  TOTAL: { count: number; taxable_value: number }
}

export interface BetaRow {
  date: string | null
  particulars: string | null
  voucher_type: string | null
  voucher_number: string | null
  gstin: string | null
  invoice_value: number | null
  gross_total_sales: number | null
  cgst: number | null
  sgst: number | null
  round_off: number | null
  igst: number | null
  discount: number | null
  segregator: string
  taxable_value: number | null
  pos: string | null
  reverse_charge: string | null
  applicable_tax_rate: number | null
  ecommerce_gstin: string | null
  cess: number | null
  hsn: string | null
  [key: string]: unknown
}

export interface FilingFlag {
  type: string
  severity?: 'error' | 'warning'
  message?: string
  invoice_number?: string | null
  [key: string]: unknown
}

export interface FilingResult {
  status: string
  gstin: string
  period: string
  row_count: number
  summary: GstrSummary
  beta_register: BetaRow[]
  flags: FilingFlag[]
  ca_notice: string | null
  download: string
}

// ── Recon: GSTR-2B reconciliation + IMS management ──────────────────────────
export type ReconModule = 'gstr2b' | 'ims_outward' | 'ims_inward'

// System field keys the CA maps their columns onto (spec 2.2).
export type ReconField =
  | 'supplier_gstin' | 'supplier_name' | 'doc_type' | 'doc_no' | 'doc_date'
  | 'taxable' | 'tax' | 'invoice' | 'ims_status' | 'return_period' | 'reported_in_form'

export type ReconMap = Partial<Record<ReconField, string | null>>

export interface DocTypeValue {
  raw: string
  suggested: string | null
}

// A document already uploaded through the Documents workspace.
export interface ReconDocument {
  id: string
  doc_type: string
  file_name: string
  tax_period: string | null
  uploaded_at: string | null
}

export interface ReconSourceSide {
  doc_type: string
  label: string
  documents: ReconDocument[]
}

export interface ReconSources {
  module: ReconModule
  sides: { pr?: ReconSourceSide; cp: ReconSourceSide }
}

// Result of previewing a chosen document — drives the mapping UI.
export interface ReconPreview {
  document_id: string
  file_name: string
  headers: string[]
  sample_rows: (string | number | boolean | null)[][]
  sample_row_numbers: number[]
  row_count: number
  sheet_name: string | null
  sheet_names: string[]
  header_row: number
  header_end_row: number
  omitted_count: number
  omitted_rows: { row_no: number; reason: string; label: string | null }[]
  suggested_map: ReconMap
  doc_type_values: DocTypeValue[]
}

export interface ReconResultRow {
  id: string
  seq: number
  status: 'matched' | 'mismatch' | 'missing' | 'extra' | 'duplicate_pr' | 'ambiguous'
  status_code: string
  status_label: string
  actionable: boolean
  key: string
  supplier_gstin: string | null
  supplier_name: string | null
  doc_type: string | null
  doc_no: string | null
  doc_date: string | null
  pr_invoice: number | null
  pr_taxable: number | null
  pr_tax: number | null
  cp_invoice: number | null
  cp_taxable: number | null
  cp_tax: number | null
  cp_split_count: number
  is_split: boolean
  diff_invoice: number | null
  diff_pct: number | null
  reason: string | null
  flags: string[]
  ims_status: string | null
  ims_action: 'not_actioned' | 'accept' | 'reject' | 'hold'
  ims_action_at: string | null
  ignored: boolean
  message: string | null
}

export interface ReconExcludedRow {
  side: 'pr' | 'cp'
  reason: string
  supplier_gstin: string | null
  supplier_name: string | null
  doc_type: string | null
  doc_no: string | null
  doc_date: string | null
  invoice: number | null
  taxable: number | null
  tax: number | null
  ims_status: string | null
}

export interface ReconTotals {
  matched: number
  mismatch: number
  missing: number
  extra: number
  duplicate_pr: number
  ambiguous: number
  excluded: number
  unresolved: number
  total: number
}

export interface ReconRunResult {
  run_id: string
  module: ReconModule
  period: string | null
  results: ReconResultRow[]
  excluded: ReconExcludedRow[]
  totals: ReconTotals
  engine_version: string
}

// IMS Outward: the client's outward invoices matched against the Sales Register
// (on Recipient GSTIN + invoice value) and grouped by the recipient's IMS action.
export type ImsOutwardBucket = 'accepted' | 'rejected' | 'pending'
export type SrMatch = 'in_sr' | 'not_in_sr'

export interface ImsOutwardRecord {
  row_no: number
  supplier_gstin: string | null   // the recipient GSTIN
  supplier_name: string | null    // trade / legal name
  doc_no: string | null
  doc_date: string | null
  taxable: number | null
  tax: number | null
  invoice: number | null
  return_period: string | null
  reported_in_form: string | null
  ims_status: string | null
  status: ImsOutwardBucket
  sr_match: SrMatch
  takeable: boolean
}

export interface ImsOutwardResult {
  module: 'ims_outward'
  sr_file: string
  ims_file: string
  records: ImsOutwardRecord[]
  buckets: Record<ImsOutwardBucket, number>
  totals: { total: number; in_sr: number; not_in_sr: number } & Record<string, number>
  skipped_b2c: number
  engine_version: string
  actions_executable: boolean
}
