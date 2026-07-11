import { useNavigate } from 'react-router-dom'
import { useAppStore } from '@/store/appStore'
import { EmptyState, Button, Card, CardHeader, CardTitle, CardSub } from '@/components/ui'
import { MessageSquare, Upload, CheckCircle } from 'lucide-react'

export default function Notice() {
  const navigate = useNavigate()
  const { activeClient } = useAppStore()

  if (!activeClient) {
    return (
      <div className="p-6">
        <EmptyState
          icon="📨"
          title="No client selected"
          body="Pick a client to draft a notice reply."
          action={<Button onClick={() => navigate('/clients')}>Go to clients</Button>}
        />
      </div>
    )
  }

  return (
    <div className="p-6 animate-fade-in">
      <div className="mb-6">
        <div className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--forest-2)] mb-1">
          {activeClient.name} · {activeClient.gstin}
        </div>
        <h1 className="text-xl font-extrabold tracking-tight">Notice Reply Assistant</h1>
        <p className="text-sm text-[var(--ink-3)] mt-1">
          Classified, matched to client data and reply formats, then drafted. You approve before final.
        </p>
      </div>

      {/* Stepper */}
      <div className="flex items-center gap-2 mb-6">
        {['Notice uploaded', 'Classified', 'Data retrieved', 'Draft reply', 'Approve final'].map((step, i) => (
          <div key={step} className="flex items-center gap-2">
            <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${
              i < 2 ? 'bg-[var(--forest-soft)] text-[var(--forest)]'
              : i === 3 ? 'bg-[var(--amber-soft)] text-[var(--amber)]'
              : 'bg-[var(--border)] text-[var(--ink-3)]'
            }`}>
              {i < 2 ? <CheckCircle size={11} /> : <span className="w-4 h-4 rounded-full border flex items-center justify-center text-[9px]">{i + 1}</span>}
              {step}
            </div>
            {i < 4 && <div className="w-4 h-px bg-[var(--border-2)]" />}
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* Upload */}
        <Card>
          <CardHeader>
            <div><CardTitle>Upload SCN / Notice</CardTitle><CardSub>PDF or image</CardSub></div>
          </CardHeader>
          <div className="p-5">
            <div className="border-2 border-dashed border-[var(--border-2)] rounded-xl p-8 text-center cursor-pointer hover:border-[var(--forest-2)] hover:bg-[var(--forest-dim)] transition-all">
              <Upload size={24} className="mx-auto mb-3 text-[var(--ink-4)]" />
              <div className="text-sm font-semibold text-[var(--ink-2)]">Drop notice PDF or click</div>
              <div className="text-xs text-[var(--ink-4)] mt-1">SCN, demand notice, audit memo</div>
            </div>
            <div className="mt-4 p-3 rounded-lg bg-[var(--amber-soft)] border border-[var(--amber-dim)]">
              <p className="text-xs text-[var(--amber)] font-medium">
                Notice module coming soon. The RAG-powered drafting pipeline is being integrated.
              </p>
            </div>
          </div>
        </Card>

        {/* Notice meta placeholder */}
        <Card>
          <CardHeader><CardTitle>Notice details</CardTitle></CardHeader>
          <div className="p-5 space-y-3">
            {['Notice type', 'Section / Rule', 'Demand amount', 'Reply due', 'Issue raised'].map((l) => (
              <div key={l} className="flex items-center justify-between py-2 border-b border-[var(--border)] last:border-0">
                <span className="text-xs text-[var(--ink-3)]">{l}</span>
                <span className="text-xs text-[var(--ink-4)] font-mono">—</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Draft area placeholder */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div><CardTitle>Draft reply</CardTitle><CardSub>AI-generated · Pending CA review</CardSub></div>
              <span className="pill pill-ai"><span className="pill-dot" />AI Generated</span>
            </CardHeader>
            <div className="p-8 flex flex-col items-center justify-center text-center min-h-[200px]">
              <MessageSquare size={32} className="text-[var(--ink-4)] mb-3" />
              <div className="text-sm font-semibold text-[var(--ink-2)] mb-1">No draft yet</div>
              <div className="text-xs text-[var(--ink-3)] max-w-sm">
                Upload a show-cause notice above. AICA will classify it, retrieve relevant GST Act sections, and draft a point-by-point reply for your review.
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
