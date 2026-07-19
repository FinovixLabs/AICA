import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Download, MessageSquarePlus, EyeOff, ArrowRight, RotateCcw, Layers,
  FileSpreadsheet, Upload as UploadIcon, AlertCircle,
} from 'lucide-react'
import { reconApi } from '@/lib/api'
import { useAppStore } from '@/store/appStore'
import { Card, CardHeader, CardTitle, CardSub, Button, EmptyState, Select } from '@/components/ui'
import { saveBlob, currentPeriod, formatPeriod } from '@/lib/utils'
import type {
  ReconMap, ReconField, DocTypeValue, ReconPreview, ReconSources, ReconSourceSide,
  ReconRunResult, ReconResultRow,
} from '@/types'
import {
  MappingPanel, DocTypeMapper, TakeActionModal,
  fieldsForModule, REQUIRED_FIELDS, INWARD_REQUIRED_FIELDS, DATE_ORDERS, money, STATUS_STYLE,
} from './reconShared'
import FilePreviewPanel from './FilePreviewPanel'

type Step = 'select' | 'map' | 'results'

function mergeDocTypeMap(prev: Record<string, string>, values: DocTypeValue[]): Record<string, string> {
  const next = { ...prev }
  for (const v of values) {
    if (!(v.raw in next)) next[v.raw] = v.suggested ?? 'other'
  }
  return next
}

export default function ReconWorkspace({
  module, title, subtitle, cpLabel, showIms,
}: {
  module: 'gstr2b' | 'ims_inward'
  title: string
  subtitle: string
  cpLabel: string
  showIms: boolean
}) {
  const navigate = useNavigate()
  const { activeClient, toast } = useAppStore()
  const gstin = activeClient?.gstin ?? ''

  const [step, setStep] = useState<Step>('select')
  const [sources, setSources] = useState<ReconSources | null>(null)
  const [prPreview, setPrPreview] = useState<ReconPreview | null>(null)
  const [cpPreview, setCpPreview] = useState<ReconPreview | null>(null)
  const [prLoading, setPrLoading] = useState(false)
  const [cpLoading, setCpLoading] = useState(false)

  const [prMap, setPrMap] = useState<ReconMap>({})
  const [cpMap, setCpMap] = useState<ReconMap>({})
  const [prDocTypes, setPrDocTypes] = useState<DocTypeValue[]>([])
  const [cpDocTypes, setCpDocTypes] = useState<DocTypeValue[]>([])
  const [docTypeMap, setDocTypeMap] = useState<Record<string, string>>({})
  const [prOrder, setPrOrder] = useState('auto')
  const [cpOrder, setCpOrder] = useState('auto')
  const [period, setPeriod] = useState(currentPeriod())

  const [running, setRunning] = useState(false)
  const [run, setRun] = useState<ReconRunResult | null>(null)
  const [runError, setRunError] = useState<string | null>(null)

  const fields = fieldsForModule(module)
  const requiredFields = module === 'ims_inward' ? INWARD_REQUIRED_FIELDS : REQUIRED_FIELDS

  // Load the client's uploaded documents for each side.
  useEffect(() => {
    if (!gstin) return
    reconApi.sources(module, gstin).then(setSources).catch(() => setSources(null))
  }, [module, gstin])

  const selectDoc = async (side: 'pr' | 'cp', documentId: string) => {
    if (!documentId) {
      side === 'pr' ? setPrPreview(null) : setCpPreview(null)
      return
    }
    const setLoad = side === 'pr' ? setPrLoading : setCpLoading
    setLoad(true)
    try {
      const prev: ReconPreview = await reconApi.preview(module, gstin, documentId)
      if (side === 'pr') { setPrPreview(prev); setPrMap(prev.suggested_map); setPrDocTypes(prev.doc_type_values) }
      else { setCpPreview(prev); setCpMap(prev.suggested_map); setCpDocTypes(prev.doc_type_values) }
      setDocTypeMap((p) => mergeDocTypeMap(p, prev.doc_type_values))
    } catch (e: unknown) {
      toast(errMsg(e, 'Could not read that file'), 'error')
    } finally { setLoad(false) }
  }

  // Refresh a side's distinct doc-type values when its Document Type column changes.
  useEffect(() => {
    if (step !== 'map' || !prPreview || !prMap.doc_type) return
    reconApi.docTypes(module, gstin, prPreview.document_id, prMap.doc_type, prPreview.sheet_name ?? undefined)
      .then((r) => { setPrDocTypes(r.doc_type_values); setDocTypeMap((p) => mergeDocTypeMap(p, r.doc_type_values)) })
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, prMap.doc_type])

  useEffect(() => {
    if (step !== 'map' || !cpPreview || !cpMap.doc_type) return
    reconApi.docTypes(module, gstin, cpPreview.document_id, cpMap.doc_type, cpPreview.sheet_name ?? undefined)
      .then((r) => { setCpDocTypes(r.doc_type_values); setDocTypeMap((p) => mergeDocTypeMap(p, r.doc_type_values)) })
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, cpMap.doc_type])

  const combinedDocTypes = useMemo(() => {
    const seen = new Set<string>()
    const out: DocTypeValue[] = []
    for (const v of [...prDocTypes, ...cpDocTypes]) {
      if (!seen.has(v.raw)) { seen.add(v.raw); out.push(v) }
    }
    return out
  }, [prDocTypes, cpDocTypes])

  const mapReady = useMemo(() => {
    const ok = (m: ReconMap) => requiredFields.every((f: ReconField) => m[f])
    return ok(prMap) && ok(cpMap)
  }, [prMap, cpMap, requiredFields])

  const doRun = async () => {
    if (!mapReady) { toast('Map all required (*) fields first', 'error'); return }
    setRunError(null)
    setRunning(true)
    try {
      const payload: Record<string, unknown> = {
        gstin,
        period: module === 'gstr2b' ? (period || null) : null,
        pr_document_id: prPreview!.document_id,
        cp_document_id: cpPreview!.document_id,
        pr_map: prMap,
        cp_map: cpMap,
        doc_type_map: docTypeMap,
        pr_sheet: prPreview!.sheet_name,
        cp_sheet: cpPreview!.sheet_name,
      }
      if (prOrder !== 'auto') payload.pr_date_order = prOrder
      if (cpOrder !== 'auto') payload.cp_date_order = cpOrder
      const res: ReconRunResult = await reconApi.run(module, payload)
      setRun(res)
      setStep('results')
      toast(`Reconciled — ${res.totals.total} transactions, ${res.totals.unresolved} to review`)
    } catch (e: unknown) {
      const message = errMsg(e, 'Reconciliation failed')
      setRunError(message)
      toast(message, 'error')
    } finally {
      setRunning(false)
    }
  }

  const reset = () => {
    setStep('select'); setPrPreview(null); setCpPreview(null); setPrMap({}); setCpMap({})
    setPrDocTypes([]); setCpDocTypes([]); setDocTypeMap({}); setRun(null); setRunError(null)
  }

  if (!activeClient) {
    return (
      <div className="p-6">
        <Header title={title} subtitle={subtitle} client={null} />
        <EmptyState
          icon="👥" title="Pick a client first"
          body="Reconciliation runs per GSTIN. Choose a client to begin."
          action={<Button onClick={() => navigate('/clients')}>Go to clients</Button>}
        />
      </div>
    )
  }

  return (
    <div className="p-6 animate-fade-in">
      <Header title={title} subtitle={subtitle} client={activeClient.name} />
      <Stepper step={step} />

      {step === 'select' && (
        <div className="mt-4 space-y-4">
          <Card>
            <CardHeader><div><CardTitle>Select uploaded documents</CardTitle>
              <CardSub>Files are uploaded in the Documents workspace and chosen here.</CardSub></div></CardHeader>
            <div className="p-5 grid md:grid-cols-2 gap-4">
              <DocumentPicker side={sources?.sides.pr} loading={prLoading} preview={prPreview}
                onPick={(id) => selectDoc('pr', id)} onUpload={() => navigate('/documents')} />
              <DocumentPicker side={sources?.sides.cp} loading={cpLoading} preview={cpPreview}
                onPick={(id) => selectDoc('cp', id)} onUpload={() => navigate('/documents')} />
            </div>
            <div className="px-5 pb-5 flex justify-end">
              <Button disabled={!prPreview || !cpPreview} onClick={() => setStep('map')}>
                Configure mapping <ArrowRight size={14} />
              </Button>
            </div>
          </Card>

          {(prPreview || cpPreview) && (
            <FilePreviewPanel
              tabs={[
                ...(prPreview ? [{ key: `${module}-select-pr`, label: 'Purchase Register', preview: prPreview, mapping: prMap }] : []),
                ...(cpPreview ? [{ key: `${module}-select-cp`, label: cpLabel, preview: cpPreview, mapping: cpMap }] : []),
              ]}
              subtitle="Check the selected file contents before configuring the field mapping."
            />
          )}
        </div>
      )}

      {step === 'map' && prPreview && cpPreview && (
        <div className="mt-4 space-y-4">
          <div className="grid lg:grid-cols-2 gap-4">
            <MappingPanel label={`Purchase Register · ${prPreview.file_name}`} headers={prPreview.headers}
              map={prMap} fields={fields} required={requiredFields}
              onChange={(f, h) => setPrMap((m) => ({ ...m, [f]: h }))} />
            <MappingPanel label={`${cpLabel} · ${cpPreview.file_name}`} headers={cpPreview.headers}
              map={cpMap} fields={fields} required={requiredFields}
              onChange={(f, h) => setCpMap((m) => ({ ...m, [f]: h }))} />
          </div>

          {module === 'gstr2b' && (
            <FilePreviewPanel
              tabs={[
                { key: 'gstr2b-map-pr', label: 'Purchase Register', preview: prPreview, mapping: prMap },
                { key: 'gstr2b-map-cp', label: cpLabel, preview: cpPreview, mapping: cpMap },
              ]}
              subtitle="Check the detected columns and sample values while confirming the mapping above."
            />
          )}

          <Card>
            <CardHeader><div><CardTitle>Confirm document types</CardTitle>
              <CardSub>Map each file's document-type values onto standard types (spec 2.3).</CardSub></div></CardHeader>
            <div className="p-5">
              <DocTypeMapper values={combinedDocTypes} map={docTypeMap}
                onChange={(raw, canonical) => setDocTypeMap((m) => ({ ...m, [raw]: canonical }))} />
            </div>
          </Card>

          {module === 'gstr2b' && (
            <Card>
              <div className="p-5 grid sm:grid-cols-3 gap-4 items-end">
                <div>
                  <div className="text-xs font-semibold text-[var(--ink-2)] mb-1.5">Period (YYYY-MM)</div>
                  <input value={period} onChange={(e) => setPeriod(e.target.value)} placeholder="2025-04"
                    className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--canvas)] border border-[var(--border)] text-[var(--ink)] focus:outline-none focus:border-[var(--accent)]" />
                  <div className="text-[10px] text-[var(--ink-4)] mt-1">Rows dated outside are held out, not lost.</div>
                </div>
                <OrderSelect label="PR date format" value={prOrder} onChange={setPrOrder} />
                <OrderSelect label={`${cpLabel} date format`} value={cpOrder} onChange={setCpOrder} />
              </div>
            </Card>
          )}

          {runError && (
            <div role="alert" className="rounded-xl border border-[var(--red)] bg-[var(--red-dim)] px-4 py-3 flex items-start gap-3">
              <AlertCircle size={17} className="mt-0.5 shrink-0 text-[var(--red)]" />
              <div>
                <div className="text-xs font-bold text-[var(--red)]">Reconciliation could not run</div>
                <div className="text-xs text-[var(--ink-2)] mt-1">{runError}</div>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => setStep('select')}>Back</Button>
            <Button onClick={doRun} disabled={!mapReady || running}>
              {running ? 'Reconciling…' : 'Run reconciliation'} <ArrowRight size={14} />
            </Button>
          </div>
        </div>
      )}

      {step === 'results' && run && (
        <ResultsView run={run} gstin={gstin} showIms={showIms} cpLabel={cpLabel}
          onReset={reset} onRemap={() => setStep('map')} />
      )}
    </div>
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

// ── Results (three-box structure, spec 6.3) ──────────────────────────────────
function ResultsView({
  run, gstin, showIms, cpLabel, onReset, onRemap,
}: {
  run: ReconRunResult
  gstin: string
  showIms: boolean
  cpLabel: string
  onReset: () => void
  onRemap: () => void
}) {
  const { toast } = useAppStore()
  const [rows, setRows] = useState<ReconResultRow[]>(run.results)
  const [filter, setFilter] = useState<string>('all')
  const [busyId, setBusyId] = useState<string | null>(null)
  const [resettingActions, setResettingActions] = useState(false)
  const [acceptingMatched, setAcceptingMatched] = useState(false)
  const [modal, setModal] = useState<{ row: ReconResultRow; message: string | null; loading: boolean } | null>(null)
  const [showExcluded, setShowExcluded] = useState(false)

  const isInward = run.module === 'ims_inward'
  const unresolved = rows.filter((r) => r.actionable && !r.ignored)
  const inwardQueue = rows.filter((r) => r.ims_action === 'not_actioned')
  const matchedAwaitingAction = rows.filter((r) => r.status === 'matched' && r.ims_action === 'not_actioned')
  const filtered = filter === 'all' ? rows : rows.filter((r) => r.status === filter)

  const toggleIgnore = async (row: ReconResultRow) => {
    setBusyId(row.id)
    try {
      const next = !row.ignored
      await reconApi.ignore(row.id, gstin, next)
      setRows((rs) => rs.map((r) => r.id === row.id ? { ...r, ignored: next } : r))
    } catch (e: unknown) {
      toast(errMsg(e, 'Could not update'), 'error')
    } finally { setBusyId(null) }
  }

  const takeAction = async (row: ReconResultRow) => {
    setModal({ row, message: row.message, loading: !row.message })
    if (row.message) return
    try {
      const res = await reconApi.message(row.id, gstin)
      setRows((rs) => rs.map((r) => r.id === row.id ? { ...r, message: res.message } : r))
      setModal({ row, message: res.message, loading: false })
    } catch (e: unknown) {
      toast(errMsg(e, 'Draft failed'), 'error')
      setModal(null)
    }
  }

  const setInwardAction = async (
    row: ReconResultRow, action: 'accept' | 'reject' | 'hold',
  ) => {
    setBusyId(row.id)
    try {
      const updated = await reconApi.inwardAction(row.id, gstin, action)
      setRows((current) => current.map((item) => item.id === row.id ? {
        ...item, ims_action: updated.ims_action, ims_action_at: updated.ims_action_at,
      } : item))
      toast(`IMS action saved: ${actionLabel(action)}`)
    } catch (e: unknown) {
      toast(errMsg(e, 'Could not save IMS action'), 'error')
    } finally { setBusyId(null) }
  }

  const resetInwardActions = async () => {
    setResettingActions(true)
    try {
      await reconApi.resetInwardActions(run.run_id, gstin)
      setRows((current) => current.map((row) => ({
        ...row, ims_action: 'not_actioned', ims_action_at: null, ignored: false, message: null,
      })))
      setFilter('all')
      toast('IMS Inward actions reset to Not actioned')
    } catch (e: unknown) {
      toast(errMsg(e, 'Could not reset IMS actions'), 'error')
    } finally { setResettingActions(false) }
  }

  const acceptAllMatched = async () => {
    setAcceptingMatched(true)
    try {
      const updated = await reconApi.acceptMatchedInward(run.run_id, gstin)
      const acceptedIds = new Set<string>(updated.result_ids)
      const acceptedAt = new Date().toISOString()
      setRows((current) => current.map((row) => acceptedIds.has(row.id) ? {
        ...row, ims_action: 'accept', ims_action_at: acceptedAt,
      } : row))
      toast(`${updated.updated} matched transaction(s) accepted`)
    } catch (e: unknown) {
      toast(errMsg(e, 'Could not accept matched transactions'), 'error')
    } finally { setAcceptingMatched(false) }
  }

  const downloadExcel = async () => {
    try {
      const blob = await reconApi.downloadExcel(run.run_id, gstin)
      saveBlob(blob, `${run.module}_${run.period || 'run'}.xlsx`)
    } catch (e: unknown) {
      toast(errMsg(e, 'Download failed'), 'error')
    }
  }

  const t = run.totals
  return (
    <div className="mt-4 space-y-4">
      {/* Totals + actions */}
      <div className="flex flex-wrap items-center gap-2">
        <Chip label="Matched" value={t.matched} tone="forest" />
        <Chip label="Mismatch" value={t.mismatch} tone="red" />
        <Chip label="Missing" value={t.missing} tone="amber" />
        <Chip label="Extra" value={t.extra} tone="ink" />
        {(t.duplicate_pr > 0) && <Chip label="Duplicate" value={t.duplicate_pr} tone="ink" />}
        {(t.ambiguous > 0) && <Chip label="Needs Review" value={t.ambiguous} tone="ink" />}
        <div className="ml-auto flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onRemap}><RotateCcw size={13} />Re-map</Button>
          {isInward && (
            <>
              <Button size="sm" disabled={acceptingMatched || matchedAwaitingAction.length === 0}
                onClick={acceptAllMatched}>
                {acceptingMatched ? 'Accepting…' : `Accept all matched (${matchedAwaitingAction.length})`}
              </Button>
              <Button variant="ghost" size="sm" disabled={resettingActions} onClick={resetInwardActions}>
                <RotateCcw size={13} />{resettingActions ? 'Resetting…' : 'Reset'}
              </Button>
            </>
          )}
          <Button variant="ghost" size="sm" onClick={onReset}>New run</Button>
          <Button size="sm" onClick={downloadExcel}><Download size={13} />Download Excel</Button>
        </div>
      </div>

      {/* IMS Inward has persisted local actions; other modules retain discrepancy actions. */}
      <Card>
        <CardHeader>
          <div><CardTitle>{isInward ? 'IMS Inward action queue' : 'Unresolved issues'}</CardTitle>
            <CardSub>{isInward
              ? `${inwardQueue.length} transaction(s) awaiting Accept, Reject, or Hold`
              : `${unresolved.length} item(s) need attention · Take Action or Ignore each`}</CardSub></div>
        </CardHeader>
        {(isInward ? inwardQueue : unresolved).length === 0 ? (
          <EmptyState icon="✅" title={isInward ? 'All actions saved' : 'Nothing to resolve'}
            body={isInward ? 'Use Reset to restore every action to Not actioned.' : 'Every transaction matched or has been ignored.'} />
        ) : (
          <div className="divide-y divide-[var(--border)]">
            {(isInward ? inwardQueue : unresolved).map((row) => (
              <div key={row.id} className="flex items-center gap-3 px-5 py-3">
                {isInward ? (
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold truncate">{row.supplier_name || 'Legal taxpayer name unavailable'}</div>
                    <div className="text-[11px] text-[var(--ink-3)] mt-0.5">
                      Recipient GSTIN · <span className="font-mono">{gstin}</span>
                    </div>
                  </div>
                ) : (
                  <>
                    <span className={STATUS_STYLE[row.status]?.cls}><span className="pill-dot" />{row.status_label}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold truncate">
                        {row.doc_no || '—'} · <span className="font-mono">{row.supplier_gstin || '—'}</span>
                        {row.is_split && <span className="ml-2 text-[10px]"><Layers size={10} className="inline" /> split×{row.cp_split_count}</span>}
                      </div>
                      <div className="text-[11px] text-[var(--ink-3)] mt-0.5">{row.reason || diffLine(row)}</div>
                    </div>
                    <div className="text-right text-[11px] font-mono mr-2 hidden sm:block">
                      <div>PR {money(row.pr_invoice)}</div>
                      <div className="text-[var(--ink-3)]">{cpLabel === 'GSTR-2B' ? '2B' : 'IMS'} {money(row.cp_invoice)}</div>
                    </div>
                  </>
                )}
                {isInward ? (
                  <div className="flex items-center gap-1">
                    {(['accept', 'reject', 'hold'] as const).map((action) => (
                      <Button key={action} variant="ghost" size="sm" disabled={busyId === row.id}
                        onClick={() => setInwardAction(row, action)}>
                        {actionLabel(action)}
                      </Button>
                    ))}
                  </div>
                ) : (
                  <>
                    <Button variant="ghost" size="sm" onClick={() => takeAction(row)}>
                      <MessageSquarePlus size={13} />Take Action
                    </Button>
                    <Button variant="ghost" size="sm" disabled={busyId === row.id} onClick={() => toggleIgnore(row)}>
                      <EyeOff size={13} />Ignore
                    </Button>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* CONTEMPORARY LIST — full list with status filter + Excel (spec 6.1, 6.2, 7) */}
      <Card>
        <CardHeader>
          <div><CardTitle>Contemporary reconciliation list</CardTitle>
            <CardSub>{formatPeriod(run.period || '')} · consolidated per transaction</CardSub></div>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg text-xs bg-[var(--canvas)] border border-[var(--border)] text-[var(--ink)]">
            <option value="all">All statuses</option>
            <option value="matched">Matched</option>
            <option value="mismatch">Mismatch</option>
            <option value="missing">Missing</option>
            <option value="extra">Extra</option>
            {t.duplicate_pr > 0 && <option value="duplicate_pr">Duplicate</option>}
            {t.ambiguous > 0 && <option value="ambiguous">Needs Review</option>}
          </select>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-[10px] uppercase tracking-wide text-[var(--ink-4)] border-b border-[var(--border)]">
                <th className="px-4 py-2 font-semibold">Supplier GSTIN</th>
                <th className="px-4 py-2 font-semibold">Trade / Legal Name</th>
                <th className="px-4 py-2 font-semibold">Doc No</th>
                <th className="px-4 py-2 font-semibold">Type</th>
                <th className="px-4 py-2 font-semibold">Date</th>
                <th className="px-4 py-2 font-semibold text-right">PR Invoice</th>
                <th className="px-4 py-2 font-semibold text-right">{cpLabel === 'GSTR-2B' ? '2B' : 'IMS'} Invoice</th>
                <th className="px-4 py-2 font-semibold text-right">Diff</th>
                {showIms && <th className="px-4 py-2 font-semibold">{isInward ? 'Action Status' : 'IMS Status'}</th>}
                <th className="px-4 py-2 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr key={row.id} className={`border-b border-[var(--border)] hover:bg-[var(--canvas)] ${row.ignored ? 'opacity-45' : ''}`}>
                  <td className="px-4 py-2 font-mono">{row.supplier_gstin || '—'}</td>
                  <td className="px-4 py-2">{row.supplier_name || '—'}</td>
                  <td className="px-4 py-2">{row.doc_no || '—'}{row.is_split && <span className="ml-1 text-[10px] text-[var(--ink-4)]">×{row.cp_split_count}</span>}</td>
                  <td className="px-4 py-2">{row.doc_type || '—'}</td>
                  <td className="px-4 py-2 font-mono">{row.doc_date || '—'}</td>
                  <td className="px-4 py-2 text-right font-mono">{money(row.pr_invoice)}</td>
                  <td className="px-4 py-2 text-right font-mono">{money(row.cp_invoice)}</td>
                  <td className="px-4 py-2 text-right font-mono">{row.diff_invoice != null ? money(row.diff_invoice) : '—'}</td>
                  {showIms && <td className="px-4 py-2">{isInward ? actionLabel(row.ims_action) : (row.ims_status || '—')}</td>}
                  <td className="px-4 py-2">
                    <span className={STATUS_STYLE[row.status]?.cls}><span className="pill-dot" />{row.status_label}</span>
                    {row.ignored && <span className="ml-1 text-[10px] text-[var(--ink-4)]">ignored</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && <div className="px-4 py-8 text-center text-xs text-[var(--ink-4)]">No transactions in this filter.</div>}
        </div>
        {run.excluded.length > 0 && (
          <div className="px-5 py-3 border-t border-[var(--border)]">
            <button onClick={() => setShowExcluded((s) => !s)} className="text-xs text-[var(--ink-3)] hover:text-[var(--ink)]">
              {showExcluded ? 'Hide' : 'Show'} {run.excluded.length} row(s) held out of period
            </button>
            {showExcluded && (
              <div className="mt-2 space-y-1">
                {run.excluded.map((ex, i) => (
                  <div key={i} className="text-[11px] font-mono text-[var(--ink-3)]">
                    [{ex.side.toUpperCase()}] {ex.supplier_gstin || '—'} · {ex.supplier_name || '—'} · {ex.doc_no || '—'} · {ex.doc_date || '—'} · {money(ex.invoice)}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Reserved boxes — middle/bottom purpose is unfinalized in the spec (6.3, 11). */}
      <div className="grid sm:grid-cols-2 gap-4">
        <ReservedBox n="Middle box" />
        <ReservedBox n="Bottom box" />
      </div>

      {modal && (
        <TakeActionModal row={modal.row} message={modal.message} loading={modal.loading}
          onClose={() => setModal(null)} />
      )}
    </div>
  )
}

// ── small pieces ──────────────────────────────────────────────────────────────
function Header({ title, subtitle, client }: { title: string; subtitle: string; client: string | null }) {
  return (
    <div className="mb-2">
      <div className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--forest-2)] mb-1">
        {client || 'Select a client'}
      </div>
      <h1 className="text-xl font-extrabold tracking-tight">{title}</h1>
      <p className="text-sm text-[var(--ink-3)] mt-1">{subtitle}</p>
    </div>
  )
}

function Stepper({ step }: { step: Step }) {
  const steps: { key: Step; label: string }[] = [
    { key: 'select', label: '1 · Select files' },
    { key: 'map', label: '2 · Map fields' },
    { key: 'results', label: '3 · Reconcile' },
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

function OrderSelect({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <div className="text-xs font-semibold text-[var(--ink-2)] mb-1.5">{label}</div>
      <select value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 rounded-lg text-sm bg-[var(--canvas)] border border-[var(--border)] text-[var(--ink)] focus:outline-none focus:border-[var(--accent)]">
        <option value="auto">Auto-detect</option>
        {DATE_ORDERS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

function Chip({ label, value, tone }: { label: string; value: number; tone: 'forest' | 'red' | 'amber' | 'ink' }) {
  const color = { forest: 'var(--forest-2)', red: 'var(--red)', amber: 'var(--amber-2)', ink: 'var(--ink-3)' }[tone]
  return (
    <div className="px-3 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] flex items-center gap-2">
      <span className="text-[10px] uppercase tracking-wide text-[var(--ink-4)]">{label}</span>
      <span className="text-sm font-bold num" style={{ color }}>{value}</span>
    </div>
  )
}

function ReservedBox({ n }: { n: string }) {
  return (
    <div className="rounded-xl border border-dashed border-[var(--border)] p-4 text-center">
      <div className="text-xs font-semibold text-[var(--ink-4)]">{n}</div>
      <div className="text-[11px] text-[var(--ink-4)] mt-0.5">Reserved — purpose not yet finalized</div>
    </div>
  )
}

function diffLine(row: ReconResultRow): string {
  if (row.diff_pct != null) return `Invoice values differ by ${(row.diff_pct * 100).toFixed(2)}%`
  return 'Review this transaction'
}

function actionLabel(action: ReconResultRow['ims_action'] | 'accept' | 'reject' | 'hold'): string {
  return {
    not_actioned: 'Not actioned',
    accept: 'Accept',
    reject: 'Reject',
    hold: 'Hold',
  }[action] ?? 'Not actioned'
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
  if (typeof error.response?.data === 'string' && error.response.data.trim()) {
    return `${fallback}: ${error.response.data.trim()}`
  }
  if (!error.response && (error.code === 'ERR_NETWORK' || error.message === 'Network Error')) {
    return 'Cannot reach the backend API. Confirm that FastAPI is running on port 8000 and the frontend API URL is correct.'
  }
  if (error.response?.status) return `${fallback} (HTTP ${error.response.status})`
  return error.message?.trim() || fallback
}
