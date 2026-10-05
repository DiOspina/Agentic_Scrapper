import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { formatNumber, formatDuration } from '../utils/helpers'
import {
  ChartContainer,
  ChartGrid,
  StatCard,
  LineChartComponent,
  BarChartComponent,
  PieChartComponent,
  AreaChartComponent,
  ComposedChartComponent,
} from '../components/charts'
import { Card, CardTitle, CardContent } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Button } from '../components/ui/Button'
import { Download, Calendar, TrendingUp, Filter, RefreshCw } from 'lucide-react'
import { cn } from '../utils/helpers'

const TIME_RANGES = [
  { value: '7', label: 'Last 7 Days' },
  { value: '30', label: 'Last 30 Days' },
  { value: '90', label: 'Last 90 Days' },
]

const mockExecutionTrend = [
  { date: '2024-01-15', completed: 45, failed: 3, running: 5, duration: 12.5, tokens: 45000 },
  { date: '2024-01-16', completed: 52, failed: 2, running: 3, duration: 11.8, tokens: 52000 },
  { date: '2024-01-17', completed: 38, failed: 4, running: 7, duration: 14.2, tokens: 38000 },
  { date: '2024-01-18', completed: 61, failed: 1, running: 2, duration: 10.5, tokens: 61000 },
  { date: '2024-01-19', completed: 55, failed: 3, running: 4, duration: 12.1, tokens: 55000 },
  { date: '2024-01-20', completed: 49, failed: 2, running: 6, duration: 11.3, tokens: 49000 },
  { date: '2024-01-21', completed: 58, failed: 1, running: 3, duration: 10.8, tokens: 58000 },
]

const mockAgentPerformance = [
  { agent: 'Scraper', executions: 456, avgDuration: 8.2, successRate: 94.2, tokensUsed: 456000, cost: 12.45 },
  { agent: 'Analyst', executions: 389, avgDuration: 12.5, successRate: 97.1, tokensUsed: 789000, cost: 28.67 },
  { agent: 'Synthesizer', executions: 234, avgDuration: 5.8, successRate: 98.5, tokensUsed: 234000, cost: 4.89 },
]

const mockDocumentTypes = [
  { name: 'PDF', value: 145 },
  { name: 'CSV', value: 89 },
  { name: 'TXT', value: 56 },
  { name: 'DOCX', value: 32 },
  { name: 'XLSX', value: 20 },
]

const mockExecutionTypes = [
  { name: 'Full Pipeline', value: 567 },
  { name: 'Scraping', value: 342 },
  { name: 'Analysis', value: 234 },
  { name: 'Synthesis', value: 104 },
]

const mockErrorTypes = [
  { name: 'Timeout', value: 23 },
  { name: 'Network Error', value: 18 },
  { name: 'Parse Error', value: 12 },
  { name: 'Rate Limit', value: 8 },
  { name: 'Auth Error', value: 5 },
  { name: 'Other', value: 3 },
]

export function Analytics() {
  const [timeRange, setTimeRange] = useState('7')
  const [autoRefresh, setAutoRefresh] = useState(false)

  const { data: metrics } = useQuery({
    queryKey: ['metrics', 'summary'],
    queryFn: () => api.getMetricsSummary(),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const { data: execStats } = useQuery({
    queryKey: ['metrics', 'executions', 'stats', timeRange],
    queryFn: () => api.getExecutionStats(parseInt(timeRange)),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const { data: execByStatus } = useQuery({
    queryKey: ['metrics', 'executions', 'by-status', timeRange],
    queryFn: () => api.getExecutionsByStatus(parseInt(timeRange)),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const { data: execByType } = useQuery({
    queryKey: ['metrics', 'executions', 'by-type', timeRange],
    queryFn: () => api.getExecutionsByType(parseInt(timeRange)),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const { data: durationTrend } = useQuery({
    queryKey: ['metrics', 'executions', 'duration-trend', timeRange],
    queryFn: () => api.getExecutionDurationTrend(parseInt(timeRange)),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const { data: agentPerf } = useQuery({
    queryKey: ['metrics', 'agents', 'performance'],
    queryFn: () => api.getAgentPerformance(),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const { data: docStats } = useQuery({
    queryKey: ['metrics', 'documents', 'stats'],
    queryFn: () => api.getDocumentStats(),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const stats = metrics?.executions
    ? {
        totalExecutions: metrics.executions.total || 0,
        successRate: metrics.executions.by_status?.completed
          ? ((metrics.executions.by_status.completed / Math.max(metrics.executions.total, 1)) * 100).toFixed(1)
          : '0',
        avgDuration: metrics.executions.avg_duration || 0,
        totalTokens: metrics.agents?.total_tokens || 0,
        totalCost: metrics.agents?.total_cost || 0,
      }
    : {
        totalExecutions: 1247,
        successRate: '92.7',
        avgDuration: 11.5,
        totalTokens: 1250000,
        totalCost: 45.67,
      }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Analytics</h1>
          <p className="text-dark-500 dark:text-dark-400 mt-1">System performance and usage analytics</p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <Select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            options={TIME_RANGES}
            leftIcon={<Calendar className="w-4 h-4" />}
            className="w-48"
          />
          <label className="flex items-center gap-2 text-sm text-dark-600 dark:text-dark-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4 rounded border-dark-300 text-primary-600 focus:ring-primary-500"
            />
            Auto-refresh
          </label>
          <Button variant="outline" leftIcon={<Download className="w-4 h-4" />}>Export</Button>
          <Button variant="outline" leftIcon={<RefreshCw className="w-4 h-4" />}>Refresh</Button>
        </div>
      </div>

      {/* KPIs */}
      <ChartGrid columns={4}>
        <StatCard
          title="Total Executions"
          value={formatNumber(stats.totalExecutions)}
          change={12.5}
          changeLabel="vs previous period"
          icon={<TrendingUp className="w-6 h-6" />}
          iconColor="primary"
          trend="up"
        />
        <StatCard
          title="Success Rate"
          value={`${stats.successRate}%`}
          change={2.1}
          changeLabel="vs previous period"
          icon={<TrendingUp className="w-6 h-6" />}
          iconColor="success"
          trend="up"
        />
        <StatCard
          title="Avg Duration"
          value={`${stats.avgDuration}s`}
          change={-5.2}
          changeLabel="vs previous period"
          icon={<TrendingUp className="w-6 h-6" />}
          iconColor="info"
          trend="down"
        />
        <StatCard
          title="Total Cost"
          value={`$${stats.totalCost}`}
          change={8.3}
          changeLabel="vs previous period"
          icon={<TrendingUp className="w-6 h-6" />}
          iconColor="warning"
          trend="up"
        />
      </ChartGrid>

      {/* Execution Trends */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartContainer title="Execution Volume Trend" subtitle="Daily executions by status" height={350}>
          <AreaChartComponent
            data={mockExecutionTrend}
            xKey="date"
            areas={[
              { key: 'completed', name: 'Completed', color: '#10b981', opacity: 0.3 },
              { key: 'running', name: 'Running', color: '#6366f1', opacity: 0.3 },
              { key: 'failed', name: 'Failed', color: '#ef4444', opacity: 0.3 },
            ]}
            stacked
            height={300}
          />
        </ChartContainer>

        <ChartContainer title="Execution Duration Trend" subtitle="Average execution duration over time" height={350}>
          <LineChartComponent
            data={mockExecutionTrend}
            xKey="date"
            lines={[
              { key: 'duration', name: 'Avg Duration (s)', color: '#f59e0b' },
            ]}
            height={300}
          />
        </ChartContainer>
      </div>

      {/* Status & Type Distribution */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartContainer title="Execution Status" subtitle="Breakdown by status" height={350}>
          <PieChartComponent
            data={[
              { name: 'Completed', value: 1156, color: '#10b981' },
              { name: 'Running', value: 24, color: '#6366f1' },
              { name: 'Failed', value: 67, color: '#ef4444' },
            ]}
            height={300}
            innerRadius={60}
          />
        </ChartContainer>

        <ChartContainer title="Execution Types" subtitle="Distribution of execution types" height={350}>
          <PieChartComponent
            data={mockExecutionTypes}
            height={300}
            innerRadius={50}
          />
        </ChartContainer>
      </div>

      {/* Agent Performance */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartContainer title="Agent Executions" subtitle="Total executions per agent" height={350}>
          <BarChartComponent
            data={mockAgentPerformance}
            xKey="agent"
            bars={[
              { key: 'executions', name: 'Executions', color: '#6366f1' },
            ]}
            height={300}
          />
        </ChartContainer>

        <ChartContainer title="Agent Success Rate" subtitle="Success rate by agent" height={350}>
          <BarChartComponent
            data={mockAgentPerformance}
            xKey="agent"
            bars={[
              { key: 'successRate', name: 'Success Rate (%)', color: '#10b981' },
            ]}
            height={300}
          />
        </ChartContainer>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartContainer title="Agent Duration" subtitle="Average execution duration per agent" height={350}>
          <BarChartComponent
            data={mockAgentPerformance}
            xKey="agent"
            bars={[
              { key: 'avgDuration', name: 'Avg Duration (s)', color: '#f59e0b' },
            ]}
            height={300}
          />
        </ChartContainer>

        <ChartContainer title="Agent Tokens & Cost" subtitle="Token usage and cost by agent" height={350}>
          <ComposedChartComponent
            data={mockAgentPerformance}
            xKey="agent"
            bars={[
              { key: 'tokensUsed', name: 'Tokens Used', color: '#8b5cf6' },
            ]}
            lines={[
              { key: 'cost', name: 'Cost ($)', color: '#ef4444' },
            ]}
            height={300}
          />
        </ChartContainer>
      </div>

      {/* Document Analytics */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartContainer title="Documents by Type" subtitle="Distribution of uploaded documents" height={350}>
          <PieChartComponent
            data={mockDocumentTypes}
            height={300}
            innerRadius={50}
          />
        </ChartContainer>

        <ChartContainer title="Error Analysis" subtitle="Error types breakdown" height={350}>
          <BarChartComponent
            data={mockErrorTypes}
            xKey="name"
            bars={[
              { key: 'value', name: 'Count', color: '#ef4444' },
            ]}
            horizontal
            height={300}
            showValue
          />
        </ChartContainer>
      </div>

      {/* Detailed Tables */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardTitle title="Agent Performance Details" subtitle="Detailed metrics per agent" />
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-dark-200 dark:border-dark-700">
                    <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Agent</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Executions</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Avg Duration</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Success Rate</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Tokens</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Cost</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-200 dark:divide-dark-700">
                  {mockAgentPerformance.map((agent) => (
                    <tr key={agent.agent} className="hover:bg-dark-50 dark:hover:bg-dark-800/50">
                      <td className="px-4 py-3 font-medium text-dark-900 dark:text-white">{agent.agent}</td>
                      <td className="px-4 py-3 text-right text-dark-600 dark:text-dark-400 font-mono">{formatNumber(agent.executions)}</td>
                      <td className="px-4 py-3 text-right text-dark-600 dark:text-dark-400 font-mono">{agent.avgDuration}s</td>
                      <td className="px-4 py-3 text-right text-green-600 dark:text-green-400 font-mono">{agent.successRate}%</td>
                      <td className="px-4 py-3 text-right text-dark-600 dark:text-dark-400 font-mono">{formatNumber(agent.tokensUsed)}</td>
                      <td className="px-4 py-3 text-right text-dark-600 dark:text-dark-400 font-mono">${agent.cost.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardTitle title="Execution Types Breakdown" subtitle="Detailed execution type metrics" />
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-dark-200 dark:border-dark-700">
                    <th className="px-4 py-3 text-left text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Type</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Count</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-dark-500 dark:text-dark-400 uppercase tracking-wider">Percentage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-200 dark:divide-dark-700">
                  {mockExecutionTypes.map((type) => (
                    <tr key={type.name} className="hover:bg-dark-50 dark:hover:bg-dark-800/50">
                      <td className="px-4 py-3 font-medium text-dark-900 dark:text-white">{type.name}</td>
                      <td className="px-4 py-3 text-right text-dark-600 dark:text-dark-400 font-mono">{formatNumber(type.value)}</td>
                      <td className="px-4 py-3 text-right text-dark-600 dark:text-dark-400 font-mono">
                        {((type.value / mockExecutionTypes.reduce((sum, t) => sum + t.value, 0)) * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}