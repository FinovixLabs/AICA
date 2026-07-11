import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Plus, Search, X, ChevronRight } from 'lucide-react'
import { clientsApi } from '@/lib/api'
import { useAppStore } from '@/store/appStore'
import { Card, CardHeader, CardTitle, CardSub, Button, Input, StatusPill, ScoreBar, Skeleton, EmptyState } from '@/components/ui'
import type { Client } from '@/types'

const STATES = ['All', 'Regular', 'Composition', 'Exporter']
const GSTIN_RE = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$/

export default function ClientList() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { setActiveClient, toast } = useAppStore()
  const [filter, setFilter] = useState('')
  const [segment, setSegment] = useState('All')
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({ gstin: '', name: '', state: '', type: 'Regular', scheme: 'Monthly' })
  const [formError, setFormError] = useState('')

  const { data: clients, isLoading } = useQuery<Client[]>({
    queryKey: ['clients'],
    queryFn: clientsApi.list,
  })

  const createMutation = useMutation({
    mutationFn: clientsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clients'] })
      toast('Client added')
      setShowModal(false)
      setForm({ gstin: '', name: '', state: '', type: 'Regular', scheme: 'Monthly' })
    },
    onError: (e: { response?: { data?: { detail?: string } } }) => {
      setFormError(e?.response?.data?.detail || 'Failed to add client')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')
    const gstin = form.gstin.trim().toUpperCase()
    if (!GSTIN_RE.test(gstin)) { setFormError('Invalid GSTIN format'); return }
    if (!form.name.trim()) { setFormError('Name is required'); return }
    createMutation.mutate({ ...form, gstin })
  }

  const filtered = (clients || []).filter((c) => {
    const q = filter.toLowerCase()
    const matchQ = !q || c.name.toLowerCase().includes(q) || c.gstin.toLowerCase().includes(q)
    const matchSeg = segment === 'All' || (c.type || '').includes(segment)
    return matchQ && matchSeg
  })

  const handleSelect = (c: Client) => {
    setActiveClient(c)
    navigate('/filing')
  }

  return (
    <div className="p-6 animate-fade-in">
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--forest-2)] mb-1">Client register</div>
          <h1 className="text-xl font-extrabold tracking-tight">Clients</h1>
          <p className="text-sm text-[var(--ink-3)] mt-1">Managed GSTIN-wise with isolated document stores.</p>
        </div>
        <Button onClick={() => setShowModal(true)}><Plus size={13} />Add client</Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
          {STATES.map((s) => (
            <button
              key={s}
              onClick={() => setSegment(s)}
              className={`px-3 py-1.5 text-xs font-semibold transition-all border-r border-[var(--border)] last:border-r-0 ${segment === s ? 'bg-[var(--forest)] text-white' : 'text-[var(--ink-3)] hover:text-[var(--ink)] hover:bg-[var(--canvas)]'}`}
            >
              {s}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ink-4)]" />
          <Input
            placeholder="Filter by name or GSTIN…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="pl-8 text-xs"
          />
        </div>
      </div>

      {/* Table */}
      <Card>
        {isLoading ? (
          <div className="p-4 space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon="👥"
            title={filter ? 'No clients match' : 'No clients yet'}
            body={filter ? 'Try a different filter.' : 'Add your first client to begin.'}
            action={!filter ? <Button onClick={() => setShowModal(true)}><Plus size={12} />Add client</Button> : undefined}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border)] bg-[var(--surface-2)]">
                  {['Client', 'GSTIN', 'State', 'Type', 'Scheme', 'Filing', 'Risk', 'Score', ''].map((h) => (
                    <th key={h} className="text-left text-[10px] font-mono uppercase tracking-wider text-[var(--ink-4)] px-4 py-2.5">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr
                    key={c.gstin}
                    onClick={() => handleSelect(c)}
                    className="border-b border-[var(--border)] hover:bg-[var(--canvas)] cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-[var(--forest-dim)] flex items-center justify-center text-xs font-bold text-[var(--forest-2)] flex-shrink-0">
                          {c.init || c.name[0]}
                        </div>
                        <span className="text-sm font-semibold">{c.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-[var(--ink-3)]">{c.gstin}</td>
                    <td className="px-4 py-3 text-xs text-[var(--ink-3)]">{c.state || '—'}</td>
                    <td className="px-4 py-3 text-xs">{c.type || '—'}</td>
                    <td className="px-4 py-3 text-xs">{c.scheme || '—'}</td>
                    <td className="px-4 py-3">
                      <StatusPill variant={(c.filing?.toLowerCase() as 'filed' | 'due' | 'overdue') || 'due'}>
                        {c.filing || 'Due'}
                      </StatusPill>
                    </td>
                    <td className="px-4 py-3">
                      <StatusPill variant={c.risk?.toLowerCase() === 'high' ? 'overdue' : c.risk?.toLowerCase() === 'low' ? 'filed' : 'due'}>
                        {c.risk || 'Med'}
                      </StatusPill>
                    </td>
                    <td className="px-4 py-3 w-36">
                      <ScoreBar score={c.score ?? 50} />
                    </td>
                    <td className="px-4 py-3">
                      <ChevronRight size={14} className="text-[var(--ink-4)]" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Add client modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="w-full max-w-md bg-[var(--surface)] rounded-2xl shadow-2xl border border-[var(--border)] animate-fade-in">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
              <div>
                <div className="font-bold text-sm">Add new client</div>
                <div className="text-xs text-[var(--ink-3)]">GSTIN-wise document isolation enforced</div>
              </div>
              <button onClick={() => setShowModal(false)} className="text-[var(--ink-3)] hover:text-[var(--ink)]">
                <X size={16} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
              {formError && (
                <div className="px-3 py-2.5 rounded-lg bg-[var(--red-dim)] border border-[var(--red-soft)] text-[var(--red)] text-xs">
                  {formError}
                </div>
              )}
              <div>
                <label className="block text-xs font-semibold text-[var(--ink-2)] mb-1.5">GSTIN <span className="text-[var(--red)]">*</span></label>
                <Input
                  placeholder="27AABCS1429B1ZB"
                  value={form.gstin}
                  onChange={(e) => setForm(f => ({ ...f, gstin: e.target.value.toUpperCase() }))}
                  className="font-mono uppercase"
                  maxLength={15}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--ink-2)] mb-1.5">Legal name <span className="text-[var(--red)]">*</span></label>
                <Input
                  placeholder="Sharma Textiles Pvt Ltd"
                  value={form.name}
                  onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[var(--ink-2)] mb-1.5">Registration type</label>
                  <select
                    value={form.type}
                    onChange={(e) => setForm(f => ({ ...f, type: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg text-sm border border-[var(--border)] bg-[var(--canvas)] text-[var(--ink)] focus:outline-none focus:border-[var(--accent)]"
                  >
                    {['Regular', 'Composition', 'Exporter', 'SEZ', 'ISD', 'NRTP'].map(t => <option key={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[var(--ink-2)] mb-1.5">Filing scheme</label>
                  <select
                    value={form.scheme}
                    onChange={(e) => setForm(f => ({ ...f, scheme: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg text-sm border border-[var(--border)] bg-[var(--canvas)] text-[var(--ink)] focus:outline-none focus:border-[var(--accent)]"
                  >
                    {['Monthly', 'Quarterly (QRMP)', 'CMP-08'].map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--ink-2)] mb-1.5">State</label>
                <Input
                  placeholder="Maharashtra"
                  value={form.state}
                  onChange={(e) => setForm(f => ({ ...f, state: e.target.value }))}
                />
              </div>
              <div className="flex gap-2 pt-2">
                <Button type="button" variant="ghost" onClick={() => setShowModal(false)} className="flex-1">Cancel</Button>
                <Button type="submit" disabled={createMutation.isPending} className="flex-1">
                  {createMutation.isPending ? 'Adding…' : 'Add client'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
