import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Eye, EyeOff, ArrowRight } from 'lucide-react'
import { authApi } from '@/lib/api'
import { useAppStore } from '@/store/appStore'
import { Input } from '@/components/ui'

export default function Login() {
  const navigate = useNavigate()
  const { setUser, setToken, theme } = useAppStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) { setError('Email and password are required'); return }
    setLoading(true); setError('')
    try {
      const data = await authApi.login(email, password)
      setToken(data.token)
      setUser(data.user)
      navigate('/dashboard')
    } catch {
      setError('Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-[1.1fr_1fr]" style={{ background: 'var(--canvas)', overflow: 'auto' }}>
      {/* LEFT — brand panel */}
      <div className="relative flex flex-col justify-between p-12 bg-[var(--forest)] overflow-hidden">
        {/* Grid */}
        <div className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)',
            backgroundSize: '48px 48px'
          }}
        />
        {/* Decorative circle */}
        <div className="absolute right-[-120px] bottom-[-120px] w-[400px] h-[400px] rounded-full border border-white/10 pointer-events-none" />
        <div className="absolute right-[-60px] bottom-[-60px] w-[280px] h-[280px] rounded-full border border-white/5 pointer-events-none" />

        {/* Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-9 h-9 rounded-[10px] bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-lg">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span className="text-xl font-extrabold text-white tracking-tight" style={{ letterSpacing: '-0.03em' }}>
            AI<span className="text-amber-300">CA</span>
          </span>
        </div>

        {/* Pitch */}
        <div className="relative z-10 max-w-sm">
          <div className="text-xs font-mono font-bold uppercase tracking-widest text-amber-300/70 mb-4">
            GST Compliance Workspace
          </div>
          <h1 className="text-4xl font-extrabold text-white leading-[1.1] mb-4" style={{ letterSpacing: '-0.04em' }}>
            Smart filing.<br />
            <span className="text-amber-300">CA in control.</span>
          </h1>
          <p className="text-white/50 text-base leading-relaxed mb-8">
            Classify sales registers, generate GSTR-1 JSON, draft notice replies — with you approving every step.
          </p>
          <div className="flex flex-col gap-3">
            {['No portal automation', 'CA approval on every output', 'Client data isolated per GSTIN'].map((t) => (
              <div key={t} className="flex items-center gap-2.5 text-white/60 text-sm">
                <div className="w-4 h-4 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                </div>
                {t}
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-white/25 text-xs">© 2026 AICA · Not affiliated with ICAI</p>
      </div>

      {/* RIGHT — form */}
      <div className="flex items-center justify-center p-8 bg-[var(--surface)]">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-[9px] bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              </svg>
            </div>
            <span className="text-lg font-extrabold tracking-tight">AI<span style={{ color: 'var(--forest-2)' }}>CA</span></span>
          </div>

          <div className="mb-7">
            <h2 className="text-2xl font-extrabold tracking-tight mb-1.5" style={{ letterSpacing: '-0.03em' }}>
              Welcome back
            </h2>
            <p className="text-sm text-[var(--ink-3)]">Sign in to your CA workspace</p>
          </div>

          {error && (
            <div className="mb-4 px-4 py-3 rounded-lg bg-[var(--red-dim)] border border-[var(--red-soft)] text-[var(--red)] text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--ink-2)] mb-1.5 tracking-wide">
                Work email
              </label>
              <Input
                type="email"
                placeholder="you@cafirm.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[var(--ink-2)] mb-1.5 tracking-wide">
                Password
              </label>
              <div className="relative">
                <Input
                  type={showPw ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--ink-4)] hover:text-[var(--ink-2)]"
                >
                  {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-2 text-[var(--ink-3)] cursor-pointer">
                <input type="checkbox" className="rounded" />
                Remember me
              </label>
              <a href="#" className="text-[var(--forest-2)] font-semibold hover:underline">
                Forgot password?
              </a>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-bold transition-all disabled:opacity-60"
              style={{ background: 'var(--forest)', color: '#fff' }}
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>Sign in to workspace <ArrowRight size={14} /></>
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-xs text-[var(--ink-3)]">
            Don't have an account?{' '}
            <Link to="/" className="text-[var(--forest-2)] font-semibold hover:underline">
              Request access
            </Link>
          </div>

          <div className="mt-4 pt-4 border-t border-[var(--border)] text-center text-xs text-[var(--ink-4)] font-mono">
            v0.1.0 · AICA GST Workspace
          </div>
        </div>
      </div>
    </div>
  )
}
