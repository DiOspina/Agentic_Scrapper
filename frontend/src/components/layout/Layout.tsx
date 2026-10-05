import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { useAppStore } from '../../stores/useAppStore'
import { cn } from '../../utils/helpers'

export function Layout() {
  const { sidebarOpen, darkMode } = useAppStore()

  return (
    <div className={cn('min-h-screen transition-colors duration-300', darkMode ? 'dark' : '')}>
      <Sidebar />
      <div className={cn('transition-all duration-300', sidebarOpen ? 'lg:pl-64' : 'lg:pl-20')}>
        <Header />
        <main className="pt-16 min-h-screen pb-8">
          <div className="p-4 sm:p-6 lg:p-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}