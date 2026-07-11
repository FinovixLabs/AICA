import { useQuery } from '@tanstack/react-query'
import { noticesApi } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardSub, Skeleton } from '@/components/ui'
import { BookOpen, Database, FileText, Clock } from 'lucide-react'

export default function Knowledge() {
  const { data: k, isLoading } = useQuery({
    queryKey: ['knowledge'],
    queryFn: () => noticesApi.knowledge(),
  })

  const stats = k?.stats || {}

  return (
    <div className="p-6 animate-fade-in">
      <div className="mb-6">
        <div className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--forest-2)] mb-1">
          RAG reference · not client data
        </div>
        <h1 className="text-xl font-extrabold tracking-tight">GST Knowledge Base</h1>
        <p className="text-sm text-[var(--ink-3)] mt-1">
          Reference material retrieved during drafting. Kept separate from all client records.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Knowledge chunks', value: stats.chunks ?? 0, icon: Database, color: 'var(--forest-3)' },
          { label: 'Reply templates', value: stats.templates ?? 0, icon: FileText, color: 'var(--amber-2)' },
          { label: 'Return forms', value: stats.forms ?? 0, icon: BookOpen, color: 'var(--sage)' },
          { label: 'Last updated', value: stats.updated || '—', icon: Clock, color: 'var(--ink-3)' },
        ].map((s) => (
          <Card key={s.label} className="p-5">
            {isLoading ? (
              <Skeleton className="h-14" />
            ) : (
              <>
                <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-3" style={{ background: `${s.color}18` }}>
                  <s.icon size={15} style={{ color: s.color }} />
                </div>
                <div className="text-xs text-[var(--ink-3)] mb-1">{s.label}</div>
                <div className="text-xl font-bold num" style={{ color: s.color }}>{s.value}</div>
              </>
            )}
          </Card>
        ))}
      </div>

      {/* Info */}
      <div className="grid lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <div><CardTitle>Hybrid retrieval</CardTitle><CardSub>BM25 + PGVector ensemble</CardSub></div>
          </CardHeader>
          <div className="p-5 space-y-3 text-xs text-[var(--ink-2)]">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)]">
              <div className="w-6 h-6 rounded bg-[var(--forest-dim)] flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-[10px] font-mono font-bold text-[var(--forest-2)]">0.4</span>
              </div>
              <div>
                <div className="font-semibold mb-0.5">BM25 sparse retrieval</div>
                <div className="text-[var(--ink-3)] leading-relaxed">Keyword matching for exact GST section references, circular numbers, notification IDs.</div>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)]">
              <div className="w-6 h-6 rounded bg-[var(--amber-dim)] flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-[10px] font-mono font-bold text-[var(--amber)]">0.6</span>
              </div>
              <div>
                <div className="font-semibold mb-0.5">PGVector dense retrieval</div>
                <div className="text-[var(--ink-3)] leading-relaxed">Semantic search via OpenAI embeddings for conceptually similar GST provisions and case contexts.</div>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <div><CardTitle>Ingestion pipeline</CardTitle><CardSub>How knowledge is added</CardSub></div>
          </CardHeader>
          <div className="p-5 space-y-2 text-xs">
            {[
              { step: '1', label: 'Pre-chunked GST docs ingested', sub: 'gst_filing.txt, gst_notice.txt with [CHUNK_] markers' },
              { step: '2', label: 'Uploaded with content hash', sub: 'Deduplication on re-ingest' },
              { step: '3', label: 'Stored in langchain_pg_embedding', sub: 'PGVector table in Supabase' },
              { step: '4', label: 'BM25 index rebuilt at startup', sub: 'From langchain_pg_collection table' },
            ].map((s) => (
              <div key={s.step} className="flex items-start gap-3 py-2 border-b border-[var(--border)] last:border-0">
                <div className="w-5 h-5 rounded-full bg-[var(--forest-dim)] flex items-center justify-center flex-shrink-0 text-[10px] font-bold text-[var(--forest-2)]">
                  {s.step}
                </div>
                <div>
                  <div className="font-semibold text-[var(--ink)]">{s.label}</div>
                  <div className="text-[var(--ink-3)] mt-0.5">{s.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
