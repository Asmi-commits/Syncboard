import axios from 'axios'

const BASE = '/api'

const http = axios.create({ baseURL: BASE, headers: { 'Content-Type': 'application/json' } })

http.interceptors.request.use(cfg => {
  const t = localStorage.getItem('access_token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

http.interceptors.response.use(r => r, async err => {
  const orig = err.config
  if (err.response?.status === 401 && !orig._retry) {
    orig._retry = true
    try {
      const rt = localStorage.getItem('refresh_token')
      const { data } = await axios.post(`${BASE}/auth/refresh`, { refresh_token: rt })
      localStorage.setItem('access_token', data.access_token)
      orig.headers.Authorization = `Bearer ${data.access_token}`
      return http(orig)
    } catch {
      localStorage.clear()
      window.location.href = '/login'
    }
  }
  return Promise.reject(err)
})

export const authApi = {
  register: (d: any) => http.post('/auth/register', d),
  login: (d: any) => http.post('/auth/login', d),
  me: () => http.get('/auth/me'),
}

export const boardsApi = {
  list: () => http.get('/boards/'),
  create: (d: any) => http.post('/boards/', d),
  get: (id: number) => http.get(`/boards/${id}`),
  update: (id: number, d: any) => http.patch(`/boards/${id}`, d),
  delete: (id: number) => http.delete(`/boards/${id}`),
  addMember: (bid: number, uid: number, role = 'member') =>
    http.post(`/boards/${bid}/members`, { user_id: uid, role }),
  createColumn: (bid: number, d: any) => http.post(`/boards/${bid}/columns`, d),
}

export const tasksApi = {
  list: (boardId: number) => http.get(`/tasks/boards/${boardId}/tasks`),
  create: (boardId: number, d: any) => http.post(`/tasks/boards/${boardId}/tasks`, d),
  get: (id: number) => http.get(`/tasks/${id}`),
  update: (id: number, d: any) => http.patch(`/tasks/${id}`, d),
  move: (id: number, d: any) => http.post(`/tasks/${id}/move`, d),
  delete: (id: number) => http.delete(`/tasks/${id}`),
}
