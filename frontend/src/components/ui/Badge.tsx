import { cn } from '../../utils/helpers'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral'
  size?: 'sm' | 'md' | 'lg'
  className?: string
  dot?: boolean
}

export function Badge({ children, variant = 'neutral', size = 'md', className, dot }: BadgeProps) {
  const variants = {
    success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    neutral: 'bg-dark-100 text-dark-800 dark:bg-dark-700 dark:text-dark-300',
  }

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-xs',
    lg: 'px-3 py-1 text-sm',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-medium',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full', variants[variant].replace('bg-', 'bg-').replace('text-', 'bg-'))} />}
      {children}
    </span>
  )
}

export function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, BadgeProps['variant']> = {
    pending: 'neutral',
    running: 'info',
    completed: 'success',
    failed: 'error',
    cancelled: 'warning',
    uploaded: 'neutral',
    processing: 'info',
    processed: 'success',
    deleted: 'neutral',
    draft: 'neutral',
    active: 'success',
    paused: 'warning',
    archived: 'neutral',
    sent: 'success',
    delivered: 'success',
    read: 'info',
  }

  return (
    <Badge variant={variants[status] || 'neutral'} dot>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  )
}