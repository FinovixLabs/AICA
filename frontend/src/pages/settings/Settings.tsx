import { useAppStore } from '@/store/appStore'
import { Card, CardHeader, CardTitle } from '@/components/ui'
import { Sun, Moon, Shield, Lock, Users } from 'lucide-react'

function Toggle({ on, locked }: { on: boolean; locked?: boolean }) {
  return (
    <div className={`w-10 h-5 rounded-full flex items-center transition-all ${on ? 'bg-[var(--forest-3)]' : 'bg-[var(--border-2)]'} ${locked ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}>
      <div className={`w-4 h-4 rounded-full bg-white shadow transition-all ml-0.5 ${on ? 'ml-5' : ''}`} />
    </div>
  )
}

function SettingRow({ label, sub, on, locked }: { label: string; sub: string; on: boolean; locked?: boolean }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-[var(--border)] last:border-0">
      <div>
        <div className="text-sm font-semibold flex items-center gap-2">
          {label}
          {locked && <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[var(--forest-dim)] text-[var(--forest-2)]">enforced</span>}
        </div>
        <div className="text-xs text-[var(--ink-3)] mt-0.5">{sub}</div>
      </div>
      <Toggle on={on} locked={locked} />
    </div>
  )
}

export default function Settings() {
  const { theme, setTheme, user } = useAppStore()

  return (
    <div className="p-6 animate-fade-in">
      <div className="mb-6">
        <div className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--forest-2)] mb-1">Practice configuration</div>
        <h1 className="text-xl font-extrabold tracking-tight">Settings</h1>
        <p className="text-sm text-[var(--ink-3)] mt-1">Controls that govern how the assistant behaves across every client.</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-4 max-w-3xl">
        {/* Theme */}
        <Card>
          <CardHeader><CardTitle>Appearance</CardTitle></CardHeader>
          <div className="p-5">
            <div className="grid grid-cols-2 gap-3">
              {(['light', 'dark'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTheme(t)}
                  className={`flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                    theme === t
                      ? 'border-[var(--forest-2)] bg-[var(--forest-dim)]'
                      : 'border-[var(--border)] hover:border-[var(--border-2)]'
                  }`}
                >
                  <div className={`w-12 h-8 rounded-lg flex items-center justify-center ${t === 'light' ? 'bg-[#f5f5f0] border border-[#e5e5dc]' : 'bg-[#100e0a] border border-[#2e2820]'}`}>
                    {t === 'light' ? <Sun size={14} style={{ color: '#d97706' }} /> : <Moon size={14} style={{ color: '#f5a623' }} />}
                  </div>
                  <span className="text-xs font-semibold capitalize">{t}</span>
                </button>
              ))}
            </div>
          </div>
        </Card>

        {/* Connection */}
        <Card>
          <CardHeader><CardTitle>Connection</CardTitle></CardHeader>
          <div className="p-5 space-y-0">
            {[
              { label: 'API base', value: '/api (same origin)' },
              { label: 'Auth', value: user ? 'Token present' : 'Not signed in' },
              { label: 'Streaming chat', value: 'SSE enabled' },
              { label: 'Backend', value: 'FastAPI + Uvicorn' },
            ].map((r) => (
              <div key={r.label} className="flex items-center justify-between py-2.5 border-b border-[var(--border)] last:border-0">
                <span className="text-xs text-[var(--ink-3)]">{r.label}</span>
                <code className="text-xs bg-[var(--canvas)] px-2 py-0.5 rounded border border-[var(--border)] text-[var(--ink-2)] font-mono">{r.value}</code>
              </div>
            ))}
          </div>
        </Card>

        {/* Review controls */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield size={14} style={{ color: 'var(--forest-2)' }} />
              <CardTitle>Review & control</CardTitle>
            </div>
          </CardHeader>
          <div className="px-5 py-2">
            <SettingRow label="Require CA approval before final" sub="Every AI output stays a draft until approved." on={true} locked />
            <SettingRow label="Block portal auto-submission" sub="Never submits to the GST portal automatically." on={true} locked />
            <SettingRow label="Separate client & knowledge stores" sub="Client records and RAG knowledge never mix." on={true} locked />
          </div>
        </Card>

        {/* Firm profile */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Users size={14} style={{ color: 'var(--forest-2)' }} />
              <CardTitle>Firm profile</CardTitle>
            </div>
          </CardHeader>
          <div className="p-5 space-y-3">
            <div>
              <label className="block text-xs font-semibold text-[var(--ink-2)] mb-1.5">Firm name</label>
              <input
                defaultValue={user?.firm || ''}
                placeholder="Your CA firm name"
                className="w-full px-3 py-2 rounded-lg text-sm border border-[var(--border)] bg-[var(--canvas)] text-[var(--ink)] placeholder:text-[var(--ink-4)] focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[var(--ink-2)] mb-1.5">FRN</label>
              <input
                defaultValue={user?.frn || ''}
                placeholder="Firm Registration Number"
                className="w-full px-3 py-2 rounded-lg text-sm border border-[var(--border)] bg-[var(--canvas)] text-[var(--ink)] font-mono placeholder:text-[var(--ink-4)] focus:outline-none focus:border-[var(--accent)]"
              />
            </div>
            <div className="pt-1">
              <button className="text-xs font-semibold px-4 py-2 rounded-lg transition-all" style={{ background: 'var(--forest)', color: '#fff' }}>
                Save profile
              </button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
