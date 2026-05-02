import { create } from 'zustand'

export interface User {
  id: number; email: string; username: string
  full_name?: string; avatar_color?: string; is_active: boolean
}

export interface Task {
  id: number; title: string; description?: string
  priority: string; position: number; is_completed: boolean
  due_date?: string; board_id: number; column_id: number
  assignee?: User; creator: User
  created_at: string; updated_at?: string
}

export interface Column {
  id: number; name: string; position: number
  color: string; board_id: number
  tasks: Task[]
}

export interface BoardMember { id: number; user: User; role: string; joined_at: string }

export interface Board {
  id: number; name: string; description?: string
  color: string; is_archived: boolean
  owner_id: number; members: BoardMember[]; columns: Column[]
  created_at: string; updated_at?: string
}

interface Store {
  user: User | null
  setUser: (u: User | null) => void
  isAuthenticated: boolean

  boards: Board[]
  setBoards: (b: Board[]) => void

  currentBoard: Board | null
  setCurrentBoard: (b: Board | null) => void

  addTask: (colId: number, task: Task) => void
  updateTask: (id: number, changes: Partial<Task>) => void
  deleteTask: (id: number, colId: number) => void

  selectedTask: Task | null
  setSelectedTask: (t: Task | null) => void
}

export const useStore = create<Store>((set) => ({
  user: null,
  isAuthenticated: false,
  setUser: (u) => set({ user: u, isAuthenticated: !!u }),

  boards: [],
  setBoards: (b) => set({ boards: b }),

  currentBoard: null,
  setCurrentBoard: (b) => set({ currentBoard: b }),

  addTask: (colId, task) => set(s => {
    if (!s.currentBoard) return s
    return {
      currentBoard: {
        ...s.currentBoard,
        columns: s.currentBoard.columns.map(c =>
          c.id === colId ? { ...c, tasks: [...c.tasks, task] } : c
        )
      }
    }
  }),

  updateTask: (id, changes) => set(s => {
    if (!s.currentBoard) return s
    return {
      currentBoard: {
        ...s.currentBoard,
        columns: s.currentBoard.columns.map(c => ({
          ...c, tasks: c.tasks.map(t => t.id === id ? { ...t, ...changes } : t)
        }))
      },
      selectedTask: s.selectedTask?.id === id ? { ...s.selectedTask, ...changes } : s.selectedTask
    }
  }),

  deleteTask: (id, colId) => set(s => {
    if (!s.currentBoard) return s
    return {
      currentBoard: {
        ...s.currentBoard,
        columns: s.currentBoard.columns.map(c =>
          c.id === colId ? { ...c, tasks: c.tasks.filter(t => t.id !== id) } : c
        )
      },
      selectedTask: s.selectedTask?.id === id ? null : s.selectedTask
    }
  }),

  selectedTask: null,
  setSelectedTask: (t) => set({ selectedTask: t }),
}))
