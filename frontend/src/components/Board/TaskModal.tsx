import { useState } from 'react'
import { tasksApi } from '../../services/api'
import { Task, Column } from '../../store/useStore'

const PRIORITIES = ['low', 'medium', 'high', 'urgent']
const P_COLOR: Record<string, string> = { low: '#4ade80', medium: '#60a5fa', high: '#fbbf24', urgent: '#f87171' }

interface Props {
  task: Task; columns: Column[]
  onClose: () => void
  onUpdate: (id: number, c: Partial<Task>) => void
  onDelete: (id: number) => void
}

export default function TaskModal({ task, columns, onClose, onUpdate, onDelete }: Props) {
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(task.title)
  const [desc, setDesc] = useState(task.description || '')
  const [saving, setSaving] = useState(false)

  const save = async () => {
    if (!title.trim()) return
    setSaving(true)
    try {
      const { data } = await tasksApi.update(task.id, { title: title.trim(), description: desc })
      onUpdate(task.id, { title: data.title, description: data.description })
      setEditing(false)
    } finally { setSaving(false) }
  }

  const changePriority = async (priority: string) => {
    await tasksApi.update(task.id, { priority })
    onUpdate(task.id, { priority })
  }

  const toggleComplete = async () => {
    const { data } = await tasksApi.update(task.id, { is_completed: !task.is_completed })
    onUpdate(task.id, { is_completed: data.is_completed })
  }

  const del = async () => {
    if (!window.confirm('Delete this task?')) return
    await tasksApi.delete(task.id)
    onDelete(task.id)
  }

  const lbl = (t: string) => <label style={{ display: 'block', fontSize: 11, color: 'var(--text-3)', marginBottom: 5, textTransform: 'uppercase' as const, letterSpacing: '0.06em' }}>{t}</label>

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem 1.25rem', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', gap: 6 }}>
            <span className="badge" style={{ background: `${P_COLOR[task.priority]}20`, color: P_COLOR[task.priority] }}>{task.priority}</span>
            <span className="badge" style={{ background: 'var(--bg-3)', color: 'var(--text-2)' }}>#{task.id}</span>
            {task.is_completed && <span className="badge" style={{ background: 'rgba(74,222,128,0.12)', color: '#4ade80' }}>completed</span>}
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="btn btn-danger btn-sm" onClick={del}>Delete</button>
            <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
          </div>
        </div>

        <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
          {editing ? (
            <div>
              <input className="input" value={title} onChange={e => setTitle(e.target.value)} autoFocus style={{ fontWeight: 600, marginBottom: 8 }} />
              <textarea className="input" value={desc} onChange={e => setDesc(e.target.value)} rows={3} placeholder="Description..." style={{ resize: 'vertical', fontFamily: 'DM Sans, sans-serif' }} />
              <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                <button className="btn btn-primary btn-sm" onClick={save} disabled={saving}>{saving ? '...' : 'Save'}</button>
                <button className="btn btn-ghost btn-sm" onClick={() => { setEditing(false); setTitle(task.title); setDesc(task.description || '') }}>Cancel</button>
              </div>
            </div>
          ) : (
            <div onClick={() => setEditing(true)} style={{ cursor: 'text' }}>
              <h2 style={{ fontSize: 18, marginBottom: 6 }}>{task.title}</h2>
              <p style={{ color: task.description ? 'var(--text-2)' : 'var(--text-3)', fontSize: 14, lineHeight: 1.6 }}>{task.description || 'Click to add description...'}</p>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              {lbl('Priority')}
              <select className="input" value={task.priority} onChange={e => changePriority(e.target.value)} style={{ cursor: 'pointer' }}>
                {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              {lbl('Column')}
              <select className="input" value={task.column_id} style={{ cursor: 'pointer' }} onChange={async e => {
                const colId = Number(e.target.value)
                await tasksApi.move(task.id, { column_id: colId, position: 0 })
                onUpdate(task.id, { column_id: colId })
              }}>
                {columns.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              onClick={toggleComplete}
              className={task.is_completed ? 'btn btn-primary btn-sm' : 'btn btn-ghost btn-sm'}
              style={{ flex: 1, justifyContent: 'center' }}>
              {task.is_completed ? '✓ Completed' : 'Mark complete'}
            </button>
          </div>

          <div style={{ fontSize: 12, color: 'var(--text-3)', display: 'flex', gap: 12 }}>
            <span>By {task.creator?.username}</span>
            {task.assignee && <span>→ {task.assignee.username}</span>}
            <span>{new Date(task.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
