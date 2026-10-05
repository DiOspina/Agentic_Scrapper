import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { formatDate, formatDuration, formatRelativeTime, getStatusColor } from '../utils/helpers'
import { Table, Pagination, Badge } from '../components/ui'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Card, CardTitle, CardContent } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { ConfirmDialog } from '../components/ui/Modal'
import { Search, Filter, Play, Pause, StopCircle, RotateCw, Trash2, Eye, Download, ExternalLink } from 'lucide-react'
import { cn } from '../utils/helpers'

const STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: 'pending', label: 'Pending' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
]

const TYPE_OPTIONS = [
  { value: '', label: 'All Types' },
  { value: 'scraping', label: 'Scraping' },
  { value: 'analysis', label: 'Analysis' },
  { value: 'synthesis', label: 'Synthesis' },
  { value: 'full_pipeline', label: 'Full Pipeline' },
]

export function Executions() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedExecution, setSelectedExecution] = useState<any>(null)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [executionToDelete, setExecutionToDelete] = useState<string | null>(null)
  const [showLogs, setShowLogs] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['executions', page, pageSize, statusFilter, typeFilter, searchQuery],
    queryFn: () => api.listExecutions({ page, page_size: pageSize, status: statusFilter || undefined, execution_type: typeFilter || undefined }),
    placeholderData: (previousData) => previousData,
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createExecution(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] })
    },
  })

  const cancelMutation = useMutation({
    mutationFn: (id: string) => api.cancelExecution(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] })
    },
  })

  const handleCreateExecution = (type: string) => {
    createMutation.mutate({
      execution_type: type,
      input_data: {},
    })
  }

  const columns = [
    {
      key: 'execution_id',
      header: 'Execution ID',
      render: (row: any) => (
        <div>
          <div className="font-mono text-sm text-dark-900 dark:text-white">{row.execution_id.slice(0, 8)}...</div>
          <div className="text-xs text-dark-500 dark:text-dark-400">{formatRelativeTime(row.created_at)}</div>
        </div>
      ),
    },
    {
      key: 'execution_type',
      header: 'Type',
      render: (row: any) => (
        <Badge variant="info" size="sm">{row.execution_type.replace('_', ' ')}</Badge>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row: any) => (
        <Badge variant={getStatusColor(row.status) as any} dot>
          {row.status.charAt(0).toUpperCase() + row.status.slice(1)}
        </Badge>
      ),
      sortable: true,
    },
    {
      key: 'agent_name',
      header: 'Agent',
      render: (row: any) => (
        <Badge variant="neutral" size="sm">{row.agent_name || 'orchestrator'}</Badge>
      ),
    },
    {
      key: 'duration',
      header: 'Duration',
      render: (row: any) => (
        <span className="font-mono text-dark-600 dark:text-dark-400">
          {row.duration_seconds ? formatDuration(row.duration_seconds) : row.status === 'running' ? 'Running...' : '—'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: any) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSelectedExecution(row)}
            className="p-1.5 rounded-lg text-dark-500 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800 transition-colors"
            title="View details"
          >
            <Eye className="w-4 h-4" />
          </button>
          {row.status === 'running' && (
            <button
              onClick={() => cancelMutation.mutate(row.execution_id)}
              disabled={cancelMutation.isPending}
              className="p-1.5 rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="Cancel execution"
            >
              <StopCircle className="w-4 h-4" />
            </button>
          )}
          {row.status === 'pending' && (
            <button
              onClick={() => queryClient.invalidateQueries({ queryKey: ['executions'] })}
              className="p-1.5 rounded-lg text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
              title="Retry"
            >
              <RotateCw className="w-4 h-4" />
            </button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Executions</h1>
          <p className="text-dark-500 dark:text-dark-400 mt-1">Monitor and manage pipeline executions</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {TYPE_OPTIONS.slice(1).map((type) => (
            <Button
              key={type.value}
              variant="outline"
              size="sm"
              onClick={() => handleCreateExecution(type.value)}
              disabled={createMutation.isPending}
              leftIcon={<Play className="w-4 h-4" />}
            >
              Run {type.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <Card padding="sm">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 max-w-md">
            <Input
              placeholder="Search executions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
          </div>
          <div className="flex gap-2">
            <Select
              placeholder="All Status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              options={STATUS_OPTIONS}
              leftIcon={<Filter className="w-4 h-4" />}
            />
            <Select
              placeholder="All Types"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              options={TYPE_OPTIONS}
              leftIcon={<Filter className="w-4 h-4" />}
            />
          </div>
        </div>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <Table
            columns={columns}
            data={data?.executions || []}
            keyExtractor={(row) => row.execution_id}
            loading={isLoading}
            sortable
            striped
            hoverable
            emptyMessage="No executions found"
          />
          {data && (
            <Pagination
              currentPage={data.page}
              totalPages={data.total_pages}
              onPageChange={setPage}
              pageSize={data.page_size}
              onPageSizeChange={setPageSize}
              totalItems={data.total}
              showPageSize
            />
          )}
        </CardContent>
      </Card>

      {/* Execution Detail Modal */}
      <Modal
        isOpen={!!selectedExecution}
        onClose={() => setSelectedExecution(null)}
        title="Execution Details"
        size="lg"
      >
        {selectedExecution && (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Execution ID</label>
                <p className="font-mono text-dark-900 dark:text-white mt-1">{selectedExecution.execution_id}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Type</label>
                <p className="mt-1"><Badge variant="info">{selectedExecution.execution_type}</Badge></p>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Status</label>
                <p className="mt-1"><Badge variant={getStatusColor(selectedExecution.status) as any} dot>{selectedExecution.status}</Badge></p>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Agent</label>
                <p className="mt-1 text-dark-900 dark:text-white">{selectedExecution.agent_name || 'orchestrator'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Created</label>
                <p className="mt-1 text-dark-900 dark:text-white">{formatDate(selectedExecution.created_at)}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Duration</label>
                <p className="mt-1 font-mono text-dark-900 dark:text-white">
                  {selectedExecution.duration_seconds ? formatDuration(selectedExecution.duration_seconds) : '—'}
                </p>
              </div>
              {selectedExecution.started_at && (
                <div>
                  <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Started</label>
                  <p className="mt-1 text-dark-900 dark:text-white">{formatDate(selectedExecution.started_at)}</p>
                </div>
              )}
              {selectedExecution.completed_at && (
                <div>
                  <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Completed</label>
                  <p className="mt-1 text-dark-900 dark:text-white">{formatDate(selectedExecution.completed_at)}</p>
                </div>
              )}
            </div>

            {selectedExecution.error_message && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <label className="text-sm font-medium text-red-800 dark:text-red-400">Error</label>
                <p className="mt-1 text-red-700 dark:text-red-300">{selectedExecution.error_message}</p>
              </div>
            )}

            {selectedExecution.input_data && (
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Input Data</label>
                <pre className="mt-2 p-4 bg-dark-100 dark:bg-dark-800 rounded-lg text-sm overflow-x-auto max-h-64">
                  {JSON.stringify(selectedExecution.input_data, null, 2)}
                </pre>
              </div>
            )}

            {selectedExecution.output_data && (
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Output Data</label>
                <pre className="mt-2 p-4 bg-dark-100 dark:bg-dark-800 rounded-lg text-sm overflow-x-auto max-h-64">
                  {JSON.stringify(selectedExecution.output_data, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => { setShowDeleteDialog(false); setExecutionToDelete(null); }}
        onConfirm={() => { /* delete logic */ setShowDeleteDialog(false); setExecutionToDelete(null); }}
        title="Delete Execution"
        message="Are you sure you want to delete this execution? This action cannot be undone."
        variant="danger"
      />
    </div>
  )
}