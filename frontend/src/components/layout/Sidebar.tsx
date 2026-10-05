import { NavLink, useLocation } from 'react-router-dom'
import { useAppStore } from '../../stores/useAppStore'
import {
  LayoutDashboard,
  FileText,
  Workflow,
  Bot,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  FolderOpen,
  MessageSquare,
  Bell,
  History,
} from 'lucide-react'
import { cn } from '../../utils/helpers'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Executions', href: '/executions', icon: History },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Workflows', href: '/workflows', icon: Workflow },
  { name: 'Agents', href: '/agents', icon: Bot },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const { sidebarOpen, toggleSidebar, darkMode } = useAppStore()
  const location = useLocation()

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen transition-all duration-300 bg-white dark:bg-dark-900 border-r border-dark-200 dark:border-dark-700',
        sidebarOpen ? 'w-64' : 'w-20'
      )}
    >
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className={cn('flex h-16 items-center justify-between px-4 border-b border-dark-200 dark:border-dark-700', !sidebarOpen && 'justify-center')}>
          <NavLink to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            {sidebarOpen && (
              <span className="text-xl font-bold text-dark-900 dark:text-white">
                Agenttic
              </span>
            )}
          </NavLink>
          <button
            onClick={toggleSidebar}
            className={cn(
              'p-1.5 rounded-lg text-dark-500 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800 transition-colors',
              !sidebarOpen && 'ml-auto'
            )}
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1" role="navigation" aria-label="Main navigation">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href || (item.href !== '/' && location.pathname.startsWith(item.href))
            const Icon = item.icon

            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400'
                    : 'text-dark-600 hover:bg-dark-100 hover:text-dark-900 dark:text-dark-400 dark:hover:bg-dark-800 dark:hover:text-white',
                  !sidebarOpen && 'justify-center'
                )}
                title={sidebarOpen ? undefined : item.name}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                {sidebarOpen && <span>{item.name}</span>}
              </NavLink>
            )
          })}
        </nav>

        {/* Bottom section */}
        <div className={cn('p-3 border-t border-dark-200 dark:border-dark-700', !sidebarOpen && 'hidden')}>
          <div className="space-y-2">
            <button
              className={cn(
                'w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-dark-600 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800 transition-colors'
              )}
            >
              <FolderOpen className="w-5 h-5" />
              <span>Projects</span>
            </button>
            <button
              className={cn(
                'w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-dark-600 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800 transition-colors'
              )}
            >
              <Bell className="w-5 h-5" />
              <span>Notifications</span>
            </button>
          </div>

          <div className="mt-4 pt-4 border-t border-dark-200 dark:border-dark-700">
            <button
              onClick={() => useAppStore.getState().toggleDarkMode()}
              className="w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-dark-600 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800 transition-colors"
            >
              {darkMode ? (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  <span>Light Mode</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                  <span>Dark Mode</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </aside>
  )
}