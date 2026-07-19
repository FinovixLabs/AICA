import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowRight, Info, MessageSquarePlus, FileSpreadsheet, Upload as UploadIcon,
} from 'lucide-react'
import { reconApi } from '@/lib/api'
import { useAppStore } from '@/store/appStore'
import { Card, CardHeader, CardTitle, CardSub, Button, EmptyState, Select } from '@/components/ui'
import type {
  ReconMap, ReconPreview, ReconSources, ReconSourceSide, ReconField,
  ImsOutwardResult, ImsOutwardRecord, ImsOutwardBucket,
} from '@/types'
import {
  MappingPanel, TakeActionModal, fieldsForModule,
  OUTWARD_IMS_REQUIRED, OUTWARD_SR_REQUIRED, money,
} from './reconShared'
import FilePreviewPanel from './FilePreviewPanel'

type Step = 'select' | 'map' | 'results'

const BUCKETS: { key: ImsOutwardBucket; label: string; tone: string; sub: string; takeable: boolean }[] = [
  { key: 'accepted', label: 'Accepted', tone: 'var(--forest-2)', sub: 'Accepted or No Action on the IMS', takeable: false },
  { key: 'rejected', label: 'Rejected', tone: 'var(--red)', sub: 'Recipient rejected — intimate the client', takeable: true },
  { key: 'pending', label: 'Pending', tone: 'var(--amber-2)', sub: 'No recipient action yet — follow up', takeable: true },
]

export default function ImsOutward() {
  const navigate = useNavigate()
  const { activeClient, toast } = useAppStore()
  const gstin = activeClient?.gstin ?? ''

  const [step, setStep] = useState<Step>('select')
  const [sources, setSources] = useState<ReconSources | null>(null)
  const [srPreview, setSrPreview] = useState<ReconPreview | null>(null)
  const [imsPreview, setImsPreview] = useState<ReconPreview | null>(null)
  const [srLoading, setSrLoading] = useState(false)
  const [imsLoading, setImsLoading] = useState(false)

  const [srMap, setSrMap] = useState<ReconMap>({})
  const [imsMap, setImsMap] = useState<ReconMap>({})

  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<ImsOutwardResult | null>(null)
  const [runError, setRunError] = useState<string | null>(null)

  const fields = fieldsForModule('ims_outward')

  useEffect(() => {
    if (!gstin) return
    reconApi.sources('ims_outward', gstin).then(setSources).catch(() => setSources(null))
  }, [gstin])

  const selectDoc = async (side: 'sr' | 'ims', documentId: string) => {
    if (!documentId) {
      side === 'sr' ? setSrPreview(null) : setImsPreview(null)
      return
    }
    const setLoad = side === 'sr' ? setSrLoading : setImsLoading
    setLoad(true)
    try {
      const prev: ReconPreview = await reconApi.preview('ims_outward', gstin, documentId)
      if (side === 'sr') { setSrPreview(prev); setSrMap(prev.suggested_map) }
      else { setImsPreview(prev); setImsMap(prev.suggested_map) }
    } catch (e: unknown) {
      toast(errMsg(e, 'Could not read that file'), 'error')
    } finally { setLoad(false) }
  }

  const mapReady = useMemo(() => {
    return OUTWARD_SR_REQUIRED.every((f: ReconField) => srMap[f]) &&
      OUTWARD_IMS_REQUIRED.every((f: ReconField) => imsMap[f])
  }, [srMap, imsMap])

  const reconcile = async () => {
    if (!mapReady) { toast('Map all required (*) fields on both files first', 'error'); return }
    setRunError(null)
    setRunning(true)
    try {
      const res: ImsOutwardResult = await reconApi.outwardReconcile({
        gstin,
        sr_document_id: srPreview!.document_id,
        ims_document_id: imsPreview!.document_id,
        sr_map: srMap,
        ims_map: imsMap,
        sr_sheet: srPreview!.sheet_name,
        ims_sheet: imsPreview!.sheet_name,
      })
      setResult(res)
      setStep('results')
      const skipped = res.skipped_b2c ? ` · ${res.skipped_b2c} B2C skipped` : ''
      toast(`Matched ${res.totals.total} outward records${skipped}`)
    } catch (e: unknown) {
      const message = errMsg(e, 'Matching failed')
      setRunError(message)
      toast(message, 'error')
    } finally { setRunning(false) }
  }

  const reset = () => {
    setStep('select'); setSrPreview(null); setImsPreview(null); setSrMap({}); setImsMap({})
    setResult(null); setRunError(null)
  }

  if (!activeClient) {
    return (
      <div className="p-6">
        <Head client={null} />
        <EmptyState icon="👥" title="Pick a client first" body="IMS Outward is matched per GSTIN."
          action={<Button onClick={() => navigate('/clients')}>Go to clients</Button>} />
      </div>
    )
  }

  return (
    <div className="p-6 animate-fade-in">
      <Head client={activeClient.name} />
      <Stepper step={step} />

      {step === 'select' && (
        <Card className="mt-4">
          <CardHeader><div><CardTitle>Select uploaded documents</CardTitle>
            <CardSub>Sales Register and IMS Outward files are uploaded in the Documents workspace and chosen here.</CardSub></div></CardHeader>
          <div className="p-5 grid md:grid-cols-2 gap-4">
            <DocumentPicker side={sources?.sides.pr} loading={srLoading} preview={srPreview}
              onPick={(id) => selectDoc('sr', id)} onUpload={() => navigate('/documents')} />
            <DocumentPicker side={sources?.sides.cp} loading={imsLoading} preview={imsPreview}
              onPick={(id) => selectDoc('ims', id)} onUpload={() => navigate('/documents')} />
          </div>
          <div className="px-5 pb-5 flex justify-end">
            <Button disabled={!srPreview || !imsPreview} onClick={() => setStep('map')}>
              Configure mapping <ArrowRight size={14} />
            </Button>
          </div>
        </Card>
      )}

      {step === 'map' && srPreview && imsPreview && (
        <div className="mt-4 space-y-4">
          <div className="grid lg:grid-cols-2 gap-4">
            <MappingPanel label={`Sales Register · ${srPreview.file_name}`} headers={srPreview.headers}
              map={srMap} fields={fields} required={OUTWARD_SR_REQUIRED}
              onChange={(f, h) => setSrMap((m) => ({ ...m, [f]: h }))} />
            <MappingPanel label={`IMS Outward · ${imsPreview.file_name}`} headers={imsPreview.headers}
              map={imsMap} fields={fields} required={OUTWARD_IMS_REQUIRED}
              onChange={(f, h) => setImsMap((m) => ({ ...m, [f]: h }))} />
          </div>

          <FilePreviewPanel
            tabs={[
              { key: 'sr', label: 'Sales Register', preview: srPreview, mapping: srMap },
              { key: 'ims', label: 'IMS Outward', preview: imsPreview, mapping: imsMap },
            ]}
            subtitle="Check the detected columns and sample values while confirming the mapping above."
          />

          <div className="px-4 py-2.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] flex items-start gap-2">
            <Info size={14} className="mt-0.5 flex-shrink-0 text-[var(--ink-3)]" />
            <div className="text-xs text-[var(--ink-3)]">
              Records are matched against the Sales Register on <strong>Recipient GSTIN + invoice value</strong> and
              grouped by IMS status. Rows without a Recipient GSTIN are treated as <strong>B2C</strong> and skipped.
            </div>
          </div>

          {runError && (
            <div role="alert" className="rounded-xl border border-[var(--red)] bg-[var(--red-dim)] px-4 py-3">
              <div className="text-xs font-bold text-[var(--red)]">Matching could not run</div>
              <div className="text-xs text-[var(--ink-2)] mt-1">{runError}</div>
            </div>
          )}

          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => setStep('select')}>Back</Button>
            <Button onClick={reconcile} disabled={!mapReady || running}>
              {running ? 'Matching…' : 'Match against Sales Register'} <ArrowRight size={14} />
            </Button>
          </div>
        </div>
      )}

      {step === 'results' && result && (
        <ResultsView result={result} gstin={gstin} onReset={reset} onRemap={() => setStep('map')} />
      )}
    </div>
  )
}

// ── Results: three status terminals ──────────────────────────────────────────
function ResultsView({
  result, gstin, onReset, onRemap,
}: {
  result: ImsOutwardResult
  gstin: string
  onReset: () => void
  onRemap: () => void
}) {
  const { toast } = useAppStore()
  const [modal, setModal] = useState<{ record: ImsOutwardRecord; message: string | null; loading: boolean } | null>(null)

  const byBucket = useMemo(() => {
    const map: Record<ImsOutwardBucket, ImsOutwardRecord[]> = { accepted: [], rejected: [], pending: [] }
    for (const r of result.records) map[r.status].push(r)
    return map
  }, [result.records])

  const takeAction = async (record: ImsOutwardRecord) => {
    setModal({ record, message: null, loading: true })
    try {
      // Draft only — send the IMS-shaped record (no reconciliation status) so the
      // draft uses the recipient-action template. Email delivery is not yet wired.
      const res = await reconApi.draftMessage(gstin, {
        supplier_gstin: record.supplier_gstin,
        supplier_name: record.supplier_name,
        doc_no: record.doc_no,
        doc_date: record.doc_date,
        invoice: record.invoice,
        ims_status: record.ims_status,
      })
      setModal({ record, message: res.message, loading: false })
    } catch (e: unknown) {
      toast(errMsg(e, 'Draft failed'), 'error')
      setModal(null)
    }
  }

  const t = result.totals
  return (
    <div className="mt-4 space-y-4">
      {/* Totals + actions */}
      <div className="flex flex-wrap items-center gap-2">
        {BUCKETS.map((b) => <Chip key={b.key} label={b.label} value={result.buckets[b.key]} color={b.tone} />)}
        <Chip label="In Sales Register" value={t.in_sr} color="var(--forest-2)" />
        {result.skipped_b2c > 0 && <Chip label="B2C skipped" value={result.skipped_b2c} color="var(--ink-4)" />}
        <div className="ml-auto flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onRemap}>Re-map</Button>
          <Button variant="ghost" size="sm" onClick={onReset}>New run</Button>
        </div>
      </div>

      <div className="px-4 py-2.5 rounded-lg border border-[var(--amber-soft)] bg-[var(--amber-dim)] flex items-start gap-2">
        <Info size={14} className="mt-0.5 flex-shrink-0" style={{ color: 'var(--amber-2)' }} />
        <div className="text-xs text-[var(--ink-2)]">
          <strong>Take Action</strong> drafts a client email for Rejected and Pending invoices. Live email
          delivery awaits Email/GSP integration.
        </div>
      </div>

      {BUCKETS.map((b) => (
        <BucketCard key={b.key} bucket={b} records={byBucket[b.key]} onTakeAction={takeAction} />
      ))}

      {modal && (
        <TakeActionModal
          row={{ doc_no: modal.record.doc_no, status_label: `IMS: ${modal.record.ims_status || '—'}` }}
          message={modal.message} loading={modal.loading} onClose={() => setModal(null)} />
      )}
    </div>
  )
}

function BucketCard({
  bucket, records, onTakeAction,
}: {
  bucket: { key: ImsOutwardBucket; label: string; tone: string; sub: string; takeable: boolean }
  records: ImsOutwardRecord[]
  onTakeAction: (record: ImsOutwardRecord) => void
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: bucket.tone }} />
          <div>
            <CardTitle>{bucket.label} · {records.length}</CardTitle>
            <CardSub>{bucket.sub}</CardSub>
          </div>
        </div>
      </CardHeader>
      {records.length === 0 ? (
        <div className="px-5 py-6 text-center text-xs text-[var(--ink-4)]">No {bucket.label.toLowerCase()} records.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-[10px] uppercase tracking-wide text-[var(--ink-4)] border-b border-[var(--border)]">
                <th className="px-4 py-2 font-semibold">Recipient GSTIN</th>
                <th className="px-4 py-2 font-semibold">Trade / Legal Name</th>
                <th className="px-4 py-2 font-semibold">Doc No</th>
                <th className="px-4 py-2 font-semibold">Date</th>
                <th className="px-4 py-2 font-semibold">Return Period</th>
                <th className="px-4 py-2 font-semibold">Reported in Form</th>
                <th className="px-4 py-2 font-semibold text-right">Taxable</th>
                <th className="px-4 py-2 font-semibold text-right">Invoice</th>
                {bucket.takeable && <th className="px-4 py-2 font-semibold text-right">Action</th>}
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.row_no} className="border-b border-[var(--border)] hover:bg-[var(--canvas)]">
                  <td className="px-4 py-2 font-mono">{r.supplier_gstin || '—'}</td>
                  <td className="px-4 py-2">{r.supplier_name || '—'}</td>
                  <td className="px-4 py-2">{r.doc_no || '—'}</td>
                  <td className="px-4 py-2 font-mono">{r.doc_date || '—'}</td>
                  <td className="px-4 py-2">{r.return_period || '—'}</td>
                  <td className="px-4 py-2">{r.reported_in_form || '—'}</td>
                  <td className="px-4 py-2 text-right font-mono">{money(r.taxable)}</td>
                  <td className="px-4 py-2 text-right font-mono">{money(r.invoice)}</td>
                  {bucket.takeable && (
                    <td className="px-4 py-2 text-right">
                      <Button variant="ghost" size="sm" onClick={() => onTakeAction(r)}>
                        <MessageSquarePlus size={13} />Take Action
                      </Button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

// ── Document picker (one side) ────────────────────────────────────────────────
function DocumentPicker({
  side, loading, preview, onPick, onUpload,
}: {
  side?: ReconSourceSide
  loading: boolean
  preview: ReconPreview | null
  onPick: (documentId: string) => void
  onUpload: () => void
}) {
  if (!side) {
    return <div className="rounded-xl border border-[var(--border)] p-5 text-sm text-[var(--ink-4)]">Loading…</div>
  }
  const docs = side.documents
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
      <div className="px-4 py-2.5 border-b border-[var(--border)] bg-[var(--surface-2)] flex items-center justify-between">
        <div className="text-xs font-bold text-[var(--ink)]">{side.label}</div>
        <span className="text-[10px] font-mono text-[var(--ink-4)]">{docs.length} uploaded</span>
      </div>
      <div className="p-4 space-y-3">
        {docs.length === 0 ? (
          <div className="text-center py-4">
            <div className="text-xs text-[var(--ink-3)] mb-2">No {side.label} uploaded yet.</div>
            <Button size="sm" variant="ghost" onClick={onUpload}><UploadIcon size={13} />Upload in Documents</Button>
          </div>
        ) : (
          <Select defaultValue="" onChange={(e) => onPick(e.target.value)}>
            <option value="">— choose a file —</option>
            {docs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.file_name}{d.tax_period ? ` · ${d.tax_period}` : ''}
              </option>
            ))}
          </Select>
        )}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-[var(--ink-3)]">
            <div className="w-3.5 h-3.5 border-2 border-[var(--forest-dim)] border-t-[var(--forest-2)] rounded-full animate-spin" />
            Reading file…
          </div>
        )}
        {preview && !loading && (
          <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--forest-2)' }}>
            <FileSpreadsheet size={13} />
            {preview.file_name} · {preview.row_count} rows{preview.sheet_name ? ` · ${preview.sheet_name}` : ''}
          </div>
        )}
      </div>
    </div>
  )
}

// ── small pieces ──────────────────────────────────────────────────────────────
function Head({ client }: { client: string | null }) {
  return (
    <div className="mb-2">
      <div className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--forest-2)] mb-1">
        {client || 'Select a client'}
      </div>
      <h1 className="text-xl font-extrabold tracking-tight">IMS Outward</h1>
      <p className="text-sm text-[var(--ink-3)] mt-1">
        Match outward invoices against the Sales Register and group by the recipient's IMS action.
      </p>
    </div>
  )
}

function Stepper({ step }: { step: Step }) {
  const steps: { key: Step; label: string }[] = [
    { key: 'select', label: '1 · Select files' },
    { key: 'map', label: '2 · Map fields' },
    { key: 'results', label: '3 · Match' },
  ]
  const idx = steps.findIndex((s) => s.key === step)
  return (
    <div className="flex items-center gap-2 mt-3">
      {steps.map((s, i) => (
        <div key={s.key} className={`text-[11px] font-mono px-2.5 py-1 rounded-full border ${
          i <= idx ? 'border-[var(--forest-2)] text-[var(--forest-2)] bg-[var(--forest-dim)]'
                   : 'border-[var(--border)] text-[var(--ink-4)]'}`}>
          {s.label}
        </div>
      ))}
    </div>
  )
}

function Chip({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="px-3 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] flex items-center gap-2">
      <span className="text-[10px] uppercase tracking-wide text-[var(--ink-4)]">{label}</span>
      <span className="text-sm font-bold num" style={{ color }}>{value}</span>
    </div>
  )
}

function errMsg(e: unknown, fallback: string): string {
  const error = e as {
    message?: string
    code?: string
    response?: { status?: number; data?: { detail?: unknown } | string }
  }
  const detail = typeof error.response?.data === 'object' ? error.response.data?.detail : undefined
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => typeof item === 'object' && item && 'msg' in item ? String(item.msg) : String(item))
      .filter(Boolean)
    if (messages.length) return messages.join('; ')
  }
  if (!error.response && (error.code === 'ERR_NETWORK' || error.message === 'Network Error')) {
    return 'Cannot reach the backend API. Confirm that FastAPI is running on port 8000.'
  }
  if (error.response?.status) return `${fallback} (HTTP ${error.response.status})`
  return error.message?.trim() || fallback
}
