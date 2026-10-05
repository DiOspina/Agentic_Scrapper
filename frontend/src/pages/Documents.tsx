import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { formatDate, formatFileSize, getStatusColor, formatRelativeTime } from '../utils/helpers'
import { Table, Pagination, Badge } from '../components/ui'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Card, CardTitle, CardContent } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { ConfirmDialog } from '../components/ui/Modal'
import { Upload, FileText, Search, Filter, Download, Trash2, Eye, RotateCw, FilePlus } from 'lucide-react'
import { cn } from '../utils/helpers'
import toast from 'react-hot-toast'

const STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: 'uploaded', label: 'Uploaded' },
  { value: 'processing', label: 'Processing' },
  { value: 'processed', label: 'Processed' },
  { value: 'failed', label: 'Failed' },
  { value: 'deleted', label: 'Deleted' },
]

const TYPE_OPTIONS = [
  { value: '', label: 'All Types' },
  { value: 'pdf', label: 'PDF' },
  { value: 'csv', label: 'CSV' },
  { value: 'txt', label: 'TXT' },
  { value: 'markdown', label: 'Markdown' },
  { value: 'docx', label: 'DOCX' },
  { value: 'xlsx', label: 'XLSX' },
  { value: 'html', label: 'HTML' },
  { value: 'json', label: 'JSON' },
]

export function Documents() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDocument, setSelectedDocument] = useState<any>(null)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [documentToDelete, setDocumentToDelete] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})

  const { data, isLoading } = useQuery({
    queryKey: ['documents', page, pageSize, statusFilter, typeFilter, searchQuery],
    queryFn: () => api.listDocuments({ page, page_size: pageSize, status: statusFilter || undefined, document_type: typeFilter || undefined }),
    placeholderData: (previousData) => previousData,
  })

  const uploadMutation = useMutation({
    mutationFn: ({ file, onProgress }: { file: File; onProgress?: (progress: number) => void }) =>
      api.uploadDocument(file, onProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document uploaded successfully')
      setShowUpload(false)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Upload failed')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Document deleted')
      setShowDeleteDialog(false)
      setDocumentToDelete(null)
    },
    onError: () => toast.error('Failed to delete document'),
  })

  const reprocessMutation = useMutation({
    mutationFn: (ids: string[]) => api.batchProcessDocuments(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      toast.success('Documents queued for reprocessing')
    },
  })

  const handleFileUpload = (files: FileList) => {
    Array.from(files).forEach((file) => {
      const fileId = `${file.name}-${Date.now()}`
      setUploadProgress(prev => ({ ...prev, [fileId]: 0 }))
      uploadMutation.mutate({
        file,
        onProgress: (progress) => setUploadProgress(prev => ({ ...prev, [fileId]: progress })),
      })
    })
  }

  const columns = [
    {
      key: 'original_filename',
      header: 'Filename',
      render: (row: any) => (
        <div className="flex items-center gap-3">
          <div className={cn(
            'w-10 h-10 rounded-lg flex items-center justify-center',
            row.document_type === 'pdf' && 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
            row.document_type === 'csv' && 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
            row.document_type === 'txt' && 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
            row.document_type === 'markdown' && 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
            row.document_type === 'docx' && 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
            row.document_type === 'xlsx' && 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
            'bg-dark-100 text-dark-600 dark:bg-dark-700 dark:text-dark-400'
          )}>
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="font-medium text-dark-900 dark:text-white truncate max-w-xs">{row.original_filename}</div>
            <div className="text-xs text-dark-500 dark:text-dark-400">
              {formatFileSize(row.file_size)} • {row.document_type.toUpperCase()}
            </div>
          </div>
        </div>
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
      key: 'chunks',
      header: 'Chunks',
      render: (row: any) => (
        <span className="text-dark-600 dark:text-dark-400 font-mono">{row.chunk_count}</span>
      ),
    },
    {
      key: 'created',
      header: 'Uploaded',
      render: (row: any) => (
        <div className="text-dark-600 dark:text-dark-400">
          <div>{formatRelativeTime(row.created_at)}</div>
          <div className="text-xs">{formatDate(row.created_at)}</div>
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
            onClick={() => setSelectedDocument(row)}
            className="p-1.5 rounded-lg text-dark-500 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800 transition-colors"
            title="View details"
          >
            <Eye className="w-4 h-4" />
          </button>
          {row.status === 'processed' && (
            <button
              onClick={() => api.getDocumentContent(row.document_id).then(res => {
                const blob = new Blob([res.content], { type: 'text/plain' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = row.original_filename
                a.click()
                URL.revokeObjectURL(url)
              })}
              className="p-1.5 rounded-lg text-dark-500 hover:bg-dark-100 dark:text-dark-400 dark:hover:bg-dark-800 transition-colors"
              title="Download content"
            >
              <Download className="w-4 h-4" />
            </button>
          )}
          {row.status === 'failed' && (
            <button
              onClick={() => reprocessMutation.mutate([row.document_id])}
              disabled={reprocessMutation.isPending}
              className="p-1.5 rounded-lg text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
              title="Reprocess"
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
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Documents</h1>
          <p className="text-dark-500 dark:text-dark-400 mt-1">Manage and process your documents</p>
        </div>
        <Button onClick={() => setShowUpload(true)} leftIcon={<Upload className="w-4 h-4" />}>
          Upload Document
        </Button>
      </div>

      {/* Filters */}
      <Card padding="sm">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 max-w-md">
            <Input
              placeholder="Search documents..."
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

      {/* Upload Progress */}
      {Object.keys(uploadProgress).length > 0 && (
        <Card>
          <CardTitle title="Uploading..." subtitle={`${Object.keys(uploadProgress).length} file(s) in progress`} />
          <CardContent>
            <div className="space-y-3">
              {Object.entries(uploadProgress).map(([fileId, progress]) => (
                <div key={fileId} className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-dark-900 dark:text-white truncate">{fileId.split('-')[0]}</span>
                      <span className="text-dark-500 dark:text-dark-400">{progress}%</span>
                    </div>
                    <div className="h-2 bg-dark-200 dark:bg-dark-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-600 transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <Table
            columns={columns}
            data={data?.documents || []}
            keyExtractor={(row) => row.document_id}
            loading={isLoading}
            sortable
            striped
            hoverable
            emptyMessage="No documents found. Upload your first document to get started."
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

      {/* Upload Modal */}
      <Modal
        isOpen={showUpload}
        onClose={() => setShowUpload(false)}
        title="Upload Document"
        size="lg"
      >
        <div className="space-y-6">
          <div className="border-2 border-dashed border-dark-300 dark:border-dark-600 rounded-xl p-8 text-center hover:border-primary-400 transition-colors">
            <input
              type="file"
              multiple
              accept=".pdf,.csv,.txt,.md,.docx,.xlsx,.html,.json"
              onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="w-12 h-12 text-dark-400 mx-auto mb-4" />
              <p className="text-dark-600 dark:text-dark-400 mb-2">Drag & drop files here, or click to browse</p>
              <p className="text-sm text-dark-500 dark:text-dark-400">PDF, CSV, TXT, MD, DOCX, XLSX, HTML, JSON (max 50MB)</p>
            </label>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowUpload(false)}>Cancel</Button>
          </div>
        </div>
      </Modal>

      {/* Document Detail Modal */}
      <Modal
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)}
        title="Document Details"
        size="lg"
      >
        {selectedDocument && (
          <div className="space-y-6 max-h-[70vh] overflow-y-auto">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Document ID</label>
                <p className="font-mono text-dark-900 dark:text-white mt-1">{selectedDocument.document_id}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Filename</label>
                <p className="mt-1 text-dark-900 dark:text-white">{selectedDocument.original_filename}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Type</label>
                <p className="mt-1"><Badge variant="info">{selectedDocument.document_type.toUpperCase()}</Badge></p>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Status</label>
                <p className="mt-1"><Badge variant={getStatusColor(selectedDocument.status) as any} dot>{selectedDocument.status}</Badge></p>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Size</label>
                <p className="mt-1 text-dark-900 dark:text-white">{formatFileSize(selectedDocument.file_size)}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Chunks</label>
                <p className="mt-1 text-dark-900 dark:text-white">{selectedDocument.chunk_count}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Uploaded</label>
                <p className="mt-1 text-dark-900 dark:text-white">{formatDate(selectedDocument.created_at)}</p>
              </div>
              {selectedDocument.processed_at && (
                <div>
                  <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Processed</label>
                  <p className="mt-1 text-dark-900 dark:text-white">{formatDate(selectedDocument.processed_at)}</p>
                </div>
              )}
            </div>

            {selectedDocument.summary && (
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Summary</label>
                <p className="mt-2 p-4 bg-dark-50 dark:bg-dark-800 rounded-lg text-dark-700 dark:text-dark-300">{selectedDocument.summary}</p>
              </div>
            )}

            {selectedDocument.metadata && (
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Metadata</label>
                <pre className="mt-2 p-4 bg-dark-100 dark:bg-dark-800 rounded-lg text-sm overflow-x-auto max-h-64">
                  {JSON.stringify(selectedDocument.metadata, null, 2)}
                </pre>
              </div>
            )}

            {selectedDocument.content && (
              <div>
                <label className="text-sm font-medium text-dark-500 dark:text-dark-400">Content Preview</label>
                <pre className="mt-2 p-4 bg-dark-100 dark:bg-dark-800 rounded-lg text-sm overflow-x-auto max-h-96 whitespace-pre-wrap">
                  {selectedDocument.content.slice(0, 5000)}{selectedDocument.content.length > 5000 ? '... (truncated)' : ''}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => { setShowDeleteDialog(false); setDocumentToDelete(null); }}
        onConfirm={() => { documentToDelete && deleteMutation.mutate(documentToDelete); }}
        title="Delete Document"
        message="Are you sure you want to delete this document? This will also remove it from the vector store."
        variant="danger"
      />
    </div>
  )
}