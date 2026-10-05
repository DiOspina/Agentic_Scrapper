import { cn } from '../../utils/helpers'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { useState } from 'react'

interface Column<T> {
  key: string
  header: string
  render?: (row: T, index: number) => React.ReactNode
  className?: string
  sortable?: boolean
  width?: string
}

interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyExtractor: (row: T) => string
  onRowClick?: (row: T) => void
  sortable?: boolean
  striped?: boolean
  hoverable?: boolean
  emptyMessage?: string
  loading?: boolean
  className?: string
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  sortable = false,
  striped = true,
  hoverable = true,
  emptyMessage = 'No data available',
  loading = false,
  className,
}: TableProps<T>) {
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null)

  const handleSort = (key: string) => {
    if (!sortable) return
    setSortConfig((current) => {
      if (current?.key === key && current.direction === 'asc') {
        return { key, direction: 'desc' }
      }
      return { key, direction: 'asc' }
    })
  }

  const sortedData = [...data].sort((a, b) => {
    if (!sortConfig) return 0
    const aVal = a[sortConfig.key as keyof T]
    const bVal = b[sortConfig.key as keyof T]
    if (aVal === bVal) return 0
    const direction = sortConfig.direction === 'asc' ? 1 : -1
    return aVal > bVal ? direction : -direction
  })

  if (loading) {
    return (
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key} className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[...Array(5)].map((_, i) => (
              <tr key={i}>
                {columns.map(() => (
                  <td key={column.key} className="px-4 py-3">
                    <div className="h-4 bg-dark-200 dark:bg-dark-700 rounded animate-pulse" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-dark-500 dark:text-dark-400">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="w-full text-sm">
        <thead className="bg-dark-50 dark:bg-dark-800/50">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  'px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider',
                  column.className,
                  column.sortable && sortable && 'cursor-pointer select-none hover:bg-dark-100 dark:hover:bg-dark-700'
                )}
                style={{ width: column.width }}
                onClick={() => column.sortable && sortable && handleSort(column.key)}
              >
                <div className="flex items-center gap-1">
                  {column.header}
                  {column.sortable && sortable && sortConfig?.key === column.key && (
                    sortConfig.direction === 'asc' ? (
                      <ChevronUp className="w-4 h-4 text-primary-600" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-primary-600" />
                    )
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-dark-200 dark:divide-dark-700">
          {sortedData.map((row, rowIndex) => (
            <tr
              key={keyExtractor(row)}
              className={cn(
                'transition-colors',
                striped && rowIndex % 2 === 0 && 'bg-dark-50/50 dark:bg-dark-900/50',
                hoverable && 'hover:bg-dark-100/50 dark:hover:bg-dark-800/50',
                onRowClick && 'cursor-pointer'
              )}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((column) => (
                <td key={column.key} className={cn('px-4 py-3', column.className)}>
                  {column.render ? column.render(row, rowIndex) : String(row[column.key as keyof T] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  showPageSize?: boolean
  pageSize?: number
  onPageSizeChange?: (size: number) => void
  totalItems?: number
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  showPageSize = false,
  pageSize,
  onPageSizeChange,
  totalItems,
}: PaginationProps) {
  if (totalPages <= 1) return null

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1)
  const visiblePages = pages.filter(
    (page) =>
      page === 1 ||
      page === totalPages ||
      (page >= currentPage - 1 && page <= currentPage + 1)
  )

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-4 py-3 border-t border-dark-200 dark:border-dark-700">
      <div className="flex items-center gap-2 text-sm text-dark-600 dark:text-dark-400">
        <span>
          Showing{' '}
          <strong>{(currentPage - 1) * (pageSize || 10) + 1}</strong>{' '}
          to{' '}
          <strong>{Math.min(currentPage * (pageSize || 10), totalItems || totalPages * (pageSize || 10))}</strong>{' '}
          of <strong>{totalItems || totalPages * (pageSize || 10)}</strong> results
        </span>
      </div>

      <div className="flex items-center gap-2">
        {showPageSize && pageSize && onPageSizeChange && (
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="px-2 py-1 text-sm border border-dark-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-800"
          >
            {[10, 20, 50, 100].map((size) => (
              <option key={size} value={size}>
                {size} per page
              </option>
            ))}
          </select>
        )}

        <button
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          className="p-2 rounded-lg text-dark-500 hover:bg-dark-100 disabled:opacity-50 disabled:cursor-not-allowed dark:text-dark-400 dark:hover:bg-dark-800"
          aria-label="First page"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>

        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="p-2 rounded-lg text-dark-500 hover:bg-dark-100 disabled:opacity-50 disabled:cursor-not-allowed dark:text-dark-400 dark:hover:bg-dark-800"
          aria-label="Previous page"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div className="flex items-center gap-1">
          {visiblePages.map((page, index) => {
            const prevPage = visiblePages[index - 1]
            const showEllipsis = prevPage && page - prevPage > 1

            return (
              <Fragment key={page}>
                {showEllipsis && (
                  <span className="px-2 text-dark-400">...</span>
                )}
                <button
                  onClick={() => onPageChange(page)}
                  className={cn(
                    'w-8 h-8 rounded-lg text-sm font-medium transition-colors',
                    page === currentPage
                      ? 'bg-primary-600 text-white'
                      : 'text-dark-600 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800'
                  )}
                  aria-label={`Page ${page}`}
                  aria-current={page === currentPage ? 'page' : undefined}
                >
                  {page}
                </button>
              </Fragment>
            )
          })}
        </div>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="p-2 rounded-lg text-dark-500 hover:bg-dark-100 disabled:opacity-50 disabled:cursor-not-allowed dark:text-dark-400 dark:hover:bg-dark-800"
          aria-label="Next page"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>

        <button
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          className="p-2 rounded-lg text-dark-500 hover:bg-dark-100 disabled:opacity-50 disabled:cursor-not-allowed dark:text-dark-400 dark:hover:bg-dark-800"
          aria-label="Last page"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7m-8-14l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  )
}