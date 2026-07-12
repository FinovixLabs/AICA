import { create } from 'zustand'
import type { User, Client, ChatMessage, FilingResult } from '@/types'

type Theme = 'light' | 'dark'

interface AppState {
  // Auth
  user: User | null
  token: string | null
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  logout: () => void

  // Theme
  theme: Theme
  toggleTheme: () => void
  setTheme: (t: Theme) => void

  // Active client
  activeClient: Client | null
  setActiveClient: (c: Client | null) => void
  clients: Client[]
  setClients: (clients: Client[]) => void

  // Filing state
  lastFilingResult: FilingResult | null
  setLastFilingResult: (r: FilingResult | null) => void

  // Chat
  chatHistory: ChatMessage[]
  setChatHistory: (msgs: ChatMessage[]) => void
  appendChat: (msg: ChatMessage) => void
  clearChat: () => void

  // UI
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  toast: (msg: string, type?: 'success' | 'error' | 'info') => void
  toasts: { id: string; msg: string; type: string }[]
  removeToast: (id: string) => void
}

export const useAppStore = create<AppState>((set, get) => ({
  // Auth
  user: null,
  token: localStorage.getItem('aica_token'),
  setUser: (user) => set({ user }),
  setToken: (token) => {
    if (token) localStorage.setItem('aica_token', token)
    else localStorage.removeItem('aica_token')
    set({ token })
  },
  logout: () => {
    localStorage.removeItem('aica_token')
    set({ user: null, token: null, activeClient: null, clients: [] })
  },

  // Theme
  theme: (localStorage.getItem('aica_theme') as Theme) || 'light',
  toggleTheme: () => {
    const next = get().theme === 'light' ? 'dark' : 'light'
    localStorage.setItem('aica_theme', next)
    document.documentElement.classList.toggle('dark', next === 'dark')
    set({ theme: next })
  },
  setTheme: (t) => {
    localStorage.setItem('aica_theme', t)
    document.documentElement.classList.toggle('dark', t === 'dark')
    set({ theme: t })
  },

  // Clients
  activeClient: null,
  setActiveClient: (c) => set((state) => {
    if (state.activeClient?.gstin === c?.gstin) return { activeClient: c }
    return { activeClient: c, lastFilingResult: null, chatHistory: [] }
  }),
  clients: [],
  setClients: (clients) => set({ clients }),

  // Filing
  lastFilingResult: null,
  setLastFilingResult: (r) => set({ lastFilingResult: r }),

  // Chat
  chatHistory: [],
  setChatHistory: (msgs) => set({ chatHistory: msgs }),
  appendChat: (msg) => set((s) => ({ chatHistory: [...s.chatHistory, msg] })),
  clearChat: () => set({ chatHistory: [] }),

  // UI
  sidebarOpen: false,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toasts: [],
  toast: (msg, type = 'success') => {
    const id = Math.random().toString(36).slice(2)
    set((s) => ({ toasts: [...s.toasts, { id, msg, type }] }))
    setTimeout(() => get().removeToast(id), 3000)
  },
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))
