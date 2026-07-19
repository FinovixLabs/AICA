import { useRef, useState } from 'react'
import { Upload, FileSpreadsheet, X, CheckCircle, AlertCircle, Copy } from 'lucide-react'
import { Button, Select } from '@/components/ui'
import type {
  ReconField, ReconMap, DocTypeValue, ReconResultRow, ReconModule,
} from '@/types'

// ── Field + doc-type vocab (mirrors backend schema_fields / doctype) ─────────
export const FIELD_LABELS: Record<ReconField, string> = {
  supplier_gstin: 'Supplier GSTIN',
  supplier_name: 'Trade / Legal Name',
  doc_type: 'Document Type',
  doc_no: 'Document Number',
  doc_date: 'Document Date',
  taxable: 'Taxable Value',
  tax: 'Combined Tax',
  invoice: 'Invoice Value',
  ims_status: 'IMS Status',
  return_period: 'Return Period',
  reported_in_form: 'Reported in Form',
}

export const COMMON_FIELDS: ReconField[] = [
  'supplier_gstin', 'supplier_name', 'doc_type', 'doc_no', 'doc_date', 'taxable', 'tax', 'invoice',
]
export const REQUIRED_FIELDS: ReconField[] = [
  'supplier_gstin', 'doc_type', 'doc_no', 'doc_date', 'invoice',
]
export const INWARD_REQUIRED_FIELDS: ReconField[] = [
  'supplier_gstin', 'doc_type', 'doc_no', 'invoice',
]

export function fieldsForModule(module: ReconModule): ReconField[] {
  if (module === 'gstr2b') return COMMON_FIELDS
  // doc_type is not part of the outward match (GSTIN + invoice + IMS status only).
  if (module === 'ims_outward') return [
    ...COMMON_FIELDS.filter((f) => f !== 'doc_type'), 'ims_status', 'return_period', 'reported_in_form',
  ]
  return ['supplier_gstin', 'supplier_name', 'doc_type', 'doc_no', 'invoice', 'tax']
}

// IMS Outward matches on GSTIN + invoice value and buckets by status, so its two
// sides need less than the two-sided modules (mirrors backend required_fields_for_module).
export const OUTWARD_IMS_REQUIRED: ReconField[] = ['supplier_gstin', 'invoice', 'ims_status']
export const OUTWARD_SR_REQUIRED: ReconField[] = ['supplier_gstin', 'invoice']

export const CANONICAL_DOC_TYPES: { value: string; label: string }[] = [
  { value: 'invoice', label: 'Invoice' },
  { value: 'credit_note', label: 'Credit Note' },
  { value: 'debit_note', label: 'Debit Note' },
  { value: 'isd', label: 'ISD Invoice' },
  { value: 'impg', label: 'Import of Goods' },
  { value: 'impgsez', label: 'Import of Goods (SEZ)' },
  { value: 'other', label: 'Other' },
]

export const DATE_ORDERS = [
  { value: 'DMY', label: 'DD / MM / YYYY' },
  { value: 'MDY', label: 'MM / DD / YYYY' },
  { value: 'YMD', label: 'YYYY / MM / DD' },
]

// Exact rupee formatting — reconciliation needs full figures, not abbreviations.
export function money(n: number | null | undefined): string {
  if (n === null || n === undefined) return '—'
  return n.toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 })
}

export const STATUS_STYLE: Record<string, { label: string; cls: string }> = {
  matched: { label: 'Matched', cls: 'pill pill-filed' },
  mismatch: { label: 'Mismatch', cls: 'pill pill-overdue' },
  missing: { label: 'Missing', cls: 'pill pill-due' },
  extra: { label: 'Extra', cls: 'pill pill-review' },
  duplicate_pr: { label: 'Duplicate', cls: 'pill pill-review' },
  ambiguous: { label: 'Needs Review', cls: 'pill pill-ai' },
}

// ── Upload card (one side) ────────────────────────────────────────────────────
export function UploadCard({
  title, hint, fileName, busy, onFile,
}: {
  title: string
  hint: string
  fileName?: string | null
  busy?: boolean
  onFile: (file: File) => void
}) {
  const ref = useRef<HTMLInputElement>(null)
  const [drag, setDrag] = useState(false)
  return (
    <div
      className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ${
        drag ? 'border-[var(--forest-2)] bg-[var(--forest-dim)]'
             : 'border-[var(--border-2)] hover:border-[var(--forest-2)] hover:bg-[var(--forest-dim)]'
      }`}
      onClick={() => ref.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => { e.preventDefault(); setDrag(false); if (e.dataTransfer.files[0]) onFile(e.dataTransfer.files[0]) }}
    >
      {busy ? (
        <div className="w-5 h-5 mx-auto mb-2 border-2 border-[var(--forest-dim)] border-t-[var(--forest-2)] rounded-full animate-spin" />
      ) : fileName ? (
        <FileSpreadsheet size={22} className="mx-auto mb-2" style={{ color: 'var(--forest-2)' }} />
      ) : (
        <Upload size={22} className="mx-auto mb-2 text-[var(--ink-4)]" />
      )}
      <div className="text-sm font-semibold text-[var(--ink-2)]">{title}</div>
      {fileName ? (
        <div className="text-xs mt-1 font-mono truncate" style={{ color: 'var(--forest-2)' }}>{fileName}</div>
      ) : (
        <div className="text-xs text-[var(--ink-4)] mt-1">{hint}</div>
      )}
      <input
        ref={ref} type="file" className="hidden" accept=".csv,.xlsx"
        onChange={(e) => { if (e.target.files?.[0]) onFile(e.target.files[0]); e.target.value = '' }}
      />
    </div>
  )
}

// ── Column mapping for one file ───────────────────────────────────────────────
export function MappingPanel({
  label, headers, map, fields, onChange, required: requiredFields = REQUIRED_FIELDS,
}: {
  label: string
  headers: string[]
  map: ReconMap
  fields: ReconField[]
  onChange: (field: ReconField, header: string | null) => void
  required?: ReconField[]
}) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
      <div className="px-4 py-2.5 border-b border-[var(--border)] bg-[var(--surface-2)]">
        <div className="text-xs font-bold text-[var(--ink)]">{label}</div>
      </div>
      <div className="p-4 space-y-2.5">
        {fields.map((field) => {
          const required = requiredFields.includes(field)
          const unset = required && !map[field]
          return (
            <div key={field} className="grid grid-cols-2 gap-2 items-center">
              <label className="text-xs font-medium text-[var(--ink-2)]">
                {FIELD_LABELS[field]}
                {required && <span className="text-[var(--red)] ml-0.5">*</span>}
              </label>
              <Select
                value={map[field] ?? ''}
                onChange={(e) => onChange(field, e.target.value || null)}
                className={unset ? 'border-[var(--red)]' : ''}
              >
                <option value="">— not mapped —</option>
                {headers.map((h, i) => <option key={`${h}-${i}`} value={h}>{h}</option>)}
              </Select>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Document-type confirmation (spec 2.3) ────────────────────────────────────
export function DocTypeMapper({
  values, map, onChange,
}: {
  values: DocTypeValue[]
  map: Record<string, string>
  onChange: (raw: string, canonical: string) => void
}) {
  if (values.length === 0) {
    return <div className="text-xs text-[var(--ink-4)] px-1">Map a Document Type column above to confirm its values.</div>
  }
  return (
    <div className="grid sm:grid-cols-2 gap-2">
      {values.map((v) => (
        <div key={v.raw} className="grid grid-cols-2 gap-2 items-center">
          <span className="text-xs font-mono truncate text-[var(--ink-2)]" title={v.raw}>{v.raw || '(blank)'}</span>
          <Select value={map[v.raw] ?? v.suggested ?? 'other'} onChange={(e) => onChange(v.raw, e.target.value)}>
            {CANONICAL_DOC_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </Select>
        </div>
      ))}
    </div>
  )
}

// ── Take Action modal (spec 6.4 / 10.4) ──────────────────────────────────────
export function TakeActionModal({
  row, message, loading, onClose,
}: {
  row: { doc_no: string | null; status_label: string }
  message: string | null
  loading: boolean
  onClose: () => void
}) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    if (!message) return
    navigator.clipboard?.writeText(message).then(() => {
      setCopied(true); setTimeout(() => setCopied(false), 1500)
    }).catch(() => {})
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="w-full max-w-lg rounded-xl bg-[var(--surface)] border border-[var(--border)] shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[var(--border)]">
          <div>
            <div className="text-sm font-bold text-[var(--ink)]">Take Action — client message</div>
            <div className="text-xs text-[var(--ink-3)] mt-0.5">
              {row.doc_no || '—'} · {row.status_label} · AI-drafted, review before sending
            </div>
          </div>
          <button onClick={onClose} className="text-[var(--ink-4)] hover:text-[var(--ink)]"><X size={16} /></button>
        </div>
        <div className="p-5">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-[var(--ink-3)] py-8 justify-center">
              <div className="w-4 h-4 border-2 border-[var(--forest-dim)] border-t-[var(--forest-2)] rounded-full animate-spin" />
              Drafting message…
            </div>
          ) : (
            <textarea
              className="w-full h-56 p-3 rounded-lg text-sm bg-[var(--canvas)] border border-[var(--border)] text-[var(--ink)] font-mono resize-none focus:outline-none focus:border-[var(--accent)]"
              defaultValue={message ?? ''}
            />
          )}
        </div>
        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-[var(--border)]">
          <Button variant="ghost" size="sm" onClick={copy} disabled={!message}>
            <Copy size={13} />{copied ? 'Copied' : 'Copy'}
          </Button>
          <Button size="sm" onClick={onClose}>Done</Button>
        </div>
      </div>
    </div>
  )
}

export { CheckCircle, AlertCircle }
