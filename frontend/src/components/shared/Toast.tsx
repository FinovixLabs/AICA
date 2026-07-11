import { CheckCircle, XCircle, Info } from 'lucide-react'

export default function Toast({ msg, type = 'success' }: { msg: string; type?: 'success' | 'error' | 'info' }) {
  const icon = type === 'success' ? <CheckCircle size={14} /> : type === 'error' ? <XCircle size={14} /> : <Info size={14} />
  const color = type === 'success' ? 'var(--forest-2)' : type === 'error' ? 'var(--red)' : 'var(--amber)'

  return (
    <div
      className="flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg animate-fade-in pointer-events-auto"
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border-2)',
        color: 'var(--ink)',
        minWidth: '220px',
        maxWidth: '360px',
      }}
    >
      <span style={{ color }}>{icon}</span>
      <span className="text-sm font-medium">{msg}</span>
    </div>
  )
}
