import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Download, CheckCircle, AlertCircle, AlertTriangle, RefreshCw, Send, FileText } from 'lucide-react'
import { filingApi, chatApi } from '@/lib/api'
import { useAppStore } from '@/store/appStore'
import { Card, CardHeader, CardTitle, CardSub, Button, EmptyState } from '@/components/ui'
import { currentPeriod, formatCurrency, saveBlob, downloadJson } from '@/lib/utils'
import type { FilingResult, ChatMessage, BetaRow } from '@/types'

const BUCKETS = ['B2B', 'B2CL', 'B2CS', 'Nil-rated'] as const
type Bucket = (typeof BUCKETS)[number]

const BUCKET_LABELS: Record<Bucket, string> = {
  B2B: 'B2B — Registered buyers',
  B2CL: 'B2CL — Unregistered, large invoices',
  B2CS: 'B2CS — Unregistered, summary',
  'Nil-rated': 'Nil-rated — 0% GST supplies',
}

// Columns shown in the beta-register table, in order.
const BETA_COLS: { key: keyof BetaRow; label: string }[] = [
  { key: 'voucher_number', label: 'Voucher No' },
  { key: 'date', label: 'Date' },
  { key: 'particulars', label: 'Particulars' },
  { key: 'voucher_type', label: 'Voucher Type' },
  { key: 'gstin', label: 'GSTIN' },
  { key: 'pos', label: 'POS' },
  { key: 'segregator', label: 'Bucket' },
  { key: 'taxable_value', label: 'Taxable' },
  { key: 'gross_total_sales', label: 'Gross Sales' },
  { key: 'applicable_tax_rate', label: 'Rate %' },
  { key: 'igst', label: 'IGST' },
  { key: 'cgst', label: 'CGST' },
  { key: 'sgst', label: 'SGST' },
  { key: 'cess', label: 'Cess' },
  { key: 'invoice_value', label: 'Invoice Val' },
  { key: 'round_off', label: 'Round Off' },
  { key: 'discount', label: 'Discount' },
  { key: 'reverse_charge', label: 'RCM' },
  { key: 'ecommerce_gstin', label: 'E-Com GSTIN' },
  { key: 'hsn', label: 'HSN' },
]

export default function Filing() {
  const navigate = useNavigate()
  const { activeClient, lastFilingResult, setLastFilingResult, toast, chatHistory, appendChat, clearChat } = useAppStore()
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [activeBucket, setActiveBucket] = useState<Bucket>('B2B')
  const [chatInput, setChatInput] = useState('')
  const [chatMode, setChatMode] = useState<'ask' | 'edit'>('ask')
  const [streaming, setStreaming] = useState(false)
  const chatBodyRef = useRef<HTMLDivElement>(null)
  const period = currentPeriod()

  if (!activeClient) {
    return (
      <div className="p-6">
        <EmptyState
          icon="👥"
          title="No client selected"
          body="Pick a client from the register to start a GSTR-1 filing."
          action={<Button onClick={() => navigate('/clients')}>Go to clients</Button>}
        />
      </div>
    )
  }

  const handleGenerate = async () => {
    setLoading(true)
    setLastFilingResult(null)
    clearChat()
    try {
      const result: FilingResult = await filingApi.generate(activeClient.gstin, period)
      setLastFilingResult(result)
      toast(`GSTR-1 generated — ${result.row_count} transactions processed`)
      const firstBucket = BUCKETS.find((b) => (result.summary[b]?.count ?? 0) > 0) || 'B2B'
      setActiveBucket(firstBucket)
      if (result.ca_notice) appendChat({ role: 'assistant', content: result.ca_notice })
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Generation failed'
      toast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!result) return
    setDownloading(true)
    try {
      const blob = await filingApi.downloadWorkbook(result.download)
      saveBlob(blob, `GSTR1_${activeClient.gstin}_${period}.xlsx`)
      toast('Workbook downloaded')
    } catch {
      toast('Download failed', 'error')
    } finally {
      setDownloading(false)
    }
  }

  const handleSendChat = async () => {
    if (!chatInput.trim() || streaming) return
    const msg = chatInput.trim()
    setChatInput('')
    appendChat({ role: 'user', content: msg })
    setStreaming(true)
    let acc = ''
    try {
      if (result && chatMode === 'edit') {
        const edited = await filingApi.editRegister({
          gstin: activeClient.gstin,
          period,
          instruction: msg,
          beta_register: result.beta_register,
        })
        setLastFilingResult({ ...result, ...edited })
        appendChat({ role: 'assistant', content: edited.message || 'Register updated.' })
        toast('Register and workbook updated')
        return
      }

      const allMsgs: ChatMessage[] = [...chatHistory, { role: 'user', content: msg }]
      await chatApi.stream(
        allMsgs.map((m) => ({ role: m.role, content: m.content })),
        'filing',
        activeClient.gstin,
        result?.gstin === activeClient.gstin ? result : null,
        (tok) => {
          acc += tok
          const updated = [...chatHistory, { role: 'user' as const, content: msg }, { role: 'assistant' as const, content: acc }]
          useAppStore.getState().setChatHistory(updated)
          chatBodyRef.current?.scrollTo(0, chatBodyRef.current.scrollHeight)
        }
      )
    } catch (error: unknown) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      appendChat({
        role: 'assistant',
        content: detail || (error instanceof Error ? error.message : 'Assistant error — please try again.'),
      })
    } finally {
      setStreaming(false)
    }
  }

  const result = lastFilingResult
  const summary = result?.summary
  const activeRows = result ? result.beta_register.filter((r) => r.segregator === activeBucket) : []
  const flags = result?.flags ?? []
  const errorFlags = flags.filter((f) => f.severity === 'error')
  const warningFlags = flags.filter((f) => f.severity !== 'error')
  const totalTax = summary
    ? BUCKETS.reduce((acc, b) => acc + (summary[b]?.igst || 0) + (summary[b]?.cgst || 0) + (summary[b]?.sgst || 0), 0)
    : 0

  return (
    <div className="p-6 animate-fade-in">
      {/* Page head */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--forest-2)] mb-1">
            {activeClient.name} · {activeClient.gstin}
          </div>
          <h1 className="text-xl font-extrabold tracking-tight">GSTR-1 Filing Assistant</h1>
          <p className="text-sm text-[var(--ink-3)] mt-1">
            AI extraction · Standardized beta register · CA approval required · Period {period}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {result && (
            <>
              <Button variant="ghost" size="sm" onClick={() => downloadJson(result.beta_register, `beta_register_${activeClient.gstin}_${period}.json`)}>
                <Download size={12} /> Beta JSON
              </Button>
              <Button variant="ghost" size="sm" onClick={handleDownload} disabled={downloading}>
                {downloading ? <RefreshCw size={12} className="animate-spin" /> : <Download size={12} />} GSTR-1 Workbook
              </Button>
            </>
          )}
          <Button onClick={handleGenerate} disabled={loading}>
            {loading ? <RefreshCw size={13} className="animate-spin" /> : <Play size={13} />}
            {loading ? 'Generating…' : result ? 'Re-generate' : 'Generate GSTR-1'}
          </Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-[minmax(0,1fr)_320px] gap-4">
        {/* Main panel */}
        <div className="min-w-0 space-y-4">
          {/* Bucket cards */}
          {result && summary && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
              {BUCKETS.map((key) => {
                const s = summary[key]
                const count = s?.count ?? 0
                return (
                  <button
                    key={key}
                    onClick={() => setActiveBucket(key)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      activeBucket === key
                        ? 'border-[var(--forest-2)] bg-[var(--forest-dim)]'
                        : 'border-[var(--border)] bg-[var(--surface)] hover:border-[var(--border-2)]'
                    }`}
                  >
                    <div className="text-[10px] font-mono font-bold text-[var(--ink-3)] mb-1">{key}</div>
                    <div className="text-lg font-bold num" style={{ color: activeBucket === key ? 'var(--forest-2)' : 'var(--ink)' }}>
                      {count}
                    </div>
                    <div className="text-[10px] text-[var(--ink-4)] mt-0.5 leading-tight truncate">
                      {formatCurrency(s?.taxable_value || 0)}
                    </div>
                  </button>
                )
              })}
            </div>
          )}

          {/* TOTAL summary */}
          {summary?.TOTAL && (
            <Card>
              <div className="grid grid-cols-3 divide-x divide-[var(--border)]">
                <div className="p-4 text-center">
                  <div className="text-xs text-[var(--ink-3)] mb-1">Transactions</div>
                  <div className="text-xl font-bold num">{summary.TOTAL.count}</div>
                </div>
                <div className="p-4 text-center">
                  <div className="text-xs text-[var(--ink-3)] mb-1">Total taxable value</div>
                  <div className="text-xl font-bold num" style={{ color: 'var(--forest-2)' }}>
                    {formatCurrency(summary.TOTAL.taxable_value)}
                  </div>
                </div>
                <div className="p-4 text-center">
                  <div className="text-xs text-[var(--ink-3)] mb-1">Total GST</div>
                  <div className="text-xl font-bold num" style={{ color: 'var(--amber-2)' }}>
                    {formatCurrency(totalTax)}
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Validation flags */}
          {result && flags.length > 0 && (
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Validation flags</CardTitle>
                  <CardSub>{errorFlags.length} to fix · {warningFlags.length} to review</CardSub>
                </div>
              </CardHeader>
              <div className="p-4 space-y-2 max-h-52 overflow-y-auto">
                {[...errorFlags, ...warningFlags].map((f, i) => {
                  const isError = f.severity === 'error'
                  return (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      {isError ? (
                        <AlertCircle size={14} className="flex-shrink-0 mt-0.5" style={{ color: 'var(--red)' }} />
                      ) : (
                        <AlertTriangle size={14} className="flex-shrink-0 mt-0.5" style={{ color: 'var(--amber)' }} />
                      )}
                      <span className="text-[var(--ink-2)] leading-relaxed">{f.message || f.type}</span>
                    </div>
                  )
                })}
              </div>
            </Card>
          )}

          {/* Beta register table */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>{BUCKET_LABELS[activeBucket]}</CardTitle>
                <CardSub>{activeRows.length} rows · beta sales register · {period}</CardSub>
              </div>
              {result && <span className="pill pill-ai"><span className="pill-dot" />Standardized</span>}
            </CardHeader>

            {!result ? (
              <EmptyState
                icon={<FileText size={32} />}
                title="No GSTR-1 generated yet"
                body="Run the pipeline to extract, standardize and fill the government GSTR-1 workbook from your uploaded sales documents."
                action={
                  <Button onClick={handleGenerate} disabled={loading}>
                    {loading ? <RefreshCw size={13} className="animate-spin" /> : <Play size={13} />}
                    {loading ? 'Generating…' : 'Generate GSTR-1'}
                  </Button>
                }
              />
            ) : activeRows.length === 0 ? (
              <EmptyState title="No rows in this bucket" body="No transactions were segregated into this category." />
            ) : (
              <div className="max-h-80 overflow-x-hidden overflow-y-auto">
                <table className="w-full table-fixed text-[10px]">
                  <thead className="sticky top-0 bg-[var(--surface-2)] border-b border-[var(--border)]">
                    <tr>
                      {BETA_COLS.map((c) => (
                        <th key={String(c.key)} className="break-words px-1 py-2 text-left font-mono text-[8px] uppercase leading-tight tracking-tight text-[var(--ink-4)]">
                          {c.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {activeRows.map((row, i) => (
                      <tr key={i} className="border-b border-[var(--border)] hover:bg-[var(--canvas)] transition-colors">
                        {BETA_COLS.map((c) => (
                          <td key={String(c.key)} className="break-words px-1 py-2 align-top font-mono leading-tight text-[var(--ink-2)]">
                            {String(row[c.key] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Actions */}
            {result && (
              <div className="border-t border-[var(--border)] px-5 py-3 flex items-center justify-between bg-[var(--surface-2)]">
                <span className="text-xs text-[var(--ink-3)]">
                  {result.row_count} transactions · {errorFlags.length > 0 ? `${errorFlags.length} issues to resolve` : 'no blocking issues'}
                </span>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={handleDownload} disabled={downloading}>
                    {downloading ? <RefreshCw size={11} className="animate-spin" /> : <Download size={11} />} GSTR-1 Workbook
                  </Button>
                  <Button size="sm" onClick={() => toast('Output marked as CA reviewed')}>
                    <CheckCircle size={11} /> Mark reviewed
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Chat panel */}
        <Card className="flex flex-col" style={{ height: 'calc(100vh - 180px)' }}>
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-lg bg-[var(--forest-dim)] flex items-center justify-center">
                <span className="text-[10px] font-bold" style={{ color: 'var(--forest-2)' }}>AI</span>
              </div>
              <div>
                <CardTitle>Filing Assistant</CardTitle>
                <CardSub>Grounded in GST knowledge base</CardSub>
              </div>
            </div>
          </CardHeader>

          {/* Messages */}
          <div ref={chatBodyRef} className="flex-1 overflow-y-auto p-4 space-y-3">
            {chatHistory.length === 0 && (
              <div className="flex gap-2">
                <div className="w-7 h-7 rounded-lg bg-[var(--forest-dim)] flex items-center justify-center text-[10px] font-bold flex-shrink-0" style={{ color: 'var(--forest-2)' }}>AI</div>
                <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded-xl rounded-tl-sm px-3 py-2.5 text-xs text-[var(--ink-2)] max-w-[85%] leading-relaxed">
                  Ask me about the GSTR-1 output, specific transaction buckets, or request changes to the register.
                </div>
              </div>
            )}
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold flex-shrink-0"
                  style={{
                    background: msg.role === 'user' ? 'var(--forest-dim)' : 'var(--amber-dim)',
                    color: msg.role === 'user' ? 'var(--forest-2)' : 'var(--amber)',
                  }}
                >
                  {msg.role === 'user' ? 'CA' : 'AI'}
                </div>
                <div
                  className="rounded-xl px-3 py-2.5 text-xs max-w-[85%] leading-relaxed whitespace-pre-wrap"
                  style={{
                    background: msg.role === 'user' ? 'var(--forest-dim)' : 'var(--surface-2)',
                    border: '1px solid var(--border)',
                    borderTopLeftRadius: msg.role === 'assistant' ? '4px' : undefined,
                    borderTopRightRadius: msg.role === 'user' ? '4px' : undefined,
                    color: 'var(--ink-2)',
                  }}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {streaming && (
              <div className="flex gap-2">
                <div className="w-7 h-7 rounded-lg bg-[var(--amber-dim)] flex items-center justify-center text-[10px] font-bold flex-shrink-0" style={{ color: 'var(--amber)' }}>AI</div>
                <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded-xl rounded-tl-sm px-3 py-2.5">
                  <div className="flex gap-1 items-center">
                    {[0,1,2].map(i => (
                      <div key={i} className="w-1.5 h-1.5 rounded-full bg-[var(--ink-3)] animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-[var(--border)] p-3">
            <div className="mb-2 flex gap-1" role="group" aria-label="Assistant mode">
              {(['ask', 'edit'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setChatMode(mode)}
                  disabled={mode === 'edit' && !result}
                  className={`rounded-md px-2 py-1 text-[10px] font-semibold transition-colors disabled:opacity-40 ${
                    chatMode === mode
                      ? 'bg-[var(--forest-dim)] text-[var(--forest-2)]'
                      : 'text-[var(--ink-4)] hover:text-[var(--ink-2)]'
                  }`}
                >
                  {mode === 'ask' ? 'Ask' : 'Edit register'}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendChat() } }}
              placeholder={chatMode === 'edit' ? 'Describe the exact register change…' : 'Ask about the filing…'}
              rows={1}
              className="flex-1 resize-none text-xs px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--canvas)] text-[var(--ink)] placeholder:text-[var(--ink-4)] focus:outline-none focus:border-[var(--accent)] transition-all"
              style={{ maxHeight: '80px' }}
            />
            <button
              onClick={handleSendChat}
              disabled={streaming || !chatInput.trim()}
              className="w-8 h-8 rounded-lg flex items-center justify-center transition-all disabled:opacity-40"
              style={{ background: 'var(--forest)', color: '#fff' }}
            >
              <Send size={13} />
            </button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
