import { useState, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { documentsApi } from '@/lib/api'
import { useAppStore } from '@/store/appStore'
import { Card, CardHeader, CardTitle, CardSub, Button, EmptyState, Skeleton } from '@/components/ui'
import type { Document } from '@/types'

const DOC_TYPES = [
  { key: 'purchase_register', label: 'Purchase Register', desc: 'Inward supply' },
  { key: 'gstr_2b', label: 'GSTR-2B', desc: 'Auto-draft ITC (for reconciliation)' },
  { key: 'ims_inward', label: 'IMS Inward', desc: 'Inward invoices (for reconciliation)' },
  { key: 'ims_outward', label: 'IMS Outward', desc: 'Outward invoices (for reconciliation)' },
  { key: 'sales_register', label: 'Sales Register', desc: 'Outward supply' },
  { key: 'sales_invoice', label: 'Tax Invoices', desc: 'B2B / B2C' },
]

interface UploadItem {
  id: string
  name: string
  status: 'uploading' | 'done' | 'error'
  msg?: string
}

export default function Documents() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { activeClient, toast } = useAppStore()
  const [selectedType, setSelectedType] = useState('sales_register')
  const [uploads, setUploads] = useState<UploadItem[]>([])
  const [dragging, setDragging] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const { data: docs, isLoading } = useQuery<Document[]>({
    queryKey: ['documents', activeClient?.gstin],
    queryFn: () => documentsApi.list(activeClient!.gstin),
    enabled: !!activeClient,
  })

  const handleFiles = async (files: FileList | null) => {
    if (!files || !activeClient) return
    for (const file of Array.from(files)) {
      const id = Math.random().toString(36).slice(2)
      setUploads((prev) => [...prev, { id, name: file.name, status: 'uploading' }])
      try {
        await documentsApi.upload(activeClient.gstin, file, selectedType)
        setUploads((prev) => prev.map((u) => u.id === id ? { ...u, status: 'done', msg: 'Stored' } : u))
        qc.invalidateQueries({ queryKey: ['documents', activeClient.gstin] })
        toast(`${file.name} uploaded`)
      } catch (e: unknown) {
        const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Upload failed'
        setUploads((prev) => prev.map((u) => u.id === id ? { ...u, status: 'error', msg } : u))
        toast(msg, 'error')
      }
    }
  }

  return (
    <div className="p-6 animate-fade-in">
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--forest-2)] mb-1">
            {activeClient?.name || 'Select a client'}
          </div>
          <h1 className="text-xl font-extrabold tracking-tight">Documents</h1>
          <p className="text-sm text-[var(--ink-3)] mt-1">Upload once. Backend classifies and routes each file.</p>
        </div>
      </div>

      {!activeClient ? (
        <EmptyState
          icon="👥"
          title="Pick a client first"
          body="Documents are stored per GSTIN. Choose a client to upload against."
          action={<Button onClick={() => navigate('/clients')}>Go to clients</Button>}
        />
      ) : (
        <div className="grid lg:grid-cols-2 gap-4">
          {/* Upload panel */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Upload documents</CardTitle>
                  <CardSub>Posts to /api/clients/{activeClient.gstin}/documents</CardSub>
                </div>
              </CardHeader>
              <div className="p-5 space-y-4">
                {/* Drop zone */}
                <div
                  className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                    dragging
                      ? 'border-[var(--forest-2)] bg-[var(--forest-dim)]'
                      : 'border-[var(--border-2)] hover:border-[var(--forest-2)] hover:bg-[var(--forest-dim)]'
                  }`}
                  onClick={() => fileRef.current?.click()}
                  onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files) }}
                >
                  <Upload size={24} className="mx-auto mb-3 text-[var(--ink-4)]" />
                  <div className="text-sm font-semibold text-[var(--ink-2)]">Drop files or click to upload</div>
                  <div className="text-xs text-[var(--ink-4)] mt-1">CSV, PDF, XLSX, TXT supported</div>
                  <input
                    ref={fileRef}
                    type="file"
                    multiple
                    className="hidden"
                    onChange={(e) => handleFiles(e.target.files)}
                    accept=".csv,.pdf,.xlsx,.xls,.txt"
                  />
                </div>

                {/* Doc type selector */}
                <div>
                  <div className="text-xs font-semibold text-[var(--ink-2)] mb-2">Document type</div>
                  <div className="grid grid-cols-2 gap-1.5">
                    {DOC_TYPES.map((dt) => (
                      <button
                        key={dt.key}
                        onClick={() => setSelectedType(dt.key)}
                        className={`text-left px-3 py-2 rounded-lg border text-xs transition-all ${
                          selectedType === dt.key
                            ? 'border-[var(--forest-2)] bg-[var(--forest-dim)] text-[var(--forest-2)]'
                            : 'border-[var(--border)] bg-[var(--surface-2)] text-[var(--ink-3)] hover:border-[var(--border-2)]'
                        }`}
                      >
                        <div className="font-semibold">{dt.label}</div>
                        <div className="text-[10px] opacity-70 mt-0.5">{dt.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Upload list */}
                {uploads.length > 0 && (
                  <div className="space-y-2">
                    {uploads.map((u) => (
                      <div
                        key={u.id}
                        className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-[var(--border)] bg-[var(--surface-2)]"
                      >
                        <FileText size={14} className="text-[var(--ink-3)] flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-semibold truncate">{u.name}</div>
                          <div className="text-[10px] text-[var(--ink-3)] mt-0.5">{u.msg || 'Uploading…'}</div>
                        </div>
                        {u.status === 'uploading' && (
                          <div className="w-4 h-4 border-2 border-[var(--forest-dim)] border-t-[var(--forest-2)] rounded-full animate-spin flex-shrink-0" />
                        )}
                        {u.status === 'done' && <CheckCircle size={14} className="flex-shrink-0" style={{ color: 'var(--forest-3)' }} />}
                        {u.status === 'error' && <AlertCircle size={14} className="flex-shrink-0" style={{ color: 'var(--red)' }} />}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>

            {/* Info card */}
            <div className="px-4 py-3 rounded-xl border border-[var(--forest-soft)] bg-[var(--forest-dim)] flex items-start gap-3">
              <CheckCircle size={14} className="mt-0.5 flex-shrink-0" style={{ color: 'var(--forest-2)' }} />
              <div className="text-xs text-[var(--forest)]">
                <strong>Isolation enforced.</strong> Client data and the GST knowledge base are stored separately and never mixed.
              </div>
            </div>
          </div>

          {/* Stored docs */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Stored documents</CardTitle>
                <CardSub>Classified and routed automatically</CardSub>
              </div>
              {docs && docs.length > 0 && (
                <span className="text-xs font-mono text-[var(--ink-4)]">{docs.length} files</span>
              )}
            </CardHeader>

            {isLoading ? (
              <div className="p-4 space-y-2">
                {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12" />)}
              </div>
            ) : !docs || docs.length === 0 ? (
              <EmptyState
                icon={<FileText size={28} />}
                title="No documents yet"
                body="Upload documents to see them classified here."
              />
            ) : (
              <div className="divide-y divide-[var(--border)]">
                {docs.map((d, i) => (
                  <div key={i} className="flex items-center gap-3 px-5 py-3 hover:bg-[var(--canvas)] transition-colors">
                    <div className="w-8 h-8 rounded-lg bg-[var(--forest-dim)] flex items-center justify-center flex-shrink-0">
                      <FileText size={14} style={{ color: 'var(--forest-2)' }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold truncate">{d.name}</div>
                      <div className="text-[10px] text-[var(--ink-3)] mt-0.5">
                        {d.type} · {d.route || '—'} · {d.extracted}
                      </div>
                    </div>
                    <span className="pill pill-filed flex-shrink-0">
                      <span className="pill-dot" />Stored
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
