import { Routes, Route, Navigate } from 'react-router-dom'
import { useAppStore } from '@/store/appStore'
import AppShell from '@/components/layout/AppShell'
import Landing from '@/pages/Landing'
import Login from '@/pages/auth/Login'
import Dashboard from '@/pages/dashboard/Dashboard'
import ClientList from '@/pages/clients/ClientList'
import Documents from '@/pages/documents/Documents'
import Filing from '@/pages/filing/Filing'
import Notice from '@/pages/notice/Notice'
import Knowledge from '@/pages/knowledge/Knowledge'
import Settings from '@/pages/settings/Settings'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token } = useAppStore()
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />

      {/* Protected app shell */}
      <Route
        path="/"
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="clients" element={<ClientList />} />
        <Route path="documents" element={<Documents />} />
        <Route path="filing" element={<Filing />} />
        <Route path="notices" element={<Notice />} />
        <Route path="knowledge" element={<Knowledge />} />
        <Route path="settings" element={<Settings />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
