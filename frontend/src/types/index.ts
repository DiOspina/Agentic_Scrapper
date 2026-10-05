// Type definitions for the frontend

export interface Execution {
  id: number;
  execution_id: string;
  execution_type: ExecutionType;
  status: ExecutionStatus;
  agent_name?: string;
  workflow_id?: number;
  parent_execution_id?: number;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  retry_count: number;
  max_retries: number;
  created_at: string;
  updated_at: string;
}

export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type ExecutionType = 'scraping' | 'analysis' | 'synthesis' | 'full_pipeline';

export interface Document {
  id: number;
  document_id: string;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  document_type: DocumentType;
  status: DocumentStatus;
  content?: string;
  summary?: string;
  metadata?: Record<string, any>;
  vector_ids?: string[];
  chunk_count: number;
  embedding_model?: string;
  error_message?: string;
  processing_time_seconds?: number;
  uploaded_by?: number;
  execution_id?: number;
  created_at: string;
  updated_at: string;
  processed_at?: string;
}

export type DocumentType = 'pdf' | 'csv' | 'txt' | 'markdown' | 'docx' | 'xlsx' | 'html' | 'json';
export type DocumentStatus = 'uploaded' | 'processing' | 'processed' | 'failed' | 'deleted';

export interface Workflow {
  id: number;
  workflow_id: string;
  n8n_workflow_id?: string;
  name: string;
  description?: string;
  status: WorkflowStatus;
  trigger_type: WorkflowTrigger;
  config?: Record<string, any>;
  schedule_cron?: string;
  webhook_path?: string;
  agents_config?: Record<string, any>;
  enabled_agents: string[];
  notify_on_success: boolean;
  notify_on_failure: boolean;
  notification_channels: string[];
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  last_execution_at?: string;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export type WorkflowStatus = 'draft' | 'active' | 'paused' | 'archived';
export type WorkflowTrigger = 'manual' | 'scheduled' | 'webhook' | 'event' | 'file_upload';

export interface AgentLog {
  id: number;
  execution_id: number;
  agent_type: AgentType;
  level: LogLevel;
  message: string;
  details?: Record<string, any>;
  step_name?: string;
  tool_name?: string;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  duration_ms?: number;
  tokens_used?: number;
  cost_usd?: number;
  created_at: string;
}

export type AgentType = 'scraper' | 'analyst' | 'synthesizer' | 'orchestrator';
export type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

export interface Metric {
  id: number;
  execution_id: number;
  name: string;
  metric_type: MetricType;
  value: number;
  unit?: string;
  labels?: Record<string, any>;
  description?: string;
  agent_type?: string;
  step_name?: string;
  created_at: string;
}

export type MetricType = 'performance' | 'quality' | 'business' | 'system' | 'custom';

export interface Alert {
  id: number;
  alert_id: string;
  workflow_id?: number;
  execution_id?: number;
  title: string;
  message: string;
  severity: string;
  channel: AlertChannel;
  recipient: string;
  status: AlertStatus;
  sent_at?: string;
  delivered_at?: string;
  read_at?: string;
  error_message?: string;
  retry_count: number;
  payload?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export type AlertChannel = 'email' | 'telegram' | 'whatsapp' | 'slack' | 'webhook' | 'sms';
export type AlertStatus = 'pending' | 'sent' | 'failed' | 'delivered' | 'read';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, any>;
  timestamp?: string;
}

export interface ChatSession {
  session_id: string;
  title?: string;
  messages: ChatMessage[];
  context?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HealthCheckResponse {
  status: string;
  version: string;
  environment: string;
  services: Record<string, string>;
  timestamp: string;
}

export interface ApiError {
  error: string;
  detail?: string;
  code?: string;
  status_code: number;
}

export interface ScrapedPage {
  url: string;
  title?: string;
  content: string;
  html: string;
  metadata: Record<string, any>;
  links: string[];
  images: string[];
  tables: any[];
  structured_data: any[];
  timestamp: number;
}

export interface AnalysisResult {
  analysis_type: string;
  result: Record<string, any>;
  confidence: number;
  sources: Array<Record<string, any>>;
  metrics: Record<string, number>;
}

export interface GeneratedReport {
  report_id: string;
  report_type: string;
  title: string;
  sections: ReportSection[];
  formats: Record<string, string>;
  metadata: Record<string, any>;
  created_at: string;
}

export interface ReportSection {
  title: string;
  content: string;
  order: number;
  format: string;
  metadata: Record<string, any>;
}