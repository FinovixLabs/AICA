import { useNavigate } from 'react-router-dom'
import { ArrowRight, CheckCircle, Shield, Zap, FileCheck, Users, Lock } from 'lucide-react'

const FEATURES = [
  { icon: FileCheck, title: 'GSTR-1 Classification', desc: 'Upload your sales register. Every invoice classified to B2B, B2CL, B2CS, EXP using GST Act rules — deterministic, not AI guesswork.' },
  { icon: Zap, title: 'Instant JSON Export', desc: 'Portal-ready GSTR-1 JSON structured to the exact GST schema. Download and upload directly. No manual entry.' },
  { icon: Users, title: 'Client-wise Isolation', desc: 'Every client\'s documents stored in isolated partitions. GST knowledge base never mixes with client data.' },
  { icon: Shield, title: 'Notice Reply Drafting', desc: 'Upload an SCN. AICA retrieves relevant GST Act sections and drafts a point-by-point reply for your review.' },
  { icon: Lock, title: 'CA Approval Gate', desc: 'Every output is a draft until you approve it. Nothing is final without your sign-off. Full audit trail retained.' },
  { icon: Zap, title: 'Streaming AI Assistant', desc: 'Ask questions about any filing. The assistant retrieves from client documents and the GST knowledge base in real time.' },
]

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[var(--canvas)] text-[var(--ink)]" >
      {/* NAV */}
      <nav className="sticky top-0 z-50 flex items-center justify-between px-8 h-14 bg-[var(--forest)] border-b border-[rgba(255,255,255,0.1)]">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-md">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span className="text-base font-extrabold tracking-tight text-white" style={{ letterSpacing: '-0.03em' }}>
            AI<span className="text-amber-300">CA</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/login')}
            className="text-sm font-semibold text-white/70 hover:text-white transition-colors px-3 py-1.5"
          >
            Sign in
          </button>
          <button
            onClick={() => navigate('/login')}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-amber-500 text-white text-sm font-bold hover:bg-amber-400 transition-all shadow-sm"
          >
            Get access <ArrowRight size={13} />
          </button>
        </div>
      </nav>

      {/* HERO */}
      <div className="bg-[var(--forest)] pt-20 pb-0 px-8 text-white relative overflow-hidden">
        {/* Grid background */}
        <div className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)',
            backgroundSize: '48px 48px'
          }}
        />
        <div className="max-w-5xl mx-auto relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-amber-500/20 border border-amber-400/30 text-amber-300 text-xs font-semibold font-mono uppercase tracking-wider mb-6">
            🇮🇳 Built for Indian CAs
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight leading-[1.06] mb-5" style={{ letterSpacing: '-0.04em' }}>
            GST compliance,<br />
            <span className="text-amber-300">done right.</span>
          </h1>
          <p className="text-lg text-white/60 max-w-xl leading-relaxed mb-8">
            Classify sales registers, generate GSTR-1 JSON, draft notice replies — all from a single workspace built for Chartered Accountants. Zero portal automation. Zero auto-submission.
          </p>
          <div className="flex items-center gap-3 mb-12">
            <button
              onClick={() => navigate('/login')}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-amber-500 text-white font-bold text-sm hover:bg-amber-400 transition-all shadow-lg"
            >
              Start free <ArrowRight size={15} />
            </button>
            <div className="flex items-center gap-4 text-white/40 text-xs">
              <span className="flex items-center gap-1.5"><CheckCircle size={12} className="text-green-400" />No portal login</span>
              <span className="flex items-center gap-1.5"><CheckCircle size={12} className="text-green-400" />CA approval gated</span>
              <span className="flex items-center gap-1.5"><CheckCircle size={12} className="text-green-400" />Data isolated</span>
            </div>
          </div>

          {/* Dashboard preview */}
          <div className="rounded-t-xl overflow-hidden border border-white/10 shadow-2xl" style={{ background: 'var(--canvas)' }}>
            <div className="flex items-center gap-1.5 px-4 py-2.5 bg-white/5 border-b border-white/10">
              <div className="w-2.5 h-2.5 rounded-full bg-red-400/60" />
              <div className="w-2.5 h-2.5 rounded-full bg-amber-400/60" />
              <div className="w-2.5 h-2.5 rounded-full bg-green-400/60" />
              <span className="ml-3 text-xs text-white/30 font-mono">aica.app/dashboard</span>
            </div>
            <div className="grid grid-cols-4 gap-3 p-4">
              {[
                { label: 'Filings ready', val: '18/24', color: 'var(--forest-3)' },
                { label: 'Open notices', val: '3', color: 'var(--red)' },
                { label: 'CA approved', val: '12', color: 'var(--sage)' },
                { label: 'ITC reconciled', val: '₹2.4L', color: 'var(--amber-2)' },
              ].map((s) => (
                <div key={s.label} className="rounded-lg p-3 border border-[var(--border)] bg-[var(--surface)]">
                  <div className="text-xs text-[var(--ink-3)] mb-1">{s.label}</div>
                  <div className="text-xl font-bold num" style={{ color: s.color }}>{s.val}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* FEATURES */}
      <div className="max-w-5xl mx-auto px-8 py-20">
        <div className="text-center mb-12">
          <div className="text-xs font-mono font-bold uppercase tracking-widest text-[var(--forest-2)] mb-3">Core capabilities</div>
          <h2 className="text-3xl font-extrabold tracking-tight mb-3" style={{ letterSpacing: '-0.04em' }}>
            Everything your practice needs
          </h2>
          <p className="text-[var(--ink-3)] text-base max-w-md mx-auto">
            AICA handles the mechanical work. You handle the judgment calls.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="p-6 rounded-xl bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--border-2)] hover:-translate-y-0.5 transition-all duration-200 group"
            >
              <div className="w-9 h-9 rounded-lg bg-[var(--forest-dim)] flex items-center justify-center mb-4 group-hover:bg-[var(--forest-soft)] transition-colors">
                <f.icon size={18} color="var(--forest-2)" />
              </div>
              <div className="font-bold text-sm mb-2">{f.title}</div>
              <div className="text-xs text-[var(--ink-3)] leading-relaxed">{f.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* HOW IT WORKS */}
      <div className="bg-[var(--forest)] text-white py-20 px-8">
        <div className="max-w-5xl mx-auto">
          <div className="text-xs font-mono font-bold uppercase tracking-widest text-amber-300 mb-3">How it works</div>
          <h2 className="text-3xl font-extrabold tracking-tight mb-2" style={{ letterSpacing: '-0.04em' }}>GSTR-1 in 4 steps</h2>
          <p className="text-white/50 text-base mb-10">From upload to export in under 5 minutes.</p>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-1 rounded-xl overflow-hidden border border-white/10">
            {[
              { n: '01', t: 'Upload', d: 'Drop your sales register CSV. AICA identifies column structure automatically.' },
              { n: '02', t: 'Classify', d: 'Every invoice row classified to the correct GSTR-1 table using GST Act rules.' },
              { n: '03', t: 'Review', d: 'Browse the classified output. Query the assistant. Make corrections.' },
              { n: '04', t: 'Export', d: 'Download portal-ready JSON and CA-readable CSV. You upload to GST portal.' },
            ].map((s) => (
              <div key={s.n} className="p-6 bg-white/[0.03] border-r border-white/10 last:border-r-0">
                <div className="text-amber-300 text-xs font-mono font-bold mb-3">{s.n} / {s.t}</div>
                <div className="text-white font-bold text-sm mb-2">{s.t}</div>
                <div className="text-white/40 text-xs leading-relaxed">{s.d}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="py-20 px-8 text-center">
        <h2 className="text-3xl font-extrabold tracking-tight mb-3" style={{ letterSpacing: '-0.04em' }}>
          Ready to file smarter?
        </h2>
        <p className="text-[var(--ink-3)] mb-6">Join CA firms using AICA to cut filing time from hours to minutes.</p>
        <button
          onClick={() => navigate('/login')}
          className="inline-flex items-center gap-2 px-7 py-3 rounded-xl bg-[var(--forest)] text-white font-bold hover:bg-[var(--forest-2)] transition-all"
        >
          Get started <ArrowRight size={15} />
        </button>
      </div>

      {/* FOOTER */}
      <footer className="border-t border-[var(--border)] px-8 py-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            </svg>
          </div>
          <span className="text-sm font-bold">AICA</span>
        </div>
        <p className="text-xs text-[var(--ink-4)]">© 2026 AICA. Built for Indian Chartered Accountants. Not affiliated with ICAI.</p>
        <p className="text-xs font-mono text-[var(--ink-4)]">v0.1.0</p>
      </footer>
    </div>
  )
}
