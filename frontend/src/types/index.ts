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

export interface ClassificationSummary {
  B2B: TableSummary
  B2CL: TableSummary
  B2CS: TableSummary
  EXP: TableSummary
  CDNR: TableSummary
  CDNUR: TableSummary
  AT: TableSummary
  ATA: TableSummary
  EXEMP: TableSummary
  HSN: { count: number }
  TOTAL: { total_taxable_value: number; total_tax: number }
}

export interface TableSummary {
  count: number
  taxable_value?: number
  igst?: number
  cgst?: number
  sgst?: number
  cess?: number
  total_tax?: number
}

export interface FilingResult {
  status: string
  gstin: string
  period: string
  total_rows_processed: number
  summary: ClassificationSummary
  tables: Record<string, Record<string, unknown>[]>
  gstr1_json: Record<string, unknown>
  classification_csv: string
  parse_errors: string[]
}
