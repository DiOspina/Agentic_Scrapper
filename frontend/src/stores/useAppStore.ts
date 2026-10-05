import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Execution, Document, Workflow, ChatSession, ChatMessage } from '../types'

interface AppState {
  // Theme
  darkMode: boolean
  toggleDarkMode: () => void
  setDarkMode: (enabled: boolean) => void

  // Sidebar
  sidebarOpen: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void

  // Selected items
  selectedExecutionId: string | null
  setSelectedExecutionId: (id: string | null) => void

  selectedDocumentId: string | null
  setSelectedDocumentId: (id: string | null) => void

  selectedWorkflowId: string | null
  setSelectedWorkflowId: (id: string | null) => void

  // Chat
  activeChatSessionId: string | null
  setActiveChatSessionId: (id: string | null) => void
  chatSessions: ChatSession[]
  setChatSessions: (sessions: ChatSession[]) => void
  addChatSession: (session: ChatSession) => void
  updateChatSession: (id: string, updates: Partial<ChatSession>) => void
  removeChatSession: (id: string) => void

  // Real-time logs
  liveLogs: Record<string, any[]>
  addLiveLog: (executionId: string, log: any) => void
  clearLiveLogs: (executionId: string) => void

  // Notifications
  notifications: Array<{ id: string; message: string; type: 'success' | 'error' | 'info' | 'warning' }>
  addNotification: (notification: Omit<AppState['notifications'][0], 'id'>) => void
  removeNotification: (id: string) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Theme
      darkMode: false,
      toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
      setDarkMode: (enabled) => set({ darkMode: enabled }),

      // Sidebar
      sidebarOpen: true,
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      // Selected items
      selectedExecutionId: null,
      setSelectedExecutionId: (id) => set({ selectedExecutionId: id }),

      selectedDocumentId: null,
      setSelectedDocumentId: (id) => set({ selectedDocumentId: id }),

      selectedWorkflowId: null,
      setSelectedWorkflowId: (id) => set({ selectedWorkflowId: id }),

      // Chat
      activeChatSessionId: null,
      setActiveChatSessionId: (id) => set({ activeChatSessionId: id }),
      chatSessions: [],
      setChatSessions: (sessions) => set({ chatSessions: sessions }),
      addChatSession: (session) => set((state) => ({ chatSessions: [session, ...state.chatSessions] })),
      updateChatSession: (id, updates) =>
        set((state) => ({
          chatSessions: state.chatSessions.map((s) => (s.session_id === id ? { ...s, ...updates } : s)),
        })),
      removeChatSession: (id) =>
        set((state) => ({
          chatSessions: state.chatSessions.filter((s) => s.session_id !== id),
          activeChatSessionId: state.activeChatSessionId === id ? null : state.activeChatSessionId,
        })),

      // Live logs
      liveLogs: {},
      addLiveLog: (executionId, log) =>
        set((state) => ({
          liveLogs: {
            ...state.liveLogs,
            [executionId]: [...(state.liveLogs[executionId] || []), log],
          },
        })),
      clearLiveLogs: (executionId) =>
        set((state) => {
          const newLogs = { ...state.liveLogs }
          delete newLogs[executionId]
          return { liveLogs: newLogs }
        }),

      // Notifications
      notifications: [],
      addNotification: (notification) =>
        set((state) => ({
          notifications: [...state.notifications, { ...notification, id: Math.random().toString(36).substr(2, 9) }],
        })),
      removeNotification: (id) =>
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        })),
    }),
    {
      name: 'agenttic-app-storage',
      partialize: (state) => ({
        darkMode: state.darkMode,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
)