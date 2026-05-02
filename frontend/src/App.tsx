import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useStore } from './store/useStore'
import { authApi } from './services/api'
import LoginPage from './components/Auth/LoginPage'
import RegisterPage from './components/Auth/RegisterPage'
import DashboardPage from './components/Board/DashboardPage'
import BoardPage from './components/Board/BoardPage'

function Private({ children }: { children: React.ReactNode }) {
  const auth = useStore(s => s.isAuthenticated)
  return auth ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  const { setUser, isAuthenticated } = useStore()

  useEffect(() => {
    const t = localStorage.getItem('access_token')
    if (t) {
      authApi.me()
        .then(r => setUser(r.data))
        .catch(() => { localStorage.clear(); setUser(null) })
    }
  }, [setUser])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
        <Route path="/register" element={isAuthenticated ? <Navigate to="/" replace /> : <RegisterPage />} />
        <Route path="/" element={<Private><DashboardPage /></Private>} />
        <Route path="/board/:boardId" element={<Private><BoardPage /></Private>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
