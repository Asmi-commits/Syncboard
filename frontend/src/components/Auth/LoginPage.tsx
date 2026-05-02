import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../../services/api'
import { useStore } from '../../store/useStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const setUser = useStore(s => s.setUser)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      const { data } = await authApi.login({ email, password })
      localStorage.setItem('access_token', data.access_token)
      if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
      setUser(data.user)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally { setLoading(false) }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-0)', position: 'relative' }}>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 70% 50% at 50% 0%, rgba(124,106,247,0.12) 0%, transparent 60%)', pointerEvents: 'none' }} />
      <div style={{ background: 'var(--bg-2)', border: '1px solid var(--border-hi)', borderRadius: 16, padding: '2.25rem', width: '100%', maxWidth: 400, boxShadow: '0 24px 64px rgba(0,0,0,0.5)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '1.75rem' }}>
          <span style={{ fontSize: 22 }}>⚡</span>
          <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 800, fontSize: 18, color: 'var(--accent)' }}>SyncBoard</span>
        </div>
        <h1 style={{ fontSize: 26, marginBottom: 6 }}>Welcome back</h1>
        <p style={{ color: 'var(--text-2)', marginBottom: '1.5rem', fontSize: 14 }}>Sign in to your workspace</p>
        <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label style={{ display: 'block', fontSize: 11, color: 'var(--text-2)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Email</label>
            <input className="input" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 11, color: 'var(--text-2)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Password</label>
            <input className="input" type="password" placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          {error && <p style={{ color: 'var(--red)', fontSize: 13, padding: '8px 12px', background: 'rgba(248,113,113,0.08)', borderRadius: 7 }}>{error}</p>}
          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: '100%', justifyContent: 'center', padding: '10px', marginTop: 4 }}>
            {loading ? <span className="spinner" /> : 'Sign In'}
          </button>
        </form>
        <p style={{ textAlign: 'center', marginTop: '1.25rem', color: 'var(--text-2)', fontSize: 13 }}>
          No account? <Link to="/register" style={{ color: 'var(--accent)' }}>Register</Link>
        </p>
      </div>
    </div>
  )
}
