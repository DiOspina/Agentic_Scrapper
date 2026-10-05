import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ApiError } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Generic methods
  async get<T>(url: string, params?: Record<string, any>) {
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  async post<T>(url: string, data?: any) {
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  async patch<T>(url: string, data?: any) {
    const response = await this.client.patch<T>(url, data)
    return response.data
  }

  async delete<T>(url: string) {
    const response = await this.client.delete<T>(url)
    return response.data
  }

  // File upload
  async upload<T>(url: string, file: File, onProgress?: (progress: number) => void) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await this.client.post<T>(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          onProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total))
        }
      },
    })
    return response.data
  }

  // Health
  async healthCheck() {
    return this.get<{ status: string; version: string; environment: string; services: Record<string, string> }>('/health')
  }

  // Executions
  async listExecutions(params?: {
    page?: number
    page_size?: number
    status?: string
    execution_type?: string
    workflow_id?: number
  }) {
    return this.get<{ executions: any[]; total: number; page: number; page_size: number; total_pages: number }>('/executions', params)
  }

  async getExecution(executionId: string) {
    return this.get<any>(`/executions/${executionId}`)
  }

  async createExecution(data: {
    execution_type: string
    input_data?: Record<string, any>
    agent_name?: string
    workflow_id?: number
    max_retries?: number
  }) {
    return this.post<any>('/executions', data)
  }

  async cancelExecution(executionId: string) {
    return this.post<any>(`/executions/${executionId}/cancel`)
  }

  async getExecutionLogs(executionId: string, params?: {
    page?: number
    page_size?: number
    level?: string
    agent_type?: string
  }) {
    return this.get<any>(`/executions/${executionId}/logs`, params)
  }

  async getExecutionMetrics(executionId: string) {
    return this.get<any>(`/executions/${executionId}/metrics`)
  }

  // Documents
  async listDocuments(params?: {
    page?: number
    page_size?: number
    status?: string
    document_type?: string
  }) {
    return this.get<{ documents: any[]; total: number; page: number; page_size: number; total_pages: number }>('/documents', params)
  }

  async getDocument(documentId: string) {
    return this.get<any>(`/documents/${documentId}`)
  }

  async getDocumentContent(documentId: string) {
    return this.get<{ content: string; metadata: Record<string, any> }>(`/documents/${documentId}/content`)
  }

  async uploadDocument(file: File, onProgress?: (progress: number) => void) {
    return this.upload<any>('/documents/upload', file, onProgress)
  }

  async deleteDocument(documentId: string) {
    return this.delete<any>(`/documents/${documentId}`)
  }

  async batchProcessDocuments(documentIds: string[]) {
    return this.post<any>('/documents/batch-process', { document_ids: documentIds })
  }

  // Workflows
  async listWorkflows(params?: {
    page?: number
    page_size?: number
    status?: string
    trigger_type?: string
  }) {
    return this.get<{ workflows: any[]; total: number; page: number; page_size: number; total_pages: number }>('/workflows', params)
  }

  async getWorkflow(workflowId: string) {
    return this.get<any>(`/workflows/${workflowId}`)
  }

  async createWorkflow(data: {
    name: string
    description?: string
    trigger_type: string
    config?: Record<string, any>
    schedule_cron?: string
    webhook_path?: string
    agents_config?: Record<string, any>
    enabled_agents?: string[]
    notify_on_success?: boolean
    notify_on_failure?: boolean
    notification_channels?: string[]
  }) {
    return this.post<any>('/workflows', data)
  }

  async updateWorkflow(workflowId: string, data: Partial<any>) {
    return this.patch<any>(`/workflows/${workflowId}`, data)
  }

  async deleteWorkflow(workflowId: string) {
    return this.delete<any>(`/workflows/${workflowId}`)
  }

  async executeWorkflow(workflowId: string, data: {
    input_data?: Record<string, any>
    trigger_type?: string
    webhook_payload?: Record<string, any>
  }) {
    return this.post<any>(`/workflows/${workflowId}/execute`, data)
  }

  async getWorkflowExecutions(workflowId: string, params?: { page?: number; page_size?: number }) {
    return this.get<any>(`/workflows/${workflowId}/executions`, params)
  }

  async getWorkflowTemplates() {
    return this.get<any>('/workflows/templates')
  }

  // Agents
  async scrape(data: { urls: string[]; config?: Record<string, any> }) {
    return this.post<any>('/agents/scrape', data)
  }

  async analyze(data: {
    documents: any[]
    queries?: string[]
    analysis_types?: string[]
    document_ids?: string[]
  }) {
    return this.post<any>('/agents/analyze', data)
  }

  async synthesize(data: {
    analysis_results: any[]
    scraped_data?: Record<string, any>
    query_results?: any[]
    metrics?: Record<string, any>
    report_config?: Record<string, any>
  }) {
    return this.post<any>('/agents/synthesize', data)
  }

  async getAgentsStatus() {
    return this.get<any>('/agents/status')
  }

  // Chat
  async createChatSession(data: { title?: string; initial_context?: Record<string, any> }) {
    return this.post<any>('/chat/sessions', data)
  }

  async listChatSessions(limit?: number) {
    return this.get<any>('/chat/sessions', { limit })
  }

  async getChatSession(sessionId: string) {
    return this.get<any>(`/chat/sessions/${sessionId}`)
  }

  async deleteChatSession(sessionId: string) {
    return this.delete<any>(`/chat/sessions/${sessionId}`)
  }

  async sendChatMessage(sessionId: string, data: {
    message: string
    context?: Record<string, any>
    use_rag?: boolean
    top_k?: number
    temperature?: number
    max_tokens?: number
  }) {
    return this.post<any>(`/chat/sessions/${sessionId}/message`, data)
  }

  async queryWithoutSession(data: {
    message: string
    context?: Record<string, any>
    use_rag?: boolean
    top_k?: number
    temperature?: number
    max_tokens?: number
  }) {
    return this.post<any>('/chat/query', data)
  }

  // Metrics
  async getMetricsSummary() {
    return this.get<any>('/metrics/summary')
  }

  async getExecutionStats(days?: number) {
    return this.get<any>('/metrics/executions/stats', { days })
  }

  async getExecutionsByStatus(days?: number) {
    return this.get<any>('/metrics/executions/by-status', { days })
  }

  async getExecutionsByType(days?: number) {
    return this.get<any>('/metrics/executions/by-type', { days })
  }

  async getExecutionDurationTrend(days?: number) {
    return this.get<any>('/metrics/executions/duration-trend', { days })
  }

  async getAgentPerformance() {
    return this.get<any>('/metrics/agents/performance')
  }

  async getDocumentStats() {
    return this.get<any>('/metrics/documents/stats')
  }

  async getVectorStoreStats() {
    return this.get<any>('/metrics/vector-store/stats')
  }

  async getSystemMetrics() {
    return this.get<any>('/metrics/system')
  }

  // n8n
  async triggerN8nWorkflow(workflowId: string, data?: Record<string, any>) {
    return this.post<any>('/n8n/trigger-workflow', { workflow_id: workflowId, data })
  }

  async triggerWebhook(webhookPath: string, payload: Record<string, any>) {
    return this.post<any>('/n8n/trigger-webhook', { webhook_path: webhookPath, payload })
  }

  async listN8nWorkflows(active?: boolean) {
    return this.get<any>('/n8n/workflows', { active })
  }

  async getN8nWorkflow(workflowId: string) {
    return this.get<any>(`/n8n/workflows/${workflowId}`)
  }

  async importN8nWorkflow(workflowJson: Record<string, any>) {
    return this.post<any>('/n8n/workflows/import', workflowJson)
  }

  async getN8nTemplates() {
    return this.get<any>('/n8n/templates')
  }

  async getN8nTemplate(templateId: string) {
    return this.get<any>(`/n8n/templates/${templateId}`)
  }

  async deployN8nTemplate(templateId: string, workflowName: string) {
    return this.post<any>(`/n8n/templates/${templateId}/deploy`, { workflow_name: workflowName })
  }

  async listN8nExecutions(params?: { workflow_id?: string; status?: string; limit?: number }) {
    return this.get<any>('/n8n/executions', params)
  }

  async n8nHealth() {
    return this.get<any>('/n8n/health')
  }
}

export const api = new ApiClient()