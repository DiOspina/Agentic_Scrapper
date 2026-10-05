import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { formatNumber, formatRelativeTime } from '../utils/helpers'
import {
  ChartContainer,
  ChartGrid,
  StatCard,
  LineChartComponent,
  BarChartComponent,
  PieChartComponent,
} from '../components/charts'
import { Card, CardTitle, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import {
  FileText,
  Workflow,
  Bot,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  ExternalLink,
} from 'lucide-react'
import { useState, useEffect } from 'react'

const mockMetrics = {
  executions: { total: 1247, success: 1156, failed: 67, running: 24, change: 12.5 },
  documents: { total: 342, processed: 318, pending: 24, change: 8.2 },
  workflows: { total: 18, active: 12, paused: 4, draft: 2, change: 5.1 },
  agents: { total: 3, avgDuration: 4.2, tokensUsed: 1250000, cost: 45.67, change: -2.3 },
}

const mockExecutionTrend = [
  { date: '2024-01-15', completed: 45, failed: 3, duration: 12.5 },
  { date: '2024-01-16', completed: 52, failed: 2, duration: 11.8 },
  { date: '2024-01-17', completed: 38, failed: 4, duration: 14.2 },
  { date: '2024-01-18', completed: 61, failed: 1, duration: 10.5 },
  { date: '2024-01-19', completed: 55, failed: 3, duration: 12.1 },
  { date: '2024-01-20', completed: 49, failed: 2, duration: 11.3 },
  { date: '2024-01-21', completed: 58, failed: 1, duration: 10.8 },
]

const mockAgentPerformance = [
  { agent: 'Scraper', executions: 456, avgDuration: 8.2, successRate: 94.2 },
  { agent: 'Analyst', executions: 389, avgDuration: 12.5, successRate: 97.1 },
  { agent: 'Synthesizer', executions: 234, avgDuration: 5.8, successRate: 98.5 },
]

const mockDocumentTypes = [
  { name: 'PDF', value: 145 },
  { name: 'CSV', value: 89 },
  { name: 'TXT', value: 56 },
  { name: 'DOCX', value: 32 },
  { name: 'XLSX', value: 20 },
]

const mockRecentExecutions = [
  { id: 'exec_001', type: 'full_pipeline', status: 'completed', agent: 'orchestrator', duration: '1m 23s', time: '2 min ago' },
  { id: 'exec_002', type: 'scraping', status: 'completed', agent: 'scraper', duration: '45s', time: '5 min ago' },
  { id: 'exec_003', type: 'analysis', status: 'running', agent: 'analyst', duration: '2m 10s', time: '1 min ago' },
  { id: 'exec_004', type: 'synthesis', status: 'completed', agent: 'synthesizer', duration: '32s', time: '10 min ago' },
  { id: 'exec_005', type: 'full_pipeline', status: 'failed', agent: 'orchestrator', duration: '1m 05s', time: '15 min ago' },
]

export function Dashboard() {
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch real data from API
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['metrics', 'summary'],
    queryFn: () => api.getMetricsSummary(),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const { data: execStats, isLoading: execLoading } = useQuery({
    queryKey: ['metrics', 'executions', 'stats'],
    queryFn: () => api.getExecutionStats(7),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const { data: docStats, isLoading: docLoading } = useQuery({
    queryKey: ['metrics', 'documents', 'stats'],
    queryFn: () => api.getDocumentStats(),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const { data: recentExecutions, isLoading: recentLoading } = useQuery({
    queryKey: ['executions', 'recent'],
    queryFn: () => api.listExecutions({ page: 1, page_size: 10 }),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        // Trigger refetch
      }, 30000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const stats = metrics?.executions
    ? {
        executions: {
          total: metrics.executions.total || mockMetrics.executions.total,
          success: metrics.executions.by_status?.completed || mockMetrics.executions.success,
          failed: metrics.executions.by_status?.failed || mockMetrics.executions.failed,
          running: metrics.executions.by_status?.running || mockMetrics.executions.running,
        },
        documents: {
          total: docStats?.total_documents || mockMetrics.documents.total,
          processed: docStats?.by_status?.processed || mockMetrics.documents.processed,
          pending: docStats?.by_status?.processing || mockMetrics.documents.pending,
        },
        workflows: { total: mockMetrics.workflows.total, active: mockMetrics.workflows.active, paused: mockMetrics.workflows.paused, draft: mockMetrics.workflows.draft },
        agents: { total: mockMetrics.agents.total, avgDuration: mockMetrics.agents.avgDuration, tokensUsed: mockMetrics.agents.tokensUsed, cost: mockMetrics.agents.cost },
      }
    : mockMetrics

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Dashboard</h1>
          <p className="text-dark-500 dark:text-dark-400 mt-1">Overview of your Agenttic AI orchestration system</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm text-dark-600 dark:text-dark-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
            />
            Auto-refresh (30s)
          </label>
          <button
            className="btn-secondary"
            onClick={() => window.location.reload()}
            disabled={metricsLoading}
          >
            <RefreshCw className="w-4 h-4 animate-spin" />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <ChartGrid columns={4}>
        <StatCard
          title="Total Executions"
          value={formatNumber(stats.executions.total)}
          change={stats.executions.change}
          changeLabel="vs last week"
          icon={<FileText className="w-6 h-6" />}
          iconColor="primary"
          trend="up"
        />
        <StatCard
          title="Success Rate"
          value={`${(((stats.executions.success || 0) / Math.max(stats.executions.total, 1)) * 100).toFixed(1)}%`}
          change={2.1}
          changeLabel="vs last week"
          icon={<CheckCircle className="w-6 h-6" />}
          iconColor="success"
          trend="up"
        />
        <StatCard
          title="Documents Processed"
          value={formatNumber(stats.documents.processed)}
          change={stats.documents.change}
          changeLabel="vs last week"
          icon={<FileText className="w-6 h-6" />}
          iconColor="info"
          trend="up"
        />
        <StatCard
          title="Active Workflows"
          value={stats.workflows.active}
          change={stats.workflows.change}
          changeLabel="vs last week"
          icon={<Workflow className="w-6 h-6" />}
          iconColor="warning"
          trend="neutral"
        />
      </ChartGrid>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Execution Trend */}
        <ChartContainer title="Execution Trend (7 Days)" subtitle="Completed vs Failed executions" height={350}>
          <LineChartComponent
            data={mockExecutionTrend}
            xKey="date"
            lines={[
              { key: 'completed', name: 'Completed', color: '#10b981' },
              { key: 'failed', name: 'Failed', color: '#ef4444' },
            ]}
            height={300}
          />
        </ChartContainer>

        {/* Agent Performance */}
        <ChartContainer title="Agent Performance" subtitle="Average duration and success rate by agent" height={350}>
          <ComposedChartComponent
            data={mockAgentPerformance}
            xKey="agent"
            bars={[
              { key: 'executions', name: 'Executions', color: '#6366f1' },
            ]}
            lines={[
              { key: 'avgDuration', name: 'Avg Duration (s)', color: '#f59e0b' },
              { key: 'successRate', name: 'Success Rate (%)', color: '#10b981' },
            ]}
            height={300}
          />
        </ChartContainer>
      </div>

      {/* Second Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Document Types */}
        <ChartContainer title="Documents by Type" subtitle="Distribution of uploaded documents" height={350}>
          <PieChartComponent
            data={mockDocumentTypes}
            height={300}
            innerRadius={50}
          />
        </ChartContainer>

        {/* Execution Status */}
        <ChartContainer title="Execution Status" subtitle="Current status breakdown" height={350}>
          <PieChartComponent
            data={[
              { name: 'Completed', value: stats.executions.success, color: '#10b981' },
              { name: 'Running', value: stats.executions.running, color: '#6366f1' },
              { name: 'Failed', value: stats.executions.failed, color: '#ef4444' },
              { name: 'Pending', value: Math.max(stats.executions.total - stats.executions.success - stats.executions.failed - stats.executions.running, 0), color: '#f59e0b' },
            ]}
            height={300}
            innerRadius={60}
          />
        </ChartContainer>
      </div>

      {/* Recent Executions */}
      <Card>
        <CardTitle
          title="Recent Executions"
          subtitle="Latest pipeline executions"
          action={
            <a href="/executions" className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 flex items-center gap-1">
              View all
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          }
        />
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-200 dark:border-dark-700">
                  <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Execution ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Agent</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Duration</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-200 dark:divide-dark-700">
                {mockRecentExecutions.map((exec) => (
                  <tr key={exec.id} className="hover:bg-dark-50 dark:hover:bg-dark-800/50">
                    <td className="px-4 py-3 font-mono text-dark-900 dark:text-white">{exec.id}</td>
                    <td className="px-4 py-3">
                      <Badge variant="info" size="sm">{exec.type.replace('_', ' ')}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={exec.status === 'completed' ? 'success' : exec.status === 'running' ? 'info' : exec.status === 'failed' ? 'error' : 'warning'} dot>
                        {exec.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="neutral" size="sm">{exec.agent}</Badge>
                    </td>
                    <td className="px-4 py-3 text-dark-600 dark:text-dark-400 font-mono">{exec.duration}</td>
                    <td className="px-4 py-3 text-dark-500 dark:text-dark-400">{exec.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardTitle title="Quick Actions" subtitle="Common tasks to get started" />
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <button className="group p-6 rounded-xl border border-dark-200 dark:border-dark-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors text-left">
              <div className="w-12 h-12 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mb-4 group-hover:bg-primary-600 group-hover:text-white transition-colors">
                <Bot className="w-6 h-6 text-primary-600 dark:text-primary-400 group-hover:text-white" />
              </div>
              <h3 className="font-semibold text-dark-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">Run Scraper</h3>
              <p className="text-sm text-dark-500 dark:text-dark-400 mt-1">Extract data from websites</p>
            </button>
            <button className="group p-6 rounded-xl border border-dark-200 dark:border-dark-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors text-left">
              <div className="w-12 h-12 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-4 group-hover:bg-green-600 group-hover:text-white transition-colors">
                <FileText className="w-6 h-6 text-green-600 dark:text-green-400 group-hover:text-white" />
              </div>
              <h3 className="font-semibold text-dark-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">Upload Document</h3>
              <p className="text-sm text-dark-500 dark:text-dark-400 mt-1">Process PDF, CSV, or text files</p>
            </button>
            <button className="group p-6 rounded-xl border border-dark-200 dark:border-dark-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors text-left">
              <div className="w-12 h-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mb-4 group-hover:bg-purple-600 group-hover:text-white transition-colors">
                <Workflow className="w-6 h-6 text-purple-600 dark:text-purple-400 group-hover:text-white" />
              </div>
              <h3 className="font-semibold text-dark-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">Create Workflow</h3>
              <p className="text-sm text-dark-500 dark:text-dark-400 mt-1">Automate recurring tasks</p>
            </button>
            <button className="group p-6 rounded-xl border border-dark-200 dark:border-dark-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors text-left">
              <div className="w-12 h-12 rounded-lg bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center mb-4 group-hover:bg-orange-600 group-hover:text-white transition-colors">
                <TrendingUp className="w-6 h-6 text-orange-600 dark:text-orange-400 group-hover:text-white" />
              </div>
              <h3 className="font-semibold text-dark-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">Analyze Data</h3>
              <p className="text-sm text-dark-500 dark:text-dark-400 mt-1">Run RAG analysis on documents</p>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}