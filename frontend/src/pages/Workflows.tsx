import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { formatDate, formatRelativeTime, getStatusColor } from '../utils/helpers'
import { Table, Pagination, Badge } from '../components/ui'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Card, CardTitle, CardContent } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { ConfirmDialog } from '../components/ui/Modal'
import { Textarea } from '../components/ui/Textarea'
import { Plus, Play, Pause, Edit, Trash2, Eye, Copy, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '../utils/helpers'
import toast from 'react-hot-toast'

const STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: 'draft', label: 'Draft' },
  { value: 'active', label: 'Active' },
  { value: 'paused', label: 'Paused' },
  { value: 'archived', label: 'Archived' },
]

const TRIGGER_OPTIONS = [
  { value: '', label: 'All Triggers' },
  { value: 'manual', label: 'Manual' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'webhook', label: 'Webhook' },
  { value: 'event', label: 'Event' },
  { value: 'file_upload', label: 'File Upload' },
]

export function Workflows() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState('')
  const [triggerFilter, setTriggerFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [workflowToDelete, setWorkflowToDelete] = useState<string | null>(null)
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  const { data, isLoading } = useQuery({
    queryKey: ['workflows', page, pageSize, statusFilter, triggerFilter, searchQuery],
    queryFn: () => api.listWorkflows({ page, page_size: pageSize, status: statusFilter || undefined, trigger_type: triggerFilter || undefined }),
    placeholderData: (previousData) => previousData,
  })

  const { data: templates } = useQuery({
    queryKey: ['workflow-templates'],
    queryFn: () => api.getWorkflowTemplates(),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createWorkflow(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      toast.success('Workflow created')
      setShowCreate(false)
    },
    onError: (error: any) => toast.error(error.response?.data?.detail || 'Failed to create workflow'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => api.updateWorkflow(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflows'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteWorkflow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      toast.success('Workflow deleted')
      setShowDeleteDialog(false)
      setWorkflowToDelete(null)
    },
  })

  const executeMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => api.executeWorkflow(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      toast.success('Workflow execution started')
    },
  })

  const deployTemplateMutation = useMutation({
    mutationFn: ({ templateId, name }: { templateId: string; name: string }) =>
      api.deployN8nTemplate(templateId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      toast.success('Template deployed as workflow')
    },
  })

  const columns = [
    {
      key: 'name',
      header: 'Workflow',
      render: (row: any) => (
        <div>
          <div className="font-medium text-dark-900 dark:text-white">{row.name}</div>
          <div className="text-xs text-dark-500 dark:text-dark-400 truncate max-w-xs">{row.description || 'No description'}</div>
        </div>
      ),
    },
    {
      key: 'trigger_type',
      header: 'Trigger',
      render: (row: any) => (
        <Badge variant="info" size="sm">{row.trigger_type.replace('_', ' ')}</Badge>
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
      key: 'stats',
      header: 'Executions',
      render: (row: any) => (
        <div className="text-sm text-dark-600 dark:text-dark-400">
          <div>{row.total_executions} total</div>
          <div className="flex gap-4 text-xs">
            <span className="text-green-600 dark:text-green-400">✓ {row.successful_executions}</span>
            <span className="text-red-600 dark:text-red-400">✗ {row.failed_executions}</span>
          </div>
        </div>
      ),
    },
    {
      key: 'last_run',
      header: 'Last Run',
      render: (row: any) => (
        <div className="text-dark-600 dark:text-dark-400">
          {row.last_execution_at ? formatRelativeTime(row.last_execution_at) : 'Never'}
        </div>
      ),
      sortable: true,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: any) => (
        <div className="flex items-center gap-1">
          <button
            onClick={() => setSelectedWorkflow(row)}
            className="p-1.5 rounded-lg text-dark-500 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800 transition-colors"
            title="View details"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={() => executeMutation.mutate({ id: row.workflow_id, data: {} })}
            disabled={executeMutation.isPending || row.status !== 'active'}
            className="p-1.5 rounded-lg text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors opacity-50"
            title="Execute"
          >
            <Play className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              updateMutation.mutate({
                id: row.workflow_id,
                data: { status: row.status === 'active' ? 'paused' : 'active' },
              })
            }}
            className="p-1.5 rounded-lg text-dark-500 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800 transition-colors"
            title={row.status === 'active' ? 'Pause' : 'Activate'}
          >
            {row.status === 'active' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Workflows</h1>
          <p className="text-dark-500 dark:text-dark-400 mt-1">Manage automation workflows and n8n integrations</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowCreate(true)} leftIcon={<Plus className="w-4 h-4" />}>
            Create Workflow
          </Button>
        </div>
      </div>

      {/* Templates Section */}
      {templates?.templates && templates.templates.length > 0 && (
        <Card>
          <CardTitle title="Workflow Templates" subtitle="Quick-start templates for common patterns" action={
            <button className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400">View all</button>
          } />
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {templates.templates.slice(0, 6).map((template: any) => (
                <button
                  key={template.id}
                  onClick={() => {
                    const name = prompt(`Enter name for new workflow from "${template.name}":`)
                    if (name) deployTemplateMutation.mutate({ templateId: template.id, name })
                  }}
                  className="p-4 rounded-xl border border-dark-200 dark:border-dark-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors text-left group"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center group-hover:bg-primary-600 group-hover:text-white transition-colors">
                      <ExternalLink className="w-5 h-5 text-primary-600 dark:text-primary-400 group-hover:text-white" />
                    </div>
                    <h3 className="font-semibold text-dark-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">{template.name}</h3>
                  </div>
                  <p className="text-sm text-dark-500 dark:text-dark-400">{template.nodes_count} nodes</p>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card padding="sm">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 max-w-md">
            <Input
              placeholder="Search workflows..."
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
              placeholder="All Triggers"
              value={triggerFilter}
              onChange={(e) => setTriggerFilter(e.target.value)}
              options={TRIGGER_OPTIONS}
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
            data={data?.workflows || []}
            keyExtractor={(row) => row.workflow_id}
            loading={isLoading}
            sortable
            striped
            hoverable
            emptyMessage="No workflows found. Create your first workflow or deploy a template."
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

      {/* Create/Edit Modal */}
      <Modal
        isOpen={showCreate || !!selectedWorkflow}
        onClose={() => { setShowCreate(false); setSelectedWorkflow(null); }}
        title={selectedWorkflow ? 'Edit Workflow' : 'Create Workflow'}
        size="lg"
      >
        <WorkflowForm
          workflow={selectedWorkflow}
          onSubmit={(data) => {
            if (selectedWorkflow) {
              updateMutation.mutate({ id: selectedWorkflow.workflow_id, data })
            } else {
              createMutation.mutate(data)
            }
            setShowCreate(false)
            setSelectedWorkflow(null)
          }}
          onClose={() => { setShowCreate(false); setSelectedWorkflow(null); }}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => { setShowDeleteDialog(false); setWorkflowToDelete(null); }}
        onConfirm={() => { workflowToDelete && deleteMutation.mutate(workflowToDelete); }}
        title="Delete Workflow"
        message="Are you sure you want to delete this workflow? This action cannot be undone."
        variant="danger"
      />
    </div>
  )
}

function WorkflowForm({ workflow, onSubmit, onClose, isLoading }: any) {
  const [formData, setFormData] = useState({
    name: workflow?.name || '',
    description: workflow?.description || '',
    trigger_type: workflow?.trigger_type || 'manual',
    schedule_cron: workflow?.schedule_cron || '',
    webhook_path: workflow?.webhook_path || '',
    agents_config: workflow?.agents_config || {},
    enabled_agents: workflow?.enabled_agents || ['scraper', 'analyst', 'synthesizer'],
    notify_on_success: workflow?.notify_on_success || false,
    notify_on_failure: workflow?.notify_on_failure || true,
    notification_channels: workflow?.notification_channels || [],
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="Name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="My Workflow"
          required
        />
        <Select
          label="Trigger Type"
          value={formData.trigger_type}
          onChange={(e) => setFormData({ ...formData, trigger_type: e.target.value })}
          options={TRIGGER_OPTIONS.filter(o => o.value)}
        />
      </div>

      <Textarea
        label="Description"
        value={formData.description}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        placeholder="Workflow description"
        rows={3}
      />

      {formData.trigger_type === 'scheduled' && (
        <Input
          label="Cron Schedule"
          value={formData.schedule_cron}
          onChange={(e) => setFormData({ ...formData, schedule_cron: e.target.value })}
          placeholder="0 */6 * * * (every 6 hours)"
          helperText="Standard cron expression"
        />
      )}

      {formData.trigger_type === 'webhook' && (
        <Input
          label="Webhook Path"
          value={formData.webhook_path}
          onChange={(e) => setFormData({ ...formData, webhook_path: e.target.value })}
          placeholder="my-webhook"
          helperText="Path for webhook endpoint (e.g., /webhook/my-webhook)"
        />
      )}

      <div className="border-t border-dark-200 dark:border-dark-700 pt-6">
        <h3 className="font-medium text-dark-900 dark:text-white mb-4">Agent Configuration</h3>
        <div className="grid gap-4 sm:grid-cols-3">
          {['scraper', 'analyst', 'synthesizer'].map((agent) => (
            <label key={agent} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.enabled_agents.includes(agent)}
                onChange={(e) => setFormData({
                  ...formData,
                  enabled_agents: e.target.checked
                    ? [...formData.enabled_agents, agent]
                    : formData.enabled_agents.filter((a: string) => a !== agent),
                })}
                className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-dark-900 dark:text-white capitalize">{agent}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="border-t border-dark-200 dark:border-dark-700 pt-6">
        <h3 className="font-medium text-dark-900 dark:text-white mb-4">Notifications</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.notify_on_success}
              onChange={(e) => setFormData({ ...formData, notify_on_success: e.target.checked })}
              className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-dark-700 dark:text-dark-300">Notify on success</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.notify_on_failure}
              onChange={(e) => setFormData({ ...formData, notify_on_failure: e.target.checked })}
              className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-dark-700 dark:text-dark-300">Notify on failure</span>
          </label>
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-dark-200 dark:border-dark-700">
        <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
        <Button type="submit" loading={isLoading}>
          {workflow ? 'Update' : 'Create'} Workflow
        </Button>
      </div>
    </form>
  )
}