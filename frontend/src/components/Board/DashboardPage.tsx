import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { boardsApi } from '../../services/api'
import { useStore, Board } from '../../store/useStore'

const COLORS = ['#7c6af7','#f7706a','#4ade80','#60a5fa','#fbbf24','#f472b6','#34d399','#a78bfa']

export default function DashboardPage() {
  const navigate = useNavigate()
  const { boards, setBoards, user, setUser } = useStore()
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', color: COLORS[0] })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    boardsApi.list()
      .then(r => { setBoards(r.data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [setBoards])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault(); setCreating(true)
    try {
      const { data } = await boardsApi.create(form)
      setBoards([...boards, data])
      navigate(`/board/${data.id}`)
    } finally { setCreating(false) }
  }

  const logout = () => { localStorage.clear(); setUser(null); navigate('/login') }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-0)' }}>
      <header style={{ background: 'var(--bg-1)', borderBottom: '1px solid var(--border)', height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 1.5rem', position: 'sticky', top: 0, zIndex: 50 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>⚡</span>
          <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 800, color: 'var(--accent)' }}>SyncBoard</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ color: 'var(--text-2)', fontSize: 13 }}>{user?.full_name || user?.username}</span>
          <button className="btn btn-ghost btn-sm" onClick={logout}>Sign out</button>
        </div>
      </header>

      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '2.5rem 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: '2rem' }}>
          <div>
            <h1 style={{ fontSize: 28 }}>Your Boards</h1>
            <p style={{ color: 'var(--text-2)', marginTop: 4, fontSize: 13 }}>{boards.length} board{boards.length !== 1 ? 's' : ''}</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ New Board</button>
        </div>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><span className="spinner" style={{ width: 32, height: 32 }} /></div>
        ) : boards.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-2)' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>🗂️</div>
            <p style={{ marginBottom: '1rem' }}>No boards yet</p>
            <button className="btn btn-primary" onClick={() => setShowCreate(true)}>Create your first board</button>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.25rem' }}>
            {boards.map((b, i) => <BoardCard key={b.id} board={b} index={i} onClick={() => navigate(`/board/${b.id}`)} />)}
          </div>
        )}
      </main>

      {showCreate && (
        <div className="overlay" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ padding: '1.75rem' }}>
            <h2 style={{ marginBottom: '1.25rem', fontSize: 20 }}>New Board</h2>
            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ display: 'block', fontSize: 11, color: 'var(--text-2)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Name *</label>
                <input className="input" placeholder="e.g. Product Roadmap" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required autoFocus />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 11, color: 'var(--text-2)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Description</label>
                <input className="input" placeholder="Optional" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 11, color: 'var(--text-2)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Color</label>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {COLORS.map(c => (
                    <button key={c} type="button" onClick={() => setForm({ ...form, color: c })}
                      style={{ width: 28, height: 28, borderRadius: '50%', background: c, border: form.color === c ? '3px solid white' : '3px solid transparent', cursor: 'pointer', outline: 'none', transition: 'transform 0.12s' }}
                      onMouseOver={e => { e.currentTarget.style.transform = 'scale(1.2)' }}
                      onMouseOut={e => { e.currentTarget.style.transform = 'scale(1)' }}
                    />
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 4 }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={creating}>{creating ? <span className="spinner" /> : 'Create'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

function BoardCard({ board, index, onClick }: { board: Board; index: number; onClick: () => void }) {
  const taskCount = board.columns?.reduce((a, c) => a + (c.tasks?.length || 0), 0) || 0
  const doneCount = board.columns?.reduce((a, c) => a + (c.tasks?.filter(t => t.is_completed).length || 0), 0) || 0
  const pct = taskCount > 0 ? Math.round((doneCount / taskCount) * 100) : 0

  return (
    <div onClick={onClick}
      style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 12, padding: '1.25rem', cursor: 'pointer', transition: 'all 0.15s', animation: `fadeUp 0.3s ease ${index * 0.05}s both` }}
      onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--border-hi)'; e.currentTarget.style.transform = 'translateY(-2px)' }}
      onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.transform = 'none' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <div style={{ width: 36, height: 36, borderRadius: 9, background: `${board.color}20`, border: `2px solid ${board.color}40`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16 }}>📋</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={{ fontFamily: 'Syne, sans-serif', fontSize: 14, fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{board.name}</h3>
          <p style={{ color: 'var(--text-3)', fontSize: 11 }}>{board.members?.length || 0} members</p>
        </div>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: board.color, boxShadow: `0 0 6px ${board.color}` }} />
      </div>
      {board.description && <p style={{ color: 'var(--text-2)', fontSize: 13, marginBottom: 10, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' as any }}>{board.description}</p>}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-3)', marginBottom: 4 }}>
          <span>{doneCount}/{taskCount} done</span><span>{pct}%</span>
        </div>
        <div style={{ height: 3, background: 'var(--bg-4)', borderRadius: 2 }}>
          <div style={{ height: '100%', width: `${pct}%`, background: board.color, borderRadius: 2, transition: 'width 0.5s ease' }} />
        </div>
      </div>
    </div>
  )
}
