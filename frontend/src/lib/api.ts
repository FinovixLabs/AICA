import axios from 'axios'


const BASE = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: `${BASE}/api`,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aica_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }).then((r) => r.data),
  logout: () => api.post('/auth/logout').then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
}

// Dashboard
export const dashboardApi = {
  get: () => api.get('/dashboard').then((r) => r.data),
}

// Clients
export const clientsApi = {
  list: () => api.get('/clients').then((r) => r.data),
  get: (gstin: string) => api.get(`/clients/${gstin}`).then((r) => r.data),
  create: (data: { gstin: string; name: string; state?: string; type?: string; scheme?: string }) =>
    api.post('/clients', data).then((r) => r.data),
}

// Documents
export const documentsApi = {
  list: (gstin: string) => api.get(`/clients/${gstin}/documents`).then((r) => r.data),
  upload: (gstin: string, file: File, doc_type: string) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('doc_type', doc_type)
    return api.post(`/clients/${gstin}/documents`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data)
  },
}

// Filing
export const filingApi = {
  prerequisites: (gstin: string, filing_type: string) =>
    api.post('/filing/prerequisites', { gstin, filing_type }).then((r) => r.data),
  requirementsCheck: (gstin: string, period?: string) =>
    api.post('/filing/requirements-check', { gstin, period }).then((r) => r.data),
  classify: (gstin: string, period?: string) =>
    api.post('/filing/classify', { gstin, period }).then((r) => r.data),
  editOutput: (payload: {
    gstin: string; period?: string; instruction: string
    filing_csv: string; filing_json: Record<string, unknown>
  }) => api.post('/filing/edit-output', payload).then((r) => r.data),
}

// Chat — SSE streaming
export const chatApi = {
  stream: async (
    messages: { role: string; content: string }[],
    context: string,
    gstin: string | null,
    onToken: (t: string) => void
  ) => {
    const token = localStorage.getItem('aica_token')
    const res = await fetch(`${BASE}/api/chat?stream=true`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ messages, context, gstin }),
    })
    if (!res.ok || !res.body) throw new Error(`Chat error ${res.status}`)
    const reader = res.body.getReader()
    const dec = new TextDecoder()
    let buf = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buf += dec.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() ?? ''
      for (const line of lines) {
        const t = line.replace(/^data:\s*/, '').trim()
        if (t === '[DONE]') return
        try {
          const j = JSON.parse(t)
          if (j.token) onToken(j.token)
        } catch { /* ignore */ }
      }
    }
  },
}

// Notices
export const noticesApi = {
  draftReply: (gstin: string, noticeId: string) =>
    api.post('/notices/draft-reply', { gstin, noticeId }).then((r) => r.data),
  approveReply: (gstin: string, noticeId: string, html: string, version: string) =>
    api.post('/notices/approve', { gstin, noticeId, html, version }).then((r) => r.data),
  knowledge: (q?: string) =>
    api.get('/notices/knowledge', { params: { q } }).then((r) => r.data),
}

export default api