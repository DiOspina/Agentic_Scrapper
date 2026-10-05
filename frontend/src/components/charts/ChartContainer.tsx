import { cn } from '../../utils/helpers'
import { ResponsiveContainer } from 'recharts'

interface ChartContainerProps {
  children: React.ReactNode
  height?: number
  width?: string | number
  className?: string
  title?: string
  subtitle?: string
  action?: React.ReactNode
}

export function ChartContainer({
  children,
  height = 300,
  width = '100%',
  className,
  title,
  subtitle,
  action,
}: ChartContainerProps) {
  return (
    <div className={cn('bg-white dark:bg-dark-900 rounded-xl border border-dark-200 dark:border-dark-700 p-6', className)}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4">
          <div>
            {title && <h3 className="text-lg font-semibold text-dark-900 dark:text-white">{title}</h3>}
            {subtitle && <p className="text-sm text-dark-500 dark:text-dark-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div style={{ width, height }}>
        <ResponsiveContainer width={width} height={height}>
          {children}
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export function ChartGrid({ children, className, columns = 2 }: { children: React.ReactNode; className?: string; columns?: number }) {
  return (
    <div className={cn(`grid gap-6`, `grid-cols-1 md:grid-cols-${columns}`, className)}>
      {children}
    </div>
  )
}

export function StatCard({
  title,
  value,
  change,
  changeLabel,
  icon,
  iconColor = 'primary',
  trend: trendProp = 'neutral',
  className,
}: {
  title: string
  value: string | number
  change?: number
  changeLabel?: string
  icon?: React.ReactNode
  iconColor?: 'primary' | 'success' | 'warning' | 'error' | 'info'
  trend?: 'up' | 'down' | 'neutral'
  className?: string
}) {
  const iconColors = {
    primary: 'bg-primary-100 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400',
    success: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
    warning: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400',
    error: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
    info: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
  }

  const trendColors = {
    up: 'text-green-600 dark:text-green-400',
    down: 'text-red-600 dark:text-red-400',
    neutral: 'text-dark-500 dark:text-dark-400',
  }

  const trendIcons = {
    up: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>,
    down: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>,
    neutral: <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" /></svg>,
  }

  return (
    <div className={cn('bg-white dark:bg-dark-900 rounded-xl border border-dark-200 dark:border-dark-700 p-6', className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-dark-500 dark:text-dark-400">{title}</p>
          <p className="mt-1 text-2xl font-bold text-dark-900 dark:text-white">{value}</p>
        </div>
        {icon && (
          <div className={cn('p-3 rounded-xl', iconColors[iconColor])}>
            {icon}
          </div>
        )}
      </div>
      {(change !== undefined || changeLabel) && (
        <div className="mt-4 flex items-center gap-2">
          <span className={cn('text-sm font-medium', trendColors[trendProp])}>
            {trendIcons[trendProp]}
            {change !== undefined ? `${change >= 0 ? '+' : ''}${change}%` : ''}
          </span>
          {changeLabel && <span className="text-sm text-dark-500 dark:text-dark-400">{changeLabel}</span>}
        </div>
      )}
    </div>
  )
}