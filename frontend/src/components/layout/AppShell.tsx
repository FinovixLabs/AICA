import { useEffect } from 'react'
import { NavLink, useNavigate, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, Users, FileText, ClipboardCheck,
  Bell, BookOpen, Settings, LogOut, X,
  GitCompareArrows, Inbox, Send
} from 'lucide-react'
import { useAppStore } from '@/store/appStore'
import { authApi } from '@/lib/api'
import Toast from '@/components/shared/Toast'

const NAV_ITEMS = [
  { label: 'Workspace', items: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/clients', icon: Users, label: 'Clients' },
    { to: '/documents', icon: FileText, label: 'Documents' },
  ]},
  { label: 'Modules', items: [
    { to: '/filing', icon: ClipboardCheck, label: 'GST Filing' },
    { to: '/notices', icon: Bell, label: 'Notices', badge: 0 },
  ]},
  { label: 'Reconciliation', items: [
    { to: '/recon/gstr2b', icon: GitCompareArrows, label: 'GSTR-2B' },
    { to: '/recon/ims-inward', icon: Inbox, label: 'IMS Inward' },
    { to: '/recon/ims-outward', icon: Send, label: 'IMS Outward' },
  ]},
  { label: 'Reference', items: [
    { to: '/knowledge', icon: BookOpen, label: 'Knowledge' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ]},
]

export default function AppShell() {
  const { user, theme, logout, activeClient, sidebarOpen, setSidebarOpen, toasts } = useAppStore()
  const navigate = useNavigate()

  // Apply theme class on mount
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  const handleLogout = async () => {
    await authApi.logout().catch(() => {})
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--canvas)]">
      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* SIDEBAR */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-40
          w-[224px] flex-shrink-0 h-screen
          flex flex-col
          bg-[var(--sidebar-bg)]
          border-r border-[var(--sidebar-border)]
          transition-transform duration-300
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-[var(--sidebar-border)]">
          <div className="w-8 h-8 rounded-[9px] bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-md flex-shrink-0">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span className="text-base font-extrabold tracking-tight" style={{ color: 'var(--sidebar-text-active)', letterSpacing: '-0.03em' }}>
            AI<span style={{ color: theme === 'dark' ? 'var(--gold)' : '#fbbf24' }}>CA</span>
          </span>
          <button
            className="ml-auto lg:hidden text-[var(--sidebar-text)]"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={16} />
          </button>
        </div>

        {/* Active client chip */}
        {activeClient && (
          <div className="mx-3 mt-3 px-3 py-2 rounded-lg" style={{ background: 'var(--sidebar-active-bg)', border: '1px solid var(--sidebar-border)' }}>
            <div className="text-[10px] font-mono uppercase tracking-wider" style={{ color: 'var(--sidebar-label)' }}>Active client</div>
            <div className="text-sm font-semibold mt-0.5 truncate" style={{ color: 'var(--sidebar-text-active)' }}>{activeClient.name}</div>
            <div className="text-[10px] font-mono mt-0.5 opacity-50" style={{ color: 'var(--sidebar-text)' }}>{activeClient.gstin}</div>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-2 px-2">
          {NAV_ITEMS.map((group) => (
            <div key={group.label} className="mb-1">
              <div
                className="text-[10px] font-mono uppercase tracking-widest px-3 py-3 pb-1"
                style={{ color: 'var(--sidebar-label)' }}
              >
                {group.label}
              </div>
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => `
                    flex items-center gap-2.5 px-3 py-2 rounded-lg mb-0.5 text-[13px] font-medium
                    transition-all duration-150
                    ${isActive
                      ? 'bg-[var(--sidebar-active-bg)] text-[var(--sidebar-text-active)]'
                      : 'text-[var(--sidebar-text)] hover:bg-[var(--sidebar-hover-bg)] hover:text-[var(--sidebar-text-active)]'
                    }
                  `}
                  onClick={() => setSidebarOpen(false)}
                >
                  {({ isActive }) => (
                    <>
                      <item.icon
                        size={14}
                        style={{ color: isActive ? (theme === 'dark' ? 'var(--gold)' : '#fbbf24') : 'currentColor' }}
                      />
                      {item.label}
                      {'badge' in item && item.badge != null && item.badge > 0 && (
                        <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded bg-[var(--red-dim)] text-[var(--red)] font-mono">
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {/* Bottom user row */}
        <div className="p-3 border-t border-[var(--sidebar-border)]">
          <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg hover:bg-[var(--sidebar-hover-bg)] cursor-pointer transition-all">
            <div className="w-8 h-8 rounded-[9px] bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
              {user?.initials || 'CA'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-bold truncate" style={{ color: 'var(--sidebar-text-active)' }}>
                {user?.name || 'CA User'}
              </div>
              <div className="text-[10px] truncate" style={{ color: 'var(--sidebar-label)' }}>
                {user?.frn ? `FRN ${user.frn}` : user?.firm || 'Chartered Accountant'}
              </div>
            </div>
            <button onClick={handleLogout} title="Sign out" className="flex-shrink-0" style={{ color: 'var(--sidebar-label)' }}>
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>

      {/* MAIN */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* PAGE CONTENT */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      {/* TOASTS */}
      <div id="toast-root">
        {toasts.map((t) => (
          <Toast key={t.id} msg={t.msg} type={t.type as 'success' | 'error' | 'info'} />
        ))}
      </div>
    </div>
  )
}
