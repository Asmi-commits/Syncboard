import axios from 'axios'

// On Render: use the backend's public URL via env var
// Locally: use /api (proxied by Vite)
const BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

const http = axios.create({ baseURL: BASE, headers: { 'Content-Type': 'application/json' } })

http.interceptors.request.use(cfg => {
  const t = localStorage.getItem('access_token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

http.interceptors.response.use(r => r, async err => {
  if (err.response?.status === 401) {
    localStorage.clear()
    window.location.href = '/login'
  }
  return Promise.reject(err)
})

export const authApi = {
  register: (d: { email: string; username: string; password: string; full_name?: string }) =>
    http.post('/auth/register', d),
  login: (d: { email: string; password: string }) =>
    http.post('/auth/login', d),
  me: () => http.get('/auth/me'),
}

export const boardsApi = {
  list: () => http.get('/boards/'),
  create: (d: any) => http.post('/boards/', d),
  get: (id: number) => http.get(`/boards/${id}`),
  update: (id: number, d: any) => http.patch(`/boards/${id}`, d),
  delete: (id: number) => http.delete(`/boards/${id}`),
  inviteMember: (boardId: number, d: { user_id: number; role?: string }) =>
    http.post(`/boards/${boardId}/members`, d),
  createColumn: (boardId: number, d: any) => http.post(`/boards/${boardId}/columns`, d),
}

export const tasksApi = {
  list: (boardId: number) => http.get(`/tasks/boards/${boardId}/tasks`),
  create: (boardId: number, d: any) => http.post(`/tasks/boards/${boardId}/tasks`, d),
  get: (id: number) => http.get(`/tasks/${id}`),
  update: (id: number, d: any) => http.patch(`/tasks/${id}`, d),
  move: (id: number, d: { column_id: number; position: number }) =>
    http.post(`/tasks/${id}/move`, d),
  delete: (id: number) => http.delete(`/tasks/${id}`),
}
