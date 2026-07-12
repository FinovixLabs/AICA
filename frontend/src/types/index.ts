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
