import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ClipboardCheck, Bell, CheckCircle, DollarSign, Plus, ChevronRight } from 'lucide-react'
import { dashboardApi, clientsApi } from '@/lib/api'
import { useAppStore } from '@/store/appStore'
import { Card, CardHeader, CardTitle, CardSub, StatusPill, ScoreBar, Skeleton, EmptyState, Button } from '@/components/ui'
import type { Client } from '@/types'

function KpiCard({ label, value, sub, icon: Icon, color, trend }: {
  label: string; value: string | number; sub?: string
  icon: React.ElementType; color: string; trend?: string; trendUp?: boolean
}) {
  return (
    <Card className="relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-0.5" style={{ background: color }} />
      <div className="p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${color}18` }}>
            <Icon size={15} style={{ color }} />
          </div>
          {trend && (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: `${color}18`, color }}>
              {trend}
            </span>
          )}
        </div>
        <div className="text-xs text-[var(--ink-3)] mb-1 font-medium">{label}</div>
        <div className="text-2xl font-bold num tracking-tight" style={{ color }}>{value}</div>
        {sub && <div className="text-xs text-[var(--ink-4)] mt-1.5">{sub}</div>}
      </div>
    </Card>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { user, setActiveClient, setClients } = useAppStore()

  const { data: dash, isLoading: dashLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.get,
  })

  const { data: clients, isLoading: clientsLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: clientsApi.list,
    onSuccess: (data: Client[]) => setClients(data),
  } as Parameters<typeof useQuery>[0])

  const stats = dash?.stats

  const handleSelectClient = (c: Client) => {
    setActiveClient(c)
    navigate(`/filing`)
  }

  return (
    <div className="p-6 animate-fade-in">
      {/* Page head */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--forest-2)] mb-1">
            Practice overview
          </div>
          <h1 className="text-xl font-extrabold tracking-tight">
            {user?.name ? `Good morning, ${user.name}` : 'Dashboard'}
          </h1>
          <p className="text-sm text-[var(--ink-3)] mt-1">
            {Array.isArray(clients) ? `${clients.length} active client${clients.length === 1 ? '' : 's'}` : 'Loading...'} · {new Date().toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {dashLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="p-5"><Skeleton className="h-16" /></Card>
          ))
        ) : (
          <>
            <KpiCard label="Filings prepared" value={`${stats?.filings?.done ?? 0}/${stats?.filings?.total ?? 0}`} sub={stats?.filings?.delta ? `+${stats.filings.delta} since last week` : 'Ready for review'} icon={ClipboardCheck} color="var(--forest-3)" trend={stats?.filings?.delta ? `+${stats.filings.delta}` : undefined} />
            <KpiCard label="Open notices" value={stats?.openNotices ?? 0} sub="Awaiting reply" icon={Bell} color="var(--red)" />
            <KpiCard label="CA approved" value={stats?.approved ?? 0} sub="This month" icon={CheckCircle} color="var(--sage)" trend="+5" />
            <KpiCard label="ITC reconciled" value={stats?.itcReconciled ?? '₹0'} sub="Against GSTR-2B" icon={DollarSign} color="var(--amber-2)" trend="review" />
          </>
        )}
      </div>

      {/* Content grid */}
      <div className="grid lg:grid-cols-[1fr_296px] gap-4">
        {/* Client table */}
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Client compliance</CardTitle>
              <CardSub>{new Date().toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })} · return period</CardSub>
            </div>
            <button
              onClick={() => navigate('/clients')}
              className="text-xs text-[var(--forest-2)] font-semibold flex items-center gap-1 hover:underline"
            >
              View all <ChevronRight size={12} />
            </button>
          </CardHeader>
          {clientsLoading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10" />)}
            </div>
          ) : !Array.isArray(clients) || clients.length === 0 ? (
            <EmptyState
              icon="👥"
              title="No clients yet"
              body="Add your first client to start filing."
              action={<Button onClick={() => navigate('/clients')} size="sm"><Plus size={12} />Add client</Button>}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--surface-2)]">
                    {['Client', 'Filing', 'Risk', 'Score'].map((h) => (
                      <th key={h} className="text-left text-[10px] font-mono uppercase tracking-wider text-[var(--ink-4)] px-5 py-2.5">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(clients as Client[]).slice(0, 6).map((c) => (
                    <tr
                      key={c.gstin}
                      onClick={() => handleSelectClient(c)}
                      className="border-b border-[var(--border)] hover:bg-[var(--canvas)] cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-3">
                        <div className="text-sm font-bold">{c.name}</div>
                        <div className="text-[10px] font-mono text-[var(--ink-4)] mt-0.5">{c.gstin}</div>
                      </td>
                      <td className="px-5 py-3">
                        <StatusPill variant={(c.filing?.toLowerCase() as 'filed' | 'due' | 'overdue') || 'due'}>
                          {c.filing || 'Due'}
                        </StatusPill>
                      </td>
                      <td className="px-5 py-3">
                        <StatusPill variant={c.risk?.toLowerCase() === 'high' ? 'overdue' : c.risk?.toLowerCase() === 'low' ? 'filed' : 'due'}>
                          {c.risk || 'Med'}
                        </StatusPill>
                      </td>
                      <td className="px-5 py-3 w-32">
                        <ScoreBar score={c.score ?? 50} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Right panel */}
        <div className="flex flex-col gap-4">
          {/* Deadlines */}
          <Card>
            <CardHeader>
              <CardTitle>Upcoming deadlines</CardTitle>
            </CardHeader>
            <div className="px-5 py-8 text-center text-xs text-[var(--ink-3)]">
              No upcoming deadlines.
            </div>
          </Card>

          {/* Activity */}
          <Card>
            <CardHeader><CardTitle>Recent activity</CardTitle></CardHeader>
            <div className="px-5 py-8 text-center text-xs text-[var(--ink-3)]">
              No recent activity.
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
