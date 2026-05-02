import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { boardsApi, tasksApi } from '../../services/api'
import { useStore, Task, Column } from '../../store/useStore'
import { useWebSocket } from '../../hooks/useWebSocket'
import TaskModal from './TaskModal'

const P_COLOR: Record<string, string> = { low: '#4ade80', medium: '#60a5fa', high: '#fbbf24', urgent: '#f87171' }

async function fetchBoardWithTasks(boardId: number) {
  const [boardRes, tasksRes] = await Promise.all([
    boardsApi.get(boardId),
    tasksApi.list(boardId),
  ])
  const board = boardRes.data
  const tasks: Task[] = tasksRes.data
  board.columns = board.columns.map((col: Column) => ({
    ...col,
    tasks: tasks.filter(t => t.column_id === col.id),
  }))
  return board
}

export default function BoardPage() {
  const { boardId } = useParams<{ boardId: string }>()
  const navigate = useNavigate()
  const { currentBoard, setCurrentBoard, addTask, updateTask, deleteTask, selectedTask, setSelectedTask, setUser } = useStore()
  const [loading, setLoading] = useState(true)
  const [addingCol, setAddingCol] = useState<number | null>(null)
  const [newTitle, setNewTitle] = useState('')

  const reload = useCallback(async () => {
    if (!boardId) return
    try {
      const board = await fetchBoardWithTasks(Number(boardId))
      setCurrentBoard(board)
    } catch {}
  }, [boardId, setCurrentBoard])

  const onWsEvent = useCallback((e: any) => {
    const refreshTypes = ['task_created', 'task_updated', 'task_deleted', 'board_updated']
    if (refreshTypes.includes(e.type)) reload()
  }, [reload])

  const { connected } = useWebSocket(Number(boardId), onWsEvent)

  useEffect(() => {
    if (!boardId) return
    fetchBoardWithTasks(Number(boardId))
      .then(board => { setCurrentBoard(board); setLoading(false) })
      .catch(() => navigate('/'))
    return () => setCurrentBoard(null)
  }, [boardId, setCurrentBoard, navigate])

  const addTask_ = async (colId: number) => {
    if (!newTitle.trim() || !boardId) return
    try {
      const { data } = await tasksApi.create(Number(boardId), { title: newTitle.trim(), column_id: colId })
      addTask(colId, data)
      setNewTitle(''); setAddingCol(null)
    } catch {}
  }

  const moveTask = async (task: Task, toColId: number) => {
    try {
      await tasksApi.move(task.id, { column_id: toColId, position: 0 })
      reload()
    } catch {}
  }

  const logout = () => { localStorage.clear(); setUser(null); navigate('/login') }

  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-0)' }}>
      <span className="spinner" style={{ width: 36, height: 36 }} />
    </div>
  )
  if (!currentBoard) return null

  const cols = [...currentBoard.columns].sort((a, b) => a.position - b.position)

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-0)', display: 'flex', flexDirection: 'column' }}>
      <header style={{ background: 'var(--bg-1)', borderBottom: '1px solid var(--border)', height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 1.25rem', flexShrink: 0, position: 'sticky', top: 0, zIndex: 50 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/')}>← Back</button>
          <div style={{ width: 1, height: 18, background: 'var(--border)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 10, height: 10, borderRadius: 3, background: currentBoard.color }} />
            <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 15 }}>{currentBoard.name}</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: connected ? 'var(--green)' : 'var(--red)', boxShadow: connected ? '0 0 5px var(--green)' : 'none' }} />
            <span style={{ fontSize: 12, color: 'var(--text-2)' }}>{connected ? 'Live' : 'Reconnecting...'}</span>
          </div>
          <div style={{ display: 'flex', gap: 3 }}>
            {currentBoard.members.slice(0, 5).map(m => (
              <div key={m.id} title={m.user.username}
                style={{ width: 26, height: 26, borderRadius: '50%', background: `hsl(${(m.user.id * 47) % 360},55%,38%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: 'white', border: '2px solid var(--bg-1)' }}>
                {(m.user.full_name || m.user.username)[0].toUpperCase()}
              </div>
            ))}
          </div>
          <button className="btn btn-ghost btn-sm" onClick={logout}>Sign out</button>
        </div>
      </header>

      <div style={{ flex: 1, display: 'flex', gap: '1.1rem', padding: '1.25rem', overflowX: 'auto', alignItems: 'flex-start' }}>
        {cols.map(col => (
          <div key={col.id} style={{ width: 288, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 2px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                <div style={{ width: 7, height: 7, borderRadius: '50%', background: col.color || 'var(--text-3)' }} />
                <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 13 }}>{col.name}</span>
                <span className="badge" style={{ background: 'var(--bg-3)', color: 'var(--text-3)', fontSize: 11 }}>{col.tasks.length}</span>
              </div>
              <button onClick={() => { setAddingCol(col.id); setNewTitle('') }}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-3)', cursor: 'pointer', fontSize: 18, lineHeight: 1, padding: '0 2px', borderRadius: 4 }}
                title="Add task">+</button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 7, minHeight: 60 }}>
              {[...col.tasks].sort((a, b) => a.position - b.position).map(task => (
                <TaskCard key={task.id} task={task} cols={cols} onClick={() => setSelectedTask(task)} onMove={moveTask} />
              ))}
            </div>

            {addingCol === col.id ? (
              <div style={{ background: 'var(--bg-2)', border: '1px solid var(--accent)', borderRadius: 9, padding: '10px' }}>
                <input className="input" autoFocus placeholder="Task title..." value={newTitle}
                  onChange={e => setNewTitle(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') addTask_(col.id); if (e.key === 'Escape') setAddingCol(null) }}
                  style={{ marginBottom: 7 }} />
                <div style={{ display: 'flex', gap: 6 }}>
                  <button className="btn btn-primary btn-sm" onClick={() => addTask_(col.id)}>Add</button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setAddingCol(null)}>Cancel</button>
                </div>
              </div>
            ) : (
              <button onClick={() => { setAddingCol(col.id); setNewTitle('') }}
                style={{ background: 'transparent', border: '1px dashed var(--border)', borderRadius: 9, padding: '7px 10px', color: 'var(--text-3)', cursor: 'pointer', fontSize: 13, textAlign: 'left', transition: 'all 0.13s' }}
                onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.color = 'var(--accent)' }}
                onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-3)' }}>
                + Add task
              </button>
            )}
          </div>
        ))}
      </div>

      {selectedTask && (
        <TaskModal task={selectedTask} columns={cols} onClose={() => setSelectedTask(null)}
          onUpdate={(id, c) => { updateTask(id, c); setSelectedTask(selectedTask ? { ...selectedTask, ...c } : null) }}
          onDelete={(id) => { deleteTask(id, selectedTask.column_id); setSelectedTask(null) }}
        />
      )}
    </div>
  )
}

function TaskCard({ task, cols, onClick, onMove }: { task: Task; cols: Column[]; onClick: () => void; onMove: (t: Task, colId: number) => void }) {
  const pc = P_COLOR[task.priority] || 'var(--text-3)'
  return (
    <div onClick={onClick}
      style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 9, padding: '10px 11px', cursor: 'pointer', position: 'relative', transition: 'all 0.13s' }}
      onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--border-hi)'; e.currentTarget.style.transform = 'translateY(-1px)' }}
      onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.transform = 'none' }}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, borderRadius: '9px 9px 0 0', background: pc, opacity: 0.6 }} />
      <p style={{ fontSize: 13, fontWeight: 500, lineHeight: 1.4, marginBottom: 7, paddingTop: 2 }}>{task.title}</p>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
          <span className="badge" style={{ background: `${pc}15`, color: pc, fontSize: 10 }}>{task.priority}</span>
          {task.is_completed && <span className="badge" style={{ background: 'rgba(74,222,128,0.12)', color: '#4ade80', fontSize: 10 }}>done</span>}
        </div>
        {task.assignee && (
          <div title={task.assignee.username}
            style={{ width: 20, height: 20, borderRadius: '50%', background: `hsl(${(task.assignee.id * 47) % 360},55%,38%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, color: 'white' }}>
            {(task.assignee.full_name || task.assignee.username)[0].toUpperCase()}
          </div>
        )}
      </div>
      <div onClick={e => e.stopPropagation()} style={{ marginTop: 7, borderTop: '1px solid var(--border)', paddingTop: 6, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {cols.filter(c => c.id !== task.column_id).map(c => (
          <button key={c.id} onClick={() => onMove(task, c.id)}
            style={{ background: 'var(--bg-3)', border: '1px solid var(--border)', borderRadius: 4, color: 'var(--text-3)', fontSize: 10, padding: '2px 7px', cursor: 'pointer' }}>
            → {c.name.split(' ')[0]}
          </button>
        ))}
      </div>
    </div>
  )
}
