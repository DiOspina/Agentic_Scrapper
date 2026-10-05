import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { formatRelativeTime } from '../utils/helpers'
import { Card, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Textarea } from '../components/ui/Textarea'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { Send, Plus, Trash2, Copy, Check, Loader2, Bot, User, Sparkles, FileText, Globe, X } from 'lucide-react'
import { cn } from '../utils/helpers'
import { useAppStore } from '../stores/useAppStore'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'
import { remarkGfm } from 'remark-gfm'

export function Chat() {
  const queryClient = useQueryClient()
  const { chatSessions, activeChatSessionId, setActiveChatSessionId, addChatSession, updateChatSession, removeChatSession, setChatSessions } = useAppStore()
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string; metadata?: any; timestamp: string }>>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showNewSession, setShowNewSession] = useState(false)
  const [newSessionTitle, setNewSessionTitle] = useState('')
  const [useRag, setUseRag] = useState(true)
  const [showSettings, setShowSettings] = useState(false)
  const [temperature, setTemperature] = useState(0.1)
  const [maxTokens, setMaxTokens] = useState(4000)
  const [topK, setTopK] = useState(5)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Load sessions
  const { data: sessionsData } = useQuery({
    queryKey: ['chat', 'sessions'],
    queryFn: () => api.listChatSessions(),
  })

  useEffect(() => {
    if (sessionsData) {
      setChatSessions(sessionsData)
      if (!activeChatSessionId && sessionsData.length > 0) {
        setActiveChatSessionId(sessionsData[0].session_id)
      }
    }
  }, [sessionsData])

  // Load messages when session changes
  useEffect(() => {
    if (activeChatSessionId) {
      const session = chatSessions.find(s => s.session_id === activeChatSessionId)
      if (session) {
        setMessages(session.messages || [])
      }
    } else {
      setMessages([])
    }
  }, [activeChatSessionId, chatSessions])

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      if (!activeChatSessionId) {
        const newSession = await api.createChatSession({ title: message.slice(0, 50) })
        setActiveChatSessionId(newSession.session_id)
        return api.sendChatMessage(newSession.session_id, { message, use_rag: useRag, temperature, max_tokens: maxTokens, top_k: topK })
      }
      return api.sendChatMessage(activeChatSessionId, { message, use_rag: useRag, temperature, max_tokens: maxTokens, top_k: topK })
    },
    onSuccess: (response) => {
      setMessages(prev => [...prev, { role: 'assistant', content: response.message, metadata: { sources: response.sources }, timestamp: new Date().toISOString() }])
      if (activeChatSessionId) {
        const session = chatSessions.find(s => s.session_id === activeChatSessionId)
        if (session) {
          updateChatSession(activeChatSessionId, {
            messages: [...session.messages, { role: 'user', content: inputValue, timestamp: new Date().toISOString() }, { role: 'assistant', content: response.message, metadata: { sources: response.sources }, timestamp: new Date().toISOString() }],
          })
        }
      }
      setInputValue('')
      setIsLoading(false)
    },
    onError: () => {
      setIsLoading(false)
      toast.error('Failed to send message')
    },
  })

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || isLoading) return

    const userMessage = { role: 'user' as const, content: inputValue, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    sendMessageMutation.mutate(inputValue)
  }

  const handleNewSession = () => {
    const title = newSessionTitle || 'New Chat'
    api.createChatSession({ title }).then(session => {
      addChatSession(session)
      setActiveChatSessionId(session.session_id)
      setShowNewSession(false)
      setNewSessionTitle('')
    }).catch(() => toast.error('Failed to create session'))
  }

  const handleDeleteSession = (sessionId: string) => {
    api.deleteChatSession(sessionId).then(() => {
      removeChatSession(sessionId)
      toast.success('Session deleted')
    }).catch(() => toast.error('Failed to delete session'))
  }

  const handleClearMessages = () => {
    if (activeChatSessionId) {
      updateChatSession(activeChatSessionId, { messages: [] })
      setMessages([])
    }
  }

  return (
    <div className="h-[calc(100vh-200px)] flex flex-col animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Chat</h1>
          <p className="text-dark-500 dark:text-dark-400 mt-1">Conversational AI with RAG-powered document search</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowNewSession(true)} leftIcon={<Plus className="w-4 h-4" />}>
            New Chat
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowSettings(!showSettings)} leftIcon={<Sparkles className="w-4 h-4" />}>
            Settings
          </Button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Sessions */}
        <aside className="w-72 flex-shrink-0 border-r border-dark-200 dark:border-dark-700 bg-white dark:bg-dark-900 flex flex-col">
          <div className="p-4 border-b border-dark-200 dark:border-dark-700">
            <h3 className="font-semibold text-dark-900 dark:text-white">Conversations</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {chatSessions.length === 0 ? (
              <div className="text-center py-8 text-dark-500 dark:text-dark-400">
                <p className="mb-2">No conversations yet</p>
                <Button variant="ghost" size="sm" onClick={() => setShowNewSession(true)}>
                  Start a new chat
                </Button>
              </div>
            ) : (
              chatSessions.map((session) => (
                <button
                  key={session.session_id}
                  onClick={() => setActiveChatSessionId(session.session_id)}
                  className={cn(
                    'w-full text-left p-3 rounded-lg transition-colors',
                    activeChatSessionId === session.session_id
                      ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                      : 'text-dark-600 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium truncate">{session.title || 'Untitled'}</span>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteSession(session.session_id) }}
                      className="p-1 text-dark-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="text-xs text-dark-500 dark:text-dark-400 mt-1 truncate">
                    {session.messages[session.messages.length - 1]?.content?.slice(0, 50) || 'No messages'}
                  </div>
                  <div className="text-xs text-dark-400 mt-1">
                    {formatRelativeTime(session.updated_at)}
                  </div>
                </button>
              ))
            )}
          </div>
        </aside>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Chat Header */}
          <div className="p-4 border-b border-dark-200 dark:border-dark-700 bg-white dark:bg-dark-900">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                <Bot className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <h3 className="font-semibold text-dark-900 dark:text-white">
                  {chatSessions.find(s => s.session_id === activeChatSessionId)?.title || 'Select a conversation'}
                </h3>
                <p className="text-sm text-dark-500 dark:text-dark-400">
                  {activeChatSessionId ? `${chatSessions.find(s => s.session_id === activeChatSessionId)?.messages.length || 0} messages` : 'Start a new chat'}
                </p>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6" ref={messagesEndRef}>
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Bot className="w-16 h-16 text-dark-300 dark:text-dark-600 mb-4" />
                <h3 className="text-lg font-medium text-dark-900 dark:text-white mb-2">
                  {activeChatSessionId ? 'Start the conversation' : 'Select or create a conversation'}
                </p>
                <p className="text-dark-500 dark:text-dark-400 max-w-md">
                  {activeChatSessionId
                    ? 'Ask a question about your documents or request analysis.'
                    : 'Create a new chat session from the sidebar to begin.'}
                </p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div key={index} className={cn('flex gap-3', message.role === 'user' && 'flex-row-reverse')}>
                  <div
                    className={cn(
                      'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                      message.role === 'user'
                        ? 'bg-dark-100 dark:bg-dark-800'
                        : 'bg-primary-100 dark:bg-primary-900/30'
                    )}
                  >
                    {message.role === 'user' ? (
                      <User className="w-5 h-5 text-dark-600 dark:text-dark-400" />
                    ) : (
                      <Bot className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                    )}
                  </div>
                  <div className={cn('flex-1 max-w-[80%]', message.role === 'user' && 'text-right')}>
                    <div
                      className={cn(
                        'px-4 py-2 rounded-2xl',
                        message.role === 'user'
                          ? 'bg-primary-600 text-white rounded-tr-none'
                          : 'bg-dark-100 dark:bg-dark-800 text-dark-900 dark:text-white rounded-tl-none'
                      )}
                    >
                      <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-sm dark:prose-invert max-w-none">
                        {message.content}
                      </ReactMarkdown>
                    </div>
                    {message.metadata?.sources && message.metadata.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-dark-200 dark:border-dark-700">
                        <p className="text-xs font-medium text-dark-500 dark:text-dark-400 mb-1">Sources ({message.metadata.sources.length})</p>
                        <div className="space-y-1">
                          {message.metadata.sources.slice(0, 3).map((source: any, i: number) => (
                            <div key={i} className="text-xs text-dark-500 dark:text-dark-400 bg-dark-50 dark:bg-dark-900/50 p-2 rounded">
                              <span className="font-mono">{source.metadata?.document_id || source.metadata?.filename || 'Unknown'}</span>
                              {source.score && <span className="ml-2 text-primary-600 dark:text-primary-400">({(source.score * 100).toFixed(0)}%)</span>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-dark-400">{formatRelativeTime(message.timestamp)}</span>
                      <button
                        onClick={() => navigator.clipboard.writeText(message.content)}
                        className="p-1 text-dark-400 hover:text-dark-600 dark:hover:text-dark-300 transition-colors"
                        title="Copy"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
                <div className="bg-dark-100 dark:bg-dark-800 rounded-2xl rounded-tl-none px-4 py-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-dark-200 dark:border-dark-700 bg-white dark:bg-dark-900">
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask a question..."
                  rows={1}
                  className="w-full px-4 py-3 pr-12 bg-dark-100 dark:bg-dark-800 border border-dark-200 dark:border-dark-700 rounded-xl text-dark-900 dark:text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 resize-none min-h-[48px] max-h-48"
                  disabled={isLoading}
                />
                <div className="absolute right-3 bottom-3 flex items-center gap-1">
                  <label className="flex items-center gap-1 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useRag}
                      onChange={(e) => setUseRag(e.target.checked)}
                      className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-xs text-dark-500 dark:text-dark-400">RAG</span>
                  </label>
                </div>
              </div>
              <Button
                type="submit"
                loading={isLoading}
                disabled={!inputValue.trim() || isLoading}
                className="h-12"
              >
                <Send className="w-5 h-5" />
              </Button>
            </form>
            <div className="flex items-center gap-4 mt-2 text-xs text-dark-500 dark:text-dark-400">
              <span>Shift+Enter for new line</span>
              <span>•</span>
              <span>Enter to send</span>
            </div>
          </div>
        </div>
      </div>

      {/* New Session Modal */}
      <Modal
        isOpen={showNewSession}
        onClose={() => setShowNewSession(false)}
        title="New Conversation"
        size="sm"
      >
        <div className="space-y-4">
          <Input
            label="Title (optional)"
            value={newSessionTitle}
            onChange={(e) => setNewSessionTitle(e.target.value)}
            placeholder="Leave empty for auto-generated title"
          />
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="secondary" onClick={() => setShowNewSession(false)}>Cancel</Button>
            <Button onClick={handleNewSession}>Create</Button>
          </div>
        </div>
      </Modal>

      {/* Settings Modal */}
      <Modal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        title="Chat Settings"
        size="md"
      >
        <div className="space-y-6">
          <div>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={useRag}
                onChange={(e) => setUseRag(e.target.checked)}
                className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
              />
              <div>
                <p className="font-medium text-dark-900 dark:text-white">Enable RAG (Retrieval-Augmented Generation)</p>
                <p className="text-sm text-dark-500 dark:text-dark-400">Search documents for relevant context</p>
              </div>
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-1">Temperature: {temperature}</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full h-2 bg-dark-200 dark:bg-dark-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
              <p className="text-xs text-dark-500 dark:text-dark-400 mt-1">Controls randomness (0 = focused, 1 = creative)</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-1">Max Tokens: {maxTokens}</label>
              <input
                type="range"
                min="500"
                max="8000"
                step="500"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full h-2 bg-dark-200 dark:bg-dark-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
              <p className="text-xs text-dark-500 dark:text-dark-400 mt-1">Maximum response length</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-700 dark:text-dark-300 mb-1">Top K Results: {topK}</label>
            <input
              type="range"
              min="1"
              max="20"
              step="1"
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value))}
              className="w-full h-2 bg-dark-200 dark:bg-dark-700 rounded-lg appearance-none cursor-pointer accent-primary-600"
            />
            <p className="text-xs text-dark-500 dark:text-dark-400 mt-1">Number of document chunks to retrieve</p>
          </div>

          <Button variant="secondary" onClick={handleClearMessages} className="w-full" leftIcon={<Trash2 className="w-4 h-4" />}>
            Clear Current Conversation
          </Button>
        </div>
      </Modal>
    </div>
  )
}