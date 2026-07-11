import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Download, CheckCircle, AlertCircle, RefreshCw, Send, FileText } from 'lucide-react'
import { filingApi, chatApi } from '@/lib/api'
import { useAppStore } from '@/store/appStore'
import { Card, CardHeader, CardTitle, CardSub, Button, EmptyState } from '@/components/ui'
import { currentPeriod, formatCurrency, downloadBlob, downloadJson } from '@/lib/utils'
import type { FilingResult, ChatMessage } from '@/types'

const TABLE_LABELS: Record<string, string> = {
  B2B: 'B2B — Registered buyers',
  B2CL: 'B2CL — Unregistered, inter-state >2.5L',
  B2CS: 'B2CS — Unregistered, summary',
  EXP: 'EXP — Exports',
  CDNR: 'CDNR — Credit/debit notes (registered)',
  CDNUR: 'CDNUR — Credit/debit notes (unregistered)',
  AT: 'AT — Advance receipts',
  ATA: 'ATA — Advance adjustments',
  EXEMP: 'EXEMP — Nil/exempt/non-GST',
}

export default function Filing() {
  const navigate = useNavigate()
  const { activeClient, lastFilingResult, setLastFilingResult, toast, chatHistory, appendChat, clearChat } = useAppStore()
  const [loading, setLoading] = useState(false)
  const [activeTable, setActiveTable] = useState('B2B')
  const [chatInput, setChatInput] = useState('')
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

  const handleClassify = async () => {
    setLoading(true)
    setLastFilingResult(null)
    clearChat()
    try {
      const result: FilingResult = await filingApi.classify(activeClient.gstin, period)
      setLastFilingResult(result)
      toast(`Classification complete — ${result.total_rows_processed} invoices processed`)
      // Find first non-empty table
      const firstTable = Object.entries(result.tables).find(([, rows]) => rows.length > 0)?.[0] || 'B2B'
      setActiveTable(firstTable)
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Classification failed'
      toast(msg, 'error')
    } finally {
      setLoading(false)
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
      const allMsgs: ChatMessage[] = [...chatHistory, { role: 'user', content: msg }]
      await chatApi.stream(
        allMsgs.map((m) => ({ role: m.role, content: m.content })),
        'filing',
        activeClient.gstin,
        (tok) => {
          acc += tok
          // Update last AI message
          const updated = [...chatHistory, { role: 'user' as const, content: msg }, { role: 'assistant' as const, content: acc }]
          useAppStore.getState().setChatHistory(updated)
          chatBodyRef.current?.scrollTo(0, chatBodyRef.current.scrollHeight)
        }
      )
    } catch {
      appendChat({ role: 'assistant', content: 'Assistant error — please try again.' })
    } finally {
      setStreaming(false)
    }
  }

  const result = lastFilingResult
  const summary = result?.summary
  const nonEmptyTables = result ? Object.entries(result.tables).filter(([, rows]) => rows.length > 0) : []
  const activeRows = result?.tables[activeTable] || []

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
            Deterministic classification · CA approval required · Period {period}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {result && (
            <>
              <Button variant="ghost" size="sm" onClick={() => downloadBlob(result.classification_csv, `GSTR1_${activeClient.gstin}_${period}.csv`)}>
                <Download size={12} /> CSV
              </Button>
              <Button variant="ghost" size="sm" onClick={() => downloadJson(result.gstr1_json, `GSTR1_${activeClient.gstin}_${period}.json`)}>
                <Download size={12} /> JSON
              </Button>
            </>
          )}
          <Button onClick={handleClassify} disabled={loading}>
            {loading ? <RefreshCw size={13} className="animate-spin" /> : <Play size={13} />}
            {loading ? 'Classifying…' : result ? 'Re-classify' : 'Run GSTR-1 Classification'}
          </Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr_320px] gap-4">
        {/* Main panel */}
        <div className="space-y-4">
          {/* Summary cards */}
          {result && summary && (
            <div className="grid grid-cols-3 lg:grid-cols-6 gap-2">
              {Object.entries(TABLE_LABELS).map(([key, label]) => {
                const s = summary[key as keyof typeof summary]
                if (!s || typeof s !== 'object') return null
                const count = (s as { count: number }).count
                return (
                  <button
                    key={key}
                    onClick={() => setActiveTable(key)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      activeTable === key
                        ? 'border-[var(--forest-2)] bg-[var(--forest-dim)]'
                        : 'border-[var(--border)] bg-[var(--surface)] hover:border-[var(--border-2)]'
                    }`}
                  >
                    <div className="text-[10px] font-mono font-bold text-[var(--ink-3)] mb-1">{key}</div>
                    <div className="text-lg font-bold num" style={{ color: activeTable === key ? 'var(--forest-2)' : 'var(--ink)' }}>
                      {count}
                    </div>
                    <div className="text-[10px] text-[var(--ink-4)] mt-0.5 leading-tight truncate">
                      {label.split('—')[0].trim()}
                    </div>
                  </button>
                )
              })}
            </div>
          )}

          {/* TOTAL summary */}
          {summary?.TOTAL && (
            <Card>
              <div className="grid grid-cols-2 divide-x divide-[var(--border)]">
                <div className="p-4 text-center">
                  <div className="text-xs text-[var(--ink-3)] mb-1">Total taxable value</div>
                  <div className="text-xl font-bold num" style={{ color: 'var(--forest-2)' }}>
                    {formatCurrency(summary.TOTAL.total_taxable_value)}
                  </div>
                </div>
                <div className="p-4 text-center">
                  <div className="text-xs text-[var(--ink-3)] mb-1">Total GST</div>
                  <div className="text-xl font-bold num" style={{ color: 'var(--amber-2)' }}>
                    {formatCurrency(summary.TOTAL.total_tax)}
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Table viewer */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>{TABLE_LABELS[activeTable] || activeTable}</CardTitle>
                <CardSub>{activeRows.length} rows · {period}</CardSub>
              </div>
              {result && (
                <span className="pill pill-ai"><span className="pill-dot" />AI Classified</span>
              )}
            </CardHeader>

            {!result ? (
              <EmptyState
                icon={<FileText size={32} />}
                title="No classification yet"
                body="Run the GSTR-1 classifier to process your uploaded sales register."
                action={
                  <Button onClick={handleClassify} disabled={loading}>
                    {loading ? <RefreshCw size={13} className="animate-spin" /> : <Play size={13} />}
                    {loading ? 'Classifying…' : 'Run Classification'}
                  </Button>
                }
              />
            ) : activeRows.length === 0 ? (
              <EmptyState title="No rows in this table" body="No invoices were classified into this GSTR-1 category." />
            ) : (
              <div className="overflow-x-auto max-h-80 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-[var(--surface-2)] border-b border-[var(--border)]">
                    <tr>
                      {Object.keys(activeRows[0]).filter(k => k !== 'gstr1_table').map((h) => (
                        <th key={h} className="text-left font-mono text-[10px] uppercase tracking-wide text-[var(--ink-4)] px-4 py-2.5 whitespace-nowrap">
                          {h.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {activeRows.map((row, i) => (
                      <tr key={i} className="border-b border-[var(--border)] hover:bg-[var(--canvas)] transition-colors">
                        {Object.entries(row).filter(([k]) => k !== 'gstr1_table').map(([k, v]) => (
                          <td key={k} className="px-4 py-2.5 whitespace-nowrap font-mono text-[var(--ink-2)]">
                            {String(v ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Parse errors */}
            {result?.parse_errors && result.parse_errors.length > 0 && (
              <div className="border-t border-[var(--border)] p-4">
                <div className="flex items-center gap-2 text-xs text-[var(--amber)] mb-2">
                  <AlertCircle size={13} /> Parse warnings
                </div>
                {result.parse_errors.map((e, i) => (
                  <div key={i} className="text-xs text-[var(--ink-3)] font-mono">{e}</div>
                ))}
              </div>
            )}

            {/* Actions */}
            {result && (
              <div className="border-t border-[var(--border)] px-5 py-3 flex items-center justify-between bg-[var(--surface-2)]">
                <span className="text-xs text-[var(--ink-3)]">{result.total_rows_processed} invoices · {nonEmptyTables.length} tables populated</span>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={() => downloadBlob(result.classification_csv, `GSTR1_${activeClient.gstin}_${period}.csv`)}>
                    <Download size={11} /> Download CSV
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => downloadJson(result.gstr1_json, `GSTR1_${activeClient.gstin}_${period}.json`)}>
                    <Download size={11} /> Download JSON
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
                  Ask me about the GSTR-1 classification, specific invoice categories, or request changes to the output.
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
                  className="rounded-xl px-3 py-2.5 text-xs max-w-[85%] leading-relaxed"
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
          <div className="border-t border-[var(--border)] p-3 flex gap-2">
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendChat() } }}
              placeholder="Ask about the filing or request a change…"
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
        </Card>
      </div>
    </div>
  )
}
