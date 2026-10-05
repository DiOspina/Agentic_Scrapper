import { useAppStore } from '../../stores/useAppStore'
import { Menu, Sun, Moon, Bell, User, LogOut, ChevronDown } from 'lucide-react'
import { cn } from '../../utils/helpers'
import { useState, useRef, useEffect } from 'react'

export function Header() {
  const { sidebarOpen, toggleSidebar, darkMode, toggleDarkMode, notifications, removeNotification } = useAppStore()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const notificationsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
      if (notificationsRef.current && !notificationsRef.current.contains(event.target as Node)) {
        setShowNotifications(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <header
      className={cn(
        'fixed top-0 z-30 h-16 bg-white/80 dark:bg-dark-900/80 backdrop-blur-md border-b border-dark-200 dark:border-dark-700 transition-all duration-300',
        sidebarOpen ? 'left-64' : 'left-20'
      )}
    >
      <div className="flex h-full items-center justify-between px-4 sm:px-6">
        {/* Left side - Mobile menu toggle */}
        <div className="flex items-center gap-4 lg:hidden">
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg text-dark-500 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800"
            aria-label="Toggle menu"
          >
            <Menu className="w-6 h-6" />
          </button>
        </div>

        {/* Search */}
        <div className="hidden md:block flex-1 max-w-md mx-4 lg:mx-8">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search executions, documents, workflows..."
              className="w-full pl-10 pr-4 py-2 text-sm bg-dark-100 dark:bg-dark-800 border border-dark-200 dark:border-dark-700 rounded-lg text-dark-900 dark:text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Right side - Actions */}
        <div className="flex items-center gap-2">
          {/* Theme toggle */}
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-lg text-dark-500 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800 transition-colors"
            aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>

          {/* Notifications */}
          <div className="relative" ref={notificationsRef}>
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 rounded-lg text-dark-500 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800 transition-colors"
              aria-label="Notifications"
              aria-expanded={showNotifications}
            >
              <Bell className="w-5 h-5" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-xs font-medium flex items-center justify-center">
                  {notifications.length > 9 ? '9+' : notifications.length}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white dark:bg-dark-900 rounded-xl shadow-lg border border-dark-200 dark:border-dark-700 py-2 z-50 animate-slide-down">
                <div className="px-4 py-3 border-b border-dark-200 dark:border-dark-700 flex items-center justify-between">
                  <h3 className="font-semibold text-dark-900 dark:text-white">Notifications</h3>
                  {notifications.length > 0 && (
                    <button
                      onClick={() => {
                        notifications.forEach(n => removeNotification(n.id))
                        setShowNotifications(false)
                      }}
                      className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
                    >
                      Clear all
                    </button>
                  )}
                </div>
                {notifications.length === 0 ? (
                  <div className="px-4 py-8 text-center text-dark-500 dark:text-dark-400">
                    No notifications
                  </div>
                ) : (
                  <div className="max-h-96 overflow-y-auto">
                    {notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className="px-4 py-3 hover:bg-dark-50 dark:hover:bg-dark-800 border-b border-dark-100 dark:border-dark-800 last:border-0 flex items-start gap-3"
                      >
                        <div
                          className={cn(
                            'w-2 h-2 rounded-full mt-2 flex-shrink-0',
                            notification.type === 'success' && 'bg-green-500',
                            notification.type === 'error' && 'bg-red-500',
                            notification.type === 'warning' && 'bg-yellow-500',
                            notification.type === 'info' && 'bg-blue-500'
                          )}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-dark-900 dark:text-white truncate">{notification.message}</p>
                        </div>
                        <button
                          onClick={() => removeNotification(notification.id)}
                          className="p-1 text-dark-400 hover:text-dark-600 dark:hover:text-dark-300"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* User menu */}
          <div className="relative ml-2" ref={userMenuRef}>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-dark-100 dark:hover:bg-dark-800 transition-colors"
              aria-expanded={showUserMenu}
              aria-label="User menu"
            >
              <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                <User className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              </div>
              <span className="hidden sm:block text-sm font-medium text-dark-700 dark:text-dark-300">Admin</span>
              <ChevronDown className="w-4 h-4 text-dark-400 hidden sm:block" />
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-dark-900 rounded-xl shadow-lg border border-dark-200 dark:border-dark-700 py-2 z-50 animate-slide-down">
                <div className="px-4 py-3 border-b border-dark-200 dark:border-dark-700">
                  <p className="font-medium text-dark-900 dark:text-white">Admin User</p>
                  <p className="text-sm text-dark-500 dark:text-dark-400">admin@agenttic.ai</p>
                </div>
                <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-dark-700 dark:text-dark-300 hover:bg-dark-100 dark:hover:bg-dark-800">
                  <User className="w-5 h-5" />
                  Profile
                </button>
                <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-dark-700 dark:text-dark-300 hover:bg-dark-100 dark:hover:bg-dark-800">
                  <Settings className="w-5 h-5" />
                  Settings
                </button>
                <hr className="my-2 border-dark-200 dark:border-dark-700" />
                <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20">
                  <LogOut className="w-5 h-5" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}